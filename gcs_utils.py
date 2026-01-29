"""
Google Cloud Storage helper utilities
"""
from google.cloud import storage
from typing import List, Optional
import logging
from google.api_core import exceptions as gcp_exceptions


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

        except gcp_exceptions.Forbidden as e:
            # High-signal guidance for common IAM misconfig
            self.logger.error(
                "Error listing blobs (403 Forbidden). "
                "The service account used by GOOGLE_APPLICATION_CREDENTIALS likely lacks "
                "permission 'storage.objects.list' on the bucket.\n"
                f"- bucket: gs://{bucket_name}\n"
                f"- prefix: {prefix or '(empty)'}\n"
                "Fix: grant one of these roles on the bucket to the service account:\n"
                "- roles/storage.objectViewer (minimum for list/read)\n"
                "- roles/storage.admin (broader)\n"
                "Also double-check bucket vs prefix:\n"
                "- If your bucket is 'kia-demo' and folder is 'input-data/', set "
                "GCS_INPUT_BUCKET=kia-demo and GCS_INPUT_PREFIX=input-data/.\n"
            )
            raise

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

    def get_blob_size(self, gcs_uri: str) -> int:
        """Get blob size (bytes) for a gs:// URI."""
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        parts = gcs_uri[5:].split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ""
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.reload()
        return int(getattr(blob, "size", 0) or 0)

    def read_file(self, gcs_uri: str) -> str:
        """Read file content from GCS
        
        Args:
            gcs_uri: GCS URI (e.g., gs://bucket/path/file.json)
            
        Returns:
            File content as string
        """
        try:
            if not gcs_uri.startswith('gs://'):
                raise ValueError(f"Invalid GCS URI: {gcs_uri}")
            
            parts = gcs_uri[5:].split('/', 1)
            bucket_name = parts[0]
            blob_name = parts[1]
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            return blob.download_as_text()
        
        except Exception as e:
            self.logger.error(f"Error reading file from GCS: {str(e)}")
            raise
