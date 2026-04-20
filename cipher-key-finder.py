#!/usr/bin/env python3
"""
Voynich Cipher Key Finder
===========================
Focus on FINDING THE REAL CIPHER KEY using proven techniques:

1. Frequency Analysis Matching - Match Voynich frequencies to known languages
2. Kasiski Examination - Find repeated sequences for key length
3. Index of Coincidence - Determine cipher type
4. Evolutionary Search - Genetic algorithm for key discovery
5. Crib-based Attack - Use illustration-derived cribs
6. Bigram/Trigram Matching - Match patterns to known languages
7. Friedman Test - Determine if monoalphabetic or polyalphabetic

Based on historical breakthroughs:
- Zodiac Cipher (2020): AI-assisted frequency analysis + constraint solving
- Linear B (1952): Pattern recognition + hypothesis testing
- Enigma: Crib-based attacks

Usage:
    python3 cipher-key-finder.py --eva eva-takahashi.txt --method frequency
    python3 cipher-key-finder.py --eva eva-takahashi.txt --method evolutionary
    python3 cipher-key-finder.py --eva eva-takahashi.txt --method crib
    python3 cipher-key-finder.py --eva eva-takahashi.txt --method all
"""

import json
import math
import os
import sys
import random
from collections import Counter, defaultdict
from datetime import datetime


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "research-output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# EVA TOKENIZER (29 tokens)
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
        if not matched:
            if i < len(clean) and clean[i].isalpha():
                tokens.append(clean[i])
            i += 1
    return tokens


# ============================================================
# KNOWN LANGUAGE FREQUENCIES
# ============================================================

# Italian character frequencies (%)
ITALIAN_FREQ = {
    'a': 11.74, 'b': 0.92, 'c': 4.50, 'd': 3.73, 'e': 11.79,
    'f': 0.95, 'g': 1.64, 'h': 1.54, 'i': 10.14, 'l': 6.51,
    'm': 2.51, 'n': 6.88, 'o': 9.83, 'p': 3.05, 'q': 0.51,
    'r': 6.37, 's': 4.98, 't': 5.62, 'u': 3.01, 'v': 2.10,
    'z': 0.49,
}

# Latin character frequencies (%)
LATIN_FREQ = {
    'a': 8.12, 'b': 1.49, 'c': 2.71, 'd': 4.32, 'e': 12.02,
    'f': 2.30, 'g': 2.03, 'h': 5.92, 'i': 7.31, 'l': 3.97,
    'm': 2.61, 'n': 6.95, 'o': 7.68, 'p': 1.82, 'q': 0.10,
    'r': 5.97, 's': 6.35, 't': 9.05, 'u': 2.80, 'v': 1.06,
}

# Hebrew character frequencies (%)
HEBREW_FREQ = {
    'a': 8.0, 'b': 3.0, 'g': 2.5, 'd': 2.0, 'h': 8.5,
    'v': 3.5, 'z': 0.5, 'ch': 3.0, 't': 2.5, 'y': 10.0,
    'k': 2.5, 'l': 5.0, 'm': 5.5, 'n': 7.0, 's': 3.0,
    'p': 2.0, 'ts': 1.5, 'q': 1.0, 'r': 6.0, 'sh': 3.5,
}

# Occitan character frequencies (%)
OCCITAN_FREQ = {
    'a': 12.0, 'b': 1.0, 'c': 4.0, 'd': 4.0, 'e': 13.0,
    'f': 1.0, 'g': 1.5, 'h': 1.0, 'i': 8.0, 'l': 6.0,
    'm': 2.5, 'n': 7.0, 'o': 8.5, 'p': 3.0, 'q': 0.5,
    'r': 6.5, 's': 6.0, 't': 6.0, 'u': 4.0, 'v': 1.5,
}

LANGUAGE_FREQS = {
    'italian': ITALIAN_FREQ,
    'latin': LATIN_FREQ,
    'hebrew': HEBREW_FREQ,
    'occitan': OCCITAN_FREQ,
}


