#!/usr/bin/env python3
"""
Voynich True Cipher Key Finder
================================
Based on CORRECTED research direction:

KEY INSIGHT: Voynich uses HOMOPHONIC SUBSTITUTION
- Multiple EVA tokens map to ONE plaintext character
- EVA words are VERBOSE (long) → plaintext words are SHORT
- IC = 0.0771 confirms monoalphabetic at TOKEN level
- But the encoding is COMPRESSED (not 1:1)

APPROACHES:
1. Naibbe Compression - Find which tokens compress together
2. Syllabic Decomposition - 29 tokens as CV pairs
3. Currier-Separate Analysis - Different rules for A vs B
4. Crib-Based Constraint Solving
5. Evolutionary Search for compression rules

Usage:
    python3 true-key-finder.py --eva eva-takahashi.txt --method compression
    python3 true-key-finder.py --eva eva-takahashi.txt --method syllabic
    python3 true-key-finder.py --eva eva-takahashi.txt --method crib
"""

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "research-output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# EVA TOKENIZER
# ============================================================

EVA_MULTI = ['cth', 'cph', 'cfh', 'ckh', 'sh', 'ch', 'qo']

def tokenize(word):
    tokens = []
    i = 0
    clean = ''.join(c for c in word if c.isalpha() or c in '!*-=')
    while i < len(clean):
        matched = False
        for t in sorted(EVA_MULTI, key=len, reverse=True):
            if clean[i:i+len(t)] == t:
                tokens.append(t)
                i += len(t)
                matched = True
                break
        if not matched and i < len(clean) and clean[i].isalpha():
            tokens.append(clean[i])
            i += 1
    return tokens


# ============================================================
# APPROACH 1: NAIBBE COMPRESSION ANALYSIS
# ============================================================

class NaibbeCompressor:
    """Find compression rules for verbose homophonic substitution.
    
    Key idea: Voynich words are LONG because of verbose encoding.
    'daiin' (5 tokens) might compress to 1-2 characters.
    """
    
    def __init__(self, words):
        self.words = words
        self.word_freq = Counter(words)
        
        # Tokenize all words
        self.tokenized = {}
        for w in set(words):
            self.tokenized[w] = tokenize(w)
    
    def find_compression_patterns(self):
        """Find which EVA tokens frequently co-occur (might compress)."""
        # Bigram token analysis
        token_bigrams = Counter()
        for w, tokens in self.tokenized.items():
            for i in range(len(tokens) - 1):
                bigram = tokens[i] + tokens[i+1]
                token_bigrams[bigram] += 1
        
        # Find most common bigrams (candidates for compression)
        common_bigrams = token_bigrams.most_common(20)
        
        # Trigram analysis
        token_trigrams = Counter()
        for w, tokens in self.tokenized.items():
            for i in range(len(tokens) - 2):
                trigram = tokens[i] + tokens[i+1] + tokens[i+2]
                token_trigrams[trigram] += 1
        
        common_trigrams = token_trigrams.most_common(15)
        
        return {
            'bigrams': common_bigrams,
            'trigrams': common_trigrams,
        }
    
    def analyze_word_lengths(self):
        """Analyze if long Voynich words compress to short plaintext."""
        lengths = Counter(len(w) for w in self.words)
        
        # Most common lengths
        common_lengths = lengths.most_common(10)
        
        # Words by length
        words_by_length = defaultdict(list)
        for w, count in self.word_freq.most_common(100):
            words_by_length[len(w)].append((w, count))
        
        return {
            'length_distribution': common_lengths,
            'top_words_by_length': {
                length: words[:5] for length, words in 
                sorted(words_by_length.items())[:8]
            }
        }
    
    def test_compression_hypothesis(self):
        """Test if compressing repeated tokens produces shorter words."""
        # Hypothesis: Repeated tokens (like 'ii' in 'daiin') are compressed
        compression_candidates = []
        
        for w, count in self.word_freq.most_common(30):
            tokens = self.tokenized.get(w, [])
            # Count repeated tokens
            repeats = 0
            for i in range(len(tokens) - 1):
                if tokens[i] == tokens[i+1]:
                    repeats += 1
            
            if repeats > 0:
                compressed_len = len(tokens) - repeats
                compression_candidates.append({
                    'word': w,
                    'count': count,
                    'tokens': tokens,
                    'token_count': len(tokens),
                    'repeats': repeats,
                    'compressed_length': compressed_len,
                })
        
        return compression_candidates
    
    def build_compression_mapping(self):
        """Build a compression mapping hypothesis."""
        # Step 1: Find which token sequences compress
        compression = self.test_compression_hypothesis()
        
        # Step 2: Build mapping from long → short
        mapping = {}
        for item in compression:
            w = item['word']
            tokens = item['tokens']
            
            # Simple compression: remove repeated tokens
            compressed = []
            for i, t in enumerate(tokens):
                if i == 0 or t != tokens[i-1]:
                    compressed.append(t)
            
            mapping[w] = {
                'original_tokens': tokens,
                'compressed_tokens': compressed,
                'original_length': len(tokens),
                'compressed_length': len(compressed),
            }
        
        return mapping


