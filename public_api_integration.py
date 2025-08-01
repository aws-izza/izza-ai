import os
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any
import json

@tool
def search_ulsan_manufacturing_policies(
    result_count: int = 10,
    category_id: Optional[str] = None,
    tags: Optional[str] = None,
) -> str:
    """
    울산 지역 제조업 관련 정부 지원 정책을 검색합니다.

    Args:
        result_count (int): 반환할 정책 수. 기본값 10.
        category_id (Optional[str]): 카테고리 코드. 제조업 관련:
                                     '01'(금융지원), '02'(기술지원), '03'(인력지원),
                                     '04'(수출지원), '05'(내수지원), '06'(창업지원).
        tags (Optional[str]): 필터링용 해시태그 (쉼표 구분).
                              예: '울산,제조업,공장설립'

    Returns:
        str: 울산 제조업 관련 정책 목록 JSON 문자열
    """
    try:
        # NOTE: The public API key for bizinfo.go.kr is often rate-limited or
        # may require registration. This is a placeholder key.
        api_key = os.environ.get("BIZINFO_API_KEY", "YOUR_API_KEY_HERE")
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
        # 울산 지역 제조업에 특화된 기본 태그 추가
        default_tags = "울산,제조업"
        if tags:
            tags = f"{default_tags},{tags}"
        else:
            tags = default_tags
        params['hashtags'] = tags

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        print(f"--- [Tool] Calling Bizinfo API with params: {params} ---")
        response = requests.get(base_url, headers=headers, params=params, timeout=15)
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


# Example usage for setting up the API key
def setup_api_key():
    """Set up the Bizinfo API key from environment or use placeholder"""
    os.environ['BIZINFO_API_KEY'] = 'VtdTy4'  # Replace with your actual API key


if __name__ == "__main__":
    # Test the API integration
    setup_api_key()
    
    # Example API call
    result = search_ulsan_manufacturing_policies(
        result_count=5,
        category_id="02",  # Technology support category
        tags="공장설립,산업단지"
    )
    
    print("API Response:")
    print(result)

# 통합 테스트 함수
def test_all_ulsan_apis():
    """모든 울산 관련 API 테스트"""
    print("🏭 울산 제조업 입지 관련 API 통합 테스트")
    print("=" * 60)
    
    # 1. 정책 정보
    print("\n📋 1. 울산 제조업 지원 정책")
    policies = search_ulsan_manufacturing_policies(result_count=3, tags="공장설립")
    print(f"정책 수: {len(json.loads(policies))}")
    
    print("\n" + "=" * 60)
    print("✅ 울산 제조업 입지 API 통합 완료!")


if __name__ == "__main__":
    # 기존 테스트
    setup_api_key()
    
    result = search_ulsan_manufacturing_policies(
        result_count=5,
        category_id="02",  # Technology support category
        tags="공장설립,산업단지"
    )
    
    print("API Response:")
    print(result)
    
    # 통합 테스트 실행
    print("\n" + "="*60)
    test_all_ulsan_apis()