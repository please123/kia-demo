"""
Metadata generation module for Kia documents using Gemini 2.5 Pro
"""
import re
import json
from typing import Dict, List, Optional
from datetime import datetime
import logging
import google.generativeai as genai
import os


class MetadataGenerator:
    """Generate metadata from extracted text using Gemini 2.5 Pro"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize metadata generator with Gemini API

        Args:
            api_key: Google AI API key. If not provided, reads from environment variable.
        """
        self.logger = logging.getLogger('kia_metadata.generator')

        # Configure Gemini API
        api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key must be provided or set in GOOGLE_API_KEY environment variable")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        # System prompt for Gemini
        self.system_prompt = """## Gemini 데이터 라벨링 시스템 프롬프트 ##
[Role & Context]
너는 기아(Kia) 고객경험본부 상품CX실 AI CX팀의 데이터 자산화 전문가야. 너의 임무는 입력된 다양한 형태의 문서(FAQ, 매뉴얼, 영상 스크립트 등)를 분석하여, 일관된 정책에 따라 메타데이터를 추출하고 라벨링하는 것이야.

[Metadata Definition & Master Tables]
각 필드에 대해 아래 정의된 마스터 테이블 값을 우선적으로 사용하고, 정보가 없는 경우 규칙에 따라 처리해.

1. 기본 분류 정보
유형 (type): 브랜드, 차종정보, 비즈니스, 고객정보, 기술정보 중 선택.
출처 (source): 도메인, 상품운영안, 신차해설서, FAQ, 카탈로그, 기타판매문서, 기타교육문서, 기타비즈니스설명문서, YOUTUBE, 오너스매뉴얼 중 선택.

2. 지역 및 국가 정보
지역 (region): UNKNOWN, COMMON, A1(KOREA), A2(APAC), A3(CHINA), A4(INDIA), B1(NORTH AMERICA), B2(SOUTH AMERICA).
국가 (country): UNKNOWN, COMMON, US, Mexico, Canada 등 (영문 국가명 사용).
주의: 지역과 국가는 서로 연계되어야 하며, 확실하지 않으면 UNKNOWN을 사용해.

3. 차량 사양 정보
차종 (model): UNKNOWN, COMMON, 또는 설계코드 + PE여부 + (상품명) 형식.
예시: MQ4 PE (The all new Sorrento), CT (The Kia EV4).
XEV 타입 (xev): NULL (하이브리드 아닐 때), Hybrid, Plugin-Hybrid.

4. 버전 및 관리 정보
연식 (year): 시작연식(year1)과 종료연식(year2)을 구분. 없으면 NULL.
언어 (language): BCP-47 기반 (예: ko-KR, en-US).
버전 (version): SemVer 방식 (예: v1.0.0).
날짜 (updated_at): YYYY-MM-DD 형식.
파일형식 (file_format): ppt, pdf, html, web, video, string_link 등.

[Labeling Rules]
정확도 우선: 사람의 검토 시 90% 이상의 정확도를 유지할 수 있도록 정교하게 분석해.
UNKNOWN/NULL 활용: 문서 내에 명시적인 정보가 없는 경우 임의로 판단하지 말고 정책에 따라 UNKNOWN 또는 NULL을 부여해.
JSON 출력: 모든 결과는 반드시 아래 구조의 JSON 형식으로만 응답해.

[Output Format]
{
  "metadata": {
    "type": "string",
    "source": "string",
    "region": "string",
    "country": "string",
    "model": "string",
    "xev": "string | null",
    "year1": "string | null",
    "year2": "string | null",
    "language": "string",
    "version": "string",
    "updated_at": "YYYY-MM-DD",
    "file_format": "string"
  },
  "content_summary": "문서의 핵심 내용 요약 (1000자 이내)"
}
"""
    
    def generate_metadata(self, extracted_data: Dict, source_type: str = 'document') -> Dict:
        """Generate metadata from extracted text using Gemini API

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

            # Determine file format from file name
            file_format = self._determine_file_format(file_name, source_type)

            # Call Gemini API to extract metadata
            gemini_metadata = self._extract_metadata_with_gemini(full_text, file_format)

            # Combine with basic document information
            metadata = {
                # 'document_id': self._generate_document_id(file_name),
                # 'file_name': file_name,
                # 'upload_date': datetime.now().strftime('%Y-%m-%d'),
                # 'gcs_uri': gcs_uri,
                # 'page_count': len(extracted_data.get('pages', [])),
                # 'text_length': len(full_text),

                # Gemini-extracted metadata
                'type': gemini_metadata.get('type', 'UNKNOWN'),
                'source': gemini_metadata.get('source', 'UNKNOWN'),
                'region': gemini_metadata.get('region', 'UNKNOWN'),
                'country': gemini_metadata.get('country', 'UNKNOWN'),
                'model': gemini_metadata.get('model', 'UNKNOWN'),
                'xev': gemini_metadata.get('xev'),
                'year1': gemini_metadata.get('year1'),
                'year2': gemini_metadata.get('year2'),
                'language': gemini_metadata.get('language', 'UNKNOWN'),
                'version': gemini_metadata.get('version', 'v1.0.0'),
                'updated_at': gemini_metadata.get('updated_at', datetime.now().strftime('%Y-%m-%d')),
                'file_format': gemini_metadata.get('file_format', file_format),
                'content_summary': gemini_metadata.get('content_summary', ''),
            }

            self.logger.info(f"Metadata generated successfully for {file_name}")
            return metadata

        except Exception as e:
            self.logger.error(f"Error generating metadata: {str(e)}")
            raise
    
    def _extract_metadata_with_gemini(self, text: str, file_format: str) -> Dict:
        """Extract metadata using Gemini API

        Args:
            text: Document text
            file_format: File format (pdf, ppt, video, etc.)

        Returns:
            Dictionary containing extracted metadata
        """
        try:
            # Prepare the prompt
            user_prompt = f"""다음 문서를 분석하여 메타데이터를 추출해주세요.

