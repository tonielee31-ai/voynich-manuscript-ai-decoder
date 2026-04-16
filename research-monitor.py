#!/usr/bin/env python3
"""
Voynich Research Monitor - Simple Version
Monitors research-data/cycles/ for new research findings
"""

import json
import os
from pathlib import Path
from datetime import datetime
import glob
import sys

PROJECT_PATH = Path("/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder")
RESEARCH_DIR = PROJECT_PATH / "research-data" / "cycles"

def get_latest_research_cycle():
    """Find and parse the most recent research cycle JSON"""
    if not RESEARCH_DIR.exists():
        return None
    
    files = sorted(glob.glob(str(RESEARCH_DIR / "voynich_research_cycle_*.json")))
    if not files:
        return None
    
    latest = files[-1]
    try:
        with open(latest, 'r') as f:
            return json.load(f)
    except:
        return None

def print_dashboard():
    """Display research dashboard from persistent storage"""
    data = get_latest_research_cycle()
    
    if not data:
        print("\n⏳ Awaiting first research cycle in persistent storage...")
        print(f"   Location: {RESEARCH_DIR}")
        return
    
    print("\n" + "="*70)
    print(" VOYNICH RESEARCH MONITORING DASHBOARD (PERSISTENT STORAGE)")
    print("="*70)
    
    timestamp = data.get('timestamp', 'Unknown')
    cycle = data.get('cycle_number', 'N/A')
    
    print(f"\n📊 Latest Cycle: #{cycle} ({timestamp})")
    print(f"📁 Storage: {RESEARCH_DIR}")
    print("-" * 70)
    
    # Search engines used
    engines = data.get('search_engines_used', [])
    print(f"\n🔍 SEARCH ENGINES USED: {len(engines)}")
    for e in engines:
        print(f"   • {e}")
    
    # Theories found
    theories = data.get('research_sections', {}).get('cutting_edge_voynich_theories', {}).get('findings', [])
    if theories:
        print(f"\n⚡ CUTTING-EDGE THEORIES ({len(theories)} found):")
        for t in theories[:3]:
            score = t.get('relevance_score', 'N/A')
            print(f"   • {t.get('theory', 'Unknown'):50} Score: {score}")
    
    # Case studies
    cases = data.get('research_sections', {}).get('historical_language_decoding_case_studies', {})
    if cases:
        print(f"\n📚 HISTORICAL CASE STUDIES ({len(cases)} analyzed):")
        for k, v in list(cases.items())[:5]:
            if isinstance(v, dict) and 'name' in v:
                print(f"   • {v.get('name', 'Unknown')}")
    
    # Recommendations
    recs = data.get('enhancements_recommended', [])
    if recs:
        print(f"\n💡 RECOMMENDATIONS ({len(recs)} total):")
        for r in recs[:5]:
            if isinstance(r, str):
                print(f"   • {r}")
            elif isinstance(r, dict):
                print(f"   • {r.get('title', 'Unknown')}")
    
    # Storage info
    cycles = list(RESEARCH_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in cycles if f.name.startswith('voynich_research_cycle')) / (1024*1024)
    
    print(f"\n📊 STORAGE STATISTICS:")
    print(f"   Total cycles saved: {len([c for c in cycles if c.name.startswith('voynich_research_cycle')])}")
    print(f"   Total storage used: {total_size:.2f} MB")
    print(f"   Location: {RESEARCH_DIR}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    print_dashboard()
