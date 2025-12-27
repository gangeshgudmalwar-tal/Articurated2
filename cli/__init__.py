"""
CLI Utilities for AI Orchestration v3.0
Governance-First Model | 100 PRU Hard Limit

Tools:
- scope_validator: Classify risk from diff/files
- logic_validator: Validate business logic (placeholder AI)
- adversarial_tests: Generate pytest skeletons
- pru_tracker: Log PRU usage to CSV

All tools: Local-only, no network, structured JSON output
"""

__version__ = "3.0.0"
__all__ = [
    "scope_validator",
    "logic_validator",
    "adversarial_tests",
    "pru_tracker",
]
