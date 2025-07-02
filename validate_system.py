#!/usr/bin/env python3
"""
System Validation and Testing Script
Validates that all components of FinOpSysAI are working correctly
"""

import os
import sys
import importlib
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemValidator:
    """Validates system components and configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
    
    def check_python_version(self):
        """Check Python version compatibility"""
        logger.info("Checking Python version...")
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.errors.append(f"Python 3.8+ required, found {version.major}.{version.minor}")
        else:
            self.passed.append(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    def check_dependencies(self):
        """Check required Python packages"""
        logger.info("Checking dependencies...")
        
        required_packages = [
            'streamlit',
            'snowflake.connector',
            'pandas',
            'pydantic',
            ('dotenv', 'python-dotenv')  # Special case: module name differs from package name
        ]
        
        optional_packages = [
            'google.generativeai',
            'ollama',
            'openpyxl'
        ]
        
        for package in required_packages:
            if isinstance(package, tuple):
                module_name, package_name = package
                try:
                    importlib.import_module(module_name)
                    self.passed.append(f"Required package: {package_name}")
                except ImportError:
                    self.errors.append(f"Missing required package: {package_name}")
            else:
                try:
                    importlib.import_module(package)
                    self.passed.append(f"Required package: {package}")
                except ImportError:
                    self.errors.append(f"Missing required package: {package}")
        
        for package in optional_packages:
            try:
                importlib.import_module(package)
                self.passed.append(f"Optional package: {package}")
            except ImportError:
                self.warnings.append(f"Missing optional package: {package}")
    
    def check_file_structure(self):
        """Check project file structure"""
        logger.info("Checking file structure...")
        
        required_files = [
            'streamlit/src/app.py',
            'utils/error_handler.py',
            'utils/query_validator.py',
            'utils/query_optimizer.py',
            'config.py',
            'column_reference_loader.py',
            'requirements.txt',
            '.env.example'        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                self.passed.append(f"File exists: {file_path}")
            else:
                self.errors.append(f"Missing file: {file_path}")
    
    def check_environment_template(self):
        """Check environment template"""
        logger.info("Checking environment template...")
        
        env_example = Path('.env.example')
        if not env_example.exists():
            self.errors.append("Missing .env.example file")
            return
        
        required_vars = [
            'SNOWFLAKE_ACCOUNT',
            'SNOWFLAKE_USER',
            'SNOWFLAKE_PASSWORD',
            'SNOWFLAKE_WAREHOUSE',
            'SNOWFLAKE_DATABASE',
            'GEMINI_API_KEY',
            'DEFAULT_PROVIDER',
            'DEFAULT_MODEL'
        ]
        
        content = env_example.read_text()
        for var in required_vars:
            if var in content:
                self.passed.append(f"Environment variable template: {var}")
            else:
                self.warnings.append(f"Missing environment variable template: {var}")
    
    def check_configuration(self):
        """Check configuration module"""
        logger.info("Checking configuration...")
        
        try:
            from config import Config
            config = Config()
            
            # Test validation (will raise if required vars are missing)
            try:
                config.validate_config()
                self.passed.append("Configuration validation works")
            except ValueError as e:
                self.warnings.append(f"Configuration validation: {str(e)}")
            
        except ImportError as e:
            self.errors.append(f"Cannot import config module: {str(e)}")
    
    def check_utils_modules(self):
        """Check utility modules"""
        logger.info("Checking utility modules...")
        
        utils_modules = [
            ('utils.error_handler', ['AppError', 'error_handler']),
            ('utils.query_validator', ['QueryValidator']),
            ('utils.query_optimizer', ['QueryOptimizer'])
        ]
        
        for module_name, expected_classes in utils_modules:
            try:
                module = importlib.import_module(module_name)
                
                for class_name in expected_classes:
                    if hasattr(module, class_name):
                        self.passed.append(f"Module {module_name} has {class_name}")
                    else:
                        self.errors.append(f"Module {module_name} missing {class_name}")
                        
            except ImportError as e:
                self.errors.append(f"Cannot import {module_name}: {str(e)}")
    
    def check_app_syntax(self):
        """Check main application syntax"""
        logger.info("Checking application syntax...")
        
        app_path = Path('streamlit/src/app.py')
        if not app_path.exists():
            self.errors.append("Main application file not found")
            return
        
        try:
            # Try to compile the file to check for syntax errors
            with open(app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, str(app_path), 'exec')
            self.passed.append("Main application syntax is valid")
            
        except SyntaxError as e:
            self.errors.append(f"Syntax error in main application: {str(e)}")
        except Exception as e:
            self.warnings.append(f"Could not validate main application: {str(e)}")
    
    def run_validation(self):
        """Run all validation checks"""
        logger.info("Starting system validation...")
        
        self.check_python_version()
        self.check_dependencies()
        self.check_file_structure()
        self.check_environment_template()
        self.check_configuration()
        self.check_utils_modules()
        self.check_app_syntax()
        
        # Print results
        print("\n" + "="*60)
        print("SYSTEM VALIDATION RESULTS")
        print("="*60)
        
        if self.passed:
            print(f"\nPASSED ({len(self.passed)}):")
            for item in self.passed:
                print(f"   * {item}")
        
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for item in self.warnings:
                print(f"   ! {item}")
        
        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for item in self.errors:
                print(f"   X {item}")
        
        print("\n" + "="*60)
        
        if self.errors:
            print("VALIDATION FAILED - Please fix the errors above")
            return False
        elif self.warnings:
            print("VALIDATION PASSED WITH WARNINGS - Some optional features may not work")
            return True
        else:
            print("VALIDATION PASSED - System is ready for deployment")
            return True

def main():
    """Main validation function"""
    print("FinOpSysAI - System Validator")
    print("="*60)
    
    validator = SystemValidator()
    success = validator.run_validation()
    
    if success:
        print("\nNEXT STEPS:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your actual credentials in .env")
        print("3. Run: streamlit run streamlit/src/app.py")
        print("4. Open http://localhost:8501 in your browser")
        
        if validator.warnings:
            print("\nTO ENABLE ALL FEATURES:")
            print("   pip install google-generativeai ollama openpyxl")
    else:
        print("\nPlease fix the errors above before proceeding")
        sys.exit(1)

if __name__ == "__main__":
    main()
