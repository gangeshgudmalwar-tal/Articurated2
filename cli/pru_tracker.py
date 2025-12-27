#!/usr/bin/env python3
"""
PRU Tracker CLI - Usage Logging
Local-only | CSV append | Structured tracking

Usage:
  python cli/pru_tracker.py --agent scope_validator --model gpt-4o-mini --pru 8 --context "PR-123"
  python cli/pru_tracker.py --report today
  python cli/pru_tracker.py --report session
"""

import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


LOG_FILE = Path("logs/pru_usage.csv")
LOG_FIELDS = ["date", "time", "agent", "model", "pru_cost", "context", "session_id"]


def ensure_log_file():
    """Ensure log directory and file exist with headers."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if not LOG_FILE.exists():
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
            writer.writeheader()


def log_usage(
    agent: str,
    model: str,
    pru_cost: int,
    context: str = "",
    session_id: Optional[str] = None
) -> Dict:
    """
    Log PRU usage to CSV file.
    
    Returns confirmation with timestamp and running total.
    """
    ensure_log_file()
    
    now = datetime.now()
    entry = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "agent": agent,
        "model": model,
        "pru_cost": pru_cost,
        "context": context,
        "session_id": session_id or now.strftime("%Y%m%d-%H")
    }
    
    # Append to CSV
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        writer.writerow(entry)
    
    # Calculate running total
    total = calculate_total()
    
    return {
        "status": "logged",
        "timestamp": f"{entry['date']} {entry['time']}",
        "pru_logged": pru_cost,
        "session_total": total["session"],
        "daily_total": total["daily"],
        "budget_status": check_budget_status(total)
    }


def calculate_total(session_id: Optional[str] = None, date: Optional[str] = None) -> Dict:
    """Calculate PRU totals from log file."""
    if not LOG_FILE.exists():
        return {"session": 0, "daily": 0, "all_time": 0}
    
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_session = session_id or now.strftime("%Y%m%d-%H")
    
    session_total = 0
    daily_total = 0
    all_time_total = 0
    
    with open(LOG_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pru = int(row["pru_cost"])
            all_time_total += pru
            
            if row["date"] == today:
                daily_total += pru
            
            if row["session_id"] == current_session:
                session_total += pru
    
    return {
        "session": session_total,
        "daily": daily_total,
        "all_time": all_time_total
    }


def check_budget_status(totals: Dict) -> str:
    """Check if usage is within budget limits."""
    SESSION_LIMIT = 100
    DAILY_LIMIT = 500
    ALERT_THRESHOLD = 75  # 75% of session limit
    
    if totals["session"] >= SESSION_LIMIT:
        return "EXCEEDED"
    elif totals["session"] >= ALERT_THRESHOLD:
        return "WARNING"
    else:
        return "OK"


def generate_report(period: str = "today") -> Dict:
    """Generate usage report."""
    if not LOG_FILE.exists():
        return {
            "status": "no_data",
            "message": "No usage logs found"
        }
    
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_session = now.strftime("%Y%m%d-%H")
    
    entries = []
    with open(LOG_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if period == "today" and row["date"] == today:
                entries.append(row)
            elif period == "session" and row["session_id"] == current_session:
                entries.append(row)
            elif period == "all":
                entries.append(row)
    
    # Aggregate by agent
    agent_totals = {}
    for entry in entries:
        agent = entry["agent"]
        pru = int(entry["pru_cost"])
        if agent not in agent_totals:
            agent_totals[agent] = {"count": 0, "total_pru": 0}
        agent_totals[agent]["count"] += 1
        agent_totals[agent]["total_pru"] += pru
    
    totals = calculate_total()
    
    return {
        "status": "success",
        "period": period,
        "entries_count": len(entries),
        "totals": totals,
        "budget_status": check_budget_status(totals),
        "by_agent": agent_totals,
        "budget_limits": {
            "session": 100,
            "daily": 500,
            "alert_threshold": 75
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="PRU Tracker - Log and report PRU usage"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Log command
    log_parser = subparsers.add_parser("log", help="Log PRU usage")
    log_parser.add_argument("--agent", required=True, help="Agent name")
    log_parser.add_argument("--model", required=True, help="Model name")
    log_parser.add_argument("--pru", type=int, required=True, help="PRU cost")
    log_parser.add_argument("--context", default="", help="Context/description")
    log_parser.add_argument("--session", help="Session ID (auto-generated if omitted)")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate usage report")
    report_parser.add_argument(
        "--period",
        choices=["session", "today", "all"],
        default="today",
        help="Report period"
    )
    
    # Backwards compatibility: if no subcommand, treat as log
    if len(sys.argv) > 1 and sys.argv[1] not in ["log", "report", "-h", "--help"]:
        sys.argv.insert(1, "log")
    
    args = parser.parse_args()
    
    if args.command == "report":
        result = generate_report(args.period)
        print(json.dumps(result, indent=2))
    elif args.command == "log":
        result = log_usage(
            agent=args.agent,
            model=args.model,
            pru_cost=args.pru,
            context=args.context,
            session_id=getattr(args, 'session', None)
        )
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
