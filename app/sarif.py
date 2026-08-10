"""
OASIS SARIF v2.1.0 Static Analysis Results Interchange Format export module for GitHub Code Scanning integration.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.ai.base import ReviewIssue


class SARIFGenerator:
    """Generates OASIS SARIF v2.1.0 JSON reports from code review findings."""

    TOOL_NAME = "CodeReview-Agent"
    TOOL_VERSION = "1.1.0"
    INFORMATION_URI = "https://github.com/Thanishka1410/codereview-agent"

    def __init__(self, issues: List[ReviewIssue], target_path: str = "."):
        self.issues = issues
        self.target_path = target_path

    def _severity_to_sarif_level(self, severity: str) -> str:
        """Map CodeReview severity level to SARIF level."""
        sev_upper = severity.upper()
        if sev_upper == "HIGH":
            return "error"
        elif sev_upper == "MEDIUM":
            return "warning"
        return "note"

    def generate_sarif_dict(self) -> Dict[str, Any]:
        """Construct SARIF v2.1.0 dictionary representation."""
        rules_map: Dict[str, Dict[str, Any]] = {}
        results: List[Dict[str, Any]] = []

        for issue in self.issues:
            rule_id = f"CR-{issue.category.upper()}-{hash(issue.title) % 10000:04d}"
            
            if rule_id not in rules_map:
                rules_map[rule_id] = {
                    "id": rule_id,
                    "name": issue.title,
                    "shortDescription": {"text": issue.title},
                    "fullDescription": {"text": issue.description},
                    "defaultConfiguration": {
                        "level": self._severity_to_sarif_level(issue.severity)
                    },
                    "properties": {
                        "category": issue.category,
                        "precision": "high"
                    }
                }

            normalized_path = issue.file_path.replace("\\", "/")

            result_entry = {
                "ruleId": rule_id,
                "level": self._severity_to_sarif_level(issue.severity),
                "message": {
                    "text": f"{issue.description}\n\nSuggested Fix:\n{issue.suggestion}"
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": normalized_path,
                                "uriBaseId": "%SRCROOT%"
                            },
                            "region": {
                                "startLine": max(1, issue.line_number)
                            }
                        }
                    }
                ]
            }
            results.append(result_entry)

        sarif_data = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.TOOL_NAME,
                            "version": self.TOOL_VERSION,
                            "informationUri": self.INFORMATION_URI,
                            "rules": list(rules_map.values()),
                        }
                    },
                    "results": results,
                }
            ],
        }

        return sarif_data

    def export_sarif_file(self, output_path: Path) -> Path:
        """Write SARIF v2.1.0 report to disk as JSON."""
        output_path = Path(output_path).resolve()
        sarif_dict = self.generate_sarif_dict()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(sarif_dict, indent=2), encoding="utf-8")
        return output_path
