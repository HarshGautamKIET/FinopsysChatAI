#!/usr/bin/env python3
"""
FinOpsys ChatAI - Feedback System Setup Script
This script helps set up the vector-based feedback system with FAISS and Gemini embeddings.
"""

import os
import sys
import subprocess
import json
import requests
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n🔹 Step {step}: {description}")

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python version")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_requirements():
    """Install required packages"""
    print_step(2, "Installing required packages")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                      check=True, capture_output=True, text=True)
        print("✅ Required packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_faiss_installation():
    """Check if FAISS is installed"""
    print_step(3, "Checking FAISS installation")
    
    try:
        import faiss
        print("✅ FAISS is installed")
        return True
    except ImportError:
        print("❌ FAISS not installed")
        print("Installing FAISS...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "faiss-cpu"], 
                          check=True, capture_output=True, text=True)
            print("✅ FAISS installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install FAISS: {e}")
            return False

def setup_feedback_directories():
    """Setup directories for FAISS index and feedback data"""
    print_step(4, "Setting up feedback directories")
    
    # Create directories for FAISS index and feedback data
    feedback_dir = Path("feedback_data")
    if not feedback_dir.exists():
        feedback_dir.mkdir(parents=True)
        print(f"✅ Created directory: {feedback_dir}")
    else:
        print(f"✅ Directory already exists: {feedback_dir}")
    
    # Initialize empty feedback data file if it doesn't exist
    feedback_file = feedback_dir / "feedback.json"
    if not feedback_file.exists():
        with open(feedback_file, 'w') as f:
            json.dump([], f)
        print(f"✅ Created feedback data file: {feedback_file}")
    
    return True

def check_environment_variables():
    """Check if required environment variables are set"""
    print_step(5, "Checking environment variables")
    
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please create .env file from .env.example")
        return False
    
    # Read .env file
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    required_vars = [
        'SNOWFLAKE_ACCOUNT',
        'SNOWFLAKE_USER',
        'SNOWFLAKE_PASSWORD',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not env_vars.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Check feedback system variables
    feedback_vars = {
        'DEVELOPMENT_MODE': env_vars.get('DEVELOPMENT_MODE', 'false'),
        'FAISS_INDEX_PATH': env_vars.get('FAISS_INDEX_PATH', './feedback_data/faiss_index'),
        'FEEDBACK_DATA_PATH': env_vars.get('FEEDBACK_DATA_PATH', './feedback_data/feedback.json'),
        'FEEDBACK_SIMILARITY_THRESHOLD': env_vars.get('FEEDBACK_SIMILARITY_THRESHOLD', '0.85'),
    }
    
    print("✅ Required environment variables are set")
    print("📋 Feedback system configuration:")
    for key, value in feedback_vars.items():
        print(f"   {key}: {value}")
    
    return True

def test_vector_store_connection():
    """Test connection to vector store"""
    print_step(6, "Testing vector store connection")
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from feedback.vector_store import feedback_store
        
        # Test health check
        health = feedback_store.health_check()
        if health["status"] == "healthy":
            print("✅ Vector store connection successful")
            print(f"   FAISS available: {health.get('faiss_available', False)}")
            print(f"   Gemini available: {health.get('gemini_available', False)}")
            print(f"   Index exists: {health.get('index_exists', False)}")
            print(f"   Data exists: {health.get('data_exists', False)}")
            return True
        else:
            print(f"❌ Vector store connection failed: {health.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing vector store: {str(e)}")
        return False

def test_feedback_system():
    """Test the feedback system end-to-end"""
    print_step(7, "Testing feedback system")
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from feedback.manager import feedback_manager
        
        # Enable development mode
        feedback_manager.set_development_mode(True)
        
        # Test feedback submission
        test_prompt = "What is the total amount of invoices?"
        test_response = "The total amount is $45,230 across 15 invoices."
        
        success = feedback_manager.submit_feedback(
            original_prompt=test_prompt,
            original_response=test_response,
            is_helpful=True,
            correction="This is a test feedback entry",
            category="test",
            severity=1
        )
        
        if success:
            print("✅ Feedback submission test successful")
            
            # Test feedback retrieval
            similar = feedback_manager.get_relevant_feedback(test_prompt, limit=1)
            if similar:
                print("✅ Feedback retrieval test successful")
                return True
            else:
                print("⚠️ Feedback retrieval returned no results (this is normal for first run)")
                return True
        else:
            print("❌ Feedback submission test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing feedback system: {str(e)}")
        return False

def create_sample_feedback():
    """Create sample feedback entries for demonstration"""
    print_step(8, "Creating sample feedback entries")
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from feedback.manager import feedback_manager
        
        # Enable development mode
        feedback_manager.set_development_mode(True)
        
        sample_feedback = [
            {
                "prompt": "What is the price of cloud storage?",
                "response": "Cloud storage pricing varies by vendor and usage.",
                "is_helpful": False,
                "correction": "Should provide specific pricing from actual database records, not generic responses.",
                "category": "pricing",
                "severity": 3
            },
            {
                "prompt": "How many invoices do I have?",
                "response": "You have 23 invoices in the system.",
                "is_helpful": True,
                "improvement_suggestion": "Could include additional context like date range or status breakdown.",
                "category": "query_accuracy",
                "severity": 1
            },
            {
                "prompt": "Show me overdue invoices",
                "response": "Here are your overdue invoices with specific vendor IDs visible.",
                "is_helpful": False,
                "correction": "Never show vendor IDs or other sensitive identifiers to users.",
                "category": "security",
                "severity": 5
            }
        ]
        
        created_count = 0
        for feedback in sample_feedback:
            success = feedback_manager.submit_feedback(
                original_prompt=feedback["prompt"],
                original_response=feedback["response"],
                is_helpful=feedback["is_helpful"],
                correction=feedback.get("correction"),
                improvement_suggestion=feedback.get("improvement_suggestion"),
                category=feedback["category"],
                severity=feedback["severity"]
            )
            if success:
                created_count += 1
        
        print(f"✅ Created {created_count}/{len(sample_feedback)} sample feedback entries")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample feedback: {str(e)}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print_header("🎉 Setup Complete!")
    
    print("""
Next Steps:

1. 🚀 Start the application:
   streamlit run streamlit/src/app.py

2. 🔧 Initialize the system:
   - Click "🚀 Initialize System" in the sidebar
   - Wait for AI models and database connection

3. 🏢 Set vendor context:
   - Click "📋 Load Available Cases"
   - Select a case ID from the dropdown
   - Click "🔒 Set Vendor Context"

4. 🛠️ Access Developer Feedback Portal:
   - Look for "🛠️ Developer Feedback Portal" in the sidebar
   - Only visible when DEVELOPMENT_MODE=true
   - Use it to:
     • Provide feedback on AI responses
     • Review existing feedback
     • View feedback statistics
     • Test similarity retrieval

5. 🧪 Test the feedback system:
   - Ask some questions and get AI responses
   - Use "💬 Provide Feedback" to give developer feedback
   - Try "🔍 Test Retrieval" to see how similar queries are found

Key Features:
✅ Vector-based feedback storage with FAISS
✅ Semantic similarity search using Gemini embeddings
✅ Prompt enhancement with developer feedback
✅ Development/production mode toggle
✅ Comprehensive feedback analytics

Happy analyzing! 🎯
""")

def main():
    """Main setup function"""
    print_header("FinOpsys ChatAI - Feedback System Setup")
    
    all_tests_passed = True
    
    # Run setup steps
    if not check_python_version():
        all_tests_passed = False
    
    if not install_requirements():
        all_tests_passed = False
    
    if not check_faiss_installation():
        all_tests_passed = False
    
    if not setup_feedback_directories():
        all_tests_passed = False
    
    if not check_environment_variables():
        all_tests_passed = False
    
    if not test_vector_store_connection():
        all_tests_passed = False
        print("\n⚠️ Vector store connection failed. Check:")
        print("1. FAISS is properly installed")
        print("2. FAISS_INDEX_PATH in .env is accessible")
        print("3. GEMINI_API_KEY is set for embeddings")
    
    if not test_feedback_system():
        all_tests_passed = False
    
    if not create_sample_feedback():
        all_tests_passed = False
    
    # Print results
    if all_tests_passed:
        print_next_steps()
    else:
        print_header("❌ Setup Issues Detected")
        print("""
Some setup steps failed. Please review the errors above and:

1. Fix any missing environment variables in .env
2. Ensure FAISS is properly installed (pip install faiss-cpu)
3. Verify Gemini API key is valid
4. Check that all required packages are installed
5. Ensure feedback directories are writable

You can re-run this script after fixing the issues.
""")
        sys.exit(1)

if __name__ == "__main__":
    main()
