# 매출 데이터 분석기 (Sales Data Analyzer)

AI 기반 계층적 매출 데이터 분석 및 트렌드 요약 시스템

## 📋 Prerequisites

### 시스템 요구사항
- Python 3.8+
- AWS 계정 및 Bedrock 서비스 액세스 권한
- 인터넷 연결

### AWS 설정
```bash
# AWS CLI 설치 및 구성
pip install awscli
aws configure
```

### 필요한 AWS 권한
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-3-5-sonnet-20240620-v1:0"
            ]
        }
    ]
}
```

## 🚀 설치

### 1. 의존성 설치
```bash
pip install streamlit boto3
```

### 2. 프로젝트 클론/다운로드
```bash
# 파일 다운로드 후
cd /path/to/sales_analyzer
```

### 3. AWS 자격 증명 설정
```bash
# 방법 1: AWS CLI 구성
aws configure

# 방법 2: 환경 변수 설정
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## 🏗️ 아키텍처

### 전체 시스템 아키텍처
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │───▶│  Sales Analyzer  │───▶│  AWS Bedrock    │
│                 │    │                  │    │  Claude Models  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   JSON Input    │    │  Data Processing │    │   AI Analysis   │
│   Validation    │    │   & Extraction   │    │   & Summary     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 데이터 처리 플로우
```
JSON 입력
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    extract_metrics_with_path_and_comment     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 카테고리    │  │ 경로 추적   │  │ 메트릭 & 코멘트     │  │
│  │ 순회        │─▶│ (path)      │─▶│ 추출               │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    make_summary_inputs_with_comment         │
│  각 메트릭을 Claude AI 입력 형식으로 변환                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                         BedrockClaude                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 개별 요약   │  │ 전체 요약   │  │ 계층적 주석         │  │
│  │ 생성        │─▶│ 생성        │─▶│ 추가               │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    create_footnote_references               │
│  계층별 카테고리 주석 생성 및 텍스트 매핑                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
결과 출력 (UI)
```

## 🔧 주요 함수 분석

### 1. `BedrockClaude` 클래스
```python
class BedrockClaude:
    def __init__(self):
        # Claude 4.0 (Sonnet v2) 및 3.7 (Sonnet v1) 모델 설정
    
    def invoke_claude(self, prompt):
        # Fallback 메커니즘: 4.0 실패 시 3.7로 자동 전환
```

**기능**: AWS Bedrock을 통한 Claude AI 모델 호출 및 Fallback 처리

### 2. `extract_metrics_with_path_and_comment`
```python
def extract_metrics_with_path_and_comment(data, path=None, comments=None):
    # 재귀적으로 JSON 구조 탐색
    # 각 메트릭에 대해 전체 경로와 코멘트 추적
    # 반환: 메트릭 리스트 (경로, 코멘트, 제품 정보 포함)
```

**플로우**:
```
JSON 입력 → 재귀 탐색 → 경로 추적 → 메트릭 추출 → 구조화된 데이터 반환
```

### 3. `extract_categories_and_keywords`
```python
def extract_categories_and_keywords(data, categories=None):
    # 모든 카테고리명 추출 (중복 제거)
    # UI 키워드 섹션용 데이터 생성
```

### 4. `create_footnote_references`
```python
def create_footnote_references(summary_text, metrics_info):
    # 계층별 카테고리 경로 생성
    # 주석 번호 할당 (계층 순서대로)
    # 텍스트 내 카테고리명에 주석 추가
```

**계층적 주석 시스템**:
```
전자제품[1]                    ← 최상위
├── 가전제품[2]                ← 중간 계층
│   ├── TV[3]                 ← 세부 항목
│   └── 냉장고[4]
└── 모바일기기[5]
    ├── 스마트폰[6]
    └── 태블릿[7]
```

### 5. `make_summary_inputs_with_comment`
```python
def make_summary_inputs_with_comment(metrics_info):
    # 메트릭 정보를 Claude AI 입력 형식으로 변환
    # 경로, 코멘트, 제품 정보를 하나의 문자열로 결합
```

## 📊 데이터 구조

### JSON 입력 형식
```json
{
  "category": "전자제품",
  "comment": "시장 전반 코멘트",
  "subcategories": [
    {
      "category": "가전제품",
      "comment": "중간 계층 코멘트",
      "subcategories": [
        {
          "category": "TV",
          "comment": "세부 카테고리 코멘트",
          "metrics": [
            {
              "product": "삼성 Neo QLED 8K",
              "sales": 2850,
              "change": "increase",
              "description": "AI 화질 개선과 게이밍 기능으로 25% 증가",
              "comment": "프리미엄 시장 선도"
            }
          ]
        }
      ]
    }
  ]
}
```

