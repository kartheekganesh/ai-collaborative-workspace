from app.services.rag_builder import rag_prompt_builder


def test_rag_prompt_includes_context_and_question():
    prompt = rag_prompt_builder.build_context_prompt(
        "What stores vectors?",
        [
            {
                "chunk_index": 0,
                "similarity_score": 0.95,
                "content": "PostgreSQL stores vectors with pgvector.",
            }
        ],
    )

    assert "PostgreSQL stores vectors with pgvector." in prompt
    assert "What stores vectors?" in prompt
    assert "Score: 0.95" in prompt


def test_rag_prompt_handles_no_matching_context():
    prompt = rag_prompt_builder.build_context_prompt("Question?", [])

    assert "Question?" in prompt
    assert "No relevant document sections found." in prompt
