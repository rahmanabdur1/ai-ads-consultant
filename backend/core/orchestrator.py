# backend/core/orchestrator.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from agents.research_agent import ResearchAgent
from agents.strategy_agent import StrategyAgent
from agents.copywriting_agent import CopywritingAgent
from agents.validator_agent import ValidatorAgent
from memory.short_term import ShortTermMemory
from memory.vector_memory import VectorMemory

class CampaignState(TypedDict):
    user_input: str
    budget: Optional[float]
    platform: Optional[str]
    goal: Optional[str]
    tone: Optional[str]
    workspace_id: str
    session_id: str
    research: Optional[str]
    strategy: Optional[str]
    ad_copy: Optional[str]
    validation: Optional[str]
    agent_log: List[str]
    approved: bool

class Orchestrator:
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.strategy_agent = StrategyAgent()
        self.copy_agent = CopywritingAgent()
        self.validator_agent = ValidatorAgent()
        self.short_mem = ShortTermMemory()
        self.vector_mem = VectorMemory()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(CampaignState)

        graph.add_node("research", self.research_agent.run)
        graph.add_node("strategy", self.strategy_agent.run)
        graph.add_node("copywriting", self.copy_agent.run)
        graph.add_node("validate", self.validator_agent.run)
        graph.add_node("store_memory", self._store_memory)

        graph.set_entry_point("research")
        graph.add_edge("research", "strategy")
        graph.add_edge("strategy", "copywriting")
        graph.add_edge("copywriting", "validate")
        graph.add_conditional_edges("validate", self._check_approval, {
            "approved": "store_memory",
            "retry": "copywriting"
        })
        graph.add_edge("store_memory", END)

        return graph.compile()

    def _check_approval(self, state: dict) -> str:
        import json
        try:
            result = json.loads(state['validation'])
            return "approved" if result.get("approved") and result.get("score", 0) >= 70 else "retry"
        except:
            return "approved"

    def _store_memory(self, state: dict) -> dict:
        summary = f"Campaign: {state['user_input']} | Result: {state['ad_copy'][:200]}"
        self.vector_mem.store(state['workspace_id'], summary, {"type": "campaign_result"})
        self.short_mem.add_context(state['session_id'], {"role": "assistant", "content": summary})
        state['approved'] = True
        return state

    async def run(self, input_data: dict) -> dict:
        state = {
            "user_input": input_data["message"],
            "budget": input_data.get("budget"),
            "platform": input_data.get("platform", "google"),
            "goal": input_data.get("goal", "conversions"),
            "tone": input_data.get("tone", "professional"),
            "workspace_id": input_data["workspace_id"],
            "session_id": input_data["session_id"],
            "research": None, "strategy": None, "ad_copy": None,
            "validation": None, "agent_log": [], "approved": False
        }
        return self.graph.invoke(state)