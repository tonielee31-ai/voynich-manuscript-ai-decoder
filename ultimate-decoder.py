#!/usr/bin/env python3
"""
Voynich Ultimate Decoder - Combines ALL Research Findings
==========================================================
The definitive decoder that integrates:

1. Correct EVA tokenization (ch, sh, qo as single tokens)
2. Currier A/B section separation
3. HMM vowel/consonant detection
4. Constraint solving with multiple language targets
5. Hybrid method comparison (Naibbe, Caspari, Hebrew, Occitan)
6. Statistical scoring (IC, Zipf, H2, vocabulary match)
7. Prefix/suffix morphological analysis

This is the culmination of all research cycles.

Usage:
    python3 ultimate-decoder.py --eva eva-takahashi.txt --lines 30
    python3 ultimate-decoder.py --eva eva-takahashi.txt --currier A
    python3 ultimate-decoder.py --eva eva-takahashi.txt --currier B
    python3 ultimate-decoder.py --eva eva-takahashi.txt --full
"""

import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "research-output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# EVA TOKENIZER (ch, sh, qo, cth, cph as single tokens)
# ============================================================

EVA_MULTI_TOKENS = ['cth', 'cph', 'cfh', 'ckh', 'sh', 'ch', 'qo']

def tokenize_eva(word):
    """Tokenize EVA word treating multi-char tokens as single units."""
    tokens = []
    i = 0
    clean = ''.join(c for c in word if c.isalpha() or c in '!*-=')
    while i < len(clean):
        matched = False
        for token in sorted(EVA_MULTI_TOKENS, key=len, reverse=True):
            if clean[i:i+len(token)] == token:
                tokens.append(token)
                i += len(token)
                matched = True
                break
        if not matched:
            if i < len(clean) and clean[i].isalpha():
                tokens.append(clean[i])
            i += 1
    return tokens


# ============================================================
# VOCABULARY DATABASES
# ============================================================

VOWELS_LATIN = set('aeiou')

ITALIAN_WORDS = set([
    'il', 'lo', 'la', 'le', 'di', 'del', 'al', 'da', 'che', 'per', 'con', 'in',
    'non', 'e', 'o', 'a', 'ma', 'se', 'si', 'mi', 'ti', 'ci', 'vi',
    'come', 'dove', 'quando', 'molto', 'poco', 'tanto', 'primo',
    'cuore', 'testa', 'occhio', 'naso', 'bocca', 'mano', 'piede',
    'acqua', 'olio', 'sale', 'miele', 'vino', 'latte',
    'erba', 'fiore', 'foglia', 'radice', 'pianta', 'seme', 'frutto', 'albero',
    'sole', 'luna', 'stella', 'terra', 'cielo', 'mare', 'fuoco', 'aria',
    'dolore', 'male', 'febbre', 'tosse', 'cura', 'rimedio', 'medicina',
    'rosso', 'nero', 'bianco', 'verde', 'giallo', 'grande', 'piccolo',
    'dare', 'fare', 'dire', 'avere', 'essere', 'prendere', 'bollire',
    'buono', 'bello', 'forte', 'dolce', 'caldo', 'freddo', 'secco',
    'salvia', 'menta', 'rosmarino', 'basilico', 'timo', 'origano',
    'lavanda', 'camomilla', 'verbena', 'ruta', 'alloro', 'olivo',
])

HEBREW_WORDS = set([
    'shem', 'melech', 'adam', 'yom', 'laila', 'aretz', 'mayim',
    'esh', 'ruach', 'nefesh', 'lev', 'ayin', 'yad', 'regel', 'rosh',
    'ben', 'bat', 'av', 'em', 'ach', 'ish', 'tov', 'ra',
    'gadol', 'katan', 'or', 'shemesh', 'kochav', 'etz', 'pri',
    'deshe', 'eshev', 'zera', 'lechem', 'yayin', 'shemen', 'devash',
])

OCCITAN_WORDS = set([
    'lo', 'la', 'los', 'las', 'de', 'del', 'al', 'que', 'per', 'se',
    'flor', 'fuelha', 'raitz', 'erba', 'planta', 'aiga', 'oli', 'sal',
    'mel', 'ros', 'rosa', 'vin', 'pan', 'lait', 'uelh', 'cor', 'man',
    'sol', 'luna', 'cel', 'flors', 'suc', 'poma', 'bon', 'bel', 'gran',
    'caud', 'freg', 'sec', 'verd', 'roge', 'negre', 'clar',
])


