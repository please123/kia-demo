"""
Text extraction module using Google Document AI
"""
from google.cloud import documentai_v1 as documentai
from typing import Dict, Optional
import logging
import re
import time
import json
from google.api_core.client_options import ClientOptions


class TextExtractor:
    """Extract text from documents using Google Document AI"""
    
    def __init__(self, project_id: str, location: str, processor_id: str):
        """Initialize Document AI client
        
        Args:
            project_id: GCP project ID
            location: Processor location (e.g., 'us', 'eu')
            processor_id: Document AI processor ID
        """
        self.client = documentai.DocumentProcessorServiceClient()
        self.processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
        self.logger = logging.getLogger('kia_metadata.extractor')
    
    def extract_text_from_gcs(self, gcs_uri: str, mime_type: str = 'application/pdf') -> Dict:
        """Extract text from a document in GCS
        
        Args:
            gcs_uri: GCS URI of the document (e.g., gs://bucket/path/file.pdf)
            mime_type: MIME type of the document
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            self.logger.info(f"Processing document: {gcs_uri}")
            
            # Determine MIME type from file extension if not provided
            if gcs_uri.endswith('.pptx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            elif gcs_uri.endswith('.pdf'):
                mime_type = 'application/pdf'
            elif gcs_uri.endswith('.docx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            # Create GCS document
            gcs_document = documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type=mime_type
            )
            
            # Configure the process request
            request = documentai.ProcessRequest(
                name=self.processor_name,
                gcs_document=gcs_document
            )
            
            # Process the document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract text and structure
            extracted_data = {
                'full_text': document.text,
                'pages': [],
                'entities': [],
                'gcs_uri': gcs_uri,
                'mime_type': mime_type
            }
            
            # Extract page-level information
            for page in document.pages:
                page_data = {
                    'page_number': page.page_number,
                    'text': self._extract_page_text(document.text, page),
                }
                extracted_data['pages'].append(page_data)
            
            # Extract entities if available
            for entity in document.entities:
                entity_data = {
                    'type': entity.type_,
                    'mention_text': entity.mention_text,
                    'confidence': entity.confidence
                }
                extracted_data['entities'].append(entity_data)
            
            self.logger.info(f"Successfully extracted text from {gcs_uri}")
            self.logger.info(f"Total pages: {len(extracted_data['pages'])}")
            self.logger.info(f"Total text length: {len(extracted_data['full_text'])} characters")
            
            return extracted_data
        
        except Exception as e:
            self.logger.error(f"Error extracting text from {gcs_uri}: {str(e)}")
            raise
    
    def _extract_page_text(self, full_text: str, page) -> str:
        """Extract text for a specific page
        
        Args:
            full_text: Full document text
            page: Page object from Document AI
            
        Returns:
            Text content of the page
        """
        try:
            # Get text segments for this page
            page_text = ""
            for paragraph in page.paragraphs:
                paragraph_text = self._get_text_from_layout(full_text, paragraph.layout)
                page_text += paragraph_text + "\n"
            
            return page_text.strip()
        except:
            return ""
    
    def _get_text_from_layout(self, full_text: str, layout) -> str:
        """Extract text from a layout object
        
        Args:
            full_text: Full document text
            layout: Layout object
            
        Returns:
            Extracted text
        """
        try:
            text_segments = []
            for segment in layout.text_anchor.text_segments:
                start_index = int(segment.start_index) if segment.start_index else 0
                end_index = int(segment.end_index) if segment.end_index else len(full_text)
                text_segments.append(full_text[start_index:end_index])
            return "".join(text_segments)
        except:
            return ""
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might cause issues
        text = text.strip()
        return text

    def batch_process_document(self, gcs_uri: str, gcs_output_uri_prefix: str, gcs_helper) -> Dict:
        """Process a large document using Document AI Batch API (Async)
        
        Args:
            gcs_uri: Input GCS URI
            gcs_output_uri_prefix: Output GCS URI prefix (must end with /)
            gcs_helper: GCSHelper instance for reading results
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            self.logger.info(f"Starting async batch processing for: {gcs_uri}")
            
            # Determine MIME type
            mime_type = 'application/pdf'  # default
            if gcs_uri.endswith('.pptx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            elif gcs_uri.endswith('.pdf'):
                mime_type = 'application/pdf'
            elif gcs_uri.endswith('.docx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

            # Configure input
            gcs_documents = documentai.GcsDocuments(
                documents=[
                    documentai.GcsDocument(
                        gcs_uri=gcs_uri,
                        mime_type=mime_type
                    )
                ]
            )
            input_config = documentai.BatchDocumentsInputConfig(gcs_documents=gcs_documents)

            # Configure output
            output_config = documentai.DocumentOutputConfig(
                gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
                    gcs_uri=gcs_output_uri_prefix
                )
            )

            # Create request
            request = documentai.BatchProcessRequest(
                name=self.processor_name,
                input_documents=input_config,
                document_output_config=output_config
            )

            # Start operation
            operation = self.client.batch_process_documents(request=request)
            
            self.logger.info(f"Waiting for operation to complete... (Operation: {operation.operation.name})")
            operation.result(timeout=600)  # Wait up to 10 minutes
            self.logger.info("Operation completed successfully.")

            # List output files
            # Output format: [gcs_output_uri_prefix]/[operation_id]/[input_file_index]/[input_file_name]/[output_file_index].json
            # We just list everything under the prefix and look for JSONs
            
            # Parse prefix to bucket and path
            if not gcs_output_uri_prefix.startswith('gs://'):
                raise ValueError(f"Invalid output prefix: {gcs_output_uri_prefix}")
            
            parts = gcs_output_uri_prefix[5:].split('/', 1)
            bucket_name = parts[0]
            prefix = parts[1] if len(parts) > 1 else ''
            
            output_files = gcs_helper.list_blobs(bucket_name=bucket_name, prefix=prefix, suffix=".json")
            
            if not output_files:
                raise RuntimeError("No output JSON files found after batch processing")

            # Combine results (Document AI might split large files into multiple JSONs)
            combined_text = ""
            combined_pages = []
            combined_entities = []
            
            # Sort to ensure order
            output_files.sort()
            
            for output_file in output_files:
                json_content = gcs_helper.read_file(output_file)
                document = documentai.Document.from_json(json_content)
                
                # Append text
                combined_text += document.text
                
                # Append pages (adjust page numbers if necessary, but usually they are absolute)
                for page in document.pages:
                    page_data = {
                        'page_number': page.page_number,
                        'text': self._extract_page_text(document.text, page),
                    }
                    combined_pages.append(page_data)
                
                # Append entities
                for entity in document.entities:
                    entity_data = {
                        'type': entity.type_,
                        'mention_text': entity.mention_text,
                        'confidence': entity.confidence
                    }
                    combined_entities.append(entity_data)

            extracted_data = {
                'full_text': combined_text,
                'pages': combined_pages,
                'entities': combined_entities,
                'gcs_uri': gcs_uri,
                'mime_type': mime_type
            }
            
            self.logger.info(f"Successfully processed large file: {gcs_uri}")
            self.logger.info(f"Total pages: {len(combined_pages)}")
            
            return extracted_data

        except Exception as e:
            self.logger.error(f"Error in batch processing for {gcs_uri}: {str(e)}")
            raise
