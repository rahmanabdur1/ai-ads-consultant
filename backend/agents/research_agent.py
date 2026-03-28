# backend/agents/research_agent.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings

class ResearchAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)

    def run(self, state: dict) -> dict:
        prompt = f"""
        You are a market research expert for digital advertising.
        Analyze the following campaign brief and return:
        - Target audience profile
        - Competitor landscape
        - Market trends
        - Best keywords to target
        - Estimated CPCs

        Campaign Brief: {state['user_input']}
        Budget: {state.get('budget', 'Not specified')}
        Platform: {state.get('platform', 'Google & Meta')}
        """
        response = self.llm([SystemMessage(content="You are an expert market researcher."), HumanMessage(content=prompt)])
        state['research'] = response.content
        state['agent_log'] = state.get('agent_log', []) + ["Research Agent: Complete"]
        return state