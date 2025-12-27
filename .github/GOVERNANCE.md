# AI Agent Governance Policy
**Version:** 3.0  
**Effective Date:** December 2025  
**Authority:** Engineering Leadership  
**Enforcement:** Automated + Human Oversight

---

## 1. Executive Summary

This document establishes binding governance rules for AI-assisted SDLC operations.

### Core Principles
1. **Cost-Bounded:** 100 PRU hard limit per lifecycle
2. **Deterministic:** Predictable routing based on measurable criteria
3. **Human-Gated:** Non-negotiable approval points
4. **Sandboxed:** MCP access restricted to repository
5. **Auditable:** Complete logging of all operations

### Scope
- **Applies to:** All commits, PRs, deployments
- **Enforcement:** Automated via orchestrator_v3
- **Overrides:** Tech lead approval required
- **Review Cycle:** Quarterly

---

## 2. Risk Classification Rules

### 2.1 Risk Levels (5-Point Scale)

#### TRIVIAL (0 PRU - Skip AI)
**Criteria:**
- Documentation-only changes (*.md, *.txt)
- Whitespace/formatting (linting auto-fix)
- Comment updates
- Dependabot version bumps
- Typo corrections

**Validation:**
- Static tools only (pytest, ruff, bandit)
- No AI invocation

**Example:**
```diff
- # Fix tpyo in comment
+ # Fix typo in comment
```

#### LOW (8 PRU - Scope Validator Only)
**Criteria:**
- < 50 lines changed
- No state machine modifications
- Tests pass
- Coverage maintained
- Follows existing patterns

**Validation:**
- Scope validator (GPT-4o-mini, 8 PRU)
- Static tools

**Example:**
```python
# Add logging to existing function
def process_order(order_id):
    logger.info(f"Processing order {order_id}")  # NEW
    # ... existing logic
```

#### MEDIUM (48 PRU - Logic Validator)
**Criteria:**
- 50-200 lines changed
- Business logic modifications
- Database schema changes
- API endpoint modifications
- New dependencies

**Validation:**
- Scope validator (8 PRU)
- Logic risk validator (40 PRU)
- Static tools

**Example:**
```python
# Modify order calculation logic
def calculate_total(items):
    subtotal = sum(item.price * item.quantity for item in items)
    tax = subtotal * 0.08  # Changed tax rate
    return subtotal + tax
```

#### HIGH (83 PRU - All Validators)
**Criteria:**
- > 200 lines changed
- State machine transitions modified
- Payment/refund logic changes
- Authentication/authorization changes
- Security-critical paths

**Validation:**
- Scope validator (8 PRU)
- Logic risk validator (40 PRU)
- Adversarial test agent (35 PRU)
- Static tools

**Example:**
```python
# Modify state transition rules
ORDER_TRANSITIONS = {
    OrderStatus.PENDING_PAYMENT: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED},  # REMOVED: PROCESSING_IN_WAREHOUSE
    # ^^ HIGH RISK: Breaks existing workflow
}
```

#### CRITICAL (100 PRU - Emergency Protocol)
**Criteria:**
- Production incident
- Security vulnerability fix
- Data corruption risk
- Payment gateway failure

**Validation:**
- All agents (100 PRU budget)
- Immediate tech lead notification
- Post-deployment audit required

**Example:**
```python
# Emergency: Payment gateway timeout causing duplicate charges
@retry(max_attempts=1)  # Changed from 3 to prevent duplicates
def process_payment(order_id):
    # Emergency fix deployed
```

### 2.2 Risk Detection Logic

```python
def classify_risk(pr_data):
    """Deterministic risk classification."""
    
    # File patterns
    if any(f.endswith('.md') for f in pr_data.files):
        if all(f.endswith('.md') for f in pr_data.files):
            return "TRIVIAL"
    
    # State machine check
    if "state_machine.py" in pr_data.files:
        return "HIGH"
    
    # Payment/security check
    security_paths = ["payment", "auth", "security", "refund"]
    if any(path in str(pr_data.files) for path in security_paths):
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

## 3. Budget Enforcement

### 3.1 Hard Limits

```yaml
per_lifecycle_limits:
  total_pru: 100
  alert_threshold: 75  # 75% consumed
  emergency_reserve: 15  # Reserved for CRITICAL
  
