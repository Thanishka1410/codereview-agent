from pathlib import Path
from app.rag import RAGEngine, DocumentChunk, TFIDFVectorIndex
from app.config import ReviewConfig
from app.reviewer import ReviewerEngine

TEST_DOCS_DIR = Path(__file__).parent.parent / "examples" / "sample_project" / "docs"
TEST_PROJECT_DIR = Path(__file__).parent.parent / "examples" / "sample_project"

def test_rag_chunking_and_indexing():
    rag = RAGEngine()
    chunks_count = rag.index_directory(TEST_DOCS_DIR)
    assert chunks_count >= 3
    assert rag.is_indexed is True

def test_rag_similarity_retrieval():
    rag = RAGEngine()
    rag.index_directory(TEST_DOCS_DIR)
    
    query_code = "SELECT * FROM users WHERE id = '" + "user_input" + "'"
    context = rag.retrieve_context(query_code, top_k=2)
    
    assert "Database Security Guidelines" in context or "SQL injection" in context

def test_reviewer_engine_with_rag():
    config = ReviewConfig(provider="mock", use_rag=True, docs_dir=str(TEST_DOCS_DIR))
    engine = ReviewerEngine(config)
    result = engine.run_review(TEST_PROJECT_DIR)
    
    assert result.rag_indexed_chunks >= 3
    assert len(result.issues) > 0
