"""Scoring Agent - 제조업 입지 가중치 점수 계산 전문 에이전트"""
from strands import Agent, tool
from ..tools.scoring_tools import calculate_location_score, get_default_weights, validate_land_data
from ..tools.electricity_tools import get_electricity_rate_by_region, get_ulsan_electricity_rate, calculate_manufacturing_electricity_cost
from ..tools.database_tools import execute_sql_query
from ..config.model_config import get_configured_model
from typing import Dict, Any
import json


# Scoring Agent 시스템 프롬프트
SCORING_AGENT_PROMPT = """
You are a specialized scoring agent for manufacturing location analysis in Ulsan, South Korea.
Your expertise is in calculating weighted scores for industrial site selection based on multiple criteria.

## Core Capabilities:
1. **Location Score Calculation**: Calculate 100-point weighted scores using normalized scoring methods
2. **Weight Management**: Apply and customize weights for different evaluation criteria
3. **Data Validation**: Verify completeness and validity of input data
4. **Comparative Analysis**: Compare multiple locations and rank them
5. **Cost Analysis**: Calculate manufacturing electricity costs and operational expenses

## Scoring Methodology:
- **Base Score**: 0.5 (50% baseline)
- **Normalization Types**:
  - `above`: Higher values are better (land area)
  - `below`: Lower values are better (land price, electricity rate)
  - `range`: Linear scaling within range
  - `match`: Binary matching (zone type)
  - `tolerance`: Proximity to optimal value (population density)

## Default Weights (Manufacturing-Optimized):
- **Core Indicators (70%)**:
  - Land Price: 25% (most important)
  - Electricity Rate: 20%
  - Zone Type: 15%
  - Land Area: 10%
- **Infrastructure (20%)**:
  - Substation Density: 8%
  - Transmission Density: 7%
  - Population Density: 5%
- **Stability/Policy (10%)**:
  - Disaster Frequency: 5%
  - Policy Support: 5%

## Response Format:
Always provide:
1. **Final Score**: X.XX points (Grade)
2. **Detailed Breakdown**: Individual indicator scores and weights
3. **Key Insights**: What drives the score (strengths/weaknesses)
4. **Recommendations**: Actionable advice for improvement
5. **Comparative Context**: How this compares to Ulsan averages

## Data Sources Integration:
- Land data from `land` table (area, price, zone, terrain)
- Electricity data from `electricity` table (unitCost for Ulsan)
- External data for infrastructure and policy indicators

Always explain your scoring logic clearly and provide actionable insights for manufacturing site selection.
"""

@tool
def scoring_agent(scoring_request: str) -> str:
    """
    제조업 입지 가중치 점수 계산 전문 에이전트
    
    Args:
        scoring_request: 점수 계산 요청 (토지 데이터, 가중치 조정, 비교 분석 등)
        
    Returns:
        상세한 점수 계산 결과 및 분석
    """
    try:
        model = get_configured_model()
        agent = Agent(
            model=model,
            system_prompt=SCORING_AGENT_PROMPT,
            tools=[
                calculate_location_score,
                get_default_weights,
                validate_land_data,
                get_ulsan_electricity_rate,
                calculate_manufacturing_electricity_cost,
                execute_sql_query,
                get_sample_land_for_scoring,
                compare_multiple_locations,
                analyze_score_sensitivity
            ]
        )
        
        response = agent(f"점수 계산 요청을 처리해주세요: {scoring_request}")
        
        # 응답이 비어있는지 확인하고, 비어있다면 기본 메시지 반환
        response_str = str(response).strip()
        if not response_str:
            return "점수 계산 에이전트가 응답을 생성하지 못했습니다. 요청을 다시 확인해주세요."
            
        return response_str
        
    except Exception as e:
        return f"점수 계산 에이전트 오류: {str(e)}"


