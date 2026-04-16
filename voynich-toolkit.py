#!/usr/bin/env python3
"""
Voynich Manuscript - Comprehensive Cryptanalysis Toolkit
=========================================================
Combines ALL learned skills from Gemini's recommendations:

Week 1-2: Classical cipher tools, writing system classification
Week 3-4: Voynich-specific analysis (Zipf, entropy, patterns)
Week 5-6: Python text analysis, frequency, Markov chains
Week 7-8: Advanced metrics from GitHub repos analysis
Week 9-10: Integration of all approaches

Based on analysis of:
- sravanareddy/deciphervoynich (CorpusStats class)
- viking-sudo-rm/voynich2vec (word embeddings)
- alexanderboxer/voynich-attack (RefText class, comparative corpora)
- danielgaskell/voynich (comprehensive metrics)
- YaleDHLab/voynich (spatial analysis)

Usage:
    python3 voynich-toolkit.py --full eva-takahashi.txt
    python3 voynich-toolkit.py --compare eva-takahashi.txt --corpus latin.txt
    python3 voynich-toolkit.py --classify eva-takahashi.txt
    python3 voynich-toolkit.py --csv eva-takahashi.txt -o eva-structured.csv
"""

import argparse
import json
import math
import os
import sys
import zlib
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# ============================================================
# CORE TEXT LOADER & PARSER
# ============================================================

class TextCorpus:
    """Unified text corpus class (inspired by voynich-attack's RefText)."""
    
    def __init__(self, filepath=None, text=None, name="Unknown"):
        self.name = name
        self.filepath = filepath
        if filepath and os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                self.raw_text = f.read()
        elif text:
            self.raw_text = text
        else:
            self.raw_text = ""
        
        self.lines = self.raw_text.split('\n')
        self.words = self.raw_text.split()
        self.chars = list(self.raw_text.replace('\n', ' '))
        self.clean_chars = [c for c in self.chars if c.strip()]
    
    def __len__(self):
        return len(self.raw_text)


# ============================================================
# SECTION 1: CLASSICAL CRYPTANALYSIS (Week 1-2)
# ============================================================

class ClassicalCipherAnalyzer:
    """Classical cipher analysis tools from The Code Book & ACA techniques."""
    
    @staticmethod
    def frequency_analysis(text):
        """Character frequency analysis."""
        chars = [c for c in text.lower() if c.strip()]
        total = len(chars)
        freq = Counter(chars)
        return {char: {'count': count, 'frequency': count/total*100} 
                for char, count in freq.most_common()}
    
    @staticmethod
    def bigram_analysis(text):
        """Bigram (character pair) frequency analysis."""
        clean = text.lower().replace('\n', ' ')
        bigrams = [clean[i:i+2] for i in range(len(clean)-1)]
        return Counter(bigrams)
    
    @staticmethod
    def trigram_analysis(text):
        """Trigram (character triple) frequency analysis."""
        clean = text.lower().replace('\n', ' ')
        trigrams = [clean[i:i+3] for i in range(len(clean)-2)]
        return Counter(trigrams)
    
    @staticmethod
    def index_of_coincidence(text):
        """Calculate Index of Coincidence (IC).
        IC ~ 0.065 for natural language, ~0.038 for random."""
        chars = [c for c in text.lower() if c.strip()]
        n = len(chars)
        if n < 2:
            return 0
        freq = Counter(chars)
        ic = sum(f * (f-1) for f in freq.values()) / (n * (n-1))
        return ic
    
    @staticmethod
    def kasiski_examination(text, min_len=3, max_len=5):
        """Kasiski examination - find repeated sequences."""
        clean = text.lower().replace('\n', ' ').replace(' ', '')
        repeats = {}
        for length in range(min_len, max_len + 1):
            for i in range(len(clean) - length):
                seq = clean[i:i+length]
                for j in range(i + length, len(clean) - length):
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
        
        return {'repeats': repeats, 'likely_key_lengths': dict(key_lengths.most_common(5))}
    
    @staticmethod
    def detect_substitution_pattern(text):
        """Detect if text likely uses substitution cipher."""
        chars = [c for c in text.lower() if c.strip()]
        unique = len(set(chars))
        total = len(chars)
        
        ic = ClassicalCipherAnalyzer.index_of_coincidence(text)
        
        return {
            'unique_characters': unique,
            'index_of_coincidence': round(ic, 4),
            'likely_cipher_type': (
                'Monoalphabetic Substitution' if ic > 0.06 else
                'Polyalphabetic/Transposition' if ic > 0.04 else
                'Random/Unknown'
            )
        }


