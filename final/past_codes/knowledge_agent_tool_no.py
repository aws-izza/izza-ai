from strands import Agent, tool
from strands_tools import retrieve
from config import get_configured_model, get_agent_prompt, knowledge_base_config
import os
from dotenv import load_dotenv

load_dotenv()

kb_id = os.getenv('KNOWLEDGE_BASE_ID')
region = os.getenv('AWS_REGION')

@tool
def knowledge_agent(query: str) -> str:
    """
    Domain-specific knowledge retrieval agent using Amazon Bedrock Knowledge Base
    
    Args:
        query: User's knowledge query or question
        
    Returns:
        Comprehensive answer from knowledge base sources
    """
    try:
        model = get_configured_model()
        agent = Agent(
            model=model
        )

        query_prompt = f"""
        다음 지식 검색 요청을 처리해주세요: {query}
        """
        
        response = agent(f"{query_prompt}")
        return str(response)
        
    except Exception as e:
        return f"지식 검색 에이전트 오류: {str(e)}"

if __name__ == "__main__":
    print("Knowledge Retrieving...")

    test_queries = [
        # "토지 법규 및 용도지역/지구에 용도지역이 뭔지 알려줘",
        # "공업용지 적합도 및 투자 분석을 어떻게 해야하지?",
        # "토지법규 및 용도지역/지구에 지목의 분류 중 창고용지가 뭔지 알려줘",
        "이 토지에 대해 공업용지 적합도 및 투자 분석 의견을 적어줘.  '주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', '용도지역': '중심상업지역', '용도지구': '지정되지않음', '토지이용상황': '업무용', '지형고저': '평지', '형상': '세로장방', '도로접면': '광대소각', '공시지가': 3735000"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 테스트 {i}: {query}")
        try:
            result = knowledge_agent(query)
            print(result)
            # print(result[:200] + "..." if len(result) > 200 else result)
        except Exception as e:
            print(f"❌ 오류: {str(e)}")