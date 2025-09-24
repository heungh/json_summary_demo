import streamlit as st
import json
import boto3
import logging

logger = logging.getLogger(__name__)


class BedrockClaude:
    def __init__(self):
        self.bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
        self.sonnet_4_model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
        self.sonnet_3_7_model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

    def invoke_claude(self, prompt):
        claude_input = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 6000,
                "messages": [{"role": "user", "content": prompt}],
            }
        )

        # Claude Sonnet 4 inference profile 호출
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.sonnet_4_model_id, body=claude_input
            )
            response_body = json.loads(response.get("body").read())
            return response_body.get("content", [{}])[0].get("text", "")
        except Exception as e:
            logger.warning(
                f"Claude Sonnet 4 호출 실패 → Claude 3.7 Sonnet cross-region profile로 fallback: {e}"
            )
            # Claude 3.7 Sonnet inference profile 호출 (fallback)
            try:
                response = self.bedrock_client.invoke_model(
                    modelId=self.sonnet_3_7_model_id, body=claude_input
                )
                response_body = json.loads(response.get("body").read())
                return response_body.get("content", [{}])[0].get("text", "")
            except Exception as e:
                logger.error(f"Claude 3.7 Sonnet 호출 오류: {e}")
                return f"Claude 호출 중 오류 발생: {str(e)}"


def extract_categories_and_keywords(data, categories=None):
    if categories is None:
        categories = set()

    if "category" in data:
        categories.add(data["category"])

    if "subcategories" in data:
        for subcat in data["subcategories"]:
            extract_categories_and_keywords(subcat, categories)

    return categories


def create_footnote_references(summary_text, metrics_info):
    """요약 텍스트에 각 계층별 카테고리에 맞는 주석 번호를 추가"""
    # 모든 계층별 카테고리 경로 수집
    all_category_paths = set()
    for metric in metrics_info:
        path = metric["path"]
        # 각 계층별로 경로 생성 (전체 > 중간 > 세부)
        for i in range(1, len(path) + 1):
            category_path = " > ".join(path[:i])
            all_category_paths.add(category_path)

    # 주석 번호 할당
    footnotes = {}
    footnote_counter = 1
    for category_path in sorted(all_category_paths):
        footnotes[category_path] = footnote_counter
        footnote_counter += 1

    # 카테고리명과 해당 계층의 주석 번호 매핑
    category_to_footnote = {}
    for category_path, footnote_num in footnotes.items():
        categories = category_path.split(" > ")
        leaf_category = categories[-1]  # 해당 계층의 마지막 카테고리
        # 더 구체적인 경로가 있으면 덮어쓰지 않음
        if leaf_category not in category_to_footnote:
            category_to_footnote[leaf_category] = footnote_num
        # 하지만 정확한 계층 매칭을 위해 전체 경로도 저장
        category_to_footnote[category_path] = footnote_num

    # 텍스트에 주석 번호 추가 (긴 경로부터 우선 처리)
    annotated_text = summary_text
    sorted_paths = sorted(footnotes.keys(), key=len, reverse=True)

    for category_path in sorted_paths:
        footnote_num = footnotes[category_path]
        leaf_category = category_path.split(" > ")[-1]

        if (
            leaf_category in annotated_text
            and f"{leaf_category}[" not in annotated_text
        ):
            annotated_text = annotated_text.replace(
                leaf_category, f"{leaf_category}[{footnote_num}]", 1
            )

    return annotated_text, footnotes


def extract_metrics_with_path_and_comment(data, path=None, comments=None):
    if path is None:
        path = []
    if comments is None:
        comments = []
    metrics_list = []
    current_path = path + [data.get("category")] if "category" in data else path
    current_comments = (
        comments + [data.get("comment")] if "comment" in data else comments
    )

    if "metrics" in data:
        for item in data["metrics"]:
            metrics_list.append(
                {
                    "path": current_path,
                    "comments": current_comments,
                    "product": item["product"],
                    "change": item["change"],
                    "description": item["description"],
                    "sales": item["sales"],
                    "product_comment": item.get("comment", ""),
                }
            )
    if "subcategories" in data:
        for subcat in data["subcategories"]:
            metrics_list.extend(
                extract_metrics_with_path_and_comment(
                    subcat, current_path, current_comments
                )
            )
    return metrics_list


def make_summary_inputs_with_comment(metrics_info):
    return [
        f"카테고리 경로: {' > '.join(item['path'])}, 경로 코멘트: {' / '.join([c for c in item['comments'] if c])}, "
        f"상품: {item['product']}, 변화: {item['change']}, 설명: {item['description']}, 매출: {item['sales']}, "
        f"상품 코멘트: {item['product_comment']}"
        for item in metrics_info
    ]


st.title("매출 데이터 분석기 (Bedrock Claude)")

