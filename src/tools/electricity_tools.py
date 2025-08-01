"""Electricity Tools - 전기요금 데이터 조회 및 분석"""
from typing import Dict, Any, List, Optional
from strands import tool
from .database_tools import execute_sql_query
import statistics


@tool
def get_electricity_rate_by_region(metro: str = "울산광역시", year: int = 2024, month: Optional[int] = None) -> Dict[str, Any]:
    """
    지역별 전기요금 데이터를 조회합니다. (확장성을 위한 범용 함수)
    
    Args:
        metro: 조회할 광역시/도 (기본값: 울산광역시)
        year: 조회할 연도 (기본값: 2024)
        month: 조회할 월 (None이면 최신 데이터)
        
    Returns:
        지역별 전기요금 정보
    """
    try:
        # 지역별 전기요금 조회 쿼리 (확장 가능한 구조)
        if month:
            query = f"""
            SELECT year, month, unitCost, metro, city, full_code
            FROM electricity 
            WHERE metro = '{metro}' 
            AND year = {year} 
            AND month = {month}
            AND unitCost IS NOT NULL
            AND unitCost > 0
            ORDER BY city;
            """
        else:
            # 최신 데이터 조회 (월별 최신 순)
            query = f"""
            SELECT year, month, unitCost, metro, city, full_code
            FROM electricity 
            WHERE metro = '{metro}' 
            AND year = {year}
            AND unitCost IS NOT NULL
            AND unitCost > 0
            ORDER BY year DESC, month DESC, city
            LIMIT 20;
            """
        
        result = execute_sql_query(query)
        
        if result['success'] and result['data']:
            electricity_data = result['data']
            
            # unitCost 컬럼명 정규화 (대소문자 처리)
            unit_costs = []
            for row in electricity_data:
                # 다양한 컬럼명 패턴 처리
                cost_value = row.get('unitcost') or row.get('unitCost') or row.get('UNITCOST')
                if cost_value and float(cost_value) > 0:
                    unit_costs.append(float(cost_value))
            
            if unit_costs:
                stats = {
                    "average_rate": round(statistics.mean(unit_costs), 2),
                    "min_rate": round(min(unit_costs), 2),
                    "max_rate": round(max(unit_costs), 2),
                    "median_rate": round(statistics.median(unit_costs), 2),
                    "data_points": len(unit_costs)
                }
            else:
                # 지역별 기본값 설정 (확장 가능)
                default_rates = {
                    "울산광역시": 88.0,
                    "부산광역시": 90.0,
                    "서울특별시": 95.0,
                    "경상남도": 85.0
                }
                default_rate = default_rates.get(metro, 90.0)
                
                stats = {
                    "average_rate": default_rate,
                    "min_rate": default_rate - 5.0,
                    "max_rate": default_rate + 5.0,
                    "median_rate": default_rate,
                    "data_points": 0
                }
            
            return {
                "success": True,
                "region": metro,
                "year": year,
                "month": month,
                "data_count": len(electricity_data),
                "statistics": stats,
                "detailed_data": electricity_data[:5],  # 상위 5개만 반환
                "recommended_rate": stats["average_rate"],  # 점수 계산용
                "query_info": {
                    "has_real_data": len(unit_costs) > 0,
                    "fallback_used": len(unit_costs) == 0
                }
            }
        else:
            # 데이터가 없는 경우 지역별 기본값 반환
            default_rates = {
                "울산광역시": 88.0,
                "부산광역시": 90.0, 
                "서울특별시": 95.0,
                "경상남도": 85.0
            }
            default_rate = default_rates.get(metro, 90.0)
            
            return {
                "success": True,
                "region": metro,
                "year": year,
                "month": month,
                "data_count": 0,
                "statistics": {
                    "average_rate": default_rate,
                    "min_rate": default_rate - 5.0,
                    "max_rate": default_rate + 5.0,
                    "median_rate": default_rate,
                    "data_points": 0
                },
                "detailed_data": [],
                "recommended_rate": default_rate,
                "query_info": {
                    "has_real_data": False,
                    "fallback_used": True,
                    "note": f"{metro} 지역 실제 데이터 없음 - 기본값 사용"
                }
            }
            
    except Exception as e:
        # 오류 시에도 기본값 제공
        default_rate = 88.0 if metro == "울산광역시" else 90.0
        return {
            "success": False,
            "error": f"전기요금 조회 중 오류: {str(e)}",
            "region": metro,
            "recommended_rate": default_rate,
            "query_info": {
                "has_real_data": False,
                "fallback_used": True,
                "error_fallback": True
            }
        }


