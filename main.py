"""Main Application - Strands Agents Workshop"""
import os
import sys
from typing import Dict, Any
from orchestrator_agent import OrchestratorAgent
from model_config import get_configured_model


class StrandsAgentsWorkshopApp:
    
    """
    Strands Agents Workshop Main Application
    
    Actual implementation of multi-agent system using 
    Agents as Tools pattern.
    """

    def __init__(self, model_id: str = None, user_id: str = "workshop_user"):
        self.model = get_configured_model(model_id)
        self.user_id = user_id
        self.orchestrator_agent = OrchestratorAgent(self.model, user_id)
        
        # 시스템 정보 출력
        model_name = type(self.model).__name__
        current_model_id = getattr(self.model, 'model_id', 'unknown')

        print("=" * 60)
        print("🗄️ Database Analysis System")
        print("=" * 60)
        print(f"사용자 ID: {user_id}")
        print()
        print("사용 가능한 Agent:")
        print("• Planning Agent - 실행 계획 수립")
        print("• Database Agent - PostgreSQL 데이터베이스 쿼리 및 분석")
        print("• Orchestrator Agent - 오케스트레이터 (Sub Agent 관리)")
        print()
        print("🔄 처리 흐름:")
        print("1. 계획 수립 → 2. 데이터베이스 분석 → 3. 결과 응답")
        print("=" * 60)

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력을 Orchestrator Agent를 통해 처리"""
        try:
            result = self.orchestrator_agent.process_user_input(user_input)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"처리 중 오류가 발생했습니다: {str(e)}",
                "user_input": user_input
            }

    def format_response(self, response: Dict[str, Any]) -> str:
        """응답 포맷팅 - 가독성 개선"""
        if response.get("success"):
            raw_response = response.get("response", "응답을 생성할 수 없습니다.")
            return raw_response
        else:
            return f"❌ 오류: {response.get('error', '알 수 없는 오류')}"


    def run_interactive_mode(self):
        """대화형 모드 실행"""
        print("\n🚀 데이터베이스 분석 모드 시작!")
        print("다양한 데이터베이스 요청을 입력해보세요:")
        print("  - 테이블 조회: '데이터베이스에 어떤 테이블이 있어?'")
        print("  - 스키마 분석: 'electricity 테이블의 구조를 알려줘'")
        print("  - 데이터 조회: 'population 테이블에서 샘플 데이터를 보여줘'")
        print("  - 분석 쿼리: '전력 소비량이 가장 높은 지역은 어디야?'")
        print("  - 복합 분석: '지역별 인구와 전력 소비량의 관계를 분석해줘'")
        print("  - 종료: '/quit'")
        print()

        while True:
            try:
                user_input = input("💬 입력: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['/quit', 'quit', 'exit', '종료']:
                    print("👋 시스템을 종료합니다. 안녕히 가세요!")
                    break
                
                # 요청 처리
                result = self.process_input(user_input)
                response = self.format_response(result)
                
                # 응답 출력
                print("\n🎯" + "=" * 58 + "🎯")
                print("🤖 최종 응답")
                print(response)
                print("🎯" + "=" * 58 + "🎯")
                print("\n" + "-" * 50 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 시스템을 종료합니다. 안녕히 가세요!")
                break
            except Exception as e:
                print(f"\n❌ 예상치 못한 오류: {str(e)}")
                print("다시 시도해주세요.\n")


def main():
    """메인 실행 함수"""
    
    app = StrandsAgentsWorkshopApp()
    app.run_interactive_mode()


if __name__ == "__main__":
    main()
