import os
from typing import List
from openai import AsyncOpenAI


class EmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "text-embedding-3-small"
        self.dimensions = 1536

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of text strings."""
        if not texts:
            return []

        if not self.client:
            # Fallback/Mock vector for local testing when API key is not present
            print("[EmbeddingService] WARNING: No API key found. Using mock vectors.")
            return [[0.01 * (i + 1)] * self.dimensions for i in range(len(texts))]

        response = await self.client.embeddings.create(input=texts, model=self.model)
        return [data.embedding for data in response.data]

    async def get_single_embedding(self, text: str) -> List[float]:
        results = await self.get_embeddings([text])
        return results[0] if results else []


embedding_service = EmbeddingService()
