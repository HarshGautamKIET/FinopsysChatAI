#!/usr/bin/env python3
"""
Startup script for FinOpSysAI
Validates system and launches the application
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main startup function"""
    print("🚀 FinOpSysAI - Startup Script")
    print("="*60)
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("📝 Please copy .env.example to .env and fill in your credentials:")
        print("   cp .env.example .env")
        print("   # Then edit .env with your actual database credentials")
        return False
    
    # Run validation first
    print("🔍 Running system validation...")
    try:
        result = subprocess.run([sys.executable, 'validate_system.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ System validation passed!")
    except subprocess.CalledProcessError as e:
        print("❌ System validation failed!")
        print(e.stdout)
        print(e.stderr)
        return False
    
    # Launch the application
    print("\n💼 Launching FinOpSysAI...")
    print("📱 The application will open in your browser at: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the application")
    print("="*60)
    
    try:
        # Make sure we're in the project root directory
        os.chdir(Path(__file__).parent)
        
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'streamlit/src/app.py',
            '--server.port', '8501',
            '--server.address', 'localhost'
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
