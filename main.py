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
        
        # Extract text from document
        logger.info(f"\n📄 Processing: {settings.gcs_input_path}")
        extracted_data = text_extractor.extract_text_from_gcs(
            gcs_uri=settings.gcs_input_path
        )
        
        # Generate metadata
        logger.info("\n🔍 Generating metadata...")
        metadata = metadata_generator.generate_metadata(extracted_data)
        
        # Create DataFrame and save to GCS
        logger.info("\n💾 Saving metadata to GCS...")
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
        local_output_path = project_root / 'data' / 'local_output' / output_file_name
        csv_handler.save_locally(df, str(local_output_path))
        
        # Generate and display report
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        report = csv_handler.generate_report(df)
        print(report)
        
        logger.info(f"\n✅ CSV saved to GCS: {gcs_uri}")
        logger.info(f"✅ CSV saved locally: {local_output_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"\n❌ Error processing file: {str(e)}")
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
        bucket_name, prefix = settings.parse_gcs_uri(settings.gcs_input_folder)
        logger.info(f"\n📁 Listing files in gs://{bucket_name}/{prefix}")
        
        file_uris = gcs_helper.list_blobs(
            bucket_name=bucket_name,
            prefix=prefix,
            suffix='.pptx'  # Can be modified to support multiple formats
        )
        
        if not file_uris:
            logger.warning("No files found to process")
            return False
        
        logger.info(f"Found {len(file_uris)} files to process")
        
        # Process each file
        all_metadata = []
        
        for file_uri in tqdm(file_uris, desc="Processing files"):
            try:
                logger.info(f"\n📄 Processing: {file_uri}")
                
                # Extract text
                extracted_data = text_extractor.extract_text_from_gcs(gcs_uri=file_uri)
                
                # Generate metadata
                metadata = metadata_generator.generate_metadata(extracted_data)
                all_metadata.append(metadata)
                
                logger.info(f"✅ Successfully processed: {file_uri.split('/')[-1]}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {file_uri}: {str(e)}")
                continue
        
        if not all_metadata:
            logger.error("No metadata generated from any files")
            return False
        
        # Create DataFrame and save to GCS
        logger.info(f"\n💾 Saving metadata for {len(all_metadata)} files to GCS...")
        df = csv_handler.create_dataframe(all_metadata)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file_name = f"kia_batch_metadata_{timestamp}.csv"
        
        gcs_uri = csv_handler.save_to_gcs(
            df=df,
            bucket_name=settings.gcs_output_bucket,
            blob_path=settings.gcs_output_path,
            file_name=output_file_name
        )
        
        # Optional: Save locally as backup
        local_output_path = project_root / 'data' / 'local_output' / output_file_name
        csv_handler.save_locally(df, str(local_output_path))
        
        # Generate and display report
        logger.info("\n" + "=" * 60)
        logger.info("BATCH PROCESSING COMPLETE")
        logger.info("=" * 60)
        report = csv_handler.generate_report(df)
        print(report)
        
        logger.info(f"\n✅ CSV saved to GCS: {gcs_uri}")
        logger.info(f"✅ CSV saved locally: {local_output_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"\n❌ Error in batch processing: {str(e)}")
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
        help='Process all files in GCS_INPUT_FOLDER (batch mode)'
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
        if not settings.gcs_input_folder:
            logger.error("GCS_INPUT_FOLDER must be set in .env for batch mode")
            sys.exit(1)
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
