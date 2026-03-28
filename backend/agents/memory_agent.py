

from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.vector_memory import VectorMemory
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings
import json

class MemoryAgent:
    def __init__(self):
        self.short = ShortTermMemory()
        self.long = LongTermMemory()
        self.vector = VectorMemory()
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def run(self, state: dict) -> dict:
        action = state.get('memory_action', 'read')
        if action == 'read':
            return self._read_memory(state)
        elif action == 'write':
            return self._write_memory(state)
        elif action == 'summarize':
            return self._summarize_and_compress(state)
        else:
            return self._read_memory(state)

    def _read_memory(self, state: dict) -> dict:
        workspace_id = state.get('workspace_id', '')
        session_id = state.get('session_id', '')
        query = state.get('user_input', '')

        # Short-term context
        short_context = self.short.get_context(session_id)

        # Long-term facts
        long_facts = self.long.get_workspace_facts(workspace_id)

        # Semantic search
        vector_results = self.vector.search(workspace_id, query, top_k=5)

        # Rank and build context
        context = self._build_ranked_context(
            short_context, long_facts, vector_results, query
        )

        state['memory_context'] = context
        state['agent_log'] = state.get('agent_log', []) + ["Memory Agent: Context loaded"]
        return state

    def _write_memory(self, state: dict) -> dict:
        workspace_id = state.get('workspace_id', '')
        session_id = state.get('session_id', '')

        # Write to short term
        if state.get('user_input'):
            self.short.add_context(session_id, {
                "role": "user",
                "content": state['user_input']
            })

        # Write campaign result to long term
        if state.get('ad_copy'):
            self.long.store_fact(workspace_id, {
                "type": "campaign_result",
                "platform": state.get('platform'),
                "budget": state.get('budget'),
                "goal": state.get('goal'),
                "ad_copy_preview": state.get('ad_copy', '')[:200],
                "approved": state.get('approved', False)
            })

        # Write to vector store
        if state.get('ad_copy') and state.get('approved'):
            summary = (
                f"Successful campaign for {state.get('platform')} | "
                f"Goal: {state.get('goal')} | Budget: ${state.get('budget')} | "
                f"Copy preview: {state.get('ad_copy', '')[:150]}"
            )
            self.vector.store(workspace_id, summary, {
                "type": "campaign_success",
                "platform": state.get('platform'),
                "roi_label": "positive"
            })

        state['agent_log'] = state.get('agent_log', []) + ["Memory Agent: Memory written"]
        return state

    def _summarize_and_compress(self, state: dict) -> dict:
        session_id = state.get('session_id', '')
        history = self.short.get_context(session_id)

        if len(history) < 10:
            state['agent_log'] = state.get('agent_log', []) + ["Memory Agent: No compression needed"]
            return state

        conversation = "\n".join([
            f"{m['role'].upper()}: {m['content'][:200]}"
            for m in history[-20:]
        ])

        response = self.llm([
            SystemMessage(content="You summarize advertising consultant conversations into concise memory."),
            HumanMessage(content=f"""
                Summarize this conversation into key facts to remember:

                {conversation}

                Return JSON:
                {{
                    "summary": "2-3 sentence overview",
                    "key_facts": ["fact1", "fact2", "fact3"],
                    "user_preferences": {{"tone": "...", "platform": "...", "budget_range": "..."}},
                    "campaign_insights": ["insight1", "insight2"]
                }}
            """)
        ])

        try:
            summary_data = json.loads(response.content)
            compressed = {
                "role": "system",
                "content": f"[MEMORY SUMMARY] {summary_data.get('summary')} Key facts: {', '.join(summary_data.get('key_facts', []))}"
            }
            self.short.set(f"context:{session_id}", {"messages": [compressed]})
        except:
            pass

        state['agent_log'] = state.get('agent_log', []) + ["Memory Agent: Memory compressed"]
        return state

    def _build_ranked_context(self, short: list, long: list, vector: list, query: str) -> dict:
        return {
            "recent_conversation": short[-5:] if short else [],
            "workspace_facts": long[:5] if long else [],
            "relevant_past_campaigns": [v.get('text', '')[:200] for v in vector[:3]],
            "total_context_items": len(short) + len(long) + len(vector)
        }