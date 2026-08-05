from app.context import CodeContextBuilder

def test_code_summarizer():
    builder = CodeContextBuilder()
    long_code = "\n".join([f"line_{i} = {i}" for i in range(200)])
    summarized = builder.summarize_code(long_code, "python", max_chars=500)
    assert "omitted" in summarized

def test_ast_signature_extraction():
    builder = CodeContextBuilder()
    sample_py = """
class UserEngine:
    def login(self, username, password):
        pass
"""
    sigs = builder.extract_python_signatures(sample_py)
    assert "class UserEngine:" in sigs
    assert "def login(self, username, password):" in sigs
