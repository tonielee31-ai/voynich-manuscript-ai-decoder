#!/bin/bash
# voynich-autonomous-research.sh
# Runs the Voynich research loop directly with full filesystem access
# Called by system crontab every 15 minutes

# Set PATH for cron environment
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"

# Use Kilo.ai API for all LLM operations
export KILO_MODEL="kilo-auto/free"
export KILO_API_BASE="https://api.kilo.ai/api/gateway"
export OPENAI_API_BASE="${KILO_API_BASE}"

PROJECT_DIR="/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
SCRIPT="$PROJECT_DIR/web-research-loop.py"
LOG="$PROJECT_DIR/research-data/cron.log"
PYTHON="/usr/bin/python3"

# Fallback to python3 in PATH
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

cd "$PROJECT_DIR"

# Run the research cycle
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting research cycle (model: kilo-auto/free, provider: kilocode)..." >> "$LOG"
$PYTHON "$SCRIPT" --cycle >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cycle complete." >> "$LOG"

# Also run HMM analysis every 2 hours (at minute 0)
MINUTE=$(date '+%M')
if [ "$MINUTE" = "00" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running HMM analysis (model: kilo-auto/free, provider: kilocode)..." >> "$LOG"
    $PYTHON "$PROJECT_DIR/hmm-analyzer.py" "$PROJECT_DIR/eva-takahashi.txt" --states 2 >> "$LOG" 2>&1
fi