# ============================================================
# CIPHER ANALYSIS
# ============================================================

class CipherAnalyzer:
    """Analyze the Voynich cipher to determine its type."""
    
    def __init__(self, text):
        self.text = text
        self.words = text.split()
        self.all_tokens = []
        for w in self.words:
            self.all_tokens.extend(tokenize(w))
        self.token_freq = Counter(self.all_tokens)
        self.total_tokens = sum(self.token_freq.values())
    
    def index_of_coincidence(self):
        """Calculate IC to determine cipher type.
        IC ≈ 0.065 for natural language (monoalphabetic)
        IC ≈ 0.038 for random text (polyalphabetic)"""
        n = self.total_tokens
        if n < 2:
            return 0
        ic = sum(f * (f - 1) for f in self.token_freq.values()) / (n * (n - 1))
        return round(ic, 4)
    
    def friedman_test(self):
        """Friedman test for key length estimation."""
        ic = self.index_of_coincidence()
        n = self.total_tokens
        
        # Expected IC for different languages
        lang_ic = {
            'italian': 0.0738,
            'latin': 0.0725,
            'english': 0.0667,
            'german': 0.0762,
            'french': 0.0746,
        }
        
        # Estimate key length
        kappa_p = 0.065  # Expected IC for plaintext
        kappa_r = 1.0 / len(self.token_freq)  # IC for random
        
        if ic > kappa_r:
            key_length = (kappa_p - kappa_r) / (ic - kappa_r)
        else:
            key_length = float('inf')
        
        return {
            'index_of_coincidence': ic,
            'estimated_key_length': round(key_length, 2),
            'cipher_type': (
                'MONOALPHABETIC' if ic > 0.060 else
                'POLYALPHABETIC' if ic > 0.045 else
                'RANDOM/UNKNOWN'
            ),
            'interpretation': (
                'Simple substitution cipher likely' if ic > 0.060 else
                'Polyalphabetic or complex cipher' if ic > 0.045 else
                'Very complex or random encoding'
            )
        }
    
    def kasiski_examination(self, min_len=3, max_len=5):
        """Find repeated sequences to estimate key length."""
        clean = ''.join(self.all_tokens)
        repeats = {}
        
        for length in range(min_len, max_len + 1):
            for i in range(len(clean) - length):
                seq = clean[i:i+length]
                for j in range(i + 1, len(clean) - length):
                    if clean[j:j+length] == seq:
                        if seq not in repeats:
                            repeats[seq] = []
                        repeats[seq].append(j - i)
        
        # Calculate GCD of distances
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        
        key_lengths = Counter()
        for seq, distances in repeats.items():
            if len(distances) >= 2:
                g = distances[0]
                for d in distances[1:]:
                    g = gcd(g, d)
                if g > 1:
                    key_lengths[g] += 1
        
        return {
            'repeated_sequences': len(repeats),
            'likely_key_lengths': dict(key_lengths.most_common(5)),
        }
    
    def frequency_analysis(self):
        """Get Voynich token frequencies."""
        return {
            token: {
                'count': count,
                'frequency': round(count / self.total_tokens * 100, 2)
            }
            for token, count in self.token_freq.most_common()
        }


# ============================================================
# FREQUENCY MATCHING
# ============================================================

