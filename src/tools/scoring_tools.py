"""Scoring Tools - 제조업 입지 가중치 점수 계산"""
from typing import Dict, Any, Optional
from strands import tool
import math


class LocationScoring:
    """제조업 입지 가중치 점수 계산 클래스"""
    
    def __init__(self):
        self.base_score = 0.5  # 기본 점수
        
        # 제조업 기준값 (울산 지역 특화)
        self.manufacturing_standards = {
            "population_density": {
                "mean": 3000,  # 명/km²
                "tolerance": 700  # 허용편차
            }
        }
    
    def normalize_score(self, value: float, min_val: float, max_val: float, 
                       reference: Optional[float] = None, 
                       score_type: str = "range") -> float:
        """
        점수 정규화 함수 (0~1 범위)
        
        Args:
            value: 실제 값
            min_val: 최소값
            max_val: 최대값  
            reference: 기준값 (필요시)
            score_type: 정규화 방식 ("above", "below", "range", "match", "tolerance")
            
        Returns:
            정규화된 점수 (0~1)
        """
        bs = self.base_score
        
        try:
            if score_type == "above":
                # ① 이상: 클수록 유리 (토지면적)
                if value >= reference:
                    return bs + (value - reference) / (max_val - reference) * (1 - bs)
                else:
                    return bs + (1 - abs(value - reference) / (reference - min_val)) * (1 - bs)
                    
            elif score_type == "below":
                # ② 이하: 작을수록 유리 (공시지가, 전기요금)
                if value <= reference:
                    return bs + ((reference - value) / (reference - min_val)) * (1 - bs)
                else:
                    return bs + ((max_val - value) / (max_val - reference)) * (1 - bs)
                    
            elif score_type == "range":
                # ③ 범위: 범위 내에서 클수록 유리
                return bs + (value - min_val) / (max_val - min_val) * (1 - bs)
                
            elif score_type == "match":
                # 일치하면 1, 불일치하면 0 (용도지역)
                return 1.0 if value == reference else 0.0
                
            elif score_type == "tolerance":
                # 기준값 근처일수록 유리 (인구밀도)
                if reference is None:
                    raise ValueError("tolerance 방식은 reference 값이 필요합니다")
                tolerance = self.manufacturing_standards["population_density"]["tolerance"]
                return max(0, 1 - abs(value - reference) / tolerance)
                
            elif score_type == "reverse_range":
                # 범위에서 작을수록 유리 (재난문자)
                return bs + (max_val - value) / (max_val - min_val) * (1 - bs)
                
            else:
                raise ValueError(f"지원하지 않는 score_type: {score_type}")
                
        except (ZeroDivisionError, TypeError):
            return bs  # 오류 시 기본 점수 반환


