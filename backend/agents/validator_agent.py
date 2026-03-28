# backend/agents/validator_agent.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings

class ValidatorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)

    def run(self, state: dict) -> dict:
        prompt = f"""
        Review this campaign output for accuracy and quality.
        Check for:
        - Hallucinations or made-up statistics
        - Policy violations (Google/Meta ad policies)
        - Character limit violations
        - Logical inconsistencies
        - Missing required elements

        Research: {state['research']}
        Strategy: {state['strategy']}
        Ad Copy: {state['ad_copy']}

        Return JSON: {{"approved": true/false, "score": 0-100, "issues": [], "recommendations": []}}
        """
        response = self.llm([SystemMessage(content="You are a strict ad campaign quality reviewer."), HumanMessage(content=prompt)])
        state['validation'] = response.content
        state['agent_log'].append("Validator Agent: Complete")
        return state