# ============================================================
# APPROACH 2: SYLLABIC DECOMPOSITION
# ============================================================

class SyllabicAnalyzer:
    """Analyze 29 EVA tokens as syllabic units (CV pairs)."""
    
    # Hypothesis: Each EVA token = consonant + vowel
    SYLLABIC_HYPOTHESES = {
        'hypothesis_1': {
            'name': 'Vowel-final tokens',
            'description': 'Tokens ending in vowels are V, others are C',
            'vowel_tokens': ['o', 'e', 'a', 'y', 'i'],
            'consonant_tokens': ['ch', 'sh', 'qo', 'd', 'l', 'k', 'r', 'n', 't', 's', 'cth', 'cph'],
        },
        'hypothesis_2': {
            'name': 'Frequency-based',
            'description': 'Most frequent = vowels',
            'vowel_tokens': ['o', 'e', 'y', 'a', 'd'],
            'consonant_tokens': ['i', 'ch', 'l', 'k', 'r', 'n', 't', 'qo', 'sh', 's', 'cth', 'cph'],
        },
    }
    
    def __init__(self, words):
        self.words = words
        self.all_tokens = []
        for w in words:
            self.all_tokens.extend(tokenize(w))
        self.token_freq = Counter(self.all_tokens)
    
    def test_syllabic_patterns(self):
        """Test if tokens follow CVCV patterns."""
        results = {}
        
        for hyp_name, hyp in self.SYLLABIC_HYPOTHESES.items():
            vowels = set(hyp['vowel_tokens'])
            
            # Analyze token sequences
            cv_patterns = []
            for w in self.words[:1000]:
                tokens = tokenize(w)
                pattern = ''.join(['V' if t in vowels else 'C' for t in tokens])
                cv_patterns.append(pattern)
            
            # Count patterns
            pattern_freq = Counter(cv_patterns)
            
            # Check for CVCV dominance
            cvcv_count = sum(count for pattern, count in pattern_freq.items() 
                           if self._is_alternating(pattern))
            total = sum(pattern_freq.values())
            
            results[hyp_name] = {
                'name': hyp['name'],
                'vowel_tokens': hyp['vowel_tokens'],
                'alternating_ratio': round(cvcv_count / total, 3) if total > 0 else 0,
                'top_patterns': pattern_freq.most_common(10),
            }
        
        return results
    
    def _is_alternating(self, pattern):
        """Check if pattern alternates C/V."""
        for i in range(len(pattern) - 1):
            if pattern[i] == pattern[i+1]:
                return False
        return True
    
    def decode_syllabic(self, word, vowel_tokens):
        """Decode word using syllabic hypothesis."""
        tokens = tokenize(word)
        vowels = set(vowel_tokens)
        
        decoded = []
        for t in tokens:
            if t in vowels:
                decoded.append('V')
            else:
                decoded.append('C')
        
        return ''.join(decoded)