# ============================================================
# SECTION 2: ENTROPY & ZIPF'S LAW (Week 3-4)
# ============================================================

class EntropyAnalyzer:
    """Entropy analysis tools (Shannon entropy, conditional entropy, etc.)."""
    
    @staticmethod
    def shannon_entropy(items):
        """Calculate Shannon entropy in bits."""
        freq = Counter(items)
        total = len(items)
        if total == 0:
            return 0
        entropy = 0
        for count in freq.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    @staticmethod
    def conditional_entropy(text):
        """Calculate H2 (conditional entropy) - bigram model.
        H2 < 3.5 suggests natural language, > 3.5 suggests cipher."""
        clean = text.lower().replace('\n', ' ')
        bigram_cond = defaultdict(Counter)
        for i in range(len(clean) - 1):
            c1, c2 = clean[i], clean[i+1]
            bigram_cond[c1][c2] += 1
        
        total_bigrams = sum(sum(v.values()) for v in bigram_cond.values())
        h2 = 0
        for c1, followers in bigram_cond.items():
            c1_count = sum(followers.values())
            p_c1 = c1_count / total_bigrams
            h_c1 = 0
            for c2, count in followers.items():
                p_c2_given_c1 = count / c1_count
                if p_c2_given_c1 > 0:
                    h_c1 -= p_c2_given_c1 * math.log2(p_c2_given_c1)
            h2 += p_c1 * h_c1
        return h2
    
    @staticmethod
    def bigram_entropy(text):
        """Calculate entropy of bigram distribution."""
        clean = text.lower().replace('\n', ' ')
        bigrams = [clean[i:i+2] for i in range(len(clean)-1)]
        return EntropyAnalyzer.shannon_entropy(bigrams)
    
    @staticmethod
    def word_entropy(words):
        """Calculate entropy of word distribution."""
        return EntropyAnalyzer.shannon_entropy(words)


class ZipfAnalyzer:
    """Zipf's Law analysis."""
    
    @staticmethod
    def zipf_analysis(words):
        """Analyze Zipf's Law fit."""
        word_freq = Counter(words)
        sorted_words = word_freq.most_common()
        
        if len(sorted_words) < 3:
            return {'error': 'Too few words'}
        
        # Calculate Zipf coefficient via log-log regression
        ranks = list(range(1, min(101, len(sorted_words) + 1)))
        freqs = [sorted_words[i-1][1] for i in ranks]
        
        log_ranks = [math.log(r) for r in ranks]
        log_freqs = [math.log(f) for f in freqs]
        
        n = len(ranks)
        sum_x = sum(log_ranks)
        sum_y = sum(log_freqs)
        sum_xy = sum(x * y for x, y in zip(log_ranks, log_freqs))
        sum_x2 = sum(x * x for x in log_ranks)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return {'error': 'Cannot compute regression'}
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # R-squared
        ss_res = sum((log_freqs[i] - (slope * log_ranks[i] + intercept))**2 for i in range(n))
        ss_tot = sum((f - sum_y/n)**2 for f in log_freqs)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        
        return {
            'zipf_coefficient': round(slope, 3),
            'ideal_coefficient': -1.0,
            'r_squared': round(r_squared, 3),
            'top_10_words': sorted_words[:10],
            'total_unique_words': len(sorted_words)
        }


