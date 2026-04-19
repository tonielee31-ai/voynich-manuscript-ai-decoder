#!/usr/bin/env python3
"""
Voynich Crib Finder - Extract Known Words from Illustrations
=============================================================
Based on research gap: "no_confirmed_words"
Inspired by: Rosetta Stone (parallel text) + Enigma (crib-based attacks)

Strategy:
1. Identify zodiac labels (month names)
2. Map botanical illustrations to herb names
3. Find numbers in astronomical sections
4. Detect proper nouns from repeated patterns

These become "cribs" - known plaintext that constrains the cipher.

Usage:
    python3 crib-finder.py --eva eva-takahashi.txt
"""

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")


# ============================================================
# CRIB CANDIDATES FROM KNOWN ILLUSTRATION CONTEXTS
# ============================================================

# Zodiac month names (if manuscript has zodiac pages)
ZODIAC_LABELS = {
    'aries': ['ariete', 'aries', 'taleh'],
    'taurus': ['toro', 'taurus', 'shor'],
    'gemini': ['gemelli', 'gemini', 'teomim'],
    'cancer': ['cancro', 'cancer', 'sartan'],
    'leo': ['leone', 'leo', 'arye'],
    'virgo': ['vergine', 'virgo', 'betulah'],
    'libra': ['bilancia', 'libra', 'moznayim'],
    'scorpio': ['scorpione', 'scorpio', 'aqrav'],
    'sagittarius': ['sagittario', 'sagittarius', 'kashat'],
    'capricorn': ['capricorno', 'capricorn', 'gedi'],
    'aquarius': ['acquario', 'aquarius', 'dli'],
    'pisces': ['pesci', 'pisces', 'dagim']
}

# Common herbs in medieval herbals (Caspari/Faccini context)
MEDIEVAL_HERBS = [
    'salvia', 'menta', 'rosmarino', 'basilico', 'timo', 'origano',
    'lavanda', 'camomilla', 'verbena', 'ruta', 'alloro', 'olivo',
    'finocchio', 'cumino', 'anice', 'zafferano', 'cannella', 'garofano',
    'oppio', 'balsamo', 'ortica', 'assenzio', 'giglio', 'rosa',
    'viola', 'malva', 'plantago', 'artemisia', 'achillea', 'calendula'
]

# Astronomical/astrological terms
ASTRONOMICAL_TERMS = [
    'sole', 'luna', 'stella', 'pianeta', 'segno', 'eclisse',
    'saturno', 'giove', 'marte', 'venere', 'mercurio',
    'oroscopo', 'ascendente', 'domificazione'
]

# Medical/body terms (balneological section)
MEDICAL_TERMS = [
    'cuore', 'testa', 'occhio', 'naso', 'bocca', 'mano', 'piede',
    'sangue', 'acqua', 'olio', 'sale', 'miele', 'vino',
    'febbre', 'dolore', 'tosse', 'cura', 'rimedio', 'medicina'
]


