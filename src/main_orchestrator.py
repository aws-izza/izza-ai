from strands import Agent, tool
from config import get_configured_model, get_agent_prompt
from knowledge_agent_tool import knowledge_agent
from policy_agent import policy_agent
from dotenv import load_dotenv
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
import re

load_dotenv()

@tool
def land_knowledge_analysis(land_data: str, analyze_data: Dict[str, Any]) -> str:
    """
    토지 데이터와 분석 점수를 기반으로 전문적인 지식 기반 분석을 수행합니다.
    
    Args:
        land_data: 토지 정보 데이터 (주소, 지목, 용도지역 등)
        analyze_data: 분석 점수 데이터 (입지조건, 인프라, 안정성)
        
    Returns:
        토지에 대한 전문적인 분석 결과
    """
    
    score_lines = []
    if analyze_data.get('totalScore') is not None:
        score_lines.append(f"- 종합 점수: {round(analyze_data['totalScore'], 2)}")
    if analyze_data.get('입지조건') is not None:
        score_lines.append(f"- 입지조건: {round(analyze_data['입지조건'], 2)}")
    if analyze_data.get('인프라') is not None:
        score_lines.append(f"- 인프라: {round(analyze_data['인프라'], 2)}")
    if analyze_data.get('안정성') is not None:
        score_lines.append(f"- 안정성: {round(analyze_data['안정성'], 2)}")

    if score_lines:
        scores_section = "분석 점수:\n" + "\n".join(score_lines)
    else:
        scores_section = "분석 점수: 제공된 점수 없음"

    query = f"""
    다음 토지 정보와 점수를 바탕으로 상세한 분석을 해주세요:

    토지 정보:
    {land_data}

    {scores_section}

    다음 항목들을 포함하여 분석해주세요:
    1. 지목과 용도지역의 특성 및 의미
    2. 토지 이용 현황 분석
    3. 지형 및 형상의 장단점
    4. 도로 접면 상황 평가
    5. 공시지가 수준 분석
    6. 개발 가능성 및 제약사항
    7. 투자 가치 평가
    8. 위 분석 점수들을 고려한 종합적인 투자 의견 및 위험 요소 분석
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
    - 지역 개발 관련 기술 지원 정책
    """
    
    return policy_agent(query)


