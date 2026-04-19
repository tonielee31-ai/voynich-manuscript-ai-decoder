#!/usr/bin/env python3
"""
Voynich Autonomous Research Loop - Web Scraper & Analyzer
==========================================================
Following Gemini's recommendations:
1. Read state file to see what's been tried
2. Search specific domains for new research
3. Download and analyze content
4. Test hypotheses against local manuscript
5. Update state file

Usage:
    python3 web-research-loop.py --cycle
    python3 web-research-loop.py --search "syllabic structures"
    python3 web-research-loop.py --analyze paper.txt
"""

import json
import os
import sys
import urllib.request
import urllib.error
import re
from datetime import datetime
from pathlib import Path
from collections import Counter


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
STATE_FILE = os.path.join(PROJECT_DIR, "voynich_state.json")
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")
KB_DIR = os.path.join(PROJECT_DIR, "knowledge-base")
PAPERS_DIR = os.path.join(KB_DIR, "papers")
WEB_DIR = os.path.join(KB_DIR, "web-research")
CYCLES_DIR = os.path.join(PROJECT_DIR, "research-data", "cycles")
REPORT_FILE = os.path.join(PROJECT_DIR, "RESEARCH_CYCLE_REPORT.md")

# Ensure directories exist
os.makedirs(PAPERS_DIR, exist_ok=True)
os.makedirs(WEB_DIR, exist_ok=True)


# ============================================================
# STATE MANAGEMENT
# ============================================================

class StateManager:
    """Manages the persistent state file."""
    
    def __init__(self):
        self.state = self.load()
    
    def load(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return self._default_state()
    
    def _default_state(self):
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "total_cycles": 0,
            "total_papers_analyzed": 0,
            "completed_hypotheses": [],
            "invalidated_hypotheses": [],
            "current_focus": "general_research",
            "knowledge_base": {"arxiv_papers": [], "web_research": [], "github_repos": []},
            "research_gaps": [],
            "next_focus_queue": [],
            "preferred_search_domains": [
                "arxiv.org", "voynich.nu", "stephenbax.net",
                "ciphermysteries.com", "voynich.ninja"
            ],
            "last_run_findings": "",
            "last_run_timestamp": ""
        }
    
    def save(self):
        self.state["last_updated"] = datetime.now().isoformat()
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_current_focus(self):
        return self.state.get("current_focus", "general_research")
    
    def get_next_focus(self):
        queue = self.state.get("next_focus_queue", [])
        if queue:
            return queue.pop(0)
        return self.get_current_focus()
    
    def update_after_cycle(self, findings, papers_added=None, gaps_found=None):
        self.state["total_cycles"] += 1
        self.state["last_run_findings"] = findings
        self.state["last_run_timestamp"] = datetime.now().isoformat()
        
        if papers_added:
            self.state["total_papers_analyzed"] += len(papers_added)
            self.state["knowledge_base"]["web_research"].extend(papers_added)
        
        if gaps_found:
            self.state["research_gaps"] = gaps_found
        
        # Move to next focus
        self.state["current_focus"] = self.get_next_focus()
        self.save()


# ============================================================
# WEB RESEARCH
# ============================================================

