#!/usr/bin/env python3
"""
Voynich Currier A/B Language Analysis
=======================================
Following Gemini's recommendation:
- Segment manuscript by folio/page number
- Analyze if -edy and -iin suffixes cluster on specific pages
- Detect "Currier Language A" vs "Currier Language B"
- Treat 'ch' and 'sh' as single EVA characters

Background:
- Currier A: Herbal/Pharmaceutical pages, lots of -edy suffixes
- Currier B: Biological/Astronomical pages, lots of -iin suffixes

Usage:
    python3 currier-analysis.py --eva eva-takahashi.txt
"""

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")
STATE_FILE = os.path.join(PROJECT_DIR, "voynich_state.json")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "research-output")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# EVA TOKENIZER (treats ch, sh, cth, cph as single tokens)
# ============================================================

# Multi-character EVA tokens that represent single manuscript characters
EVA_MULTI_TOKENS = ['cth', 'cph', 'cfh', 'ckh', 'cph', 'sh', 'ch', 'qo']

def tokenize_eva(word):
    """Tokenize an EVA word, treating multi-char tokens as single units.
    
    Example: 'chedy' → ['ch', 'e', 'd', 'y']
             'shedy' → ['sh', 'e', 'd', 'y']
             'cth!res' → ['cth', '!', 'r', 'e', 's']
    """
    tokens = []
    i = 0
    clean = ''.join(c for c in word if c.isalpha() or c == '!' or c == '*')
    
    while i < len(clean):
        matched = False
        # Try longest multi-char tokens first
        for token in sorted(EVA_MULTI_TOKENS, key=len, reverse=True):
            if clean[i:i+len(token)] == token:
                tokens.append(token)
                i += len(token)
                matched = True
                break
        if not matched:
            if clean[i].isalpha():
                tokens.append(clean[i])
            i += 1
    
    return tokens


def tokenize_word_for_suffix(word):
    """Tokenize and return suffix tokens."""
    tokens = tokenize_eva(word)
    return tokens


# ============================================================
# CURRIER ANALYSIS
# ============================================================