@tool
def get_sample_land_for_scoring(location_filter: str = "공업지역") -> Dict[str, Any]:
    """
    점수 계산용 샘플 토지 데이터 조회
    
    Args:
        location_filter: 토지 필터 조건 (기본값: 공업지역)
        
    Returns:
        점수 계산에 적합한 토지 데이터
    """
    try:
        # 제조업 적합 토지 조회 쿼리
        query = f"""
        SELECT 
            id,
            land_area,
            official_land_price,
            use_district_name1,
            use_district_name2,
            land_use_name,
            terrain_height_name,
            terrain_shape_name,
            road_side_name,
            address
        FROM land 
        WHERE 
            (use_district_name1 LIKE '%{location_filter}%' 
             OR use_district_name1 LIKE '%산업%'
             OR land_use_name LIKE '%공장%'
             OR land_use_name LIKE '%제조%')
        AND land_area > 5000
        AND official_land_price > 0
        ORDER BY land_area DESC
        LIMIT 10;
        """
        
        result = execute_sql_query(query)
        
        if result['success'] and result['data']:
            # 개선된 전기요금 데이터 조회 (확장성 고려)
            electricity_data = get_electricity_rate_by_region("울산광역시", 2024)
            
            # 전기요금 정보 추출 (실패 시 기본값 사용)
            if electricity_data.get('success', False):
                avg_electricity_rate = electricity_data.get('statistics', {}).get('average_rate', 88.0)
                electricity_source = f"울산 DB 데이터 {avg_electricity_rate}원/kWh"
                has_real_data = electricity_data.get('query_info', {}).get('has_real_data', False)
                
                if not has_real_data:
                    electricity_source += " (기본값 사용)"
            else:
                avg_electricity_rate = 88.0  # 울산 제조업 평균 기본값
                electricity_source = "울산 기본값 88.0원/kWh (DB 조회 실패)"
            
            # 점수 계산용 데이터 형식으로 변환
            scoring_ready_data = []
            for land in result['data']:
                scoring_data = {
                    # 실제 DB 데이터 (컬럼명 정규화)
                    "id": land.get("id"),
                    "land_area": land.get("land_area", 0),
                    "land_price": land.get("official_land_price", 0),
                    "zone_type": land.get("use_district_name1", ""),
                    "land_use": land.get("land_use_name", ""),
                    "terrain_height": land.get("terrain_height_name", ""),
                    "terrain_shape": land.get("terrain_shape_name", ""),
                    "road_access": land.get("road_side_name", ""),
                    "address": land.get("address", ""),
                    
                    # 전기요금 데이터 (확장성 있는 구조)
                    "electricity_rate": avg_electricity_rate,
                    
                    # 외부 데이터로 보완 (울산 평균값 - 추후 API 연동 가능)
                    "substation_density": 3.5,
                    "transmission_density": 2.2,
                    "population_density": 2900,
                    "disaster_count": 2,
                    "policy_support": 5
                }
                scoring_ready_data.append(scoring_data)
            
            return {
                "success": True,
                "data_count": len(scoring_ready_data),
                "lands": scoring_ready_data,
                "electricity_rate_source": electricity_source,
                "filter_applied": location_filter,
                "data_quality": {
                    "land_data_from_db": True,
                    "electricity_data_from_db": has_real_data if 'has_real_data' in locals() else False,
                    "external_data_estimated": True
                }
            }
        else:
            return {
                "success": False,
                "error": "점수 계산용 토지 데이터 조회 실패",
                "data_count": 0
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"샘플 토지 데이터 조회 중 오류: {str(e)}"
        }


