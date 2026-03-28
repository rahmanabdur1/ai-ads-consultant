# backend/agents/copywriting_agent.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings

class CopywritingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)

    def run(self, state: dict) -> dict:
        prompt = f"""
        Write ad copy based on this strategy:

        Strategy: {state['strategy']}
        Platform: {state.get('platform', 'Google & Meta')}
        Tone: {state.get('tone', 'professional')}

        Produce:
        - 3 Google Ad headlines (max 30 chars each)
        - 2 Google Ad descriptions (max 90 chars each)
        - 1 Meta Ad primary text (max 125 chars)
        - 1 Meta Ad headline (max 40 chars)
        - 3 CTA options
        """
        response = self.llm([SystemMessage(content="You are an expert copywriter for digital ads."), HumanMessage(content=prompt)])
        state['ad_copy'] = response.content
        state['agent_log'].append("Copywriting Agent: Complete")
        return state