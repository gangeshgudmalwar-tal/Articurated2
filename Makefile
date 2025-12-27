# AI Orchestration CLI - Makefile
# Governance-First | 100 PRU Hard Limit

.PHONY: help validate-scope validate-logic gen-adversarial track-pru report install test clean

PYTHON := python
CLI_DIR := cli

help:
	@echo "AI Orchestration CLI v3.0"
	@echo ""
	@echo "Usage:"
	@echo "  make validate-scope FILES='file1.py file2.py' LINES=50"
	@echo "  make validate-logic FILES='service.py' CRITERIA='Must validate transitions'"
	@echo "  make gen-adversarial TARGET='app/api/v1/orders.py'"
	@echo "  make track-pru AGENT=scope_validator MODEL=gpt-4o-mini PRU=8 CONTEXT='PR-123'"
	@echo "  make report PERIOD=today"
	@echo "  make install"
	@echo "  make test"
	@echo "  make clean"

# Scope Validator
validate-scope:
	@$(PYTHON) $(CLI_DIR)/scope_validator.py --files $(FILES) --lines $(LINES)

validate-scope-diff:
	@$(PYTHON) $(CLI_DIR)/scope_validator.py --diff $(DIFF)

validate-scope-stdin:
	@cat $(INPUT) | $(PYTHON) $(CLI_DIR)/scope_validator.py --stdin

# Logic Validator
validate-logic:
	@$(PYTHON) $(CLI_DIR)/logic_validator.py --code $(FILES) --criteria "$(CRITERIA)" --risk $(RISK)

validate-logic-medium:
	@$(PYTHON) $(CLI_DIR)/logic_validator.py --code $(FILES) --risk MEDIUM

# Adversarial Tests
gen-adversarial:
	@$(PYTHON) $(CLI_DIR)/adversarial_tests.py --target $(TARGET) --format python

gen-adversarial-json:
	@$(PYTHON) $(CLI_DIR)/adversarial_tests.py --target $(TARGET) --format json

gen-adversarial-output:
	@$(PYTHON) $(CLI_DIR)/adversarial_tests.py --target $(TARGET) --output $(OUTPUT)

# PRU Tracker
track-pru:
	@$(PYTHON) $(CLI_DIR)/pru_tracker.py log --agent $(AGENT) --model $(MODEL) --pru $(PRU) --context "$(CONTEXT)"

report:
	@$(PYTHON) $(CLI_DIR)/pru_tracker.py report --period $(PERIOD)

report-session:
	@$(PYTHON) $(CLI_DIR)/pru_tracker.py report --period session

# Installation
install:
	@echo "Installing dependencies..."
	@pip install -q -r requirements.txt
	@echo "Making CLI scripts executable..."
	@chmod +x $(CLI_DIR)/*.py
	@echo "Creating logs directory..."
	@mkdir -p logs
	@echo "Installation complete."

# Testing
test:
	@echo "Running CLI tests..."
	@$(PYTHON) -m pytest tests/cli/ -v

test-scope:
	@echo "Testing scope validator..."
	@$(PYTHON) $(CLI_DIR)/scope_validator.py --files app/models/order.py --lines 10

test-logic:
	@echo "Testing logic validator..."
	@$(PYTHON) $(CLI_DIR)/logic_validator.py --code app/services/state_machine.py --criteria "Test" --risk LOW

test-adversarial:
	@echo "Testing adversarial tests generator..."
	@$(PYTHON) $(CLI_DIR)/adversarial_tests.py --target app/api/v1/orders.py --format json

test-pru:
	@echo "Testing PRU tracker..."
	@$(PYTHON) $(CLI_DIR)/pru_tracker.py log --agent test_agent --model test_model --pru 0 --context "test"
	@$(PYTHON) $(CLI_DIR)/pru_tracker.py report --period all

# Cleanup
clean:
	@echo "Cleaning generated files..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -f logs/pru_usage.csv
	@echo "Clean complete."

# Quick workflow examples
workflow-feature:
	@echo "Feature workflow: Scope → Logic → Implementation"
	@$(PYTHON) $(CLI_DIR)/scope_validator.py --files $(FILES) --lines 150
	@$(PYTHON) $(CLI_DIR)/logic_validator.py --code $(FILES) --risk MEDIUM

workflow-security:
	@echo "Security workflow: Scope → Adversarial Tests"
	@$(PYTHON) $(CLI_DIR)/scope_validator.py --files $(FILES)
	@$(PYTHON) $(CLI_DIR)/adversarial_tests.py --target $(FILES) --output tests/security/

workflow-complete:
	@echo "Complete workflow with tracking"
	@$(PYTHON) $(CLI_DIR)/scope_validator.py --files $(FILES) > /tmp/scope.json
	@$(PYTHON) $(CLI_DIR)/pru_tracker.py log --agent scope_validator --model gpt-4o-mini --pru 8 --context "$(CONTEXT)"
	@$(PYTHON) $(CLI_DIR)/logic_validator.py --code $(FILES) --risk MEDIUM > /tmp/logic.json
	@$(PYTHON) $(CLI_DIR)/pru_tracker.py log --agent logic_validator --model gpt-4o --pru 40 --context "$(CONTEXT)"
	@$(PYTHON) $(CLI_DIR)/pru_tracker.py report --period session
