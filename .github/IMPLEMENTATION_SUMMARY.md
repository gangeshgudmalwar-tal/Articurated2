# AI Agent Orchestration Framework v3.0
## Governance-First Architecture - Implementation Summary

**Version:** 3.0  
**Date:** December 2025  
**Status:** Production Ready  
**Breaking Changes:** Yes (from v2.0)

---

## Executive Summary

This document summarizes the complete refactoring of the AI-assisted SDLC orchestration framework from a multi-agent, skill-based model (v2.0) to a governance-first, cost-bounded architecture (v3.0).

### Key Changes

| Aspect | v2.0 | v3.0 | Impact |
|--------|------|------|--------|
| **Agents** | 5 agents (300 PRU) | 4 agents (100 PRU) | -67% cost |
| **Default Execution** | AI-first | Copilot + static tools | 0 PRU default |
| **Routing** | Skill-based | Risk-based | Deterministic |
| **Human Gates** | Optional | Mandatory | Non-negotiable |
| **MCP Access** | Full repository | Sandboxed | Security-first |
| **Budget Model** | Per-agent allocation | Hard lifecycle limit | Predictable |

---

## File Structure (v3.0)

```
.github/
├── GOVERNANCE.md                 # NEW: Comprehensive governance policy
├── skills_v3.yml                 # NEW: Consolidated skill definitions
├── agents/
│   ├── README.md                 # UPDATED: v3.0 governance model
│   ├── orchestrator_v3.yml       # UPDATED: 4-agent coordinator
│   ├── validation_v3.yml         # NEW: Static-first validation
│   └── [DEPRECATED]
│       ├── orchestrator.yml      # v2.0 multi-agent
│       ├── analysis.yml
│       ├── implementation.yml
│       ├── validation.yml
│       └── deployment.yml
└── skills/
    └── README.md                 # UPDATED: v3.0 skill governance
```

---

## Architecture Overview

### Agent Structure (4 Agents)

```
┌─────────────────────────────────────────────┐
│         PRU Governance Agent (0 PRU)        │
│         ├─ Budget tracking                  │
│         ├─ Alert on >75% usage              │
│         └─ Block on exceed                  │
└─────────────────────────────────────────────┘
                     ▲
                     │ Reports to
                     │
┌─────────────────────────────────────────────┐
│      Orchestrator (0-15 PRU routing)        │
│      ├─ Risk classification                 │
│      ├─ Deterministic routing               │
│      └─ Budget enforcement                  │
└─────────────────────────────────────────────┘
        ▼             ▼              ▼
┌────────────┐ ┌────────────┐ ┌──────────────┐
│   Scope    │ │   Logic    │ │ Adversarial  │
│ Validator  │ │   Risk     │ │     Test     │
│  (8 PRU)   │ │ Validator  │ │    Agent     │
│ GPT-4o-mini│ │  (40 PRU)  │ │   (35 PRU)   │
│            │ │   GPT-4o   │ │    GPT-4o    │
└────────────┘ └────────────┘ └──────────────┘
```

### Execution Model

```
Default Path (0 PRU):
Commit → Static Tools (pytest, bandit, ruff, mypy) → Merge (if pass)
         └─ Copilot code generation

Risk-Triggered Path (8-83 PRU):
Commit → Scope Validator (8 PRU) → Risk ≥ MEDIUM?
         ├─ NO → Static Tools → Merge
         └─ YES → Logic Validator (40 PRU) → Risk ≥ HIGH?
                  ├─ NO → Merge (if pass)
                  └─ YES → Adversarial Tests (35 PRU) → Merge (if pass)
```

---

## Budget Allocation

### Cost by PR Type

| PR Type | Agents Invoked | PRU Cost | Example |
|---------|----------------|----------|---------|
| **Trivial** | None | 0 | Typo fix, whitespace, docs |
| **Simple** | Scope only | 8 | <50 lines, tests pass, follows patterns |
| **Medium** | Scope + Logic | 48 | 50-200 lines, business logic changes |
| **High Risk** | All 3 validators | 83 | State machine, security, payment logic |
| **Critical** | Full budget | ≤100 | Production incident, security vulnerability |

### Budget Distribution

