from knowledge_agent_tool import knowledge_agent
from strands import Agent, tool
from strands_tools import current_time
from config import get_configured_model, get_agent_prompt
import os
from dotenv import load_dotenv

load_dotenv()

ORCHESTRATOR_AGENT_PROMPT = get_agent_prompt('orchestrator_agent_prompt')

region = os.getenv('AWS_REGION')

class ReportOrchestrator:
    def __init__(self):
        self.agent = Agent(
            model = get_configured_model(),
            system_prompt=get_agent_prompt(knowledge_agent_prompt)
            tools=[knowledge_agent, current_time]
        )

    def generate(self, query: str) -> str:
        """
        Creates real estate analysis document by orchestrating two agents.

        Args:
            query (str): The user's natural language request.

        Returns:
            str: The generated string data that is used for jinja2's template rendering.
        """
        print(f"input quert: {query}")

        
