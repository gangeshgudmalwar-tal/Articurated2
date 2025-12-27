#!/usr/bin/env python3
"""
Scope Validator CLI - Risk Classification
No network | Local-only | Structured JSON output

Usage:
  python cli/scope_validator.py --diff git.diff
  python cli/scope_validator.py --files app/services/state_machine.py
  echo "diff summary" | python cli/scope_validator.py --stdin
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional


def classify_risk(
    files_changed: List[str],
    lines_changed: int,
    diff_content: Optional[str] = None
) -> Dict:
    """
    Classify change risk based on deterministic rules.
    
    Returns: {
        "risk_level": "TRIVIAL|LOW|MEDIUM|HIGH|CRITICAL",
        "route_to": "copilot_only|logic_validator|adversarial_test",
        "estimated_pru": int,
        "justification": str,
        "details": {...}
    }
    """
    # Deterministic classification rules
    risk_indicators = {
        "state_machine": ["state_machine.py", "ORDER_TRANSITIONS", "RETURN_TRANSITIONS"],
        "security": ["auth", "security", "password", "token", "jwt"],
        "payment": ["payment", "refund", "transaction"],
        "database": ["alembic", "migration", "models/"],
        "api_critical": ["api/v1/orders", "api/v1/returns"],
    }
    
    # Check for high-risk patterns
    high_risk_patterns = []
    if diff_content:
        content_lower = diff_content.lower()
        for category, patterns in risk_indicators.items():
            if any(p.lower() in content_lower for p in patterns):
                high_risk_patterns.append(category)
    
    # Check files
    for fpath in files_changed:
        fpath_lower = fpath.lower()
        for category, patterns in risk_indicators.items():
            if any(p in fpath_lower for p in patterns):
                high_risk_patterns.append(category)
    
    # Classification logic
    if any(ext in str(files_changed) for ext in [".md", ".txt", ".yml"]) and not high_risk_patterns:
        return {
            "risk_level": "TRIVIAL",
            "route_to": "copilot_only",
            "estimated_pru": 0,
            "justification": "Documentation/config changes only",
            "details": {
                "files_changed": len(files_changed),
                "lines_changed": lines_changed,
                "patterns_detected": []
            }
        }
    
    if lines_changed < 50 and len(files_changed) <= 2 and not high_risk_patterns:
        return {
            "risk_level": "LOW",
            "route_to": "copilot_only",
            "estimated_pru": 0,
            "justification": "Small, isolated change",
            "details": {
                "files_changed": len(files_changed),
                "lines_changed": lines_changed,
                "patterns_detected": []
            }
        }
    
    if high_risk_patterns:
        if "state_machine" in high_risk_patterns or "security" in high_risk_patterns:
            return {
                "risk_level": "HIGH",
                "route_to": "adversarial_test",
                "estimated_pru": 83,  # scope + logic + adversarial
                "justification": f"Critical patterns detected: {', '.join(high_risk_patterns)}",
                "details": {
                    "files_changed": len(files_changed),
                    "lines_changed": lines_changed,
                    "patterns_detected": high_risk_patterns
                }
            }
        else:
            return {
                "risk_level": "MEDIUM",
                "route_to": "logic_validator",
                "estimated_pru": 48,  # scope + logic
                "justification": f"Sensitive areas modified: {', '.join(high_risk_patterns)}",
                "details": {
                    "files_changed": len(files_changed),
                    "lines_changed": lines_changed,
                    "patterns_detected": high_risk_patterns
                }
            }
    
    if lines_changed >= 200 or len(files_changed) >= 10:
        return {
            "risk_level": "MEDIUM",
            "route_to": "logic_validator",
            "estimated_pru": 48,
            "justification": "Large-scale changes require validation",
            "details": {
                "files_changed": len(files_changed),
                "lines_changed": lines_changed,
                "patterns_detected": []
            }
        }
    
    return {
        "risk_level": "LOW",
        "route_to": "copilot_only",
        "estimated_pru": 8,  # scope validation only
        "justification": "Standard change, minimal validation needed",
        "details": {
            "files_changed": len(files_changed),
            "lines_changed": lines_changed,
            "patterns_detected": []
        }
    }


def parse_diff_summary(diff_path: Path) -> Dict:
    """Parse git diff or diff summary file."""
    if not diff_path.exists():
        return {"files_changed": [], "lines_changed": 0, "diff_content": ""}
    
    content = diff_path.read_text()
    files = []
    additions = 0
    deletions = 0
    
    for line in content.split("\n"):
        if line.startswith("+++") or line.startswith("---"):
            # Extract file path
            parts = line.split()
            if len(parts) > 1:
                fpath = parts[1].replace("b/", "").replace("a/", "")
                if fpath not in files and fpath != "/dev/null":
                    files.append(fpath)
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    
    return {
        "files_changed": files,
        "lines_changed": additions + deletions,
        "diff_content": content
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scope Validator - Classify change risk"
    )
    parser.add_argument(
        "--diff",
        type=Path,
        help="Path to git diff file"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="List of changed file paths"
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=0,
        help="Total lines changed"
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read diff from stdin"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=True,
        help="Output as JSON (default)"
    )
    
    args = parser.parse_args()
    
    # Parse input
    if args.stdin:
        diff_content = sys.stdin.read()
        files_changed = []
        lines_changed = diff_content.count("\n")
    elif args.diff:
        diff_data = parse_diff_summary(args.diff)
        files_changed = diff_data["files_changed"]
        lines_changed = diff_data["lines_changed"]
        diff_content = diff_data["diff_content"]
    elif args.files:
        files_changed = args.files
        lines_changed = args.lines
        diff_content = ""
    else:
        print(json.dumps({
            "error": "Must provide --diff, --files, or --stdin",
            "status": "INVALID_INPUT"
        }))
        sys.exit(1)
    
    # Classify risk
    result = classify_risk(files_changed, lines_changed, diff_content)
    
    # Output
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Risk: {result['risk_level']}")
        print(f"Route: {result['route_to']}")
        print(f"PRU: {result['estimated_pru']}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