```yaml
total_budget: 100
agents:
  scope_validator: 8        # Auto-triggered on commit/PR
  logic_risk_validator: 40  # Triggered if risk ≥ MEDIUM
  adversarial_test_agent: 35  # Triggered if risk ≥ HIGH
  emergency_reserve: 15     # Reserved for CRITICAL incidents
  pru_governance: 0         # Accounting only

alert_threshold: 75  # 75% budget consumed
hard_limit: 100      # Cannot exceed
```

---

## Risk Classification

### 5-Point Scale

```
TRIVIAL (0 PRU):
├─ Documentation-only (*.md)
├─ Whitespace/formatting
├─ Comment updates
└─ Dependabot PRs
→ Action: Skip AI, static tools only

LOW (8 PRU):
├─ < 50 lines changed
├─ Tests pass
├─ Coverage maintained
└─ Follows existing patterns
→ Action: Scope validator + static tools

MEDIUM (48 PRU):
├─ 50-200 lines changed
├─ Business logic modifications
├─ Database schema changes
└─ API endpoint modifications
→ Action: Scope + logic validators + static tools

HIGH (83 PRU):
├─ > 200 lines changed
├─ State machine transitions modified
├─ Payment/refund logic changes
└─ Security-critical paths
→ Action: All validators + adversarial tests + static tools

CRITICAL (100 PRU):
├─ Production incident
├─ Security vulnerability
├─ Data corruption risk
└─ Payment gateway failure
→ Action: Emergency protocol, all agents, immediate escalation
```

### Detection Logic

```python
def classify_risk(pr_data):
    # Documentation-only
    if all(f.endswith('.md') for f in pr_data.files):
        return "TRIVIAL"
    
    # State machine check
    if "state_machine.py" in pr_data.files:
        return "HIGH"
    
    # Security-critical paths
    if any(path in str(pr_data.files) for path in ["payment", "auth", "security"]):
        return "HIGH"
    
    # Line count
    if pr_data.lines_changed < 50:
        return "LOW"
    elif pr_data.lines_changed < 200:
        return "MEDIUM"
    else:
        return "HIGH"
```

---

## Human Gates (Mandatory)

### Gate Definitions

```yaml
GATE-001: PR Review
  trigger: every_pr
  approver: team_lead OR tech_lead
  bypass: NEVER
  timeout: 24h
  escalation: tech_lead → manager

GATE-002: Production Deployment
  trigger: deploy_to_production
  approvers: tech_lead AND ops_lead
  bypass: NEVER (even for emergencies)
  timeout: 4h
  escalation: ops_lead → manager
```

### Override Protocol (Emergency Only)

```yaml
override_conditions:
  trigger: critical_incident
  approver: engineering_manager
  documentation: required (incident report)
  audit: immediate
  post_mortem: within_24h
```

---

## MCP Sandboxing

### Allowed Operations

```yaml
github_mcp:
  read: [pr_metadata, file_contents, commit_history, diff]
  write: FORBIDDEN

filesystem_mcp:
  read: [repo_root/**]
  write: FORBIDDEN
  exec: FORBIDDEN

database_mcp:
  read: [schema_only, migrations_only]
  write: FORBIDDEN
  production: FORBIDDEN
```

### Forbidden Operations

- ❌ Network access
- ❌ External APIs
- ❌ System commands
- ❌ Credential access
- ❌ Write operations
- ❌ Production database

---

## Skip Rules (When NOT to Run Agents)

### Never Validate

```yaml
skip_patterns:
  - dependabot/**         # Automated dependency updates
  - *.md (all files)      # Documentation-only changes
  - whitespace_only       # Formatting-only changes
  - comment_only          # Non-functional comments
```

### Skip Logic Validator (Risk < MEDIUM)

```yaml
skip_conditions:
  - risk_level: TRIVIAL OR LOW
  - tests_passing: true
  - coverage_maintained: true
  - no_state_machine_changes: true
```

### Skip Adversarial Tests (Risk < HIGH)

```yaml
skip_conditions:
  - risk_level: TRIVIAL, LOW, MEDIUM
  - no_security_implications: true
  - no_payment_logic: true
  - no_auth_changes: true
```

---

## Triggers

### Automatic

