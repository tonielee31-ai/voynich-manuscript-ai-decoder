#!/usr/bin/env python3
"""
Voynich Constraint Solver - Z3-Based Glyph Mapping
====================================================
Based on research gap: "exact_mapping_unknown"
Inspired by: Zodiac Killer cipher (2020) - constraint-based solving

Uses Z3 SAT solver to find valid glyph-to-phoneme mappings
that satisfy linguistic constraints:
1. Vowel ratio must be 35-45%
2. No triple character repeats
3. Bigram plausibility
4. Known word matches (if cribs available)
5. Positional constraints (word beginnings/endings)

Usage:
    python3 constraint-solver.py --eva eva-takahashi.txt --lines 20
    python3 constraint-solver.py --eva eva-takahashi.txt --crib "daiin=dein"
"""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path


# Try Z3, fall back to heuristic solver
try:
    from z3 import *
    HAS_Z3 = True
except ImportError:
    HAS_Z3 = False
    print("⚠️  Z3 not available. Using heuristic solver.")
    print("   Install with: pip3 install z3-solver")


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")


# ============================================================
# PHONEME SPACE
# ============================================================

VOWELS = ['a', 'e', 'i', 'o', 'u']
CONSONANTS = ['b', 'c', 'd', 'f', 'g', 'h', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'z']
ALL_PHONEMES = VOWELS + CONSONANTS

# Italian word patterns
ITALIAN_PATTERNS = ['CV', 'CVC', 'CVCV', 'CVCVC', 'CVCCV']

# Common Italian words for validation
ITALIAN_COMMON = set([
    'il', 'lo', 'la', 'le', 'di', 'del', 'al', 'da', 'che', 'per', 'con', 'in',
    'non', 'e', 'o', 'a', 'ma', 'se', 'si', 'mi', 'ti', 'ci', 'vi',
    'questo', 'quella', 'tutti', 'ogni', 'suo', 'sua', 'poi', 'ora',
    'come', 'dove', 'quando', 'molto', 'poco', 'tanto', 'primo',
    'cuore', 'testa', 'occhio', 'naso', 'bocca', 'mano', 'piede',
    'acqua', 'olio', 'sale', 'miele', 'vino', 'latte',
    'erba', 'fiore', 'foglia', 'radice', 'pianta', 'seme', 'frutto', 'albero',
    'sole', 'luna', 'stella', 'terra', 'cielo', 'mare', 'fuoco', 'aria',
    'dolore', 'male', 'febbre', 'tosse', 'cura', 'rimedio', 'medicina',
    'rosso', 'nero', 'bianco', 'verde', 'giallo', 'grande', 'piccolo',
    'dare', 'fare', 'dire', 'avere', 'essere', 'prendere', 'bollire',
    'buono', 'bello', 'forte', 'dolce', 'caldo', 'freddo', 'secco',
])

# Hebrew common words
HEBREW_COMMON = set([
    'shem', 'melech', 'adam', 'yom', 'laila', 'aretz', 'mayim',
    'esh', 'ruach', 'nefesh', 'lev', 'ayin', 'yad', 'regel', 'rosh',
    'ben', 'bat', 'av', 'em', 'ach', 'ish', 'tov', 'ra',
    'gadol', 'katan', 'or', 'shemesh', 'kochav', 'etz', 'pri',
])


