# 베드락 Agent를 모델로 쓰기

AWS Bedrock에서 Agent를 모델처럼 호출하는 방법에 대한 가이드입니다.

## 1. Bedrock Agents Runtime API 사용

```python
import boto3
from typing import Dict, Any

def call_bedrock_agent(agent_id: str, agent_alias_id: str, session_id: str, input_text: str, region: str = "ap-northeast-2") -> Dict[str, Any]:
    """
    Bedrock Agent를 호출하는 함수
    
    Args:
        agent_id: Bedrock Agent ID
        agent_alias_id: Agent Alias ID (보통 "TSTALIASID" 또는 "DRAFT")
        session_id: 세션 ID (고유한 문자열)
        input_text: 사용자 입력
        region: AWS 리전
    
    Returns:
        Agent 응답
    """
    client = boto3.client('bedrock-agent-runtime', region_name=region)
    
    try:
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=input_text
        )
        
        # 스트리밍 응답 처리
        result = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result += chunk['bytes'].decode('utf-8')
        
        return {
            "success": True,
            "response": result,
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## 2. BedrockAgentWrapper 클래스

`model_config.py`에 추가된 래퍼 클래스:

```python
class BedrockAgentWrapper:
    """
    Bedrock Agent를 모델처럼 사용할 수 있게 해주는 래퍼 클래스
    """
    
    def __init__(self, agent_id: str, agent_alias_id: str = "TSTALIASID", region: str = "ap-northeast-2"):
        """
        Initialize Bedrock Agent Wrapper
        
        Args:
            agent_id: Bedrock Agent ID
            agent_alias_id: Agent Alias ID (기본값: "TSTALIASID")
            region: AWS 리전
        """
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id
        self.region = region
        self.client = boto3.client('bedrock-agent-runtime', region_name=region)
        self.session_id = str(uuid.uuid4())
    
    def invoke(self, input_text: str) -> str:
        """
        Agent를 호출하고 응답을 반환
        
        Args:
            input_text: 사용자 입력
            
        Returns:
            Agent 응답 텍스트
        """
        try:
            response = self.client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=self.session_id,
                inputText=input_text
            )
            
            # 스트리밍 응답 처리
            result = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result += chunk['bytes'].decode('utf-8')
            
            return result
            
        except Exception as e:
            return f"Agent 호출 오류: {str(e)}"
    
    def generate(self, messages, **kwargs):
        """
        Strands 프레임워크와 호환성을 위한 메서드
        """
        if isinstance(messages, list) and len(messages) > 0:
            # 마지막 메시지의 내용을 추출
            last_message = messages[-1]
            if isinstance(last_message, dict) and 'content' in last_message:
                input_text = last_message['content']
            else:
                input_text = str(last_message)
        else:
            input_text = str(messages)
        
        return self.invoke(input_text)
```

## 3. 사용 방법

### 기본 Bedrock 모델 사용 (기존 방식)
```python
from model_config import get_configured_model

# 일반 Bedrock 모델 사용
model = get_configured_model()
response = model.generate("안녕하세요!")
```

### Bedrock Agent를 모델처럼 사용 (새로운 방식)
```python
from model_config import get_bedrock_agent

# Bedrock Agent를 모델처럼 사용
agent_model = get_bedrock_agent(
    agent_id="YOUR_AGENT_ID",
    agent_alias_id="TSTALIASID",  # 또는 "DRAFT"
    region="ap-northeast-2"
)

# 일반 모델처럼 호출
response = agent_model.invoke("서울 날씨 알려줘")

# 또는 Strands 프레임워크와 호환되는 방식
response = agent_model.generate([{"content": "서울 날씨 알려줘"}])
```

### 환경 변수로 Agent ID 설정
```bash
export BEDROCK_AGENT_ID="your-agent-id"
export BEDROCK_AGENT_ALIAS="TSTALIASID"
```

## 4. 실제 사용 예시

`sub_agents.py`에서 사용하는 방법:

```python
from model_config import get_bedrock_agent
import os

# 환경 변수에서 Agent ID 가져오기
agent_id = os.getenv("BEDROCK_AGENT_ID")

if agent_id:
    # Bedrock Agent 사용
    agent_model = get_bedrock_agent(agent_id)
    response = agent_model.invoke("검색 요청")
else:
    # 일반 모델 사용
    model = get_configured_model()
    response = model.generate("검색 요청")
```

## 5. 주요 특징

1. **호환성**: Strands 프레임워크와 완벽 호환
2. **세션 관리**: 자동으로 고유한 세션 ID 생성
3. **오류 처리**: Agent 호출 실패 시 적절한 오류 메시지 반환
4. **스트리밍 지원**: Bedrock Agent의 스트리밍 응답 처리
5. **리전 설정**: Seoul 리전(`ap-northeast-2`) 기본 지원

## 6. 헬퍼 함수

```python
def get_bedrock_agent(agent_id: str, agent_alias_id: str = "TSTALIASID", region: str = None) -> BedrockAgentWrapper:
    """
    Bedrock Agent 래퍼 인스턴스를 생성
    
    Args:
        agent_id: Bedrock Agent ID
        agent_alias_id: Agent Alias ID
        region: AWS 리전 (기본값: ap-northeast-2)
        
    Returns:
        BedrockAgentWrapper 인스턴스
    """
    region = region or os.getenv("AWS_REGION", "ap-northeast-2")
    return BedrockAgentWrapper(agent_id, agent_alias_id, region)
```

## 7. 장점

- **통합성**: 기존 모델과 동일한 인터페이스로 사용 가능
- **유연성**: Agent ID만 변경하면 다른 Agent로 쉽게 전환
- **확장성**: 여러 Agent를 동시에 사용 가능
- **호환성**: 기존 Strands 코드 수정 없이 사용 가능

이제 Bedrock Agent를 일반 모델처럼 사용할 수 있습니다! 🎉