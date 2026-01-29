"""
Metadata generation module for Kia documents
"""
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging


class MetadataGenerator:
    """Generate metadata from extracted text"""
    
    def __init__(self):
        """Initialize metadata generator"""
        self.logger = logging.getLogger('kia_metadata.generator')
        
        # Kia car models (expand as needed)
        self.car_models = [
            'EV6', 'EV9', 'Niro', 'Soul', 'Sportage', 'Sorento', 
            'Carnival', 'Seltos', 'K5', 'K8', 'Stinger', 'Telluride',
            'K3', 'K8', 'Mohave', 'Ray', 'Morning', 'Picanto'
        ]
        
        # Car types
        self.car_types = [
            'SUV', 'Sedan', 'Electric', 'Hybrid', 'MPV', 'Hatchback', 
            'Crossover', 'Minivan'
        ]
        
        # Engine types
        self.engine_types = [
            'Electric', 'Gasoline', 'Diesel', 'Hybrid', 'Plug-in Hybrid',
            'Battery Electric', 'EV', 'ICE'
        ]
    
    def generate_metadata(self, extracted_data: Dict, source_type: str = 'document') -> Dict:
        """Generate metadata from extracted text
        
        Args:
            extracted_data: Dictionary containing extracted text and structure
            source_type: Type of source ('document' or 'video')
            
        Returns:
            Dictionary containing metadata
        """
        try:
            full_text = extracted_data.get('full_text', '')
            gcs_uri = extracted_data.get('gcs_uri', '')
            
            self.logger.info(f"Generating metadata for {gcs_uri}")
            
            # Extract file name from GCS URI
            file_name = gcs_uri.split('/')[-1] if gcs_uri else 'unknown'
            
            metadata = {
                'document_id': self._generate_document_id(file_name),
                'source_type': source_type,
                'file_name': file_name,
                'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'gcs_uri': gcs_uri,
                'page_count': len(extracted_data.get('pages', [])),
                'text_length': len(full_text),
                
                # Car information
                'car_model': self._extract_car_model(full_text),
                'car_type': self._extract_car_type(full_text),
                'engine_type': self._extract_engine_type(full_text),
                'price': self._extract_price(full_text),
                
                # Content analysis
                'features': self._extract_features(full_text),
                'keywords': self._extract_keywords(full_text),
                'summary': self._generate_summary(full_text),
                
                # Technical specs (if available)
                'specifications': self._extract_specifications(full_text),
            }
            
            self.logger.info(f"Metadata generated successfully for {file_name}")
            return metadata
        
        except Exception as e:
            self.logger.error(f"Error generating metadata: {str(e)}")
            raise
    
    def _generate_document_id(self, file_name: str) -> str:
        """Generate unique document ID
        
        Args:
            file_name: Name of the file
            
        Returns:
            Document ID
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        clean_name = re.sub(r'[^\w\-]', '_', file_name.split('.')[0])
        return f"{clean_name}_{timestamp}"
    
    def _extract_car_model(self, text: str) -> str:
        """Extract car model from text
        
        Args:
            text: Document text
            
        Returns:
            Car model name or 'Unknown'
        """
        text_upper = text.upper()
        
        for model in self.car_models:
            if model.upper() in text_upper:
                return model
        
        return 'Unknown'
    
    def _extract_car_type(self, text: str) -> str:
        """Extract car type from text
        
        Args:
            text: Document text
            
        Returns:
            Car type or 'Unknown'
        """
        text_upper = text.upper()
        
        for car_type in self.car_types:
            if car_type.upper() in text_upper:
                return car_type
        
        return 'Unknown'
    
    def _extract_engine_type(self, text: str) -> str:
        """Extract engine type from text
        
        Args:
            text: Document text
            
        Returns:
            Engine type or 'Unknown'
        """
        text_upper = text.upper()
        
        for engine_type in self.engine_types:
            if engine_type.upper() in text_upper:
                return engine_type
        
        return 'Unknown'
    
    def _extract_price(self, text: str) -> str:
        """Extract price information from text
        
        Args:
            text: Document text
            
        Returns:
            Price information or 'Not specified'
        """
        # Pattern for Korean Won (원)
        price_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*만?\s*원',  # 3,000만원 or 3000만원
            r'(\d{1,3}(?:,\d{3})*)\s*천만원',     # 3,000천만원
            r'\$\s*(\d{1,3}(?:,\d{3})*)',         # $30,000
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return 'Not specified'
    
    def _extract_features(self, text: str) -> str:
        """Extract key features from text
        
        Args:
            text: Document text
            
        Returns:
            Comma-separated features
        """
        feature_keywords = [
            '안전', '편의', '퍼포먼스', '디자인', '연비', '주행', 
            '시스템', '기술', 'Safety', 'Convenience', 'Performance',
            'Design', 'Efficiency', 'Technology', 'Smart', 'Advanced'
        ]
        
        found_features = []
        
        # Look for sentences containing feature keywords
        sentences = text.split('.')
        for sentence in sentences[:20]:  # Check first 20 sentences
            for keyword in feature_keywords:
                if keyword in sentence and len(sentence) < 200:
                    found_features.append(sentence.strip())
                    break
        
        # Limit to top 5 features
        return ' | '.join(found_features[:5]) if found_features else 'Not specified'
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> str:
        """Extract top keywords from text
        
        Args:
            text: Document text
            top_n: Number of top keywords to extract
            
        Returns:
            Comma-separated keywords
        """
        # Simple keyword extraction (can be enhanced with NLP libraries)
        words = re.findall(r'\b[가-힣a-zA-Z]{2,}\b', text)
        
        # Count word frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Remove common stop words (expand as needed)
        stop_words = {'the', 'and', 'or', 'is', 'in', 'at', 'to', 'of', 
                     '입니다', '있습니다', '합니다', '하는', '되는'}
        
        filtered_freq = {k: v for k, v in word_freq.items() 
                        if k.lower() not in stop_words and v > 1}
        
        # Sort by frequency
        top_keywords = sorted(filtered_freq.items(), 
                            key=lambda x: x[1], reverse=True)[:top_n]
        
        keywords = [word for word, freq in top_keywords]
        return ', '.join(keywords) if keywords else 'Not extracted'
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate summary from text
        
        Args:
            text: Document text
            max_length: Maximum summary length
            
        Returns:
            Summary text
        """
        # Simple extractive summary - first meaningful paragraph
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) > 50:  # Skip very short paragraphs
                if len(paragraph) > max_length:
                    return paragraph[:max_length] + '...'
                return paragraph
        
        # Fallback: return first max_length characters
        return text[:max_length] + '...' if len(text) > max_length else text
    
    def _extract_specifications(self, text: str) -> str:
        """Extract technical specifications
        
        Args:
            text: Document text
            
        Returns:
            Specifications as string
        """
        spec_patterns = [
            r'배터리\s*:\s*([^\n]+)',
            r'모터\s*:\s*([^\n]+)',
            r'출력\s*:\s*([^\n]+)',
            r'토크\s*:\s*([^\n]+)',
            r'Battery\s*:\s*([^\n]+)',
            r'Motor\s*:\s*([^\n]+)',
            r'Power\s*:\s*([^\n]+)',
        ]
        
        specs = []
        for pattern in spec_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            specs.extend(matches)
        
        return ' | '.join(specs[:5]) if specs else 'Not specified'
    
    def batch_generate_metadata(self, extracted_data_list: List[Dict]) -> List[Dict]:
        """Generate metadata for multiple documents
        
        Args:
            extracted_data_list: List of extracted data dictionaries
            
        Returns:
            List of metadata dictionaries
        """
        metadata_list = []
        
        for extracted_data in extracted_data_list:
            try:
                metadata = self.generate_metadata(extracted_data)
                metadata_list.append(metadata)
            except Exception as e:
                self.logger.error(f"Error processing document: {str(e)}")
                continue
        
        self.logger.info(f"Generated metadata for {len(metadata_list)} documents")
        return metadata_list
