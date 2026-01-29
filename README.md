# Kia Metadata Generator

기아자동차 문서(PPT, PDF 등)에서 텍스트를 추출하고 메타데이터를 생성하여 GCS에 CSV 파일로 저장하는 시스템입니다.

## 📋 프로젝트 개요

이 프로젝트는 다음과 같은 작업을 수행합니다:

1. **GCS에서 문서 읽기**: 수동으로 업로드된 문서를 GCS에서 읽어옵니다
2. **텍스트 추출**: Google Document AI를 사용하여 문서에서 텍스트를 추출합니다
3. **메타데이터 생성**: 추출된 텍스트를 분석하여 차량 정보, 키워드, 요약 등의 메타데이터를 생성합니다
4. **CSV 저장**: 생성된 메타데이터를 CSV 형식으로 GCS에 저장합니다

## 🏗️ 프로젝트 구조

```
kia_metadata_generator/
│
├── config/
│   ├── __init__.py
│   └── settings.py              # 환경 설정 관리
│
├── modules/
│   ├── __init__.py
│   ├── text_extractor.py        # Document AI 텍스트 추출
│   ├── metadata_generator.py    # 메타데이터 생성
│   └── csv_handler.py           # CSV 생성 및 GCS 업로드
│
├── utils/
│   ├── __init__.py
│   ├── gcs_utils.py             # GCS 헬퍼 함수
│   └── logger.py                # 로깅 유틸리티
│
├── credentials/
│   └── gcp-service-account.json # GCP 인증 키 (직접 추가 필요)
│
├── data/
│   └── local_output/            # 로컬 백업 CSV 저장소
│
├── main.py                      # 메인 실행 파일
├── requirements.txt             # Python 의존성
├── .env.template                # 환경 변수 템플릿
└── README.md                    # 이 파일
```

## 🚀 설치 방법

### 1. 저장소 클론 또는 다운로드

```bash
# 프로젝트 디렉토리로 이동
cd kia_metadata_generator
```

### 2. Python 가상환경 생성 (권장)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

## ⚙️ 설정 방법

### 1. GCP 프로젝트 설정

#### a) Google Cloud Storage (GCS) 설정
1. GCP Console에서 버킷 생성
2. 입력 파일용 폴더 생성 (예: `input/`)
3. 출력 CSV용 폴더 생성 (예: `output/metadata/`)

#### b) Document AI 설정
1. GCP Console에서 Document AI API 활성화
2. Processor 생성 (OCR Processor 또는 Form Parser)
3. Processor ID 복사

#### c) 서비스 계정 생성
1. GCP Console에서 서비스 계정 생성
2. 다음 권한 부여:
   - Storage Admin
   - Document AI User
3. JSON 키 파일 다운로드
4. 키 파일을 `credentials/gcp-service-account.json`으로 저장

### 2. 환경 변수 설정

`.env.template` 파일을 복사하여 `.env` 파일 생성:

```bash
cp .env.template .env
```

`.env` 파일을 편집하여 실제 값으로 수정:

```bash
# GCP 설정
GCP_PROJECT_ID=your-project-id
GCP_CREDENTIALS_PATH=./credentials/gcp-service-account.json

# Document AI 설정
DOCUMENTAI_PROCESSOR_ID=your-processor-id
DOCUMENTAI_LOCATION=us

# GCS 경로 설정 (단일 파일)
GCS_INPUT_PATH=gs://kia-documents/input/presentation.pptx

# GCS 경로 설정 (폴더 - 일괄 처리시)
# GCS_INPUT_FOLDER=gs://kia-documents/input/

# CSV 출력 경로
GCS_OUTPUT_BUCKET=kia-documents
GCS_OUTPUT_PATH=output/metadata/
```

## 📖 사용 방법

### 단일 파일 처리

1. GCS에 문서 업로드:
   ```bash
   gsutil cp your_presentation.pptx gs://kia-documents/input/
   ```

2. `.env` 파일에서 `GCS_INPUT_PATH` 설정:
   ```bash
   GCS_INPUT_PATH=gs://kia-documents/input/your_presentation.pptx
   ```

3. 스크립트 실행:
   ```bash
   python main.py
   ```