class FrequencyMatcher:
    """Match Voynich frequencies to known languages."""
    
    def __init__(self, voynich_freq):
        self.voynich = voynich_freq
    
    def match_language(self, lang_freq, lang_name):
        """Match Voynich frequencies to a language."""
        # Get top N Voynich tokens
        voynich_top = sorted(self.voynich.items(), key=lambda x: -x[1]['count'])[:15]
        voynich_tokens = [t for t, _ in voynich_top]
        voynich_pcts = [d['frequency'] for _, d in voynich_top]
        
        # Get top N language characters
        lang_top = sorted(lang_freq.items(), key=lambda x: -x[1])[:15]
        lang_chars = [c for c, _ in lang_top]
        lang_pcts = [f for _, f in lang_top]
        
        # Calculate correlation
        n = min(len(voynich_pcts), len(lang_pcts))
        if n < 3:
            return {'correlation': 0, 'mapping': {}}
        
        # Spearman-like rank correlation
        voynich_ranks = list(range(1, n + 1))
        lang_ranks = list(range(1, n + 1))
        
        # Simple mapping: map highest freq Voynich token to highest freq lang char
        mapping = {}
        for i in range(n):
            if i < len(voynich_tokens) and i < len(lang_chars):
                mapping[voynich_tokens[i]] = lang_chars[i]
        
        # Calculate score based on frequency distribution similarity
        diff_sum = sum(abs(voynich_pcts[i] - lang_pcts[i]) for i in range(n))
        max_diff = sum(max(voynich_pcts[i], lang_pcts[i]) for i in range(n))
        similarity = 1 - (diff_sum / max_diff) if max_diff > 0 else 0
        
        return {
            'language': lang_name,
            'similarity': round(similarity, 4),
            'mapping': mapping,
            'voynich_top': voynich_top[:10],
            'lang_top': lang_top[:10],
        }
    
    def find_best_match(self):
        """Find the best matching language."""
        results = []
        for lang_name, lang_freq in LANGUAGE_FREQS.items():
            result = self.match_language(lang_freq, lang_name)
            results.append(result)
        
        results.sort(key=lambda x: -x['similarity'])
        return results


# ============================================================
# EVOLUTIONARY KEY SEARCH
# ============================================================

