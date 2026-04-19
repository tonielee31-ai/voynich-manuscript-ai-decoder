#!/bin/bash
# voynich-autonomous-research.sh
# Runs the Voynich research loop directly with full filesystem access
# Called by system crontab every 15 minutes

PROJECT_DIR="/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
SCRIPT="$PROJECT_DIR/web-research-loop.py"
LOG="$PROJECT_DIR/research-data/cron.log"

cd "$PROJECT_DIR"

# Run the research cycle
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting research cycle..." >> "$LOG"
python3 "$SCRIPT" --cycle >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cycle complete." >> "$LOG"

# Also run HMM analysis every 2 hours (at minute 0)
MINUTE=$(date '+%M')
if [ "$MINUTE" = "00" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running HMM analysis..." >> "$LOG"
    python3 "$PROJECT_DIR/hmm-analyzer.py" "$PROJECT_DIR/eva-takahashi.txt" --states 2 >> "$LOG" 2>&1
fi
