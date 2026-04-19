#!/usr/bin/env python3
"""
Voynich Autonomous Research Loop - Cron Compatible Version
===========================================================
This version outputs all data as JSON to stdout.
The cron job's AI agent will handle file writing.

Usage:
    python3 voynich-cron-cycle.py
    
Output: JSON to stdout (captured by cron)
"""

import json
import os
import urllib.request
import urllib.error
import re
from datetime import datetime
from collections import Counter


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")
STATE_FILE = os.path.join(PROJECT_DIR, "voynich_state.json")
CYCLES_DIR = os.path.join(PROJECT_DIR, "research-data", "cycles")
KB_DIR = os.path.join(PROJECT_DIR, "knowledge-base", "web-research")
REPORT_FILE = os.path.join(PROJECT_DIR, "RESEARCH_CYCLE_REPORT.md")


def load_state():
    """Load current state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"total_cycles": 0, "total_papers_analyzed": 0, "current_focus": "general"}


def analyze_eva():
    """Analyze local EVA text."""
    if not os.path.exists(EVA_FILE):
        return {"error": "EVA file not found"}
    
    with open(EVA_FILE, 'r') as f:
        text = f.read()
    
    words = text.split()
    chars = [c for c in text.lower() if c.strip()]
    char_freq = Counter(chars)
    word_freq = Counter(words)
    
    # Syllabic test
    clean = text.lower().replace('\n', ' ')
    bigrams = [clean[i:i+2] for i in range(len(clean)-1)]
    unique_bigrams = len(set(bigrams))
    total_bigrams = len(bigrams)
    bigram_ratio = unique_bigrams / total_bigrams if total_bigrams > 0 else 0
    
    # Prefix/suffix patterns
    prefixes = Counter(w[:2] for w in words if len(w) >= 2)
    suffixes = Counter(w[-2:] for w in words if len(w) >= 2)
    
    return {
        "total_words": len(words),
        "unique_words": len(word_freq),
        "unique_chars": len(char_freq),
        "top_words": word_freq.most_common(5),
        "top_chars": char_freq.most_common(5),
        "syllabic_ratio": round(bigram_ratio, 4),
        "syllabic_supported": bigram_ratio < 0.01,
        "top_prefixes": prefixes.most_common(5),
        "top_suffixes": suffixes.most_common(5)
    }


def search_arxiv(query="voynich manuscript", max_results=3):
    """Search arXiv for papers."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{encoded}&start=0&max_results={max_results}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
        
        papers = []
        entries = content.split("<entry>")[1:]
        for entry in entries[:max_results]:
            title = extract_xml(entry, "title")
            summary = extract_xml(entry, "summary")
            link = extract_xml(entry, "id")
            if title:
                papers.append({
                    "source": "arxiv",
                    "title": title.strip()[:100],
                    "abstract": summary.strip()[:300] if summary else "",
                    "url": link.strip() if link else ""
                })
        return papers
    except Exception as e:
        return [{"error": str(e)}]


def extract_xml(text, tag):
    """Extract XML tag content."""
    start = text.find(f"<{tag}>")
    end = text.find(f"</{tag}>")
    if start != -1 and end != -1:
        return text[start + len(tag) + 2:end]
    return ""


def run_cycle():
    """Run one research cycle."""
    state = load_state()
    cycle_num = state.get("total_cycles", 0) + 1
    focus = state.get("current_focus", "general")
    timestamp = datetime.now().isoformat()
    
    # 1. Analyze manuscript
    eva_analysis = analyze_eva()
    
    # 2. Search for new research
    search_results = search_arxiv(f"voynich {focus}", max_results=3)
    
    # 3. Build cycle report
    report = {
        "cycle_number": cycle_num,
        "timestamp": timestamp,
        "focus": focus,
        "eva_analysis": eva_analysis,
        "search_results": search_results,
        "state_before": {
            "cycles": state.get("total_cycles", 0),
            "papers": state.get("total_papers_analyzed", 0)
        }
    }
    
    # 4. Determine next focus
    focus_queue = state.get("next_focus_queue", [])
    next_focus = focus_queue.pop(0) if focus_queue else focus
    
    # 5. Build updated state
    new_state = state.copy()
    new_state["total_cycles"] = cycle_num
    new_state["total_papers_analyzed"] = state.get("total_papers_analyzed", 0) + len(search_results)
    new_state["current_focus"] = next_focus
    new_state["last_updated"] = timestamp
    new_state["last_run_findings"] = f"Cycle {cycle_num}: Found {len(search_results)} papers on '{focus}'"
    if focus_queue:
        new_state["next_focus_queue"] = focus_queue
    
    # 6. Build file contents
    report_filename = f"voynich_research_cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 7. Build markdown section
    markdown = f"\n## 🔬 Cycle #{cycle_num} - {timestamp}\n\n"
    markdown += f"### Focus: {focus}\n\n"
    markdown += "### Search Results\n"
    for r in search_results:
        if "title" in r:
            markdown += f"- **{r.get('source', '?')}**: {r['title'][:60]}\n"
    markdown += "\n### Manuscript Analysis\n"
    if "error" not in eva_analysis:
        markdown += f"- Words: {eva_analysis.get('total_words', 0):,}\n"
        markdown += f"- Syllabic: {'SUPPORTED' if eva_analysis.get('syllabic_supported') else 'INCONCLUSIVE'}\n"
        markdown += f"- Top prefixes: {[p[0] for p in eva_analysis.get('top_prefixes', [])[:3]]}\n"
        markdown += f"- Top suffixes: {[s[0] for s in eva_analysis.get('top_suffixes', [])[:3]]}\n"
    markdown += "\n---\n"
    
    # Output everything as JSON
    output = {
        "action": "RESEARCH_CYCLE_COMPLETE",
        "cycle": report,
        "files_to_write": {
            "state_file": {
                "path": STATE_FILE,
                "content": new_state
            },
            "cycle_file": {
                "path": os.path.join(CYCLES_DIR, report_filename),
                "content": report
            },
            "report_append": {
                "path": REPORT_FILE,
                "content": markdown
            }
        },
        "summary": {
            "cycle": cycle_num,
            "focus": focus,
            "papers_found": len(search_results),
            "next_focus": next_focus,
            "syllabic_supported": eva_analysis.get("syllabic_supported", False)
        }
    }
    
    return output


if __name__ == "__main__":
    result = run_cycle()
    print(json.dumps(result, indent=2, default=str))
