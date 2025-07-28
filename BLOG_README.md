# 🎭 Strands Agents Workshop: AI 멀티 에이전트 시스템 구축하기

> Amazon Bedrock과 Strands Agents를 활용한 "Agents as Tools" 패턴 실습 프로젝트

## 🚀 프로젝트 소개

이 프로젝트는 **지능형 오케스트레이터**가 사용자 요청을 분석하고 적절한 **전문 에이전트**에게 작업을 위임하는 멀티 에이전트 시스템입니다. 실제 API와 연동되어 정보 검색, 날씨 조회, 자연스러운 대화가 가능한 완전한 AI 시스템을 구현했습니다.

### ✨ 핵심 특징

- **🧠 지능형 오케스트레이션**: LLM이 자동으로 요청을 분석하고 적절한 에이전트 선택
- **🔍 멀티모달 검색**: Wikipedia와 DuckDuckGo를 지능적으로 선택하여 검색
- **🌤️ 실시간 날씨**: 미국 지역 날씨 정보 제공
- **💬 자연스러운 대화**: 감정을 이해하는 대화 에이전트
- **📋 전략적 계획**: 복잡한 요청을 단계별로 분해하여 처리

## 🏗️ 시스템 아키텍처

```
사용자 입력
    ↓
🎭 Orchestrator Agent (오케스트레이터)
    ↓
📋 Planning Agent (항상 먼저 실행)
    ↓
전문 에이전트들 (계획에 따라 순차 실행)
├── 🔍 Search Agent (Wikipedia + DuckDuckGo)
├── 🌤️ Weather Agent (미국 날씨)
└── 💬 Conversation Agent (일반 대화)
    ↓
최종 응답 통합 및 전달
```

## 🛠️ 기술 스택

### AI/ML 프레임워크
- **Strands Agents**: 멀티 에이전트 시스템 구축 프레임워크
- **Amazon Bedrock**: Claude 3 Haiku 모델 활용
- **MCP (Model Context Protocol)**: 도구 통합 프로토콜

### 외부 API 연동
- **Wikipedia API**: 백과사전 정보 검색
- **DuckDuckGo API**: 웹 검색 및 정의
- **National Weather Service**: 미국 날씨 정보
- **OpenStreetMap Nominatim**: 지오코딩 서비스

### Python 라이브러리
```python
strands-agents          # 에이전트 프레임워크
strands-agents-tools    # 추가 도구들
httpx                   # 비동기 HTTP 클라이언트
wikipedia              # Wikipedia API
pydantic               # 데이터 검증
python-dotenv          # 환경변수 관리
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd strands-agents-workshop

# 환경변수 설정
cp .env.example .env
# .env 파일에 AWS 자격증명 추가
```

### 2. 자동 실행 (권장)

```bash
# 가상환경 생성, 패키지 설치, 앱 실행을 한 번에
chmod +x run.sh
./run.sh
```

### 3. 수동 설정

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 애플리케이션 실행
python3 main.py
```

## 💡 사용 예시

### 단일 요청
```
💬 입력: "인공지능에 대해 알려줘"
🤖 응답: [Search Agent가 Wikipedia에서 정보 검색 후 상세 설명 제공]
```

### 복합 요청
```
💬 입력: "뉴욕에 대해 알려주고 날씨도 확인해줘"
🤖 처리 과정:
1. Planning Agent: 실행 계획 수립
2. Search Agent: 뉴욕 정보 검색
3. Weather Agent: 뉴욕 날씨 조회
4. 결과 통합하여 응답
```

### 일반 대화
```
💬 입력: "안녕하세요! 좋은 하루예요"
🤖 응답: [Conversation Agent가 친근하고 따뜻한 톤으로 응답]
```

## 🧪 테스트 및 검증

### 개별 컴포넌트 테스트
```bash
# MCP 도구 테스트
python3 mcp_tools.py

# 서브 에이전트 테스트
python3 sub_agents.py

# 오케스트레이터 테스트
python3 orchestrator_agent.py
```

### 통합 시스템 테스트
```bash
# 전체 시스템 기능 검증
python3 workshop_test.py
```

## 📁 프로젝트 구조

```
strands-agents-workshop/
├── 🎯 main.py                    # 대화형 애플리케이션
├── 🎭 orchestrator_agent.py      # 메인 오케스트레이터
├── 🤖 sub_agents.py              # 4개 전문 에이전트
├── 🔧 mcp_tools.py               # MCP 도구 구현
├── ⚙️ model_config.py            # Bedrock 모델 설정
├── 🧪 workshop_test.py           # 통합 테스트
├── 🚀 run.sh                     # 자동 실행 스크립트
├── 📋 requirements.txt           # 의존성 목록
└── 📚 templates/                 # 참조 구현체
    ├── lab2-mcp_tools.py
    ├── lab3-sub_agents.py
    ├── lab4-orchestrator_agent.py
    └── lab5-main.py
