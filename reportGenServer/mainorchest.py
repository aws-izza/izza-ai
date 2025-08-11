from strands import Agent, tool
from config import get_configured_model, get_agent_prompt
from knowledge_agent_tool_origin import knowledge_agent
from policy_agent import policy_agent
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, Any

load_dotenv()

@tool
def land_knowledge_analysis(land_data: str) -> str:
    """
    토지 데이터를 분석하여 전문적인 지식 기반 분석을 수행합니다.
    
    Args:
        land_data: 토지 정보 데이터 (주소, 지목, 용도지역 등)
        
    Returns:
        토지에 대한 전문적인 분석 결과
    """
    query = f"""
    다음 토지 정보에 대해 상세한 분석을 해주세요:
    {land_data}
    
    다음 항목들을 포함하여 분석해주세요:
    1. 지목과 용도지역의 특성 및 의미
    2. 토지 이용 현황 분석
    3. 지형 및 형상의 장단점
    4. 도로 접면 상황 평가
    5. 공시지가 수준 분석
    6. 개발 가능성 및 제약사항
    7. 투자 가치 평가
    """
    
    return knowledge_agent(query)

@tool
def policy_search_analysis(land_data: str) -> str:
    """
    토지 위치와 특성에 맞는 정부 지원 정책을 검색하고 분석합니다.
    
    Args:
        land_data: 토지 정보 데이터
        
    Returns:
        관련 정부 지원 정책 정보
    """
    # 주소에서 지역 정보 추출
    address = ""
    for line in land_data.split('\n'):
        if '주소' in line:
            address = line.split(':')[1].strip().replace("'", "")
            break
    
    # 지역명 추출 (시/도 단위)
    region = ""
    if "서울" in address:
        region = "서울"
    elif "부산" in address:
        region = "부산"
    elif "대구" in address:
        region = "대구"
    elif "인천" in address:
        region = "인천"
    elif "광주" in address:
        region = "광주"
    elif "대전" in address:
        region = "대전"
    elif "울산" in address:
        region = "울산"
    elif "세종" in address:
        region = "세종"
    elif "경기" in address:
        region = "경기"
    elif "강원" in address:
        region = "강원"
    elif "충북" in address or "충청북도" in address:
        region = "충북"
    elif "충남" in address or "충청남도" in address:
        region = "충남"
    elif "전북" in address or "전라북도" in address:
        region = "전북"
    elif "전남" in address or "전라남도" in address:
        region = "전남"
    elif "경북" in address or "경상북도" in address:
        region = "경북"
    elif "경남" in address or "경상남도" in address:
        region = "경남"
    elif "제주" in address:
        region = "제주"
    
    query = f"""
    다음 토지 정보와 관련된 정부 지원 정책을 찾아주세요:
    위치: {address}
    토지 데이터: {land_data}
    
    특히 다음과 같은 정책들을 우선적으로 검색해주세요:
    - {region} 지역의 부동산 개발 지원 정책
    - 상업지역 관련 창업 지원 정책
    - 토지 활용 관련 금융 지원 정책
    - 지역 개발 관련 기술 지원 정책
    """
    
    return policy_agent(query)

