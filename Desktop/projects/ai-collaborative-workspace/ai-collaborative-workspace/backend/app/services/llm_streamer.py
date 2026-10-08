import os
from typing import AsyncGenerator
from openai import AsyncOpenAI


class LLMStreamerService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o-mini"  # Fast, highly performant streaming model

    async def stream_rag_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Async generator yielding SSE-formatted data chunks from the LLM."""
        if not self.client:
            # Mock fallback stream for local testing without an API key
            mock_tokens = [
                "Based ",
                "on ",
                "your ",
                "document ",
                "context, ",
                "here ",
                "is ",
                "the ",
                "answer ",
                "you ",
                "requested...",
            ]
            for token in mock_tokens:
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
            return

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI document assistant."},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                temperature=0.3,
            )

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    lines = content.splitlines() or [""]
                    yield "".join(f"data: {line}\n" for line in lines) + "\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"


llm_streamer = LLMStreamerService()
