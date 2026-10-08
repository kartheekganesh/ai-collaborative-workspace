from typing import List


class TextChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """Splits document content into overlapping word-based chunks."""
        if not text or not text.strip():
            return []

        words = text.split()
        if len(words) <= self.chunk_size:
            return [text]

        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i : i + self.chunk_size]
            chunks.append(" ".join(chunk_words))
            # Move forward by chunk_size minus overlap
            i += self.chunk_size - self.chunk_overlap

        return chunks


text_chunker = TextChunker(chunk_size=300, chunk_overlap=40)