def parse_policy_response(policy_response: str) -> str:
    """
    정책 에이전트 응답을 파싱하여 구조화된 형식으로 변환합니다.
    """
    try:
        # JSON 부분 찾기
        json_start = policy_response.find('{"projects":')
        if json_start == -1:
            json_start = policy_response.find('{{')
        
        if json_start != -1:
            # JSON 끝 찾기
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(policy_response[json_start:], json_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if json_end > json_start:
                json_str = policy_response[json_start:json_end]
                # 이중 중괄호 처리
                json_str = json_str.replace('{{', '{').replace('}}', '}')
                
                try:
                    policy_data = json.loads(json_str)
                    projects = policy_data.get("projects", [])
                    
                    if projects:
                        formatted_content = "### 관련 정부 지원 정책\n\n"
                        
                        for i, project in enumerate(projects[:5], 1):
                            formatted_content += f"#### {i}. 지원정책\n\n"
                            formatted_content += f"- **지원정책 이름**: {project.get('projectName', 'N/A')}\n"
                            formatted_content += f"- **주관**: {project.get('organization', 'N/A')}\n"
                            formatted_content += f"- **기간**: {project.get('applicationPeriod', 'N/A')}\n"
                            formatted_content += f"- **요약**: {project.get('summary', 'N/A')}\n"
                            formatted_content += f"- **링크**: {project.get('detailsUrl', 'N/A')}\n\n"
                        
                        return formatted_content
                    
                except json.JSONDecodeError:
                    pass
        
        # JSON 파싱 실패 시 텍스트에서 유용한 정보 추출
        lines = policy_response.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # 불필요한 라인 제거
            if (line and 
                not line.startswith('Tool #') and 
                not line.startswith('---') and 
                'Response [200]' not in line and 
                not line.startswith('{') and 
                not line.startswith('}')):
                clean_lines.append(line)
        
        if clean_lines:
            return "### 관련 정부 지원 정책\n\n" + '\n'.join(clean_lines)
        else:
            return "### 관련 정부 지원 정책\n\n해당 지역과 관련된 정부 지원 정책 정보를 찾지 못했습니다."
            
    except Exception as e:
        return f"### 관련 정부 지원 정책\n\n정책 정보 처리 중 오류가 발생했습니다: {str(e)}"

def create_korean_land_report(land_data: Dict[str, Any], knowledge_analysis: str, policy_analysis: str) -> str:
    """
    토지 분석 결과를 종합하여 한국어 보고서를 생성합니다.
    """
    current_date = datetime.now().strftime("%Y년 %m월 %d일")
    
    # 공시지가 포맷팅 처리
    gongsi_price = land_data.get('공시지가', 0)
    if isinstance(gongsi_price, (int, float)):
        gongsi_display = f"{gongsi_price:,}원"
    else:
        gongsi_display = str(gongsi_price)
    
    # 정책 분석에서 JSON 부분 추출 및 정리
    policy_content = ""
    
    if "projects" in policy_analysis and "{" in policy_analysis:
        try:
            # JSON 부분 추출
            json_start = policy_analysis.find("{")
            json_end = policy_analysis.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                json_str = policy_analysis[json_start:json_end]
                policy_data = json.loads(json_str)
                
                # 정책 정보를 요청된 형식으로 포맷팅
                projects = policy_data.get("projects", [])
                if projects:
                    policy_content = "### 관련 정부 지원 정책\n\n"
                    
                    for i, project in enumerate(projects[:5], 1):  # 상위 5개만 표시
                        policy_content += f"#### {i}. 지원정책\n\n"
                        policy_content += f"- **지원정책 이름**: {project.get('projectName', 'N/A')}\n"
                        policy_content += f"- **주관**: {project.get('organization', 'N/A')}\n"
                        policy_content += f"- **기간**: {project.get('applicationPeriod', 'N/A')}\n"
                        policy_content += f"- **요약**: {project.get('summary', 'N/A')}\n"
                        policy_content += f"- **링크**: {project.get('detailsUrl', 'N/A')}\n\n"
                else:
                    policy_content = "### 관련 정부 지원 정책\n\n해당 지역 및 토지 특성과 관련된 정부 지원 정책을 찾지 못했습니다.\n\n"
                    
        except (json.JSONDecodeError, KeyError) as e:
            # JSON 파싱 실패 시 텍스트에서 정보 추출 시도
            policy_content = "### 관련 정부 지원 정책\n\n"
            
            # 정책 에이전트의 텍스트 응답에서 유용한 정보 추출
            lines = policy_analysis.split('\n')
            useful_info = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('{') and not line.startswith('}') and 'Tool #' not in line and 'Response [200]' not in line:
                    useful_info.append(line)
            
            if useful_info:
                policy_content += '\n'.join(useful_info)
            else:
                policy_content += "정책 정보를 처리하는 중 오류가 발생했습니다.\n"
    else:
        # JSON이 없는 경우 원본 텍스트 사용
        policy_content = f"### 관련 정부 지원 정책\n\n{policy_analysis}"
    
    report = f"""# 토지 분석 보고서

**작성일**: {current_date}

## 1. 토지 기본 정보

| 항목 | 내용 |
|------|------|
| 주소 | {land_data.get('주소', 'N/A')} |
| 지목 | {land_data.get('지목', 'N/A')} |
| 용도지역 | {land_data.get('용도지역', 'N/A')} |
| 용도지구 | {land_data.get('용도지구', 'N/A')} |
| 토지이용상황 | {land_data.get('토지이용상황', 'N/A')} |
| 지형고저 | {land_data.get('지형고저', 'N/A')} |
| 형상 | {land_data.get('형상', 'N/A')} |
| 도로접면 | {land_data.get('도로접면', 'N/A')} |
| 공시지가 | {gongsi_display} |

## 2. 전문가 토지 분석

{knowledge_analysis}

## 3. 관련 정부 지원 정책

{policy_content}

## 4. 종합 의견 및 권고사항

위의 분석 결과를 종합하면, 해당 토지는 다음과 같은 특성을 가지고 있습니다:

- **위치적 장점**: {land_data.get('주소', '')}에 위치하여 접근성이 우수
- **용도지역 특성**: {land_data.get('용도지역', '')}으로 분류되어 상업적 활용 가능
- **현재 이용상황**: {land_data.get('토지이용상황', '')}으로 활용 중
- **투자 가치**: 공시지가 {gongsi_display} 기준 평가

### 권고사항
1. 관련 정부 지원 정책 적극 활용 검토
2. 용도지역 특성에 맞는 개발 계획 수립
3. 지역 개발 동향 지속적 모니터링
4. 전문가 자문을 통한 세부 투자 계획 수립

---
*본 보고서는 AI 기반 분석 결과이며, 실제 투자 결정 시에는 전문가의 추가 검토가 필요합니다.*
"""
    
    return report

@tool
def orchestrate_land_analysis(land_data_str: str) -> str:
    """
    토지 데이터를 입력받아 종합적인 한국어 토지 분석 보고서를 생성합니다.
    
    Args:
        land_data_str: 토지 정보 문자열 (예: "'주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', ...")
        
    Returns:
        완성된 한국어 토지 분석 보고서
    """
    try:
        # 문자열 데이터를 딕셔너리로 파싱 (더 안전한 방식)
        land_data = {}
        
        # 입력 데이터 정리
        clean_data = land_data_str.replace("'", "").strip()
        
        # 각 항목을 분리하여 파싱
        items = clean_data.split(', ')
        for item in items:
            if ':' in item:
                parts = item.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # 공시지가는 숫자로 변환
                    if key == '공시지가':
                        try:
                            value = int(value)
                        except ValueError:
                            pass
                    
                    land_data[key] = value
        
        # 필수 데이터 확인
        if not land_data or '주소' not in land_data:
            return "토지 데이터 파싱 오류: 주소 정보가 없습니다. 데이터 형식을 확인해주세요."
        
        print("🔍 토지 지식 분석 시작...")
        knowledge_analysis = land_knowledge_analysis(land_data_str)
        
        print("🏛️ 정책 분석 시작...")
        policy_analysis = policy_search_analysis(land_data_str)
        
        print("📋 보고서 생성 중...")
        final_report = create_korean_land_report(land_data, knowledge_analysis, policy_analysis)
        
        return final_report
        
    except Exception as e:
        return f"토지 분석 오케스트레이션 오류: {str(e)}\n입력 데이터: {land_data_str}"

def main():
    """메인 오케스트레이터 실행"""
    model = get_configured_model()
    
    # 시스템 프롬프트 설정
    system_prompt = """
    당신은 토지 분석 전문 AI 오케스트레이터입니다. 
    토지 데이터를 받아서 전문적인 지식 분석과 정책 분석을 수행하고, 
    이를 종합하여 한국어로 된 상세한 토지 분석 보고서를 작성합니다.
    
    사용자가 토지 데이터를 제공하면, orchestrate_land_analysis 도구를 사용하여
    종합적인 분석 보고서를 생성해야 합니다.
    
    항상 정확하고 전문적인 분석을 제공하며, 
    실용적인 권고사항을 포함한 보고서를 생성해야 합니다.
    """
    
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[orchestrate_land_analysis]
    )
    
    # 테스트 데이터
    test_land_data = "'주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', '용도지역': '중심상업지역', '용도지구': '지정되지않음', '토지이용상황': '업무용', '지형고저': '평지', '형상': '세로장방', '도로접면': '광대소각', '공시지가': 3735000"
    
    print("🚀 토지 분석 오케스트레이터 시작")
    print(f"📍 분석 대상: {test_land_data}")
    print("=" * 80)
    
    try:
        # 직접 도구 호출로 테스트
        print("🔧 직접 도구 호출 테스트...")
        direct_result = orchestrate_land_analysis(test_land_data)
        print("✅ 직접 호출 성공!")
        print(direct_result)
        
        # 결과를 파일로 저장
        filename = f"토지분석보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(direct_result))
        print(f"\n📄 보고서가 {filename}로 저장되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

# 개별 함수 테스트를 위한 추가 함수
def test_individual_agents():
    """개별 에이전트 테스트"""
    test_data = "'주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', '용도지역': '중심상업지역', '용도지구': '지정되지않음', '토지이용상황': '업무용', '지형고저': '평지', '형상': '세로장방', '도로접면': '광대소각', '공시지가': 3735000"
    
    print("🧪 개별 에이전트 테스트")
    print("=" * 50)
    
    try:
        print("1️⃣ 지식 에이전트 테스트...")
        knowledge_result = land_knowledge_analysis(test_data)
        print("✅ 지식 에이전트 성공")
        print(knowledge_result[:200] + "..." if len(knowledge_result) > 200 else knowledge_result)
        
        print("\n2️⃣ 정책 에이전트 테스트...")
        policy_result = policy_search_analysis(test_data)
        print("✅ 정책 에이전트 성공")
        print(policy_result[:200] + "..." if len(policy_result) > 200 else policy_result)
        
    except Exception as e:
        print(f"❌ 개별 테스트 오류: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_individual_agents()
    else:
        main()