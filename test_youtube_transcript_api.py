"""
Gemini 1.5 Flash를 이용한 동영상 자막 추출 테스트
- VIDEO_PATH 환경변수에 지정된 동영상 파일에서 자막 추출
- Verbatim transcription (있는 그대로 받아쓰기)
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import google.generativeai as genai


def main():
    # ── .env 로드 ──
    env_path = Path(__file__).resolve().parent / '.env'
    load_dotenv(env_path)

    api_key = os.getenv('GOOGLE_API_KEY')
    video_path = os.getenv('VIDEO_PATH')

    if not api_key:
        print("[ERROR] GOOGLE_API_KEY 환경변수가 설정되어 있지 않습니다.")
        sys.exit(1)
    if not video_path:
        print("[ERROR] VIDEO_PATH 환경변수가 설정되어 있지 않습니다.")
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"[ERROR] 동영상 파일을 찾을 수 없습니다: {video_path}")
        sys.exit(1)

    print(f"Video Path  : {video_path}")
    print(f"File Size   : {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    print("=" * 60)

    # ── Gemini API 설정 ──
    print("Step 1) Gemini API 연결 및 파일 업로드 ...")
    try:
        genai.configure(api_key=api_key)

        # 동영상 파일 업로드
        print(f"  Uploading video file...")
        video_file = genai.upload_file(path=video_path)
        print(f"  [OK] 파일 업로드 완료: {video_file.name}")

        # 파일 처리 대기
        import time
        while video_file.state.name == "PROCESSING":
            print("  Processing video...")
            time.sleep(5)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError(f"파일 처리 실패: {video_file.state.name}")

        print(f"  [OK] 파일 처리 완료: {video_file.state.name}")

    except Exception as e:
        print(f"  [FAIL] Gemini API 연결 또는 파일 업로드 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("-" * 60)

    # ── 자막 추출 ──
    print("Step 2) Gemini 1.5 Flash로 자막 추출 ...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = """첨부된 파일의 음성을 토씨 하나 틀리지 않고 그대로 받아쓰기(Verbatim transcription)해줘.
음성 중간의 '음', '어'와 같은 감탄사나 반복되는 단어도 생략하지 말고 포함해줘.
문법 교정이나 문장 다듬기를 절대 하지 마."""

        print("  Generating transcript...")
        response = model.generate_content(
            [video_file, prompt],
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

    finally:
        # 업로드된 파일 삭제 (선택적)
        try:
            genai.delete_file(video_file.name)
            print(f"  [INFO] 업로드된 파일 삭제 완료: {video_file.name}")
        except:
            pass


if __name__ == "__main__":
    main()
