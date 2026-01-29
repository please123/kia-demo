# GCP Credentials

이 디렉토리에 GCP 서비스 계정 키 파일을 저장하세요.

## 파일 이름
`gcp-service-account.json`

## 생성 방법

1. GCP Console (https://console.cloud.google.com/) 접속
2. IAM & Admin > Service Accounts 메뉴로 이동
3. "CREATE SERVICE ACCOUNT" 클릭
4. 서비스 계정 이름 입력 (예: kia-metadata-generator)
5. 다음 권한 부여:
   - Storage Admin
   - Document AI User
6. "CREATE KEY" 클릭
7. Key type: JSON 선택
8. 다운로드된 JSON 파일을 이 디렉토리에 `gcp-service-account.json`으로 저장

## 보안 주의사항

⚠️ **중요**: 이 파일은 절대 Git에 커밋하지 마세요!

- `.gitignore` 파일에 이미 추가되어 있습니다
- 이 파일을 공유하거나 공개 저장소에 업로드하지 마세요
- 정기적으로 키를 교체하는 것이 좋습니다