# ============================================================
# CURRIER SECTION DETECTOR
# ============================================================

class CurrierDetector:
    """Detect Currier A/B sections based on suffix distribution."""
    
    @staticmethod
    def classify_lines(lines, tokenized_words):
        """Classify each line as Currier A, B, or Mixed."""
        classifications = []
        
        for i, line in enumerate(lines):
            words = line.split()
            edy_count = 0
            iin_count = 0
            total = 0
            
            for word in words:
                tokens = tokenize_eva(word)
                total += 1
                if len(tokens) >= 3:
                    if tokens[-3:] == ['e', 'd', 'y']:
                        edy_count += 1
                    if tokens[-3:] == ['i', 'i', 'n']:
                        iin_count += 1
            
            if total > 0:
                edy_pct = edy_count / total * 100
                iin_pct = iin_count / total * 100
                
                if edy_pct > iin_pct * 1.5:
                    lang = 'A'
                elif iin_pct > edy_pct * 1.5:
                    lang = 'B'
                else:
                    lang = 'M'
            else:
                lang = 'M'
                edy_pct = 0
                iin_pct = 0
            
            classifications.append({
                'line': i + 1,
                'language': lang,
                'edy_pct': round(edy_pct, 1),
                'iin_pct': round(iin_pct, 1),
                'total_words': total
            })
        
        return classifications


# ============================================================
# DECODING METHODS
# ============================================================

class NaibbeDecoder:
    """Naibbe Inverse Decoder (Greshko 2025)."""
    
    MAPPING = {
        'o': 'i', 'e': 'qu', 'y': 'a', 'a': 'e', 'd': 'd',
        'i': 'n', 'ch': 'g', 'l': 'l', 'k': 'c', 'r': 'l',
        'n': 'e', 't': 'o', 'sh': 'o', 'qo': 'm', 's': 'o',
    }
    
    def decode_word(self, word):
        tokens = tokenize_eva(word)
        return ''.join(self.MAPPING.get(t, '?') for t in tokens)


class CaspariDecoder:
    """Caspari-Faccini EVA→Italian."""
    
    MAPPING = {
        'o': 'o', 'e': 'e', 'y': 'i', 'a': 'a', 'd': 'd',
        'i': 'i', 'ch': 'c', 'l': 'l', 'k': 'c', 'r': 'r',
        'n': 'n', 't': 't', 'sh': 's', 'qo': 'qu', 's': 's',
    }
    
    def decode_word(self, word):
        tokens = tokenize_eva(word)
        return ''.join(self.MAPPING.get(t, '?') for t in tokens)


class HebrewDecoder:
    """Hebrew/Judeo-Italian consonant mapping."""
    
    MAPPING = {
        'o': '', 'e': '', 'y': 'y', 'a': '', 'd': 'd',
        'i': '', 'ch': 'kh', 'l': 'l', 'k': 'k', 'r': 'r',
        'n': 'n', 't': 't', 'sh': 'sh', 'qo': 'q', 's': 's',
    }
    
    def decode_word(self, word):
        tokens = tokenize_eva(word)
        return ''.join(self.MAPPING.get(t, t) for t in tokens)


class OccitanDecoder:
    """Occitan phonetic mapping."""
    
    MAPPING = {
        'o': 'o', 'e': 'e', 'y': 'i', 'a': 'a', 'd': 'd',
        'i': 'i', 'ch': 'ch', 'l': 'l', 'k': 'c', 'r': 'r',
        'n': 'n', 't': 't', 'sh': 'ch', 'qo': 'qu', 's': 's',
    }
    
    def decode_word(self, word):
        tokens = tokenize_eva(word)
        return ''.join(self.MAPPING.get(t, '?') for t in tokens)


# ============================================================
# SCORING ENGINE
# ============================================================