per_agent_limits:
  scope_validator: 8
  logic_risk_validator: 40
  adversarial_test_agent: 35
  pru_governance: 0  # Accounting only
```

### 3.2 Pre-Invocation Checks

```python
def check_budget_before_invocation(agent, estimated_pru):
    """Enforce budget before agent runs."""
    
    current_usage = get_session_pru_usage()
    remaining = 100 - current_usage
    
    if estimated_pru > remaining:
        if agent == "adversarial_test_agent":
            # Skip non-critical agent
            log_skip(agent, "budget_exceeded")
            return False
        else:
            # Block critical agents
            raise BudgetExceededError(
                f"Insufficient budget: {remaining} PRU remaining, {estimated_pru} required"
            )
    
    return True
```

### 3.3 Overrun Prevention

```yaml
safeguards:
  pre_check: Verify budget before invocation
  fail_fast: Cancel operation if budget exceeded
  rollback: Revert to static tools only (0 PRU)
  alert: Notify tech lead if >90% consumed
```

### 3.4 Budget Reporting

```bash
# Real-time budget dashboard
@orchestrator pru-report --session

Output:
Session PRU Usage: 48 / 100
  - scope_validator: 8 PRU
  - logic_risk_validator: 40 PRU
  - adversarial_test_agent: 0 PRU (skipped)
Alert Threshold: 75 PRU (27 PRU remaining)
Emergency Reserve: 15 PRU (available)
```

---

## 4. Human Gates (Non-Negotiable)

### 4.1 Mandatory Approval Points

```yaml
gate_1_pr_review:
  trigger: every_pr
  approver: team_lead OR tech_lead
  bypass: NEVER
  timeout: 24h
  escalation: tech_lead
  
gate_2_production_deployment:
  trigger: deploy_to_production
  approvers: [tech_lead, ops_lead]
  bypass: NEVER
  timeout: 4h
  escalation: engineering_manager
```

### 4.2 Gate Override (Emergency Only)

```yaml
override_protocol:
  trigger: critical_incident
  approver: engineering_manager
  documentation: required
  audit: immediate
  post_mortem: within_24h
```

### 4.3 Gate Timeout Behavior

```yaml
timeout_actions:
  pr_review:
    24h: escalate_to_tech_lead
    48h: escalate_to_manager
    72h: auto_close_pr
    
  production_deployment:
    4h: escalate_to_ops_lead
    8h: escalate_to_manager
    12h: cancel_deployment
```

---

## 5. MCP Sandboxing Rules

### 5.1 Allowed Operations

```yaml
github_mcp:
  read: [pr_metadata, file_contents, commit_history, diff]
  write: FORBIDDEN
  network: FORBIDDEN
  