# 샘플 데이터
default_data = {
    "category": "전자제품",
    "comment": "전자제품 시장은 AI 기술 통합과 친환경 트렌드가 주도하며, 프리미엄 제품군의 성장이 두드러짐.",
    "subcategories": [
        {
            "category": "가전제품",
            "comment": "스마트 가전과 에너지 효율성이 핵심 경쟁 요소로 부상하며 전체적으로 성장세.",
            "subcategories": [
                {
                    "category": "TV",
                    "comment": "8K, OLED 기술과 스마트 기능 강화로 프리미엄 시장 확대.",
                    "metrics": [
                        {
                            "product": "삼성 Neo QLED 8K",
                            "sales": 2850,
                            "change": "increase",
                            "description": "AI 화질 개선과 게이밍 기능으로 25% 증가",
                            "comment": "프리미엄 시장 선도",
                        },
                        {
                            "product": "LG OLED C3",
                            "sales": 2340,
                            "change": "increase",
                            "description": "영화관급 화질로 18% 증가",
                            "comment": "중고급 시장 강세",
                        },
                        {
                            "product": "소니 브라비아 X90L",
                            "sales": 1680,
                            "change": "decrease",
                            "description": "가격 경쟁력 부족으로 12% 감소",
                            "comment": "고급 시장에서 고전",
                        },
                    ],
                },
                {
                    "category": "냉장고",
                    "comment": "대용량, 스마트 기능, 에너지 효율성이 주요 구매 요인.",
                    "metrics": [
                        {
                            "product": "삼성 비스포크 4도어",
                            "sales": 3200,
                            "change": "increase",
                            "description": "맞춤형 디자인으로 30% 증가",
                            "comment": "프리미엄 맞춤형 시장 독점",
                        },
                        {
                            "product": "LG 디오스 오브제컬렉션",
                            "sales": 2890,
                            "change": "increase",
                            "description": "인테리어 융합으로 22% 증가",
                            "comment": "디자인 중심 고객층 확보",
                        },
                        {
                            "product": "위니아 딤채",
                            "sales": 1450,
                            "change": "stable",
                            "description": "김치냉장고 전문성으로 안정적",
                            "comment": "틈새시장 전문화",
                        },
                    ],
                },
            ],
        },
        {
            "category": "모바일기기",
            "comment": "5G 확산과 카메라 성능 향상이 주요 트렌드이며, 폴더블 시장 성장.",
            "subcategories": [
                {
                    "category": "스마트폰",
                    "comment": "AI 기능과 카메라 성능이 차별화 포인트로 부상.",
                    "metrics": [
                        {
                            "product": "아이폰 15 Pro",
                            "sales": 4500,
                            "change": "increase",
                            "description": "티타늄 소재와 액션버튼으로 35% 증가",
                            "comment": "프리미엄 시장 압도적 1위",
                        },
                        {
                            "product": "갤럭시 S24 Ultra",
                            "sales": 3800,
                            "change": "increase",
                            "description": "AI 기능 강화로 28% 증가",
                            "comment": "안드로이드 플래그십 선도",
                        },
                        {
                            "product": "갤럭시 Z 플립5",
                            "sales": 2100,
                            "change": "increase",
                            "description": "폴더블 대중화로 45% 증가",
                            "comment": "새로운 폼팩터 시장 개척",
                        },
                        {
                            "product": "픽셀 8 Pro",
                            "sales": 890,
                            "change": "decrease",
                            "description": "마케팅 부족으로 15% 감소",
                            "comment": "기술력 대비 인지도 부족",
                        },
                    ],
                },
                {
                    "category": "태블릿",
                    "comment": "원격근무와 디지털 교육 확산으로 수요 증가.",
                    "metrics": [
                        {
                            "product": "아이패드 프로 M2",
                            "sales": 2650,
                            "change": "increase",
                            "description": "전문가용 기능으로 20% 증가",
                            "comment": "크리에이터 시장 독점",
                        },
                        {
                            "product": "갤럭시 탭 S9",
                            "sales": 1340,
                            "change": "stable",
                            "description": "안드로이드 생태계로 안정적",
                            "comment": "비즈니스 시장 확보",
                        },
                        {
                            "product": "서피스 프로 9",
                            "sales": 980,
                            "change": "decrease",
                            "description": "노트북 대체재 경쟁으로 8% 감소",
                            "comment": "하이브리드 시장에서 고전",
                        },
                    ],
                },
            ],
        },
        {
            "category": "컴퓨터",
            "comment": "AI 워크로드와 게이밍 성능이 주요 구매 동기로 부상.",
            "subcategories": [
                {
                    "category": "노트북",
                    "comment": "휴대성과 성능의 균형, AI 가속기 탑재가 트렌드.",
                    "metrics": [
                        {
                            "product": "맥북 프로 M3",
                            "sales": 3400,
                            "change": "increase",
                            "description": "AI 성능과 배터리로 32% 증가",
                            "comment": "크리에이터와 개발자 선호",
                        },
                        {
                            "product": "델 XPS 13",
                            "sales": 1890,
                            "change": "stable",
                            "description": "비즈니스 시장에서 안정적",
                            "comment": "기업 시장 강세",
                        },
                        {
                            "product": "레노버 씽크패드 X1",
                            "sales": 1650,
                            "change": "decrease",
                            "description": "재택근무 감소로 10% 하락",
                            "comment": "기업 수요 둔화",
                        },
                    ],
                }
            ],
        },
    ],
}

