#!/usr/bin/env python3
"""
Voynich Manuscript - Mathematical Pattern Analyzer
===================================================
Based on arxiv:2505.02261 - "Voynich Codex Decoded - Statistical Symbolism"

Detects mathematical patterns in Voynich text:
- Prime number grouping
- Fibonacci sequence clustering
- Golden ratio alignment
- Scroll-wide sequencing

Usage:
    python3 math-patterns.py --eva eva-takahashi.txt
"""

import json
import math
import os
import sys
from collections import Counter, defaultdict


def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def fibonacci_up_to(n):
    fibs = [1, 1]
    while fibs[-1] < n:
        fibs.append(fibs[-1] + fibs[-2])
    return set(fibs)

PHI = (1 + math.sqrt(5)) / 2  # Golden ratio


class MathPatternAnalyzer:
    """Analyze mathematical patterns in Voynich text."""
    
    def __init__(self, text):
        self.text = text
        self.lines = text.split('\n')
        self.words = text.split()
        
        # Word lengths
        self.word_lengths = [len(w) for w in self.words]
        
        # Character positions
        self.chars = [c for c in text.lower() if c.strip()]
        
        # Line lengths
        self.line_lengths = [len(l.split()) for l in self.lines if l.strip()]
    
    def prime_patterns(self):
        """Detect prime number patterns."""
        primes_found = []
        prime_word_positions = []
        
        # Check word positions
        for i, length in enumerate(self.word_lengths):
            if is_prime(length):
                prime_word_positions.append(i)
        
        # Check line lengths
        prime_line_lengths = [l for l in self.line_lengths if is_prime(l)]
        
        # Check character frequencies
        char_freq = Counter(self.chars)
        prime_freq_chars = {c: f for c, f in char_freq.items() if is_prime(f)}
        
        # Check consecutive prime word lengths
        consecutive_primes = 0
        max_consecutive = 0
        for length in self.word_lengths:
            if is_prime(length):
                consecutive_primes += 1
                max_consecutive = max(max_consecutive, consecutive_primes)
            else:
                consecutive_primes = 0
        
        return {
            'prime_word_lengths': len(prime_word_positions),
            'prime_word_ratio': round(len(prime_word_positions) / len(self.word_lengths), 3) if self.word_lengths else 0,
            'prime_line_lengths': len(prime_line_lengths),
            'max_consecutive_prime_words': max_consecutive,
            'prime_frequency_chars': len(prime_freq_chars),
            'expected_prime_ratio': 0.28,  # ~28% of numbers 1-20 are prime
            'analysis': 'HIGH prime clustering' if len(prime_word_positions) / len(self.word_lengths) > 0.35 else 'Normal' if self.word_lengths else 'N/A'
        }
    
    def fibonacci_patterns(self):
        """Detect Fibonacci sequence patterns."""
        fibs = fibonacci_up_to(max(self.word_lengths) if self.word_lengths else 20)
        
        # Words with Fibonacci lengths
        fib_word_positions = []
        for i, length in enumerate(self.word_lengths):
            if length in fibs:
                fib_word_positions.append(i)
        
        # Fibonacci clustering in consecutive words
        fib_clusters = []
        current_cluster = []
        for i, length in enumerate(self.word_lengths):
            if length in fibs:
                current_cluster.append(i)
            else:
                if len(current_cluster) >= 3:
                    fib_clusters.append(current_cluster)
                current_cluster = []
        if len(current_cluster) >= 3:
            fib_clusters.append(current_cluster)
        
        # Fibonacci in line lengths
        fib_line_lengths = [l for l in self.line_lengths if l in fibs]
        
        return {
            'fibonacci_word_lengths': len(fib_word_positions),
            'fibonacci_word_ratio': round(len(fib_word_positions) / len(self.word_lengths), 3) if self.word_lengths else 0,
            'fibonacci_clusters_3plus': len(fib_clusters),
            'fibonacci_line_lengths': len(fib_line_lengths),
            'expected_fib_ratio': 0.15,  # ~15% of numbers 1-20 are Fibonacci
            'analysis': 'HIGH Fibonacci clustering' if len(fib_word_positions) / len(self.word_lengths) > 0.25 else 'Normal' if self.word_lengths else 'N/A'
        }
    
    def golden_ratio_patterns(self):
        """Detect golden ratio alignment."""
        phi = PHI
        
        # Check ratio between consecutive word lengths
        phi_ratios = []
        for i in range(len(self.word_lengths) - 1):
            if self.word_lengths[i] > 0 and self.word_lengths[i+1] > 0:
                ratio = max(self.word_lengths[i], self.word_lengths[i+1]) / min(self.word_lengths[i], self.word_lengths[i+1])
                if abs(ratio - phi) < 0.1:  # Within 0.1 of golden ratio
                    phi_ratios.append((i, ratio))
        
        # Check ratio between consecutive line lengths
        phi_line_ratios = []
        for i in range(len(self.line_lengths) - 1):
            if self.line_lengths[i] > 0 and self.line_lengths[i+1] > 0:
                ratio = max(self.line_lengths[i], self.line_lengths[i+1]) / min(self.line_lengths[i], self.line_lengths[i+1])
                if abs(ratio - phi) < 0.15:  # Within 0.15 of golden ratio
                    phi_line_ratios.append((i, ratio))
        
        return {
            'golden_ratio_word_pairs': len(phi_ratios),
            'golden_ratio_line_pairs': len(phi_line_ratios),
            'phi_value': round(phi, 4),
            'analysis': 'HIGH golden ratio alignment' if len(phi_ratios) > len(self.word_lengths) * 0.1 else 'Normal' if self.word_lengths else 'N/A'
        }
    
    def scroll_sequencing(self):
        """Analyze scroll-wide sequencing patterns."""
        # Character position entropy (beginning vs middle vs end of text)
        third = len(self.chars) // 3
        if third > 0:
            beginning = self.chars[:third]
            middle = self.chars[third:2*third]
            end = self.chars[2*third:]
            
            def char_entropy(chars):
                freq = Counter(chars)
                total = len(chars)
                h = 0
                for count in freq.values():
                    p = count / total
                    if p > 0:
                        h -= p * math.log2(p)
                return round(h, 3)
            
            entropy_by_section = {
                'beginning': char_entropy(beginning),
                'middle': char_entropy(middle),
                'end': char_entropy(end)
            }
        else:
            entropy_by_section = {'beginning': 0, 'middle': 0, 'end': 0}
        
        # Word frequency drift across manuscript
        section_size = max(1, len(self.words) // 5)
        top_words_by_section = []
        for i in range(5):
            start = i * section_size
            end = min((i+1) * section_size, len(self.words))
            section_words = self.words[start:end]
            freq = Counter(section_words)
            top_words_by_section.append(freq.most_common(3))
        
        return {
            'entropy_by_section': entropy_by_section,
            'top_words_by_section': [dict(tw) for tw in top_words_by_section],
            'analysis': 'Structured scroll' if abs(entropy_by_section.get('beginning', 0) - entropy_by_section.get('end', 0)) > 0.3 else 'Uniform'
        }
    
    def full_analysis(self):
        """Run all mathematical pattern analyses."""
        results = {
            'prime_patterns': self.prime_patterns(),
            'fibonacci_patterns': self.fibonacci_patterns(),
            'golden_ratio': self.golden_ratio_patterns(),
            'scroll_sequencing': self.scroll_sequencing(),
            'summary': {}
        }
        
        # Summary
        prime = results['prime_patterns']
        fib = results['fibonacci_patterns']
        phi = results['golden_ratio']
        
        results['summary'] = {
            'prime_clustering': prime['analysis'],
            'fibonacci_clustering': fib['analysis'],
            'golden_ratio_alignment': phi['analysis'],
            'overall_assessment': (
                'STRONG mathematical structure detected' if
                prime['prime_word_ratio'] > 0.35 or fib['fibonacci_word_ratio'] > 0.25 or phi['golden_ratio_word_pairs'] > 50
                else 'Normal linguistic patterns'
            ) if self.word_lengths else 'Insufficient data'
        }
        
        return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 math-patterns.py <eva_file> [--json]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    analyzer = MathPatternAnalyzer(text)
    results = analyzer.full_analysis()
    
    if '--json' in sys.argv:
        print(json.dumps(results, indent=2))
    else:
        print("=" * 60)
        print("MATHEMATICAL PATTERN ANALYSIS")
        print("(Based on arxiv:2505.02261)")
        print("=" * 60)
        
        print("\n📊 PRIME NUMBER PATTERNS")
        print("-" * 40)
        p = results['prime_patterns']
        print(f"  Words with prime lengths: {p['prime_word_lengths']} ({p['prime_word_ratio']*100:.1f}%)")
        print(f"  Expected: ~{p['expected_prime_ratio']*100:.0f}%")
        print(f"  Max consecutive prime words: {p['max_consecutive_prime_words']}")
        print(f"  Assessment: {p['analysis']}")
        
        print("\n📊 FIBONACCI PATTERNS")
        print("-" * 40)
        f = results['fibonacci_patterns']
        print(f"  Words with Fibonacci lengths: {f['fibonacci_word_lengths']} ({f['fibonacci_word_ratio']*100:.1f}%)")
        print(f"  Expected: ~{f['expected_fib_ratio']*100:.0f}%")
        print(f"  Fibonacci clusters (3+): {f['fibonacci_clusters_3plus']}")
        print(f"  Assessment: {f['analysis']}")
        
        print("\n📊 GOLDEN RATIO")
        print("-" * 40)
        g = results['golden_ratio']
        print(f"  φ = {g['phi_value']}")
        print(f"  Word pairs near φ ratio: {g['golden_ratio_word_pairs']}")
        print(f"  Line pairs near φ ratio: {g['golden_ratio_line_pairs']}")
        print(f"  Assessment: {g['analysis']}")
        
        print("\n📊 SCROLL SEQUENCING")
        print("-" * 40)
        s = results['scroll_sequencing']
        print(f"  Character entropy by section:")
        for section, entropy in s['entropy_by_section'].items():
            print(f"    {section}: {entropy}")
        print(f"  Assessment: {s['analysis']}")
        
        print(f"\n{'='*60}")
        print(f"OVERALL: {results['summary']['overall_assessment']}")
        print("=" * 60)
    
    # Save
    output = 'research-output/math-patterns.json'
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Saved to {output}")


if __name__ == "__main__":
    main()