class CribFinder:
    """Find potential cribs in Voynich text based on illustration context."""
    
    def __init__(self, text):
        self.text = text
        self.lines = text.split('\n')
        self.words = text.split()
        
        # Word frequency
        self.word_freq = Counter(self.words)
        
        # Page sections
        self.pages = self._parse_pages()
        
        # Position analysis
        self.line_start_words = Counter()
        self.line_end_words = Counter()
        for line in self.lines:
            words = line.split()
            if words:
                self.line_start_words[words[0]] += 1
                self.line_end_words[words[-1]] += 1
    
    def _parse_pages(self):
        """Parse manuscript into pages."""
        pages = {}
        current_page = 'f1r'
        current_words = []
        
        for line in self.lines:
            if line.startswith('f') and len(line) > 2:
                parts = line.split()
                if parts:
                    marker = parts[0]
                    if ('r' in marker[:4] or 'v' in marker[:4]):
                        if current_words:
                            pages[current_page] = current_words
                        current_page = marker
                        current_words = []
                        continue
            current_words.extend(line.split())
        
        if current_words:
            pages[current_page] = current_words
        
        return pages
    
    def find_zodiac_labels(self):
        """Find potential zodiac labels based on position patterns."""
        candidates = []
        
        # Words that appear at line beginnings (potential labels)
        for word, count in self.line_start_words.most_common(20):
            if count >= 3:  # Appears at start multiple times
                # Check if it's short (labels are usually short)
                if 3 <= len(word) <= 8:
                    candidates.append({
                        'word': word,
                        'count': count,
                        'type': 'line_start_label',
                        'possible_meanings': list(ZODIAC_LABELS.keys())[:3]
                    })
        
        return candidates
    
    def find_repeated_patterns(self):
        """Find words that repeat at regular intervals (potential markers)."""
        candidates = []
        
        # Find words with high repetition
        for word, count in self.word_freq.most_common(30):
            if count >= 5:
                # Find positions
                positions = [i for i, w in enumerate(self.words) if w == word]
                
                # Calculate intervals
                if len(positions) >= 3:
                    intervals = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
                    avg_interval = sum(intervals) / len(intervals)
                    
                    # Low variance = regular pattern
                    variance = sum((i - avg_interval)**2 for i in intervals) / len(intervals)
                    
                    if variance < avg_interval * 0.5:
                        candidates.append({
                            'word': word,
                            'count': count,
                            'avg_interval': round(avg_interval, 1),
                            'variance': round(variance, 1),
                            'type': 'regular_marker',
                            'interpretation': 'Possible section marker or structural element'
                        })
        
        return candidates
    
    def find_potential_names(self):
        """Find words that could be proper nouns."""
        candidates = []
        
        # Words that appear isolated (surrounded by different words)
        for i, word in enumerate(self.words):
            if 4 <= len(word) <= 10:
                # Check context
                prev_word = self.words[i-1] if i > 0 else ''
                next_word = self.words[i+1] if i < len(self.words)-1 else ''
                
                # Unique context = potential name
                if prev_word != word and next_word != word:
                    if self.word_freq[word] <= 5:  # Rare = likely name
                        candidates.append({
                            'word': word,
                            'frequency': self.word_freq[word],
                            'type': 'potential_name',
                            'context': f"{prev_word} {word} {next_word}"
                        })
        
        # Deduplicate
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c['word'] not in seen:
                seen.add(c['word'])
                unique_candidates.append(c)
        
        return sorted(unique_candidates, key=lambda x: -x['frequency'])[:20]
    
    def find_herb_labels(self):
        """Find potential herb labels based on botanical section patterns."""
        candidates = []
        
        # In herbal sections, labels often appear near the beginning of lines
        # and are followed by descriptive text
        
        for line in self.lines[:500]:  # Focus on first pages (herbal section)
            words = line.split()
            if len(words) >= 3:
                # First word might be label
                label_candidate = words[0]
                if 3 <= len(label_candidate) <= 8:
                    candidates.append({
                        'word': label_candidate,
                        'line_preview': ' '.join(words[:5]),
                        'type': 'herb_label_candidate',
                        'possible_meanings': MEDIEVAL_HERBS[:3]
                    })
        
        # Count and return most common
        label_counts = Counter(c['word'] for c in candidates)
        return [
            {'word': word, 'count': count, 'type': 'herb_label', 'possible_meanings': MEDIEVAL_HERBS[:5]}
            for word, count in label_counts.most_common(15)
            if count >= 2
        ]
    
    def generate_cribs(self):
        """Generate crib mappings for evolutionary computation."""
        cribs = []
        
        # From zodiac labels
        zodiac = self.find_zodiac_labels()
        if zodiac:
            for z in zodiac[:3]:
                # Guess first few characters
                word = z['word']
                # Simple heuristic: map to Italian month abbreviation
                for month_italian in ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic']:
                    if len(word) == len(month_italian):
                        crib_mapping = {w: m for w, m in zip(word, month_italian) if w.isalpha() and m.isalpha()}
                        if crib_mapping:
                            cribs.append({
                                'source': f'zodiac_{z["word"]}',
                                'mapping': crib_mapping,
                                'confidence': 0.3,
                                'rationale': 'Zodiac label hypothesis'
                            })
        
        # From repeated patterns
        markers = self.find_repeated_patterns()
        if markers:
            # 'daiin' is the most common word - might be "and" or section marker
            top_marker = markers[0]
            if top_marker['word'] == 'daiin':
                cribs.append({
                    'source': 'daiin_as_and',
                    'mapping': {'d': 'e', 'a': 't', 'i': 'n', 'n': 'd'},
                    'confidence': 0.4,
                    'rationale': 'Most common word = likely conjunction or marker'
                })
        
        return cribs
    
    def full_analysis(self):
        """Run complete crib analysis."""
        results = {
            'zodiac_labels': self.find_zodiac_labels(),
            'repeated_patterns': self.find_repeated_patterns(),
            'potential_names': self.find_potential_names(),
            'herb_labels': self.find_herb_labels(),
            'generated_cribs': self.generate_cribs(),
            'summary': {}
        }
        
        # Summary
        results['summary'] = {
            'total_words': len(self.words),
            'unique_words': len(self.word_freq),
            'zodiac_candidates': len(results['zodiac_labels']),
            'regular_markers': len(results['repeated_patterns']),
            'potential_names': len(results['potential_names']),
            'herb_candidates': len(results['herb_labels']),
            'cribs_generated': len(results['generated_cribs'])
        }
        
        return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 crib-finder.py <eva_file> [--json]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    with open(filepath, 'r') as f:
        text = f.read()
    
    finder = CribFinder(text)
    results = finder.full_analysis()
    
    if '--json' in sys.argv:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("=" * 60)
        print("VOYNICH CRIB FINDER")
        print("=" * 60)
        
        print(f"\n📊 ZODIAC LABELS")
        print("-" * 40)
        for z in results['zodiac_labels'][:5]:
            print(f"  '{z['word']}' ({z['count']}x) - {z['type']}")
        
        print(f"\n📊 REPEATED PATTERNS (Structural Markers)")
        print("-" * 40)
        for p in results['repeated_patterns'][:5]:
            print(f"  '{p['word']}' ({p['count']}x, interval={p['avg_interval']})")
            print(f"    → {p['interpretation']}")
        
        print(f"\n📊 POTENTIAL NAMES")
        print("-" * 40)
        for n in results['potential_names'][:5]:
            print(f"  '{n['word']}' ({n['frequency']}x) - {n['context']}")
        
        print(f"\n📊 HERB LABELS")
        print("-" * 40)
        for h in results['herb_labels'][:5]:
            print(f"  '{h['word']}' ({h['count']}x) - possible: {', '.join(h['possible_meanings'][:3])}")
        
        print(f"\n📊 GENERATED CRIBS")
        print("-" * 40)
        for c in results['generated_cribs']:
            print(f"  {c['source']}: {c['mapping']}")
            print(f"    Confidence: {c['confidence']}, Rationale: {c['rationale']}")
        
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        s = results['summary']
        print(f"  Total words: {s['total_words']}")
        print(f"  Unique words: {s['unique_words']}")
        print(f"  Zodiac candidates: {s['zodiac_candidates']}")
        print(f"  Regular markers: {s['regular_markers']}")
        print(f"  Potential names: {s['potential_names']}")
        print(f"  Herb candidates: {s['herb_candidates']}")
        print(f"  Cribs generated: {s['cribs_generated']}")
    
    # Save
    output = os.path.join(PROJECT_DIR, 'research-output', 'crib-analysis.json')
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Saved to {output}")


if __name__ == "__main__":
    main()
