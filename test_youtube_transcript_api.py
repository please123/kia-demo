"""
YouTube Data API v3 연결 확인 및 자막 추출 테스트
- Step 1: API 키 로드 및 YouTube Data API v3 연결 확인 (videos.list)
- Step 2: captions.list 로 자막 목록 조회
- Step 3: youtube_transcript_api 로 자막 텍스트 추출 및 출력
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """YouTube URL에서 video ID 추출"""
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be',):
        return parsed.path.lstrip('/')
    if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [''])[0]
        if parsed.path.startswith(('/embed/', '/v/')):
            return parsed.path.split('/')[2]
    raise ValueError(f"Cannot extract video ID from URL: {url}")


def main():
    # ── .env 로드 ──
    env_path = Path(__file__).resolve().parent / '.env'
    load_dotenv(env_path)

    api_key = os.getenv('GOOGLE_API_KEY')
    youtube_url = os.getenv('YOUTUBE_URL')

    if not api_key:
        print("[ERROR] GOOGLE_API_KEY 환경변수가 설정되어 있지 않습니다.")
        sys.exit(1)
    if not youtube_url:
        print("[ERROR] YOUTUBE_URL 환경변수가 설정되어 있지 않습니다.")
        sys.exit(1)

    video_id = extract_video_id(youtube_url)
    print(f"YouTube URL : {youtube_url}")
    print(f"Video ID    : {video_id}")
    print("=" * 60)

    # ── Step 1: YouTube Data API v3 연결 확인 (videos.list) ──
    print("Step 1) YouTube Data API v3 연결 확인 (videos.list) ...")
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()

        items = response.get('items', [])
        if not items:
            print(f"  [WARN] 동영상을 찾을 수 없습니다: {video_id}")
            sys.exit(1)

        snippet = items[0]['snippet']
        print(f"  [OK] API 연결 성공")
        print(f"  Title   : {snippet.get('title')}")
        print(f"  Channel : {snippet.get('channelTitle')}")
        print(f"  Published: {snippet.get('publishedAt')}")
    except Exception as e:
        print(f"  [FAIL] API 연결 실패: {e}")
        sys.exit(1)

    print("-" * 60)

    # ── Step 2: captions.list 로 자막 목록 조회 ──
    print("Step 2) captions.list 로 자막 목록 조회 ...")
    try:
        captions_response = youtube.captions().list(
            part='snippet',
            videoId=video_id
        ).execute()

        caption_items = captions_response.get('items', [])
        if not caption_items:
            print("  [WARN] 등록된 자막 트랙이 없습니다.")
        else:
            for cap in caption_items:
                s = cap['snippet']
                print(f"  - id: {cap['id']}  language: {s['language']}  "
                      f"name: \"{s.get('name', '')}\"  trackKind: {s.get('trackKind')}")
    except Exception as e:
        print(f"  [WARN] captions.list 호출 실패 (권한 제한일 수 있음): {e}")

    print("-" * 60)

    # ── Step 3: 자막 텍스트 추출 (youtube_transcript_api) ──
    print("Step 3) 자막 텍스트 추출 (youtube_transcript_api) ...")
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # 사용 가능한 자막 목록 출력
        print("  Available transcripts:")
        for t in transcript_list:
            print(f"    - {t.language} ({t.language_code})  generated={t.is_generated}")

        # ko → en 순으로 탐색
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['ko', 'en'])
        except Exception:
            transcript = transcript_list.find_generated_transcript(['ko', 'en'])

        print(f"  Selected : {transcript.language} ({transcript.language_code})")
        print("-" * 60)

        entries = transcript.fetch()
        print(f"  Total entries: {len(entries)}")
        print()

        # 전체 자막 출력
        for i, entry in enumerate(entries):
            text = entry['text'] if isinstance(entry, dict) else getattr(entry, 'text', str(entry))
            print(f"  [{i+1:04d}] {text}")

        print()
        print("=" * 60)
        print("[SUCCESS] 자막 추출 완료")

    except Exception as e:
        print(f"  [FAIL] 자막 추출 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