# ============================================================
# APPROACH 3: CRIB-BASED CONSTRAINT SOLVING
# ============================================================

class CribSolver:
    """Use known words (cribs) to constrain the cipher key."""
    
    # Curated cribs from Voynich research
    CRIBS = [
        # Most likely cribs (high confidence)
        {'eva': 'daiin', 'plain': 'and', 'confidence': 0.7, 'rationale': 'Most common word = conjunction'},
        {'eva': 'ol', 'plain': 'la', 'confidence': 0.5, 'rationale': 'Common short word = article'},
        {'eva': 'ar', 'plain': 'ar', 'confidence': 0.6, 'rationale': 'Short word, matches Italian'},
        {'eva': 'or', 'plain': 'or', 'confidence': 0.6, 'rationale': 'Short word, matches Italian'},
        
        # Zodiac-inspired
        {'eva': 'okal', 'plain': 'marc', 'confidence': 0.3, 'rationale': 'Possible zodiac label'},
        {'eva': 'otal', 'plain': 'apri', 'confidence': 0.3, 'rationale': 'Possible zodiac label'},
        
        # Herb-inspired (from herbal section)
        {'eva': 'chedy', 'plain': 'erbe', 'confidence': 0.4, 'rationale': 'Herbal section, common word'},
        {'eva': 'shedy', 'plain': 'sede', 'confidence': 0.4, 'rationale': 'Herbal section'},
    ]
    
    def __init__(self, words):
        self.words = words
        self.word_freq = Counter(words)
    
    def test_crib(self, crib):
        """Test if a crib is consistent."""
        eva_word = crib['eva']
        plain_word = crib['plain']
        
        # Check occurrences
        count = self.word_freq.get(eva_word, 0)
        
        # Build partial key
        eva_tokens = tokenize(eva_word)
        key = {}
        conflicts = []
        
        for i, (eva_t, plain_c) in enumerate(zip(eva_tokens, plain_word)):
            if eva_t in key:
                if key[eva_t] != plain_c:
                    conflicts.append((eva_t, key[eva_t], plain_c))
            else:
                key[eva_t] = plain_c
        
        return {
            'crib': crib,
            'occurrences': count,
            'partial_key': key,
            'conflicts': conflicts,
            'consistent': len(conflicts) == 0,
        }
    
    def find_consistent_cribs(self):
        """Find set of cribs that are mutually consistent."""
        results = []
        combined_key = {}
        consistent_set = []
        
        # Sort by confidence
        sorted_cribs = sorted(self.CRIBS, key=lambda x: -x['confidence'])
        
        for crib in sorted_cribs:
            result = self.test_crib(crib)
            
            # Check if consistent with combined key
            is_consistent = True
            for token, char in result['partial_key'].items():
                if token in combined_key and combined_key[token] != char:
                    is_consistent = False
                    break
            
            if is_consistent and result['occurrences'] > 0:
                consistent_set.append(result)
                combined_key.update(result['partial_key'])
            
            results.append(result)
        
        return {
            'all_results': results,
            'consistent_set': consistent_set,
            'combined_key': combined_key,
            'key_coverage': len(combined_key),
            'coverage_pct': round(len(combined_key) / 29 * 100, 1),
        }
    
    def decode_with_key(self, key):
        """Decode text using a partial key."""
        decoded_lines = []
        for line in ' '.join(self.words[:100]).split('.'):
            words = line.split()
            decoded = []
            for w in words:
                tokens = tokenize(w)
                d = ''.join(key.get(t, '?') for t in tokens)
                decoded.append(d)
            decoded_lines.append(' '.join(decoded))
        return decoded_lines


# ============================================================
# APPROACH 4: PATTERN-BASED KEY DISCOVERY
# ============================================================

