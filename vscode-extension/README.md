# CodeReview Agent VS Code & Cursor Extension 🤖

> Real-time inline code review, static analysis, and security linting for VS Code & Cursor IDE.

## Features

- ⚡ **Real-Time Inline Diagnostics**: Runs `codereview` on file save and highlights security vulnerabilities (`HIGH`), bugs (`MEDIUM`), and readability suggestions directly in your editor.
- 🛠️ **Problems Panel Integration**: Populates actionable recommendations and fix suggestions in the native VS Code Problems panel.
- 🎯 **Custom Rules Engine**: Respects project-specific custom static rules configured in `.codereview.toml`.

## Installation & Setup

1. Ensure the `codereview` CLI is installed and available on your system `PATH`:
   ```bash
   pip install -e .
   ```
2. Open the extension in VS Code / Cursor and press `F5` to launch Extension Development Host.

## Extension Settings

This extension contributes the following settings:

* `codereview.executablePath`: Path to the `codereview` CLI executable (default: `codereview`).
* `codereview.runOnSave`: Automatically trigger code review on file save (default: `true`).
