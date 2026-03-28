# backend/agents/strategy_agent.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings

class StrategyAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)

    def run(self, state: dict) -> dict:
        prompt = f"""
        Based on this research, create a complete ad campaign strategy:

        Research: {state['research']}
        Budget: {state.get('budget')}
        Goal: {state.get('goal', 'conversions')}

        Return:
        - Campaign structure (ad sets, targeting)
        - Budget allocation per platform
        - Bidding strategy
        - Timeline
        - KPI targets (CTR, CPC, ROAS)
        """
        response = self.llm([SystemMessage(content="You are a senior paid media strategist."), HumanMessage(content=prompt)])
        state['strategy'] = response.content
        state['agent_log'].append("Strategy Agent: Complete")
        return state