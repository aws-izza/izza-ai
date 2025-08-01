"""Sub Agents - Strands Agents Workshop"""
from strands import Agent, tool
from strands_tools import http_request
from ..tools.mcp_tools import get_position, wikipedia_search, duckduckgo_search
from ..tools.database_tools import execute_sql_query, get_database_schema, get_table_sample, get_table_list
from .scoring_agent import scoring_agent
from ..config.model_config import get_configured_model
from typing import Dict, Any


# Search Agent - 지능적 검색 도구 선택
SEARCH_AGENT_PROMPT = """
You are an intelligent search specialist agent.
Analyze user search requests and select the most appropriate search tool to use.

 Search Tool Selection Strategy:

1. **WIKIPEDIA Priority Use Cases:**
   - Historical facts, people, regions, country information
   - Scientific concepts, academic content
   - Comprehensive explanations of well-established topics
   - Examples: "Einstein", "France", "quantum mechanics", "Renaissance"

2. **DUCKDUCKGO Priority Use Cases:**
   - Technical term definitions, programming concepts
   - Latest trends, modern topics
   - Cases requiring simple definitions or explanations
   - Examples: "What is API", "machine learning definition", "React framework"

3. **Selection Principles:**
   - First use only one tool for searching
   - Use additional tools only if results are insufficient or failed
   - Using both tools should be a last resort

After searching, analyze the results to summarize them in an easy-to-understand way for users, and specify which search tool was used.
"""

@tool
def search_agent(query: str) -> str:
    """
    Optimized information search agent through intelligent search tool selection

    Args:
        query: Content to search for

    Returns:
        Optimized answer through selected search tool
    """
    try:
        model = get_configured_model()
        agent = Agent(
            model=model,
            system_prompt=SEARCH_AGENT_PROMPT,
            tools=[wikipedia_search, duckduckgo_search]
        )
        
        response = agent(f"다음 검색 요청을 처리해주세요: {query}")
        return str(response)
        
    except Exception as e:
        return f"검색 에이전트 오류: {str(e)}"


# Weather Agent - 위치 기반 날씨 정보
WEATHER_AGENT_PROMPT = """You are a weather assistant with HTTP capabilities. You can:

1. Make HTTP requests to the National Weather Service API
2. Process and display weather forecast data
3. Provide weather information for locations in the United States

When retrieving weather information:
1. First get the coordinates using get_position tool if needed
2. Then get the grid information using https://api.weather.gov/points/{latitude},{longitude}
3. Finally use the returned forecast URL to get the actual forecast

When displaying responses:
- Format weather data in a human-readable way
- Highlight important information like temperature, precipitation, and alerts
- Handle errors appropriately
- Convert technical terms to user-friendly language

Always explain the weather conditions clearly and provide context for the forecast.
"""

@tool 
def weather_agent(location: str) -> str:
    """
    Weather information agent using National Weather Service API

    Args:
        location: Location to get weather for

    Returns:
        Formatted weather information
    """
    try:
        model = get_configured_model()
        agent = Agent(
            model=model,
            system_prompt=WEATHER_AGENT_PROMPT,
            tools=[get_position, http_request]  # 가이드 문서와 동일
        )

        response = agent(f"What's the weather like in {location}?")
        return str(response)

    except Exception as e:
        return f"Weather agent error: {str(e)}"


# Conversation Agent - 일반 대화 처리
CONVERSATION_AGENT_PROMPT = """
You are a friendly and helpful conversation specialist agent.

Characteristics:
- Communicate with a warm and friendly tone
- Understand and empathize with users' emotions
- Use appropriate emojis to enhance expressiveness
- Provide concise yet meaningful responses

Approach by conversation type:
- Greetings: Warmly acknowledge greetings
- Emotional expressions: Show empathy and respond appropriately
- General questions: Provide helpful answers
- Thank you messages: Accept graciously

Guidelines:
- For questions requiring search or weather information, guide users that other agents will handle them
- Keep responses brief, 2-3 sentences maximum
- Maintain natural and human-like conversation
"""

@tool
def conversation_agent(message: str) -> str:
    """
    General conversation handling agent

    Args:
        message: User message

    Returns:
        Conversation response
    """ 
    model = get_configured_model()
    agent = Agent(
        model=model,
        system_prompt=CONVERSATION_AGENT_PROMPT,
        tools=[]
    )
    
    response = agent(message)
    return str(response)

