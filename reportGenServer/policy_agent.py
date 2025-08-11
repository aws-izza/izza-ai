from strands import Agent, tool
from strands_tools import retrieve
from config import get_configured_model, get_agent_prompt, knowledge_base_config
import os, sys
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from bs4 import BeautifulSoup
import requests

load_dotenv()

@tool
def search_bizinfo_projects(
    result_count: int = 10,
    category_id: Optional[str] = None,
    tags: Optional[str] = None,
        ) -> str:
    """
    Finds South Korean government business support projects from the Bizinfo API.

    Args:
        result_count (int): The maximum number of projects to return. Defaults to 10.
        category_id (Optional[str]): The category code to filter projects.
            Valid Codes:
            - '01': 금융 (Finance)
            - '02': 기술 (Technology)
            - '03': 인력 (Human Resources)
            - '04': 수출 (Export)
            - '05': 내수 (Domestic Market)
            - '06': 창업 (Start-up)
            - '07': 경영 (Management)
            - '09': 기타 (Etc.)
        tags (Optional[str]): A comma-separated string of hashtags for filtering by region (e.g., '서울', '부산')
                            or field (e.g., '창업'). Example: '서울,창업,기술'
                            Available field hashtags include 금융, 기술, 인력, 수출, 내수, 창업, 경영, and 기타. 
                            Available region hashtags include 서울, 부산, 대구, 인천, 광주, 대전, 울산, 세종, 경기, 강원, 충북, 충남, 전북, 전남, 경북, 경남, and 제주.
                            IMPORTANT: Must use only the available tags listed above.

    Returns:
        str: A JSON string containing a list of project objects. Returns an empty
            JSON array string '[]' if no projects are found or an error occurs.
    """
    try:
        # NOTE: The public API key for bizinfo.go.kr is often rate-limited or
        # may require registration. This is a placeholder key.
        api_key = os.getenv("BIZINFO_API_KEY", "")
        if api_key == "":
            print("Warning: BIZINFO_API_KEY is not set.")
            sys.exit("Aborting due to API KEY being not available.")



        base_url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
        params = {
            'crtfcKey': api_key,
            'dataType': 'json',
            'searchCnt': str(result_count),
        }
        if category_id:
            params['searchLclasId'] = category_id
        if tags:
            params['hashtags'] = tags

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        print(f"--- [Tool] Calling Bizinfo API with params: {params} ---")
        response = requests.get(base_url, headers=headers, params=params, timeout=15)
        print(response)
        response.raise_for_status()
        raw_data = response.json()
        items = raw_data.get("jsonArray", [])

        summarized_projects = []
        for item in items:
            summary_html = item.get("bsnsSumryCn", "")
            soup = BeautifulSoup(summary_html, "html.parser")
            clean_summary = soup.get_text(separator=' ', strip=True)

            project = {
                "projectName": item.get("pblancNm"),
                "organization": item.get("jrsdInsttNm"),
                "summary": clean_summary,
                "applicationPeriod": item.get("reqstBeginEndDe"),
                "detailsUrl": f"https://www.bizinfo.go.kr{item.get('pblancUrl', '')}"
            }
            summarized_projects.append(project)

        # The tool should return a string, so we serialize the list to a JSON string.
        return json.dumps(summarized_projects, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return "[]" # Return empty JSON array on error
    except Exception as e:
        print(f"An error occurred in the tool: {e}")
        return "[]" # Return empty JSON array on error

@tool
def policy_agent(query: str) -> List[Dict[str, Any]]:
    """
    Agent Description: Bizinfo Project Finder

    Purpose: An autonomous agent that finds South Korean government business support projects by querying the search_bizinfo_projects tool. This agent is designed to be called by an orchestrator within a multi-agent system.

    Functionality:
        - Input: Accepts a natural language query (query: str) in Korean or English.
        - Processing:
            - Analyzes the query to extract key parameters:
                - Business Category: (e.g., 'finance(금융)', 'start-up(창업)', 'technology(기술)').
                - Tags: (e.g., 'Seoul(서울)', 'Busan(부산)', 'export(수출)').
                - Result Count: The number of projects to return.
            - Operates autonomously and will perform a broad search if the query is vague, without asking for clarification.
        - Output: Returns a raw JSON string (str) representing a list of project objects. This data is intended for further processing by another agent (e.g., for rendering into a report). Returns an empty JSON array string '[]' if no projects are found.
    """
    try:
        model = get_configured_model("apac.anthropic.claude-3-sonnet-20240229-v1:0")
        agent_prompt = get_agent_prompt('past_prompt')
        agent = Agent(
            model=model,
            system_prompt=agent_prompt,
            tools=[search_bizinfo_projects]
        )

        query_prompt = f"""
        언제나 시스템 프롬프트를 지켜서 툴을 사용하고 답변하세요.
        {query}
        """
        
        response = agent(f"{query_prompt}")
        return str(response)
        
    except Exception as e:
        return f"정책 에이전트 오류: {str(e)}"

if __name__ == "__main__":
    print("Policy........")

    test_queries = [
        "서울의 금융 지원 정책을 찾아봐",
        "대구광역시 중구 동인동1가 2-1에 연관된 창업 지원 정책이 뭐가 있지?",
        "대전의 지원 정책을 찾아봐.",
        "서울의 금융 지원 정책을 찾아봐"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 테스트 {i}: {query}")
        try:
            result = policy_agent(query)
            print(result)
            # print(result[:200] + "..." if len(result) > 200 else result)
        except Exception as e:
            print(f"❌ 오류: {str(e)}")