# JSON 데이터 입력
st.subheader("매출 데이터 입력")
json_input = st.text_area(
    "JSON 데이터",
    value=json.dumps(default_data, ensure_ascii=False, indent=2),
    height=300,
)

if st.button("분석 실행", key="analyze_button"):
    try:
        # JSON 파싱
        json_data = json.loads(json_input)

        # 메트릭 추출
        metrics_info = extract_metrics_with_path_and_comment(json_data)

        # 추출된 데이터 표시
        st.subheader("추출된 메트릭")
        for i, metric in enumerate(metrics_info):
            with st.expander(
                f"상품 {metric['product']} - {' > '.join(metric['path'])}"
            ):
                st.write(f"**경로:** {' > '.join(metric['path'])}")
                st.write(f"**매출:** {metric['sales']:,}")
                st.write(f"**변화:** {metric['change']}")
                st.write(f"**설명:** {metric['description']}")
                if metric["product_comment"]:
                    st.write(f"**상품 코멘트:** {metric['product_comment']}")

        # Bedrock Claude 분석
        with st.spinner("Claude AI 분석 중..."):
            summary_inputs = make_summary_inputs_with_comment(metrics_info)

            # Bedrock Claude 초기화
            claude = BedrockClaude()

            # 개별 요약 생성
            individual_summaries = []
            for text in summary_inputs:
                prompt = f"다음 상품 매출 데이터를 한 문장으로 요약하세요. 반드시 카테고리 경로(depth 전체)와 각 경로 및 상품별 코멘트가 반영되어야 합니다:\n{text}"
                summary = claude.invoke_claude(prompt)
                individual_summaries.append(summary)

            # 전체 요약 생성 (카테고리 정보 포함)
            docs_text = "\n".join(individual_summaries)
            categories = extract_categories_and_keywords(json_data)
            category_list = ", ".join(sorted(categories))

            final_prompt = f"""아래는 각 상품 및 카테고리 경로별 요약입니다:
{docs_text}

분석 대상 카테고리: {category_list}

모든 카테고리별 핵심 트렌드와 특징을 포함하여 전체 시장 동향을 3-4문장으로 요약하세요. 
각 카테고리명을 언급할 때는 구체적인 카테고리 이름을 사용하세요."""

            final_summary = claude.invoke_claude(final_prompt)

        # 결과 표시
        st.subheader("분석 결과")

        # 키워드 섹션 추가
        categories = extract_categories_and_keywords(json_data)
        col1, col2 = st.columns([2, 1])

        with col2:
            st.write("**📊 분석 카테고리**")
            for category in sorted(categories):
                st.write(f"• {category}")

        with col1:
            st.write("**개별 상품별 요약:**")
            for i, summary in enumerate(individual_summaries):
                st.write(f"{i+1}. {summary}")

            st.write("**전체 트렌드 요약:**")
            # 주석이 포함된 요약 생성
            annotated_summary, footnotes = create_footnote_references(
                final_summary, metrics_info
            )
            st.info(annotated_summary)

            # 주석 설명 추가
            if footnotes:
                st.write("**📝 카테고리 참조:**")
                for category_path, footnote_num in sorted(
                    footnotes.items(), key=lambda x: x[1]
                ):
                    # 해당 계층의 코멘트 찾기
                    path_parts = category_path.split(" > ")
                    category_comments = []

                    # 해당 계층까지의 모든 코멘트 수집
                    for metric in metrics_info:
                        if (
                            len(metric["path"]) >= len(path_parts)
                            and metric["path"][: len(path_parts)] == path_parts
                        ):
                            # 해당 계층까지의 코멘트만 추출
                            relevant_comments = metric["comments"][: len(path_parts)]
                            category_comments = [c for c in relevant_comments if c]
                            break

                    comment_text = (
                        " / ".join(category_comments)
                        if category_comments
                        else "상위 카테고리 정보"
                    )
                    st.write(f"[{footnote_num}] {category_path}: {comment_text}")

    except json.JSONDecodeError:
        st.error("올바른 JSON 형식이 아닙니다.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