```yaml
on_commit:
  - scope_validator (8 PRU, conditional)
  - static_tools (0 PRU, always)

on_pr:
  - scope_validator (8 PRU, conditional)
  - static_tools (0 PRU, always)

on_risk_detected:
  - logic_risk_validator (40 PRU, if risk ≥ MEDIUM)
  - adversarial_test_agent (35 PRU, if risk ≥ HIGH)
```

### Manual Only

```yaml
deployment:
  trigger: manual
  gate: GATE-002
  approvers: [tech_lead, ops_lead]

rollback:
  trigger: manual
  gate: GATE-002
  emergency_override: engineering_manager

hotfix:
  trigger: manual
  gate: expedited_review
  post_deploy_audit: required
```

---

## Fallback Behavior

| Condition | Action | Fallback | Notification |
|-----------|--------|----------|--------------|
| Agent failure | Block merge | Manual review | Immediate |
| Budget exceeded | Halt AI | Static tools only | Immediate |
| Model unavailable | Queue retry | Manual review | 15m delay |
| MCP violation | Block + suspend | Security review | Immediate |
| Gate timeout (24h) | Auto-close PR | Escalate | Per policy |

---

## Output Standards

### Required Format

```yaml
agent_output:
  risk_level: TRIVIAL|LOW|MEDIUM|HIGH|CRITICAL
  pru_used: integer
  validation_status: PASS|FAIL|UNCERTAIN
  issues:
    - id: string
      severity: LOW|MEDIUM|HIGH|CRITICAL
      description: string
      remediation: string
  recommendations: array_of_strings
  confidence: 0.0-1.0
  timestamp: iso8601_utc
```

### Forbidden Content

- ❌ Verbose explanations
- ❌ Apologetic language ("I'm sorry, I cannot...")
- ❌ Uncertainty hedging ("It seems like...", "Maybe...")
- ❌ Marketing language
- ❌ Emoji
- ❌ Colloquial language

---

## Migration Guide (v2.0 → v3.0)

### Deprecated Components

```yaml
removed:
  - orchestrator.yml (v2.0)     # 25 PRU
  - analysis.yml                 # 80 PRU
  - implementation.yml           # 70 PRU
  - validation.yml (v1.0)        # 60 PRU
  - deployment.yml               # 40 PRU
  - skills/*.yml (modular)       # 26+ skills

total_removed: 275+ PRU budget
```

### New Components

```yaml
added:
  - orchestrator_v3.yml          # 4-agent coordinator
  - validation_v3.yml            # Static-first validation
  - skills_v3.yml                # Consolidated skills
  - GOVERNANCE.md                # Comprehensive policy

total_budget: 100 PRU (hard limit)
```

### Breaking Changes

```yaml
breaking_changes:
  - Agent invocation API changed
  - Budget model changed (per-agent → lifecycle)
  - MCP access restricted (full → sandboxed)
  - Human gates mandatory (optional → required)
  - Output format standardized (free-form → structured)
  - Default execution model (AI-first → Copilot+static)
```

### Migration Steps

1. **Read new documentation:**
   - orchestrator_v3.yml (agent definitions)
   - GOVERNANCE.md (risk classification, skip rules)
   - skills_v3.yml (skill mappings)

2. **Update CI/CD configuration:**
   - Replace old agent invocations
   - Add budget tracking
   - Implement human gates

3. **Train team:**
   - New risk classification rules
   - Budget enforcement policy
   - Skip rules (when NOT to run)

4. **Monitor metrics:**
   - Budget utilization (target: 50-75%)
   - Skip rate (target: >60%)
   - False positive rate (target: <5%)

---

## Quick Start Guide

### For Developers

```bash
# Typical workflow (0 PRU for simple changes)
git commit -m "fix: typo in order service"
# Auto-triggers: static tools only (tests, linting, security)
# No AI invocation needed

# Medium change (8-48 PRU)
git commit -m "feat: add tax calculation to orders"
# Auto-triggers: scope validator (8 PRU) → detects business logic
# → Escalates to logic validator (40 PRU)

# High risk change (83 PRU)
git commit -m "feat: modify state machine transitions"
# Auto-triggers: scope validator (8 PRU) → detects state machine
# → Escalates to logic validator (40 PRU)
# → Escalates to adversarial tests (35 PRU)
```

