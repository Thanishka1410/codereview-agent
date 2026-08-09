import * as vscode from 'vscode';
import { exec } from 'child_process';

interface ReviewIssue {
    severity: string;
    category: string;
    file_path: string;
    line_number?: number;
    title: string;
    description: string;
    suggestion: string;
    code_example?: string;
}

interface ProjectReviewResult {
    issues: ReviewIssue[];
}

let diagnosticCollection: vscode.DiagnosticCollection;

export function activate(context: vscode.ExtensionContext) {
    diagnosticCollection = vscode.languages.createDiagnosticCollection('codereview');
    context.subscriptions.push(diagnosticCollection);

    // Register manual command
    const reviewCommand = vscode.commands.registerCommand('codereview.runFileReview', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            runCodeReview(editor.document);
        }
    });
    context.subscriptions.push(reviewCommand);

    // Run on save event handler
    vscode.workspace.onDidSaveTextDocument((document) => {
        const config = vscode.workspace.getConfiguration('codereview');
        if (config.get<boolean>('runOnSave', true)) {
            runCodeReview(document);
        }
    });
}

function runCodeReview(document: vscode.TextDocument) {
    const filePath = document.uri.fsPath;
    const config = vscode.workspace.getConfiguration('codereview');
    const executable = config.get<string>('executablePath', 'codereview');

    const cmd = `"${executable}" "${filePath}" --json --quiet`;

    exec(cmd, { maxBuffer: 1024 * 1024 * 5 }, (error, stdout, stderr) => {
        if (error && !stdout) {
            return;
        }

        try {
            const result: ProjectReviewResult = JSON.parse(stdout);
            const diagnostics: vscode.Diagnostic[] = [];

            for (const issue of result.issues) {
                const line = Math.max(0, (issue.line_number || 1) - 1);
                const range = new vscode.Range(line, 0, line, 200);

                let severity = vscode.DiagnosticSeverity.Warning;
                if (issue.severity === 'HIGH') {
                    severity = vscode.DiagnosticSeverity.Error;
                } else if (issue.severity === 'LOW' || issue.severity === 'INFO') {
                    severity = vscode.DiagnosticSeverity.Information;
                }

                const message = `[${issue.category}] ${issue.title}\n\n${issue.description}\n\nFix: ${issue.suggestion}`;
                const diagnostic = new vscode.Diagnostic(range, message, severity);
                diagnostic.source = 'CodeReview Agent';

                diagnostics.push(diagnostic);
            }

            diagnosticCollection.set(document.uri, diagnostics);

        } catch (e) {
            // Ignore JSON parse errors
        }
    });
}

export function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.clear();
        diagnosticCollection.dispose();
    }
}