### 여러 파일 일괄 처리

1. GCS에 여러 문서 업로드:
   ```bash
   gsutil cp *.pptx gs://kia-documents/input/
   ```

2. `.env` 파일에서 `GCS_INPUT_FOLDER` 설정:
   ```bash
   GCS_INPUT_FOLDER=gs://kia-documents/input/
   ```

3. 배치 모드로 스크립트 실행:
   ```bash
   python main.py --batch
   ```

### 옵션

- `--batch`: 일괄 처리 모드 (폴더 내 모든 파일 처리)
- `--verbose`: 상세 로그 출력

예시:
```bash
python main.py --batch --verbose
```

## 📊 출력 형식

생성되는 CSV 파일은 다음과 같은 컬럼을 포함합니다:

| 컬럼명 | 설명 |
|--------|------|
| document_id | 문서 고유 ID |
| source_type | 소스 타입 (document/video) |
| file_name | 파일명 |
| upload_date | 처리 날짜 |
| car_model | 차량 모델 (EV6, Sportage 등) |
| car_type | 차량 타입 (SUV, Sedan 등) |
| engine_type | 엔진 타입 (Electric, Hybrid 등) |
| price | 가격 정보 |
| page_count | 페이지 수 |
| text_length | 추출된 텍스트 길이 |
| features | 주요 특징 |
| keywords | 키워드 |
| summary | 요약 |
| specifications | 기술 사양 |
| gcs_uri | GCS 원본 파일 경로 |

## 🔍 메타데이터 추출 로직

### 차량 모델 인식
- EV6, EV9, Niro, Sportage, Carnival 등 기아 차량 모델명 자동 인식

### 차량 타입 분류
- SUV, Sedan, Electric, Hybrid 등 차량 타입 자동 분류

### 가격 정보 추출
- 한국어 원화 표기 인식 (예: "3,000만원")
- 달러 표기 인식 (예: "$30,000")

### 키워드 추출
- 문서 내 빈도수 기반 키워드 추출
- 불용어 필터링

### 요약 생성
- 문서의 첫 번째 의미있는 단락 추출

## 🛠️ 트러블슈팅

### 인증 오류
```
Error: Could not automatically determine credentials
```
**해결방법**: 
- `credentials/gcp-service-account.json` 파일이 존재하는지 확인
- `.env` 파일의 `GCP_CREDENTIALS_PATH` 경로가 올바른지 확인

### Document AI 오류
```
Error: Permission denied on resource project
```
**해결방법**:
- 서비스 계정에 Document AI User 권한이 있는지 확인
- Document AI API가 활성화되어 있는지 확인

### GCS 업로드 오류
```
Error: 403 Forbidden
```
**해결방법**:
- 서비스 계정에 Storage Admin 권한이 있는지 확인
- GCS 버킷이 존재하는지 확인

## 📝 로그 확인

실행 중 로그는 콘솔에 실시간으로 출력됩니다:

```
2024-01-29 10:00:00 - kia_metadata - INFO - Loading settings from .env file...
2024-01-29 10:00:01 - kia_metadata - INFO - ✅ All required settings are valid
2024-01-29 10:00:02 - kia_metadata.extractor - INFO - Processing document: gs://...
```

## 🔄 확장 가능성

이 시스템은 다음과 같이 확장할 수 있습니다:

1. **YouTube 비디오 지원**: 
   - `youtube-dl` 또는 `yt-dlp`를 사용하여 비디오 다운로드
   - 자막 추출 또는 음성-텍스트 변환

2. **더 많은 파일 형식 지원**:
   - PDF, DOCX, XLSX 등

3. **고급 NLP 기능**:
   - 개체명 인식 (NER)
   - 감정 분석
   - 주제 모델링

4. **데이터베이스 통합**:
   - CSV 대신 BigQuery나 Cloud SQL 저장

## 📄 라이선스

이 프로젝트는 기아자동차 내부 사용을 위한 것입니다.

## 👥 기여자

- 개발자: [Your Name]
- 날짜: 2024-01-29

## 📞 문의

문제가 있거나 질문이 있으시면 팀에 문의하세요.