### Check Budget

```bash
@orchestrator pru-report --session

Output:
Session PRU Usage: 48 / 100
Alert Threshold: 75 PRU (27 PRU remaining)
Emergency Reserve: 15 PRU (available)
```

### Force Manual Review

```bash
@orchestrator require-human-review --reason="complex_change"
```

---

## Monitoring & Metrics

### Key Metrics

```yaml
tracked_metrics:
  budget_utilization: pru_used / pru_allocated
  skip_rate: skipped_prs / total_prs
  human_gate_rate: gated_prs / total_prs
  false_positive_rate: incorrect_escalations / total_escalations
  avg_validation_time: sum(validation_times) / count

success_targets:
  budget_utilization: 50-75%
  skip_rate: > 60%
  human_gate_rate: < 20%
  false_positive_rate: < 5%
  avg_validation_time: < 10m
```

### Dashboards

```yaml
real_time_dashboard:
  - current_session_usage
  - remaining_budget
  - risk_distribution
  - agent_invocation_counts

weekly_report:
  - total_prs_processed
  - budget_utilization_trend
  - skip_rate_trend
  - escalation_accuracy

monthly_analysis:
  - cost_savings_vs_v2
  - false_positive_analysis
  - policy_effectiveness
  - recommendation_for_tuning
```

---

## Support & Escalation

### Contact Points

```yaml
tier_1_support:
  contact: team_lead
  response_sla: 4h
  for: [budget_questions, skip_rule_clarification]

tier_2_support:
  contact: tech_lead
  response_sla: 1h
  for: [policy_exceptions, risk_classification_disputes]

tier_3_support:
  contact: engineering_manager
  response_sla: 30m
  for: [emergency_overrides, security_incidents]
```

### Incident Response

```yaml
incident_protocol:
  detection: automated_monitoring
  triage: tech_lead (15m SLA)
  mitigation: team_effort
  post_mortem: within_24h
  documentation: incident_log
  policy_review: if_applicable
```

---

## Appendix: Complete File Manifest

### Core Files (v3.0)

```
.github/
├── GOVERNANCE.md (5.8 KB)        # Comprehensive governance policy
├── skills_v3.yml (2.1 KB)        # Consolidated skill definitions
├── agents/
│   ├── README.md (4.2 KB)        # Agent architecture overview
│   ├── orchestrator_v3.yml (6.3 KB)  # 4-agent coordinator
│   └── validation_v3.yml (3.1 KB)    # Static-first validation
└── skills/
    └── README.md (2.8 KB)        # Skills governance overview
```

### Documentation Files

```
Updated_PRD.md                   # Business requirements
TECHNICAL_PRD.md                 # Technical specification
WORKFLOW_DESIGN.md               # State machines & workflows
API-SPECIFICATION.yml            # API contracts
.github/docs/TDD_FRAMEWORK.md    # Testing strategy
```

### Total Documentation: ~30 KB (v3.0 core)

---

## Success Criteria

### Quantitative

- ✅ 100 PRU hard limit enforced
- ✅ 0 PRU default execution path
- ✅ Deterministic risk classification
- ✅ Mandatory human gates
- ✅ Sandboxed MCP access

### Qualitative

- ✅ Clear, unambiguous governance rules
- ✅ Predictable cost model
- ✅ Fail-safe fallback behavior
- ✅ Comprehensive audit trail
- ✅ Engineering-grade documentation

---

## Next Steps

1. **Implementation:** Deploy orchestrator_v3 to CI/CD
2. **Training:** Team workshop on new governance model
3. **Monitoring:** Set up budget tracking dashboard
4. **Review:** Quarterly policy effectiveness assessment
5. **Optimization:** Tune risk classification based on data

---

**Version:** 3.0  
**Status:** Production Ready  
**Governance Authority:** Engineering Leadership  
**Next Review:** March 2026

---

## See Also

- [orchestrator_v3.yml](agents/orchestrator_v3.yml) - Agent coordinator
- [GOVERNANCE.md](GOVERNANCE.md) - Complete governance policy
- [skills_v3.yml](skills_v3.yml) - Skill definitions
- [validation_v3.yml](agents/validation_v3.yml) - Validation rules
