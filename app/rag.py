import math
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents a chunk of indexed project documentation."""
    chunk_id: str
    file_path: str
    heading: str
    text: str


class TFIDFVectorIndex:
    """Pure-Python TF-IDF & Cosine Similarity Vector Index."""

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.tfidf_vectors: List[Dict[str, float]] = []

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercased alpha-numeric terms and expand code keywords."""
        raw_tokens = re.findall(r'\b[a-zA-Z0-9_]+\b', text.lower())
        expanded = list(raw_tokens)

        # Domain mapping for code-to-documentation context retrieval
        code_synonyms = {
            "select": ["database", "sql", "query"],
            "insert": ["database", "sql", "query"],
            "update": ["database", "sql", "query"],
            "delete": ["database", "sql", "query"],
            "password": ["credentials", "secret", "security"],
            "api_key": ["credentials", "secret", "security"],
            "eval": ["code", "execution", "security"],
            "exec": ["code", "execution", "security"],
        }
        for token in raw_tokens:
            if token in code_synonyms:
                expanded.extend(code_synonyms[token])

        return expanded

    def fit_transform(self, chunks: List[DocumentChunk]):
        """Build TF-IDF matrix for all document chunks."""
        self.chunks = chunks
        if not chunks:
            return

        doc_count = len(chunks)
        term_doc_freq: Dict[str, int] = {}
        doc_term_freqs: List[Dict[str, float]] = []

        # 1. Compute Term Frequency (TF) for each document
        for chunk in chunks:
            tokens = self._tokenize(chunk.heading + " " + chunk.text)
            tf: Dict[str, float] = {}
            seen_in_doc = set()

            total_tokens = max(1, len(tokens))
            for token in tokens:
                tf[token] = tf.get(token, 0.0) + 1.0
                if token not in seen_in_doc:
                    seen_in_doc.add(token)
                    term_doc_freq[token] = term_doc_freq.get(token, 0) + 1

            # Normalize TF
            for k in tf:
                tf[k] = tf[k] / total_tokens

            doc_term_freqs.append(tf)

        # 2. Compute Inverse Document Frequency (IDF)
        self.idf = {
            term: math.log((1.0 + doc_count) / (1.0 + df)) + 1.0
            for term, df in term_doc_freq.items()
        }

        # 3. Compute TF-IDF vectors
        self.tfidf_vectors = []
        for tf in doc_term_freqs:
            vector: Dict[str, float] = {}
            for term, val in tf.items():
                vector[term] = val * self.idf.get(term, 1.0)
            self.tfidf_vectors.append(vector)

    def search(self, query: str, top_k: int = 3) -> List[Tuple[DocumentChunk, float]]:
        """Compute cosine similarity between query vector and indexed document vectors."""
        if not self.chunks or not self.tfidf_vectors:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        # Compute Query TF-IDF
        query_tf: Dict[str, float] = {}
        total_tokens = len(tokens)
        for t in tokens:
            query_tf[t] = query_tf.get(t, 0.0) + 1.0
        for t in query_tf:
            query_tf[t] = (query_tf[t] / total_tokens) * self.idf.get(t, 1.0)

        query_norm = math.sqrt(sum(v * v for v in query_tf.values()))
        if query_norm == 0:
            return []

        scores: List[Tuple[int, float]] = []
        for idx, doc_vec in enumerate(self.tfidf_vectors):
            dot_product = sum(query_tf[t] * doc_vec[t] for t in query_tf if t in doc_vec)
            doc_norm = math.sqrt(sum(v * v for v in doc_vec.values()))

            if doc_norm > 0:
                similarity = dot_product / (query_norm * doc_norm)
            else:
                similarity = 0.0

            scores.append((idx, similarity))

        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:top_k]:
            if score > 0.01:
                results.append((self.chunks[idx], score))

        return results


class RAGEngine:
    """RAG Engine for indexing project documentation and retrieving contextual guidance."""

    def __init__(self):
        self.index = TFIDFVectorIndex()
        self.is_indexed = False

    def chunk_markdown_file(self, file_path: Path, relative_path: str) -> List[DocumentChunk]:
        """Split a Markdown documentation file by headings (# ## ###) into semantic chunks."""
        chunks: List[DocumentChunk] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            return chunks

        lines = content.splitlines()
        current_heading = "General Overview"
        current_lines: List[str] = []

        chunk_idx = 0
        for line in lines:
            if not line.startswith("#"):
                current_lines.append(line)
                continue

            if current_lines:
                text_block = "\n".join(current_lines).strip()
                if text_block:
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{relative_path}#{chunk_idx}",
                            file_path=relative_path,
                            heading=current_heading,
                            text=text_block,
                        )
                    )
                    chunk_idx += 1
                current_lines = []
            current_heading = line.lstrip("#").strip()

        if current_lines:
            text_block = "\n".join(current_lines).strip()
            if text_block:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{relative_path}#{chunk_idx}",
                        file_path=relative_path,
                        heading=current_heading,
                        text=text_block,
                    )
                )

        return chunks

    def index_directory(self, docs_dir: Path) -> int:
        """Scan and index all markdown/text documentation files in docs_dir."""
        if not docs_dir.exists():
            return 0

        all_chunks: List[DocumentChunk] = []
        doc_extensions = {".md", ".markdown", ".txt", ".rst"}

        files_to_scan = []
        if docs_dir.is_file():
            files_to_scan = [docs_dir]
            root = docs_dir.parent
        else:
            files_to_scan = [
                p for p in docs_dir.rglob("*")
                if p.is_file() and p.suffix.lower() in doc_extensions and ".git" not in p.parts
            ]
            root = docs_dir

        for file_path in files_to_scan:
            rel_path = str(file_path.relative_to(root)) if file_path != root else file_path.name
            chunks = self.chunk_markdown_file(file_path, rel_path)
            all_chunks.extend(chunks)

        self.index.fit_transform(all_chunks)
        self.is_indexed = len(all_chunks) > 0
        return len(all_chunks)

    def retrieve_context(self, code_snippet: str, top_k: int = 3) -> str:
        """Retrieve relevant project documentation context for a given code file/snippet."""
        if not self.is_indexed:
            return ""

        matches = self.index.search(code_snippet, top_k=top_k)
        if not matches:
            return ""

        context_blocks = []
        for chunk, score in matches:
            context_blocks.append(
                f"--- [Doc: {chunk.file_path} > {chunk.heading} (Relevance: {score:.2f})] ---\n{chunk.text}"
            )

        return "\n\n".join(context_blocks)