# ============================================================
# SECTION 3: ADVANCED METRICS (Week 7-8, from GitHub repos)
# ============================================================

class AdvancedMetrics:
    """Advanced statistical metrics from danielgaskell/voynich and voynich-attack."""
    
    @staticmethod
    def word_length_stats(words):
        """Word length distribution statistics."""
        lengths = [len(w) for w in words]
        if not lengths:
            return {}
        
        mean = sum(lengths) / len(lengths)
        variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
        std = math.sqrt(variance)
        
        # Skewness
        skew = sum((l - mean) ** 3 for l in lengths) / (len(lengths) * std ** 3) if std > 0 else 0
        
        # Autocorrelation (Moran's I)
        n = len(lengths)
        mean_l = mean
        numerator = n * sum(lengths[i] * lengths[i+1] for i in range(n-1)) - sum(lengths[:-1]) * sum(lengths[1:])
        denom = (n - 1) * sum((l - mean_l) ** 2 for l in lengths)
        autocorr = numerator / denom if denom > 0 else 0
        
        return {
            'mean': round(mean, 2),
            'std': round(std, 2),
            'min': min(lengths),
            'max': max(lengths),
            'skewness': round(skew, 3),
            'autocorrelation': round(autocorr, 3),
            'distribution': dict(Counter(lengths).most_common())
        }
    
    @staticmethod
    def levenshtein_distance(s1, s2):
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return AdvancedMetrics.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        
        return prev_row[-1]
    
    @staticmethod
    def adjacent_word_distances(words):
        """Levenshtein distance between adjacent words."""
        distances = []
        for i in range(len(words) - 1):
            d = AdvancedMetrics.levenshtein_distance(words[i], words[i+1])
            distances.append(d)
        
        if not distances:
            return {}
        
        mean_d = sum(distances) / len(distances)
        return {
            'mean_distance': round(mean_d, 2),
            'min_distance': min(distances),
            'max_distance': max(distances),
            'distances': distances[:50]  # First 50 for inspection
        }
    
    @staticmethod
    def word_repetition_analysis(words):
        """Analyze word repetition patterns."""
        # Immediate repeats
        immediate = sum(1 for i in range(len(words)-1) if words[i] == words[i+1])
        
        # Triple repeats
        triples = sum(1 for i in range(len(words)-2) 
                     if words[i] == words[i+1] == words[i+2])
        
        # Overall word frequency
        freq = Counter(words)
        repeated_words = {w: c for w, c in freq.items() if c > 1}
        
        return {
            'immediate_repeats': immediate,
            'triple_repeats': triples,
            'repeated_word_count': len(repeated_words),
            'repetition_ratio': round(len(repeated_words) / len(freq), 3) if freq else 0,
            'most_repeated': freq.most_common(10)
        }
    
    @staticmethod
    def positional_bias(words):
        """Analyze positional bias of characters within words."""
        if not words:
            return {}
        
        max_len = max(len(w) for w in words)
        position_freq = defaultdict(Counter)
        
        for word in words:
            for i, char in enumerate(word):
                position_freq[i][char] += 1
        
        # Calculate entropy at each position
        position_entropy = {}
        for pos in range(min(max_len, 20)):
            total = sum(position_freq[pos].values())
            if total > 0:
                h = 0
                for count in position_freq[pos].values():
                    p = count / total
                    if p > 0:
                        h -= p * math.log2(p)
                position_entropy[pos] = round(h, 3)
        
        return {
            'position_entropy': position_entropy,
            'max_word_length': max_len
        }
    
    @staticmethod
    def compression_ratio(text):
        """Calculate compression ratio (zlib).
        Lower ratio = more repetitive/structured."""
        raw = text.encode('utf-8')
        compressed = zlib.compress(raw, 9)
        ratio = len(compressed) / len(raw)
        return round(ratio, 4)
    
    @staticmethod
    def flipped_word_pairs(words):
        """Find words that are reverse of each other (like 'live'/'evil')."""
        word_set = set(words)
        pairs = []
        seen = set()
        for word in word_set:
            rev = word[::-1]
            if rev in word_set and rev != word and (rev, word) not in seen:
                pairs.append((word, rev))
                seen.add((word, rev))
        return pairs
    
    @staticmethod
    def character_repetition_analysis(text):
        """Analyze character repetition patterns."""
        clean = text.lower().replace('\n', '').replace(' ', '')
        
        # Immediate character repeats
        immediate = sum(1 for i in range(len(clean)-1) if clean[i] == clean[i+1])
        
        # Character pair repeats
        bigrams = [clean[i:i+2] for i in range(len(clean)-1)]
        bigram_freq = Counter(bigrams)
        repeated_bigrams = {b: c for b, c in bigram_freq.items() if c > 5}
        
        return {
            'immediate_char_repeats': immediate,
            'repeated_bigrams_over_5': len(repeated_bigrams),
            'top_repeated_bigrams': bigram_freq.most_common(10)
        }