### 내부 데이터 구조
```python
metrics_info = [
    {
        "path": ["전자제품", "가전제품", "TV"],
        "comments": ["시장 전반 코멘트", "중간 계층 코멘트", "세부 카테고리 코멘트"],
        "product": "삼성 Neo QLED 8K",
        "sales": 2850,
        "change": "increase",
        "description": "AI 화질 개선과 게이밍 기능으로 25% 증가",
        "product_comment": "프리미엄 시장 선도"
    }
]
```

## 🎯 사용 방법

### 1. 기본 실행
```bash
streamlit run sales_analyzer.py
```

### 2. 브라우저에서 접속
```
http://localhost:8501
```

### 3. 사용 단계

#### Step 1: JSON 데이터 입력
- 기본 샘플 데이터가 제공됨
- 또는 사용자 정의 JSON 데이터 입력

#### Step 2: 분석 실행
- "분석 실행" 버튼 클릭
- AI 분석 진행 (약 10-30초 소요)

#### Step 3: 결과 확인
- **추출된 메트릭**: 각 제품별 상세 정보
- **개별 상품별 요약**: 제품별 AI 요약
- **전체 트렌드 요약**: 계층적 주석이 포함된 종합 분석
- **분석 카테고리**: 키워드 목록
- **카테고리 참조**: 주석 설명

## 📝 사용 예시

### 예시 1: 기본 분석
```python
# 기본 샘플 데이터로 분석 실행
# 결과: 전자제품 시장 전반 트렌드 분석
```

### 예시 2: 커스텀 데이터
```json
{
  "category": "식품",
  "comment": "건강식품 트렌드 확산",
  "subcategories": [
    {
      "category": "음료",
      "comment": "무설탕 제품 선호",
      "metrics": [
        {
          "product": "제로콜라",
          "sales": 1500,
          "change": "increase",
          "description": "건강 트렌드로 20% 증가",
          "comment": "젊은층 선호"
        }
      ]
    }
  ]
}
```

### 예시 출력
```
전체 트렌드 요약:
식품[1] 시장에서는 건강식품 트렌드가 확산되고 있으며, 
음료[2] 부문에서는 무설탕 제품에 대한 선호가 두드러집니다.

📝 카테고리 참조:
[1] 식품: 건강식품 트렌드 확산
[2] 식품 > 음료: 건강식품 트렌드 확산 / 무설탕 제품 선호
```

## 🔍 고급 기능

### 1. 계층적 주석 시스템
- 언급되는 계층 수준에 따라 적절한 주석 제공
- 최상위 → 중간 → 세부 순서로 주석 번호 할당

### 2. AI 모델 Fallback
- Claude 4.0 실패 시 자동으로 Claude 3.7로 전환
- 안정적인 서비스 제공

### 3. 반응형 UI
- 2컬럼 레이아웃: 메인 분석 + 키워드 섹션
- 확장 가능한 제품 상세 정보

## 🚨 문제 해결

### 일반적인 오류

#### 1. AWS 인증 오류
```
Error: Unable to locate credentials
```
**해결책**: AWS 자격 증명 재설정
```bash
aws configure
```

#### 2. Bedrock 모델 액세스 오류
```
Error: Access denied to model
```
**해결책**: AWS 콘솔에서 Bedrock 모델 액세스 요청

#### 3. JSON 형식 오류
```
Error: 올바른 JSON 형식이 아닙니다
```
**해결책**: JSON 유효성 검사 도구 사용

### 성능 최적화

#### 1. 토큰 수 조정
```python
"max_tokens": 8192  # 더 긴 응답을 위해 증가
```

#### 2. 배치 처리
- 대량 데이터의 경우 청크 단위로 분할 처리

## 📈 확장 가능성

### 1. 추가 AI 모델 지원
- GPT, Gemini 등 다른 모델 통합 가능

### 2. 데이터 소스 확장
- CSV, Excel, 데이터베이스 연동

### 3. 시각화 기능
- 차트, 그래프 추가

### 4. 내보내기 기능
- PDF, Word 보고서 생성

## 📄 라이선스

MIT License

## 🤝 기여

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📞 지원

문의사항이나 버그 리포트는 이슈 탭에서 등록해 주세요.
