#
# A Python script to generate a report on government business support projects
# using a Strands Agent, a public API tool, and Jinja2 for templating.
#
# This script demonstrates a complete workflow:
# 1. A user provides a natural language query.
# 2. A Strands Agent interprets the query to call a tool with the right parameters.
# 3. The tool fetches data from the bizinfo.go.kr public API.
# 4. The agent receives the structured data and formats it into an HTML
#    report using a Jinja2 template.
#

# --- Prerequisites ---
# Ensure you have the necessary libraries installed:
# pip install strands-agents boto3 requests beautifulsoup4 jinja2

import os
import requests
from bs4 import BeautifulSoup
from strands import Agent, tool
from strands.models import BedrockModel
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Optional, List, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()


# --- Tool Definition ---
# An agent uses tools to interact with the outside world. Here, we define a tool
# to search for projects on the Bizinfo public portal.

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

    Returns:
        str: A JSON string containing a list of project objects. Returns an empty
            JSON array string '[]' if no projects are found or an error occurs.
    """
    try:
        # NOTE: The public API key for bizinfo.go.kr is often rate-limited or
        # may require registration. This is a placeholder key.
        api_key = os.getenv("BIZINFO_API_KEY")
        if api_key == "YOUR_API_KEY_HERE":
            print("Warning: BIZINFO_API_KEY is not set. Using a placeholder.")


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


# --- Jinja2 Template ---
# This HTML template will be used to render the final report.

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Support Project Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 20px auto; padding: 0 20px; background-color: #f9f9f9; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .project { background-color: #ffffff; border: 1px solid #e0e0e0; border-left: 5px solid #3498db; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .project h2 { margin-top: 0; color: #3498db; }
        .project p { margin: 5px 0; }
        .project strong { color: #555; }
        .project-footer { margin-top: 15px; font-size: 0.9em; }
        .project-footer a { color: #2980b9; text-decoration: none; font-weight: bold; }
        .project-footer a:hover { text-decoration: underline; }
        .query { background-color: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-style: italic; color: #555; }
    </style>
</head>
<body>
    <h1>지원 정책 보고서</h1>
    <p class="query"><strong>Query:</strong> {{ user_query }}</p>
    {% if projects %}
        {% for project in projects %}
        <div class="project">
            <h2>{{ project.projectName }}</h2>
            <p><strong>Organization:</strong> {{ project.organization }}</p>
            <p><strong>Application Period:</strong> {{ project.applicationPeriod }}</p>
            <p><strong>Summary:</strong> {{ project.summary }}</p>
            <div class="project-footer">
                <a href="{{ project.detailsUrl }}" target="_blank">View Details</a>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <p>No projects found for the given criteria.</p>
    {% endif %}
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
            tools=[search_bizinfo_projects]
        )

    def generate(self, query: str) -> List[Dict[str, Any]]:
        """
        Runs the agent to generate the HTML report based on the user's query.

        Args:
            query (str): The user's natural language request.

        Returns:
            List[Dict[str, Any]]: output should be in List[Dict[str, Any]] format
        """
        print(f"--- Starting report generation for query: '{query}' ---")

        # The full prompt is constructed here, before calling the agent.
        # This prompt tells the agent its role, what tools to use,
        # what the user wants, and the template for the final output.
        full_prompt = f"""
        ## 🎯 ROLE & GOAL
        You are a helpful assistant that generates HTML reports.
        Your task is to understand the user's request, use the 'search_bizinfo_projects'
        tool to find relevant data, and then check the provided json format to create
        a final json like the format.

        The final output MUST be only the generated json content and nothing else.

        Here is the json format to stick to:
        {{
            "projects": [
                {{
                    "projectName": "string",
                    "organization": "string",
                    "applicationPeriod": "string",
                    "summary": "string",
                    "detailsUrl": "string"
                }}
            ]
        }}

        User Request: {query}
        """

        # 1. The agent returns a result object, which is like a dictionary.
        agent_result = self.agent(full_prompt)

        # 2. The actual response from the LLM is a JSON string in the 'output' key.
        output_str = str(agent_result)
        print(output_str)

        projects_list = []
        try:
            # 3. Parse the JSON string into a Python dictionary.
            projects_list = json.loads(output_str)
            # 4. Extract the list of projects from the 'projects' key. Use .get() for safety.
            #projects_list = data.get("projects", [])
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error: Failed to parse LLM output as JSON. Error: {e}")
            print(f"Raw LLM output: {output_str}")
            # Return an empty list if parsing fails
            return []

        print("--- Report Generation Complete! ---")
        # 5. Return the list, which matches the expected type for the rendering function.
        return projects_list
    
# --- Jinja2 HTML Rendering Function ---
def render_html_report(user_query: str, projects: List[Dict[str, Any]], template_str: str) -> str:
    env = Environment(autoescape=select_autoescape(['html', 'xml']))
    template = env.from_string(template_str)
    return template.render(user_query=user_query, projects=projects)

def extract_projects_from_agent_result(result) -> List[Dict[str, Any]]:
    # If your tool returns JSON string, parse it here
    try:
        parsed = json.dumps(result)
        return parsed['projects'] 
    except Exception as e:
        print("Failed to parse agent output:", e)
        return []

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Configure the LLM provider (e.g., Amazon Bedrock)
    # IMPORTANT: Ensure your AWS credentials are configured in your environment.
    try:
        llm = BedrockModel(
            model_id="apac.anthropic.claude-3-sonnet-20240229-v1:0", # Use Claude 3 Sonnet instead
            region_name="ap-northeast-2",
            temperature=0.3
        )
    except Exception as e:
        print(f"Error initializing BedrockModel: {e}")
        print("Please ensure your AWS credentials and permissions are correctly configured.")
        exit()

    # 2. Set the API Key for the tool
    # You can get a key from the public data portal (data.go.kr) after signing up.
    # For now, it will use a placeholder which may result in an error from the API.


    # 3. Initialize the generator and define the user query
    generator = ReportGenerator(llm_provider=llm)
    user_query = "정보통신업 관련 지원사업을 5개 찾아줘."

    # 4. Generate the report
    result = generator.generate(user_query)
    print(result)
    print(type(result))
    print(result['projects'])
    # projects = extract_projects_from_agent_result(result)

    report_html = render_html_report(user_query, result['projects'], HTML_TEMPLATE)

    # 5. Save the report to a file
    report_filename = "bizinfo_report.html"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(str(report_html))

    print(f"\nSuccessfully generated report. Please open '{report_filename}' in your browser.")