class WebResearcher:
    """Search and download research from specific domains."""
    
    PREFERRED_DOMAINS = [
        "arxiv.org",
        "voynich.nu",
        "stephenbax.net",
        "ciphermysteries.com",
        "voynich.ninja",
        "github.com",
    ]
    
    SEARCH_TOPICS = [
        "Voynich manuscript statistical analysis",
        "Voynich cipher decryption methods",
        "Voynich linguistic patterns",
        "Voynich entropy analysis",
        "Voynich word structure",
        "undeciphered manuscripts computational analysis",
        "historical cipher breaking techniques",
        "unknown script classification",
    ]
    
    def __init__(self):
        self.results = []
    
    def search_arxiv(self, query="voynich manuscript", max_results=5):
        """Search arXiv for papers."""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"
            
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
            
            # Parse simple XML
            papers = []
            entries = content.split("<entry>")[1:]
            for entry in entries[:max_results]:
                title = self._extract_xml(entry, "title")
                summary = self._extract_xml(entry, "summary")
                link = self._extract_xml(entry, "id")
                
                if title:
                    papers.append({
                        "source": "arxiv",
                        "title": title.strip(),
                        "abstract": summary.strip()[:500] if summary else "",
                        "url": link.strip() if link else "",
                        "timestamp": datetime.now().isoformat()
                    })
            
            return papers
        except Exception as e:
            print(f"arXiv search error: {e}")
            return []
    
    def _extract_xml(self, text, tag):
        """Extract content from XML tag."""
        start = text.find(f"<{tag}>")
        end = text.find(f"</{tag}>")
        if start != -1 and end != -1:
            return text[start + len(tag) + 2:end]
        return ""
    
    def search_github(self, query="voynich", max_results=5):
        """Search GitHub for repositories."""
        try:
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={max_results}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            repos = []
            for item in data.get("items", [])[:max_results]:
                repos.append({
                    "source": "github",
                    "title": item["full_name"],
                    "description": item.get("description", "")[:300],
                    "url": item["html_url"],
                    "stars": item.get("stargazers_count", 0),
                    "language": item.get("language", ""),
                    "timestamp": datetime.now().isoformat()
                })
            
            return repos
        except Exception as e:
            print(f"GitHub search error: {e}")
            return []
    
    def download_page(self, url, max_chars=5000):
        """Download and extract text from a webpage."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            # Strip HTML tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:max_chars]
        except Exception as e:
            print(f"Download error for {url}: {e}")
            return ""
    
    def run_search_cycle(self, focus=None):
        """Run one search cycle based on current focus with rate limiting."""
        from datetime import datetime, timedelta
        
        results = []
        now = datetime.now()
        
        # Load rate limiting state
        state = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
        
        rate_limits = state.get("rate_limiting", {})
        last_arxiv = rate_limits.get("last_arxiv_search")
        last_github = rate_limits.get("last_github_search")
        arxiv_interval = rate_limits.get("arxiv_api_interval_hours", 1)
        github_interval = rate_limits.get("github_api_interval_hours", 1)
        
        # Check if arXiv search is allowed
        arxiv_allowed = True
        if last_arxiv:
            last_time = datetime.fromisoformat(last_arxiv)
            if now - last_time < timedelta(hours=arxiv_interval):
                arxiv_allowed = False
        
        # Check if GitHub search is allowed
        github_allowed = True
        if last_github:
            last_time = datetime.fromisoformat(last_github)
            if now - last_time < timedelta(hours=github_interval):
                github_allowed = False
        
        # Search arXiv (rate limited)
        if arxiv_allowed:
            query = f"voynich {focus}" if focus else "voynich manuscript"
            arxiv_results = self.search_arxiv(query, max_results=3)
            results.extend(arxiv_results)
            self._update_rate_limit("arxiv")
            print(f"  arXiv: {len(arxiv_results)} results (searched)")
        else:
            print(f"  arXiv: SKIPPED (rate limited, next in {arxiv_interval}h)")
        
        # Search GitHub (rate limited)
        if github_allowed:
            github_results = self.search_github("voynich", max_results=3)
            results.extend(github_results)
            self._update_rate_limit("github")
            print(f"  GitHub: {len(github_results)} results (searched)")
        else:
            print(f"  GitHub: SKIPPED (rate limited, next in {github_interval}h)")
        
        self.results = results
        return results
    
    def _update_rate_limit(self, api_type):
        """Update rate limiting timestamps in state file."""
        now = datetime.now().isoformat()
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            if "rate_limiting" not in state:
                state["rate_limiting"] = {}
            if api_type == "arxiv":
                state["rate_limiting"]["last_arxiv_search"] = now
            elif api_type == "github":
                state["rate_limiting"]["last_github_search"] = now
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)


# ============================================================
# MANUSCRIPT ANALYZER
# ============================================================

class ManuscriptAnalyzer:
    """Analyze the local EVA transcription against research findings."""
    
    def __init__(self):
        if os.path.exists(EVA_FILE):
            with open(EVA_FILE, 'r') as f:
                self.text = f.read()
            self.words = self.text.split()
            self.chars = [c for c in self.text.lower() if c.strip()]
        else:
            self.text = ""
            self.words = []
            self.chars = []
    
    def test_syllabic_hypothesis(self):
        """Test if Voynich might be a syllabary."""
        # Count unique character pairs (potential syllables)
        clean = self.text.lower().replace('\n', ' ')
        bigrams = [clean[i:i+2] for i in range(len(clean)-1)]
        unique_bigrams = len(set(bigrams))
        total_bigrams = len(bigrams)
        
        # Syllabaries have fewer unique bigrams relative to total
        bigram_ratio = unique_bigrams / total_bigrams if total_bigrams > 0 else 0
        
        return {
            "hypothesis": "syllabic_structure",
            "unique_bigrams": unique_bigrams,
            "total_bigrams": total_bigrams,
            "bigram_ratio": round(bigram_ratio, 4),
            "assessment": (
                "SUPPORTED - low unique bigram ratio suggests syllabic encoding"
                if bigram_ratio < 0.1 else
                "INCONCLUSIVE"
            )
        }
    
    def test_word_structure_patterns(self):
        """Analyze word structure for encoding patterns."""
        # Analyze word-initial and word-final character preferences
        initial_chars = Counter(w[0] for w in self.words if w)
        final_chars = Counter(w[-1] for w in self.words if w)
        
        # Strong positional bias suggests encoding rules
        total = len(self.words)
        top_initial = initial_chars.most_common(3)
        top_final = final_chars.most_common(3)
        
        initial_bias = sum(c for _, c in top_initial) / total if total > 0 else 0
        final_bias = sum(c for _, c in top_final) / total if total > 0 else 0
        
        return {
            "hypothesis": "word_structure_encoding",
            "top_initial": [(c, round(n/total*100, 1)) for c, n in top_initial],
            "top_final": [(c, round(n/total*100, 1)) for c, n in top_final],
            "initial_bias": round(initial_bias, 3),
            "final_bias": round(final_bias, 3),
            "assessment": (
                "SUPPORTED - strong positional bias detected"
                if initial_bias > 0.3 or final_bias > 0.3 else
                "NORMAL"
            )
        }
    
    def run_analysis(self, hypothesis=None):
        """Run analysis based on hypothesis."""
        results = {}
        
        if hypothesis == "syllabic_structures" or hypothesis is None:
            results["syllabic"] = self.test_syllabic_hypothesis()
        
        if hypothesis == "word_structure" or hypothesis is None:
            results["word_structure"] = self.test_word_structure_patterns()
        
        return results


# ============================================================
# MAIN RESEARCH LOOP
# ============================================================

class ResearchLoop:
    """Main autonomous research loop."""
    
    def __init__(self):
        self.state = StateManager()
        self.researcher = WebResearcher()
        self.analyzer = ManuscriptAnalyzer()
    
    def run_cycle(self):
        """Run one complete research cycle."""
        print("=" * 60)
        print("VOYNICH AUTONOMOUS RESEARCH LOOP")
        print(f"Cycle #{self.state.state['total_cycles'] + 1}")
        print("=" * 60)
        
        # 1. Read state
        focus = self.state.get_current_focus()
        print(f"\n📖 Current Focus: {focus}")
        print(f"   Previous cycles: {self.state.state['total_cycles']}")
        print(f"   Papers analyzed: {self.state.state['total_papers_analyzed']}")
        
        # 2. Search for new research (with rate limiting)
        print(f"\n🔍 Searching for: voynich {focus}")
        search_results = self.researcher.run_search_cycle(focus)
        print(f"   Found: {len(search_results)} results")
        
        # 3. Analyze manuscript
        print(f"\n📊 Testing hypothesis: {focus}")
        analysis = self.analyzer.run_analysis(focus)
        for key, result in analysis.items():
            print(f"   {key}: {result.get('assessment', 'N/A')}")
        
        # 4. Build findings summary
        findings = self._build_findings(search_results, analysis, focus)
        
        # 5. Save research to knowledge base
        papers_saved = self._save_research(search_results)
        
        # 6. Update state (reload to get latest rate limit timestamps)
        self.state = StateManager()  # Reload state to get rate limit updates
        self.state.update_after_cycle(
            findings=findings,
            papers_added=papers_saved,
            gaps_found=self.state.state.get("research_gaps", [])
        )
        
        # 7. Save cycle file
        cycle_report = {
            "cycle_number": self.state.state["total_cycles"],
            "timestamp": datetime.now().isoformat(),
            "focus": focus,
            "search_results": search_results,
            "analysis": analysis,
            "findings": findings
        }
        cycle_file = self._save_cycle_file(cycle_report)
        
        # 8. Update main report
        self._update_report(findings, analysis, focus)
        
        print(f"\n✅ Cycle complete!")
        print(f"   Cycle file: {cycle_file}")
        print(f"   Papers saved: {len(papers_saved)}")
        print(f"   Next focus: {self.state.get_current_focus()}")
        
        return {
            "cycle": self.state.state["total_cycles"],
            "focus": focus,
            "search_results": len(search_results),
            "findings": findings,
            "analysis": analysis
        }
    
    def _build_findings(self, search_results, analysis, focus):
        """Build findings summary."""
        lines = []
        lines.append(f"Focus: {focus}")
        lines.append(f"Search results: {len(search_results)}")
        
        for r in search_results[:3]:
            lines.append(f"- {r['source']}: {r['title'][:60]}")
        
        for key, result in analysis.items():
            lines.append(f"- {key}: {result.get('assessment', 'N/A')}")
        
        return "\n".join(lines)
    
    def _save_research(self, results):
        """Save research results to knowledge base."""
        saved = []
        for r in results:
            filename = f"{r['source']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(saved)}.json"
            filepath = os.path.join(WEB_DIR, filename)
            with open(filepath, 'w') as f:
                json.dump(r, f, indent=2)
            saved.append(filename)
        return saved
    
    def _save_cycle_file(self, report):
        """Save cycle report to research-data/cycles/."""
        filename = f"voynich_research_cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(CYCLES_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        return filename
    
    def _update_report(self, findings, analysis, focus):
        """Update RESEARCH_CYCLE_REPORT.md."""
        section = f"""

