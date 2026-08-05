# Organization Security & Style Guidelines

## Database Security Guidelines
All database queries MUST use parameterized bindings. String concatenation or format strings in SQL statements are strictly forbidden to prevent SQL injection vulnerabilities.

## Credentials and Secrets Management
Hardcoding API keys, passwords, or tokens in source files is strictly prohibited. All secrets must be stored in secure environment variables or vault secret managers.

## Code Execution Rules
Dynamic code evaluation using `eval()` or `exec()` is strictly banned in all production source files due to high risk of Remote Code Execution (RCE).