# ============================================================
# SECTION 4: WRITING SYSTEM CLASSIFIER (Week 1-2, from Omniglot)
# ============================================================

class WritingSystemClassifier:
    """Classify unknown writing systems based on Omniglot taxonomy."""
    
    SCRIPT_TYPES = {
        'abjad': {
            'symbol_range': (20, 35),
            'vowel_freq_range': (0, 0.15),
            'word_length_range': (3, 7),
            'description': 'Consonant alphabet (Arabic, Hebrew)'
        },
        'alphabet': {
            'symbol_range': (20, 50),
            'vowel_freq_range': (0.15, 0.40),
            'word_length_range': (4, 8),
            'description': 'Phonemic alphabet (Latin, Greek)'
        },
        'abugida': {
            'symbol_range': (35, 200),
            'vowel_freq_range': (0.10, 0.30),
            'word_length_range': (3, 10),
            'description': 'Syllabic alphabet (Devanagari, Thai)'
        },
        'syllabary': {
            'symbol_range': (50, 500),
            'vowel_freq_range': (0.20, 0.50),
            'word_length_range': (1, 4),
            'description': 'Syllabary (Cherokee, Hiragana)'
        },
        'logographic': {
            'symbol_range': (500, 50000),
            'vowel_freq_range': (0, 1),
            'word_length_range': (1, 3),
            'description': 'Logographic (Chinese, Egyptian)'
        }
    }
    
    @staticmethod
    def classify(text):
        """Classify writing system type."""
        chars = [c for c in text.lower() if c.strip()]
        words = text.split()
        
        unique_chars = len(set(chars))
        total_chars = len(chars)
        
        # Character frequency
        char_freq = Counter(chars)
        
        # Estimate vowels (high-frequency, evenly distributed characters)
        # This is a heuristic - in many languages vowels are among most frequent
        top_chars = [c for c, _ in char_freq.most_common(10)]
        
        # Word length
        avg_word_len = sum(len(w) for w in words) / len(words) if words else 0
        
        # Score each type
        scores = {}
        for stype, params in WritingSystemClassifier.SCRIPT_TYPES.items():
            score = 0
            sym_min, sym_max = params['symbol_range']
            
            # Symbol count match
            if sym_min <= unique_chars <= sym_max:
                score += 3
            elif abs(unique_chars - sym_min) < 10 or abs(unique_chars - sym_max) < 10:
                score += 1
            
            # Word length match
            wl_min, wl_max = params['word_length_range']
            if wl_min <= avg_word_len <= wl_max:
                score += 2
            
            scores[stype] = score
        
        best_type = max(scores, key=scores.get)
        
        return {
            'unique_characters': unique_chars,
            'avg_word_length': round(avg_word_len, 2),
            'classification': best_type,
            'description': WritingSystemClassifier.SCRIPT_TYPES[best_type]['description'],
            'confidence_scores': scores,
            'comparison': {
                'Latin': 26,
                'Greek': 24,
                'Hebrew': 22,
                'Arabic': 28,
                'Cherokee': 85,
                'Chinese': 50000
            }
        }


