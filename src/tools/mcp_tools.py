"""MCP Tools - Strands Agents Workshop"""
import httpx
import wikipedia
import asyncio
import json
from typing import Dict, Any
from strands import tool

@tool
def wikipedia_search(query: str) -> Dict[str, Any]:
    """Search Wikipedia for information
    
    Args:
        query: Search query
        
    Returns:
        Dictionary containing search results
    """
    try:
        # 한국어 우선, 실패시 영어로 fallback
        try:
            wikipedia.set_lang("ko")
            page = wikipedia.page(query)
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
            wikipedia.set_lang("en")
            page = wikipedia.page(query)
        
        # 요약 텍스트 제한 (500자)
        summary = page.summary
        if len(summary) > 500:
            summary = summary[:500] + "..."
        
        return {
            "success": True,
            "title": page.title,
            "summary": summary,
            "url": page.url
        }
        
    except wikipedia.exceptions.DisambiguationError as e:
        return {
            "success": False,
            "error": "Multiple results found",
            "options": e.options[:5]  # 상위 5개만
        }
         
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@tool
def duckduckgo_search(query: str) -> Dict[str, Any]:
    """Search DuckDuckGo for information
    
    Args:
        query: Search query
        
    Returns:
        Dictionary containing search results
    """
    try:
        async def fetch_search_results():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": "1",
                        "skip_disambig": "1"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Abstract 정보가 있는 경우
                    if data.get("Abstract"):
                        return {
                            "success": True,
                            "title": data.get("Heading", query),
                            "summary": data["Abstract"],
                            "url": data.get("AbstractURL", "")
                        }
                    
                    # Definition 정보가 있는 경우
                    elif data.get("Definition"):
                        return {
                            "success": True,
                            "title": query,
                            "summary": data["Definition"],
                            "url": data.get("DefinitionURL", "")
                        }
                    
                    # 관련 주제가 있는 경우
                    elif data.get("RelatedTopics"):
                        topics = data["RelatedTopics"][:3]
                        summaries = []
                        for topic in topics:
                            if isinstance(topic, dict) and topic.get("Text"):
                                summaries.append(topic["Text"])
                        
                        if summaries:
                            return {
                                "success": True,
                                "title": query,
                                "summary": " | ".join(summaries)
                            }
                
                return {"success": False, "error": "No results found"}
        
        return asyncio.run(fetch_search_results())
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def get_position(location: str) -> Dict[str, Any]:
    """Get latitude and longitude coordinates for a given location name
    
    Args:
        location: The name of the location to get coordinates for
        
    Returns:
        Dictionary containing coordinates and location information
    """
    try:
        # Using OpenStreetMap Nominatim API for geocoding
        async def fetch_coordinates():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": location,
                        "format": "json",
                        "limit": 1
                    },
                    headers={
                        "User-Agent": "StrandsAgents/1.0",
                        "Accept": "application/json",
                        "Accept-Charset": "utf-8"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200: 
                    data = response.json()  
                    if data:
                        result = data[0]
                        return {
                            "success": True,
                            "latitude": float(result["lat"]),
                            "longitude": float(result["lon"]),
                            "display_name": result.get("display_name", location)
                        }
                
                return {"success": False, "error": "Location not found"}
        
        # 비동기 함수 실행
        return asyncio.run(fetch_coordinates())
        
    except Exception as e:
        return {"success": False, "error": str(e)}
 
 

# Test code
# 테스트 코드 (파일 하단에 추가)
if __name__ == "__main__":
    print("🧪 MCP Tool test..")
    print("=" * 50)
    
    # 위치 검색 테스트
    print("\n🌍 geo location test:")
    pos_result = get_position("newyork")
    print(f"success: {pos_result['success']}")
    if pos_result["success"]:
        print(f"location: {pos_result['display_name']}")
        print(f"geo: {pos_result['latitude']}, {pos_result['longitude']}")
    
    # Wikipedia 테스트
    print("\n📚 Wikipedia search test:")
    wiki_result = wikipedia_search("AI")
    print(f"success: {wiki_result['success']}")
    if wiki_result["success"]:
        print(f"title: {wiki_result['title']}")
        print(f"summary: {wiki_result['summary'][:100]}...")
    
    # DuckDuckGo 테스트
    print("\n🦆 DuckDuckGo search test:")
    ddg_result = duckduckgo_search("Python programming")
    print(f"success: {ddg_result['success']}")
    if ddg_result["success"]:
        print(f"title: {ddg_result['title']}")
        print(f"summary: {ddg_result['summary'][:100]}...")
