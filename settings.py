"""
Settings module for managing environment variables and configurations
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class Settings:
    """Configuration settings loaded from environment variables"""
    
    def __init__(self):
        # Load .env file
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        # GCP Settings
        self.gcp_project_id: str = os.getenv('GCP_PROJECT_ID', '')
        self.gcp_credentials_path: str = os.getenv('GCP_CREDENTIALS_PATH', '')
        
        # Document AI Settings
        self.documentai_processor_id: str = os.getenv('DOCUMENTAI_PROCESSOR_ID', '')
        self.documentai_location: str = os.getenv('DOCUMENTAI_LOCATION', 'us')
        
        # GCS Input Settings
        self.gcs_input_path: Optional[str] = os.getenv('GCS_INPUT_PATH')
        self.gcs_input_folder: Optional[str] = os.getenv('GCS_INPUT_FOLDER')
        
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
            print(f"❌ Missing required environment variables: {', '.join(missing_fields)}")
            return False
        
        # Check if at least one input method is specified
        if not self.gcs_input_path and not self.gcs_input_folder:
            print("❌ Either GCS_INPUT_PATH or GCS_INPUT_FOLDER must be specified")
            return False
        
        # Check if credentials file exists
        if not os.path.exists(self.gcp_credentials_path):
            print(f"❌ Credentials file not found: {self.gcp_credentials_path}")
            return False
        
        print("✅ All required settings are valid")
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
