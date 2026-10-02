import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    # Vector column storing 1536-dimensional embeddings
    embedding = Column(Vector(1536), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to Document model
    document = relationship("Document", back_populates="chunks")