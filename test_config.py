"""
Test script to validate configuration and GCP connection
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config import Settings
from utils.logger import setup_logger
from utils.gcs_utils import GCSClient


def test_configuration():
    """Test configuration loading"""
    print("\n" + "="*60)
    print("Testing Configuration")
    print("="*60)
    
    try:
        settings = Settings()
        settings.display_config()
        print("✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {str(e)}")
        return False


def test_gcs_connection(settings: Settings):
    """Test GCS connection"""
    print("\n" + "="*60)
    print("Testing GCS Connection")
    print("="*60)
    
    try:
        gcs_client = GCSClient(
            credentials_path=settings.gcp_credentials_path,
            project_id=settings.gcp_project_id
        )
        
        # 버킷 존재 확인
        bucket_name = settings.gcs_output_bucket
        bucket = gcs_client.client.bucket(bucket_name)
        
        if bucket.exists():
            print(f"✓ Successfully connected to GCS bucket: {bucket_name}")
            return True
        else:
            print(f"✗ Bucket does not exist: {bucket_name}")
            return False
            
    except Exception as e:
        print(f"✗ GCS connection failed: {str(e)}")
        return False


def test_input_file(settings: Settings):
    """Test if input file exists in GCS"""
    print("\n" + "="*60)
    print("Testing Input File")
    print("="*60)
    
    if not settings.gcs_input_path:
        print("ℹ No input file specified (GCS_INPUT_PATH not set)")
        return True
    
    try:
        gcs_client = GCSClient(
            credentials_path=settings.gcp_credentials_path,
            project_id=settings.gcp_project_id
        )
        
        if gcs_client.file_exists(settings.gcs_input_path):
            print(f"✓ Input file exists: {settings.gcs_input_path}")
            
            # 파일 정보 출력
            file_info = gcs_client.get_file_info(settings.gcs_input_path)
            print(f"  - Size: {file_info['size']:,} bytes")
            print(f"  - Content Type: {file_info['content_type']}")
            print(f"  - Created: {file_info['created']}")
            
            return True
        else:
            print(f"✗ Input file does not exist: {settings.gcs_input_path}")
            print("  Please upload a file to GCS first")
            return False
            
    except Exception as e:
        print(f"✗ Error checking input file: {str(e)}")
        return False


def main():
    """Run all tests"""
    logger = setup_logger(level='INFO')
    
    print("\n" + "="*60)
    print("Kia Metadata Generator - Configuration Test")
    print("="*60)
    
    # 테스트 실행
    results = []
    
    # 1. 설정 테스트
    config_ok = test_configuration()
    results.append(("Configuration", config_ok))
    
    if not config_ok:
        print("\n✗ Configuration failed. Please fix .env file first.")
        return 1
    
    settings = Settings()
    
    # 2. GCS 연결 테스트
    gcs_ok = test_gcs_connection(settings)
    results.append(("GCS Connection", gcs_ok))
    
    # 3. 입력 파일 테스트
    input_ok = test_input_file(settings)
    results.append(("Input File", input_ok))
    
    # 결과 요약
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<30} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ All tests passed! Ready to run main.py")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
