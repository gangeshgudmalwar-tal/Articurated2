---
description: "AI Agents - Governance-First (v3.0) - 100 PRU Hard Limit with Copilot + Static Tools"
---

# AI Agents - Governance-First

**100 PRU Hard Limit | Default: 0 PRU (Copilot + Static Tools)**

## Files
```
orchestrator_v3.yml      # 4-agent coordinator
validation_v3.yml        # Static-first validation
implementation_v3.yml    # Code generation & refactoring
```

## Agents

### Core Governance Agents (4)

| Agent | Model | PRU | Trigger | Skills Used |
|-------|-------|-----|---------|-------------|
| **Scope Validator** | GPT-4o-mini | 8 | Every commit/PR | classify_risk, estimate_complexity |
| **Logic Risk Validator** | GPT-4o | 40 | Risk ≥ MEDIUM | validate_state_transitions, validate_business_logic |
| **Adversarial Test** | GPT-4o | 35 | Risk ≥ HIGH | generate_exploit_tests, assess_attack_surface |
| **PRU Governance** | None | 0 | Every operation | track_pru_usage, enforce_budget_limits |

### SDLC Support Agents (Extensible)

| Agent | Model | PRU | Trigger | Skills Used |
|-------|-------|-----|---------|-------------|
| **Implementation** | Copilot | 0 | Post-validation/Manual | generate_code, refactor_code, write_test, fix_bug |
| **Validation** | None/GPT-4o-mini | 0-8 | Every PR | test_execution, security_scan, code_quality, diagnose_failure |
| **Documentation** | Copilot | 0 | Code changes | generate_docs, update_api_spec |
| **Deployment** | None | 0 | Manual/Auto | build_image, run_migrations, deploy_service |
| **Monitoring** | None/GPT-4o-mini | 0-8 | Incidents | collect_metrics, analyze_logs, diagnose_issue |

**Note:** All agents invoke skills from [skills_v3.yml](../skills_v3.yml). New SDLC agents follow same pattern: invoke skills, track PRU via governance agent, respect 100 PRU budget.

## Routing

| Risk | Files | Lines | PRU | Agents | Example |
|------|-------|-------|-----|--------|---------|
| TRIVIAL | *.md | Any | 0 | None | Docs, whitespace |
| LOW | ≤2 | <50 | 8 | Scope | Simple bug fix |
| MEDIUM | ≤10 | 50-200 | 48 | Scope + Logic | Business logic |
| HIGH | >10 | >200 | 83 | All 3 | State machine, security |
| CRITICAL | Any | Any | ≤100 | Emergency | Production incident |

**Default:** Copilot + static tools (pytest, bandit, ruff, mypy) → 0 PRU  
**Escalation:** Auto-triggered based on risk classification

### Agent → Skill Flow
```
Commit → Orchestrator
  ↓
  Scope Validator (8 PRU)
    └─ invokes: classify_risk skill
       └─ returns: risk_level, route_to
  ↓
  if risk ≥ MEDIUM:
    Logic Risk Validator (40 PRU)
      └─ invokes: validate_state_transitions skill
         └─ returns: validation_status, issues
  ↓
  if risk ≥ HIGH:
    Adversarial Test Agent (35 PRU)
      └─ invokes: generate_exploit_tests skill
         └─ returns: test_cases, exploit_scenarios
  ↓
  Implementation Agent (0 PRU) [parallel]
    └─ invokes: generate_code, refactor_code, write_test
       └─ returns: code_generated, tests_written
  ↓
  Validation Agent (0-8 PRU) [parallel]
    └─ invokes: test_execution, security_scan, code_quality
       └─ returns: test_results, security_findings
  ↓
  if tests pass:
    Documentation Agent (0 PRU)
      └─ invokes: generate_docs, update_api_spec
         └─ returns: docs_updated
  ↓
  Deployment Agent (0 PRU) [manual trigger]
    └─ invokes: build_image, deploy_service
       └─ returns: deployment_status
```

## Human Gates (Mandatory)

- **PR Review:** Always required, no bypass
- **Staging Deploy:** Team lead approval
- **Production Deploy:** Tech lead + Ops lead approval

## MCP Policy (Sandboxed)

**Allowed:** Read-only github (PR/files/diff), filesystem (repo root), database (schema/migrations local)  
**Forbidden:** Write, network, exec, credentials, production DB

## Budget

**Ceiling:** 100 PRU (hard limit)  
**Alert:** 75 PRU (75%)  
**Reserve:** 15 PRU (emergency)  
**Enforcement:** Pre-check → fail fast → rollback → static fallback

## Skip Rules

**Never validate:** Dependabot, *.md, whitespace, comments  
**Skip logic:** Risk < MEDIUM + tests pass + coverage OK  
**Skip adversarial:** Risk < HIGH + no security/payment/auth

## Triggers

**Auto:** on_commit (scope + static), on_pr (scope + conditional logic), on_risk (adversarial)  
**Manual:** deployment, rollback, hotfix

## Fallback

| Condition | Action | Fallback |
|-----------|--------|---------|
| Agent fail | Block | Manual review |
| Budget exceed | Halt AI | Static only |
| Model unavailable | Retry queue | Manual review |
| Timeout (10m) | Cancel | Manual review |

## Output Schema

```yaml
risk_level: TRIVIAL|LOW|MEDIUM|HIGH|CRITICAL
pru_used: int
validation_status: PASS|FAIL|UNCERTAIN
issues: [{id, severity, description, fix}]
confidence: float
```

**Forbidden:** Verbose text, apologies, hedging, marketing, emoji

## Usage

```bash
# Auto-triggered on commit/PR
git commit -m "feat: add partial refund"

# Check budget
@orchestrator pru-report

# Force manual review
@orchestrator require-human-review
```

---
**Version:** 3.0 | **Budget:** 100 PRU | **Breaking:** Yes (from v2.0)
