"""
Simple test script to validate the setup
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config import Settings
        print("✅ Config module imported")
    except Exception as e:
        print(f"❌ Failed to import config: {e}")
        return False
    
    try:
        from utils import setup_logger, GCSHelper
        print("✅ Utils module imported")
    except Exception as e:
        print(f"❌ Failed to import utils: {e}")
        return False
    
    try:
        from modules import TextExtractor, MetadataGenerator, CSVHandler
        print("✅ Modules imported")
    except Exception as e:
        print(f"❌ Failed to import modules: {e}")
        return False
    
    return True

def test_settings():
    """Test if settings can be loaded"""
    print("\nTesting settings...")
    
    try:
        from config import Settings
        settings = Settings()
        print("✅ Settings loaded")
        
        # Check if .env file exists
        env_file = project_root / '.env'
        if not env_file.exists():
            print("⚠️  Warning: .env file not found. Please create one from .env.template")
            return False
        
        print(f"   Project ID: {settings.gcp_project_id}")
        print(f"   Processor ID: {settings.documentai_processor_id}")
        print(f"   Location: {settings.documentai_location}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return False

def test_credentials():
    """Test if GCP credentials exist"""
    print("\nTesting credentials...")
    
    from config import Settings
    settings = Settings()
    
    cred_path = Path(settings.gcp_credentials_path)
    if cred_path.exists():
        print(f"✅ Credentials file found at {cred_path}")
        return True
    else:
        print(f"⚠️  Warning: Credentials file not found at {cred_path}")
        print("   Please download your GCP service account key and save it to credentials/")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Kia Metadata Generator - Setup Validation")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Settings", test_settings()))
    results.append(("Credentials", test_credentials()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to go!")
        print("\nNext steps:")
        print("1. Upload your document to GCS")
        print("2. Set GCS_INPUT_PATH in .env file")
        print("3. Run: python main.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nSetup checklist:")
        print("1. Copy .env.template to .env and fill in your values")
        print("2. Download GCP service account key to credentials/gcp-service-account.json")
        print("3. Create a Document AI processor in GCP Console")
        print("4. Create a GCS bucket and folders for input/output")

if __name__ == '__main__':
    main()