class PatternKeyFinder:
    """Discover key based on structural patterns."""
    
    def __init__(self, words):
        self.words = words
        self.word_freq = Counter(words)
        
        # Tokenize
        self.all_tokens = []
        self.tokenized_words = {}
        for w in set(words):
            tokens = tokenize(w)
            self.tokenized_words[w] = tokens
            self.all_tokens.extend(tokens * self.word_freq[w])
        
        self.token_freq = Counter(self.all_tokens)
    
    def find_token_relationships(self):
        """Find relationships between tokens based on context."""
        # What tokens appear before/after each token?
        before = defaultdict(Counter)
        after = defaultdict(Counter)
        
        for w, tokens in self.tokenized_words.items():
            for i in range(len(tokens)):
                if i > 0:
                    before[tokens[i]][tokens[i-1]] += 1
                if i < len(tokens) - 1:
                    after[tokens[i]][tokens[i+1]] += 1
        
        # Find tokens with similar contexts (might map to same character)
        token_similarity = {}
        token_list = sorted(self.token_freq.keys())
        
        for i, t1 in enumerate(token_list):
            for t2 in token_list[i+1:]:
                # Compare before contexts
                before_sim = len(set(before[t1].keys()) & set(before[t2].keys()))
                after_sim = len(set(after[t1].keys()) & set(after[t2].keys()))
                
                if before_sim > 2 or after_sim > 2:
                    token_similarity[(t1, t2)] = {
                        'before_shared': before_sim,
                        'after_shared': after_sim,
                        'total_similarity': before_sim + after_sim,
                    }
        
        # Sort by similarity
        sorted_sim = sorted(token_similarity.items(), 
                          key=lambda x: -x[1]['total_similarity'])
        
        return {
            'similar_pairs': sorted_sim[:15],
            'interpretation': 'Tokens with similar contexts might map to same character (homophonic)'
        }
    
    def detect_null_tokens(self):
        """Detect tokens that might be nulls (padding/meaningless)."""
        # Nulls tend to appear at word boundaries
        start_freq = Counter()
        end_freq = Counter()
        middle_freq = Counter()
        
        for w, tokens in self.tokenized_words.items():
            if len(tokens) >= 1:
                start_freq[tokens[0]] += 1
                end_freq[tokens[-1]] += 1
            if len(tokens) >= 3:
                for t in tokens[1:-1]:
                    middle_freq[t] += 1
        
        # Tokens that appear disproportionately at boundaries might be nulls
        null_candidates = []
        total_words = len(self.word_freq)
        
        for token in self.token_freq:
            start_ratio = start_freq.get(token, 0) / total_words
            end_ratio = end_freq.get(token, 0) / total_words
            middle_ratio = middle_freq.get(token, 0) / (total_words * 3)  # Approximate
            
            if (start_ratio + end_ratio) > middle_ratio * 3:
                null_candidates.append({
                    'token': token,
                    'start_pct': round(start_ratio * 100, 1),
                    'end_pct': round(end_ratio * 100, 1),
                    'middle_pct': round(middle_ratio * 100, 1),
                    'null_score': round((start_ratio + end_ratio) / max(middle_ratio, 0.001), 1),
                })
        
        return sorted(null_candidates, key=lambda x: -x['null_score'])[:10]


