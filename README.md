# MSDS 프로그램 - KOSHA API 연동 모듈

## 📁 파일 구성

```
your_project/
├── kosha_api_extended.py      ← 프로젝트 루트에 배치
├── pages/
│   ├── 11_11_독성에_관한_정보.py
│   ├── 12_12_환경에_미치는_영향.py
│   └── 15_15_법적_규제현황.py
└── ...
```

## 🔧 설치 방법

### 1. 파일 복사
- `kosha_api_extended.py` → **프로젝트 루트 폴더**에 복사
- `11_11_독성에_관한_정보.py` → `pages/` 폴더에 덮어쓰기
- `12_12_환경에_미치는_영향.py` → `pages/` 폴더에 덮어쓰기
- `15_15_법적_규제현황.py` → `pages/` 폴더에 덮어쓰기

### 2. 의존성 설치
```bash
pip install requests
```

## 🚀 사용 방법

### Streamlit 앱에서 사용

1. **섹션 3**에서 구성성분의 **물질명**과 **CAS 번호** 입력
2. **섹션 11, 12, 15** 페이지로 이동
3. 상단의 **"🔗 KOSHA API 연동"** 클릭하여 열기
4. **"🔍 KOSHA API에서 조회"** 버튼 클릭
5. 조회 결과 확인 후 양식에 직접 입력

### Python 스크립트로 직접 사용

```python
from kosha_api_extended import get_msds_sections_11_12_15

# 아세톤 조회
result = get_msds_sections_11_12_15("67-64-1")

if result['success']:
    print(f"물질명: {result['name']}")
    print(f"독성정보: {result['section11_toxicity']}")
    print(f"환경영향: {result['section12_environmental']}")
    print(f"법적규제: {result['section15_regulations']}")
```

### CLI 사용

```bash
# 단일 물질 조회
python kosha_api_extended.py --cas 67-64-1

# 여러 물질 일괄 조회
python kosha_api_extended.py --cas-list "67-64-1,108-88-3,1330-20-7"

# 결과 JSON 파일로 저장
python kosha_api_extended.py --cas 67-64-1 -o result.json
```

## 📋 공식 양식 (별표 4) 기준 항목

### 11. 독성에 관한 정보
- 가. 가능성이 높은 노출 경로에 관한 정보
- 나. 건강 유해성 정보
  - ○ 급성 독성 (노출 가능한 모든 경로에 대해 기재)
  - ○ 피부 부식성 또는 자극성
  - ○ 심한 눈 손상 또는 자극성
  - ○ 호흡기 과민성
  - ○ 피부 과민성
  - ○ 발암성
  - ○ 생식세포 변이원성
  - ○ 생식독성
  - ○ 특정 표적장기 독성 (1회 노출)
  - ○ 특정 표적장기 독성 (반복 노출)
  - ○ 흡인 유해성

### 12. 환경에 미치는 영향
- 가. 생태독성
- 나. 잔류성 및 분해성
- 다. 생물 농축성
- 라. 토양 이동성
- 마. 기타 유해 영향

### 15. 법적 규제현황
- 가. 산업안전보건법에 의한 규제
- 나. 화학물질관리법에 의한 규제
- 다. 화학물질의 등록 및 평가 등에 관한 법률에 의한 규제
- 라. 위험물안전관리법에 의한 규제
- 마. 폐기물관리법에 의한 규제
- 바. 기타 국내 및 외국법에 의한 규제

## ⚠️ 주의사항

1. **API 키**: 기본 API 키가 포함되어 있지만, 필요시 `set_api_key()` 함수로 변경 가능
2. **호출 간격**: 연속 호출 시 0.3초 간격 자동 적용 (API 부하 방지)
3. **데이터 검증**: API 데이터는 참고용이므로, 반드시 검토 후 사용
4. **네트워크**: 인터넷 연결 필요 (KOSHA 서버 접속)

## 🔗 참고 링크

- KOSHA 화학물질정보시스템: https://msds.kosha.or.kr
- 화학물질정보시스템: https://icis.me.go.kr
