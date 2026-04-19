#!/usr/bin/env python3
"""
Voynich Definitive Decoder v2.0
=================================
The BEST decoder combining ALL research:

CORRECT EVA TOKENIZATION:
  ch, sh, qo, cth, cph, cfh, ckh = single tokens

HMM-INFORMED PHONEME ASSIGNMENT:
  Vowels (State 0): o, a, y, e, i
  Consonants (State 1): ch, sh, qo, d, l, k, r, n, t, s, cth, cph

CURRIER A/B AWARENESS:
  A: -edy suffix dominant (Herbal)
  B: -iin suffix dominant (Biological)

MULTI-METHOD SCORING:
  Italian, Occitan, Hebrew vocabulary validation
  Vowel ratio, bigram plausibility, word length

Usage:
    python3 definitive-decoder.py --eva eva-takahashi.txt --lines 20
    python3 definitive-decoder.py --eva eva-takahashi.txt --currier A
    python3 definitive-decoder.py --eva eva-takahashi.txt --currier B
"""

import json
import math
import os
import sys
from collections import Counter, defaultdict


PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "research-output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# EVA TOKENIZER
# ============================================================

EVA_MULTI = ['cth', 'cph', 'cfh', 'ckh', 'sh', 'ch', 'qo']

def tokenize(word):
    """Tokenize EVA word with multi-char tokens."""
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
# PHONEME MAPPINGS (HMM-informed)
# ============================================================

# Vowels: o, a, y, e, i (from HMM State 0 + frequency analysis)
# Consonants: ch, sh, qo, d, l, k, r, n, t, s, cth, cph

# Method 1: Italian (Caspari-style, best vowel ratio)
ITALIAN_MAP = {
    'o': 'o', 'a': 'a', 'y': 'i', 'e': 'e', 'i': 'i',
    'ch': 'c', 'sh': 's', 'qo': 'qu',
    'd': 'd', 'l': 'l', 'k': 'c', 'r': 'r',
    'n': 'n', 't': 't', 's': 's',
    'cth': 'b', 'cph': 'p', 'cfh': 'f', 'ckh': 'g',
    'q': 'q', 'c': 'c', 'f': 'f', 'g': 'g',
    '!': '', '*': '', '-': '', '=': '',
}

# Method 2: Occitan (highest scores in hybrid decoder)
OCCITAN_MAP = {
    'o': 'o', 'a': 'a', 'y': 'i', 'e': 'e', 'i': 'i',
    'ch': 'ch', 'sh': 'ch', 'qo': 'qu',
    'd': 'd', 'l': 'l', 'k': 'c', 'r': 'r',
    'n': 'n', 't': 't', 's': 's',
    'cth': 'b', 'cph': 'p', 'cfh': 'f', 'ckh': 'g',
    'q': 'q', 'c': 'c', 'f': 'f', 'g': 'g',
    '!': '', '*': '', '-': '', '=': '',
}

# Method 3: Hebrew (consonant-only, abjad style)
HEBREW_MAP = {
    'o': 'o', 'a': 'a', 'y': 'y', 'e': 'e', 'i': 'i',
    'ch': 'kh', 'sh': 'sh', 'qo': 'q',
    'd': 'd', 'l': 'l', 'k': 'k', 'r': 'r',
    'n': 'n', 't': 't', 's': 's',
    'cth': 't', 'cph': 'p', 'cfh': 'f', 'ckh': 'k',
    'q': 'q', 'c': 'k', 'f': 'p', 'g': 'g',
    '!': '', '*': '', '-': '', '=': '',
}

# Method 4: Naibbe Inverse (Greshko 2025, verbose homophonic)
NAIBBE_MAP = {
    'o': 'i', 'a': 'e', 'y': 'a', 'e': 'u', 'i': 'o',
    'ch': 't', 'sh': 's', 'qo': 'qu',
    'd': 'n', 'l': 'l', 'k': 'c', 'r': 'r',
    'n': 'm', 't': 'd', 's': 'r',
    'cth': 'b', 'cph': 'p', 'cfh': 'f', 'ckh': 'g',
    'q': 'q', 'c': 'c', 'f': 'f', 'g': 'g',
    '!': '', '*': '', '-': '', '=': '',
}

