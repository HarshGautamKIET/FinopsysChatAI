#!/usr/bin/env python3
"""
FinOpsys ChatAI - Feedback System Demo
Demonstrates the vector-based feedback system capabilities.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_feedback_submission():
    """Demo feedback submission"""
    print("🔹 Demo: Feedback Submission")
    
    from feedback.manager import feedback_manager
    
    # Enable development mode
    feedback_manager.set_development_mode(True)
    
    # Example feedback scenarios
    scenarios = [
        {
            "prompt": "What is the total amount of my invoices?",
            "response": "Your total invoice amount is $15,430 across 8 invoices.",
            "is_helpful": True,
            "category": "financial_query",
            "feedback": "Good response with clear financial summary"
        },
        {
            "prompt": "Show me cloud storage costs",
            "response": "Cloud storage typically costs $10-50 per month depending on storage size.",
            "is_helpful": False,
            "correction": "Should query actual database for specific cloud storage costs from invoice data, not provide generic pricing",
            "category": "pricing",
            "severity": 4
        },
        {
            "prompt": "Which invoices are overdue?",
            "response": "Results filtered for Vendor ID: V12345. You have 3 overdue invoices.",
            "is_helpful": False,
            "correction": "Never expose vendor IDs or other sensitive identifiers to users",
            "category": "security",
            "severity": 5
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"  Submitting feedback {i}/{len(scenarios)}...")
        
        success = feedback_manager.submit_feedback(
            original_prompt=scenario["prompt"],
            original_response=scenario["response"],
            is_helpful=scenario["is_helpful"],
            correction=scenario.get("correction"),
            improvement_suggestion=scenario.get("feedback"),
            category=scenario["category"],
            severity=scenario.get("severity", 1)
        )
        
        if success:
            print(f"    ✅ Feedback {i} stored successfully")
        else:
            print(f"    ❌ Feedback {i} failed to store")
    
    print("📊 Feedback submission demo complete")

def demo_similarity_search():
    """Demo similarity search"""
    print("\n🔹 Demo: Similarity Search")
    
    from feedback.manager import feedback_manager
    
    # Test queries
    test_queries = [
        "What are my total invoice amounts?",
        "How much did I spend on cloud services?", 
        "Show me overdue payments"
    ]
    
    for query in test_queries:
        print(f"\n  🔍 Searching for: '{query}'")
        
        similar_feedback = feedback_manager.get_relevant_feedback(query, limit=2)
        
        if similar_feedback:
            print(f"    Found {len(similar_feedback)} similar feedback items:")
            for j, feedback in enumerate(similar_feedback, 1):
                similarity = feedback.get("similarity_score", 0)
                category = feedback.get("developer_feedback", {}).get("category", "unknown")
                print(f"      {j}. Similarity: {similarity:.3f}, Category: {category}")
                print(f"         Original: '{feedback['original_prompt'][:50]}...'")
        else:
            print("    No similar feedback found")
    
    print("🔍 Similarity search demo complete")

def demo_prompt_enhancement():
    """Demo prompt enhancement"""
    print("\n🔹 Demo: Prompt Enhancement")
    
    from feedback.manager import feedback_manager
    
    test_prompt = "What is the cost of cloud storage?"
    
    print(f"  Original prompt: '{test_prompt}'")
    
    enhancement = feedback_manager.generate_feedback_prompt_enhancement(test_prompt)
    
    if enhancement:
        print("  ✅ Enhancement generated:")
        print("  " + "─" * 50)
        print(enhancement)
        print("  " + "─" * 50)
    else:
        print("  ℹ️ No enhancement available (no relevant feedback found)")
    
    print("🚀 Prompt enhancement demo complete")

def demo_analytics():
    """Demo analytics and statistics"""
    print("\n🔹 Demo: Analytics & Statistics")
    
    from feedback.manager import feedback_manager
    
    stats = feedback_manager.get_feedback_statistics()
    
    if "error" not in stats:
        print("  📊 Feedback Statistics:")
        print(f"    Total feedback: {stats.get('total_feedback', 0)}")
        print(f"    Helpful: {stats.get('helpful_feedback', 0)}")
        print(f"    Unhelpful: {stats.get('unhelpful_feedback', 0)}")
        print(f"    Unique vendors: {stats.get('unique_vendors', 0)}")
        
        categories = stats.get('categories', {})
        if categories:
            print("    Categories:")
            for category, count in categories.items():
                print(f"      {category}: {count}")
        
        # Calculate helpful rate
        total = stats.get('total_feedback', 0)
        helpful = stats.get('helpful_feedback', 0)
        if total > 0:
            helpful_rate = (helpful / total) * 100
            print(f"    Helpful rate: {helpful_rate:.1f}%")
    else:
        print(f"  ❌ Error getting statistics: {stats['error']}")
    
    print("📈 Analytics demo complete")

def demo_vector_store_health():
    """Demo vector store health check"""
    print("\n🔹 Demo: Vector Store Health Check")
    
    from feedback.vector_store import feedback_store
    
    health = feedback_store.health_check()
    
    print("  🏥 Health Status:")
    print(f"    Status: {health.get('status', 'unknown')}")
    print(f"    FAISS available: {health.get('faiss_available', False)}")
    print(f"    Gemini available: {health.get('gemini_available', False)}")
    print(f"    Collection exists: {health.get('collection_exists', False)}")
    
    if health.get("status") == "healthy":
        print("    ✅ All systems operational")
    else:
        print(f"    ⚠️ Issues detected: {health.get('message', 'Unknown')}")
    
    print("🏥 Health check demo complete")

def main():
    """Run the complete demo"""
    print("=" * 60)
    print("  FinOpsys ChatAI - Feedback System Demo")
    print("=" * 60)
    
    try:
        # Check if we can import the feedback system
        from feedback.manager import feedback_manager
        from feedback.vector_store import feedback_store
        
        print("✅ Feedback system modules imported successfully")
        
        # Run demos
        demo_vector_store_health()
        demo_feedback_submission() 
        demo_similarity_search()
        demo_prompt_enhancement()
        demo_analytics()
        
        print("\n" + "=" * 60)
        print("  🎉 Demo Complete!")
        print("=" * 60)
        print("""
Next Steps:
1. Start the application: streamlit run streamlit/src/app.py
2. Initialize the system in the sidebar
3. Set vendor context with a case ID
4. Try asking questions and providing feedback
5. Use the developer feedback portal to explore the system

The feedback system is now ready for use! 🚀
""")
        
    except ImportError as e:
        print(f"❌ Error importing feedback modules: {e}")
        print("\nPlease ensure:")
        print("1. Required packages are installed: pip install -r requirements.txt")
        print("2. FAISS is installed: pip install faiss-cpu")
        print("3. Environment variables are set in .env")
        print("\nTry running: python setup_feedback_system.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nPlease check:")
        print("1. FAISS is available and working correctly")
        print("2. GEMINI_API_KEY is set correctly")
        print("3. DEVELOPMENT_MODE=true in .env")

if __name__ == "__main__":
    main()