class EvolutionaryKeySearch:
    """Use genetic algorithm to find the cipher key."""
    
    def __init__(self, text, target_language='italian'):
        self.text = text
        self.words = text.split()
        self.target_lang = target_language
        
        # Get all unique tokens
        all_tokens = set()
        for w in self.words:
            all_tokens.update(tokenize(w))
        self.tokens = sorted(all_tokens)
        
        # Target alphabet
        if target_language == 'italian':
            self.target_chars = list('abcdefghilmnopqrstuvz')
        elif target_language == 'hebrew':
            self.target_chars = list('abgdhwzchtyklmnsxfqrs')  # Hebrew transliteration
        else:
            self.target_chars = list('abcdefghilmnopqrstuvz')
    
    def random_key(self):
        """Generate random key mapping."""
        available = self.target_chars.copy()
        random.shuffle(available)
        key = {}
        for i, token in enumerate(self.tokens):
            if i < len(available):
                key[token] = available[i]
            else:
                key[token] = random.choice(self.target_chars)
        return key
    
    def decode_with_key(self, key):
        """Decode text using a key."""
        decoded_words = []
        for w in self.words[:500]:
            tokens = tokenize(w)
            decoded = ''.join(key.get(t, '?') for t in tokens)
            decoded_words.append(decoded)
        return ' '.join(decoded_words)
    
    def fitness(self, key):
        """Evaluate fitness of a key."""
        decoded = self.decode_with_key(key)
        words = decoded.split()
        if not words:
            return 0
        
        score = 0
        all_text = ''.join(words)
        
        # Vowel ratio (target 35-45%)
        vowels = set('aeiou')
        v = sum(1 for c in all_text if c in vowels)
        t = len(all_text)
        if t > 0:
            vr = v / t
            score += max(0, 20 - abs(vr - 0.4) * 100)
        
        # No triple repeats
        triples = sum(1 for i in range(len(all_text)-2)
                     if all_text[i] == all_text[i+1] == all_text[i+2])
        score -= triples * 5
        
        # Bigram plausibility
        valid = 0
        total = 0
        for w in words:
            for i in range(len(w)-1):
                total += 1
                if (w[i] in vowels) != (w[i+1] in vowels):
                    valid += 1
        if total > 0:
            score += (valid / total) * 20
        
        # Word length (target 4-6)
        avg_len = sum(len(w) for w in words) / len(words)
        score += max(0, 10 - abs(avg_len - 5) * 3)
        
        # Dictionary matching
        if self.target_lang == 'italian':
            italian = set(['il','lo','la','le','di','del','al','da','che','per','con','in','non','e','o','a','ma','se','si','ar','or','ol','et','el','cor','dare','fare','erba','fiore','sole','luna','terra','acqua'])
            matches = sum(1 for w in words if w in italian)
            score += matches * 5
        
        return score
    
    def evolve(self, population_size=30, generations=100):
        """Evolve key using genetic algorithm."""
        print(f"Evolving key for {self.target_lang} ({len(self.tokens)} tokens, {generations} generations)")
        
        # Initialize population
        population = [self.random_key() for _ in range(population_size)]
        
        best_key = None
        best_fitness = float('-inf')
        
        for gen in range(generations):
            # Evaluate
            scored = [(k, self.fitness(k)) for k in population]
            scored.sort(key=lambda x: -x[1])
            
            if scored[0][1] > best_fitness:
                best_fitness = scored[0][1]
                best_key = scored[0][0].copy()
            
            if gen % 20 == 0:
                decoded = self.decode_with_key(scored[0][0])[:60]
                print(f"  Gen {gen}: fitness={scored[0][1]:.1f} → {decoded}")
            
            # Selection (top 30%)
            survivors = [k for k, s in scored[:max(2, population_size // 3)]]
            
            # Crossover & Mutation
            new_pop = survivors.copy()
            while len(new_pop) < population_size:
                p1 = random.choice(survivors)
                p2 = random.choice(survivors)
                child = {}
                for token in self.tokens:
                    if random.random() < 0.5:
                        child[token] = p1.get(token, '?')
                    else:
                        child[token] = p2.get(token, '?')
                # Mutation
                if random.random() < 0.3:
                    t = random.choice(self.tokens)
                    child[t] = random.choice(self.target_chars)
                new_pop.append(child)
            
            population = new_pop
        
        return best_key, best_fitness


# ============================================================
# CRIB-BASED ATTACK
# ============================================================

class CribAttack:
    """Use known plaintext (cribs) to find the cipher key."""
    
    # Likely cribs from Voynich illustrations
    CRIBS = [
        # Zodiac labels (month names)
        {'name': 'zodiac_aries', 'eva': 'okal', 'plain': 'marc'},  # March
        {'name': 'zodiac_taurus', 'eva': 'otal', 'plain': 'apri'},  # April
        
        # Herb names (from herbal illustrations)
        {'name': 'herb_1', 'eva': 'daiin', 'plain': 'erba'},  # herb
        {'name': 'herb_2', 'eva': 'ol', 'plain': 'la'},      # the
        
        # Common words
        {'name': 'common_1', 'eva': 'ar', 'plain': 'ar'},     # to the
        {'name': 'common_2', 'eva': 'or', 'plain': 'or'},     # or
    ]
    
    def __init__(self, text):
        self.text = text
        self.words = text.split()
    
    def test_crib(self, crib):
        """Test if a crib is consistent with the text."""
        eva = crib['eva']
        plain = crib['plain']
        
        # Check if EVA word appears in text
        count = self.words.count(eva)
        
        # Build partial key from crib
        key = {}
        eva_tokens = tokenize(eva)
        for i, (eva_t, plain_c) in enumerate(zip(eva_tokens, plain)):
            if eva_t in key and key[eva_t] != plain_c:
                return None  # Inconsistent
            key[eva_t] = plain_c
        
        return {
            'crib': crib['name'],
            'eva_word': eva,
            'plaintext': plain,
            'occurrences': count,
            'partial_key': key,
            'confidence': min(1.0, count / 10),
        }
    
    def test_all_cribs(self):
        """Test all cribs and find consistent set."""
        results = []
        combined_key = {}
        
        for crib in self.CRIBS:
            result = self.test_crib(crib)
            if result:
                results.append(result)
                # Merge key
                for k, v in result['partial_key'].items():
                    if k in combined_key and combined_key[k] != v:
                        result['consistent'] = False
                    else:
                        combined_key[k] = v
        
        return {
            'cribs_tested': len(self.CRIBS),
            'cribs_matched': len(results),
            'results': results,
            'combined_key': combined_key,
            'key_coverage': len(combined_key),
        }


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cipher-key-finder.py <eva_file> [--method all|frequency|evolutionary|crib]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    method = 'all'
    if '--method' in sys.argv:
        idx = sys.argv.index('--method')
        method = sys.argv[idx + 1]
    
    with open(filepath, 'r') as f:
        text = f.read()
    
    print("=" * 70)
    print("VOYNICH CIPHER KEY FINDER")
    print("Focus: Finding the REAL cipher key")
    print("=" * 70)
    
    # 1. Cipher Analysis
    print("\n📊 STEP 1: CIPHER TYPE ANALYSIS")
    print("-" * 50)
    analyzer = CipherAnalyzer(text)
    friedman = analyzer.friedman_test()
    print(f"  Index of Coincidence: {friedman['index_of_coincidence']}")
    print(f"  Cipher Type: {friedman['cipher_type']}")
    print(f"  Estimated Key Length: {friedman['estimated_key_length']}")
    print(f"  Interpretation: {friedman['interpretation']}")
    
    kasiski = analyzer.kasiski_examination()
    print(f"  Kasiski Repeated Sequences: {kasiski['repeated_sequences']}")
    print(f"  Likely Key Lengths: {kasiski['likely_key_lengths']}")
    
    # 2. Frequency Matching
    print("\n📊 STEP 2: FREQUENCY MATCHING")
    print("-" * 50)
    voynich_freq = analyzer.frequency_analysis()
    matcher = FrequencyMatcher(voynich_freq)
    lang_matches = matcher.find_best_match()
    
    for m in lang_matches[:4]:
        print(f"  {m['language']:10s}: similarity={m['similarity']:.4f}")
        mapping_sample = dict(list(m['mapping'].items())[:5])
        print(f"    Sample mapping: {mapping_sample}")
    
    # 3. Crib Attack
    print("\n📊 STEP 3: CRIB-BASED ATTACK")
    print("-" * 50)
    crib = CribAttack(text)
    crib_results = crib.test_all_cribs()
    print(f"  Cribs tested: {crib_results['cribs_tested']}")
    print(f"  Cribs matched: {crib_results['cribs_matched']}")
    print(f"  Combined key tokens: {crib_results['key_coverage']}")
    for r in crib_results['results']:
        print(f"    {r['crib']}: '{r['eva_word']}' → '{r['plaintext']}' ({r['occurrences']}x)")
    
    # 4. Evolutionary Search (if requested)
    if method in ['all', 'evolutionary']:
        print("\n📊 STEP 4: EVOLUTIONARY KEY SEARCH")
        print("-" * 50)
        best_lang = lang_matches[0]['language'] if lang_matches else 'italian'
        evo = EvolutionaryKeySearch(text, best_lang)
        best_key, best_fitness = evo.evolve(population_size=20, generations=50)
        decoded_sample = evo.decode_with_key(best_key)[:100]
        print(f"  Best fitness: {best_fitness:.1f}")
        print(f"  Best key (top 10): {dict(list(best_key.items())[:10])}")
        print(f"  Decoded sample: {decoded_sample}")
    
    # Save results
    output = {
        'cipher_analysis': friedman,
        'kasiski': kasiski,
        'language_matches': lang_matches[:4],
        'crib_attack': crib_results,
    }
    
    outpath = os.path.join(OUTPUT_DIR, 'cipher-key-finder.json')
    with open(outpath, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n✅ Saved to {outpath}")


if __name__ == "__main__":
    main()
