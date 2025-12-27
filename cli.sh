#!/usr/bin/env bash
# AI Orchestration CLI Wrapper for Windows Terminal
# Governance-First | 100 PRU Hard Limit

PYTHON="python"
CLI_DIR="cli"

function show_help() {
    echo "AI Orchestration CLI v3.0 - Windows Wrapper"
    echo ""
    echo "Usage:"
    echo "  ./cli.sh scope-validate file1.py file2.py --lines 50"
    echo "  ./cli.sh logic-validate service.py --criteria 'Must validate transitions' --risk MEDIUM"
    echo "  ./cli.sh adversarial orders.py"
    echo "  ./cli.sh track scope_validator gpt-4o-mini 8 'PR-123'"
    echo "  ./cli.sh report today"
    echo "  ./cli.sh install"
    echo "  ./cli.sh test"
    echo ""
    echo "Commands:"
    echo "  scope-validate FILES... [--lines N]  - Classify change risk"
    echo "  logic-validate FILES... [OPTIONS]    - Validate business logic"
    echo "  adversarial TARGET [--output DIR]    - Generate security tests"
    echo "  track AGENT MODEL PRU CONTEXT        - Log PRU usage"
    echo "  report [today|session|all]           - Usage report"
    echo "  install                              - Install dependencies"
    echo "  test                                 - Run CLI tests"
}

function scope_validate() {
    files=()
    lines=0
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --lines)
                lines="$2"
                shift 2
                ;;
            *)
                files+=("$1")
                shift
                ;;
        esac
    done
    
    $PYTHON $CLI_DIR/scope_validator.py --files "${files[@]}" --lines $lines
}

function logic_validate() {
    files=()
    criteria=""
    risk="MEDIUM"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --criteria)
                criteria="$2"
                shift 2
                ;;
            --risk)
                risk="$2"
                shift 2
                ;;
            *)
                files+=("$1")
                shift
                ;;
        esac
    done
    
    $PYTHON $CLI_DIR/logic_validator.py --code "${files[@]}" --criteria "$criteria" --risk $risk
}

function adversarial() {
    target="$1"
    shift
    
    $PYTHON $CLI_DIR/adversarial_tests.py --target "$target" "$@"
}

function track() {
    agent="$1"
    model="$2"
    pru="$3"
    context="$4"
    
    $PYTHON $CLI_DIR/pru_tracker.py log --agent "$agent" --model "$model" --pru $pru --context "$context"
}

function report() {
    period="${1:-today}"
    
    $PYTHON $CLI_DIR/pru_tracker.py report --period "$period"
}

function install_deps() {
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
    
    echo "Creating logs directory..."
    mkdir -p logs
    
    echo "Installation complete."
}

function run_tests() {
    echo "Running CLI tests..."
    
    echo "Testing scope validator..."
    $PYTHON $CLI_DIR/scope_validator.py --files app/models/order.py --lines 10
    
    echo "Testing logic validator..."
    $PYTHON $CLI_DIR/logic_validator.py --code app/services/state_machine.py --criteria "Test" --risk LOW
    
    echo "Testing adversarial generator..."
    $PYTHON $CLI_DIR/adversarial_tests.py --target app/api/v1/orders.py --format json
    
    echo "Testing PRU tracker..."
    $PYTHON $CLI_DIR/pru_tracker.py log --agent test --model test --pru 0 --context "test"
    $PYTHON $CLI_DIR/pru_tracker.py report --period all
    
    echo "Tests complete."
}

# Main command router
case "$1" in
    scope-validate)
        shift
        scope_validate "$@"
        ;;
    logic-validate)
        shift
        logic_validate "$@"
        ;;
    adversarial)
        shift
        adversarial "$@"
        ;;
    track)
        shift
        track "$@"
        ;;
    report)
        shift
        report "$@"
        ;;
    install)
        install_deps
        ;;
    test)
        run_tests
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
