# 🧠 FinOpsys ChatAI - Vector Feedback System

A comprehensive feedback system with semantic vector storage for improving AI responses through developer feedback.

## ✨ Architecture Overview

The feedback system implements a **vector-based architecture** using:

- **🔍 FAISS Vector Database**: Stores feedback with semantic embeddings using local FAISS index
- **🤖 Gemini Embeddings**: Converts prompts + responses to vectors for similarity search
- **🛠️ Development Mode**: Secure toggle between development and production modes
- **📊 Real-time Analytics**: Track feedback trends and system performance

## 🎯 Key Features

### 1. **Vector Storage & Retrieval**
- Semantic similarity search for relevant feedback
- Automatic prompt enhancement during inference
- Configurable similarity thresholds (default: 0.85)
- Efficient storage with metadata filtering

### 2. **Developer Feedback Portal**
```
🛠️ Developer Feedback Portal
├── 💬 Provide Feedback     - Rate and correct AI responses
├── 📋 Review Feedback      - Edit existing feedback entries  
├── 📊 Statistics          - Analytics and export tools
└── 🔍 Test Retrieval      - Test semantic similarity search
```

### 3. **Feedback Schema**
Each feedback entry contains:
```json
{
  "id": "uuid",
  "original_prompt": "What is the price of product X?",
  "original_response": "The price of product X is $199.",
  "developer_feedback": {
    "is_helpful": false,
    "correction": "It should respond with actual product pricing pulled from database. Avoid static pricing.",
    "improvement_suggestion": "Include confidence level and data source",
    "category": "pricing",
    "severity": 3
  },
  "embedding_vector": [...],
  "vendor_id": "V123",
  "case_id": "CASE456", 
  "sql_query": "SELECT * FROM...",
  "query_type": "item_query",
  "created_at": "2025-07-02T12:00:00Z",
  "updated_at": "2025-07-02T12:15:00Z"
}
```

## 🚀 Setup Guide

### Prerequisites

- Python 3.8+
- Gemini API key
- Snowflake credentials

### Quick Setup

1. **Run the setup script:**
   ```bash
   python setup_feedback_system.py
   ```

2. **Manual setup (if needed):**
   ```bash
   # Install dependencies
   pip install faiss-cpu>=1.7.4
   
   # FAISS will automatically create local index files
   # No external database setup required
   ```

### Environment Variables

Add to your `.env` file:

```env
# Feedback System Configuration
DEVELOPMENT_MODE=true                    # Enable/disable feedback UI
FAISS_INDEX_PATH=./feedback_data/faiss_index  # Path to FAISS index file
FEEDBACK_DATA_PATH=./feedback_data/feedback.json  # Path to feedback JSON data
FEEDBACK_SIMILARITY_THRESHOLD=0.85      # Similarity threshold (0.0-1.0)
FEEDBACK_MAX_RESULTS=5                  # Max similar feedback items
```

## 🎮 Usage Guide

### For Developers

1. **Enable Development Mode:**
   - Set `DEVELOPMENT_MODE=true` in `.env`
   - Restart the application

2. **Provide Feedback:**
   - Use the app normally, ask questions
   - Use "💬 Provide Feedback" to rate responses
   - Add corrections and improvement suggestions

3. **Review & Edit Feedback:**
   - Use "📋 Review Feedback" to see all entries
   - Edit feedback inline with real-time updates
   - Filter by vendor, category, or helpfulness

4. **Test Retrieval System:**
   - Use "🔍 Test Retrieval" to test similarity search
   - Adjust similarity thresholds 
   - See how prompts would be enhanced

### For Production

1. **Disable Development Mode:**
   ```env
   DEVELOPMENT_MODE=false
   ```

2. **Feedback Integration:**
   - Feedback data is still used for prompt enhancement
   - No UI shown to end users
   - Feedback runs in background during inference

## 🔄 Inference Workflow

When a user asks a question:

1. **Embedding Generation**: Convert user prompt to vector
2. **Similarity Search**: Find similar feedback in FAISS index
3. **Feedback Filtering**: Extract helpful corrections/suggestions  
4. **Prompt Enhancement**: Inject guidance into system prompt
5. **AI Response**: Generate enhanced response with feedback

### Example Enhanced Prompt

```text
You are a smart assistant. Use the following developer-provided reference feedback to improve your answer style or correctness.

Reference Feedback:
"""
In previous similar questions, developers noted that pricing responses should always pull live data from the product database instead of stating static prices.
"""

Now answer the user's question using this guideline.

User question: How much does cloud storage cost?
```

