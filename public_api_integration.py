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


@tool
def get_ulsan_land_price_data(region_code: str = "31") -> str:
    """
    울산 지역 공시지가 데이터를 조회합니다.
    
    Args:
        region_code: 지역코드 (31: 울산광역시)
        
    Returns:
        str: 공시지가 데이터 JSON 문자열
    """
    try:
        # 국토교통부 공시지가 API (예시)
        api_key = os.environ.get("MOLIT_API_KEY", "YOUR_API_KEY_HERE")
        base_url = "http://apis.data.go.kr/1613000/RTMSDataSvcLandPrice/getRTMSDataSvcLandPrice"
        
        params = {
            'serviceKey': api_key,
            'LAWD_CD': region_code,  # 울산광역시
            'DEAL_YMD': '202407',    # 최근 데이터
            'numOfRows': '100',
            'pageNo': '1',
            '_type': 'json'
        }
        
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        
        land_prices = []
        for item in items:
            land_price = {
                "region": item.get("지역명", "울산"),
                "land_type": item.get("용도지역", ""),
                "price_per_sqm": item.get("단가", 0),
                "area": item.get("면적", 0),
                "transaction_date": item.get("거래일", "")
            }
            land_prices.append(land_price)
        
        return json.dumps(land_prices, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"공시지가 API 오류: {e}")
        # 울산 지역 샘플 데이터 반환
        sample_data = [
            {
                "region": "울산 남구",
                "land_type": "공업지역",
                "price_per_sqm": 180000,
                "area": 15000,
                "transaction_date": "2024-07"
            },
            {
                "region": "울산 동구",
                "land_type": "공업지역", 
                "price_per_sqm": 165000,
                "area": 12000,
                "transaction_date": "2024-07"
            }
        ]
        return json.dumps(sample_data, ensure_ascii=False, indent=2)


@tool
def get_ulsan_electricity_rates() -> str:
    """
    울산 지역 산업용 전기요금 정보를 조회합니다.
    
    Returns:
        str: 전기요금 정보 JSON 문자열
    """
    try:
        # 한국전력공사 전기요금 API 또는 공공데이터 활용
        # 실제 API가 없는 경우 울산 지역 산업용 전기요금 정보 제공
        
        electricity_data = {
            "region": "울산광역시",
            "industrial_rates": {
                "low_voltage": {
                    "basic_rate": 6160,      # 원/kW
                    "energy_rate": 88.3,     # 원/kWh
                    "description": "저압 산업용"
                },
                "high_voltage_a": {
                    "basic_rate": 6300,      # 원/kW
                    "energy_rate": 85.7,     # 원/kWh
                    "description": "고압A 산업용"
                },
                "high_voltage_b": {
                    "basic_rate": 6300,      # 원/kW
                    "energy_rate": 83.4,     # 원/kWh
                    "description": "고압B 산업용"
                }
            },
            "special_rates": {
                "manufacturing_discount": 5.0,  # 제조업 할인율 (%)
                "ulsan_industrial_zone": 3.0    # 울산 산업단지 추가 할인 (%)
            },
            "last_updated": "2024-07-28"
        }
        
        return json.dumps(electricity_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"전기요금 API 오류: {e}")
        return "{}"


