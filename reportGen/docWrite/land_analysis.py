

import os
import requests
from bs4 import BeautifulSoup
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import use_llm
from strands_tools.memory import memory
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()
STRANDS_KNOWLEDGE_BASE_ID = os.getenv("STRANDS_KNOWLEDGE_BASE_ID")

# -- Knowledge Base access --

ACTION_SYSTEM_PROMPT = """
You are an intent classification agent. Determine whether the user wants to store information or retrieve it from the knowledge base.
Respond with only one word: "store" or "retrieve".
"""

ANSWER_SYSTEM_PROMPT = """
You are an assistant answering a user based on previously stored knowledge. Answer clearly and only based on the given information.
"""

def determine_action(agent, query: str) -> str:
    result = agent.tool.use_llm(
        prompt=f"Query: {query}",
        system_prompt=ACTION_SYSTEM_PROMPT
    )
    action_text = str(result).lower().strip()
    return "store" if "store" in action_text else "retrieve"




# --- Jinja2 Template ---
# This HTML template will be used to render the final report.

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Land Analysis Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 20px auto;
            padding: 0 20px;
            background-color: #f9f9f9;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .section {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-left: 5px solid #3498db;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .section h2 {
            margin-top: 0;
            color: #3498db;
        }
        .section p {
            margin: 5px 0;
        }
        .section strong {
            color: #555;
        }
        .query {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-style: italic;
            color: #555;
        }
    </style>
</head>
<body>
    <h1>토지 상세 분석 결과</h1>
    <p class="query"><strong>Query:</strong> {{ user_query }}</p>

    <div class="section">
        <h2>1. 기본 정보</h2>
        <p><strong>주소:</strong> {{ address }}</p>
        <p><strong>토지 면적:</strong> {{ land_area }}㎡</p>
        <p><strong>공시지가:</strong> {{ official_land_price | int | stringformat:",d" }}원/㎡</p>
    </div>

    <div class="section">
        <h2>2. 토지 용도 및 분류</h2>
        <p><strong>토지 지목:</strong> {{ land_category_name }}</p>
        <p><strong>용도지역:</strong> {{ use_district_name1 }}</p>
        <p><strong>토지이용상황:</strong> {{ land_use_name }}</p>
        <p><strong>대장구분:</strong> {{ ledger_division_name }}</p>
    </div>

    <div class="section">
        <h2>3. 물리적 특성</h2>
        <p><strong>지형 높이:</strong> {{ terrain_height_name }}</p>
        <p><strong>토지 형상:</strong> {{ terrain_shape_name }}</p>
        <p><strong>도로 접면:</strong> {{ road_side_name }}</p>
    </div>

    <div class="section">
        <h2>4. 개발 가능성 및 활용도</h2>
        <p>{{ analysis_summary }}</p>
    </div>
</body>
</html>
"""

# --- Report Generation Logic ---

class ReportGenerator:
    def __init__(self, llm_provider):
        # The agent is initialized with just the model and tools.
        # The prompt logic is now handled in the 'generate' method.
        self.agent = Agent(
            model=llm_provider,
            tools=[use_llm, memory]
        )

    def generate(self, query: str, json_data: json) -> str:
        print(f"--- Starting report generation for query: '{query}' ---")

        # The full prompt is constructed here, before calling the agent.
        # This prompt tells the agent its role, what tools to use,
        # what the user wants, and the template for the final output.
        full_prompt = f"""
        You are an expert real estate analysis assistant.

        Your role is to analyze land parcel information based on the user's query and the structured data provided.
        You must reason through the fields (such as land use, terrain, zoning, road access, and pricing), generate insights,
        and fill out the following Jinja2 template with meaningful, natural-language content.

        **Instructions:**
        1. Carefully interpret the user's query to understand their intent.
        2. Use the provided data fields to write a coherent land analysis summary in Korean for the '개발 가능성 및 활용도' section.
        3. Do NOT hallucinate values — only use what is given in the input data.
        4. Replace the Jinja2 variables with actual values derived from the data.
        5. Your final output MUST be only the fully rendered HTML report. Do not include any explanations, markdown, or extra commentary.

        Here is the Jinja2 template to render (do NOT modify structure):
        ```html
        {HTML_TEMPLATE}
        ```
        User Query:
        {query}

        Structured Parcel Data:
        {json_data}
        """

        # The agent is called with the full, detailed prompt.
        html_report = self.agent(full_prompt)
        print("--- Report Generation Complete! ---")
        return html_report

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Configure the LLM provider (e.g., Amazon Bedrock)
    # IMPORTANT: Ensure your AWS credentials are configured in your environment.
    try:
        llm = BedrockModel(
            model_id="apac.anthropic.claude-3-sonnet-20240229-v1:0",
            region_name="ap-northeast-2",
            temperature=0.3
        )
    except Exception as e:
        print(f"Error initializing BedrockModel: {e}")
        print("Please ensure your AWS credentials and permissions are correctly configured.")
        exit()

    # 2. Initialize the generator and define the user query
    generator = ReportGenerator(llm_provider=llm)
    user_query = "메모리를 바탕으로 이 토지에 대한 분석을 진행해"
    json_data = {
        "full_code": "2711010100",
        "address": "대구광역시 중구 동인동1가 190-4",
        "ledger_division_code": 1,
        "ledger_division_name": "일반",
        "land_category_code": 8,
        "land_category_name": "대",
        "land_area": 88.00,
        "use_district_code1": 21,
        "use_district_name1": "중심상업지역",
        "use_district_code2": 0,
        "use_district_name2": "지정되지않음",
        "land_use_code": 210,
        "land_use_name": "상업용",
        "terrain_height_code": 2,
        "terrain_height_name": "평지",
        "terrain_shape_code": 4,
        "terrain_shape_name": "사다리형",
        "road_side_code": 1,
        "road_side_name": "광대로한면",
        "official_land_price": 1689000
    }

    # Determine if the input is meant to store or retrieve
    action = determine_action(generator.agent, user_query)

    if action == "store":
        generator.agent.tool.memory(action="store", content=f"{user_query}\n{json.dumps(json_data, ensure_ascii=False)}")
        print("Information stored in knowledge base.")
    else:
        kb_results = generator.agent.tool.memory(
            action="retrieve",
            query=user_query,
            min_score=0.4,
            max_results=9,
            STRANDS_KNOWLEDGE_BASE_ID=STRANDS_KNOWLEDGE_BASE_ID
        )
        print(f"Retrieved from KB: {kb_results}")
        # You may choose to add this into your final prompt if needed


    # 3. Generate the report
    report_html = generator.generate(user_query, json_data)

    # 4. Save the report to a file
    report_filename = "land_report.html"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(str(report_html))

    print(f"\nSuccessfully generated report. Please open '{report_filename}' in your browser.")