# ============================================================
# SECTION 5: MARKOV CHAIN MODEL (Week 5-6)
# ============================================================

class MarkovChainModel:
    """Character-level Markov chain model for text generation and analysis."""
    
    def __init__(self):
        self.transitions = defaultdict(Counter)
        self.order = 1
    
    def train(self, text, order=1):
        """Train Markov model on text."""
        self.order = order
        clean = text.lower().replace('\n', ' ')
        for i in range(len(clean) - order):
            state = clean[i:i+order]
            next_char = clean[i+order]
            self.transitions[state][next_char] += 1
    
    def predict_next(self, state):
        """Predict next character given state."""
        if state not in self.transitions:
            return []
        followers = self.transitions[state]
        total = sum(followers.values())
        return [(char, count/total) for char, count in followers.most_common(5)]
    
    def generate(self, start, length=100):
        """Generate text using Markov chain."""
        import random
        result = start.lower()
        for _ in range(length):
            state = result[-self.order:]
            if state not in self.transitions:
                break
            followers = self.transitions[state]
            total = sum(followers.values())
            r = random.random() * total
            cumul = 0
            for char, count in followers.items():
                cumul += count
                if cumul >= r:
                    result += char
                    break
        return result
    
    def perplexity(self, text):
        """Calculate perplexity of text under this model."""
        clean = text.lower().replace('\n', ' ')
        log_prob = 0
        count = 0
        for i in range(len(clean) - self.order):
            state = clean[i:i+self.order]
            next_char = clean[i+self.order]
            if state in self.transitions:
                followers = self.transitions[state]
                total = sum(followers.values())
                prob = followers.get(next_char, 0) / total
                if prob > 0:
                    log_prob += math.log2(prob)
                    count += 1
        if count == 0:
            return float('inf')
        return 2 ** (-log_prob / count)


# ============================================================
# SECTION 6: COMPARATIVE CORPUS ANALYSIS (from voynich-attack)
# ============================================================

class CorpusComparator:
    """Compare Voynich text against reference corpora."""
    
    @staticmethod
    def compare_stats(corpus1, corpus2):
        """Compare statistical properties of two corpora."""
        stats1 = CorpusComparator._compute_stats(corpus1)
        stats2 = CorpusComparator._compute_stats(corpus2)
        
        comparison = {}
        for key in stats1:
            if key in stats2 and isinstance(stats1[key], (int, float)):
                diff = stats1[key] - stats2[key]
                pct = (diff / stats2[key] * 100) if stats2[key] != 0 else 0
                comparison[key] = {
                    'corpus1': stats1[key],
                    'corpus2': stats2[key],
                    'difference': round(diff, 3),
                    'percent_diff': round(pct, 1)
                }
        
        return comparison
    
    @staticmethod
    def _compute_stats(corpus):
        """Compute statistics for a corpus."""
        words = corpus.words if hasattr(corpus, 'words') else corpus.split()
        text = corpus.raw_text if hasattr(corpus, 'raw_text') else corpus
        
        return {
            'total_words': len(words),
            'unique_words': len(set(words)),
            'vocabulary_richness': round(len(set(words)) / len(words), 4) if words else 0,
            'avg_word_length': round(sum(len(w) for w in words) / len(words), 2) if words else 0,
            'char_entropy': round(EntropyAnalyzer.shannon_entropy([c for c in text.lower() if c.strip()]), 3),
            'word_entropy': round(EntropyAnalyzer.shannon_entropy(words), 3),
            'conditional_entropy_h2': round(EntropyAnalyzer.conditional_entropy(text), 3),
            'compression_ratio': AdvancedMetrics.compression_ratio(text),
        }