@tool  
def get_ulsan_electricity_rate(year: int = 2024, month: Optional[int] = None) -> Dict[str, Any]:
    """
    울산 지역 전기요금 조회 (하위 호환성을 위한 래퍼 함수)
    
    Args:
        year: 조회할 연도 (기본값: 2024)
        month: 조회할 월 (None이면 최신 데이터)
        
    Returns:
        울산 지역 전기요금 정보
    """
    return get_electricity_rate_by_region("울산광역시", year, month)


@tool
def compare_electricity_rates_by_region(year: int = 2024) -> Dict[str, Any]:
    """
    지역별 전기요금 비교 분석
    
    Args:
        year: 비교할 연도
        
    Returns:
        지역별 전기요금 비교 결과
    """
    try:
        query = f"""
        SELECT 
            metro,
            AVG(unitCost) as avg_rate,
            MIN(unitCost) as min_rate,
            MAX(unitCost) as max_rate,
            COUNT(*) as data_count
        FROM electricity 
        WHERE year = {year}
        AND metro IS NOT NULL
        GROUP BY metro
        ORDER BY avg_rate ASC;
        """
        
        result = execute_sql_query(query)
        
        if result['success'] and result['data']:
            regional_data = []
            ulsan_rank = None
            
            for i, row in enumerate(result['data'], 1):
                region_info = {
                    "rank": i,
                    "region": row['metro'],
                    "average_rate": round(float(row['avg_rate']), 2),
                    "min_rate": round(float(row['min_rate']), 2),
                    "max_rate": round(float(row['max_rate']), 2),
                    "data_count": row['data_count']
                }
                regional_data.append(region_info)
                
                if row['metro'] == '울산광역시':
                    ulsan_rank = i
            
            return {
                "success": True,
                "year": year,
                "total_regions": len(regional_data),
                "ulsan_rank": ulsan_rank,
                "regional_comparison": regional_data,
                "ulsan_advantage": ulsan_rank <= len(regional_data) // 2 if ulsan_rank else False
            }
        else:
            return {
                "success": False,
                "error": "지역별 전기요금 데이터 없음"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"지역별 전기요금 비교 중 오류: {str(e)}"
        }


@tool
def get_electricity_trend_analysis(metro: str = "울산광역시", years: int = 3) -> Dict[str, Any]:
    """
    전기요금 추세 분석
    
    Args:
        metro: 분석할 지역 (기본값: 울산광역시)
        years: 분석할 연도 수 (기본값: 3년)
        
    Returns:
        전기요금 추세 분석 결과
    """
    try:
        current_year = 2024
        start_year = current_year - years + 1
        
        query = f"""
        SELECT 
            year,
            month,
            AVG(unitCost) as avg_monthly_rate,
            COUNT(*) as data_count
        FROM electricity 
        WHERE metro = '{metro}'
        AND year >= {start_year}
        AND year <= {current_year}
        GROUP BY year, month
        ORDER BY year, month;
        """
        
        result = execute_sql_query(query)
        
        if result['success'] and result['data']:
            trend_data = []
            rates = []
            
            for row in result['data']:
                monthly_data = {
                    "year": row['year'],
                    "month": row['month'],
                    "average_rate": round(float(row['avg_monthly_rate']), 2),
                    "data_count": row['data_count']
                }
                trend_data.append(monthly_data)
                rates.append(float(row['avg_monthly_rate']))
            
            # 추세 분석
            if len(rates) >= 2:
                trend = "상승" if rates[-1] > rates[0] else "하락" if rates[-1] < rates[0] else "안정"
                change_rate = ((rates[-1] - rates[0]) / rates[0]) * 100
            else:
                trend = "데이터 부족"
                change_rate = 0
            
            return {
                "success": True,
                "region": metro,
                "analysis_period": f"{start_year}-{current_year}",
                "data_points": len(trend_data),
                "trend_analysis": {
                    "trend": trend,
                    "change_rate": round(change_rate, 2),
                    "current_rate": rates[-1] if rates else 88.0,
                    "average_rate": round(statistics.mean(rates), 2) if rates else 88.0
                },
                "monthly_data": trend_data[-12:],  # 최근 12개월만 반환
                "recommendation": "안정적" if abs(change_rate) < 5 else "변동성 주의"
            }
        else:
            return {
                "success": False,
                "error": f"{metro} 지역 전기요금 추세 데이터 없음"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"전기요금 추세 분석 중 오류: {str(e)}"
        }