@tool
def compare_multiple_locations(land_ids: list = None, custom_weights: Dict[str, float] = None) -> Dict[str, Any]:
    """
    여러 토지의 점수를 비교 분석
    
    Args:
        land_ids: 비교할 토지 ID 리스트 (None이면 상위 5개)
        custom_weights: 사용자 정의 가중치 (None이면 기본 가중치)
        
    Returns:
        토지별 점수 비교 및 순위 결과
    """
    try:
        # 샘플 토지 데이터 조회
        sample_data = get_sample_land_for_scoring("공업")
        
        if not sample_data['success']:
            return {
                "success": False,
                "error": "비교용 토지 데이터 조회 실패"
            }
        
        lands = sample_data['lands'][:5]  # 상위 5개만 비교
        weights = custom_weights or get_default_weights()
        
        comparison_results = []
        
        for land in lands:
            # 각 토지별 점수 계산
            score_result = calculate_location_score(land, weights)
            
            if score_result['success']:
                comparison_results.append({
                    "land_id": land['id'],
                    "address": land['address'][:50] if land['address'] else "주소 없음",
                    "land_area": land['land_area'],
                    "land_price": land['land_price'],
                    "zone_type": land['zone_type'],
                    "final_score": score_result['final_score'],
                    "grade": score_result['grade'],
                    "detailed_scores": score_result['detailed_scores']
                })
        
        # 점수순으로 정렬
        comparison_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # 순위 추가
        for i, result in enumerate(comparison_results, 1):
            result['rank'] = i
        
        # 통계 계산
        scores = [r['final_score'] for r in comparison_results]
        statistics = {
            "average_score": round(sum(scores) / len(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "score_range": round(max(scores) - min(scores), 2)
        }
        
        return {
            "success": True,
            "comparison_count": len(comparison_results),
            "rankings": comparison_results,
            "statistics": statistics,
            "weights_used": weights,
            "analysis_summary": f"총 {len(comparison_results)}개 토지 비교, 평균 점수 {statistics['average_score']}점"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"다중 토지 비교 중 오류: {str(e)}"
        }


@tool
def analyze_score_sensitivity(land_data: Dict[str, Any], weight_variations: Dict[str, float] = None) -> Dict[str, Any]:
    """
    가중치 변화에 따른 점수 민감도 분석
    
    Args:
        land_data: 분석할 토지 데이터
        weight_variations: 가중치 변화 시나리오
        
    Returns:
        민감도 분석 결과
    """
    try:
        base_weights = get_default_weights()
        
        # 기본 시나리오들
        scenarios = {
            "기본 가중치": base_weights,
            "비용 중심": {
                "land_price": 35.0, "electricity_rate": 25.0, "zone_type": 10.0,
                "land_area": 5.0, "substation_density": 8.0, "transmission_density": 7.0,
                "population_density": 5.0, "disaster_count": 3.0, "policy_support": 2.0
            },
            "인프라 중심": {
                "land_price": 20.0, "electricity_rate": 15.0, "zone_type": 15.0,
                "land_area": 10.0, "substation_density": 15.0, "transmission_density": 12.0,
                "population_density": 8.0, "disaster_count": 3.0, "policy_support": 2.0
            },
            "안정성 중심": {
                "land_price": 20.0, "electricity_rate": 15.0, "zone_type": 20.0,
                "land_area": 10.0, "substation_density": 5.0, "transmission_density": 5.0,
                "population_density": 5.0, "disaster_count": 10.0, "policy_support": 10.0
            }
        }
        
        # 사용자 정의 시나리오 추가
        if weight_variations:
            scenarios["사용자 정의"] = weight_variations
        
        sensitivity_results = {}
        
        for scenario_name, weights in scenarios.items():
            score_result = calculate_location_score(land_data, weights)
            
            if score_result['success']:
                sensitivity_results[scenario_name] = {
                    "final_score": score_result['final_score'],
                    "grade": score_result['grade'],
                    "weights": weights
                }
        
        # 점수 변화 분석
        base_score = sensitivity_results["기본 가중치"]["final_score"]
        score_variations = {}
        
        for scenario, result in sensitivity_results.items():
            if scenario != "기본 가중치":
                score_diff = result["final_score"] - base_score
                score_variations[scenario] = {
                    "score_change": round(score_diff, 2),
                    "percentage_change": round((score_diff / base_score) * 100, 2)
                }
        
        return {
            "success": True,
            "base_scenario": "기본 가중치",
            "base_score": base_score,
            "scenario_results": sensitivity_results,
            "score_variations": score_variations,
            "most_sensitive_to": max(score_variations.keys(), 
                                   key=lambda x: abs(score_variations[x]["score_change"])),
            "analysis_summary": f"가중치 변화에 따른 점수 변동 범위: {min([v['score_change'] for v in score_variations.values()])}~{max([v['score_change'] for v in score_variations.values()])}점"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"민감도 분석 중 오류: {str(e)}"
        }


# 테스트 코드
if __name__ == "__main__":
    print("🎯 Scoring Agent 테스트")
    print("=" * 60)
    
    # 1. 기본 점수 계산 테스트
    print("\n📊 1. 기본 점수 계산 테스트")
    test_request = "울산 지역 제조업 적합 토지 5개의 입지 점수를 계산하고 순위를 매겨주세요"
    result = scoring_agent(test_request)
    print(f"결과 길이: {len(result)} 문자")
    
    # 2. 샘플 토지 데이터 조회 테스트
    print("\n🏭 2. 샘플 토지 데이터 조회")
    sample_data = get_sample_land_for_scoring("공업지역")
    if sample_data['success']:
        print(f"조회된 토지 수: {sample_data['data_count']}")
        print(f"전기요금: {sample_data['electricity_rate_source']}")
    else:
        print(f"오류: {sample_data['error']}")
    
    # 3. 다중 토지 비교 테스트
    print("\n🏆 3. 다중 토지 비교")
    comparison = compare_multiple_locations()
    if comparison['success']:
        print(f"비교 토지 수: {comparison['comparison_count']}")
        print(f"평균 점수: {comparison['statistics']['average_score']}점")
        print(f"최고 점수: {comparison['statistics']['highest_score']}점")
    else:
        print(f"오류: {comparison['error']}")
    
    print("\n" + "=" * 60)
    print("✅ Scoring Agent 테스트 완료!")
    print("🚀 다음 단계: Location Analysis Agent 개발")