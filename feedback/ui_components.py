"""
Streamlit UI components for the feedback system
Development mode only - provides feedback collection and review interface
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from .manager import feedback_manager
from .vector_store import FAISS_AVAILABLE

def show_feedback_ui():
    """Main feedback UI - only shown in development mode"""
    if not feedback_manager.development_mode:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠️ Developer Feedback Portal")
    
    # Vector store health check
    health = feedback_manager.store.health_check()
    if health["status"] != "healthy":
        st.sidebar.error(f"⚠️ Vector Store: {health.get('message', 'Not available')}")
        if not health.get("faiss_available", False):
            st.sidebar.info("💡 Install FAISS: `pip install faiss-cpu`")
        return
    else:
        st.sidebar.success("✅ Vector Store Connected")
    
    # Quick stats
    stats = feedback_manager.get_feedback_statistics()
    if not stats.get("error"):
        st.sidebar.metric("Total Feedback", stats.get("total_feedback", 0))
        if stats.get("total_feedback", 0) > 0:
            helpful_rate = (stats.get("helpful_feedback", 0) / stats.get("total_feedback", 1)) * 100
            st.sidebar.metric("Helpful Rate", f"{helpful_rate:.1f}%")
    
    # Main feedback actions
    feedback_action = st.sidebar.selectbox(
        "Feedback Actions:",
        ["None", "💬 Provide Feedback", "📋 Review Feedback", "📊 Statistics", "🔍 Test Retrieval", "🌟 View Positive Examples"],
        index=0
    )
    
    if feedback_action == "💬 Provide Feedback":
        show_feedback_collection()
    elif feedback_action == "📋 Review Feedback":
        show_feedback_review()
    elif feedback_action == "📊 Statistics":
        show_feedback_statistics()
    elif feedback_action == "🔍 Test Retrieval":
        show_feedback_retrieval_test()
    elif feedback_action == "🌟 View Positive Examples":
        show_positive_examples()

def show_feedback_collection():
    """Show feedback collection form"""
    st.subheader("💬 Provide Developer Feedback")
    
    # Get the last query and response from session state
    last_prompt = st.session_state.get('last_user_query', '')
    last_response = st.session_state.get('last_ai_response', '')
    last_sql = st.session_state.get('last_sql_query', '')
    vendor_id = st.session_state.get('vendor_id', '')
    case_id = st.session_state.get('case_id', '')
    
    if not last_prompt or not last_response:
        st.warning("No recent query/response found. Please ask a question first.")
        return
    
    # Display the query and response being evaluated
    with st.expander("📝 Query & Response Being Evaluated", expanded=True):
        st.markdown("**User Question:**")
        st.info(last_prompt)
        
        st.markdown("**AI Response:**")
        st.info(last_response)
        
        if last_sql:
            st.markdown("**Generated SQL:**")
            st.code(last_sql, language="sql")
    
    # Feedback form
    with st.form("feedback_form"):
        st.markdown("### Feedback Details")
        
        # Basic evaluation
        col1, col2 = st.columns(2)
        with col1:
            is_helpful = st.radio(
                "Was this response helpful?",
                options=[True, False],
                format_func=lambda x: "✅ Yes, helpful" if x else "❌ No, not helpful"
            )
        
        with col2:
            # Always show both sliders but use different labels
            if is_helpful:
                quality_rating = st.slider(
                    "Quality Rating",
                    min_value=1, max_value=5, value=4,
                    help="How good was this response? 1=Poor, 5=Excellent"
                )
                severity = 1  # Default for positive feedback
            else:
                severity = st.slider(
                    "Issue severity",
                    min_value=1, max_value=5, value=1,
                    help="1=Minor, 5=Critical"
                )
                quality_rating = 1  # Default for negative feedback
        
        # Category selection - different options for positive vs negative feedback
        if is_helpful:
            category = st.selectbox(
                "What made this response good?",
                options=["", "query_accuracy", "response_format", "data_presentation", "completeness", "clarity", "performance"],
                help="What category of excellence does this represent?"
            )
            
            good_example_type = st.selectbox(
                "Type of good example",
                options=["", "sql_structure", "data_analysis", "formatting", "error_handling", "user_guidance", "comprehensive_answer"],
                help="What type of pattern should be reused from this example?"
            )
        else:
            category = st.selectbox(
                "Issue Category",
                options=["", "query_accuracy", "response_format", "pricing_data", "item_processing", "security", "performance"],
                help="What type of issue is this?"
            )
            good_example_type = ""  # Default for negative feedback
        
        # Always show text areas but with different labels/placeholders
        if is_helpful:
            # Positive feedback fields
            positive_aspects = st.text_area(
                "What was done well?",
                placeholder="Describe what made this response excellent. What should be replicated in future responses?",
                height=100
            )
            
            reusable_pattern = st.text_area(
                "Reusable Pattern/Approach",
                placeholder="Describe the approach or pattern used here that could be applied to similar queries...",
                height=100
            )
            
            improvement_suggestion = st.text_area(
                "Optional: How could this be even better?",
                placeholder="Any suggestions to make excellent responses even better?",
                height=100
            )
            
            # Set defaults for negative feedback fields
            correction = ""
            
        else:
            # Negative feedback fields
            correction = st.text_area(
                "Correction/Fix (if applicable)",
                placeholder="If the response was incorrect, provide the correct information or approach...",
                height=100
            )
            
            improvement_suggestion = st.text_area(
                "Improvement Suggestion",
                placeholder="How could this response be improved? What should the AI do differently?",
                height=100
            )
            
            # Set defaults for positive feedback fields
            positive_aspects = ""
            reusable_pattern = ""
        
        # Automatic query type detection
        query_type = detect_query_type(last_prompt, last_sql)
        st.info(f"📋 Detected query type: **{query_type}**")
        
        # Submit button - always present regardless of feedback type
        button_text = "🎉 Submit Positive Feedback" if is_helpful else "🔧 Submit Issue Report"
        submitted = st.form_submit_button(button_text, type="primary")
        
        if submitted:
            # Enhanced duplicate feedback detection
            existing_feedback = feedback_manager.find_similar_feedback(last_prompt, last_response)
            
            # If similar feedback exists, offer to update it instead of creating new
            if existing_feedback and existing_feedback.get('similarity_score', 0) > 0.95:
                # Very similar feedback exists - update it
                feedback_id = existing_feedback.get('id')
                
                # Show information about the update
                st.info(f"🔍 Found very similar feedback (similarity: {existing_feedback.get('similarity_score', 0):.1%}). Updating existing entry instead of creating duplicate.")
                
                updates = {
                    'developer_feedback': {
                        'is_helpful': is_helpful,
                        'correction': correction if correction else None,
                        'improvement_suggestion': improvement_suggestion if improvement_suggestion else None,
                        'category': category if category else None,
                        'severity': severity,
                        'positive_aspects': positive_aspects if positive_aspects else None,
                        'quality_rating': quality_rating,
                        'reusable_pattern': reusable_pattern if reusable_pattern else None,
                        'updated_at': datetime.now().isoformat()
                    }
                }
                success = feedback_manager.update_feedback_item(feedback_id, updates)
                
                if success:
                    st.success("🔄 Updated existing feedback for this query!")
                    # Removed st.balloons() to prevent animation
                else:
                    st.error("❌ Failed to update existing feedback.")
            else:
                # Create new feedback
                success = feedback_manager.submit_feedback(
                    original_prompt=last_prompt,
                    original_response=last_response,
                    is_helpful=is_helpful,
                    correction=correction if correction else None,
                    improvement_suggestion=improvement_suggestion if improvement_suggestion else None,
                    category=category if category else None,
                    severity=severity,
                    vendor_id=vendor_id,
                    case_id=case_id,
                    sql_query=last_sql,
                    query_type=query_type,
                    # Positive feedback parameters
                    positive_aspects=positive_aspects if positive_aspects else None,
                    good_example_type=category if category else None,  # Use category as example type
                    quality_rating=quality_rating,
                    reusable_pattern=reusable_pattern if reusable_pattern else None
                )
                
                if success:
                    if is_helpful:
                        st.success("🎉 Positive feedback submitted! This will help improve future responses.")
                        # Removed st.balloons() to prevent animation
                    else:
                        st.success("🔧 Issue feedback submitted! This will help fix the problem.")
                        # Removed st.balloons() to prevent animation
                else:
                    st.error("❌ Failed to submit feedback. Check logs for details.")

def show_feedback_review():
    """Show feedback review interface"""
    st.subheader("📋 Feedback Review Dashboard")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vendor_filter = st.selectbox(
            "Filter by Vendor",
            options=["All Vendors"] + get_unique_vendors(),
            key="feedback_vendor_filter"
        )
    
    with col2:
        helpful_filter = st.selectbox(
            "Filter by Helpfulness",
            options=["All Feedback", "Helpful Only", "Unhelpful Only"],
            key="feedback_helpful_filter"
        )
    
    with col3:
        category_filter = st.selectbox(
            "Filter by Category",
            options=["All Categories"] + get_unique_categories(),
            key="feedback_category_filter"
        )
    
    # Get filtered feedback
    vendor_id = None if vendor_filter == "All Vendors" else vendor_filter
    feedback_items = feedback_manager.get_all_feedback_for_review(vendor_id)
    
    # Apply filters
    if helpful_filter == "Helpful Only":
        feedback_items = [f for f in feedback_items if f.get("developer_feedback", {}).get("is_helpful", False)]
    elif helpful_filter == "Unhelpful Only":
        feedback_items = [f for f in feedback_items if not f.get("developer_feedback", {}).get("is_helpful", True)]
    
    if category_filter != "All Categories":
        feedback_items = [f for f in feedback_items if f.get("developer_feedback", {}).get("category") == category_filter]
    
    # Display feedback items
    if not feedback_items:
        st.info("No feedback items found with the selected filters.")
        return
    
    st.markdown(f"**Found {len(feedback_items)} feedback items**")
    
    # Pagination
    items_per_page = 5
    total_pages = (len(feedback_items) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        page = st.selectbox("Page", range(1, total_pages + 1)) - 1
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_items = feedback_items[start_idx:end_idx]
    else:
        page_items = feedback_items
    
    # Display each feedback item
    for i, item in enumerate(page_items):
        with st.expander(f"📝 Feedback #{i+1} - {item.get('created_at', '')[:10]}", expanded=False):
            display_feedback_item(item)

def display_feedback_item(item: Dict[str, Any]):
    """Display a single feedback item with edit capabilities"""
    dev_feedback = item.get("developer_feedback", {})
    is_helpful = dev_feedback.get("is_helpful", False)
    
    # Basic info
    col1, col2 = st.columns(2)
    with col1:
        if is_helpful:
            st.markdown(f"**Status:** ✅ Positive Feedback")
            st.markdown(f"**Quality Rating:** {dev_feedback.get('quality_rating', 'N/A')}/5")
        else:
            st.markdown(f"**Status:** ❌ Issue Report")
            st.markdown(f"**Severity:** {dev_feedback.get('severity', 1)}/5")
        
    with col2:
        st.markdown(f"**Category:** {dev_feedback.get('category', 'N/A')}")
        st.markdown(f"**Query Type:** {item.get('query_type', 'N/A')}")
        if is_helpful and dev_feedback.get('good_example_type'):
            st.markdown(f"**Example Type:** {dev_feedback.get('good_example_type')}")
    
    # Original content
    st.markdown("**Original Prompt:**")
    st.info(item.get("original_prompt", ""))
    
    st.markdown("**Original Response:**")
    st.info(item.get("original_response", ""))
    
    if item.get("sql_query"):
        st.markdown("**Generated SQL:**")
        st.code(item.get("sql_query"), language="sql")
    
    # Feedback specific content
    if is_helpful:
        # Show positive feedback details
        if dev_feedback.get("positive_aspects"):
            st.markdown("**✨ What was done well:**")
            st.success(dev_feedback.get("positive_aspects"))
        
        if dev_feedback.get("reusable_pattern"):
            st.markdown("**🔄 Reusable Pattern:**")
            st.info(dev_feedback.get("reusable_pattern"))
        
        if dev_feedback.get("improvement_suggestion"):
            st.markdown("**💡 Suggested Enhancement:**")
            st.warning(dev_feedback.get("improvement_suggestion"))
    else:
        # Show negative feedback details
        if dev_feedback.get("correction"):
            st.markdown("**🔧 Correction Needed:**")
            st.error(dev_feedback.get("correction"))
        
        if dev_feedback.get("improvement_suggestion"):
            st.markdown("**💡 Improvement Suggestion:**")
            st.warning(dev_feedback.get("improvement_suggestion"))
    
    # Check if this item is in edit mode
    edit_mode_key = f"edit_mode_{item.get('id', '')}"
    in_edit_mode = st.session_state.get(edit_mode_key, False)
    
    if in_edit_mode:
        # Show edit form instead of action buttons
        show_edit_feedback_form(item)
    else:
        # Show action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"✏️ Edit", key=f"edit_{item.get('id', '')}"):
                st.session_state[edit_mode_key] = True
                st.rerun()
        
        with col2:
            delete_confirm_key = f"confirm_delete_{item.get('id', '')}"
            if st.button(f"🗑️ Delete", key=f"delete_{item.get('id', '')}", type="secondary"):
                if st.session_state.get(delete_confirm_key, False):
                    success = feedback_manager.delete_feedback_item(item.get('id', ''))
                    if success:
                        st.success("Feedback deleted successfully!")
                        # Clear confirmation state
                        if delete_confirm_key in st.session_state:
                            del st.session_state[delete_confirm_key]
                        st.rerun()
                    else:
                        st.error("Failed to delete feedback")
                else:
                    st.session_state[delete_confirm_key] = True
                    st.warning("⚠️ Click again to confirm deletion")
        
        with col3:
            # Export individual item
            export_data = {
                "feedback_item": item,
                "export_timestamp": datetime.now().isoformat()
            }
            st.download_button(
                "💾 Export",
                data=json.dumps(export_data, indent=2),
                file_name=f"feedback_{item.get('id', '')}.json",
                mime="application/json",
                key=f"export_{item.get('id', '')}"
            )

def show_edit_feedback_form(item: Dict[str, Any]):
    """Show enhanced edit form for feedback item"""
    st.subheader("📝 Edit Feedback")
    
    dev_feedback = item.get("developer_feedback", {})
    
    with st.form(f"edit_form_{item['id']}"):
        st.markdown("### Feedback Details")
        
        # Two column layout for better organization
        col1, col2 = st.columns(2)
        
        with col1:
            # Editable fields
            is_helpful = st.radio(
                "Is this response helpful?",
                options=[True, False],
                format_func=lambda x: "✅ Helpful" if x else "❌ Needs Improvement",
                index=0 if dev_feedback.get("is_helpful") else 1,
                key=f"edit_helpful_{item['id']}"
            )
            
            if not is_helpful:
                severity = st.slider(
                    "Issue Severity",
                    min_value=1, max_value=5,
                    value=dev_feedback.get("severity", 1),
                    help="1=Minor issue, 5=Critical problem",
                    key=f"edit_severity_{item['id']}"
                )
            else:
                quality_rating = st.slider(
                    "Quality Rating",
                    min_value=1, max_value=5,
                    value=dev_feedback.get("quality_rating", 3),
                    help="1=Poor, 5=Excellent",
                    key=f"edit_quality_{item['id']}"
                )
                severity = 1  # Default for positive feedback
        
        with col2:
            # Category selection
            if is_helpful:
                category_options = ["", "excellent_query_handling", "accurate_data_retrieval", 
                                  "clear_response_format", "helpful_explanation", 
                                  "efficient_sql_generation", "good_error_handling"]
                help_text = "What made this response successful?"
            else:
                category_options = ["", "query_accuracy", "response_format", "pricing_data", 
                                  "item_processing", "security", "performance", 
                                  "sql_generation", "data_interpretation"]
                help_text = "What type of issue was this?"
                quality_rating = 3  # Default for negative feedback
            
            current_category = dev_feedback.get("category", "")
            try:
                current_index = category_options.index(current_category) if current_category in category_options else 0
            except ValueError:
                current_index = 0
                
            category = st.selectbox(
                "Category",
                options=category_options,
                index=current_index,
                help=help_text,
                key=f"edit_category_{item['id']}"
            )
        
        # Text fields based on feedback type
        if is_helpful:
            st.markdown("### Positive Feedback Details")
            
            positive_aspects = st.text_area(
                "What was done well?",
                value=dev_feedback.get("positive_aspects", ""),
                placeholder="Describe what made this response excellent...",
                height=100,
                key=f"edit_positive_{item['id']}"
            )
            
            reusable_pattern = st.text_area(
                "Reusable Pattern/Approach",
                value=dev_feedback.get("reusable_pattern", ""),
                placeholder="Describe the approach that could be applied to similar queries...",
                height=100,
                key=f"edit_pattern_{item['id']}"
            )
            
            improvement = st.text_area(
                "How could this be even better?",
                value=dev_feedback.get("improvement_suggestion", ""),
                placeholder="Optional suggestions for improvement...",
                height=100,
                key=f"edit_improvement_{item['id']}"
            )
            
            # Set defaults for fields not used in positive feedback
            correction = None
        else:
            st.markdown("### Issue Details")
            
            correction = st.text_area(
                "Correction/Fix",
                value=dev_feedback.get("correction", ""),
                placeholder="Provide the correct information or approach...",
                height=100,
                key=f"edit_correction_{item['id']}"
            )
            
            improvement = st.text_area(
                "Improvement Suggestion",
                value=dev_feedback.get("improvement_suggestion", ""),
                placeholder="How should this response be improved?",
                height=100,
                key=f"edit_improvement_{item['id']}"
            )
            
            # Set defaults for fields not used in negative feedback
            positive_aspects = None
            reusable_pattern = None
        
        # Form submission buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", type="secondary")
        
        with col3:
            preview = st.form_submit_button("👀 Preview Changes")
        
        if submitted:
            # Validate inputs
            if is_helpful and not positive_aspects:
                st.error("⚠️ Please describe what was done well for positive feedback.")
                return
            
            if not is_helpful and not correction and not improvement:
                st.error("⚠️ Please provide either a correction or improvement suggestion for issue feedback.")
                return
            
            # Prepare updated feedback data with enhanced structure
            updated_feedback = {
                'is_helpful': is_helpful,
                'category': category,
                'updated_at': datetime.now().isoformat(),
                'updated_by': 'developer'
            }
            
            if is_helpful:
                updated_feedback.update({
                    'quality_rating': quality_rating,
                    'positive_aspects': positive_aspects,
                    'reusable_pattern': reusable_pattern,
                    'improvement_suggestion': improvement if improvement else None,
                    'severity': 1  # Reset severity for positive feedback
                })
            else:
                updated_feedback.update({
                    'severity': severity,
                    'correction': correction,
                    'improvement_suggestion': improvement,
                    'quality_rating': 1  # Reset quality rating for negative feedback
                })
            
            # Update the feedback item
            success = feedback_manager.update_feedback_item(
                item['id'], 
                {'developer_feedback': updated_feedback}
            )
            
            if success:
                st.success("✅ Feedback updated successfully!")
                # Clear edit mode
                if f"edit_mode_{item['id']}" in st.session_state:
                    del st.session_state[f"edit_mode_{item['id']}"]
                st.rerun()
            else:
                st.error("❌ Failed to update feedback. Please try again.")
        
        elif cancelled:
            # Clear edit mode without saving
            if f"edit_mode_{item['id']}" in st.session_state:
                del st.session_state[f"edit_mode_{item['id']}"]
            st.rerun()
        
        elif preview:
            # Show preview of changes without saving
            st.markdown("### 👀 Preview of Changes")
            
            preview_data = {
                'is_helpful': is_helpful,
                'category': category,
                'updated_at': datetime.now().isoformat()
            }
            
            if is_helpful:
                preview_data.update({
                    'quality_rating': quality_rating,
                    'positive_aspects': positive_aspects,
                    'reusable_pattern': reusable_pattern,
                    'improvement_suggestion': improvement if improvement else None
                })
            else:
                preview_data.update({
                    'severity': severity,
                    'correction': correction,
                    'improvement_suggestion': improvement
                })
            
            st.json(preview_data)
            st.info("💡 Click 'Save Changes' to apply these updates.")

def show_feedback_statistics():
    """Show enhanced feedback system statistics including positive examples"""
    st.subheader("📊 Feedback System Statistics")
    
    stats = feedback_manager.get_feedback_statistics()
    
    if "error" in stats:
        st.error(f"Error loading statistics: {stats['error']}")
        return
    
    # Main metrics row 1
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Feedback", stats.get("total_feedback", 0))
    
    with col2:
        st.metric("✅ Positive", stats.get("positive_feedback_count", 0))
    
    with col3:
        st.metric("❌ Issues", stats.get("negative_feedback_count", 0))
    
    with col4:
        positive_ratio = stats.get("positive_feedback_ratio", 0) * 100
        st.metric("Success Rate", f"{positive_ratio:.1f}%")
    
    # Quality metrics row 2
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_quality = stats.get("average_quality_rating", 0)
        st.metric("Avg Quality", f"{avg_quality:.1f}/5" if avg_quality > 0 else "N/A")
    
    with col2:
        st.metric("Reusable Patterns", stats.get("total_reusable_patterns", 0))
    
    with col3:
        st.metric("Unique Vendors", stats.get("unique_vendors", 0))
    
    with col4:
        example_types = stats.get("example_types_distribution", {})
        most_common_type = max(example_types, key=example_types.get) if example_types else "N/A"
        st.metric("Top Example Type", most_common_type)
    
    # Example types distribution
    if example_types:
        st.subheader("🎯 Example Types Distribution")
        
        # Create a simple bar chart data
        types_df = pd.DataFrame([
            {"Type": type_name, "Count": count} 
            for type_name, count in example_types.items()
        ])
        
        if not types_df.empty:
            st.bar_chart(types_df.set_index("Type"))
    
    # Export options
    st.subheader("📁 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("� Export All Feedback"):
            export_data = feedback_manager.export_feedback_data()
            
            if "error" not in export_data:
                st.download_button(
                    "💾 Download All Feedback",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.error(f"Export failed: {export_data['error']}")
    
    with col2:
        if st.button("🌟 Export Positive Examples"):
            export_data = feedback_manager.export_positive_examples()
            
            if "error" not in export_data:
                st.download_button(
                    "💾 Download Positive Examples",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"positive_examples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.error(f"Export failed: {export_data['error']}")
    
    with col3:
        # Query type filter for positive examples
        query_types = ["All Types", "item_query", "financial_query", "status_query", "general_query"]
        selected_type = st.selectbox("Filter by Query Type", query_types)
        
        if st.button("🎯 Export by Type"):
            filter_type = None if selected_type == "All Types" else selected_type
            export_data = feedback_manager.export_positive_examples(query_type=filter_type)
            
            if "error" not in export_data:
                filename = f"positive_examples_{selected_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                st.download_button(
                    f"💾 Download {selected_type} Examples",
                    data=json.dumps(export_data, indent=2),
                    file_name=filename,
                    mime="application/json"
                )
            else:
                st.error(f"Export failed: {export_data['error']}")
    
    # Quick preview of top positive examples
    if stats.get("positive_feedback_count", 0) > 0:
        st.subheader("🌟 Sample Positive Examples")
        
        # Get a few positive examples for preview
        sample_examples = feedback_manager.get_positive_examples("", limit=3)
        
        if sample_examples:
            for i, example in enumerate(sample_examples[:3]):
                with st.expander(f"Example {i+1} (Quality: {example.get('developer_feedback', {}).get('quality_rating', 'N/A')}/5)"):
                    st.markdown(f"**Query:** {example.get('original_prompt', '')[:100]}...")
                    
                    dev_feedback = example.get('developer_feedback', {})
                    if dev_feedback.get('positive_aspects'):
                        st.success(f"✨ Strengths: {dev_feedback['positive_aspects']}")
                    
                    if dev_feedback.get('reusable_pattern'):
                        st.info(f"🔄 Pattern: {dev_feedback['reusable_pattern']}")

def detect_query_type(prompt: str, sql_query: str) -> str:
    """Detect the type of query based on prompt and SQL"""
    prompt_lower = prompt.lower()
    sql_lower = sql_query.lower() if sql_query else ""
    
    # Check for item-related queries
    if any(keyword in prompt_lower for keyword in ['items', 'products', 'services', 'line items']):
        return "item_query"
    
    # Check for financial queries
    if any(keyword in prompt_lower for keyword in ['amount', 'total', 'balance', 'paid', 'cost', 'price']):
        return "financial_query"
    
    # Check for status queries
    if any(keyword in prompt_lower for keyword in ['status', 'overdue', 'paid', 'pending']):
        return "status_query"
    
    # Check for date queries
    if any(keyword in prompt_lower for keyword in ['date', 'when', 'due', 'recent']):
        return "date_query"
    
    # Check SQL for specific patterns
    if 'items_description' in sql_lower:
        return "item_query"
    
    if any(keyword in sql_lower for keyword in ['sum(', 'count(', 'avg(']):
        return "aggregate_query"
    
    return "general_query"

def get_unique_vendors() -> List[str]:
    """Get list of unique vendor IDs from feedback"""
    try:
        all_feedback = feedback_manager.get_all_feedback_for_review()
        vendors = list(set(f.get("vendor_id") for f in all_feedback if f.get("vendor_id")))
        return sorted(vendors)
    except:
        return []

def get_unique_categories() -> List[str]:
    """Get list of unique categories from feedback"""
    try:
        all_feedback = feedback_manager.get_all_feedback_for_review()
        categories = list(set(f.get("developer_feedback", {}).get("category") for f in all_feedback if f.get("developer_feedback", {}).get("category")))
        return sorted(categories)
    except:
        return []

def show_feedback_retrieval_test():
    """Test feedback retrieval system for developers"""
    st.subheader("🔍 Test Feedback Retrieval")
    st.write("Test how the vector similarity search works for prompt enhancement.")
    
    # Test prompt input
    test_prompt = st.text_area(
        "Enter a test prompt:",
        placeholder="e.g., What is the price of product X?",
        height=100
    )
    
    # Similarity threshold adjustment
    similarity_threshold = st.slider(
        "Similarity Threshold", 
        min_value=0.0, 
        max_value=1.0, 
        value=feedback_manager.store.similarity_threshold,
        step=0.05,
        help="Higher values = more similar results required"
    )
    
    # Max results
    max_results = st.slider("Max Results", 1, 10, 5)
    
    if st.button("🔍 Test Retrieval") and test_prompt:
        with st.spinner("Searching for similar feedback..."):
            # Temporarily adjust threshold
            original_threshold = feedback_manager.store.similarity_threshold
            feedback_manager.store.similarity_threshold = similarity_threshold
            
            try:
                # Search for similar feedback
                similar_feedback = feedback_manager.store.search_similar_feedback(
                    test_prompt, limit=max_results
                )
                
                if similar_feedback:
                    st.success(f"Found {len(similar_feedback)} similar feedback items")
                    
                    for i, feedback in enumerate(similar_feedback, 1):
                        with st.expander(f"📝 Result {i} - Similarity: {feedback['similarity_score']:.3f}"):
                            st.write("**Original Prompt:**")
                            st.write(feedback['original_prompt'])
                            
                            st.write("**Original Response:**")
                            st.write(feedback['original_response'])
                            
                            dev_feedback = feedback['developer_feedback']
                            st.write("**Developer Feedback:**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Helpful:** {'✅' if dev_feedback.get('is_helpful') else '❌'}")
                                st.write(f"**Category:** {dev_feedback.get('category', 'N/A')}")
                            
                            with col2:
                                st.write(f"**Severity:** {dev_feedback.get('severity', 'N/A')}")
                                st.write(f"**Created:** {feedback.get('created_at', 'N/A')}")
                            
                            if dev_feedback.get('correction'):
                                st.write("**Correction:**")
                                st.info(dev_feedback['correction'])
                            
                            if dev_feedback.get('improvement_suggestion'):
                                st.write("**Improvement Suggestion:**")
                                st.info(dev_feedback['improvement_suggestion'])
                    
                    # Show how this would be used for prompt enhancement
                    st.subheader("🚀 Prompt Enhancement Preview")
                    enhancement = feedback_manager.generate_feedback_prompt_enhancement(test_prompt)
                    if enhancement:
                        st.code(enhancement, language="text")
                    else:
                        st.info("No prompt enhancement would be generated (no helpful corrections found)")
                
                else:
                    st.warning("No similar feedback found for this prompt")
                    st.info("Try lowering the similarity threshold or adding more feedback data")
            
            finally:
                # Restore original threshold
                feedback_manager.store.similarity_threshold = original_threshold

def inject_feedback_into_session():
    """Store query and response in session state for feedback collection"""
    # This will be called from the main app after generating responses
    pass

def show_positive_examples():
    """Show positive feedback examples for learning purposes"""
    st.subheader("🌟 Positive Examples Library")
    
    st.markdown("""
    This section shows examples of queries that received positive feedback. 
    These examples help the AI learn successful patterns and approaches.
    """)
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        query_type_filter = st.selectbox(
            "Filter by Query Type",
            options=["All Types", "item_query", "financial_query", "status_query", "general_query"]
        )
    
    with col2:
        min_quality = st.slider(
            "Minimum Quality Rating",
            min_value=1, max_value=5, value=3,
            help="Show only examples with this quality rating or higher"
        )
    
    # Get positive examples
    filter_type = None if query_type_filter == "All Types" else query_type_filter
    examples = feedback_manager.get_positive_examples("", query_type=filter_type, limit=10)
    
    # Filter by quality rating
    filtered_examples = [
        ex for ex in examples 
        if ex.get("developer_feedback", {}).get("quality_rating", 0) >= min_quality
    ]
    
    if not filtered_examples:
        st.info("No positive examples found with the selected filters.")
        return
    
    st.markdown(f"**Found {len(filtered_examples)} positive examples**")
    
    # Display examples
    for i, example in enumerate(filtered_examples):
        dev_feedback = example.get("developer_feedback", {})
        quality = dev_feedback.get("quality_rating", 0)
        
        with st.expander(f"🌟 Example {i+1} - Quality: {quality}/5 ({example.get('query_type', 'Unknown')})"):
            # Original query and response
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Original Query:**")
                st.info(example.get("original_prompt", ""))
                
                if example.get("sql_query"):
                    st.markdown("**Generated SQL:**")
                    st.code(example.get("sql_query"), language="sql")
            
            with col2:
                st.markdown("**AI Response:**")
                response_preview = example.get("original_response", "")[:300]
                if len(example.get("original_response", "")) > 300:
                    response_preview += "..."
                st.info(response_preview)
            
            # Positive feedback details
            st.markdown("**🎯 Why This Example is Good:**")
            
            if dev_feedback.get("positive_aspects"):
                st.success(f"✨ **Strengths:** {dev_feedback['positive_aspects']}")
            
            if dev_feedback.get("reusable_pattern"):
                st.info(f"🔄 **Reusable Pattern:** {dev_feedback['reusable_pattern']}")
            
            if dev_feedback.get("good_example_type"):
                st.markdown(f"**📋 Example Type:** {dev_feedback['good_example_type']}")
            
            if dev_feedback.get("category"):
                st.markdown(f"**📂 Excellence Category:** {dev_feedback['category']}")
            
            # Timestamp
            if example.get("created_at"):
                st.caption(f"Submitted: {example['created_at'][:10]}")
