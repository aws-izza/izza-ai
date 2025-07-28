#!/usr/bin/env python3
"""
Workshop Strands Agents System Test

This file is designed to help workshop participants 
easily understand and test the core functionality of the system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import StrandsAgentsWorkshopApp


class WorkshopTester:
    """Simple test runner for workshop"""
    
    def __init__(self):
        print("🎓 Workshop Strands Agents System Test")
        print("=" * 60)
        try:
            self.app = StrandsAgentsWorkshopApp()
            print()
        except Exception as e:
            print(f"❌ Application initialization failed: {str(e)}")
            print("💡 Complete main.py in Lab 5 and try again.")
            return
    
    def test_basic_functionality(self):
        """Basic functionality test"""
        print("📋 1. Basic Functionality Test")
        print("-" * 40)
        
        test_cases = [
            ("Hello", "general conversation"),
            ("What is Python?", "search functionality"),
            ("New York weather", "weather query")
        ]
        
        for query, description in test_cases:
            print(f"\n🧪 Test: {query} ({description})")
            try:
                result = self.app.run_single_query(query)
                
                if result.get('success'):
                    print("✅ Success")
                    response = self.app.format_response(result)
                    print(f"📝 Response: {response[:100]}...")
                else:
                    print("❌ Failed")
                    print(f"Error: {result.get('error', 'Unknown')}")
            except Exception as e:
                print(f"❌ Test execution error: {str(e)}")
    
    def test_orchestrator_planning(self):
        """Orchestrator planning test"""
        print("\n📋 2. Orchestrator Planning Test")
        print("-" * 40)
        
        print("🎯 Check planning process with complex request")
        query = "Tell me about Paris and also tell me the weather"
        print(f"Test query: {query}")
        print()
        
        try:
            # Check execution plan output
            result = self.app.run_single_query(query)
            
            if result.get('success'):
                print("✅ Planning and execution success")
            else:
                print("❌ Planning failed")
        except Exception as e:
            print(f"❌ Test execution error: {str(e)}")
    
    def test_sub_agents(self):
        """Sub-agent specific test"""
        print("\n📋 3. Sub-Agent Specific Test")
        print("-" * 40)
        
        agents_tests = [
            ("Search Agent", "What is artificial intelligence?"),
            ("Weather Agent", "How's the weather in Los Angeles?"),
            ("Conversation Agent", "I'm feeling good today")
        ]
        
        for agent_name, query in agents_tests:
            print(f"\n🤖 {agent_name} Test")
            print(f"Query: {query}")
            
            try:
                result = self.app.run_single_query(query)
                
                if result.get('success'):
                    print("✅ Success")
                else:
                    print("❌ Failed")
            except Exception as e:
                print(f"❌ Test execution error: {str(e)}")
    
    def test_interactive_flow(self):
        """Interactive flow test (simplified for workshop)"""
        print("\n📋 4. Interactive Flow Test")
        print("-" * 40)
        
        print("🔄 Clarity assessment functionality test")
        
        # Clear request
        print("\n✅ Clear request test:")
        clear_query = "How's the weather in New York?"
        print(f"Query: {clear_query}")
        
        try:
            result = self.app.process_input(clear_query)
            needs_clarification = result.get('needs_clarification', False)
            
            print(f"Needs clarification: {needs_clarification}")
            if not needs_clarification:
                print("→ Executed immediately ✅")
            else:
                print("→ Additional information requested")
        except Exception as e:
            print(f"❌ Test execution error: {str(e)}")
        
        # Vague request (results may vary based on LLM judgment)
        print("\n❓ Vague request test:")
        vague_query = "coffee"
        print(f"Query: {vague_query}")
        
        try:
            result = self.app.process_input(vague_query)
            needs_clarification = result.get('needs_clarification', False)
            
            print(f"Needs clarification: {needs_clarification}")
            if needs_clarification:
                print("→ Additional information requested ✅")
                print(f"Response: {result.get('response', '')[:100]}...")
            else:
                print("→ Executed immediately (LLM judged as processable)")
        except Exception as e:
            print(f"❌ Test execution error: {str(e)}")
    
    def run_all_tests(self):
        """Execute all tests"""
        if not hasattr(self, 'app'):
            print("❌ Application not initialized.")
            return
            
        try:
            self.test_basic_functionality()
            self.test_orchestrator_planning()
            self.test_sub_agents()
            self.test_interactive_flow()
            
            print("\n" + "=" * 60)
            print("🎉 Workshop test completed!")
            print("=" * 60)
            print("✅ All core functions are working properly.")
            print("🎓 Ready to proceed with the workshop!")
            
        except Exception as e:
            print(f"\n❌ Error occurred during testing: {str(e)}")
            print("🔧 Please check system configuration.")


def main():
    """Main execution function"""
    tester = WorkshopTester()
    if hasattr(tester, 'app'):
        tester.run_all_tests()


if __name__ == "__main__":
    main()
