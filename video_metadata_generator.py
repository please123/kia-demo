"""
Video metadata generation module - YouTube 동영상 자막 추출 및 메타데이터 생성
YouTube Data API v3를 활용하여 동영상 정보 및 자막을 파싱
"""
import os
import re
import logging
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

from metadata_generator import MetadataGenerator


class VideoMetadataGenerator:
    """YouTube 동영상에서 자막을 추출하고 메타데이터를 생성"""

    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger('kia_metadata.video')

        api_key = api_key or os.getenv('YOUTUBE_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError(
                "YouTube API key must be provided or set in "
                "YOUTUBE_API_KEY / GOOGLE_API_KEY environment variable"
            )

        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.metadata_generator = MetadataGenerator()

    # ------------------------------------------------------------------
    # URL -> video ID 변환
    # ------------------------------------------------------------------
    @staticmethod
    def extract_video_id(url: str) -> str:
        """YouTube URL에서 video ID를 추출"""
        parsed = urlparse(url)

        if parsed.hostname in ('youtu.be',):
            return parsed.path.lstrip('/')

        if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if parsed.path == '/watch':
                return parse_qs(parsed.query).get('v', [''])[0]
            if parsed.path.startswith(('/embed/', '/v/')):
                return parsed.path.split('/')[2]

        raise ValueError(f"Cannot extract video ID from URL: {url}")

    # ------------------------------------------------------------------
    # YouTube Data API v3 - 동영상 정보 조회
    # ------------------------------------------------------------------
    def get_video_info(self, video_id: str) -> Dict:
        """YouTube Data API v3로 동영상 snippet 정보를 가져온다."""
        self.logger.info(f"Fetching video info for {video_id}")
        response = self.youtube.videos().list(
            part='snippet,contentDetails',
            id=video_id
        ).execute()

        items = response.get('items', [])
        if not items:
            raise ValueError(f"Video not found: {video_id}")

        snippet = items[0]['snippet']
        return {
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'channel': snippet.get('channelTitle', ''),
            'published_at': snippet.get('publishedAt', ''),
            'default_language': snippet.get('defaultLanguage', ''),
            'default_audio_language': snippet.get('defaultAudioLanguage', ''),
        }

    # ------------------------------------------------------------------
    # YouTube Data API v3 - 자막 목록 조회
    # ------------------------------------------------------------------
    def list_captions(self, video_id: str) -> list:
        """YouTube Data API v3의 captions.list 로 사용 가능한 자막 목록 조회"""
        self.logger.info(f"Listing captions for {video_id}")
        response = self.youtube.captions().list(
            part='snippet',
            videoId=video_id
        ).execute()
        return response.get('items', [])

    # ------------------------------------------------------------------
    # 자막 텍스트 가져오기 (youtube-transcript-api 활용)
    # ------------------------------------------------------------------
    def get_transcript(self, video_id: str, languages: tuple = ('ko', 'en')) -> str:
        """youtube_transcript_api를 사용하여 자막 전문 텍스트를 반환.

        YouTube Data API v3의 captions.download는 OAuth 인증이 필요하므로,
        공개 자막 텍스트는 youtube_transcript_api를 사용하여 가져온다.
        """
        self.logger.info(f"Fetching transcript for {video_id} (languages={languages})")
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 지정 언어 중 수동 자막 우선 시도
            try:
                transcript = transcript_list.find_transcript(list(languages))
            except Exception:
                # 자동 생성 자막이라도 가져오기
                transcript = transcript_list.find_generated_transcript(list(languages))

            entries = transcript.fetch()
            # entries 는 FetchedTranscript 객체이며, 각 항목은 dict-like
            text_parts = [entry.get('text', '') if isinstance(entry, dict) else getattr(entry, 'text', str(entry))
                          for entry in entries]
            return '\n'.join(text_parts)

        except Exception as e:
            self.logger.warning(f"Failed to fetch transcript: {e}")
            return ''

    # ------------------------------------------------------------------
    # 통합 처리: URL → 자막 추출 → 메타데이터 생성
    # ------------------------------------------------------------------
    def process_video(self, youtube_url: str, gcs_helper=None, save_parsing_path: str = None) -> Dict:
        """YouTube URL로부터 자막을 추출하고 메타데이터를 생성하여 반환
        
        Args:
            youtube_url: YouTube URL
            gcs_helper: Optional GCSHelper instance for saving transcript
            save_parsing_path: Optional path to save transcript
        """
        video_id = self.extract_video_id(youtube_url)
        self.logger.info(f"Processing video: {video_id} ({youtube_url})")

        # 1) 동영상 정보
        video_info = self.get_video_info(video_id)
        self.logger.info(f"Video title: {video_info['title']}")

        # 2) 자막 텍스트
        transcript_text = self.get_transcript(video_id)
        if not transcript_text:
            self.logger.warning("No transcript available; using video description as fallback")
            transcript_text = video_info.get('description', '')

        # 3) MetadataGenerator에 전달할 extracted_data 구성
        full_text = (
            f"[Video Title] {video_info['title']}\n"
            f"[Channel] {video_info['channel']}\n"
            f"[Published] {video_info['published_at']}\n\n"
            f"[Transcript]\n{transcript_text}"
        )

        extracted_data = {
            'full_text': full_text,
            'gcs_uri': youtube_url,
        }

        # Save transcript if requested
        if gcs_helper and save_parsing_path:
            try:
                self.logger.info(f"Saving transcript to {save_parsing_path}")
                gcs_helper.upload_from_string(
                    bucket_name=save_parsing_path.split('/')[2],  # gs://bucket/path...
                    blob_name='/'.join(save_parsing_path.split('/')[3:]),
                    content=full_text,
                    content_type='text/plain',
                    encoding='utf-8-sig'
                )
            except Exception as e:
                self.logger.error(f"Failed to save transcript: {e}")

        # 4) Gemini 기반 메타데이터 생성
        metadata = self.metadata_generator.generate_metadata(
            extracted_data, source_type='video'
        )
        return metadata
