from pathlib import Path
from app.static_analysis import StaticAnalyzer

def test_security_rules_detection():
    analyzer = StaticAnalyzer()
    sample_code = """
import sqlite3
import os
import subprocess

API_KEY = "sk-1234567890abcdef1234567890abcdef"

def query_user(user_id):
    query = "SELECT * FROM users WHERE id = '" + str(user_id) + "'"
    eval("print('unsafe')")
    subprocess.run("ls", shell=True)
    os.system("echo unsafe")
"""
    issues = analyzer.analyze_file(Path("test.py"), "test.py", sample_code, "python")
    categories = [i.category for i in issues]
    severities = [i.severity for i in issues]

    assert "Security" in categories
    assert "HIGH" in severities
    assert len(issues) >= 3

def test_performance_rules_detection():
    analyzer = StaticAnalyzer()
    sample_code = """
def nested_loop_example(items):
    for i in items:
        for j in items:
            for k in items:
                print(i, j, k)
"""
    issues = analyzer.analyze_file(Path("test.py"), "test.py", sample_code, "python")
    titles = [i.title for i in issues]
    assert any("Nested Loop" in t for t in titles)