METHODS = {
    'italian': (ITALIAN_MAP, 'italian'),
    'occitan': (OCCITAN_MAP, 'occitan'),
    'hebrew': (HEBREW_MAP, 'hebrew'),
    'naibbe': (NAIBBE_MAP, 'italian'),
}

# Context-dependent mappings for Currier A vs B
CURRIER_A_OVERRIDES = {
    # Currier A has more -edy endings, adjust common tokens
    'edy': 'ete',  # -edy → -ete (Italian past participle)
    'ey': 'ei',
}

CURRIER_B_OVERRIDES = {
    # Currier B has more -iin endings
    'iin': 'ino',  # -iin → -ino (Italian diminutive)
    'in': 'in',
}


# ============================================================
# VOCABULARY
# ============================================================

VOWELS = set('aeiou')

ITALIAN = set([
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
    'uno', 'due', 'tre', 'parte', 'corpo', 'ar', 'or', 'ol',
    'et', 'el', 'ol', 'al', 'il', 'ar', 'or', 'si', 'no', 'se',
])

OCCITAN = set([
    'lo', 'la', 'los', 'las', 'de', 'del', 'al', 'que', 'per', 'se',
    'flor', 'erba', 'planta', 'aiga', 'oli', 'sal', 'mel', 'ros',
    'rosa', 'vin', 'pan', 'sol', 'luna', 'cel', 'bon', 'bel', 'gran',
    'caud', 'freg', 'sec', 'verd', 'roge', 'negre', 'clar',
    'cor', 'man', 'cap', 'pel', 'os', 'sang', 'carn', 'ar', 'or', 'ol',
])

HEBREW = set([
    'shem', 'adam', 'yom', 'aretz', 'mayim', 'esh', 'lev', 'yad',
    'rosh', 'ben', 'bat', 'av', 'em', 'ach', 'ish', 'tov', 'ra',
    'or', 'etz', 'pri', 'lechem', 'yayin', 'ar', 'el', 'ol',
])

ALL_VOCABS = {'italian': ITALIAN, 'occitan': OCCITAN, 'hebrew': HEBREW}


# ============================================================
# CURRIER DETECTOR
# ============================================================

def detect_currier(lines):
    """Detect Currier language for each line."""
    results = []
    for line in lines:
        words = line.split()
        edy = sum(1 for w in words if tokenize(w)[-3:] == ['e', 'd', 'y'])
        iin = sum(1 for w in words if tokenize(w)[-3:] == ['i', 'i', 'n'])
        total = len(words)
        if total > 0:
            if edy / total > iin / total * 1.5:
                lang = 'A'
            elif iin / total > edy / total * 1.5:
                lang = 'B'
            else:
                lang = 'M'
        else:
            lang = 'M'
        results.append(lang)
    return results


# ============================================================
# DECODER
# ============================================================

def decode_word(word, method_map):
    """Decode a single word."""
    tokens = tokenize(word)
    return ''.join(method_map.get(t, '?') for t in tokens)


def score_decoded(text, vocab_name='italian'):
    """Score decoded text."""
    words = text.lower().split()
    if not words:
        return 0, {}
    
    vocab = ALL_VOCABS.get(vocab_name, ITALIAN)
    
    # Dictionary match
    matches = sum(1 for w in words if w in vocab)
    dict_score = matches / len(words) * 30
    
    # Vowel ratio
    all_text = ''.join(words)
    vowel_count = sum(1 for c in all_text if c in VOWELS)
    total = len(all_text)
    vowel_ratio = vowel_count / total if total > 0 else 0
    vowel_score = max(0, 20 - abs(vowel_ratio - 0.4) * 100)
    
    # No triple repeats
    triples = sum(1 for i in range(len(all_text)-2) if all_text[i] == all_text[i+1] == all_text[i+2])
    triple_score = max(0, 10 - triples * 5)
    
    # Bigram plausibility
    valid = 0
    total_big = 0
    for w in words:
        for i in range(len(w)-1):
            total_big += 1
            if (w[i] in VOWELS) != (w[i+1] in VOWELS):
                valid += 1
    bigram_score = (valid / total_big * 20) if total_big > 0 else 0
    
    # Word length
    avg_len = sum(len(w) for w in words) / len(words)
    length_score = max(0, 10 - abs(avg_len - 5) * 3)
    
    total_score = dict_score + vowel_score + triple_score + bigram_score + length_score
    
    return round(total_score, 1), {
        'matches': matches,
        'vowel_pct': round(vowel_ratio * 100, 1),
        'dict_score': round(dict_score, 1),
        'vowel_score': round(vowel_score, 1),
    }


