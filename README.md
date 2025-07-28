# 제조업 입지추천 플랫폼 🏭

울산 지역 제조업 기업 확장을 위한 AI 기반 입지추천 시스템

## 🎯 프로젝트 개요

- **목표**: 울산 지역 제조업 기업 확장을 위한 AI 기반 입지추천 시스템
- **핵심 기능**: 토지 가격, 토지 분류, 전기세 기반 100점 만점 가중치 점수 계산
- **사용자**: 기업 확장팀
- **데이터 소스**: 공공데이터 API, RDS 데이터베이스

## 🏗️ 시스템 아키텍처

```
사용자 입력 → Orchestrator Agent → Planning Agent → 전문 Sub-Agents → 최종 응답
```

### 전문 Sub-Agents (Phase 2 개발 예정)
1. **Location Analysis Agent**: 토지 분석
2. **Cost Analysis Agent**: 비용 분석  
3. **Policy Analysis Agent**: 정책 분석
4. **Scoring Agent**: 가중치 점수 계산

## 📊 Phase 1 완료 사항 (25% 진행률)

### ✅ 1. 가중치 점수 계산 시스템
**파일**: `src/tools/scoring_tools.py`
- weight_logic.doc 기반 100점 만점 점수 계산
- 5가지 정규화 방식 (above, below, range, match, tolerance)
- 제조업 특화 울산 지역 기준값 설정

### ✅ 2. 데이터베이스 연결 시스템  
**파일**: `src/tools/database_tools.py`
- SSH 터널을 통한 보안 PostgreSQL 연결
- database_agent로 스키마 조회 및 쿼리 실행

### ✅ 3. 울산 제조업 특화 공공데이터 API
**파일**: `public_api_integration.py`
- 5개 API 통합: 정책, 공시지가, 전기요금, 인프라, 재난통계

### ✅ 4. 템플릿 및 데모 시스템
**파일**: `templates/phase1-scoring_system.py`
- Phase 1 기능 통합 데모 및 테스트

## 🚀 빠른 시작

### 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일)
cp .env.example .env
# DB 연결 정보 및 API 키 설정
```

### Phase 1 데모 실행
```bash
# 가중치 점수 계산 시스템 데모
python templates/phase1-scoring_system.py

# 메인 애플리케이션 (데이터베이스 연동)
python main.py
# 입력: "토지데이터 스키마와 샘플 하나를 가져와줘"
```

## 📋 가중치 점수 계산 예시

### 기본 가중치 (제조업 특화)
```python
{
    "land_price": 25.0,        # 공시지가 (가장 중요)
    "electricity_rate": 20.0,  # 전기요금
    "zone_type": 15.0,         # 용도지역
    "land_area": 10.0,         # 토지면적
    "substation_density": 8.0, # 변전소 밀도
    "transmission_density": 7.0, # 송전탑 밀도
    "population_density": 5.0,   # 인구밀도
    "disaster_count": 5.0,       # 재난 발생 빈도
    "policy_support": 5.0        # 정책 지원
}
```

### 샘플 계산 결과
```
🎯 최종 점수: 78.5점 (B+ 양호)

📋 세부 점수 분석:
   land_price: 0.825 × 25% = 0.206
   electricity_rate: 0.750 × 20% = 0.150
   zone_type: 1.000 × 15% = 0.150
   ...
```

## 🗂️ 프로젝트 구조

```
├── src/
│   ├── agents/           # 에이전트 구현
│   │   ├── orchestrator_agent.py
│   │   └── sub_agents.py
│   ├── tools/            # 핵심 도구들
│   │   ├── scoring_tools.py      # ✅ 가중치 계산
│   │   ├── database_tools.py     # ✅ DB 연결
│   │   └── mcp_tools.py         # MCP 도구들
│   └── config/           # 설정 파일들
├── templates/            # 단계별 템플릿
│   └── phase1-scoring_system.py  # ✅ Phase 1 데모
├── public_api_integration.py     # ✅ 울산 특화 API
├── main.py              # 메인 애플리케이션
└── README.md           # 이 파일
```

## 📈 개발 로드맵

### ✅ Phase 1: 기반 구조 설정 (완료)
- [x] 프로젝트 구조 분석
- [x] 데이터베이스 연결 에이전트 구현
- [x] 공공데이터 API 통합 확장
- [x] 가중치 계산 로직 구현

### ⏳ Phase 2: 전문 에이전트 개발 (다음 단계)
- [ ] Location Analysis Agent (토지 분석)
- [ ] Cost Analysis Agent (비용 분석)
- [ ] Policy Analysis Agent (정책 분석)
- [ ] Scoring Agent (가중치 점수 계산)

### ⏳ Phase 3: 오케스트레이터 통합
- [ ] Manufacturing Location Orchestrator 구현
- [ ] 에이전트 간 데이터 흐름 최적화
- [ ] 토큰 사용량 최적화

### ⏳ Phase 4: 사용자 인터페이스
- [ ] 입지 추천 메인 애플리케이션
- [ ] 결과 시각화 및 리포트 생성
- [ ] 테스트 및 검증

## 🔧 기술 스택

- **Framework**: Strands Agents
- **LLM**: Amazon Bedrock (Claude)
- **Database**: PostgreSQL (RDS)
- **APIs**: 울산 특화 공공데이터 5개
- **Language**: Python 3.8+

## 📊 성공 지표

- 입지 점수 정확도 90% 이상
- API 응답 시간 5초 이내  
- 토큰 사용량 요청당 1000토큰 이하

## 🤝 기여 방법

1. 이슈 생성 또는 기존 이슈 확인
2. 브랜치 생성 (`git checkout -b feature/새기능`)
3. 변경사항 커밋 (`git commit -am '새기능 추가'`)
4. 브랜치 푸시 (`git push origin feature/새기능`)
5. Pull Request 생성

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**현재 진행률**: 25% (Phase 1 완료) | **다음 단계**: Phase 2 전문 에이전트 개발