```

## 🎓 학습 워크샵 과정

이 프로젝트는 5단계 워크샵으로 구성되어 있습니다:

1. **Lab 1**: 환경 설정 및 AWS 연동
2. **Lab 2**: MCP 도구 구현 (`mcp_tools.py`)
3. **Lab 3**: 전문 에이전트 구현 (`sub_agents.py`)
4. **Lab 4**: 오케스트레이터 구현 (`orchestrator_agent.py`)
5. **Lab 5**: 메인 애플리케이션 통합 (`main.py`)

각 단계별 완성된 코드는 `templates/` 폴더에서 참조할 수 있습니다.

## 🔧 환경변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```bash
# AWS 설정
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Bedrock 모델 설정 (선택사항)
MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

## 🎯 핵심 구현 패턴

### 에이전트 정의 패턴
```python
@tool
def search_agent(query: str) -> str:
    """정보 검색 전문 에이전트"""
    agent = Agent(
        model=get_configured_model(),
        system_prompt=SEARCH_AGENT_PROMPT,
        tools=[wikipedia_search, duckduckgo_search]
    )
    return str(agent(f"검색 요청: {query}"))
```

### 도구 정의 패턴
```python
@tool
def wikipedia_search(query: str) -> Dict[str, Any]:
    """Wikipedia 검색 도구"""
    try:
        # 구현 로직
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## 🚨 문제 해결

### 일반적인 문제들

**1. 모델 접근 오류**
- AWS 자격증명 확인
- Bedrock 서비스 권한 검증
- 리전 설정 확인

**2. 패키지 설치 오류**
- Python 3.10+ 버전 확인
- 가상환경 활성화 상태 확인
- 네트워크 연결 상태 확인

**3. API 호출 오류**
- 인터넷 연결 확인
- API 제한 확인
- 타임아웃 설정 확인

## 🎉 실제 동작 예시

```bash
🤖 Agents as Tools Multi-Agent Demo
============================================================
사용자 ID: workshop_user

사용 가능한 Agent:
• Planning Agent - 실행 계획 수립 
• Search Agent - 지능적 검색 (Wikipedia + DuckDuckGo)
• Weather Agent - 날씨 정보 (미국 지역)
• Conversation Agent - 일반 대화
• Orchestrator Agent - 오케스트레이터 (Sub Agent 관리)

🔄 처리 흐름:
1. 명확성 판단 → 2. 계획 수립 → 3. 계획 실행
============================================================

💬 입력: 파리에 대해 알려주고 시애틀 날씨도 확인해줘

🎭 ORCHESTRATOR AGENT 처리 중...
==================================================

📋 PLANNING AGENT EXECUTION PLAN
====================================
**📋 Execution Plan:**
1. search_agent - 파리(Paris)에 대한 정보 검색
2. weather_agent - 시애틀 날씨 정보 조회

**🎯 Expected Result:**
파리의 기본 정보와 시애틀의 현재 날씨 정보를 함께 제공

**⚠️ Important Notes:**
weather_agent는 미국 지역만 지원하므로 시애틀 날씨 조회 가능
====================================

✅ planning_agent completed → Next: search_agent

[Search Agent가 Wikipedia에서 파리 정보 검색...]
✅ search_agent completed → Next: weather_agent

[Weather Agent가 시애틀 날씨 정보 조회...]
✅ weather_agent completed → Next: none

🎯==========================================================🎯
🤖 최종 응답
[파리에 대한 상세 정보와 시애틀 날씨 정보가 통합된 응답]
🎯==========================================================🎯
```

## 🌟 확장 가능성

이 프로젝트는 다음과 같이 확장할 수 있습니다:

- **새로운 에이전트 추가**: 번역, 이미지 생성, 코드 분석 등
- **추가 API 연동**: 뉴스, 주식, 소셜미디어 등
- **웹 인터페이스**: Streamlit, FastAPI 등으로 웹 서비스화
- **데이터베이스 연동**: 대화 기록, 사용자 선호도 저장
- **멀티모달 지원**: 이미지, 음성 입력 처리

## 📚 학습 목표

이 프로젝트를 통해 다음을 학습할 수 있습니다:

- **Agents as Tools 패턴**: AI 기반 동적 도구 선택
- **계층적 에이전트 구조**: 오케스트레이터와 서브 에이전트
- **지능형 오케스트레이션**: 요청 분석 및 실행 계획
- **실용적 적용**: 프로덕션 환경에서 적용 가능한 아키텍처
- **API 통합**: 외부 서비스와의 효과적인 연동 방법

## 🤝 기여하기

이 프로젝트는 교육 목적으로 만들어졌습니다. 개선사항이나 새로운 아이디어가 있다면 언제든 기여해주세요!

---

**Happy Coding! 🚀**

*이 프로젝트는 AI 멀티 에이전트 시스템의 실제 구현 방법을 학습하기 위한 완성도 높은 교육용 프로젝트입니다.*