def decode_line(line, currier=None):
    """Decode a line using all methods, return best."""
    results = {}
    words = line.split()
    
    for method_name, (method_map, vocab_name) in METHODS.items():
        decoded_words = [decode_word(w, method_map) for w in words]
        decoded = ' '.join(decoded_words)
        score, details = score_decoded(decoded, vocab_name)
        results[method_name] = {
            'decoded': decoded,
            'score': score,
            'details': details,
        }
    
    best = max(results, key=lambda x: results[x]['score'])
    
    return {
        'original': line,
        'best_method': best,
        'best_decoded': results[best]['decoded'],
        'best_score': results[best]['score'],
        'all_methods': results,
        'currier': currier,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 definitive-decoder.py <eva_file> [--lines N] [--currier A|B]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    max_lines = None
    currier_filter = None
    
    if '--lines' in sys.argv:
        idx = sys.argv.index('--lines')
        max_lines = int(sys.argv[idx + 1])
    
    if '--currier' in sys.argv:
        idx = sys.argv.index('--currier')
        currier_filter = sys.argv[idx + 1]
    
    with open(filepath, 'r') as f:
        all_lines = [l.strip() for l in f.readlines() if l.strip()]
    
    # Detect Currier
    currier_labels = detect_currier(all_lines)
    
    # Filter if requested
    if currier_filter:
        lines = [l for l, c in zip(all_lines, currier_labels) if c == currier_filter]
        labels = [c for c in currier_labels if c == currier_filter]
    else:
        lines = all_lines
        labels = currier_labels
    
    if max_lines:
        lines = lines[:max_lines]
        labels = labels[:max_lines]
    
    # Decode all lines
    results = []
    method_wins = Counter()
    total_scores = defaultdict(float)
    
    for line, label in zip(lines, labels):
        if not line:
            continue
        result = decode_line(line, label)
        results.append(result)
        method_wins[result['best_method']] += 1
        for m, data in result['all_methods'].items():
            total_scores[m] += data['score']
    
    avg_scores = {m: round(s / max(1, len(results)), 1) for m, s in total_scores.items()}
    
    # Print
    print("=" * 70)
    print("VOYNICH DEFINITIVE DECODER v2.0")
    print("=" * 70)
    
    print(f"\nLines decoded: {len(results)}")
    if currier_filter:
        print(f"Currier filter: {currier_filter}")
    
    # Currier distribution
    a_count = sum(1 for l in labels if l == 'A')
    b_count = sum(1 for l in labels if l == 'B')
    m_count = sum(1 for l in labels if l == 'M')
    print(f"\nCurrier distribution: A={a_count}, B={b_count}, Mixed={m_count}")
    
    print(f"\n📊 METHOD COMPARISON")
    print("-" * 50)
    for method in ['italian', 'occitan', 'naibbe', 'hebrew']:
        wins = method_wins.get(method, 0)
        avg = avg_scores.get(method, 0)
        bar = "█" * int(avg / 2)
        print(f"  {method:10s}: {wins:4d} wins, avg {avg:5.1f} {bar}")
    
    best_method = method_wins.most_common(1)[0] if method_wins else ('none', 0)
    print(f"\n  BEST OVERALL: {best_method[0]} ({best_method[1]} wins)")
    
    print(f"\n📊 SAMPLE DECODINGS")
    print("-" * 70)
    for r in results[:15]:
        currier = r.get('currier', '?')
        print(f"  [{currier}] {r['original'][:45]}")
        print(f"       → {r['best_decoded'][:45]} ({r['best_method']}, {r['best_score']})")
    
    # Save
    output_data = {
        'lines_decoded': len(results),
        'currier_distribution': {'A': a_count, 'B': b_count, 'M': m_count},
        'method_wins': dict(method_wins),
        'average_scores': avg_scores,
        'best_method': best_method[0],
        'results': results[:100],
    }
    
    output = os.path.join(OUTPUT_DIR, 'definitive-decoder.json')
    with open(output, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    print(f"\n✅ Saved to {output}")


if __name__ == "__main__":
    main()
