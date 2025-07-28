# Tools 모듈 - 제조업 입지추천 플랫폼

이 디렉토리는 제조업 입지추천 플랫폼의 핵심 도구들을 포함합니다.

## 📁 파일 구조

### 🎯 scoring_tools.py
**제조업 입지 가중치 점수 계산 시스템**

#### 주요 기능
- **LocationScoring 클래스**: 가중치 점수 계산 엔진
- **정규화 방식**: weight_logic.doc 기반 5가지 타입
  - `above`: 클수록 유리 (토지면적)
  - `below`: 작을수록 유리 (공시지가, 전기요금)
  - `range`: 범위 내에서 클수록 유리
  - `match`: 일치/불일치 (용도지역)
  - `tolerance`: 기준값 근처일수록 유리 (인구밀도)

#### 핵심 함수들
```python
@tool
def calculate_location_score(land_data, weights) -> Dict[str, Any]
# 입지 데이터를 100점 만점으로 계산

@tool  
def get_default_weights() -> Dict[str, float]
# 제조업 특화 기본 가중치 (총 100%)
# - 토지가격: 25%, 전기요금: 20%, 용도지역: 15% 등

@tool
def validate_land_data(land_data) -> Dict[str, Any]
# 토지 데이터 유효성 검증
```

#### 제조업 특화 기준값
- **인구밀도**: 3,000명/km² (±700 허용편차)
- **울산 지역**: 제조업 최적화된 가중치 설정
- **100점 만점**: A+ (90점 이상) ~ C (50점 미만) 등급

---

### 🗄️ database_tools.py
**PostgreSQL 데이터베이스 연결 및 쿼리 도구**

#### 주요 기능
- **SSH 터널**: 보안 연결을 통한 RDS 접근
- **DatabaseConnection 클래스**: 연결 관리자
- **쿼리 실행**: SELECT 전용 (보안상 INSERT/UPDATE 제한)

#### 핵심 함수들
```python
@tool
def execute_sql_query(query: str) -> Dict[str, Any]
# SQL 쿼리 실행 (SELECT만 허용)

@tool
def get_database_schema() -> Dict[str, Any]
# 데이터베이스 스키마 정보 조회

@tool
def get_table_list() -> Dict[str, Any]
# 테이블 목록 조회

@tool
def get_table_sample(table_name: str, limit: int = 5) -> Dict[str, Any]
# 테이블 샘플 데이터 조회
```

#### 환경 변수 설정
```bash
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
BASTION_HOST=your_bastion_host
SSH_KEY_PATH=path/to/your/key.pem
```

---

### 🔧 mcp_tools.py
**기존 MCP 도구들** (워크샵에서 상속)
- `wikipedia_search`: 위키피디아 검색
- `duckduckgo_search`: 덕덕고 검색  
- `get_position`: 지리적 위치 조회
- `http_request`: HTTP 요청 (strands_tools에서 가져옴)

## 🚀 사용 예시

### 점수 계산 예시
```python
from src.tools.scoring_tools import calculate_location_score, get_default_weights

# 샘플 토지 데이터
land_data = {
    "land_area": 15000,        # m²
    "land_price": 180000,      # 원/m²
    "zone_type": "공업지역",
    "electricity_rate": 95,     # 원/kWh
    "substation_density": 3,    # 건/km²
    "population_density": 2800  # 명/km²
}

# 기본 가중치로 점수 계산
weights = get_default_weights()
result = calculate_location_score(land_data, weights)

print(f"최종 점수: {result['final_score']}점")
print(f"등급: {result['grade']}")
```

### 데이터베이스 쿼리 예시
```python
from src.tools.database_tools import execute_sql_query

# 토지 정보 조회
result = execute_sql_query("SELECT * FROM land_info LIMIT 5")
if result['success']:
    print(f"조회된 행 수: {result['row_count']}")
    for row in result['data']:
        print(row)
```

## 🎯 다음 단계
Phase 2에서는 이 도구들을 활용하여 전문 에이전트들을 개발할 예정입니다:
- Location Analysis Agent
- Cost Analysis Agent  
- Policy Analysis Agent
- Scoring Agent