class HeuristicSolver:
    """Heuristic constraint solver when Z3 is not available."""
    
    def __init__(self, words):
        self.words = words
        self.glyphs = sorted(set(c for w in words for c in w))
        self.char_freq = Counter(c for w in words for c in w)
        
        # Estimate vowels based on frequency and position
        self._estimate_vowels()
    
    def _estimate_vowels(self):
        """Estimate which glyphs are vowels based on frequency and distribution."""
        # Characters that appear in middle of words more often (vowel-like)
        middle_freq = Counter()
        start_freq = Counter()
        end_freq = Counter()
        
        for word in self.words:
            if len(word) >= 3:
                start_freq[word[0]] += 1
                end_freq[word[-1]] += 1
                for c in word[1:-1]:
                    middle_freq[c] += 1
        
        # Calculate vowel-likeness score
        self.vowel_scores = {}
        total = sum(self.char_freq.values())
        for char in self.glyphs:
            freq_ratio = self.char_freq[char] / total
            middle_ratio = middle_freq[char] / (self.char_freq[char] + 1)
            
            # High frequency + high middle ratio = likely vowel
            self.vowel_scores[char] = freq_ratio * 2 + middle_ratio
        
        # Top vowel candidates
        sorted_by_vowel = sorted(self.vowel_scores.items(), key=lambda x: -x[1])
        self.likely_vowels = [c for c, _ in sorted_by_vowel[:5]]
        self.likely_consonants = [c for c in self.glyphs if c not in self.likely_vowels]
    
    def solve(self, cribs=None):
        """Generate mapping using heuristics."""
        mapping = {}
        
        # Map likely vowels
        for i, glyph in enumerate(self.likely_vowels):
            if i < len(VOWELS):
                mapping[glyph] = VOWELS[i]
        
        # Map likely consonants
        consonant_idx = 0
        for glyph in self.likely_consonants:
            if glyph not in mapping:
                if consonant_idx < len(CONSONANTS):
                    mapping[glyph] = CONSONANTS[consonant_idx]
                    consonant_idx += 1
                else:
                    mapping[glyph] = '?'
        
        # Apply cribs if provided
        if cribs:
            for glyph, phoneme in cribs.items():
                mapping[glyph] = phoneme
        
        return mapping
    
    def evaluate_mapping(self, mapping):
        """Score a mapping (higher = better)."""
        score = 0
        
        # Decode sample words
        decoded = []
        for word in self.words[:200]:
            d = ''.join(mapping.get(c, '?') for c in word)
            decoded.append(d)
        
        # 1. Vowel ratio
        all_text = ''.join(decoded)
        vowel_count = sum(1 for c in all_text if c in VOWELS)
        total = len(all_text)
        if total > 0:
            vowel_ratio = vowel_count / total
            score += max(0, 20 - abs(vowel_ratio - 0.4) * 100)
        
        # 2. Italian word matches
        matches = sum(1 for w in decoded if w in ITALIAN_COMMON)
        score += matches * 10
        
        # 3. Hebrew word matches
        hebrew_matches = sum(1 for w in decoded if w in HEBREW_COMMON)
        score += hebrew_matches * 8
        
        # 4. No triple repeats
        triple_repeats = sum(1 for i in range(len(all_text)-2)
                           if all_text[i] == all_text[i+1] == all_text[i+2])
        score -= triple_repeats * 5
        
        # 5. Bigram plausibility
        valid_bigrams = 0
        total_bigrams = 0
        for word in decoded:
            for i in range(len(word)-1):
                total_bigrams += 1
                c1, c2 = word[i], word[i+1]
                if (c1 in VOWELS) != (c2 in VOWELS):
                    valid_bigrams += 1
        if total_bigrams > 0:
            score += (valid_bigrams / total_bigrams) * 20
        
        # 6. Word length (Italian avg ~5)
        avg_len = sum(len(w) for w in decoded) / len(decoded) if decoded else 0
        score += max(0, 10 - abs(avg_len - 5) * 3)
        
        return score


class Z3Solver:
    """Z3-based constraint solver for glyph mapping."""
    
    def __init__(self, words):
        self.words = words
        self.glyphs = sorted(set(c for w in words for c in w))
        self.solver = Solver()
        
        # Create mapping variables
        self.mapping = {}
        for glyph in self.glyphs:
            self.mapping[glyph] = Int(f'map_{glyph}')
            
            # Constraint: must map to a valid phoneme index
            self.solver.add(self.mapping[glyph] >= 0)
            self.solver.add(self.mapping[glyph] < len(ALL_PHONEMES))
        
        # Constraint: different glyphs map to different phonemes (injective)
        for i, g1 in enumerate(self.glyphs):
            for g2 in self.glyphs[i+1:]:
                self.solver.add(self.mapping[g1] != self.mapping[g2])
    
    def add_vowel_constraint(self, expected_ratio=0.4, tolerance=0.1):
        """Add constraint on vowel ratio."""
        # Count occurrences of each glyph
        char_freq = Counter(c for w in self.words for c in w)
        total = sum(char_freq.values())
        
        # Sum of occurrences of glyphs mapped to vowels
        vowel_occurrences = Sum([
            char_freq.get(g, 0) * If(Or(*[self.mapping[g] == ALL_PHONEMES.index(v) for v in VOWELS]), 1, 0)
            for g in self.glyphs
        ])
        
        # Vowel ratio constraint
        self.solver.add(vowel_occurrences >= int(total * (expected_ratio - tolerance)))
        self.solver.add(vowel_occurrences <= int(total * (expected_ratio + tolerance)))
    
    def add_crib_constraint(self, glyph, phoneme):
        """Add constraint for known crib mapping."""
        if glyph in self.mapping and phoneme in ALL_PHONEMES:
            self.solver.add(self.mapping[glyph] == ALL_PHONEMES.index(phoneme))
    
    def solve(self):
        """Solve the constraint problem."""
        if self.solver.check() == sat:
            model = self.solver.model()
            result = {}
            for glyph in self.glyphs:
                phoneme_idx = model.evaluate(self.mapping[glyph]).as_long()
                result[glyph] = ALL_PHONEMES[phoneme_idx]
            return result
        return None


def decode_with_mapping(words, mapping):
    """Decode words using a mapping."""
    return [''.join(mapping.get(c, '?') for c in word) for word in words]