@tool
def calculate_manufacturing_electricity_cost(land_area: float, electricity_rate: float, 
                                           monthly_usage_per_sqm: float = 15.0) -> Dict[str, Any]:
    """
    제조업 전기비용 계산
    
    Args:
        land_area: 토지면적 (m²)
        electricity_rate: 전기요금 (원/kWh)
        monthly_usage_per_sqm: m²당 월간 전력 사용량 (kWh/m²)
        
    Returns:
        제조업 전기비용 계산 결과
    """
    try:
        # 제조업 전력 사용량 추정 (토지면적 기반)
        estimated_facility_area = land_area * 0.6  # 건폐율 60% 가정
        monthly_usage = estimated_facility_area * monthly_usage_per_sqm
        annual_usage = monthly_usage * 12
        
        # 비용 계산
        monthly_cost = monthly_usage * electricity_rate
        annual_cost = annual_usage * electricity_rate
        
        # 비용 등급 평가
        cost_per_sqm = annual_cost / land_area
        if cost_per_sqm < 100000:
            cost_grade = "A (저비용)"
        elif cost_per_sqm < 200000:
            cost_grade = "B (보통)"
        elif cost_per_sqm < 300000:
            cost_grade = "C (고비용)"
        else:
            cost_grade = "D (매우 고비용)"
        
        return {
            "success": True,
            "land_area": land_area,
            "electricity_rate": electricity_rate,
            "usage_estimation": {
                "facility_area": round(estimated_facility_area, 2),
                "monthly_usage_kwh": round(monthly_usage, 2),
                "annual_usage_kwh": round(annual_usage, 2)
            },
            "cost_calculation": {
                "monthly_cost": round(monthly_cost, 0),
                "annual_cost": round(annual_cost, 0),
                "cost_per_sqm": round(cost_per_sqm, 0)
            },
            "cost_grade": cost_grade,
            "competitiveness": "높음" if cost_per_sqm < 150000 else "보통" if cost_per_sqm < 250000 else "낮음"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"전기비용 계산 중 오류: {str(e)}"
        }


# 테스트 코드
if __name__ == "__main__":
    print("⚡ Electricity Tools 테스트")
    print("=" * 60)
    
    try:
        # 상대 import 문제 해결을 위한 동적 import
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        from src.tools.database_tools import execute_sql_query
        
        # 1. 울산 전기요금 조회 (개선된 함수)
        print("\n🔍 1. 울산 전기요금 조회 (개선된 함수)")
        ulsan_rate = get_electricity_rate_by_region("울산광역시", 2024)
        if ulsan_rate.get('success', False):
            print(f"   평균 요금: {ulsan_rate['statistics']['average_rate']}원/kWh")
            print(f"   데이터 수: {ulsan_rate['data_count']}개")
            print(f"   실제 DB 데이터: {ulsan_rate['query_info']['has_real_data']}")
        else:
            print(f"   오류: {ulsan_rate.get('error', '알 수 없는 오류')}")
            print(f"   기본값 사용: {ulsan_rate.get('recommended_rate', 88.0)}원/kWh")
        
        # 2. 하위 호환성 테스트
        print("\n🔄 2. 하위 호환성 테스트 (기존 함수)")
        legacy_rate = get_ulsan_electricity_rate(2024)
        print(f"   기존 함수 결과: {legacy_rate.get('recommended_rate', 88.0)}원/kWh")
        
        # 3. 제조업 전기비용 계산
        print("\n💰 3. 제조업 전기비용 계산 (15,000m² 토지)")
        cost_calc = calculate_manufacturing_electricity_cost(15000, 88.0)
        if cost_calc['success']:
            print(f"   연간 전기비용: {cost_calc['cost_calculation']['annual_cost']:,}원")
            print(f"   m²당 비용: {cost_calc['cost_calculation']['cost_per_sqm']:,}원")
            print(f"   비용 등급: {cost_calc['cost_grade']}")
        
        print("\n" + "=" * 60)
        print("✅ Electricity Tools 테스트 완료!")
        print("🚀 확장성 개선: 지역별 전기요금 조회 가능")
        print("🔧 DB 조회 실패 시 기본값 제공으로 안정성 향상")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {str(e)}")
        print("💡 모듈 단독 실행 시 import 경로 문제일 수 있습니다.")
        print("   전체 프로젝트 컨텍스트에서는 정상 작동합니다.")