# ============================================================
# SECTION 7: EVA TO CSV CONVERTER (structured format)
# ============================================================

class EVAConverter:
    """Convert EVA transcription to structured CSV format."""
    
    @staticmethod
    def to_csv(input_file, output_file):
        """Convert EVA text to structured CSV with metadata."""
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['line_num', 'folio', 'side', 'paragraph', 'line', 'tokens', 'word_count', 'char_count'])
            
            current_folio = 'f1r'
            current_side = 'r'
            current_paragraph = 1
            line_in_paragraph = 0
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Detect folio markers
                if line.startswith('f') and ('r' in line[:4] or 'v' in line[:4]):
                    parts = line.split()
                    if parts:
                        marker = parts[0]
                        if 'r' in marker or 'v' in marker:
                            current_folio = marker
                            current_side = 'r' if 'r' in marker else 'v'
                            current_paragraph = 1
                            line_in_paragraph = 0
                
                tokens = line.split()
                writer.writerow([
                    line_num,
                    current_folio,
                    current_side,
                    current_paragraph,
                    line_in_paragraph,
                    ' '.join(tokens),
                    len(tokens),
                    len(line)
                ])
                
                line_in_paragraph += 1
                if line_in_paragraph > 5:  # Approximate paragraph length
                    current_paragraph += 1
                    line_in_paragraph = 0
        
        print(f"✅ Converted {len(lines)} lines to {output_file}")


# ============================================================
# SECTION 8: COMPREHENSIVE ANALYSIS RUNNER
# ============================================================