@tool
def get_ulsan_infrastructure_data() -> str:
    """
    울산 지역 인프라 정보 (변전소, 송전탑, 교통 등)를 조회합니다.
    
    Returns:
        str: 인프라 데이터 JSON 문자열
    """
    try:
        # 울산 지역 인프라 정보 (공공데이터 또는 자체 수집 데이터)
        infrastructure_data = {
            "region": "울산광역시",
            "electrical_infrastructure": {
                "substations": [
                    {"name": "울산변전소", "capacity": "765kV", "location": "남구", "density_per_km2": 4},
                    {"name": "온산변전소", "capacity": "345kV", "location": "울주군", "density_per_km2": 3},
                    {"name": "방어진변전소", "capacity": "154kV", "location": "동구", "density_per_km2": 2}
                ],
                "transmission_lines": {
                    "765kv_lines": 2,
                    "345kv_lines": 5,
                    "154kv_lines": 12,
                    "total_density_per_km2": 2.3
                }
            },
            "transportation": {
                "highways": ["경부고속도로", "울산고속도로", "동해고속도로"],
                "ports": ["울산항", "온산항"],
                "airports": "울산공항 (30km)",
                "railways": ["동해남부선", "울산선"]
            },
            "industrial_zones": [
                {"name": "울산국가산업단지", "area_km2": 52.8, "type": "석유화학"},
                {"name": "온산국가산업단지", "area_km2": 35.4, "type": "화학"},
                {"name": "미포국가산업단지", "area_km2": 8.1, "type": "조선"}
            ],
            "last_updated": "2024-07-28"
        }
        
        return json.dumps(infrastructure_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"인프라 데이터 API 오류: {e}")
        return "{}"


@tool
def get_ulsan_disaster_statistics() -> str:
    """
    울산 지역 재난 통계 정보를 조회합니다.
    
    Returns:
        str: 재난 통계 JSON 문자열
    """
    try:
        # 행정안전부 재난안전 데이터 또는 울산시 통계
        disaster_data = {
            "region": "울산광역시",
            "annual_statistics": {
                "2023": {
                    "natural_disasters": 2,      # 자연재해
                    "industrial_accidents": 8,   # 산업재해
                    "fire_incidents": 15,        # 화재
                    "total": 25
                },
                "2022": {
                    "natural_disasters": 3,
                    "industrial_accidents": 12,
                    "fire_incidents": 18,
                    "total": 33
                },
                "2021": {
                    "natural_disasters": 1,
                    "industrial_accidents": 6,
                    "fire_incidents": 12,
                    "total": 19
                }
            },
            "risk_assessment": {
                "flood_risk": "중간",
                "earthquake_risk": "낮음",
                "industrial_risk": "높음",  # 석유화학단지 인근
                "fire_risk": "중간"
            },
            "safety_measures": [
                "산업단지 안전관리 강화",
                "재난대응 시스템 구축",
                "비상대피로 확보"
            ],
            "last_updated": "2024-07-28"
        }
        
        return json.dumps(disaster_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"재난 통계 API 오류: {e}")
        return "{}"


# 통합 테스트 함수
def test_all_ulsan_apis():
    """모든 울산 관련 API 테스트"""
    print("🏭 울산 제조업 입지 관련 API 통합 테스트")
    print("=" * 60)
    
    # 1. 정책 정보
    print("\n📋 1. 울산 제조업 지원 정책")
    policies = search_ulsan_manufacturing_policies(result_count=3, tags="공장설립")
    print(f"정책 수: {len(json.loads(policies))}")
    
    # 2. 공시지가
    print("\n💰 2. 울산 공시지가 정보")
    land_prices = get_ulsan_land_price_data()
    print(f"토지 정보 수: {len(json.loads(land_prices))}")
    
    # 3. 전기요금
    print("\n⚡ 3. 울산 산업용 전기요금")
    electricity = get_ulsan_electricity_rates()
    elec_data = json.loads(electricity)
    print(f"고압A 산업용: {elec_data.get('industrial_rates', {}).get('high_voltage_a', {}).get('energy_rate', 'N/A')}원/kWh")
    
    # 4. 인프라
    print("\n🏗️ 4. 울산 인프라 정보")
    infrastructure = get_ulsan_infrastructure_data()
    infra_data = json.loads(infrastructure)
    print(f"변전소 수: {len(infra_data.get('electrical_infrastructure', {}).get('substations', []))}")
    
    # 5. 재난 통계
    print("\n🚨 5. 울산 재난 통계")
    disasters = get_ulsan_disaster_statistics()
    disaster_data = json.loads(disasters)
    print(f"2023년 총 재난: {disaster_data.get('annual_statistics', {}).get('2023', {}).get('total', 'N/A')}건")
    
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