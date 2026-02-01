"""
Settings module for managing environment variables and configurations
"""
import os
from pathlib import Path

# Set SSL certificate environment variables BEFORE loading dotenv and other imports
# This is critical for Zscaler proxy environments
ssl_cert_path = r"C:\Users\Youngki\AppData\Roaming\ZscalerRootCA.pem"
if os.path.exists(ssl_cert_path):
    os.environ['REQUESTS_CA_BUNDLE'] = ssl_cert_path
    os.environ['CURL_CA_BUNDLE'] = ssl_cert_path
    os.environ['SSL_CERT_FILE'] = ssl_cert_path

    # Also append Zscaler cert to certifi's CA bundle
    try:
        import certifi
        certifi_path = certifi.where()

        # Read Zscaler cert
        with open(ssl_cert_path, 'r') as f:
            zscaler_cert = f.read()

        # Check if already appended
        with open(certifi_path, 'r') as f:
            existing_certs = f.read()

        if 'Zscaler Root CA' not in existing_certs and zscaler_cert.strip() not in existing_certs:
            # Append Zscaler cert to certifi bundle
            with open(certifi_path, 'a') as f:
                f.write('\n# Zscaler Root CA (auto-added)\n')
                f.write(zscaler_cert)
                if not zscaler_cert.endswith('\n'):
                    f.write('\n')
    except Exception as e:
        # If this fails, continue anyway - env vars might be enough
        pass

from dotenv import load_dotenv
from typing import Optional


class Settings:
    """Configuration settings loaded from environment variables"""
    
    def __init__(self):
        # Load .env file
        # NOTE: .env는 프로젝트 루트(= settings.py가 있는 폴더)에 두는 것을 전제로 함
        env_path = Path(__file__).resolve().parent / '.env'
        load_dotenv(env_path)

        # SSL Certificate Settings (for Zscaler proxy environments)
        # Set SSL certificate paths from environment variables
        ssl_cert_file = os.getenv('SSL_CERT_FILE')
        requests_ca_bundle = os.getenv('REQUESTS_CA_BUNDLE')
        curl_ca_bundle = os.getenv('CURL_CA_BUNDLE')

        if ssl_cert_file:
            os.environ['SSL_CERT_FILE'] = ssl_cert_file
        if requests_ca_bundle:
            os.environ['REQUESTS_CA_BUNDLE'] = requests_ca_bundle
        if curl_ca_bundle:
            os.environ['CURL_CA_BUNDLE'] = curl_ca_bundle

        # GCP Settings
        self.gcp_project_id: str = os.getenv('GCP_PROJECT_ID', '')
        self.gcp_credentials_path: str = os.getenv('GCP_CREDENTIALS_PATH', '')

        # Document AI Settings
        self.documentai_processor_id: str = os.getenv('DOCUMENTAI_PROCESSOR_ID', '')
        self.documentai_location: str = os.getenv('DOCUMENTAI_LOCATION', 'us')
        # Document AI sync process_document limit (bytes). Default 20MB.
        # Large files should be handled via Document AI Batch API or pre-processing (compress/split).
        self.documentai_max_sync_bytes: int = int(os.getenv('DOCUMENTAI_MAX_SYNC_BYTES', str(20 * 1024 * 1024)))

        # GCS Input Settings
        self.gcs_input_path: Optional[str] = os.getenv('GCS_INPUT_PATH')
        self.gcs_input_folder: Optional[str] = os.getenv('GCS_INPUT_FOLDER')
        # Batch mode (bucket-wide) input settings
        # 기본값은 비워두고(안전), env.template에서 명시적으로 설정하도록 유도
        # 예: 버킷 전체 처리 -> GCS_INPUT_BUCKET=input-data
        # 예: 버킷 kia-demo의 input-data/ prefix만 -> GCS_INPUT_BUCKET=kia-demo, GCS_INPUT_PREFIX=input-data/
        self.gcs_input_bucket: str = os.getenv('GCS_INPUT_BUCKET', '')
        self.gcs_input_prefix: str = os.getenv('GCS_INPUT_PREFIX', '')

        # GCS Output Settings
        self.gcs_output_bucket: str = os.getenv('GCS_OUTPUT_BUCKET', '')
        self.gcs_output_path: str = os.getenv('GCS_OUTPUT_PATH', 'output/metadata/')

        # Set Google credentials environment variable
        if self.gcp_credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.gcp_credentials_path
    
    def validate(self) -> bool:
        """Validate that all required settings are present"""
        required_fields = [
            ('GCP_PROJECT_ID', self.gcp_project_id),
            ('GCP_CREDENTIALS_PATH', self.gcp_credentials_path),
            ('DOCUMENTAI_PROCESSOR_ID', self.documentai_processor_id),
            ('GCS_OUTPUT_BUCKET', self.gcs_output_bucket),
        ]
        
        missing_fields = [name for name, value in required_fields if not value]
        
        if missing_fields:
            print(f"[ERROR] Missing required environment variables: {', '.join(missing_fields)}")
            return False
        
        # Check if at least one input method is specified
        # - single: GCS_INPUT_PATH
        # - legacy batch: GCS_INPUT_FOLDER
        # - bucket-wide batch: GCS_INPUT_BUCKET (default: input-data)
        if not self.gcs_input_path and not self.gcs_input_folder and not self.gcs_input_bucket:
            print("[ERROR] Either GCS_INPUT_PATH, GCS_INPUT_FOLDER, or GCS_INPUT_BUCKET must be specified")
            return False
        
        # Check if credentials file exists
        if not os.path.exists(self.gcp_credentials_path):
            print(f"[ERROR] Credentials file not found: {self.gcp_credentials_path}")
            return False
        
        print("[OK] All required settings are valid")
        return True
    
    def get_processor_name(self) -> str:
        """Get the full processor name for Document AI"""
        return f"projects/{self.gcp_project_id}/locations/{self.documentai_location}/processors/{self.documentai_processor_id}"
    
    def parse_gcs_uri(self, gcs_uri: str) -> tuple:
        """Parse GCS URI into bucket and blob name
        
        Args:
            gcs_uri: GCS URI (e.g., gs://bucket-name/path/to/file)
            
        Returns:
            Tuple of (bucket_name, blob_name)
        """
        if not gcs_uri.startswith('gs://'):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        parts = gcs_uri[5:].split('/', 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ''
        
        return bucket_name, blob_name
    
    def __repr__(self) -> str:
        return f"Settings(project={self.gcp_project_id}, location={self.documentai_location})"