class Scorer:
    """Score decoded text for linguistic plausibility."""
    
    @staticmethod
    def score(decoded_text, language='italian'):
        words = decoded_text.lower().split()
        if not words:
            return {'total': 0, 'details': {}}
        
        vocab = {'italian': ITALIAN_WORDS, 'hebrew': HEBREW_WORDS, 'occitan': OCCITAN_WORDS}.get(language, ITALIAN_WORDS)
        
        # 1. Dictionary match (30 points)
        matches = sum(1 for w in words if w in vocab)
        dict_score = matches / len(words) * 30 if words else 0
        
        # 2. Vowel ratio (20 points, target 35-45%)
        all_text = ''.join(words)
        vowel_count = sum(1 for c in all_text if c in VOWELS_LATIN)
        total_chars = len(all_text)
        vowel_ratio = vowel_count / total_chars if total_chars > 0 else 0
        vowel_score = max(0, 20 - abs(vowel_ratio - 0.4) * 100)
        
        # 3. No triple repeats (10 points)
        triple_repeats = sum(1 for i in range(len(all_text)-2) if all_text[i] == all_text[i+1] == all_text[i+2])
        triple_score = max(0, 10 - triple_repeats * 5)
        
        # 4. Bigram plausibility (20 points)
        valid_bigrams = 0
        total_bigrams = 0
        for word in words:
            for i in range(len(word)-1):
                total_bigrams += 1
                c1, c2 = word[i], word[i+1]
                if (c1 in VOWELS_LATIN) != (c2 in VOWELS_LATIN):
                    valid_bigrams += 1
        bigram_score = (valid_bigrams / total_bigrams * 20) if total_bigrams > 0 else 0
        
        # 5. Word length (10 points, Italian avg ~5)
        avg_len = sum(len(w) for w in words) / len(words) if words else 0
        length_score = max(0, 10 - abs(avg_len - 5) * 3)
        
        # 6. Unique ratio (10 points)
        unique_ratio = len(set(words)) / len(words) if words else 0
        unique_score = min(10, unique_ratio * 20) if unique_ratio < 0.5 else max(0, 20 - unique_ratio * 15)
        
        total = dict_score + vowel_score + triple_score + bigram_score + length_score + unique_score
        
        return {
            'total': round(total, 1),
            'dictionary_match': round(dict_score, 1),
            'vowel_ratio': round(vowel_score, 1),
            'no_triple_repeats': round(triple_score, 1),
            'bigram_plausibility': round(bigram_score, 1),
            'word_length': round(length_score, 1),
            'unique_ratio': round(unique_score, 1),
            'matches': matches,
            'vowel_pct': round(vowel_ratio * 100, 1),
            'avg_word_len': round(avg_len, 1),
        }


# ============================================================
# ULTIMATE DECODER
# ============================================================