@tool
def calculate_location_score(land_data: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
    """
    입지 데이터를 기반으로 가중치 점수를 계산
    
    Args:
        land_data: 토지 데이터 딕셔너리
        weights: 각 지표별 가중치 (0~100%)
        
    Returns:
        계산된 점수 및 세부 정보
    """
    try:
        scorer = LocationScoring()
        detailed_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        
        # 필수 지표들의 기준값 설정 (울산 지역 제조업 기준)
        standards = {
            "land_area": {"min": 1000, "max": 50000, "reference": 10000, "type": "above"},
            "land_price": {"min": 50000, "max": 500000, "reference": 200000, "type": "below"},
            "zone_type": {"reference": "공업지역", "type": "match"},
            "electricity_rate": {"min": 80, "max": 150, "reference": 100, "type": "below"},
            "substation_density": {"min": 0, "max": 10, "type": "range"},
            "transmission_density": {"min": 0, "max": 5, "type": "range"},
            "population_density": {"reference": 3000, "type": "tolerance"},
            "disaster_count": {"min": 0, "max": 20, "type": "reverse_range"},
            "policy_support": {"min": 0, "max": 10, "type": "range"}
        }
        
        # 실제 데이터베이스 필드명 매핑
        field_mapping = {
            "land_area": "land_area",                    # land 테이블 직접 매핑
            "land_price": "official_land_price",         # land 테이블 공시지가
            "zone_type": "use_district_name1",           # land 테이블 용도지역
            "land_use": "land_use_name",                 # land 테이블 토지이용
            "terrain_height": "terrain_height_name",     # land 테이블 지형고저
            "terrain_shape": "terrain_shape_name",       # land 테이블 지형형상
            "road_access": "road_side_name",             # land 테이블 도로접면
            "electricity_rate": "unitCost"               # electricity 테이블 전기요금
        }
        
        # 각 지표별 점수 계산
        for indicator, weight in weights.items():
            # 실제 DB 필드명으로 변환
            db_field = field_mapping.get(indicator, indicator)
            if db_field in land_data and indicator in standards:
                value = land_data[indicator]
                standard = standards[indicator]
                
                # 정규화 점수 계산
                normalized_score = scorer.normalize_score(
                    value=value,
                    min_val=standard.get("min", 0),
                    max_val=standard.get("max", 100),
                    reference=standard.get("reference"),
                    score_type=standard["type"]
                )
                
                # 가중치 적용
                weighted_score = normalized_score * (weight / 100)
                
                detailed_scores[indicator] = {
                    "raw_value": value,
                    "normalized_score": round(normalized_score, 3),
                    "weight": weight,
                    "weighted_score": round(weighted_score, 3)
                }
                
                total_weighted_score += weighted_score
                total_weight += weight / 100
        
        # 최종 점수 계산 (100점 만점)
        if total_weight > 0:
            final_score = (total_weighted_score / total_weight) * 100
        else:
            final_score = 50.0  # 기본 점수
            
        return {
            "success": True,
            "final_score": round(final_score, 2),
            "grade": _get_score_grade(final_score),
            "detailed_scores": detailed_scores,
            "total_indicators": len(detailed_scores),
            "calculation_method": "정규화 방식 (0~1) × 가중치 × 100점"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"점수 계산 중 오류: {str(e)}",
            "final_score": 0
        }


def _get_score_grade(score: float) -> str:
    """점수에 따른 등급 반환"""
    if score >= 90:
        return "A+ (최우수)"
    elif score >= 80:
        return "A (우수)"
    elif score >= 70:
        return "B+ (양호)"
    elif score >= 60:
        return "B (보통)"
    elif score >= 50:
        return "C+ (미흡)"
    else:
        return "C (부적합)"


@tool
def get_default_weights() -> Dict[str, float]:
    """
    제조업 입지 평가를 위한 기본 가중치 반환
    
    Returns:
        기본 가중치 딕셔너리 (총합 100%)
    """
    return {
        # 핵심 지표 (70%)
        "land_price": 25.0,        # 공시지가 (가장 중요)
        "electricity_rate": 20.0,  # 전기요금
        "zone_type": 15.0,         # 용도지역
        "land_area": 10.0,         # 토지면적
        
        # 인프라 지표 (20%)
        "substation_density": 8.0,     # 변전소 밀도
        "transmission_density": 7.0,   # 송전탑 밀도
        "population_density": 5.0,     # 인구밀도
        
        # 안정성/정책 지표 (10%)
        "disaster_count": 5.0,         # 재난 발생 빈도
        "policy_support": 5.0          # 정책 지원
    }


@tool
def validate_land_data(land_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    토지 데이터 유효성 검증
    
    Args:
        land_data: 검증할 토지 데이터
        
    Returns:
        검증 결과
    """
    required_fields = [
        "land_price", "electricity_rate", "zone_type", 
        "land_area", "substation_density", "transmission_density"
    ]
    
    missing_fields = []
    invalid_fields = []
    
    for field in required_fields:
        if field not in land_data:
            missing_fields.append(field)
        elif field != "zone_type" and not isinstance(land_data[field], (int, float)):
            invalid_fields.append(field)
    
    is_valid = len(missing_fields) == 0 and len(invalid_fields) == 0
    
    return {
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "total_fields": len(land_data),
        "required_fields": len(required_fields)
    }


# 테스트 코드
if __name__ == "__main__":
    print("🧪 Scoring Tools 테스트")
    print("=" * 50)
    
    # 샘플 토지 데이터
    sample_data = {
        "land_area": 15000,        # m²
        "land_price": 180000,      # 원/m²
        "zone_type": "공업지역",
        "electricity_rate": 95,     # 원/kWh
        "substation_density": 3,    # 건/km²
        "transmission_density": 2,  # 건/km²
        "population_density": 2800, # 명/km²
        "disaster_count": 2,        # 건/년
        "policy_support": 6         # 건
    }
    
    # 기본 가중치 가져오기
    weights = get_default_weights()
    print(f"📊 기본 가중치: {weights}")
    
    # 데이터 검증
    validation = validate_land_data(sample_data)
    print(f"✅ 데이터 검증: {validation['is_valid']}")
    
    # 점수 계산
    result = calculate_location_score(sample_data, weights)
    print(f"🎯 최종 점수: {result['final_score']}점 ({result['grade']})")
    
    if result['success']:
        print("\n📋 세부 점수:")
        for indicator, details in result['detailed_scores'].items():
            print(f"  {indicator}: {details['normalized_score']} × {details['weight']}% = {details['weighted_score']}")
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!")