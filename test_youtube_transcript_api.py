"""
Vertex AI Gemini를 이용한 동영상 자막 추출 테스트
- VIDEO_PATH 환경변수에 지정된 GCS 파일(gs://)에서 자막 추출
- GCS 파일을 직접 참조 (다운로드 없음)
- Verbatim transcription (있는 그대로 받아쓰기)
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env 먼저 로드 (GOOGLE_APPLICATION_CREDENTIALS 설정 위해)
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)

# GCP 인증 설정
credentials_path = os.getenv('GCP_CREDENTIALS_PATH')
if credentials_path:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

import vertexai
from vertexai.generative_models import GenerativeModel, Part


def main():
    project_id = os.getenv('GCP_PROJECT_ID')
    video_path = os.getenv('VIDEO_PATH')
    location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')

    if not project_id:
        print("[ERROR] GCP_PROJECT_ID 환경변수가 설정되어 있지 않습니다.")
        sys.exit(1)
    if not video_path:
        print("[ERROR] VIDEO_PATH 환경변수가 설정되어 있지 않습니다.")
        sys.exit(1)
    if not video_path.startswith('gs://'):
        print("[ERROR] VIDEO_PATH는 GCS 경로(gs://...)여야 합니다.")
        sys.exit(1)

    print(f"Project ID  : {project_id}")
    print(f"Location    : {location}")
    print(f"Video Path  : {video_path}")
    print("=" * 60)

    # ── Vertex AI 초기화 ──
    print("Step 1) Vertex AI 초기화 ...")
    try:
        vertexai.init(project=project_id, location=location)
        print(f"  [OK] Vertex AI 초기화 완료")
    except Exception as e:
        print(f"  [FAIL] Vertex AI 초기화 실패: {e}")
        sys.exit(1)

    print("-" * 60)

    # ── 자막 추출 ──
    print("Step 2) Gemini 2.0 Flash로 자막 추출 ...")
    try:
        model = GenerativeModel('gemini-2.0-flash')

        # GCS 파일을 직접 참조
        video_part = Part.from_uri(video_path, mime_type="video/mp4")

        prompt = """첨부된 파일의 음성을 토씨 하나 틀리지 않고 그대로 받아쓰기(Verbatim transcription)해줘.
음성 중간의 '음', '어'와 같은 감탄사나 반복되는 단어도 생략하지 말고 포함해줘.
문법 교정이나 문장 다듬기를 절대 하지 마."""

        print("  Generating transcript...")
        response = model.generate_content(
            [video_part, prompt],
            generation_config={
                'temperature': 0.1,
                'max_output_tokens': 8192,
            }
        )

        print("  [OK] 자막 추출 완료")
        print("-" * 60)

        # 자막 출력
        print("\n[TRANSCRIPT]\n")
        print(response.text)

        print("\n" + "=" * 60)
        print("[SUCCESS] 자막 추출 완료")

    except Exception as e:
        print(f"  [FAIL] 자막 추출 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