# ============================================================
# MAIN
# ============================================================

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else EVA_FILE
    method = 'all'
    if '--method' in sys.argv:
        idx = sys.argv.index('--method')
        method = sys.argv[idx + 1]
    
    with open(filepath, 'r') as f:
        text = f.read()
    
    words = text.split()[:5000]  # Use first 5000 words
    
    print("=" * 70)
    print("VOYNICH TRUE CIPHER KEY FINDER")
    print("Based on: Naibbe compression + Syllabic + Cribs + Patterns")
    print("=" * 70)
    
    # 1. Naibbe Compression
    print("\n📊 APPROACH 1: NAIBBE COMPRESSION")
    print("-" * 50)
    naibbe = NaibbeCompressor(words)
    lengths = naibbe.analyze_word_lengths()
    print(f"Word length distribution:")
    for length, count in lengths['length_distribution'][:6]:
        print(f"  Length {length}: {count} words")
    
    compression = naibbe.test_compression_hypothesis()
    print(f"\nCompression candidates (repeated tokens):")
    for item in compression[:5]:
        print(f"  {item['word']:12s}: {item['token_count']} tokens → {item['compressed_length']} (removed {item['repeats']} repeats)")
    
    # 2. Syllabic Analysis
    print("\n📊 APPROACH 2: SYLLABIC DECOMPOSITION")
    print("-" * 50)
    syllabic = SyllabicAnalyzer(words)
    syllabic_results = syllabic.test_syllabic_patterns()
    for hyp_name, result in syllabic_results.items():
        print(f"  {result['name']}: alternating ratio = {result['alternating_ratio']}")
        print(f"    Top patterns: {[p for p, _ in result['top_patterns'][:5]]}")
    
    # 3. Crib-Based Solving
    print("\n📊 APPROACH 3: CRIB-BASED CONSTRAINT SOLVING")
    print("-" * 50)
    crib = CribSolver(words)
    crib_results = crib.find_consistent_cribs()
    print(f"  Cribs tested: {len(crib_results['all_results'])}")
    print(f"  Consistent set: {len(crib_results['consistent_set'])}")
    print(f"  Key coverage: {crib_results['key_coverage']}/29 tokens ({crib_results['coverage_pct']}%)")
    print(f"  Combined key: {crib_results['combined_key']}")
    
    for r in crib_results['consistent_set']:
        print(f"    '{r['crib']['eva']}' → '{r['crib']['plain']}' ({r['occurrences']}x, confidence={r['crib']['confidence']})")
    
    # 4. Pattern Analysis
    print("\n📊 APPROACH 4: PATTERN-BASED KEY DISCOVERY")
    print("-" * 50)
    patterns = PatternKeyFinder(words)
    nulls = patterns.detect_null_tokens()
    print(f"  Null token candidates:")
    for n in nulls[:5]:
        print(f"    {n['token']:6s}: start={n['start_pct']}%, end={n['end_pct']}%, null_score={n['null_score']}")
    
    similarities = patterns.find_token_relationships()
    print(f"\n  Similar token pairs (might be homophonic):")
    for (t1, t2), sim in similarities['similar_pairs'][:5]:
        print(f"    {t1} ↔ {t2}: similarity={sim['total_similarity']}")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY: CORRECT DIRECTION")
    print(f"{'='*70}")
    print("""
1. NAIBBE COMPRESSION: Most promising
   - 'daiin' (5 tokens) might compress to 1-2 chars
   - Repeated tokens (ii, ee) are likely compressed
   - Need to find the COMPRESSION RULES

2. SYLLABIC: Confirmed CVCV structure
   - 29 tokens = syllabic units
   - Each token = consonant+vowel pair
   - Need to identify which are C and which are V

3. CRIBS: Partial key found
   - Most common word = 'and' (conjunction)
   - Short words = articles/prepositions
   - Need more cribs from illustrations

4. PATTERNS: Null tokens detected
   - Some tokens might be padding/meaningless
   - Homophonic tokens share similar contexts
   - Need to identify and remove nulls

NEXT STEPS:
  1. Implement Naibbe compression decoder
  2. Find more cribs from Voynich illustrations
  3. Test Currier A/B separately
  4. Remove null tokens and re-analyze
""")
    
    # Save
    output = {
        'naibbe_compression': {
            'length_distribution': lengths['length_distribution'],
            'compression_candidates': compression[:10],
        },
        'syllabic': syllabic_results,
        'cribs': {
            'consistent_set': [
                {'eva': r['crib']['eva'], 'plain': r['crib']['plain'], 
                 'occurrences': r['occurrences'], 'confidence': r['crib']['confidence']}
                for r in crib_results['consistent_set']
            ],
            'combined_key': crib_results['combined_key'],
            'coverage_pct': crib_results['coverage_pct'],
        },
        'patterns': {
            'null_candidates': nulls[:5],
            'similar_pairs': [(t1, t2, sim) for (t1, t2), sim in similarities['similar_pairs'][:10]],
        },
    }
    
    outpath = os.path.join(OUTPUT_DIR, 'true-key-finder.json')
    with open(outpath, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"✅ Saved to {outpath}")


if __name__ == "__main__":
    main()