## 🔬 Autonomous Research Cycle - {datetime.now().isoformat()}

### Focus: {focus}

### Search Results
"""
        for r in self.researcher.results[:3]:
            section += f"- **{r['source']}**: [{r['title'][:60]}]({r.get('url', '#')})\n"
        
        section += "\n### Manuscript Analysis\n"
        for key, result in analysis.items():
            section += f"- **{key}**: {result.get('assessment', 'N/A')}\n"
        
        section += "\n---\n"
        
        with open(REPORT_FILE, 'a') as f:
            f.write(section)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 web-research-loop.py --cycle")
        print("  python3 web-research-loop.py --search 'syllabic structures'")
        print("  python3 web-research-loop.py --state")
        sys.exit(1)
    
    loop = ResearchLoop()
    
    if sys.argv[1] == "--cycle":
        result = loop.run_cycle()
        print("\n--- CYCLE SUMMARY ---")
        print(json.dumps(result, indent=2, default=str))
    
    elif sys.argv[1] == "--search":
        query = sys.argv[2] if len(sys.argv) > 2 else "voynich"
        results = loop.researcher.run_search_cycle(query)
        print(json.dumps(results, indent=2))
    
    elif sys.argv[1] == "--state":
        print(json.dumps(loop.state.state, indent=2))
    
    else:
        print(f"Unknown command: {sys.argv[1]}")


if __name__ == "__main__":
    main()