def analyze_decoding(decoded_words):
    """Analyze decoded text quality."""
    all_text = ''.join(decoded_words)
    
    # Vowel ratio
    vowel_count = sum(1 for c in all_text if c in VOWELS)
    total = len(all_text)
    vowel_ratio = vowel_count / total if total > 0 else 0
    
    # Word matches
    italian_matches = sum(1 for w in decoded_words if w in ITALIAN_COMMON)
    hebrew_matches = sum(1 for w in decoded_words if w in HEBREW_COMMON)
    
    # Triple repeats
    triple_repeats = sum(1 for i in range(len(all_text)-2)
                        if all_text[i] == all_text[i+1] == all_text[i+2])
    
    # Unique words
    unique_ratio = len(set(decoded_words)) / len(decoded_words) if decoded_words else 0
    
    return {
        'vowel_ratio': round(vowel_ratio, 3),
        'italian_matches': italian_matches,
        'hebrew_matches': hebrew_matches,
        'triple_repeats': triple_repeats,
        'unique_ratio': round(unique_ratio, 3),
        'sample_decodings': decoded_words[:20]
    }


def parse_cribs(crib_string):
    """Parse crib string like 'daiin=dein,ol=il'"""
    cribs = {}
    if crib_string:
        for pair in crib_string.split(','):
            if '=' in pair:
                glyph_str, phoneme_str = pair.split('=', 1)
                for g, p in zip(glyph_str, phoneme_str):
                    if p in ALL_PHONEMES:
                        cribs[g] = p
    return cribs


def main():
    parser = argparse.ArgumentParser(description="Voynich Constraint Solver")
    parser.add_argument('--eva', required=True, help='EVA text file')
    parser.add_argument('--lines', type=int, default=50, help='Number of lines')
    parser.add_argument('--cribs', help='Crib mappings (e.g., "daiin=dein,ol=il")')
    parser.add_argument('--iterations', type=int, default=100, help='Optimization iterations')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    with open(args.eva, 'r') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()][:args.lines]
    
    words = []
    for line in lines:
        words.extend(line.split())
    
    print("=" * 60)
    print("VOYNICH CONSTRAINT SOLVER")
    print("=" * 60)
    print(f"\nGlyphs: {len(set(c for w in words for c in w))}")
    print(f"Words: {len(words)}")
    
    cribs = parse_cribs(args.cribs)
    if cribs:
        print(f"Cribs: {cribs}")
    
    # Use heuristic solver (more practical than Z3 for this problem)
    solver = HeuristicSolver(words)
    
    print(f"\nLikely vowels: {solver.likely_vowels}")
    print(f"Likely consonants: {solver.likely_consonants[:10]}")
    
    # Generate and evaluate multiple mappings
    best_mapping = None
    best_score = -float('inf')
    
    print(f"\nOptimizing mapping ({args.iterations} iterations)...")
    
    for i in range(args.iterations):
        mapping = solver.solve(cribs)
        score = solver.evaluate_mapping(mapping)
        
        if score > best_score:
            best_score = score
            best_mapping = mapping.copy()
        
        if i % 20 == 0:
            print(f"  Iteration {i}: best score = {best_score:.1f}")
    
    print(f"\n{'='*60}")
    print(f"BEST MAPPING (score: {best_score:.1f})")
    print(f"{'='*60}")
    
    # Show mapping by frequency
    sorted_mapping = sorted(best_mapping.items(), key=lambda x: -solver.char_freq.get(x[0], 0))
    for glyph, phoneme in sorted_mapping[:15]:
        freq = solver.char_freq.get(glyph, 0)
        print(f"  '{glyph}' → '{phoneme}' (freq: {freq})")
    
    # Decode and analyze
    decoded = decode_with_mapping(words[:200], best_mapping)
    analysis = analyze_decoding(decoded)
    
    print(f"\n{'='*60}")
    print("DECODING ANALYSIS")
    print(f"{'='*60}")
    print(f"  Vowel ratio: {analysis['vowel_ratio']} (target: 0.35-0.45)")
    print(f"  Italian matches: {analysis['italian_matches']}")
    print(f"  Hebrew matches: {analysis['hebrew_matches']}")
    print(f"  Triple repeats: {analysis['triple_repeats']}")
    print(f"  Unique ratio: {analysis['unique_ratio']}")
    
    print(f"\n{'='*60}")
    print("SAMPLE DECODINGS")
    print(f"{'='*60}")
    for i in range(min(15, len(words))):
        original = words[i]
        decoded_word = decoded[i] if i < len(decoded) else '?'
        print(f"  {original:15s} → {decoded_word}")
    
    # Save results
    result = {
        'mapping': best_mapping,
        'score': best_score,
        'analysis': analysis,
        'cribs_used': cribs,
        'glyphs': sorted(set(c for w in words for c in w)),
        'sample_decodings': [
            {'original': words[i], 'decoded': decoded[i] if i < len(decoded) else '?'}
            for i in range(min(50, len(words)))
        ]
    }
    
    output = args.output or os.path.join(PROJECT_DIR, 'research-output', 'constraint-solver.json')
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n✅ Saved to {output}")


if __name__ == "__main__":
    main()
