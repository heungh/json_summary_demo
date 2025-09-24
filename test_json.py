import boto3
import json
import logging

logger = logging.getLogger(__name__)

class BedrockClaude:
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.sonnet_4_model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        self.sonnet_3_7_model_id = "us.anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    def invoke_claude(self, prompt):
        claude_input = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        })
        
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

# 계층(카테고리) 경로·코멘트·매트릭스 추출 함수
def extract_metrics_with_path_and_comment(data, path=None, comments=None):
    if path is None:
        path = []
    if comments is None:
        comments = []
    metrics_list = []
    current_path = path + [data.get("category")] if "category" in data else path
    current_comments = comments + [data.get("comment")] if "comment" in data else comments

    if "metrics" in data:
        for item in data["metrics"]:
            metrics_list.append({
                "path": current_path,
                "comments": current_comments,
                "product": item["product"],
                "change": item["change"],
                "description": item["description"],
                "sales": item["sales"],
                "product_comment": item.get("comment", "")
            })
    if "subcategories" in data:
        for subcat in data["subcategories"]:
            metrics_list.extend(
                extract_metrics_with_path_and_comment(subcat, current_path, current_comments)
            )
    return metrics_list

json_data = {
    "category": "생활",
    "comment": "전체적으로 시장이 안정적이며 소비 트렌드는 친환경 제품 쪽으로 이동 중.",
    "subcategories": [
        {
            "category": "가전제품",
            "comment": "가전제품은 올해 전체적으로 성장세를 보이고 있으며 특히 신제품이 활발히 출시되고 있음.",
            "subcategories": [
                {
                    "category": "TV",
                    "comment": "TV 시장은 프리미엄 모델의 증가와 화질 개선 제품에 주목받고 있음.",
                    "metrics": [
                        {
                            "product": "A",
                            "sales": 1150,
                            "change": "increase",
                            "description": "신제품 QLED 출시로 매출이 15% 증가.",
                            "comment": "A모델은 중상급 시장에서 강세."
                        },
                        {
                            "product": "B",
                            "sales": 840,
                            "change": "decrease",
                            "description": "경쟁 심화로 8% 감소.",
                            "comment": "B모델은 중저가 시장에서 경쟁이 심함."
                        }
                    ]
                }
            ]
        }
    ]
}

metrics_info = extract_metrics_with_path_and_comment(json_data)

def make_summary_inputs_with_comment(metrics_info):
    return [
        f"카테고리 경로: {' > '.join(item['path'])}, 경로 코멘트: {' / '.join([c for c in item['comments'] if c])}, " \
        f"상품: {item['product']}, 변화: {item['change']}, 설명: {item['description']}, 매출: {item['sales']}, " \
        f"상품 코멘트: {item['product_comment']}"
        for item in metrics_info
    ]

summary_inputs = make_summary_inputs_with_comment(metrics_info)

# Bedrock Claude 초기화
claude = BedrockClaude()

# 개별 요약 생성
individual_summaries = []
for text in summary_inputs:
    prompt = f"다음 상품 매출 데이터를 한 문장으로 요약하세요. 반드시 카테고리 경로(depth 전체)와 각 경로 및 상품별 코멘트가 반영되어야 합니다:\n{text}"
    summary = claude.invoke_claude(prompt)
    individual_summaries.append(summary)

# 전체 요약 생성
docs_text = "\n".join(individual_summaries)
final_prompt = f"아래는 각 상품 및 카테고리 경로별 요약입니다:\n{docs_text}\n모든 카테고리 경로(depth, 코멘트 기준)별 핵심 트렌드와 특징을 두세 문장으로 요약하세요."
final_summary = claude.invoke_claude(final_prompt)

print("개별 카테고리/상품별 요약:", individual_summaries)
print("전체 트렌드 요약:", final_summary)
