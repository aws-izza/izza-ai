import os
import requests
from bs4 import BeautifulSoup
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import use_agent, retrieve
from strands_tools.memory import memory
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()
knowledge_id = os.getenv("STRANDS_KNOWLEDGE_BASE_ID")
modelid = os.getenv("MODEL_ID")

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
    def __init__(self, llm_provider, knowledge_base_id: str, region: str = "ap-northeast-2"):
        self.agent = Agent(
            model=llm_provider
        )
        self.knowledge_base_id = knowledge_base_id
        self.region = region

    def generate(self, json_data: dict) -> str:

        # Extract key details from the JSON data to build a better query
        # land_category = json_data.get("land_category_name")
        # use_district = json_data.get("use_district_name1")
        # road_side = json_data.get("road_side_name")

        # Create a specific, context-rich query for the knowledge base
        query = f"""
        주어진 토지 정보를 바탕으로 상세하게 개발 가능성과 활용도에 관해 10줄 정도로 분석해줘.
        """

        # kb_results = self.agent.tool.retrieve(
        #     text=query,
        #     numberOfResults=20,
        #     score=0.0,
        #     knowledgeBaseId=self.knowledge_base_id,
        #     region=self.region
        # )

        # Build knowledge context from retrieved results
        # knowledge_context = "\n\n".join([
        #     f"Title: {item.get('title')}\nContent: {item.get('content')}"
        #     for item in kb_results.get("results", [])
        # ]) or "No relevant knowledge found."

        # Compose the full prompt
        full_prompt = f"""
        You are an expert real estate analysis assistant.

        Your role is to analyze land parcel information based on the user's query, structured data,
        and knowledge base context given.

        **Instructions:**
        1. Interpret the user's query.
        2. Use the JSON data to populate the HTML template fields.
        3. Write a summary of development potential using both the structured data and knowledge base content.
        4. Do NOT invent data — rely only on the JSON and retrieved content.
        5. Return only the fully rendered HTML using the template provided.

        ---------------------
        User Query:
        {query}

        Knowledge Base Context:
        '''
            # Land Analysis Glossary

            ## 지목 (Land Category)

            지목은 토지의 주된 용도에 따라 구분된 법률상의 명칭입니다. 총28종류:

            1. **전 (Jeon)**: 물을 상시적으로 이용하지 않고 작물을 재배하는 토지  
            2. **답 (Dap)**: 물을 상시적으로 이용하여 벼, 연, 미나리 등을 재배하는 토지  
            3. **과수원 (Gwasuwon)**: 과수류를 집단 재배하는 토지와 그 부속시설  
            4. **목장용지 (Mokjangyongji)**: 축산업·낙농업을 위한 초지 및 부속시설 부지  
            5. **임야 (Imya)**: 수림지, 암석지, 황무지 등 산림·원야를 이루는 토지  
            6. **광천지 (Gwangcheonji)**: 온수, 약수, 석유류 등이 용출되는 부지  
            7. **염전 (Yeomjeon)**: 바닷물을 끌어들여 소금을 채취하는 토지  
            8. **대 (Dae)**: 주거, 사무실, 점포 등 건축물 및 택지 조성된 토지  
            9. **공장용지 (Gongjangyongji)**: 제조업 공장 및 부속시설 부지  
            10. **학교용지 (Hakgyoyongji)**: 학교 교사 및 체육장 등 부속시설 부지  
            11. **주차장 (Juchajang)**: 자동차 주차를 위한 독립적 시설 부지  
            12. **주유소용지 (Juyusoyongji)**: 석유 판매 설비를 갖춘 시설 부지  
            13. **창고용지 (Changgoyongji)**: 물건 저장을 위한 독립적 시설 부지  
            14. **도로 (Doro)**: 보행 및 차량운행용 토지  
            15. **철도용지 (Cheoldoyongji)**: 교통 운수용 궤도 및 부속시설 부지  
            16. **제방 (Jebang)**: 방조제, 방수제 등의 부지  
            17. **하천 (Hacheon)**: 자연 유수가 있거나 예상되는 토지  
            18. **구거 (Gugeo)**: 인공수로 및 부속시설 부지  
            19. **유지 (Yuji)**: 물을 저장하는 댐, 저수지, 호수, 연못 등  
            20. **양어장 (Yangeojang)**: 수산 양식 시설 부지  
            21. **수도용지 (Sudoyongji)**: 정수, 취수, 배수 시설 부지  
            22. **공원 (Gongwon)**: 공중의 보건, 휴양, 정서를 위한 시설 부지  
            23. **체육용지 (Cheyugyongji)**: 체육시설 있는 운동장, 골프장 등  
            24. **유원지 (Yuwonji)**: 위락·휴양 시설 있는 수영장, 동물원 등  
            25. **종교용지 (Jonggyoyongji)**: 교회, 사찰 등 종교 건축물 부지  
            26. **사적지 (Sajeokji)**: 역사 유적, 기념물 보존을 위한 구획  
            27. **묘지 (Myoji)**: 시체나 유골 매장 토지  
            28. **잡종지 (Japjongji)**: 기타 범주에 속하지 않는 토지 (갈대밭, 야외시장 등)

            ## 용도지역 (Use District)

            토지이용규제 체계의 가장 기본 단위. 건축물 종류, 건폐율, 용적률 결정 기준.

            - **도시지역 (Urban Area)**  
            - 주거지역  
            - 상업지역  
            - 공업지역  
            - 녹지지역

            - **관리지역 (Management Area)**  
            - 계획관리지역  
            - 생산관리지역  
            - 보전관리지역

            - **농림지역 (Agriculture & Forestry Area)**

            - **자연환경보전지역 (Natural Environment Preservation Area)**

            ## 용도지구 (Use Area)

            용도지역 규제를 강화 또는 완화하는 추가 규제 레이어:

            - **경관지구**: 미관 보호 및 관리  
            - **고도지구**: 건축물 높이 제한  
            - **방화지구**: 화재 예방  
            - **방재지구**: 재해 예방  
            - **보호지구**: 국가유산, 생태계 등 보호  
            - **취락지구**: 마을 정비 및 건축 규제 완화  
            - **개발진흥지구**: 집중 개발을 위한 규제 완화  
            - **특정용도제한지구**: 특정 시설 입지 제한  
            - **복합용도지구**: 특정 시설 입지 완화

            ## 도로접면 (Road Frontage)

            도로와의 접촉 형태에 따른 접근성 등급:

            - **광대한면/광대소각**: 25m 이상 도로 접함  
            - **중로한면/중로각지**: 12m 이상 25m 미만  
            - **소로한면/소로각지**: 8m 이상 12m 미만  
            - **세로(가)/세각(가)**: 8m 미만, 차량 통행 가능  
            - **세로(불)/세각(불)**: 차량 통행 불가능  
            - **맹지 (Landlocked)**: 도로와 전혀 접하지 않음

            ## 지형고저 (Topography)

            지형의 고저 및 경사에 따른 분류:

            - **평지 (Flat Land)**: 경사 거의 없음, 개발 용이  
            - **완경사 (Gentle Slope)**: 경사도 15° 이하  
            - **급경사 (Steep Slope)**: 경사도 15° 초과  
            - **고지 (High Ground)**: 주위보다 높음  
            - **저지 (Low Ground)**: 주위보다 낮음

            ## 토지이용상황 (Land Use Situation)

            현재 실제 이용 상태 (지목과 무관):
            - **주거용**
            - 건부지: 건물 있음  
            - 나지: 건물 없음  
            - 기타

            - **상업·업무용**
            - 건부지  
            - 나지  
            - 기타

            - **주상복합용**
            - 건부지  
            - 나지  
            - 기타

            - **공업용**
            - 건부지  
            - 나지  
            - 기타

            - **전, 답, 과수원**: 농경지로 사용 중  
            - **임야**
            - 순수임야  
            - 토지임야

            - **특수토지**: 희소하거나 특수한 대규모 용도
        '''

        Structured Parcel Data:
        {json.dumps(json_data, ensure_ascii=False, indent=2)}

        Template:
        ```html
        {HTML_TEMPLATE}
        ```
        """
        # print(knowledge_context)
        # Get response from LLM agent
        html_report = self.agent(full_prompt)
        print("--- Report Generation Complete! ---")
        return html_report


# --- Main Execution ---
if __name__ == "__main__":
    try:
        llm = BedrockModel(
            model_id=modelid,
            region_name="ap-northeast-2",
            temperature=0.3
        )
    except Exception as e:
        print(f"Error initializing BedrockModel: {e}")
        exit()

    generator = ReportGenerator(
        llm_provider=llm,
        knowledge_base_id=knowledge_id,
        region="ap-northeast-2"
    )

    user_query = "메모리를 바탕으로 이 토지에 대한 분석을 진행해"
    json_data = {
        "full_code": "2711010100",
        "address": "대구광역시 중구 동인동1가 190-4",
        "ledger_division_code": 1,
        "ledger_division_name": "일반",
        "land_category_code": 8,
        "land_category_name": "대",
        "land_area": 8800.00,
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

    report_html = generator.generate(json_data)

    with open("land_report.html", "w", encoding="utf-8") as f:
        f.write(str(report_html))

    print("\nSuccessfully generated report. Please open 'land_report.html' in your browser.")

