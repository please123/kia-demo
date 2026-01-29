"""
Google Cloud Storage helper utilities
"""
from google.cloud import storage
from typing import List, Optional
import logging


class GCSHelper:
    """Helper class for GCS operations"""
    
    def __init__(self, project_id: str):
        """Initialize GCS client
        
        Args:
            project_id: GCP project ID
        """
        self.client = storage.Client(project=project_id)
        self.logger = logging.getLogger('kia_metadata.gcs')
    
    def list_blobs(self, bucket_name: str, prefix: str = '', suffix: str = '') -> List[str]:
        """List blobs in a GCS bucket with optional prefix and suffix filters
        
        Args:
            bucket_name: Name of the GCS bucket
            prefix: Prefix filter for blob names
            suffix: Suffix filter for blob names (e.g., '.pptx')
            
        Returns:
            List of GCS URIs
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            
            blob_uris = []
            for blob in blobs:
                # Skip directories
                if blob.name.endswith('/'):
                    continue
                
                # Apply suffix filter
                if suffix and not blob.name.endswith(suffix):
                    continue
                
                blob_uris.append(f"gs://{bucket_name}/{blob.name}")
            
            self.logger.info(f"Found {len(blob_uris)} files in gs://{bucket_name}/{prefix}")
            return blob_uris
        
        except Exception as e:
            self.logger.error(f"Error listing blobs: {str(e)}")
            raise
    
    def upload_from_string(self, bucket_name: str, blob_name: str, content: str, 
                          content_type: str = 'text/csv') -> str:
        """Upload string content to GCS
        
        Args:
            bucket_name: Name of the GCS bucket
            blob_name: Name of the blob (file path in GCS)
            content: String content to upload
            content_type: MIME type of the content
            
        Returns:
            GCS URI of the uploaded file
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.upload_from_string(content, content_type=content_type)
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            self.logger.info(f"Uploaded file to {gcs_uri}")
            return gcs_uri
        
        except Exception as e:
            self.logger.error(f"Error uploading to GCS: {str(e)}")
            raise
    
    def upload_from_filename(self, bucket_name: str, blob_name: str, 
                            filename: str) -> str:
        """Upload a file to GCS
        
        Args:
            bucket_name: Name of the GCS bucket
            blob_name: Name of the blob (file path in GCS)
            filename: Local file path to upload
            
        Returns:
            GCS URI of the uploaded file
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.upload_from_filename(filename)
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            self.logger.info(f"Uploaded file to {gcs_uri}")
            return gcs_uri
        
        except Exception as e:
            self.logger.error(f"Error uploading file to GCS: {str(e)}")
            raise
    
    def blob_exists(self, bucket_name: str, blob_name: str) -> bool:
        """Check if a blob exists in GCS
        
        Args:
            bucket_name: Name of the GCS bucket
            blob_name: Name of the blob
            
        Returns:
            True if blob exists, False otherwise
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.exists()
        
        except Exception as e:
            self.logger.error(f"Error checking blob existence: {str(e)}")
            return False
