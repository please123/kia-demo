# Kia Metadata Generator - 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 1단계: 프로젝트 설정

#### Windows PC에서:

```cmd
# 1. 프로젝트 디렉토리로 이동
cd kia_metadata_generator

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화
venv\Scripts\activate

# 4. 패키지 설치
pip install -r requirements.txt
```

### 2단계: GCP 설정

#### A. GCS 버킷 생성
```bash
# gcloud CLI 사용
gsutil mb -l asia-northeast3 gs://kia-documents

# 폴더 구조 생성
gsutil mkdir gs://kia-documents/input/
gsutil mkdir gs://kia-documents/output/
gsutil mkdir gs://kia-documents/output/metadata/
```

#### B. Document AI Processor 생성
1. https://console.cloud.google.com/ai/document-ai 접속
2. "CREATE PROCESSOR" 클릭
3. Processor type: "Document OCR" 선택
4. Processor name: "kia-doc-processor" 입력
5. Region: "us" 또는 "asia-northeast3" 선택
6. CREATE 클릭
7. **Processor ID 복사** (나중에 필요)

#### C. 서비스 계정 생성
1. https://console.cloud.google.com/iam-admin/serviceaccounts 접속
2. "CREATE SERVICE ACCOUNT" 클릭
3. 이름: "kia-metadata-sa" 입력
4. "CREATE AND CONTINUE" 클릭
5. Role 추가:
   - Storage Admin
   - Document AI User
6. "DONE" 클릭
7. 생성된 서비스 계정 클릭 > Keys 탭 > ADD KEY > Create new key
8. Key type: JSON 선택
9. 다운로드된 JSON 파일을 `credentials/gcp-service-account.json`으로 저장

### 3단계: 환경 변수 설정

`.env.template`을 복사하여 `.env` 생성:

```bash
copy .env.template .env   # Windows
# 또는
cp .env.template .env     # Linux/Mac
```

`.env` 파일 편집:

```bash
# GCP 설정
GCP_PROJECT_ID=your-project-id              # GCP 프로젝트 ID
GCP_CREDENTIALS_PATH=./credentials/gcp-service-account.json

# Document AI 설정
DOCUMENTAI_PROCESSOR_ID=abc123def456        # 2단계-B에서 복사한 ID
DOCUMENTAI_LOCATION=us                      # 또는 asia-northeast3

# 단일 파일 처리
GCS_INPUT_PATH=gs://kia-documents/input/ev6_guide.pptx

# CSV 출력 경로
GCS_OUTPUT_BUCKET=kia-documents
GCS_OUTPUT_PATH=output/metadata/
```

### 4단계: 설정 검증

```bash
python test_setup.py
```

모든 테스트가 통과하면 ✅ 표시됩니다!

### 5단계: 문서 업로드 및 실행

#### 단일 파일 처리:

```bash
# 1. GCS에 파일 업로드
gsutil cp C:\path\to\your\ev6_guide.pptx gs://kia-documents/input/

# 2. .env 파일 확인 (GCS_INPUT_PATH가 올바른지)
# GCS_INPUT_PATH=gs://kia-documents/input/ev6_guide.pptx

# 3. 실행
python main.py
```

#### 여러 파일 일괄 처리:

```bash
# 1. GCS에 여러 파일 업로드
gsutil cp C:\path\to\docs\*.pptx gs://kia-documents/input/

# 2. .env 파일 수정
# GCS_INPUT_FOLDER=gs://kia-documents/input/

# 3. 배치 모드로 실행
python main.py --batch
```

## 📊 실행 결과 확인

실행이 완료되면:

1. **GCS에서 확인**:
   ```bash
   gsutil ls gs://kia-documents/output/metadata/
   ```

2. **로컬에서 확인**:
   ```
   data/local_output/ 폴더에 CSV 백업 파일이 생성됩니다
   ```

3. **CSV 다운로드**:
   ```bash
   gsutil cp gs://kia-documents/output/metadata/kia_metadata_*.csv ./
   ```

## 🔧 실행 예시

### 예시 1: EV6 가이드 문서 처리

```bash
# 파일 업로드
gsutil cp EV6_UserGuide.pptx gs://kia-documents/input/

# .env 설정
GCS_INPUT_PATH=gs://kia-documents/input/EV6_UserGuide.pptx

# 실행
python main.py
```

