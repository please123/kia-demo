"""
CSV handler module for saving metadata to GCS
"""
import pandas as pd
from typing import List, Dict
import logging
from io import StringIO, BytesIO
from utils.gcs_utils import GCSHelper


class CSVHandler:
    """Handle CSV creation and upload to GCS"""
    
    def __init__(self, gcs_helper: GCSHelper):
        """Initialize CSV handler
        
        Args:
            gcs_helper: GCSHelper instance for GCS operations
        """
        self.gcs_helper = gcs_helper
        self.logger = logging.getLogger('kia_metadata.csv')
    
    # def create_dataframe(self, metadata_list: List[Dict]) -> pd.DataFrame:
    #     """Create pandas DataFrame from metadata list
        
    #     Args:
    #         metadata_list: List of metadata dictionaries
            
    #     Returns:
    #         pandas DataFrame
    #     """
    #     try:
    #         if not metadata_list:
    #             self.logger.warning("Empty metadata list provided")
    #             return pd.DataFrame()
            
    #         df = pd.DataFrame(metadata_list)
            
    #         # Define column order
    #         column_order = [
    #             'document_id',
    #             'source_type',
    #             'file_name',
    #             'upload_date',
    #             'car_model',
    #             'car_type',
    #             'engine_type',
    #             'price',
    #             'page_count',
    #             'text_length',
    #             'features',
    #             'keywords',
    #             'summary',
    #             'specifications',
    #             'gcs_uri',
    #         ]
            
    #         # Reorder columns (only include existing columns)
    #         existing_columns = [col for col in column_order if col in df.columns]
    #         df = df[existing_columns]
            
    #         self.logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
    #         return df
        
    #     except Exception as e:
    #         self.logger.error(f"Error creating DataFrame: {str(e)}")
    #         raise
    
    def create_dataframe(self, metadata_list: List[Dict]) -> pd.DataFrame:
        """Create pandas DataFrame from metadata list
    
        Args:
            metadata_list: List of metadata dictionaries with nested 'metadata' structure
        
        Returns:
        pandas DataFrame
        """
        try:
            if not metadata_list:
                self.logger.warning("Empty metadata list provided")
                return pd.DataFrame()
            
            # Flatten nested metadata structure
            flattened_data = []
            for item in metadata_list:
                # Handle both flat and nested structures for backward compatibility
                metadata = item.get('metadata', item)
                
                flattened = {
                    'type': metadata.get('type', ''),
                    'source': metadata.get('source', ''),
                    'region': metadata.get('region', ''),
                    'country': metadata.get('country', ''),
                    'model': metadata.get('model', ''),
                    'xev': metadata.get('xev', ''),
                    'year1': metadata.get('year1', ''),
                    'year2': metadata.get('year2', ''),
                    'language': metadata.get('language', ''),
                    'version': metadata.get('version', ''),
                    'updated_at': metadata.get('updated_at', ''),
                    'file_format': metadata.get('file_format', ''),
                    'content_summary': item.get('content_summary', '')
                }
                flattened_data.append(flattened)
            
            df = pd.DataFrame(flattened_data)
            
            # Define column order matching the new metadata structure
            column_order = [
                'type',
                'source',
                'region',
                'country',
                'model',
                'xev',
                'year1',
                'year2',
                'language',
                'version',
                'updated_at',
                'file_format',
                'content_summary'
            ]
            
            # Reorder columns (only include existing columns)
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]
            
            self.logger.info(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
            return df
        
        except Exception as e:
            self.logger.error(f"Error creating DataFrame: {str(e)}")
            raise



    def save_to_gcs(self, df: pd.DataFrame, bucket_name: str, 
                    blob_path: str, file_name: str = None) -> str:
        """Save DataFrame as CSV to GCS
        
        Args:
            df: pandas DataFrame to save
            bucket_name: GCS bucket name
            blob_path: Path in GCS bucket (e.g., 'output/metadata/')
            file_name: Optional custom file name
            
        Returns:
            GCS URI of the saved file
        """
        try:
            if df.empty:
                self.logger.warning("Empty DataFrame, skipping save")
                return ""
            
            # Generate file name if not provided
            if not file_name:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_name = f"kia_metadata_{timestamp}.csv"
            
            # Ensure file_name ends with .csv
            if not file_name.endswith('.csv'):
                file_name += '.csv'
            
            # Construct full blob path
            full_blob_path = f"{blob_path.rstrip('/')}/{file_name}"
            
            # Convert DataFrame to CSV bytes with utf-8-sig encoding
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_content = csv_buffer.getvalue()
            
            # Upload to GCS
            gcs_uri = self.gcs_helper.upload_from_string(
                bucket_name=bucket_name,
                blob_name=full_blob_path,
                content=csv_content,
                content_type='text/csv'
            )
            
            self.logger.info(f"Successfully saved CSV to {gcs_uri}")
            return gcs_uri
        
        except Exception as e:
            self.logger.error(f"Error saving CSV to GCS: {str(e)}")
            raise
    
    def save_locally(self, df: pd.DataFrame, file_path: str) -> str:
        """Save DataFrame as CSV locally (for testing/backup)
        
        Args:
            df: pandas DataFrame to save
            file_path: Local file path
            
        Returns:
            Path to saved file
        """
        try:
            if df.empty:
                self.logger.warning("Empty DataFrame, skipping save")
                return ""
            
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            self.logger.info(f"Successfully saved CSV locally to {file_path}")
            return file_path
        
        except Exception as e:
            self.logger.error(f"Error saving CSV locally: {str(e)}")
            raise
    
    def append_to_existing(self, new_df: pd.DataFrame, bucket_name: str, 
                          existing_blob_path: str) -> str:
        """Append new data to existing CSV in GCS
        
        Args:
            new_df: New DataFrame to append
            bucket_name: GCS bucket name
            existing_blob_path: Path to existing CSV in GCS
            
        Returns:
            GCS URI of the updated file
        """
        try:
            # Check if file exists
            blob_name = existing_blob_path.replace(f"gs://{bucket_name}/", "")
            
            if self.gcs_helper.blob_exists(bucket_name, blob_name):
                # Download existing CSV
                from google.cloud import storage
                client = storage.Client()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                
                # Download bytes and decode
                csv_bytes = blob.download_as_string()
                csv_content = csv_bytes.decode('utf-8-sig')
                existing_df = pd.read_csv(StringIO(csv_content))
                
                # Append new data
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                self.logger.info(f"Appending {len(new_df)} rows to existing {len(existing_df)} rows")
            else:
                combined_df = new_df
                self.logger.info(f"File doesn't exist, creating new with {len(new_df)} rows")
            
            # Save combined DataFrame as bytes with utf-8-sig
            csv_buffer = BytesIO()
            combined_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_content = csv_buffer.getvalue()
            
            gcs_uri = self.gcs_helper.upload_from_string(
                bucket_name=bucket_name,
                blob_name=blob_name,
                content=csv_content,
                content_type='text/csv'
            )
            
            self.logger.info(f"Successfully updated CSV at {gcs_uri}")
            return gcs_uri
        
        except Exception as e:
            self.logger.error(f"Error appending to CSV: {str(e)}")
            raise
    
    # def generate_report(self, df: pd.DataFrame) -> str:
    #     """Generate a simple text report from DataFrame
        
    #     Args:
    #         df: pandas DataFrame
            
    #     Returns:
    #         Report text
    #     """
    #     if df.empty:
    #         return "No data available for report"
        
    #     report = []
    #     report.append("=" * 60)
    #     report.append("KIA METADATA GENERATION REPORT")
    #     report.append("=" * 60)
    #     report.append(f"\nTotal Documents Processed: {len(df)}")
    #     report.append(f"Generation Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    #     # Car model distribution
    #     if 'car_model' in df.columns:
    #         report.append("\n\nCar Model Distribution:")
    #         model_counts = df['car_model'].value_counts()
    #         for model, count in model_counts.items():
    #             report.append(f"  - {model}: {count}")
        
    #     # Source type distribution
    #     if 'source_type' in df.columns:
    #         report.append("\n\nSource Type Distribution:")
    #         source_counts = df['source_type'].value_counts()
    #         for source, count in source_counts.items():
    #             report.append(f"  - {source}: {count}")
        
    #     # Average page count
    #     if 'page_count' in df.columns:
    #         avg_pages = df['page_count'].mean()
    #         report.append(f"\n\nAverage Page Count: {avg_pages:.2f}")
        
    #     report.append("\n" + "=" * 60)
        
    #     return "\n".join(report)

    def generate_report(self, df: pd.DataFrame) -> str:
        """Generate a simple text report from DataFrame
        
        Args:
            df: pandas DataFrame
            
        Returns:
            Report text
        """
        if df.empty:
            return "No data available for report"
        
        report = []
        report.append("=" * 60)
        report.append("KIA METADATA GENERATION REPORT")
        report.append("=" * 60)
        report.append(f"\nTotal Documents Processed: {len(df)}")
        report.append(f"Generation Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Type distribution
        if 'type' in df.columns:
            report.append("\n\nDocument Type Distribution:")
            type_counts = df['type'].value_counts()
            for doc_type, count in type_counts.items():
                report.append(f"  - {doc_type}: {count}")
        
        # Source distribution
        if 'source' in df.columns:
            report.append("\n\nSource Distribution:")
            source_counts = df['source'].value_counts()
            for source, count in source_counts.items():
                report.append(f"  - {source}: {count}")
        
        # Region distribution
        if 'region' in df.columns:
            report.append("\n\nRegion Distribution:")
            region_counts = df['region'].value_counts()
            for region, count in region_counts.items():
                report.append(f"  - {region}: {count}")
        
        # Model distribution
        if 'model' in df.columns:
            report.append("\n\nCar Model Distribution:")
            model_counts = df['model'].value_counts()
            for model, count in model_counts.head(10).items():  # Top 10 models
                report.append(f"  - {model}: {count}")
        
        # XEV type distribution
        if 'xev' in df.columns:
            report.append("\n\nXEV Type Distribution:")
            xev_counts = df['xev'].value_counts(dropna=False)
            for xev_type, count in xev_counts.items():
                xev_label = 'NULL (Non-Hybrid)' if pd.isna(xev_type) or xev_type == '' else xev_type
                report.append(f"  - {xev_label}: {count}")
        
        # Language distribution
        if 'language' in df.columns:
            report.append("\n\nLanguage Distribution:")
            lang_counts = df['language'].value_counts()
            for lang, count in lang_counts.items():
                report.append(f"  - {lang}: {count}")
        
        # File format distribution
        if 'file_format' in df.columns:
            report.append("\n\nFile Format Distribution:")
            format_counts = df['file_format'].value_counts()
            for file_format, count in format_counts.items():
                report.append(f"  - {file_format}: {count}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
