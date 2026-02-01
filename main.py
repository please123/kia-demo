"""
Main execution script for Kia Metadata Generator
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Settings
from utils import setup_logger, GCSHelper
from modules import TextExtractor, MetadataGenerator, CSVHandler
from tqdm import tqdm
from datetime import datetime


def _list_input_files(settings: Settings, gcs_helper: GCSHelper, logger) -> list[str]:
    """
    Resolve input sources into a list of GCS URIs.

    Supported:
    - GCS_INPUT_BUCKET (+ optional GCS_INPUT_PREFIX): bucket-wide batch
    - legacy GCS_INPUT_FOLDER (gs://bucket/prefix): prefix batch
    - GCS_INPUT_PATH with wildcard like gs://bucket/prefix/* : treated as prefix batch
    """
    # 1) Preferred: bucket + prefix
    if getattr(settings, "gcs_input_bucket", ""):
        bucket_name = settings.gcs_input_bucket
        prefix = getattr(settings, "gcs_input_prefix", "") or ""
        logger.info(f"\n[LISTING] Files in gs://{bucket_name}/{prefix}")
        return gcs_helper.list_blobs(bucket_name=bucket_name, prefix=prefix, suffix="")

    # 2) Legacy folder URI: gs://bucket/prefix
    if settings.gcs_input_folder:
        bucket_name, prefix = settings.parse_gcs_uri(settings.gcs_input_folder)
        logger.info(f"\n[LISTING] Files in gs://{bucket_name}/{prefix}")
        return gcs_helper.list_blobs(bucket_name=bucket_name, prefix=prefix, suffix="")

    # 3) Wildcard path: gs://bucket/prefix/*
    if settings.gcs_input_path and "*" in settings.gcs_input_path:
        base = settings.gcs_input_path.split("*", 1)[0]
        bucket_name, prefix = settings.parse_gcs_uri(base)
        logger.info(f"\n[LISTING] Files in gs://{bucket_name}/{prefix}")
        return gcs_helper.list_blobs(bucket_name=bucket_name, prefix=prefix, suffix="")

    return []


def process_single_file(settings: Settings, logger) -> bool:
    """Process a single file from GCS
    
    Args:
        settings: Settings instance
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting Kia Metadata Generator - Single File Mode")
        logger.info("=" * 60)
        
        # Initialize components
        logger.info("Initializing components...")
        text_extractor = TextExtractor(
            project_id=settings.gcp_project_id,
            location=settings.documentai_location,
            processor_id=settings.documentai_processor_id
        )
        
        metadata_generator = MetadataGenerator()
        
        gcs_helper = GCSHelper(project_id=settings.gcp_project_id)
        csv_handler = CSVHandler(gcs_helper=gcs_helper)
        
        # Check file size
        size_bytes = gcs_helper.get_blob_size(settings.gcs_input_path)
        
        if size_bytes > settings.documentai_max_sync_bytes:
            logger.info(f"[WARNING] File size ({size_bytes} bytes) exceeds sync limit. Switching to async batch processing.")
            
            # Generate temporary output prefix
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_output_prefix = f"gs://{settings.gcs_output_bucket}/temp_async_output/{timestamp}/"
            
            extracted_data = text_extractor.batch_process_document(
                gcs_uri=settings.gcs_input_path,
                gcs_output_uri_prefix=temp_output_prefix,
                gcs_helper=gcs_helper
            )
        else:
            extracted_data = text_extractor.extract_text_from_gcs(
                gcs_uri=settings.gcs_input_path
            )
        
        # Generate metadata
        logger.info("\n[PROCESSING] Generating metadata...")
        metadata = metadata_generator.generate_metadata(extracted_data)
        
        # Create DataFrame and save to GCS
        logger.info("\n[SAVING] Saving metadata to GCS...")
        df = csv_handler.create_dataframe([metadata])
        
        # Generate output file name from input file name
        input_file_name = settings.gcs_input_path.split('/')[-1]
        output_file_name = f"{input_file_name.rsplit('.', 1)[0]}_metadata.csv"
        
        gcs_uri = csv_handler.save_to_gcs(
            df=df,
            bucket_name=settings.gcs_output_bucket,
            blob_path=settings.gcs_output_path,
            file_name=output_file_name
        )
        
        # Optional: Save locally as backup
        # local_output_path = project_root / 'data' / 'local_output' / output_file_name
        # csv_handler.save_locally(df, str(local_output_path))
        
        # Generate and display report
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        report = csv_handler.generate_report(df)
        print(report)
        
        logger.info(f"\n[SUCCESS] CSV saved to GCS: {gcs_uri}")
        # logger.info(f"[SUCCESS] CSV saved locally: {local_output_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"\n[ERROR] Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def process_batch_files(settings: Settings, logger) -> bool:
    """Process multiple files from GCS folder
    
    Args:
        settings: Settings instance
        logger: Logger instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting Kia Metadata Generator - Batch Mode")
        logger.info("=" * 60)
        
        # Initialize components
        logger.info("Initializing components...")
        text_extractor = TextExtractor(
            project_id=settings.gcp_project_id,
            location=settings.documentai_location,
            processor_id=settings.documentai_processor_id
        )
        
        metadata_generator = MetadataGenerator()
        
        gcs_helper = GCSHelper(project_id=settings.gcp_project_id)
        csv_handler = CSVHandler(gcs_helper=gcs_helper)
        
        # Get list of files from GCS
        all_uris = _list_input_files(settings, gcs_helper, logger)
        supported_exts = (".pptx", ".pdf", ".docx")
        file_uris = [u for u in all_uris if u.lower().endswith(supported_exts)]
        
        if not file_uris:
            logger.warning("No files found to process")
            return False
        
        logger.info(f"Found {len(file_uris)} files to process")
        
        # Process each file
        all_metadata = []
        
        for file_uri in tqdm(file_uris, desc="Processing files"):
            try:
                logger.info(f"\n📄 Processing: {file_uri}")

                # Guard: Document AI sync API has a size limit; skip oversized files to keep batch running
                try:
                    size_bytes = gcs_helper.get_blob_size(file_uri)
                except Exception as e:
                    logger.warning(f"[WARNING] Could not get size for {file_uri}: {e}. Will try processing anyway.")
                    size_bytes = 0

                if size_bytes and size_bytes > settings.documentai_max_sync_bytes:
                    logger.info(
                        f"⚠️ File size ({size_bytes} bytes) exceeds sync limit. Switching to async batch processing."
                    )
                    # Generate temporary output prefix
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_name = file_uri.split('/')[-1]
                    temp_output_prefix = f"gs://{settings.gcs_output_bucket}/temp_async_output/{timestamp}/{file_name}/"
                    
                    extracted_data = text_extractor.batch_process_document(
                        gcs_uri=file_uri,
                        gcs_output_uri_prefix=temp_output_prefix,
                        gcs_helper=gcs_helper
                    )
                else:
                    # Extract text (Sync)
                    extracted_data = text_extractor.extract_text_from_gcs(gcs_uri=file_uri)
                
                # Generate metadata
                metadata = metadata_generator.generate_metadata(extracted_data)
                all_metadata.append(metadata)
                
                logger.info(f"[SUCCESS] Successfully processed: {file_uri.split('/')[-1]}")
                
            except Exception as e:
                logger.error(f"[ERROR] Error processing {file_uri}: {str(e)}")
                continue
        
        if not all_metadata:
            logger.error("No metadata generated from any files")
            return False
        
        # Create DataFrame and save to GCS
        logger.info(f"\n[SAVING] Saving metadata for {len(all_metadata)} files to GCS...")
        df = csv_handler.create_dataframe(all_metadata)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file_name = f"kia_batch_metadata_{timestamp}.csv"
        
        gcs_uri = csv_handler.save_to_gcs(
            df=df,
            bucket_name=settings.gcs_output_bucket,
            blob_path=settings.gcs_output_path,
            file_name=output_file_name
        )
        
        # Optional: Save locally as backup
        # local_output_path = project_root / 'data' / 'local_output' / output_file_name
        # csv_handler.save_locally(df, str(local_output_path))
        
        # Generate and display report
        logger.info("\n" + "=" * 60)
        logger.info("BATCH PROCESSING COMPLETE")
        logger.info("=" * 60)
        report = csv_handler.generate_report(df)
        print(report)
        
        logger.info(f"\n[SUCCESS] CSV saved to GCS: {gcs_uri}")
        # logger.info(f"[SUCCESS] CSV saved locally: {local_output_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"\n[ERROR] Error in batch processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Kia Metadata Generator - Extract and generate metadata from documents'
    )
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process all files in input bucket (batch mode)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logger
    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(level=log_level)
    
    # Load settings
    logger.info("Loading settings from .env file...")
    settings = Settings()
    
    # Validate settings
    if not settings.validate():
        logger.error("Settings validation failed. Please check your .env file.")
        sys.exit(1)
    
    # Process files
    if args.batch:
        success = process_batch_files(settings, logger)
    else:
        # If user provided wildcard like gs://bucket/prefix/*, treat it as batch automatically
        if settings.gcs_input_path and "*" in settings.gcs_input_path:
            logger.info("Detected wildcard in GCS_INPUT_PATH; switching to batch processing.")
            success = process_batch_files(settings, logger)
        else:
            if not settings.gcs_input_path:
                logger.error("GCS_INPUT_PATH must be set in .env for single file mode")
                sys.exit(1)
            success = process_single_file(settings, logger)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