# Database Agent - PostgreSQL 데이터베이스 쿼리 전문
DATABASE_AGENT_PROMPT = """
You are a database specialist agent with PostgreSQL expertise.
You can execute SQL queries and analyze database schemas through SSH tunnel connection.

## Available Tables and Key Information:
1. **land** table - Main land parcel data:
   - id, land_area, official_land_price, use_district_name1, use_district_name2
   - land_use_name, terrain_height_name, terrain_shape_name, road_side_name
   - address, beopjung_dong_code, boundary (polygon data)
   
2. **electricity** table - Electricity rate data:
   - year, month, unitCost, full_code, metro, city
   - For Ulsan: metro = '울산광역시'

## Query Guidelines for Manufacturing Location Analysis:
- Use `land` table for land parcel information (NOT manufacturing_land_parcels)
- Filter manufacturing-suitable land: use_district_name1 LIKE '%공업%' OR use_district_name1 LIKE '%산업%'
- For Ulsan region: Check beopjung_dong_code or address patterns
- Join with electricity table using regional codes when needed

Capabilities:
1. **Schema Analysis**: Explore database structure, tables, and relationships
2. **Query Execution**: Execute SELECT queries safely
3. **Data Analysis**: Interpret query results and provide insights
4. **Query Optimization**: Suggest efficient query patterns

Workflow:
1. First check if you have schema information about the requested tables
2. If not, use get_database_schema() to explore the database structure
3. Use get_table_sample() to understand data patterns if needed
4. Execute appropriate SELECT queries using execute_sql_query()
5. Analyze and present results in a user-friendly format

CRITICAL: When joining tables, you MUST qualify column names with the table name (e.g., `land.id`, `electricity.unitCost`) to prevent ambiguity.

Safety Guidelines:
- Only SELECT queries are allowed (no INSERT, UPDATE, DELETE)
- Limit result sets to prevent performance issues
- Always explain query logic and results clearly
- Handle errors gracefully and suggest alternatives

When presenting results:
- **Always provide clear, specific information to the user**
- Format data in readable tables or lists with actual values
- Show concrete results, not just descriptions
- For table lists: show actual table names clearly
- For data queries: display the actual data in organized format
- Highlight key insights and patterns
- Explain any technical terms or database concepts
- Suggest follow-up queries if relevant

IMPORTANT: Always include the actual query results in your response, not just descriptions of what you found.
"""

@tool
def database_agent(query_request: str) -> str:
    """
    PostgreSQL database query and analysis agent
    
    Args:
        query_request: User's database query request or question
        
    Returns:
        Database query results and analysis
    """
    try:
        model = get_configured_model()
        agent = Agent(
            model=model,
            system_prompt=DATABASE_AGENT_PROMPT,
            tools=[get_table_list, execute_sql_query, get_database_schema, get_table_sample]
        )
        
        response = agent(f"데이터베이스 요청을 처리해주세요: {query_request}")
        return str(response)
        
    except Exception as e:
        return f"데이터베이스 에이전트 오류: {str(e)}"


# Planning Agent - 실행 계획 수립 전문
PLANNING_AGENT_PROMPT = """
You are an execution planning specialist.
Analyze user requests and determine which sub-agents to use and in what order.

Available sub-agents:
    
• database_agent: PostgreSQL database queries and analysis
  - Execute SELECT queries on connected database
  - Analyze database schema and structure
  - Provide data insights and analysis
  
Create execution plans in the following format:

📋 PLANNING AGENT EXECUTION PLAN
====================================
**📋 Execution Plan:**
1. [agent_name] - [purpose and reasoning]
2. [agent_name] - [purpose and reasoning]

**🎯 Expected Result:**
[Final result to be provided to the user]

**⚠️ Important Notes:**
[Special limitations or considerations to keep in mind]
====================================
"""

@tool
def planning_agent(user_request: str) -> str:
    """
    사용자 요청에 대한 실행 계획을 수립하는 에이전트
    
    Args:
        user_request: 사용자 요청
        
    Returns:
        상세한 실행 계획
    """
    try:
        agent = Agent(
            model=get_configured_model(),
            system_prompt=PLANNING_AGENT_PROMPT,
            tools=[]
        )
        
        planning_prompt = f"""
        User request: "{user_request}"
        
        Create a detailed execution plan to handle this request.
        
        Important considerations:
        - weather_agent only supports US regions
        - search_agent optimally chooses between Wikipedia and DuckDuckGo
        - conversation_agent is for general conversation that doesn't require search
        - For complex requests, consider logical sequence
        
        You must respond in the specified format.
        """
        
        response = agent(planning_prompt)
        return str(response)
        
    except Exception as e:
        return f"계획 수립 중 오류가 발생했습니다: {str(e)}"

# 테스트 코드 (파일 하단에 추가)
if __name__ == "__main__":
    print("🧪 Sub Agent 테스트...")
    print("=" * 60)
    
    # Database Agent 테스트
    print("\n🗄️ Database Agent 테스트:")
    print("-" * 30)
    database_result = database_agent("데이터베이스에 어떤 테이블들이 있는지 알려줘")
    print(database_result[:200] + "..." if len(database_result) > 200 else database_result)
    
    # Planning Agent 테스트
    print("\n📋 Planning Agent 테스트:")
    print("-" * 30)
    planning_result = planning_agent("파리에 대해 알려주고 날씨도 확인해줘")
    print(planning_result[:300] + "..." if len(planning_result) > 300 else planning_result)
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