def parse_policy_response_for_template(policy_response: str) -> List[Dict[str, str]]:
    """
    정책 에이전트 응답을 파싱하여 템플릿용 구조화된 데이터로 변환합니다.
    강화된 파싱 로직으로 다양한 응답 형식을 처리합니다.
    """
    policies = []
    
    try:
        response_str = str(policy_response).strip()
        # 컨트롤 문자 등 숨겨진 문자 제거
        response_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_str)
        
        # 디버그 파일 저장
        debug_filename = f"policy_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write("=== POLICY AGENT RESPONSE DEBUG ===\n")
                f.write(f"Timestamp: {datetime.now()}\n\n")
                f.write("---" + "ORIGINAL RESPONSE" + "---" + "\n")
                f.write(str(policy_response))
                f.write("\n\n---" + "CLEANED RESPONSE" + "---" + "\n")
                f.write(response_str)
            print(f"📁 디버그 파일 저장: {debug_filename}")
        except Exception as e:
            print(f"❌ 디버그 파일 저장 실패: {str(e)}")

        # 방법 0: 첫 '{'와 마지막 '}'으로 JSON 블록 찾기
        print("🔍 중괄호로 JSON 블록 검색...")
        json_start = response_str.find('{')
        json_end = response_str.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_str[json_start:json_end]
            try:
                # 이중 중괄호가 있다면 단일로 변환
                if '{{' in json_str:
                    json_str = json_str.replace('{{', '{').replace('}}', '}')
                
                policy_data = json.loads(json_str)
                projects = policy_data.get("projects", [])
                print(f"✅ 중괄호 검색으로 {len(projects)}개 프로젝트 파싱")
                policies.extend(extract_policies_from_projects(projects))
            except json.JSONDecodeError as e:
                print(f"❌ 중괄호 검색 JSON 파싱 실패: {e}")

        # 방법 1: 이중 중괄호 처리 (가장 일반적인 문제)
        if not policies:
            print("🔍 이중 중괄호 처리...")
            if '{{' in response_str and '}}' in response_str:
                print("✅ 이중 중괄호 발견 - 단일 중괄호로 변환")
                # 이중 중괄호를 단일 중괄호로 변환
                cleaned_response = response_str.replace('{{', '{').replace('}}', '}')
                
                # JSON 패턴 찾기
                json_match = re.search(r'{"projects":\s*\[.*\]}', cleaned_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        policy_data = json.loads(json_str)
                        projects = policy_data.get("projects", [])
                        print(f"✅ 이중 중괄호 처리로 {len(projects)}개 프로젝트 파싱")
                        policies.extend(extract_policies_from_projects(projects))
                    except json.JSONDecodeError as e:
                        print(f"❌ 이중 중괄호 처리 후 JSON 파싱 실패: {e}")
        
        # 방법 2: <result> 태그 파싱
        if not policies:
            print("🔍 <result> 태그 검색...")
            result_match = re.search(r'<result>(.*?)</result>', response_str, re.DOTALL)
            if result_match:
                print("✅ <result> 태그 발견")
                result_content = result_match.group(1).strip()
                try:
                    policy_data = json.loads(result_content)
                    projects = policy_data.get("projects", [])
                    print(f"✅ <result>에서 {len(projects)}개 프로젝트 파싱")
                    policies.extend(extract_policies_from_projects(projects))
                except json.JSONDecodeError as e:
                    print(f"❌ <result> JSON 파싱 실패: {e}")
        
        # 방법 3: 직접 JSON 패턴 찾기 (다양한 패턴)
        if not policies:
            print("🔍 직접 JSON 패턴 검색...")
            
            # JSON 객체 또는 배열을 찾는 더 일반적인 정규식
            json_pattern = r'(\{s*"projects"s*:\s*\[.*?\]s*\})|(\[s*\{.*?\}s*\])'
            
            matches = re.finditer(json_pattern, response_str, re.DOTALL)
            
            for match in matches:
                json_str = match.group(0)
                try:
                    # 배열 형태일 경우 딕셔너리로 감싸기
                    if json_str.startswith('['):
                        policy_data = {"projects": json.loads(json_str)}
                    else:
                        policy_data = json.loads(json_str)
                    
                    projects = policy_data.get("projects", [])
                    print(f"   ✅ 정규식으로 {len(projects)}개 프로젝트 파싱")
                    policies.extend(extract_policies_from_projects(projects))
                    if policies:
                        break # 첫 번째 성공적인 파싱 후 중단
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON 파싱 실패: {e}")
                    continue
        
        # 방법 4: 전체 응답을 JSON으로 파싱 시도
        if not policies:
            print("🔍 전체 응답 JSON 파싱 시도...")
            try:
                policy_data = json.loads(response_str)
                if isinstance(policy_data, dict) and "projects" in policy_data:
                    projects = policy_data["projects"]
                    print(f"   ✅ 전체 JSON에서 {len(projects)}개 프로젝트 파싱")
                    policies.extend(extract_policies_from_projects(projects))
            except json.JSONDecodeError:
                print("   ❌ 전체 JSON 파싱 실패")
        
        # 방법 5: 정규식으로 개별 프로젝트 추출 (최후의 수단)
        if not policies:
            print("🔍 개별 프로젝트 정규식 추출...")
            
            # projectName 패턴으로 개별 프로젝트 찾기
            project_pattern = r'"projectName"s*:s*"(.*?)".*?"organization"s*:s*"(.*?)".*?"applicationPeriod"s*:s*"(.*?)".*?"summary"s*:s*"(.*?)".*?"detailsUrl"s*:s*"(.*?)"'
            
            matches = re.findall(project_pattern, response_str, re.DOTALL)
            if matches:
                print(f"   ✅ 정규식으로 {len(matches)}개 프로젝트 추출")
                for match in matches:
                    policy = {
                        'name': match[0].strip(),
                        'organization': match[1].strip(),
                        'period': match[2].strip(),
                        'summary': match[3].strip()[:200] + "..." if len(match[3]) > 200 else match[3].strip(),
                        'url': match[4].strip()
                    }
                    policies.append(policy)
        
        # 방법 6: 키워드 기반 더미 정책 생성 (최후의 최후)
        if not policies:
            print("🔍 키워드 기반 정책 감지...")
            if 'projectName' in response_str or '정책' in response_str or '지원' in response_str:
                print("✅ 정책 관련 키워드 발견 - 더미 정책 생성")
                policies.append({
                    'name': '정책 파싱 오류 - 원본 데이터 확인 필요',
                    'organization': '시스템',
                    'period': '확인 필요',
                    'summary': '해당 토지와 관련된 지원 정책이 존재하지 않습니다.',
                    'url': ''
                })
            else:
                print("❌ 정책 관련 키워드를 찾을 수 없음")

    
    except Exception as e:
        print(f"❌ 정책 파싱 전체 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시에도 더미 정책 생성
        policies.append({
            'name': f'정책 파싱 시스템 오류: {str(e)[:100]}',
            'organization': '시스템',
            'period': '확인 필요',
            'summary': '정책 파싱 중 시스템 오류가 발생했습니다. 관리자에게 문의하세요.',
            'url': ''
        })
    
    print(f"📊 최종 파싱된 정책 개수: {len(policies)}")
    if policies:
        print(f"📋 첫 번째 정책: {policies[0]['name'][:50]}...")
    
    return policies

def extract_policies_from_projects(projects: List[Dict]) -> List[Dict[str, str]]:
    """프로젝트 리스트에서 정책 정보 추출"""
    policies = []
    
    for project in projects:  # 모든 정책 표시
        policy = {
            'name': project.get('projectName', 'N/A'),
            'organization': project.get('organization', 'N/A'),
            'period': project.get('applicationPeriod', 'N/A'),
            'summary': project.get('summary', 'N/A'),
            'url': project.get('detailsUrl', '')
        }
        policies.append(policy)
    
    return policies

def parse_policy_response(policy_response: str) -> str:
    """
    정책 에이전트 응답을 파싱하여 구조화된 형식으로 변환합니다.
    """
    try:
        # <result> 태그 내부의 JSON 찾기
        result_start = policy_response.find('<result>')
        result_end = policy_response.find('</result>')
        
        if result_start != -1 and result_end != -1:
            # <result> 태그 내부 추출
            result_content = policy_response[result_start + 8:result_end].strip()
            
            try:
                policy_data = json.loads(result_content)
                projects = policy_data.get("projects", [])
                
                if projects:
                    formatted_content = "### 관련 정부 지원 정책\n\n"
                    
                    for i, project in enumerate(projects, 1):
                        formatted_content += f"#### {i}. 지원정책\n\n"
                        formatted_content += f"- **지원정책 이름**: {project.get('projectName', 'N/A')}\n"
                        formatted_content += f"- **주관**: {project.get('organization', 'N/A')}\n"
                        formatted_content += f"- **기간**: {project.get('applicationPeriod', 'N/A')}\n"
                        formatted_content += f"- **요약**: {project.get('summary', 'N/A')}\n"
                        formatted_content += f"- **링크**: {project.get('detailsUrl', 'N/A')}\n\n"
                    
                    return formatted_content
                    
            except json.JSONDecodeError as e:
                print(f"<result> 태그 내 JSON 파싱 실패: {str(e)}")
        
        # <result> 태그가 없는 경우 기존 방식으로 JSON 찾기
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
                        
                        for i, project in enumerate(projects, 1):
                            formatted_content += f"#### {i}. 지원정책\n\n"
                            formatted_content += f"- **지원정책 이름**: {project.get('projectName', 'N/A')}\n"
                            formatted_content += f"- **주관**: {project.get('organization', 'N/A')}\n"
                            formatted_content += f"- **기간**: {project.get('applicationPeriod', 'N/A')}\n"
                            formatted_content += f"- **요약**: {project.get('summary', 'N/A')}\n"
                            formatted_content += f"- **링크**: {project.get('detailsUrl', 'N/A')}\n\n"
                        
                        return formatted_content
                    
                except json.JSONDecodeError as e:
                    print(f"기존 방식 JSON 파싱 실패: {str(e)}")
        
        # JSON 파싱 실패 시 텍스트에서 유용한 정보 추출
        lines = policy_response.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # 불필요한 라인 제거 (더 많은 패턴 추가)
            if (line and 
                not line.startswith('Tool #') and 
                not line.startswith('---') and 
                'Response [200]' not in line and 
                not line.startswith('<search_quality_') and
                not line.startswith('</search_quality_') and
                not line.startswith('<result>') and
                not line.startswith('</result>') and
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
    kst_tz = timezone(timedelta(hours=9))
    current_date = datetime.now(kst_tz).strftime("%Y년 %m월 %d일")
    
    # 공시지가 포맷팅 처리
    gongsi_price = land_data.get('공시지가', 0)
    if isinstance(gongsi_price, (int, float)):
        gongsi_display = f"{gongsi_price:,}원"
    else:
        gongsi_display = str(gongsi_price)
    
    # 정책 분석 결과를 구조화된 형식으로 파싱
    policy_content = parse_policy_response(policy_analysis)
    
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

def format_ai_analysis_for_html(analysis_text: str) -> str:
    """
    AI 분석 텍스트를 HTML 형식으로 변환합니다.
    번호 목록과 불릿 목록을 적절한 HTML 태그로 변환합니다.
    """
    lines = analysis_text.split('\n')
    formatted_lines = []
    in_numbered_list = False
    in_bullet_list = False
    current_numbered_item = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 빈 줄 처리
        if not line:
            # 불릿 리스트만 종료 (번호 리스트는 유지)
            if in_bullet_list:
                formatted_lines.append('</ul>')
                in_bullet_list = False
            formatted_lines.append('')
            i += 1
            continue
        
        # 번호 목록 처리 (1., 2., 3. 등)
        numbered_match = re.match(r'^(\d+)\.\s*(.+)', line)
        if numbered_match:
            # 이전 불릿 리스트 종료
            if in_bullet_list:
                formatted_lines.append('</ul>')
                in_bullet_list = False
            
            # 번호 리스트 시작
            if not in_numbered_list:
                formatted_lines.append('<ol>')
                in_numbered_list = True
            
            number = numbered_match.group(1)
            content = numbered_match.group(2)
            current_numbered_item = number
            
            # 굵은 글씨 처리
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            
            # 번호 항목 시작 (닫지 않음 - 하위 불릿이 있을 수 있음)
            formatted_lines.append(f'<li><strong>{content}</strong>')
            
            # 다음 줄들을 확인하여 불릿 항목이 있는지 체크
            j = i + 1
            has_bullets = False
            while j < len(lines) and lines[j].strip():
                if re.match(r'^[-*]\s*(.+)', lines[j].strip()):
                    has_bullets = True
                    break
                elif re.match(r'^(\d+)\.\s*(.+)', lines[j].strip()):
                    break
                j += 1
            
            if has_bullets:
                formatted_lines.append('<ul>')
                in_bullet_list = True
            else:
                formatted_lines.append('</li>')
            
            i += 1
            continue
        
        # 불릿 목록 처리 (-, * 등)
        bullet_match = re.match(r'^[-*]\s*(.+)', line)
        if bullet_match:
            content = bullet_match.group(1)
            # 굵은 글씨 처리
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            
            if in_bullet_list:
                formatted_lines.append(f'<li>{content}</li>')
            else:
                # 독립적인 불릿 리스트
                if in_numbered_list:
                    formatted_lines.append('</ol>')
                    in_numbered_list = False
                formatted_lines.append('<ul>')
                formatted_lines.append(f'<li>{content}</li>')
                in_bullet_list = True
            
            i += 1
            continue
        
        # 일반 텍스트 처리
        # 불릿 리스트 종료 및 번호 항목 종료
        if in_bullet_list:
            formatted_lines.append('</ul>')
            formatted_lines.append('</li>')  # 번호 항목 종료
            in_bullet_list = False
        
        # 번호 리스트가 아닌 일반 텍스트면 번호 리스트도 종료
        if in_numbered_list and not re.match(r'^(\d+)\.\s*(.+)', line):
            # 다음 줄이 번호 항목인지 확인
            next_is_numbered = False
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^(\d+)\.\s*(.+)', next_line):
                    next_is_numbered = True
            
            if not next_is_numbered:
                formatted_lines.append('</ol>')
                in_numbered_list = False
        
        # 굵은 글씨 처리
        line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
        
        # 제목 처리 (### 등)
        if line.startswith('###'):
            formatted_lines.append(f'<h4>{line[3:].strip()}</h4>')
        elif line.startswith('##'):
            formatted_lines.append(f'<h3>{line[2:].strip()}</h3>')
        elif line.startswith('#'):
            formatted_lines.append(f'<h2>{line[1:].strip()}</h2>')
        else:
            formatted_lines.append(f'<p>{line}</p>')
        
        i += 1
    
    # 마지막에 열린 리스트 태그 닫기
    if in_bullet_list:
        formatted_lines.append('</ul>')
        formatted_lines.append('</li>')  # 번호 항목도 종료
    if in_numbered_list:
        formatted_lines.append('</ol>')
    
    return '\n'.join(formatted_lines)

def create_template_data(land_data: Dict[str, Any], knowledge_analysis: str, policy_analysis: str, analyze_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Jinja2 템플릿용 데이터 구조를 생성합니다.
    """
    kst_tz = timezone(timedelta(hours=9))
    current_date = datetime.now(kst_tz)
    
    # 공시지가 포맷팅
    gongsi_price = land_data.get('공시지가', 0)
    if isinstance(gongsi_price, (int, float)):
        gongsi_formatted = f"{gongsi_price:,}원"
    else:
        gongsi_formatted = str(gongsi_price)
    
    # 토지 데이터에 포맷된 공시지가 추가
    land_data_with_formatted = land_data.copy()
    land_data_with_formatted['공시지가_formatted'] = gongsi_formatted
    
    # 정책 데이터 파싱
    print("🔍 정책 분석 응답 디버깅:")
    print(f"   응답 타입: {type(policy_analysis)}")
    print(f"   응답 길이: {len(str(policy_analysis))}")
    print(f"   응답 미리보기: {str(policy_analysis)[:300]}...")
    
    policies = parse_policy_response_for_template(policy_analysis)
    
    # AI 분석 결과 HTML 포맷팅
    ai_analysis_html = format_ai_analysis_for_html(knowledge_analysis)
    
    # 분기 계산
    quarter = f"{current_date.year}년 {(current_date.month - 1) // 3 + 1}분기"
    
    # analyze_data 처리 (기본값 설정)
    if analyze_data is None:
        analyze_data = {
            "totalScore": 70,
            "입지조건": 75,
            "인프라": 70,
            "안정성": 65
        }
    
    template_data = {
        'land_data': land_data_with_formatted,
        'analyze_data': analyze_data,
        'ai_analysis': ai_analysis_html,
        'policies': policies,
        'analysis_date': current_date.strftime("%Y년 %m월 %d일 %H시 %M분"),
        'analysis_quarter': quarter
    }
    
    return template_data

def generate_html_report(template_data: Dict[str, Any]) -> str:
    """
    Jinja2 템플릿을 사용하여 HTML 보고서를 생성합니다.
    """
    try:
        # Jinja2 환경 설정
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('web_report_template.html')
        
        # 템플릿 렌더링
        html_content = template.render(**template_data)
        
        return html_content
        
    except Exception as e:
        return f"HTML 보고서 생성 오류: {str(e)}"

@tool
def orchestrate_land_analysis(land_data_str: str) -> str:
    """
    토지 데이터를 입력받아 종합적인 한국어 토지 분석 보고서를 생성합니다.
    
    Args:
        land_data_str: 토지 정보 문자열 (예: "'주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', ...")
        
    Returns:
        완성된 한국어 토지 분석 보고서 (마크다운 형식)
    """
    try:
        # AI 추론 실행
        analysis_result = run_land_analysis_inference(land_data_str)
        
        if 'error' in analysis_result:
            return f"토지 분석 오케스트레이션 오류: {analysis_result['error']}\n입력 데이터: {land_data_str}"
        
        # 마크다운 보고서 반환 (기존 호환성 유지)
        return analysis_result.get('markdown_report', '보고서 생성 중 오류가 발생했습니다.')
        
    except Exception as e:
        return f"토지 분석 오케스트레이션 오류: {str(e)}\n입력 데이터: {land_data_str}"

def render_html_report(user_query: str, analysis_result: Dict[str, Any], task_id: str, template_path: str = "template.html") -> str:
    """
    분석 결과를 사용하여 HTML 보고서를 렌더링합니다.
    
    Args:
        user_query: 사용자 쿼리 (토지 데이터)
        analysis_result: 분석 결과 딕셔너리
        template_path: HTML 템플릿 파일 경로
        
    Returns:
        렌더링된 HTML 문자열
    """
    try:
        # Jinja2 환경 설정
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template(template_path)
        
        # 템플릿 렌더링
        html_content = template.render(task_id=task_id, **analysis_result)
        
        return html_content
        
    except Exception as e:
        return f"<html><body><h1>HTML 보고서 생성 오류</h1><p>{str(e)}</p></body></html>"

def run_land_analysis_inference(land_data_input, analyze_data_input=None) -> Dict[str, Any]:
    """
    토지 분석 추론을 실행하고 구조화된 결과를 반환합니다.
    
    Args:
        land_data_input: 토지 정보 (문자열 또는 딕셔너리)
        
    Returns:
        분석 결과 딕셔너리 (템플릿 렌더링용)
    """
    try:
        # 입력 데이터 타입에 따라 처리
        if isinstance(land_data_input, dict):
            # JSON 딕셔너리인 경우
            land_data = land_data_input.copy()
            # 문자열 형태로도 변환 (기존 에이전트 호환성)
            land_data_str = ", ".join([f"'{k}': '{v}'" for k, v in land_data.items()])
        elif isinstance(land_data_input, str):
            # 기존 문자열 형태인 경우
            land_data_str = land_data_input
            land_data = {}
            clean_data = land_data_str.replace("'", "").strip()
            
            items = clean_data.split(', ')
            for item in items:
                if ':' in item:
                    parts = item.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        
                        if key == '공시지가':
                            try:
                                value = float(value)
                            except ValueError:
                                pass
                        
                        land_data[key] = value
        else:
            raise ValueError("지원하지 않는 데이터 형식입니다.")
        
        if not land_data or '주소' not in land_data:
            raise ValueError("토지 데이터 파싱 오류: 주소 정보가 없습니다.")
        
        # analyze_data 처리
        if analyze_data_input is None:
            analyze_data = {
                "totalScore": 70,
                "입지조건": 75,
                "인프라": 70,
                "안정성": 65
            }
        else:
            analyze_data = analyze_data_input

        print("🔍 토지 지식 분석 시작...")
        knowledge_analysis = land_knowledge_analysis(land_data_str, analyze_data)
        
        print("🏛️ 정책 분석 시작...")
        policy_analysis = policy_search_analysis(land_data_str)
        
        print("📋 분석 결과 구조화 중...")
        
        # 템플릿용 데이터 생성
        template_data = create_template_data(land_data, knowledge_analysis, policy_analysis, analyze_data)
        
        # 마크다운 보고서도 생성 (기존 호환성 유지)
        markdown_report = create_korean_land_report(land_data, knowledge_analysis, policy_analysis)
        
        # 결과에 마크다운 보고서도 포함
        template_data['markdown_report'] = markdown_report
        
        return template_data
        
    except Exception as e:
        # 오류 발생 시 기본 템플릿 데이터 반환
        kst_tz = timezone(timedelta(hours=9))
        current_date = datetime.now(kst_tz)
        default_analyze_data = {
            "totalScore": 0,
            "입지조건": 0,
            "인프라": 0,
            "안정성": 0
        }
        return {
            'land_data': {'주소': 'N/A', '공시지가_formatted': 'N/A'},
            'analyze_data': default_analyze_data,
            'ai_analysis': f'<p>분석 중 오류가 발생했습니다: {str(e)}</p>',
            'policies': [],
            'analysis_date': current_date.strftime("%Y년 %m월 %d일 %H시 %M분"),
            'analysis_quarter': f"{current_date.year}년 {(current_date.month - 1) // 3 + 1}분기",
            'error': str(e)
        }

def main():
    """메인 오케스트레이터 실행"""
    
    # 테스트 데이터 (JSON 형식)
    test_land_data_json = {
        '주소': '대구광역시 중구 동인동1가 2-1',
        '지목': '대',
        '용도지역': '중심상업지역',
        '용도지구': '지정되지않음',
        '토지이용상황': '업무용',
        '지형고저': '평지',
        '형상': '세로장방',
        '도로접면': '광대소각',
        '공시지가': 3735000
    }
    
    test_analyze_data_json = {
        'totalScore': 71,
        '입지조건': 86,
        '인프라': 78,
        '안정성': 48
    }
    
    # 기존 문자열 형식도 지원
    test_land_data_str = "'주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', '용도지역': '중심상업지역', '용도지구': '지정되지않음', '토지이용상황': '업무용', '지형고저': '평지', '형상': '세로장방', '도로접면': '광대소각', '공시지가': 3735000"
    
    print("🚀 토지 분석 오케스트레이터 시작")
    print(f"📍 분석 대상 (JSON): {test_land_data_json}")
    print("=" * 80)
    
    try:
        # 1. AI 추론 실행 (JSON 데이터로 테스트)
        print("🤖 AI 추론 실행 중 (JSON 입력)...")
        analysis_result = run_land_analysis_inference(test_land_data_json, test_analyze_data_json)
        
        if 'error' in analysis_result:
            print(f"⚠️ 분석 중 오류 발생: {analysis_result['error']}")
        else:
            print("✅ AI 추론 완료!")
            print(f"   - 정책 개수: {len(analysis_result.get('policies', []))}")
            print(f"   - 분석 날짜: {analysis_result.get('analysis_date', 'N/A')}")
        
        # 2. 마크다운 보고서 저장 (기존 호환성)
        if 'markdown_report' in analysis_result:
            md_filename = f"토지분석보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(md_filename, "w", encoding="utf-8") as f:
                f.write(analysis_result['markdown_report'])
            print(f"📄 마크다운 보고서 저장: {md_filename}")
        
        # 3. HTML 보고서 렌더링 (Jinja2 분리)
        print("🎨 HTML 보고서 렌더링 중...")
        # JSON 데이터를 문자열로 변환하여 기존 템플릿과 호환
        land_data_str_for_template = ", ".join([f"'{k}': '{v}'" for k, v in test_land_data_json.items()])
        report_html = render_html_report(land_data_str_for_template, analysis_result, "web_report_template.html")
        
        # 4. HTML 보고서 파일 저장
        report_filename = f"토지분석보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(str(report_html))
        
        print(f"\n✅ Successfully generated report. Please open '{report_filename}' in your browser.")
        print(f"📊 HTML 보고서 크기: {len(report_html):,} bytes")
        
        # 5. 결과 요약 출력
        print("\n📋 분석 결과 요약:")
        if analysis_result.get('policies'):
            print(f"   - 발견된 정책: {len(analysis_result['policies'])}개")
            for i, policy in enumerate(analysis_result['policies'][:3], 1):
                print(f"     {i}. {policy['name'][:50]}...")
        else:
            print("   - 관련 정책을 찾지 못했습니다.")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# 개별 함수 테스트를 위한 추가 함수
def test_individual_agents():
    """개별 에이전트 테스트"""
    test_data = "'주소': '대구광역시 중구 동인동1가 2-1', '지목': '대', '용도지역': '중심상업지역', '용도지구': '지정되지않음', '토지이용상황': '업무용', '지형고저': '평지', '형상': '세로장방', '도로접면': '광대소각', '공시지가': 3735000"
    test_analyze_data = {
        'totalScore': 82,
        '입지조건': 80,
        '인프라': 75,
        '안정성': 90
    }
    
    print("🧪 개별 에이전트 테스트")
    print("=" * 50)
    
    try:
        print("1️⃣ 지식 에이전트 테스트...")
        knowledge_result = land_knowledge_analysis(test_data, test_analyze_data)
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