class CurrierAnalyzer:
    """Analyze Currier A/B language distribution in the manuscript."""
    
    def __init__(self, text):
        self.text = text
        self.lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Parse into pages/folios
        self.pages = self._parse_pages()
        
        # Tokenize all words
        self.all_tokenized_words = []
        for line in self.lines:
            for word in line.split():
                tokens = tokenize_eva(word)
                if tokens:
                    self.all_tokenized_words.append((word, tokens))
    
    def _parse_pages(self):
        """Parse manuscript into pages/sections.
        
        If folio markers exist, use them. Otherwise, split into
        sections of ~100 lines each (approximating page boundaries).
        """
        pages = {}
        
        # Check if folio markers exist
        has_folio_markers = any(
            line.startswith('f') and len(line) > 2 
            and line[1:].replace('r','').replace('v','').replace(' ','').isdigit()
            for line in self.lines[:100]
        )
        
        if has_folio_markers:
            # Use folio markers
            current_page = 'f1r'
            current_lines = []
            for line in self.lines:
                if line.startswith('f') and len(line) > 2:
                    parts = line.split()
                    if parts:
                        marker = parts[0]
                        if len(marker) >= 3 and marker[1:].replace('r','').replace('v','').isdigit():
                            if current_lines:
                                pages[current_page] = current_lines
                            current_page = marker
                            current_lines = []
                            continue
                current_lines.append(line)
            if current_lines:
                pages[current_page] = current_lines
        else:
            # Split into sections of ~100 lines
            lines_per_section = 100
            for i in range(0, len(self.lines), lines_per_section):
                section_num = i // lines_per_section + 1
                section_name = f"section_{section_num:03d}_lines_{i+1}-{min(i+lines_per_section, len(self.lines))}"
                pages[section_name] = self.lines[i:i+lines_per_section]
        
        return pages
    
    def analyze_suffix_distribution(self):
        """Analyze distribution of -edy and -iin suffixes across pages."""
        # Define suffix patterns (as EVA tokens)
        edy_suffix = ['e', 'd', 'y']  # -edy
        iin_suffix = ['i', 'i', 'n']  # -iin
        dy_suffix = ['d', 'y']        # -dy
        ey_suffix = ['e', 'y']        # -ey
        in_suffix = ['i', 'n']        # -in
        
        suffix_patterns = {
            'edy': edy_suffix,
            'iin': iin_suffix,
            'dy': dy_suffix,
            'ey': ey_suffix,
            'in': in_suffix,
        }
        
        page_suffix_counts = {}
        
        for page_name, page_lines in self.pages.items():
            counts = defaultdict(int)
            total_words = 0
            
            for line in page_lines:
                for word in line.split():
                    tokens = tokenize_eva(word)
                    total_words += 1
                    
                    # Check for each suffix pattern
                    for suffix_name, suffix_pattern in suffix_patterns.items():
                        if len(tokens) >= len(suffix_pattern):
                            if tokens[-len(suffix_pattern):] == suffix_pattern:
                                counts[suffix_name] += 1
            
            # Calculate percentages
            if total_words > 0:
                page_suffix_counts[page_name] = {
                    'total_words': total_words,
                    'counts': dict(counts),
                    'percentages': {
                        k: round(v / total_words * 100, 2) 
                        for k, v in counts.items()
                    }
                }
        
        return page_suffix_counts
    
    def classify_currier_languages(self, page_suffix_counts):
        """Classify pages as Currier A or B based on suffix distribution."""
        classifications = {}
        
        for page_name, data in page_suffix_counts.items():
            pcts = data.get('percentages', {})
            edy_pct = pcts.get('edy', 0)
            iin_pct = pcts.get('iin', 0)
            
            # Currier A: High -edy, lower -iin
            # Currier B: High -iin, lower -edy
            if edy_pct > iin_pct * 1.5:
                language = 'A'
                confidence = min(1.0, (edy_pct - iin_pct) / 10)
            elif iin_pct > edy_pct * 1.5:
                language = 'B'
                confidence = min(1.0, (iin_pct - edy_pct) / 10)
            else:
                language = 'MIXED'
                confidence = 0.5
            
            classifications[page_name] = {
                'language': language,
                'confidence': round(confidence, 2),
                'edy_pct': edy_pct,
                'iin_pct': iin_pct,
                'total_words': data.get('total_words', 0)
            }
        
        return classifications
    
    def analyze_prefix_distribution(self):
        """Analyze prefix distribution (qo-, ch-, sh-)."""
        prefix_patterns = {
            'qo': ['q', 'o'],
            'ch': ['ch'],
            'sh': ['sh'],
            'qok': ['q', 'o', 'k'],
            'che': ['ch', 'e'],
        }
        
        page_prefix_counts = {}
        
        for page_name, page_lines in self.pages.items():
            counts = defaultdict(int)
            total_words = 0
            
            for line in page_lines:
                for word in line.split():
                    tokens = tokenize_eva(word)
                    total_words += 1
                    
                    for prefix_name, prefix_pattern in prefix_patterns.items():
                        if len(tokens) >= len(prefix_pattern):
                            if tokens[:len(prefix_pattern)] == prefix_pattern:
                                counts[prefix_name] += 1
            
            if total_words > 0:
                page_prefix_counts[page_name] = {
                    'total_words': total_words,
                    'counts': dict(counts),
                    'percentages': {
                        k: round(v / total_words * 100, 2)
                        for k, v in counts.items()
                    }
                }
        
        return page_prefix_counts
    
    def analyze_token_frequency(self):
        """Analyze overall EVA token frequency (with ch/sh as single tokens)."""
        token_freq = Counter()
        
        for word, tokens in self.all_tokenized_words:
            for token in tokens:
                token_freq[token] += 1
        
        return token_freq
    
    def full_analysis(self):
        """Run complete Currier analysis."""
        print("Running Currier A/B analysis...")
        
        # 1. Token frequency
        token_freq = self.analyze_token_frequency()
        total_tokens = sum(token_freq.values())
        
        # 2. Suffix distribution
        suffix_dist = self.analyze_suffix_distribution()
        
        # 3. Prefix distribution
        prefix_dist = self.analyze_prefix_distribution()
        
        # 4. Currier classification
        classifications = self.classify_currier_languages(suffix_dist)
        
        # 5. Summary statistics
        a_pages = [p for p, c in classifications.items() if c['language'] == 'A']
        b_pages = [p for p, c in classifications.items() if c['language'] == 'B']
        mixed_pages = [p for p, c in classifications.items() if c['language'] == 'MIXED']
        
        results = {
            'token_frequency': {
                'total_tokens': total_tokens,
                'unique_tokens': len(token_freq),
                'top_15': [(t, c, round(c/total_tokens*100, 2)) for t, c in token_freq.most_common(15)]
            },
            'suffix_distribution': suffix_dist,
            'prefix_distribution': prefix_dist,
            'currier_classifications': classifications,
            'summary': {
                'total_pages': len(classifications),
                'currier_a_pages': len(a_pages),
                'currier_b_pages': len(b_pages),
                'mixed_pages': len(mixed_pages),
                'currier_a_list': a_pages[:10],
                'currier_b_list': b_pages[:10],
            }
        }
        
        return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 currier-analysis.py <eva_file> [--json]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    with open(filepath, 'r') as f:
        text = f.read()
    
    analyzer = CurrierAnalyzer(text)
    results = analyzer.full_analysis()
    
    if '--json' in sys.argv:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("\n" + "=" * 60)
        print("CURRIER A/B LANGUAGE ANALYSIS")
        print("(ch and sh treated as single EVA tokens)")
        print("=" * 60)
        
        print(f"\n📊 TOKEN FREQUENCY (Top 15)")
        print("-" * 50)
        for token, count, pct in results['token_frequency']['top_15']:
            bar = "█" * int(pct * 2)
            print(f"  {token:6s} : {count:6d} ({pct:5.2f}%) {bar}")
        
        print(f"\n📊 CURRIER CLASSIFICATION")
        print("-" * 50)
        s = results['summary']
        print(f"  Total pages analyzed: {s['total_pages']}")
        print(f"  Currier A (Herbal):   {s['currier_a_pages']} pages")
        print(f"  Currier B (Biological): {s['currier_b_pages']} pages")
        print(f"  Mixed:                {s['mixed_pages']} pages")
        
        print(f"\n📊 CURRIER A PAGES (high -edy)")
        for page in s['currier_a_list'][:5]:
            cls = results['currier_classifications'][page]
            print(f"  {page}: edy={cls['edy_pct']}%, iin={cls['iin_pct']}%")
        
        print(f"\n📊 CURRIER B PAGES (high -iin)")
        for page in s['currier_b_list'][:5]:
            cls = results['currier_classifications'][page]
            print(f"  {page}: edy={cls['edy_pct']}%, iin={cls['iin_pct']}%")
        
        # Show sample page details
        sample_pages = list(results['suffix_distribution'].keys())[:3]
        print(f"\n📊 SAMPLE PAGE DETAILS")
        for page in sample_pages:
            data = results['suffix_distribution'][page]
            cls = results['currier_classifications'].get(page, {})
            print(f"\n  {page} ({cls.get('language', '?')}, {data['total_words']} words):")
            for suffix, pct in sorted(data['percentages'].items(), key=lambda x: -x[1])[:5]:
                print(f"    -{suffix}: {pct}%")
        
        print(f"\n{'='*60}")
        print("KEY FINDING")
        print(f"{'='*60}")
        
        if s['currier_a_pages'] > s['currier_b_pages']:
            print("  Manuscript is PREDOMINANTLY Currier Language A")
            print("  (Herbal/Pharmaceutical style, -edy dominant)")
        elif s['currier_b_pages'] > s['currier_a_pages']:
            print("  Manuscript is PREDOMINANTLY Currier Language B")
            print("  (Biological/Astronomical style, -iin dominant)")
        else:
            print("  Manuscript has BALANCED A/B distribution")
    
    # Save results
    output = os.path.join(OUTPUT_DIR, 'currier-analysis.json')
    with open(output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Saved to {output}")
    
    # Update state file
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        state['currier_analysis'] = {
            'completed': True,
            'timestamp': datetime.now().isoformat(),
            'total_pages': results['summary']['total_pages'],
            'currier_a_pages': results['summary']['currier_a_pages'],
            'currier_b_pages': results['summary']['currier_b_pages']
        }
        state['last_run_findings'] = f"Currier analysis: {results['summary']['currier_a_pages']} A pages, {results['summary']['currier_b_pages']} B pages"
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"✅ State file updated")


if __name__ == "__main__":
    main()
