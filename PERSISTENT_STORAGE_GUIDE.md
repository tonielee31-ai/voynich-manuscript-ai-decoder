# Voynich Research Loop - Persistent Storage Implementation

**Updated:** 2026-04-16 11:30 AM  
**Status:** ✅ MIGRATED TO PERSISTENT STORAGE  
**Previous:** `/tmp/` (temporary - vulnerable to deletion)  
**Current:** `research-data/cycles/` (permanent - survives reboots)

---

## The Problem: /tmp/ is Temporary

### What We Fixed

The original setup saved research outputs to `/tmp/`:
- ❌ Files deleted on system restart
- ❌ macOS cleanup tools remove files
- ❌ No backup or version history
- ❌ Not visible in project folder

### The Solution: Persistent Storage

Now research outputs are saved to:
```
/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder/
└── research-data/
    ├── cycles/                    ← Current research cycles (JSON files)
    │   ├── voynich_research_cycle_1713262800.json
    │   ├── voynich_research_cycle_1713262950.json
    │   └── ...
    ├── archives/                  ← Old cycles (compressed)
    │   ├── cycles-2026-04-week1.tar.gz
    │   └── cycles-2026-04-week2.tar.gz
    └── .gitignore                 ← Prevents bloating git repo
```

**Benefits:**
- ✅ Survives system reboots
- ✅ Survives macOS cleanup
- ✅ Permanent project storage
- ✅ Organized in project structure
- ✅ Can be backed up easily
- ✅ Integrated with git (via .gitignore rules)

---

## Directory Structure

### research-data/cycles/
**Purpose:** Current research cycle files  
**Contents:** JSON reports from active research  
**Retention:** Keep last 50-100 cycles (7-14 days of data)  
**Size:** ~100-200 KB per cycle = 5-20 MB for 50 cycles  

### research-data/archives/
**Purpose:** Compressed archives of old cycles  
**Contents:** tar.gz or zip archives (weekly batches)  
**Retention:** Indefinite (compresses 50 cycles to ~2-5 MB)  
**Backup strategy:** Can archive to cloud storage  

### research-data/.gitignore
**Purpose:** Prevent JSON files from bloating git repo  
**Rules:**
- `cycles/*.json` — Exclude raw cycle files
- `archives/*.tar.gz` — Exclude compressed archives
- `*.tmp, *.lock` — Exclude temp/lock files

---

## How to View Research Findings

### Option 1: Project Monitor Script (Recommended)
```bash
python3 /Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder/research-monitor.py
```
Shows latest findings from persistent storage + storage statistics.

### Option 2: View Latest JSON File
```bash
jq . /Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder/research-data/cycles/*.json | tail -100
```

### Option 3: List All Cycles
```bash
ls -lhS /Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder/research-data/cycles/
```

### Option 4: Check Storage Usage
```bash
du -sh /Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder/research-data/
```

---

## Cron Job Configuration

**Updated:** Job now saves to persistent storage  
**Location:** `/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder/research-data/cycles/`  
**Filename pattern:** `voynich_research_cycle_[UNIX_TIMESTAMP].json`  
**Schedule:** Every 5 minutes  
**Job ID:** `1e0ccf6d03c5`

---

## Data Lifecycle Management

### Weekly Archival (Manual)
After 50 cycles (~8 hours), compress old cycles:
```bash
cd /Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder/research-data/

# Archive cycles older than 1 week
tar -czf archives/cycles-$(date +%Y-%m-week%U).tar.gz cycles/voynich_research_cycle_*.json

# Clean up old files (keep last 20)
ls -t cycles/*.json | tail -n +21 | xargs rm
```

### Optional: Cloud Backup
```bash
# Backup archives to cloud storage
aws s3 sync archives/ s3://voynich-research-backup/

# Or use rclone for other cloud providers
rclone sync archives/ gdrive:/voynich-research/
```

---

## Storage Capacity Planning

### Consumption Rate
- Per cycle: ~100-200 KB (avg 150 KB)
- Per hour: 12 cycles × 150 KB = 1.8 MB
- Per day: 288 cycles × 150 KB = 43.2 MB
- Per week: 2,016 cycles × 150 KB = 302 MB
- Per month: ~1.3 GB

### Storage Recommendations
**Aggressive (no cleanup):**
- Disk usage: ~15 GB after 1 year
- Archive frequency: Monthly
- Retention: Keep all data

**Moderate (weekly cleanup):**
- Disk usage: ~500 MB (50 cycles max)
- Archive frequency: Weekly
- Retention: 1 week + archives

**Conservative (daily cleanup):**
- Disk usage: ~50 MB (10 cycles max)
- Archive frequency: Daily
- Retention: Last 24 hours + archives

---

## Git Integration

### Why .gitignore?
Research cycle JSON files should NOT be committed to git:
- Too large (14-58 MB per day)
- Not source code (can be regenerated)
- Would bloat repository history
- Better served as separate data store

### What SHOULD Be Committed
✅ RESEARCH_CYCLE_REPORT.md — Aggregated findings (persistent)  
✅ RESEARCH_LOOP_GUIDE.md — Setup documentation  
✅ research-monitor.py — Monitoring script  
✅ .gitignore — Exclusion rules  

### What Should NOT Be Committed
❌ cycles/*.json — Raw research data  
❌ archives/*.tar.gz — Compressed cycles  

---

## Verification Checklist

✅ Directory created: `research-data/cycles/`  
✅ Directory created: `research-data/archives/`  
✅ `.gitignore` configured: Prevents JSON commits  
✅ Cron job updated: Saves to persistent storage  
✅ Monitor script created: `research-monitor.py`  
✅ Next cycle will save to: `research-data/cycles/`  

---

## Quick Commands

```bash
# View latest research findings
python3 research-monitor.py

# List all research cycles
ls -lhS research-data/cycles/

# Check total storage used
du -sh research-data/

# Archive old cycles
tar -czf research-data/archives/week-$(date +%U).tar.gz research-data/cycles/*.json

# View raw JSON
jq . research-data/cycles/voynich_research_cycle_*.json | head -50

# Check cron job status
hermes cron list | grep voynich
```

---

## Migration Summary

| Aspect | Before (/tmp/) | After (research-data/) |
|--------|---|---|
| Location | `/tmp/` | Project folder |
| Survives reboot | ❌ No | ✅ Yes |
| Survives cleanup | ❌ No | ✅ Yes |
| Permanent storage | ❌ No | ✅ Yes |
| Git tracked | ❌ No | ✅ Via .gitignore |
| Backup friendly | ❌ No | ✅ Yes |
| Organized | ❌ Scattered | ✅ Structured |
| Space efficient | ❌ Raw files | ✅ + archives |

---

## Next Steps

1. ✅ Research-data directory created
2. ✅ Cron job updated to use persistent storage
3. ⏳ Wait for next cycle (5 minutes)
4. 👉 View results: `python3 research-monitor.py`
5. (Optional) Set up weekly archival script
6. (Optional) Set up cloud backup

---

**Generated:** 2026-04-16 11:30 AM  
**Status:** ✅ PERSISTENT STORAGE IMPLEMENTED
