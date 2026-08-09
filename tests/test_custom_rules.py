from pathlib import Path
from app.custom_rules import CustomRule, CustomRulesEngine
from app.config import ReviewConfig, load_config


def test_custom_rules_engine_evaluation():
    rule = CustomRule(
        id="no-ip-address",
        category="Security",
        severity="HIGH",
        title="Hardcoded IP Address",
        pattern=r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        message="Hardcoded IP address detected in source code.",
        suggestion="Use domain names or environment variables.",
    )

    engine = CustomRulesEngine(rules=[rule])
    sample_code = "host = '192.168.1.100'\nprint(host)"

    issues = engine.evaluate_file(sample_code, sample_code.splitlines(), "main.py", "python")
    assert len(issues) == 1
    assert issues[0].title == "Hardcoded IP Address"
    assert issues[0].severity == "HIGH"


def test_custom_rules_toml_parsing(tmp_path: Path):
    config_file = tmp_path / ".codereview.toml"
    config_file.write_text(
        """
[codereview]
provider = "mock"

[[rules.custom]]
id = "banned-pickle"
category = "Security"
severity = "HIGH"
title = "Banned Pickle Import"
pattern = "import pickle"
message = "Do not import pickle module."
suggestion = "Use json serialization."
""",
        encoding="utf-8",
    )

    config = load_config(str(config_file))
    assert len(config.custom_rules) == 1
    assert config.custom_rules[0].id == "banned-pickle"
