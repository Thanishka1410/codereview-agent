# CodeReview Agent 🤖

> **Production-Grade AI-Powered Code Review & Static Analysis CLI Tool**

[![Build Status](https://github.com/Thanishka1410/codereview-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Thanishka1410/codereview-agent/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)

`codereview` is an intelligent, developer-centric CLI tool built to review large software repositories. Combining a **rules-based static analysis engine** (for security vulnerabilities, code quality, and performance) with **multi-provider LLM integrations** (OpenAI GPT-4o, Google Gemini, Anthropic Claude, and an offline mock engine), `codereview` delivers actionable, weighted code assessments directly in your terminal and exports interactive HTML dashboards.

---

```
   ______          __      ____  ___ _   _  _____ _    _  
  / ____/___  ____/ /___  / __ \/ (_) | / /|  ___| |  | | 
 / /   / __ \/ __  / __ \/ /_/ / / /  |/ / | |_  | |  | | 
/ /___/ /_/ / /_/ /  __/ _, _/ / / /|  /  |  _| | |__| | 
\____/\____/\__,_/\___/_/ |_/_/_/_/ |_/   |_|    \____/  
                 AI-Powered Production Code Review CLI Agent v1.0.0
```

---

## 🌟 Key Capabilities & Features

- ⚡ **Multi-Threaded Repository Scanner**: Parallel directory walking (`ThreadPoolExecutor`) with binary detection, symlink safety, glob include/exclude filters, and hash-based incremental caching (`.codereview_cache.json`).
- 🌐 **16+ Language AST & Heuristic Parsing**: Python, JavaScript, TypeScript, React, Java, Kotlin, Swift, Dart, Go, Rust, PHP, C, C++, C#, HTML, CSS.
- 🛡️ **Deep Rule-Based Static Analysis (`app/static_analysis.py`)**: Detects SQL Injection, XSS, Command Injection, Secrets, Unsafe `eval`/`exec`/`pickle`/`subprocess`, Path Traversal, Nested loops $O(n^2)$, string concatenation in loops, deep nesting, and large files.
- 🧠 **Resilient Multi-Provider AI Engine**: OpenAI (`gpt-4o`), Google Gemini (`gemini-1.5-flash`), Anthropic Claude (`claude-3-5-sonnet`), and offline `MockAIProvider` with exponential backoff retries and JSON auto-repair mechanics.
- 📊 **Weighted Quality & Technical Debt Score**: Calculates Security (40%), Maintainability (25%), Code Quality (15%), Performance (10%), Documentation (5%), and Testing (5%) sub-scores alongside Technical Debt estimates (in hours).
- 📈 **Interactive Chart.js HTML Dashboard**: Generates self-contained HTML reports featuring severity pie charts, category sub-score bar charts, interactive severity filters, and top vulnerable files.
- 🤖 **GitHub Actions CI/CD Integration**: Formats GitHub Actions workflow annotations (`::warning file=...::`) and PR review payload comments.
- 🌿 **Git Integration**: Review only modified or staged files using `--diff`.

---

## 🏛️ System Architecture

```
                                  +-------------------+
                                  |  codereview CLI   |
                                  +---------+---------+
                                            |
                         +------------------+------------------+
                         |                                     |
              +----------v----------+               +----------v----------+
              | Parallel File       |               | Rule-Based Static   |
              | Scanner & Cache     |               | Analysis Engine     |
              +----------+----------+               +----------+----------+
                         |                                     |
                         +------------------+------------------+
                                            |
                                  +---------v---------+
                                  | RAG Vector Engine | (Docs & Styleguides)
                                  +---------+---------+
                                            |
                                  +---------v---------+
                                  | AI Provider Layer | (OpenAI / Gemini / Claude / Mock)
                                  +---------+---------+
                                            |
                                  +---------v---------+
                                  | Weighted Scoring  | (40% Sec / 25% Maint / 15% Qual)
                                  +---------+---------+
                                            |
                    +-----------------------+-----------------------+
                    |                       |                       |
          +---------v---------+   +---------v---------+   +---------v---------+
          | Rich Terminal UI  |   | Chart.js HTML     |   | GitHub Actions    |
          | Dashboard         |   | Interactive Report|   | Annotations       |
          +-------------------+   +-------------------+   +-------------------+
```

---

## 📦 Installation

Clone the repository and install locally in editable mode:

```bash
git clone https://github.com/Thanishka1410/codereview-agent.git
cd codereview-agent
pip install -e .
```

Verify installation:

```bash
codereview --version
```

---

## 💻 CLI Reference & Examples

### 1. Standard Project Review
```bash
codereview
```

### 2. Category Filtered Reviews
```bash
# Security audit only
codereview --security

# Performance audit only
codereview --performance

# Architecture & SOLID rules only
codereview --architecture
```

### 3. Report Exporting
```bash
# Generate Chart.js HTML dashboard and Markdown report
codereview --html --markdown

# Output machine-readable JSON report
codereview --json
```

### 4. Git Changed Files Review
```bash
codereview --diff
```

### 5. Quiet Mode for Scripting & CI Pipelines
```bash
codereview --quiet --score
```

### 6. GitHub Actions Workflow Annotations
```bash
codereview --github-annotations --quiet
```

### 7. RAG Documentation-Augmented Review
```bash
codereview --rag --docs-dir ./docs
```

---

## ⚙️ Configuration (`.codereview.toml`)

Customize scan parameters in `.codereview.toml`:

```toml
[codereview]
provider = "mock" # Options: mock, openai, gemini, claude
model = "gpt-4o"
temperature = 0.2
max_tokens = 2000
language = "auto"

[review]
ignored_folders = [
    ".git",
    "venv",
    ".venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    "reports"
]
ignored_files = [
    "package-lock.json",
    "yarn.lock",
    "poetry.lock"
]
max_file_size_kb = 500
target_score = 8.5
fail_on_high_severity = false
```

---

## 🧪 Testing & CI

Run the unit test suite:

```bash
python -m pytest -v
```

---

## ❓ FAQ & Troubleshooting

- **Q: Do I need an API key to run `codereview`?**  
  *A: No. By default, `codereview` uses the built-in offline Mock Engine which runs complete static security and quality checks locally with zero external network requests.*

- **Q: How do I pass an OpenAI or Gemini API key?**  
  *A: Set `export OPENAI_API_KEY="sk-..."` or `export GEMINI_API_KEY="AIzaSy..."` in your environment and run `codereview --provider openai` or `codereview --provider gemini`.*

---

## 📄 License

MIT License © 2026 CodeReview Agent Team