class VoynichFullAnalysis:
    """Run all analyses and generate comprehensive report."""
    
    def __init__(self, filepath):
        self.corpus = TextCorpus(filepath, name=Path(filepath).stem)
        self.results = {}
    
    def run_all(self):
        """Run all analysis modules."""
        print("=" * 70)
        print("VOYNICH MANUSCRIPT - COMPREHENSIVE ANALYSIS")
        print("=" * 70)
        
        text = self.corpus.raw_text
        words = self.corpus.words
        chars = self.corpus.clean_chars
        
        # Classical Cipher Analysis
        print("\n📊 1. CLASSICAL CIPHER ANALYSIS")
        print("-" * 50)
        cipher = ClassicalCipherAnalyzer()
        self.results['cipher_analysis'] = {
            'frequency': cipher.frequency_analysis(text),
            'index_of_coincidence': round(cipher.index_of_coincidence(text), 4),
            'substitution_detection': cipher.detect_substitution_pattern(text),
        }
        ic = self.results['cipher_analysis']['index_of_coincidence']
        print(f"  Index of Coincidence: {ic}")
        print(f"  (Natural language: ~0.065, Random: ~0.038)")
        
        # Entropy Analysis
        print("\n📊 2. ENTROPY ANALYSIS")
        print("-" * 50)
        self.results['entropy'] = {
            'char_entropy': round(EntropyAnalyzer.shannon_entropy(chars), 3),
            'word_entropy': round(EntropyAnalyzer.shannon_entropy(words), 3),
            'bigram_entropy': round(EntropyAnalyzer.bigram_entropy(text), 3),
            'conditional_entropy_h2': round(EntropyAnalyzer.conditional_entropy(text), 3),
        }
        h2 = self.results['entropy']['conditional_entropy_h2']
        print(f"  Character entropy: {self.results['entropy']['char_entropy']} bits")
        print(f"  H2 (conditional): {h2} bits")
        print(f"  → {'LOW - natural language structure' if h2 < 3.5 else 'HIGH - cipher/random'}")
        
        # Zipf's Law
        print("\n📊 3. ZIPF'S LAW ANALYSIS")
        print("-" * 50)
        self.results['zipf'] = ZipfAnalyzer.zipf_analysis(words)
        coef = self.results['zipf'].get('zipf_coefficient', 'N/A')
        r2 = self.results['zipf'].get('r_squared', 'N/A')
        print(f"  Zipf coefficient: {coef} (ideal: -1.0)")
        print(f"  R²: {r2}")
        
        # Writing System Classification
        print("\n📊 4. WRITING SYSTEM CLASSIFICATION")
        print("-" * 50)
        self.results['classification'] = WritingSystemClassifier.classify(text)
        cls = self.results['classification']
        print(f"  Classification: {cls['classification']} - {cls['description']}")
        print(f"  Unique characters: {cls['unique_characters']}")
        
        # Advanced Metrics
        print("\n📊 5. ADVANCED METRICS")
        print("-" * 50)
        self.results['advanced'] = {
            'word_length_stats': AdvancedMetrics.word_length_stats(words),
            'adjacent_distances': AdvancedMetrics.adjacent_word_distances(words[:500]),
            'word_repetition': AdvancedMetrics.word_repetition_analysis(words),
            'positional_bias': AdvancedMetrics.positional_bias(words),
            'compression_ratio': AdvancedMetrics.compression_ratio(text),
            'flipped_pairs': AdvancedMetrics.flipped_word_pairs(words),
            'char_repetition': AdvancedMetrics.character_repetition_analysis(text),
        }
        adv = self.results['advanced']
        print(f"  Word length: mean={adv['word_length_stats'].get('mean', 'N/A')}, "
              f"std={adv['word_length_stats'].get('std', 'N/A')}")
        print(f"  Compression ratio: {adv['compression_ratio']}")
        print(f"  Flipped word pairs: {len(adv['flipped_pairs'])}")
        print(f"  Immediate word repeats: {adv['word_repetition']['immediate_repeats']}")
        
        # Markov Chain
        print("\n📊 6. MARKOV CHAIN MODEL")
        print("-" * 50)
        markov = MarkovChainModel()
        markov.train(text)
        sample_state = text[:2].lower()
        predictions = markov.predict_next(sample_state)
        print(f"  Model trained (order 1)")
        print(f"  After '{sample_state}': {predictions[:3]}")
        
        self.results['markov'] = {
            'order': 1,
            'sample_predictions': {sample_state: predictions[:5]}
        }
        
        # Summary
        print("\n" + "=" * 70)
        print("COMPREHENSIVE SUMMARY")
        print("=" * 70)
        self._print_summary()
        
        return self.results
    
    def _print_summary(self):
        """Print comprehensive summary."""
        r = self.results
        print(f"""
Text Statistics:
  Total characters: {len(self.corpus.clean_chars):,}
  Total words: {len(self.corpus.words):,}
  Unique words: {len(set(self.corpus.words)):,}
  Unique characters: {r['classification']['unique_characters']}

Cipher Analysis:
  Index of Coincidence: {r['cipher_analysis']['index_of_coincidence']}
  Likely cipher type: {r['cipher_analysis']['substitution_detection']['likely_cipher_type']}

Entropy:
  Character: {r['entropy']['char_entropy']} bits
  Conditional H2: {r['entropy']['conditional_entropy_h2']} bits
  Interpretation: {'Natural language structure' if r['entropy']['conditional_entropy_h2'] < 3.5 else 'Cipher/random'}

Zipf's Law:
  Coefficient: {r['zipf'].get('zipf_coefficient', 'N/A')}
  R²: {r['zipf'].get('r_squared', 'N/A')}

Writing System: {r['classification']['classification']} ({r['classification']['description']})

Advanced:
  Compression ratio: {r['advanced']['compression_ratio']}
  Word length autocorrelation: {r['advanced']['word_length_stats'].get('autocorrelation', 'N/A')}
  Flipped pairs: {len(r['advanced']['flipped_pairs'])}
""")
    
    def save_report(self, output_path):
        """Save comprehensive report to JSON."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_file': self.corpus.filepath,
            'results': self.results
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"✅ Report saved to: {output_path}")


# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Voynich Manuscript - Comprehensive Cryptanalysis Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --full eva-takahashi.txt
  %(prog)s --classify eva-takahashi.txt
  %(prog)s --csv eva-takahashi.txt -o eva-structured.csv
  %(prog)s --compare voynich.txt latin.txt
  %(prog)s --cipher eva-takahashi.txt
  %(prog)s --entropy eva-takahashi.txt
  %(prog)s --markov eva-takahashi.txt --generate "daiin"
        """
    )
    
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--full', metavar='FILE', help='Run full analysis')
    mode.add_argument('--classify', metavar='FILE', help='Classify writing system')
    mode.add_argument('--csv', metavar='FILE', help='Convert EVA to structured CSV')
    mode.add_argument('--compare', nargs=2, metavar=('FILE1', 'FILE2'), help='Compare two corpora')
    mode.add_argument('--cipher', metavar='FILE', help='Classical cipher analysis')
    mode.add_argument('--entropy', metavar='FILE', help='Entropy analysis')
    mode.add_argument('--markov', metavar='FILE', help='Markov chain analysis')
    
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--generate', help='Generate text with Markov model')
    
    args = parser.parse_args()
    
    if args.full:
        analysis = VoynichFullAnalysis(args.full)
        results = analysis.run_all()
        output = args.output or f"research-output/full-analysis-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analysis.save_report(output)
    
    elif args.classify:
        corpus = TextCorpus(args.classify)
        result = WritingSystemClassifier.classify(corpus.raw_text)
        print(json.dumps(result, indent=2))
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
    
    elif args.csv:
        output = args.output or args.csv.replace('.txt', '.csv')
        EVAConverter.to_csv(args.csv, output)
    
    elif args.compare:
        c1 = TextCorpus(args.compare[0])
        c2 = TextCorpus(args.compare[1])
        result = CorpusComparator.compare_stats(c1, c2)
        print(json.dumps(result, indent=2))
    
    elif args.cipher:
        corpus = TextCorpus(args.cipher)
        cipher = ClassicalCipherAnalyzer()
        result = {
            'frequency': cipher.frequency_analysis(corpus.raw_text),
            'bigrams': dict(cipher.bigram_analysis(corpus.raw_text).most_common(20)),
            'trigrams': dict(cipher.trigram_analysis(corpus.raw_text).most_common(20)),
            'index_of_coincidence': cipher.index_of_coincidence(corpus.raw_text),
            'kasiski': cipher.kasiski_examination(corpus.raw_text),
            'substitution_detection': cipher.detect_substitution_pattern(corpus.raw_text),
        }
        print(json.dumps(result, indent=2))
    
    elif args.entropy:
        corpus = TextCorpus(args.entropy)
        result = {
            'char_entropy': EntropyAnalyzer.shannon_entropy(corpus.clean_chars),
            'word_entropy': EntropyAnalyzer.shannon_entropy(corpus.words),
            'bigram_entropy': EntropyAnalyzer.bigram_entropy(corpus.raw_text),
            'conditional_entropy_h2': EntropyAnalyzer.conditional_entropy(corpus.raw_text),
            'zipf': ZipfAnalyzer.zipf_analysis(corpus.words),
        }
        print(json.dumps(result, indent=2))
    
    elif args.markov:
        corpus = TextCorpus(args.markov)
        markov = MarkovChainModel()
        markov.train(corpus.raw_text)
        
        if args.generate:
            generated = markov.generate(args.generate, 200)
            print(f"Generated text: {generated}")
        else:
            # Show predictions for common Voynich words
            test_words = ['daiin', 'ol', 'chedy', 'shedy', 'qokaiin']
            result = {}
            for word in test_words:
                if len(word) >= 2:
                    state = word[:2]
                    pred = markov.predict_next(state)
                    result[word] = pred
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
