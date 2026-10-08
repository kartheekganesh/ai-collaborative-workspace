import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.vector import DocumentChunk
from app.services.embedding_service import embedding_service


class VectorSearchService:
    def __init__(self, top_k: int = 4):
        self.top_k = top_k

    async def retrieve_relevant_chunks(
        self, db: AsyncSession, document_id: uuid.UUID, query: str
    ) -> List[Dict[str, Any]]:
        """
        Converts input query into an embedding vector and performs cosine similarity search
        against document chunks stored in pgvector.
        """
        if not query or not query.strip():
            return []

        # 1. Generate query vector embedding
        query_vector = await embedding_service.get_single_embedding(query)
        if not query_vector:
            return []

        # 2. Execute cosine distance similarity search in pgvector (<=> operator)
        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.chunk_index,
                DocumentChunk.content,
                DocumentChunk.embedding.cosine_distance(query_vector).label("distance"),
            )
            .where(DocumentChunk.document_id == document_id)
            .order_by("distance")
            .limit(self.top_k)
        )

        result = await db.execute(stmt)
        rows = result.all()

        # 3. Format and return context chunks with relevance scores
        retrieved_chunks = []
        for row in rows:
            # Cosine distance ranges from 0 (identical) to 2 (opposite); convert to similarity score
            similarity_score = round(1.0 - (row.distance / 2.0), 4)
            retrieved_chunks.append(
                {
                    "chunk_id": row.id,
                    "chunk_index": row.chunk_index,
                    "content": row.content,
                    "similarity_score": similarity_score,
                    "cosine_distance": round(row.distance, 4),
                }
            )

        return retrieved_chunks


vector_search_service = VectorSearchService(top_k=4)
