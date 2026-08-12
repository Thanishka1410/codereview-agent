# CodeReview Agent 🤖

> **Production-Grade AI-Powered Code Review, Static Analysis & Technical Debt Analytics CLI Tool**

[![Build Status](https://github.com/Thanishka1410/codereview-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Thanishka1410/codereview-agent/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![Release](https://img.shields.io/badge/release-v1.1.0-brightgreen.svg)](https://github.com/Thanishka1410/codereview-agent/releases)
[![Code Health](codehealth.svg)](https://github.com/Thanishka1410/codereview-agent)

`codereview` is an intelligent, developer-centric CLI tool built to review large software repositories. Combining a **rules-based static analysis engine** with **custom regex rule extensibility**, **Git pre-commit hook automation**, **local SQLite historical trend tracking**, **VS Code / Cursor extension wrappers**, and **multi-provider LLM integrations** (OpenAI GPT-4o, Google Gemini, Anthropic Claude, Local Ollama, and an offline mock engine), `codereview` delivers actionable, weighted code assessments directly in your terminal and exports interactive HTML dashboards.

---

```
  ____ ___  ____  _____ ____  _____  __   __ _____ _____ _        __
 / ___/ _ \|  _ \| ____|  _ \| ____| \ \ / / |_ _| ____| \      / /
| |  | | | | | | |  _| | |_) |  _|    \ V /   | ||  _|  \ \    / / 
| |__| |_| | |_| | |___|  _ <| |___    \ /    | || |___  \ \/\/ /  
 \____\___/|____/|_____|_| \_\_____|    V    |___|_____|  \_/\_/   
                 AI-Powered Production Code Review CLI Agent v1.1.0
```

---

## 🌟 Key Capabilities & Features

- ⚓ **Automated Git Pre-Commit Hook Integration (`codereview install-hook`)**: Installs `.git/hooks/pre-commit` script to enforce strict code quality and security thresholds automatically before commits are finalized.
- 🦙 **Local LLM / Ollama Provider Support**: Run 100% offline AI code reviews using local LLMs (e.g. Llama 3, DeepSeek-Coder, Mistral) via Ollama REST integration (`--provider ollama`).
- 📈 **SQLite Historical Analytics & Trend Tracking (`codereview history`)**: Automatically logs review scores, issue counts, and technical debt in `.codereview_history.db` and renders terminal trend tables.
- ⚙️ **Extensible Custom Rules Engine**: Define custom static analysis rules in `.codereview.toml` enforcing team-specific naming conventions, forbidden patterns, or architectural constraints.
- 💻 **VS Code & Cursor IDE Extension Wrapper**: Instant, inline editor diagnostic warnings powered by `execFile` CLI integration (`vscode-extension/`).
- ⚡ **Multi-Threaded Repository Scanner**: Parallel directory walking (`ThreadPoolExecutor`) with binary detection, symlink safety, glob include/exclude filters, and hash-based incremental caching (`.codereview_cache.json`).
- 🌐 **16+ Language AST & Heuristic Parsing**: Python, JavaScript, TypeScript, React, Java, Kotlin, Swift, Dart, Go, Rust, PHP, C, C++, C#, HTML, CSS.
- 🛡️ **Deep Rule-Based Static Analysis**: Detects SQL Injection, XSS, Command Injection, Hardcoded Secrets, Unsafe `eval`/`exec`/`pickle`/`subprocess`, Path Traversal, Nested loops $O(n^2)$, string concatenation in loops, deep nesting, and large files.
- 🧠 **Resilient Multi-Provider AI Engine**: OpenAI (`gpt-4o`), Google Gemini (`gemini-1.5-flash`), Anthropic Claude (`claude-3-5-sonnet`), Local Ollama (`llama3`), and offline `MockAIProvider` with exponential backoff retries and JSON auto-repair.
- 📊 **Weighted Quality & Technical Debt Score**: Calculates Security (40%), Maintainability (25%), Code Quality (15%), Performance (10%), Documentation (5%), and Testing (5%) sub-scores alongside Technical Debt estimates (in hours).
- 📈 **Interactive Chart.js HTML Dashboard**: Generates self-contained HTML reports featuring severity pie charts, category sub-score bar charts, interactive severity filters, and top vulnerable files.
- 🤖 **GitHub Actions CI/CD Integration**: Formats GitHub Actions workflow annotations (`::warning file=...::`) and PR review payload comments.

---

## 🏛️ System Architecture

```
                                  +-------------------+
                                  |  codereview CLI   |
                                  +---------+---------+
                                            |
           +--------------------------------+--------------------------------+
           |                                |                                |
+----------v----------+          +----------v----------+          +----------v----------+
| Parallel File       |          | Rule & Custom Regex |          | Git Pre-Commit Hook |
| Scanner & Cache     |          | Static Analysis     |          | Manager (hooks.py)  |
+----------+----------+          +----------+----------+          +----------+----------+
           |                                |                                |
           +--------------------------------+--------------------------------+
                                            |
                                  +---------v---------+
                                  | RAG Vector Engine | (Docs & Styleguides)
                                  +---------+---------+
                                            |
                                  +---------v---------+
                                  | AI Provider Layer | (OpenAI / Gemini / Claude / Ollama / Mock)
                                  +---------+---------+
                                            |
                                  +---------v---------+
                                  | SQLite Analytics  | (History & Debt Tracking)
                                  +---------+---------+
                                            |
                    +-----------------------+-----------------------+
                    |                       |                       |
          +---------v---------+   +---------v---------+   +---------v---------+
          | Rich Terminal UI  |   | Chart.js HTML     |   | VS Code / Cursor  |
          | Dashboard & Trend |   | Interactive Report|   | IDE Extension     |
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

### 2. Git Pre-Commit Hook Management
```bash
# Install automated Git pre-commit hook into local repository
codereview install-hook

# Uninstall pre-commit hook
codereview uninstall-hook
```

### 3. Historical Analytics & Health Trends
```bash
# Display recent review history runs and technical debt trend
codereview history

# Display up to 20 historical runs
codereview history --limit 20
```

### 4. Local LLM (Ollama) Code Review
```bash
# Perform 100% offline AI code review using local Ollama model
codereview --provider ollama --model llama3
```

### 5. Category Filtered Reviews
```bash
# Security audit only
codereview --security

# Performance audit only
codereview --performance

# Architecture & SOLID rules only
codereview --architecture
```

### 6. SARIF & SVG Badge Export
```bash
# Export OASIS SARIF v2.1.0 report for GitHub Security / Code Scanning tab
codereview --sarif report.sarif

# Generate SVG health score status badge for README header
codereview --badge codehealth.svg
```

### 7. Report Exporting
```bash
# Generate Chart.js HTML dashboard and Markdown report
codereview --html --markdown

# Output machine-readable JSON report
codereview --json
```

### 7. Git Changed Files Review
```bash
codereview --diff
```

### 8. GitHub Actions Workflow Annotations
```bash
codereview --github-annotations --quiet
```

---

## ⚙️ Configuration (`.codereview.toml`)

Customize scan parameters and custom rules in `.codereview.toml`:

```toml
[codereview]
provider = "mock" # Options: mock, openai, gemini, claude, ollama
model = "gpt-4o"
temperature = 0.2
max_tokens = 2000
language = "auto"
ollama_host = "http://localhost:11434"

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
    "poetry.lock",
    ".codereview_history.db"
]
max_file_size_kb = 500
target_score = 8.5
fail_on_high_severity = false

# Custom Rules Engine Extensibility
[[rules.custom]]
id = "CUST-001"
title = "Banned Print Statements in Production"
pattern = "print\\s*\\("
category = "Quality"
severity = "LOW"
description = "Use structured logger instead of raw stdout print statements."
suggestion = "Replace print() with logger.info() or logger.debug()."

[[rules.custom]]
id = "CUST-002"
title = "Forbidden Legacy Crypto"
pattern = "md5\\(|sha1\\("
category = "Security"
severity = "HIGH"
description = "MD5 and SHA1 are cryptographically broken."
suggestion = "Use SHA256 or bcrypt instead."
```

---

## 🔌 VS Code & Cursor Extension Wrapper

The repository includes a ready-to-publish VS Code / Cursor extension wrapper located in `vscode-extension/`:

```bash
cd vscode-extension
npm install
npm run compile
```

The extension invokes `codereview` asynchronously and populates native VS Code **Problems** diagnostics tab in real-time as you edit code!

---

## 🧪 Testing & CI

Run the unit test suite (21 unit tests covering scanner, custom rules, Ollama provider, SQLite history, and Git hooks):

```bash
python -m pytest -v
```

---

## ❓ FAQ & Troubleshooting

- **Q: How does the Git Pre-Commit Hook work?**  
  *A: Running `codereview install-hook` creates an executable `.git/hooks/pre-commit` script. Whenever you run `git commit`, the hook automatically triggers `codereview --diff` and prevents commits if high-severity vulnerabilities are present.*

- **Q: Do I need an API key for local LLM review?**  
  *A: No. You can run `codereview --provider ollama` with Ollama running locally, or use the default offline Mock Engine with zero network requests.*

- **Q: Where is history stored?**  
  *A: Review runs are saved locally in SQLite database `.codereview_history.db` within your project root.*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