## 📊 Analytics & Monitoring

### Feedback Statistics
- Total feedback entries
- Helpful vs unhelpful ratios
- Category breakdowns
- Vendor-specific metrics

### Export Options
- JSON export of all feedback
- Filtered exports by vendor/category
- Timestamped data for analysis

### Health Monitoring
```python
from feedback.vector_store import feedback_store

# Check system health
health = feedback_store.health_check()
print(health)
# {
#   "status": "healthy",
#   "faiss_available": true,
#   "gemini_available": true,
#   "index_exists": true
# }
```

## 🔐 Security Features

### Development Mode Toggle
- **Development Mode ON**: Full feedback UI available
- **Production Mode**: Feedback UI hidden, data used passively

### Data Privacy
- Vendor-specific feedback isolation
- No sensitive IDs exposed in responses
- Secure session management

### Rate Limiting
- Feedback submission rate limits
- Vector search throttling
- API call optimization

## 🛠️ API Reference

### Feedback Manager

```python
from feedback.manager import feedback_manager

# Submit feedback
feedback_manager.submit_feedback(
    original_prompt="What are my total invoices?",
    original_response="You have 23 invoices",
    is_helpful=True,
    correction="Good response, but could include status breakdown",
    category="query_accuracy",
    severity=2
)

# Get relevant feedback for enhancement
relevant = feedback_manager.get_relevant_feedback("What are my invoices?", limit=3)

# Generate prompt enhancement
enhancement = feedback_manager.generate_feedback_prompt_enhancement(
    "What are my total invoices?"
)
```

### Vector Store

```python
from feedback.vector_store import feedback_store

# Search similar feedback
similar = feedback_store.search_similar_feedback(
    prompt="What is the price?",
    limit=5
)

# Get statistics
stats = feedback_store.get_feedback_statistics()

# Health check
health = feedback_store.health_check()
```

## 🧪 Testing

### Automated Tests

```bash
# Test vector store connection
python -c "from feedback.vector_store import feedback_store; print(feedback_store.health_check())"

# Test feedback submission  
python -c "
from feedback.manager import feedback_manager
feedback_manager.set_development_mode(True)
print(feedback_manager.submit_feedback('test', 'test', True))
"
```

### Manual Testing

1. **Vector Similarity**: Use "🔍 Test Retrieval" in the UI
2. **Feedback Flow**: Submit feedback and check for retrieval
3. **Prompt Enhancement**: Ask similar questions and verify enhancement

## 🔧 Configuration

### Similarity Threshold Tuning

```env
FEEDBACK_SIMILARITY_THRESHOLD=0.85  # Higher = more similar required
FEEDBACK_SIMILARITY_THRESHOLD=0.70  # Lower = more results included
```

### Performance Tuning

```env
FEEDBACK_MAX_RESULTS=5              # Limit results for performance
FAISS_INDEX_PATH=./feedback_data/faiss_index  # Local index for best performance
```

## 📈 Best Practices

### For Feedback Quality

1. **Be Specific**: Provide actionable corrections
2. **Categorize**: Use consistent categories (pricing, accuracy, security)
3. **Rate Severity**: 1=minor, 5=critical
4. **Include Context**: Add vendor/case context when relevant

### For System Performance

1. **Monitor Similarity Threshold**: Adjust based on feedback quality
2. **Regular Cleanup**: Archive old feedback periodically  
3. **Index Optimization**: Monitor FAISS performance
4. **Batch Operations**: Use bulk operations for large datasets

## 🚨 Troubleshooting

### Common Issues

**FAISS Index Issues:**
```bash
# Check if FAISS index files exist
ls -la feedback_data/

# Remove corrupted index (will recreate automatically)
rm -f feedback_data/faiss_index
rm -f feedback_data/feedback.json

# Check FAISS installation
python -c "import faiss; print('FAISS version:', faiss.__version__)"
```

**No Embeddings Generated:**
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota and usage limits
- Test with a simple embedding request

**Feedback Not Retrieving:**
- Lower similarity threshold temporarily
- Check if feedback was stored successfully
- Verify embedding generation is working

**UI Not Showing:**
- Ensure `DEVELOPMENT_MODE=true` in .env
- Restart the Streamlit application
- Check for import errors in logs

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

For issues and questions:

1. Check troubleshooting section above
2. Review application logs
3. Test individual components (FAISS, Gemini, etc.)
4. Verify environment configuration

---

*This feedback system implements the recommended architecture for vector-based feedback with semantic retrieval, providing a robust foundation for improving AI response quality through developer insights.*