파일 형식: {file_format}

문서 내용:
{text[:10000]}  # Limit to first 10000 characters to avoid token limits

위 문서를 분석하여 JSON 형식으로 메타데이터를 반환해주세요."""

            # Call Gemini API
            self.logger.info("Calling Gemini API for metadata extraction")
            response = self.model.generate_content(
                [self.system_prompt, user_prompt],
                generation_config={
                    'temperature': 0.1,  # Low temperature for consistent outputs
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 8192,
                }
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse JSON
            result = json.loads(response_text)

            # Extract metadata and content_summary
            metadata = result.get('metadata', {})
            metadata['content_summary'] = result.get('content_summary', '')

            self.logger.info("Gemini API metadata extraction successful")
            return metadata

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            self.logger.error(f"Response text: {response_text}")
            return self._get_default_metadata()
        except Exception as e:
            self.logger.error(f"Error calling Gemini API: {str(e)}")
            return self._get_default_metadata()

    def _get_default_metadata(self) -> Dict:
        """Return default metadata when Gemini API fails

        Returns:
            Dictionary with default metadata values
        """
        return {
            'type': 'UNKNOWN',
            'source': 'UNKNOWN',
            'region': 'UNKNOWN',
            'country': 'UNKNOWN',
            'model': 'UNKNOWN',
            'xev': None,
            'year1': None,
            'year2': None,
            'language': 'UNKNOWN',
            'version': 'v1.0.0',
            'updated_at': datetime.now().strftime('%Y-%m-%d'),
            'file_format': 'UNKNOWN',
            'content_summary': ''
        }

    def _determine_file_format(self, file_name: str, source_type: str) -> str:
        """Determine file format from file name

        Args:
            file_name: Name of the file
            source_type: Type of source ('document' or 'video')

        Returns:
            File format string
        """
        if source_type == 'video':
            return 'video'

        # Extract extension
        if '.' in file_name:
            ext = file_name.split('.')[-1].lower()
            format_mapping = {
                'pdf': 'pdf',
                'ppt': 'ppt',
                'pptx': 'ppt',
                'doc': 'doc',
                'docx': 'doc',
                'html': 'html',
                'htm': 'html',
                'txt': 'string_link',
            }
            return format_mapping.get(ext, 'unknown')

        return 'unknown'

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