filesystem_mcp:
  read: [repo_root/**]
  write: FORBIDDEN
  exec: FORBIDDEN
  network: FORBIDDEN
  
database_mcp:
  read: [schema_only, migrations_only]
  write: FORBIDDEN
  connection: local_only
  production: FORBIDDEN
```

### 5.2 Forbidden Operations

```yaml
forbidden:
  network_access: true
  external_apis: true
  system_commands: true
  credential_access: true
  write_operations: true
  production_database: true
```

### 5.3 Violation Response

```python
def handle_mcp_violation(operation):
    """Immediate block and alert on policy violation."""
    
    log_security_event(operation, "MCP_POLICY_VIOLATION")
    notify_security_team(operation)
    block_operation(operation)
    suspend_agent(operation.agent_id)
    
    # Require manual review before resuming
    return "BLOCKED_SECURITY_POLICY_VIOLATION"
```

---

## 6. Skip Rules (When NOT to Run Agents)

### 6.1 Never Validate

```yaml
skip_patterns:
  - pattern: "dependabot/**"
    reason: automated_updates
    
  - pattern: "*.md"
    condition: only_md_files
    reason: documentation_only
    
  - pattern: "whitespace_only"
    reason: formatting_only
    
  - pattern: "comment_only"
    reason: non_functional_change
```

### 6.2 Skip Logic Validator

```yaml
skip_conditions:
  - risk_level: TRIVIAL
  - risk_level: LOW
  - tests_passing: true AND coverage_maintained: true
  - no_state_machine_changes: true
  - follows_existing_patterns: true
```

### 6.3 Skip Adversarial Tests

```yaml
skip_conditions:
  - risk_level: [TRIVIAL, LOW, MEDIUM]
  - no_security_implications: true
  - no_payment_logic: true
  - no_auth_changes: true
```

---

## 7. Audit & Logging Requirements

### 7.1 Required Log Fields

```yaml
audit_log_schema:
  timestamp: iso8601_utc
  session_id: uuid
  operation_type: [agent_invocation, skill_execution, gate_check]
  agent_id: string
  pru_consumed: integer
  pru_remaining: integer
  risk_level: enum
  validation_status: [PASS, FAIL, UNCERTAIN]
  human_override: boolean
  justification: string
```

### 7.2 Log Retention

```yaml
retention_policy:
  real_time_logs: 30_days
  audit_logs: 7_years
  budget_reports: 2_years
  security_events: permanent
```

### 7.3 Audit Triggers

```yaml
audit_triggers:
  - budget_exceeded
  - human_override
  - mcp_violation
  - gate_timeout
  - agent_failure
  - critical_risk_detected
```

---

## 8. Fallback Behavior

### 8.1 Failure Modes

| Failure | Action | Fallback | Notification |
|---------|--------|----------|--------------|
| Agent timeout (10m) | Cancel | Manual review | Immediate |
| Budget exceeded | Halt AI | Static tools only | Immediate |
| Model unavailable | Queue retry | Manual review | 15m delay |
| MCP violation | Block | Manual review | Immediate |
| Gate timeout | Cancel | Escalate | Per policy |

### 8.2 Degraded Mode

```yaml
degraded_mode:
  trigger: model_unavailable OR budget_exceeded
  
  actions:
    - disable_ai_agents
    - enable_static_tools_only
    - notify_team
    - require_manual_review
    
  duration: until_resolved
  escalation: tech_lead
```

### 8.3 Recovery Protocol

```python
def recover_from_failure(failure_type):
    """Systematic recovery from failures."""
    
    if failure_type == "budget_exceeded":
        # Reset for next PR
        reset_session_budget()
        notify_team("Budget reset for next session")
        
    elif failure_type == "agent_timeout":
        # Retry once with higher timeout
        retry_with_timeout(timeout=20 * 60)
        
    elif failure_type == "model_unavailable":
        # Queue for retry
        queue_for_retry(delay=15 * 60)
        notify_team("Queued for retry in 15m")
```

---

## 9. Output Standards

### 9.1 Required Format

```yaml
agent_output_schema:
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

### 9.2 Forbidden Content

```yaml
forbidden_output:
  - verbose_explanations
  - apologetic_language
  - uncertainty_hedging
  - marketing_language
  - emoji
  - colloquial_language
```

### 9.3 Example Output

```json
{
  "risk_level": "MEDIUM",
  "pru_used": 48,
  "validation_status": "PASS",
  "issues": [],
  "recommendations": [
    "Add unit test for tax calculation edge case",
    "Document tax rate change in CHANGELOG"
  ],
  "confidence": 0.92,
  "timestamp": "2025-12-15T10:30:00Z"
}
```

---

## 10. Escalation Procedures

### 10.1 Escalation Triggers

```yaml
escalation_levels:
  
  level_1_team_lead:
    triggers:
      - budget_usage > 75%
      - gate_timeout > 24h
      - validation_uncertain
    response_sla: 4h
    
  level_2_tech_lead:
    triggers:
      - budget_usage > 90%
      - critical_risk_detected
      - mcp_violation
    response_sla: 1h
    
  level_3_manager:
    triggers:
      - budget_exceeded
      - gate_timeout > 48h
      - security_incident
    response_sla: 30m
```

### 10.2 Escalation Channels

```yaml
notification_channels:
  team_lead: [slack_dm, email]
  tech_lead: [slack_dm, email, phone]
  manager: [slack_dm, email, phone, pagerduty]
```

---

## 11. Compliance & Review

### 11.1 Review Schedule

```yaml
review_cycle:
  quarterly: policy_review
  monthly: budget_analysis
  weekly: incident_review
  daily: audit_log_check
```

### 11.2 Policy Updates

```yaml
update_process:
  propose: engineering_team
  review: tech_lead + manager
  approve: engineering_leadership
  notify: all_engineers
  effective: 14_days_after_approval
```

### 11.3 Incident Response

```yaml
incident_protocol:
  detection: automated_monitoring
  triage: tech_lead (15m SLA)
  mitigation: team_effort
  post_mortem: within_24h
  documentation: incident_log
```

---

## 12. Enforcement Mechanisms

### 12.1 Automated Enforcement

```python
def enforce_governance():
    """Automated policy enforcement."""
    
    # Pre-invocation checks
    if not check_budget():
        raise BudgetExceededError()
    
    if not check_mcp_compliance():
        raise MCPViolationError()
    
    if not check_human_gate():
        raise HumanApprovalRequiredError()
    
    # Post-invocation audit
    log_audit_record()
    check_budget_threshold()
    update_dashboard()
```

### 12.2 Manual Enforcement

```yaml
manual_reviews:
  trigger: policy_violation OR high_risk OR human_override
  reviewer: tech_lead
  documentation: required
  approval: required_for_merge
```

---

## 13. Metrics & KPIs

### 13.1 Tracked Metrics

```yaml
key_metrics:
  budget_utilization: pru_used / pru_allocated
  skip_rate: skipped_prs / total_prs
  human_gate_rate: gated_prs / total_prs
  false_positive_rate: incorrect_escalations / total_escalations
  time_to_validate: avg_validation_time
```

### 13.2 Success Criteria

```yaml
success_targets:
  budget_utilization: 50-75%
  skip_rate: > 60%
  human_gate_rate: < 20%
  false_positive_rate: < 5%
  time_to_validate: < 10m
```

---

## 14. Version History

| Version | Date | Changes | Approver |
|---------|------|---------|----------|
| 3.0 | Dec 2025 | Initial governance-first policy | Engineering Leadership |
| 2.0 | - | [Deprecated] Multi-agent coordination | - |
| 1.0 | - | [Deprecated] Manual oversight | - |

---

## 15. Appendix: Quick Reference

### Budget Limits
- **Total:** 100 PRU per lifecycle
- **Alert:** 75 PRU (75%)
- **Emergency:** 15 PRU reserved

### Risk Levels
- **TRIVIAL:** 0 PRU (skip AI)
- **LOW:** 8 PRU (scope only)
- **MEDIUM:** 48 PRU (+ logic)
- **HIGH:** 83 PRU (+ adversarial)
- **CRITICAL:** 100 PRU (all agents)

### Human Gates
- **PR Review:** ALWAYS required
- **Production Deploy:** ALWAYS requires tech lead + ops lead

### MCP Rules
- **Read:** Repository only
- **Write:** FORBIDDEN
- **Network:** FORBIDDEN

### Skip Rules
- Documentation-only: SKIP
- < 50 lines + tests pass: LOW risk
- State machine changes: HIGH risk

---

**Governance Authority:** Engineering Leadership  
**Enforcement:** Automated + Human Oversight  
**Review Cycle:** Quarterly  
**Next Review:** March 2026
