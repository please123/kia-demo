"""
Google Gemini API Connection Test
Tests basic connectivity and text generation with Gemini API
"""
import os
import sys
from pathlib import Path

# Add project root to path to use settings module
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import settings to handle SSL certificates (important for Zscaler proxy environments)
try:
    from settings import Settings
    # Initialize settings to configure SSL certificates
    settings = Settings()
    print("[INFO] SSL certificates configured from settings.py")
except Exception as e:
    print(f"[WARNING] Could not load settings: {e}")
    print("[INFO] Proceeding without custom SSL configuration")

import google.generativeai as genai
from dotenv import load_dotenv


def test_gemini_connection():
    """Test Gemini API connection and basic text generation"""

    print("=" * 60)
    print("Google Gemini API Connection Test")
    print("=" * 60)

    # Load environment variables
    env_path = Path(__file__).resolve().parent / '.env'
    load_dotenv(env_path)

    # Get API key from environment
    api_key = os.getenv('GOOGLE_API_KEY')

    if not api_key:
        print("\n[ERROR] GOOGLE_API_KEY not found in .env file")
        print("Please add GOOGLE_API_KEY=your_api_key to your .env file")
        return False

    print(f"\n[OK] API Key found: {api_key[:10]}...{api_key[-4:]}")

    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        print("[OK] Gemini API configured successfully")

        # List available models
        print("\n[INFO] Listing available models...")
        available_models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
                print(f"  - {model.name}")

        if not available_models:
            print("[WARNING] No models with generateContent support found")
            return False

        # Test text generation with Gemini
        print("\n[TEST] Testing text generation with Gemini Pro...")
        model = genai.GenerativeModel('gemini-pro')

        test_prompt = "Say 'Hello, this is a test from Kia Metadata Generator project!' in Korean."
        print(f"[PROMPT] {test_prompt}")

        response = model.generate_content(test_prompt)

        print("\n[RESPONSE]")
        print("-" * 60)
        print(response.text)
        print("-" * 60)

        # Check if response is valid
        if response.text:
            print("\n[SUCCESS] Gemini API connection test passed!")
            return True
        else:
            print("\n[ERROR] Response text is empty")
            return False

    except Exception as e:
        print(f"\n[ERROR] Connection test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_gemini_with_system_instruction():
    """Test Gemini with system instruction (for advanced use)"""

    print("\n" + "=" * 60)
    print("Testing Gemini with System Instruction")
    print("=" * 60)

    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("[SKIP] API key not available")
            return False

        genai.configure(api_key=api_key)

        # Create model with system instruction
        model = genai.GenerativeModel(
            'gemini-pro',
            system_instruction="You are a helpful assistant for document metadata extraction. Respond concisely and professionally."
        )

        test_prompt = "What kind of metadata can be extracted from PDF documents?"
        print(f"[PROMPT] {test_prompt}")

        response = model.generate_content(test_prompt)

        print("\n[RESPONSE]")
        print("-" * 60)
        print(response.text)
        print("-" * 60)

        print("\n[SUCCESS] System instruction test passed!")
        return True

    except Exception as e:
        print(f"\n[ERROR] System instruction test failed: {str(e)}")
        return False


def main():
    """Main entry point"""

    # Test 1: Basic connection
    test1_success = test_gemini_connection()

    # Test 2: System instruction (optional)
    if test1_success:
        test2_success = test_gemini_with_system_instruction()
    else:
        test2_success = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Basic Connection Test: {'PASSED' if test1_success else 'FAILED'}")
    print(f"System Instruction Test: {'PASSED' if test2_success else 'FAILED'}")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if test1_success else 1)


if __name__ == '__main__':
    main()
