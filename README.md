# CodeReview Agent 🤖

> **Production-Grade AI-Powered Code Review CLI Tool**

`codereview` is an intelligent, developer-centric CLI tool designed to review entire software codebases directly from your terminal. Built with Python 3.10+, Typer, Rich, and multi-provider AI support (OpenAI GPT-4o, Google Gemini, Anthropic Claude, and an offline rule-engine provider).

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

## 🌟 Key Features

- 🚀 **Terminal-First Workflow**: Run `codereview` inside any software repository.
- ⚡ **Multi-Language Scanner**: Automatically scans Python, JavaScript, TypeScript, React, Java, Go, Rust, C/C++, PHP, HTML, CSS, and C#.
- 🧠 **Multi-Provider AI Engine**: Plug-and-play support for **OpenAI** (`gpt-4o`), **Google Gemini** (`gemini-1.5-flash`), **Anthropic Claude** (`claude-3-5-sonnet`), or an **Offline Mock Engine** for keyless execution.
- 🛡️ **Comprehensive Analysis**: Detects Security Vulnerabilities (SQLi, Secret leaks, RCE), Logic Bugs, Memory Leaks, Code Smells, SOLID violations, and Performance Bottlenecks.
- 📊 **Project Health Score & Debt Estimation**: Computes Security, Maintainability, Code Quality, and Performance scores alongside Cyclomatic Complexity and Technical Debt estimates (in hours).
- 📄 **Multi-Format Report Export**: Generate beautiful HTML, Markdown (`.md`), and JSON reports.
- 🌿 **Git Integration**: Review only modified or staged files using the `--diff` flag.
- 🔌 **Extensible GitHub PR Module**: Built-in payload formatters for GitHub Actions & Pull Request inline review comments.

---

## 🛠️ Tech Stack

- **Core**: Python 3.10+
- **CLI Framework**: Typer & Rich
- **AI Integrations**: OpenAI REST API, Gemini REST API, Claude REST API
- **Configuration**: TOML (`.codereview.toml`) & Environment Variables
- **Testing**: `pytest`

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

## 💡 Usage Examples

### 1. Review Entire Project (Current Folder)
```bash
codereview
```

### 2. Review Specific Subfolder or File
```bash
codereview src/
codereview app/main.py
```

### 3. Show Only Project Health Score
```bash
codereview --score
```

### 4. Show Summary Overview Only
```bash
codereview --summary
```

### 5. Filter Files by Programming Language
```bash
codereview --language python
```

### 6. Review Only Git Changed / Staged Files
```bash
codereview --diff
```

### 7. Export Markdown and HTML Reports
```bash
codereview --markdown --html
```
*Reports are exported automatically to `reports/codereview_report.html` and `reports/codereview_report.md`.*

### 8. Output Raw JSON Report
```bash
codereview --json
```

### 9. Specify Custom AI Provider or Model
```bash
codereview --provider openai --model gpt-4o
codereview --provider gemini --model gemini-1.5-flash
codereview --provider claude --model claude-3-5-sonnet
```

---

## ⚙️ Configuration (`.codereview.toml`)

Create a `.codereview.toml` file in your repository root to configure default preferences:

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
    ".pytest_cache"
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

### API Key Environment Variables

Provide your API keys via standard environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Google Gemini
export GEMINI_API_KEY="AIzaSy..."

# Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## 🏛️ Project Architecture

```
codereview-agent/
│
├── app/
│   ├── cli.py             # Typer CLI Entrypoint (`codereview`)
│   ├── config.py          # Configuration parser (.codereview.toml + env vars)
│   ├── scanner.py         # File tree scanner & language detector
│   ├── utils.py           # AST parsing, cyclomatic complexity & Git integration
│   ├── reviewer.py        # Core Engine: Analysis + AI query + Health Scoring
│   ├── formatter.py       # Rich terminal UI, badges, panels & tables
│   ├── report.py          # Exporters: JSON, Markdown, HTML reports
│   ├── prompts.py         # Specialized prompt templates
│   ├── github.py          # GitHub PR & inline review comment module
│   └── ai/                # AI Provider abstraction layer
│       ├── base.py        # Abstract AI Provider base class
│       ├── openai_provider.py
│       ├── gemini_provider.py
│       ├── claude_provider.py
│       ├── mock_provider.py
│       └── factory.py     # Provider instantiation factory
│
├── tests/                 # Pytest unit tests
│   └── test_suite.py
│
├── examples/              # Sample vulnerable project for testing
│   └── sample_project/
│       ├── sample_vulnerable.py
│       └── sample_script.js
│
├── .codereview.toml       # Default configuration file template
├── pyproject.toml         # Build system definition
├── requirements.txt       # Project dependencies
└── README.md
```

---

## 🧪 Running Tests

To run the test suite:

```bash
python -m pytest
```

---

## 🚀 Future Roadmap & Extensibility

- [ ] **Local LLM Support**: Integration with Ollama for 100% air-gapped local AI reviews (`codereview --provider ollama --model llama3`).
- [ ] **RAG-based Documentation Context**: Index local `.md` docs and architecture decisions for contextual reviews.
- [ ] **GitHub Actions CI Workflow**: Fail build steps automatically if project health score drops below threshold.
- [ ] **VS Code Extension**: Inline review highlighting directly inside the editor.

---

## 📄 License

MIT License © 2026 CodeReview Agent Team