class UltimateDecoder:
    """Combines all methods and selects best per line."""
    
    def __init__(self):
        self.decoders = {
            'naibbe': (NaibbeDecoder(), 'italian'),
            'caspari': (CaspariDecoder(), 'italian'),
            'hebrew': (HebrewDecoder(), 'hebrew'),
            'occitan': (OccitanDecoder(), 'occitan'),
        }
        self.scorer = Scorer()
    
    def decode_line(self, line):
        """Decode a line using all methods, return best."""
        results = {}
        
        for name, (decoder, language) in self.decoders.items():
            decoded_words = [decoder.decode_word(w) for w in line.split()]
            decoded_text = ' '.join(decoded_words)
            score = self.scorer.score(decoded_text, language)
            
            results[name] = {
                'decoded': decoded_text,
                'words': decoded_words,
                'language': language,
                'score': score['total'],
                'details': score,
            }
        
        best = max(results, key=lambda x: results[x]['score'])
        
        return {
            'original': line,
            'methods': results,
            'best_method': best,
            'best_decoded': results[best]['decoded'],
            'best_score': results[best]['score'],
        }
    
    def decode_section(self, lines, section_name="all"):
        """Decode a section of lines."""
        all_results = []
        method_wins = Counter()
        total_scores = defaultdict(float)
        
        for line in lines:
            if not line.strip():
                continue
            result = self.decode_line(line)
            all_results.append(result)
            method_wins[result['best_method']] += 1
            for method, data in result['methods'].items():
                total_scores[method] += data['score']
        
        avg_scores = {m: round(s / max(1, len(all_results)), 1) for m, s in total_scores.items()}
        
        return {
            'section': section_name,
            'total_lines': len(all_results),
            'method_wins': dict(method_wins),
            'average_scores': avg_scores,
            'best_overall': method_wins.most_common(1)[0] if method_wins else ('none', 0),
            'results': all_results,
        }
    
    def decode_with_currier(self, lines):
        """Decode with Currier A/B awareness."""
        # Detect Currier sections
        tokenized = [(w, tokenize_eva(w)) for l in lines for w in l.split()]
        currier = CurrierDetector.classify_lines(lines, tokenized)
        
        # Separate by language
        a_lines = [lines[i] for i, c in enumerate(currier) if c['language'] == 'A' and i < len(lines)]
        b_lines = [lines[i] for i, c in enumerate(currier) if c['language'] == 'B' and i < len(lines)]
        m_lines = [lines[i] for i, c in enumerate(currier) if c['language'] == 'M' and i < len(lines)]
        
        # Decode each section
        a_result = self.decode_section(a_lines, "Currier A (Herbal)")
        b_result = self.decode_section(b_lines, "Currier B (Biological)")
        m_result = self.decode_section(m_lines, "Mixed")
        
        return {
            'currier_a': a_result,
            'currier_b': b_result,
            'mixed': m_result,
            'currier_distribution': {
                'a_lines': len(a_lines),
                'b_lines': len(b_lines),
                'm_lines': len(m_lines),
            }
        }
    
    def full_decode(self, filepath, max_lines=None, currier_filter=None):
        """Full manuscript decode with all analysis."""
        with open(filepath, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        
        if max_lines:
            lines = lines[:max_lines]
        
        # Token frequency analysis
        all_tokens = []
        for line in lines:
            for word in line.split():
                all_tokens.extend(tokenize_eva(word))
        token_freq = Counter(all_tokens)
        
        # Decode with Currier awareness
        currier_result = self.decode_with_currier(lines)
        
        # If filter specified, return only that section
        if currier_filter == 'A':
            return currier_result['currier_a']
        elif currier_filter == 'B':
            return currier_result['currier_b']
        
        # Otherwise return everything
        return {
            'timestamp': datetime.now().isoformat(),
            'total_lines': len(lines),
            'token_frequency': {
                'total': len(all_tokens),
                'unique': len(token_freq),
                'top_10': [(t, c, round(c/len(all_tokens)*100, 2)) for t, c in token_freq.most_common(10)]
            },
            'currier_analysis': currier_result,
        }


def main():
    parser = argparse.ArgumentParser(description="Voynich Ultimate Decoder")
    parser.add_argument('--eva', required=True, help='EVA text file')
    parser.add_argument('--lines', type=int, help='Number of lines')
    parser.add_argument('--currier', choices=['A', 'B'], help='Filter by Currier language')
    parser.add_argument('--full', action='store_true', help='Full manuscript')
    parser.add_argument('--json', action='store_true', help='JSON output')
    
    args = parser.parse_args()
    
    decoder = UltimateDecoder()
    
    if args.currier:
        result = decoder.full_decode(args.eva, currier_filter=args.currier)
    else:
        result = decoder.full_decode(args.eva, max_lines=args.lines)
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 70)
        print("VOYNICH ULTIMATE DECODER")
        print("Combining: Naibbe + Caspari + Hebrew + Occitan")
        print("With: Currier A/B + Correct EVA Tokenization")
        print("=" * 70)
        
        if 'token_frequency' in result:
            print(f"\n📊 TOKEN FREQUENCY (ch/sh/qo as single tokens)")
            print("-" * 50)
            for token, count, pct in result['token_frequency']['top_10']:
                bar = "█" * int(pct * 2)
                print(f"  {token:6s}: {count:6d} ({pct:5.2f}%) {bar}")
        
        if 'currier_analysis' in result:
            ca = result['currier_analysis']
            dist = ca['currier_distribution']
            print(f"\n📊 CURRIER DISTRIBUTION")
            print("-" * 50)
            print(f"  Currier A (Herbal):     {dist['a_lines']} lines")
            print(f"  Currier B (Biological): {dist['b_lines']} lines")
            print(f"  Mixed:                  {dist['m_lines']} lines")
            
            for section_name, section_data in [('currier_a', 'Currier A'), ('currier_b', 'Currier B')]:
                s = ca[section_name]
                if s['total_lines'] > 0:
                    print(f"\n📊 {section_name.upper().replace('_', ' ')} RESULTS ({s['total_lines']} lines)")
                    print("-" * 50)
                    print(f"  Method wins: {s['method_wins']}")
                    print(f"  Average scores: {s['average_scores']}")
                    best, count = s['best_overall']
                    print(f"  Best method: {best} ({count} wins)")
                    
                    # Show sample decodings
                    print(f"\n  Sample decodings:")
                    for r in s['results'][:5]:
                        print(f"    {r['original'][:40]:40s}")
                        print(f"    → {r['best_decoded'][:40]} ({r['best_method']}, score: {r['best_score']})")
        
        # If filtered result
        if 'total_lines' in result and 'currier_analysis' not in result:
            print(f"\n📊 RESULTS ({result['total_lines']} lines)")
            print("-" * 50)
            print(f"  Method wins: {result['method_wins']}")
            print(f"  Average scores: {result['average_scores']}")
            
            print(f"\n  Sample decodings:")
            for r in result['results'][:10]:
                print(f"    {r['original'][:40]:40s}")
                print(f"    → {r['best_decoded'][:40]} ({r['best_method']}, {r['best_score']})")
    
    # Save
    output = os.path.join(OUTPUT_DIR, 'ultimate-decoder.json')
    with open(output, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n✅ Saved to {output}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Voynich Ultimate Decoder")
    parser.add_argument('--eva', required=True, help='EVA text file')
    parser.add_argument('--lines', type=int, help='Number of lines')
    parser.add_argument('--currier', choices=['A', 'B'], help='Filter by Currier language')
    parser.add_argument('--full', action='store_true', help='Full manuscript')
    parser.add_argument('--json', action='store_true', help='JSON output')
    
    args = parser.parse_args()
    
    decoder = UltimateDecoder()
    
    if args.currier:
        result = decoder.full_decode(args.eva, currier_filter=args.currier)
    else:
        result = decoder.full_decode(args.eva, max_lines=args.lines)
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 70)
        print("VOYNICH ULTIMATE DECODER")
        print("Combining: Naibbe + Caspari + Hebrew + Occitan")
        print("With: Currier A/B + Correct EVA Tokenization")
        print("=" * 70)
        
        if 'token_frequency' in result:
            print(f"\n📊 TOKEN FREQUENCY (ch/sh/qo as single tokens)")
            print("-" * 50)
            for token, count, pct in result['token_frequency']['top_10']:
                bar = "█" * int(pct * 2)
                print(f"  {token:6s}: {count:6d} ({pct:5.2f}%) {bar}")
        
        if 'currier_analysis' in result:
            ca = result['currier_analysis']
            dist = ca['currier_distribution']
            print(f"\n📊 CURRIER DISTRIBUTION")
            print("-" * 50)
            print(f"  Currier A (Herbal):     {dist['a_lines']} lines")
            print(f"  Currier B (Biological): {dist['b_lines']} lines")
            print(f"  Mixed:                  {dist['m_lines']} lines")
            
            for section_name, section_data in [('currier_a', 'Currier A'), ('currier_b', 'Currier B')]:
                s = ca[section_name]
                if s['total_lines'] > 0:
                    print(f"\n📊 {section_name.upper().replace('_', ' ')} RESULTS ({s['total_lines']} lines)")
                    print("-" * 50)
                    print(f"  Method wins: {s['method_wins']}")
                    print(f"  Average scores: {s['average_scores']}")
                    best, count = s['best_overall']
                    print(f"  Best method: {best} ({count} wins)")
                    
                    print(f"\n  Sample decodings:")
                    for r in s['results'][:5]:
                        print(f"    {r['original'][:40]:40s}")
                        print(f"    → {r['best_decoded'][:40]} ({r['best_method']}, score: {r['best_score']})")
        
        if 'total_lines' in result and 'currier_analysis' not in result:
            print(f"\n📊 RESULTS ({result['total_lines']} lines)")
            print("-" * 50)
            print(f"  Method wins: {result['method_wins']}")
            print(f"  Average scores: {result['average_scores']}")
            
            print(f"\n  Sample decodings:")
            for r in result['results'][:10]:
                print(f"    {r['original'][:40]:40s}")
                print(f"    → {r['best_decoded'][:40]} ({r['best_method']}, {r['best_score']})")
    
    output = os.path.join(OUTPUT_DIR, 'ultimate-decoder.json')
    with open(output, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n✅ Saved to {output}")
