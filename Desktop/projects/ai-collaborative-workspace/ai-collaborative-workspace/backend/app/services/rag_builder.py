from typing import List, Dict, Any


class RAGPromptBuilder:
    @staticmethod
    def build_context_prompt(user_query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Assembles retrieved chunks into a formatted context block for LLM prompts."""
        if not retrieved_chunks:
            return f"User Question: {user_query}\n\nContext: No relevant document sections found."

        context_str = "\n\n---\n\n".join(
            [
                f"[Chunk {c['chunk_index']} | Score: {c['similarity_score']}]\n{c['content']}"
                for c in retrieved_chunks
            ]
        )

        prompt = f"""You are an intelligent assistant for a collaborative workspace document.
Use the following retrieved context passages to answer the user's question accurately.
If the context does not contain enough information, state what is missing.

=== RETRIEVED CONTEXT ===
{context_str}

=== USER QUESTION ===
{user_query}
"""
        return prompt


rag_prompt_builder = RAGPromptBuilder()
