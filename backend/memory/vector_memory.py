# backend/memory/vector_memory.py

from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from core.config import settings

class VectorMemory:
    def __init__(self):
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = pc.Index(settings.PINECONE_INDEX)
        self.embedder = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

    def store(self, workspace_id: str, text: str, metadata: dict = {}):
        embedding = self.embedder.embed_query(text)
        vector_id = f"{workspace_id}-{hash(text)}"
        self.index.upsert(vectors=[(vector_id, embedding, {"text": text, "workspace": workspace_id, **metadata})])
        return vector_id

    def search(self, workspace_id: str, query: str, top_k: int = 5) -> list:
        embedding = self.embedder.embed_query(query)
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            filter={"workspace": workspace_id},
            include_metadata=True
        )
        return [r.metadata for r in results.matches]