**출력**:
```
==============================================================
Starting Kia Metadata Generator - Single File Mode
==============================================================
Initializing components...

📄 Processing: gs://kia-documents/input/EV6_UserGuide.pptx
   Total pages: 25
   Total text length: 15423 characters

🔍 Generating metadata...
   Car model: EV6
   Car type: Electric

💾 Saving metadata to GCS...

✅ CSV saved to GCS: gs://kia-documents/output/metadata/EV6_UserGuide_metadata.csv
✅ CSV saved locally: data/local_output/EV6_UserGuide_metadata.csv
```

### 예시 2: 여러 차량 문서 일괄 처리

```bash
# 여러 파일 업로드
gsutil cp EV6_Guide.pptx gs://kia-documents/input/
gsutil cp Sportage_Intro.pptx gs://kia-documents/input/
gsutil cp Carnival_Spec.pptx gs://kia-documents/input/

# .env 설정
GCS_INPUT_FOLDER=gs://kia-documents/input/

# 배치 실행
python main.py --batch
```

**출력**:
```
==============================================================
Starting Kia Metadata Generator - Batch Mode
==============================================================

📁 Listing files in gs://kia-documents/input/
Found 3 files to process

Processing files: 100%|████████████| 3/3 [00:45<00:00, 15.2s/file]

📄 Processing: gs://kia-documents/input/EV6_Guide.pptx
✅ Successfully processed: EV6_Guide.pptx

📄 Processing: gs://kia-documents/input/Sportage_Intro.pptx
✅ Successfully processed: Sportage_Intro.pptx

📄 Processing: gs://kia-documents/input/Carnival_Spec.pptx
✅ Successfully processed: Carnival_Spec.pptx

💾 Saving metadata for 3 files to GCS...

==============================================================
KIA METADATA GENERATION REPORT
==============================================================

Total Documents Processed: 3
Generation Date: 2024-01-29 14:30:00

Car Model Distribution:
  - EV6: 1
  - Sportage: 1
  - Carnival: 1

Source Type Distribution:
  - document: 3

Average Page Count: 22.33

==============================================================

✅ CSV saved to GCS: gs://kia-documents/output/metadata/kia_batch_metadata_20240129_143000.csv
```

## ❓ 자주 묻는 질문 (FAQ)

### Q1: "Permission denied" 오류가 발생합니다
**A**: 서비스 계정 권한을 확인하세요:
```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:kia-metadata-sa@*"
```

### Q2: Document AI가 텍스트를 제대로 추출하지 못합니다
**A**: 
- PPT 파일인 경우, PDF로 변환 후 처리해보세요
- Processor type을 "Form Parser"로 변경해보세요

### Q3: 처리 속도가 느립니다
**A**:
- Document AI는 페이지당 처리 시간이 있습니다 (약 1-2초/페이지)
- 큰 파일은 분할하여 처리하는 것이 좋습니다

### Q4: 특정 차량 모델이 인식되지 않습니다
**A**: `modules/metadata_generator.py`의 `car_models` 리스트에 모델명을 추가하세요:
```python
self.car_models = [
    'EV6', 'EV9', 'Niro', 'Soul', 'Sportage', 
    'YourNewModel'  # 여기에 추가
]
```

## 📈 성능 최적화 팁

1. **배치 크기 조절**: 한 번에 처리할 파일 수를 제한하세요 (권장: 10개 이하)
2. **파일 크기**: 대용량 파일(>50MB)은 분할하여 처리
3. **동시 처리**: 여러 프로세스로 병렬 처리 가능 (추후 구현 가능)

## 🔐 보안 주의사항

- ⚠️ `.env` 파일과 `credentials/` 폴더를 절대 공유하지 마세요
- ⚠️ Git에 커밋하지 마세요 (`.gitignore`에 이미 추가됨)
- 🔄 정기적으로 서비스 계정 키를 교체하세요

## 📞 지원

문제가 있으면:
1. `test_setup.py`를 실행하여 설정을 확인하세요
2. `--verbose` 옵션으로 상세 로그를 확인하세요
3. 팀에 문의하세요

---

**즐거운 메타데이터 생성 되세요! 🚗✨**
