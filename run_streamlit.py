#!/usr/bin/env python3
"""
Simple script to run the FinOpSysAI Streamlit app
"""

import subprocess
import sys
import os

def main():
    # Change to the correct directory
    app_dir = os.path.join(os.path.dirname(__file__), 'streamlit')
    app_file = os.path.join(app_dir, 'src', 'app.py')
    
    if not os.path.exists(app_file):
        print(f"❌ App file not found: {app_file}")
        return 1
    
    print("🚀 Starting FinOpSysAI Streamlit App...")
    print(f"📁 App location: {app_file}")
    print("🌐 Once started, open: http://localhost:8501")
    print("-" * 50)
    
    try:
        # Run streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", app_file, "--server.port=8501", "--server.address=localhost"]
        subprocess.run(cmd, cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
