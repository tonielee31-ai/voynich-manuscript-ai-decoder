#!/usr/bin/env python3
"""
Voynich Manuscript - Evolutionary Glyph-Phoneme Mapper
=======================================================
Based on arxiv:2107.05381 - Evolutionary Computation for Crib-Based Decryption

Uses genetic algorithm to find optimal mapping between Voynich glyphs and
phonemic values by maximizing fitness function that measures linguistic plausibility.

Key insight: If we know some words (cribs), we can evolve a mapping that
translates Voynich text into readable language.

Usage:
    python3 evolutionary-mapper.py --eva eva-takahashi.txt --crib "daiin=dei" --generations 1000
    python3 evolutionary-mapper.py --eva eva-takahashi.txt --auto --generations 5000
"""

import argparse
import json
import math
import os
import random
import sys
from collections import Counter
from pathlib import Path


# ============================================================
# PHONEME SPACE
# ============================================================

# Italian/Latin phonemes (most likely target language based on research)
VOWELS = ['a', 'e', 'i', 'o', 'u']
CONSONANTS = ['b', 'c', 'd', 'f', 'g', 'h', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'z',
              'ch', 'gh', 'gl', 'gn', 'sc', 'qu']
ALL_PHONEMES = VOWELS + CONSONANTS

# Italian word patterns (CV, CVC, etc.)
ITALIAN_PATTERNS = [
    'CV', 'CVC', 'CVCV', 'CVCVC', 'CVCCV', 'CVCVCV',
    'VC', 'VCV', 'VCVC', 'VCCV'
]

# Common Italian words for fitness evaluation
ITALIAN_WORDS = set([
    'il', 'lo', 'la', 'le', 'di', 'del', 'al', 'da', 'che', 'per', 'con', 'in',
    'non', 'e', 'o', 'a', 'ma', 'se', 'si', 'mi', 'ti', 'ci', 'vi', 'ni',
    'questo', 'quella', 'tutti', 'ogni', 'suo', 'sua', 'poi', 'ora', 'ancora',
    'sempre', 'anche', 'come', 'dove', 'quando', 'molto', 'poco', 'tanto',
    'primo', 'secondo', 'altro', 'cuore', 'testa', 'occhio', 'naso', 'bocca',
    'mano', 'piede', 'acqua', 'olio', 'sale', 'miele', 'vino', 'latte',
    'erba', 'fiore', 'foglia', 'radice', 'pianta', 'seme', 'frutto', 'albero',
    'sole', 'luna', 'stella', 'terra', 'cielo', 'mare', 'fuoco', 'aria',
    'dolore', 'male', 'febbre', 'tosse', 'cura', 'rimedio', 'medicina',
    'rosso', 'nero', 'bianco', 'verde', 'giallo', 'blu', 'grande', 'piccolo'
])

# Hebrew words (for Judeo-Italian hypothesis)
HEBREW_WORDS = set([
    'shem', 'melech', 'adam', 'yom', 'laila', 'aretz', 'shamayim', 'mayim',
    'esh', 'ruach', 'nefesh', 'lev', 'ayin', 'yad', 'regel', 'rosh',
    'ben', 'bat', 'av', 'em', 'ach', 'achot', 'ish', 'isha',
    'tov', 'ra', 'gadol', 'katan', 'chadash', 'yashan', 'chai', 'met',
    'or', 'choshech', 'yareach', 'shemesh', 'kochav', 'etz', 'perach', 'pri'
])


class GlyphMapper:
    """Maps Voynich glyphs to phonemes using evolutionary algorithm."""
    
    def __init__(self, voynich_text):
        self.text = voynich_text
        self.words = voynich_text.split()
        
        # Extract unique glyphs
        all_chars = set()
        for word in self.words:
            for c in word:
                all_chars.add(c)
        self.glyphs = sorted(all_chars)
        
        # Character frequencies
        self.char_freq = Counter(c for w in self.words for c in w)
        
        # Bigram frequencies
        self.bigram_freq = Counter()
        clean = voynich_text.lower().replace('\n', ' ')
        for i in range(len(clean) - 1):
            self.bigram_freq[clean[i:i+2]] += 1
    
    def create_random_mapping(self):
        """Create a random glyph-to-phoneme mapping."""
        mapping = {}
        available_phonemes = ALL_PHONEMES.copy()
        random.shuffle(available_phonemes)
        
        for i, glyph in enumerate(self.glyphs):
            if i < len(available_phonemes):
                mapping[glyph] = available_phonemes[i]
            else:
                mapping[glyph] = random.choice(ALL_PHONEMES)
        
        return mapping
    
    def decode_word(self, word, mapping):
        """Decode a Voynich word using a mapping."""
        result = []
        i = 0
        while i < len(word):
            # Try 2-char phoneme first (ch, gh, etc.)
            if i + 1 < len(word):
                two_char = word[i:i+2]
                if two_char in mapping:
                    result.append(mapping[two_char])
                    i += 2
                    continue
            
            # Single char
            if word[i] in mapping:
                result.append(mapping[word[i]])
            else:
                result.append('?')
            i += 1
        
        return ''.join(result)
    
    def decode_text(self, mapping):
        """Decode entire text using a mapping."""
        return ' '.join(self.decode_word(w, mapping) for w in self.words[:1000])
    
    def fitness(self, mapping):
        """Calculate fitness of a mapping (higher = better)."""
        score = 0
        sample_words = self.words[:500]
        
        decoded_words = []
        for word in sample_words:
            decoded = self.decode_word(word, mapping)
            decoded_words.append(decoded)
        
        # Metric 1: Italian word matches
        italian_matches = sum(1 for w in decoded_words if w in ITALIAN_WORDS)
        score += italian_matches * 10
        
        # Metric 2: Hebrew word matches
        hebrew_matches = sum(1 for w in decoded_words if w in HEBREW_WORDS)
        score += hebrew_matches * 8
        
        # Metric 3: Vowel ratio (natural languages have 35-45% vowels)
        all_decoded = ''.join(decoded_words)
        vowel_count = sum(1 for c in all_decoded if c in VOWELS)
        total_count = len(all_decoded)
        if total_count > 0:
            vowel_ratio = vowel_count / total_count
            # Score closer to 0.4 is better
            score += max(0, 10 - abs(vowel_ratio - 0.4) * 50)
        
        # Metric 4: No triple repeats (e.g., 'aaa' is unnatural)
        triple_repeats = sum(1 for i in range(len(all_decoded)-2) 
                           if all_decoded[i] == all_decoded[i+1] == all_decoded[i+2])
        score -= triple_repeats * 5
        
        # Metric 5: Bigram plausibility
        valid_bigrams = 0
        total_bigrams = 0
        for word in decoded_words:
            for i in range(len(word) - 1):
                bigram = word[i:i+2]
                total_bigrams += 1
                # Check if bigram is plausible in Italian
                if (bigram[0] in VOWELS and bigram[1] in CONSONANTS) or \
                   (bigram[0] in CONSONANTS and bigram[1] in VOWELS) or \
                   (bigram[0] in VOWELS and bigram[1] in VOWELS):
                    valid_bigrams += 1
        
        if total_bigrams > 0:
            bigram_ratio = valid_bigrams / total_bigrams
            score += bigram_ratio * 20
        
        # Metric 6: Word length distribution (Italian avg ~5-6 chars)
        avg_decoded_len = sum(len(w) for w in decoded_words) / len(decoded_words) if decoded_words else 0
        score += max(0, 5 - abs(avg_decoded_len - 5.5))
        
        return score
    
    def evolve(self, population_size=50, generations=1000, cribs=None):
        """Evolve glyph-to-phoneme mapping using genetic algorithm."""
        print(f"Evolving mapping: {len(self.glyphs)} glyphs, {population_size} population, {generations} generations")
        
        # Initialize population
        population = [self.create_random_mapping() for _ in range(population_size)]
        
        # Apply cribs if provided
        if cribs:
            for mapping in population:
                for glyph, phoneme in cribs.items():
                    if glyph in mapping:
                        mapping[glyph] = phoneme
        
        best_mapping = None
        best_fitness = float('-inf')
        fitness_history = []
        
        for gen in range(generations):
            # Evaluate fitness
            scored = [(m, self.fitness(m)) for m in population]
            scored.sort(key=lambda x: x[1], reverse=True)
            
            # Track best
            if scored[0][1] > best_fitness:
                best_fitness = scored[0][1]
                best_mapping = scored[0][0].copy()
            
            fitness_history.append(best_fitness)
            
            # Print progress
            if gen % 100 == 0:
                decoded_sample = self.decode_word(self.words[0], best_mapping) if self.words else ''
                print(f"  Gen {gen}: Best fitness={best_fitness:.1f}, Sample: '{self.words[0]}' → '{decoded_sample}'")
            
            # Selection (top 20%)
            survivors = [m for m, s in scored[:max(2, population_size // 5)]]
            
            # Crossover & Mutation
            new_population = survivors.copy()
            while len(new_population) < population_size:
                parent1 = random.choice(survivors)
                parent2 = random.choice(survivors)
                child = self.crossover(parent1, parent2)
                child = self.mutate(child, rate=0.1)
                
                # Apply cribs
                if cribs:
                    for glyph, phoneme in cribs.items():
                        if glyph in child:
                            child[glyph] = phoneme
                
                new_population.append(child)
            
            population = new_population
        
        return best_mapping, best_fitness, fitness_history
    
    def crossover(self, parent1, parent2):
        """Crossover two mappings."""
        child = {}
        for glyph in self.glyphs:
            if random.random() < 0.5:
                child[glyph] = parent1.get(glyph, random.choice(ALL_PHONEMES))
            else:
                child[glyph] = parent2.get(glyph, random.choice(ALL_PHONEMES))
        return child
    
    def mutate(self, mapping, rate=0.1):
        """Mutate a mapping."""
        mutated = mapping.copy()
        for glyph in self.glyphs:
            if random.random() < rate:
                mutated[glyph] = random.choice(ALL_PHONEMES)
        return mutated


def parse_cribs(crib_string):
    """Parse crib string like 'daiin=dei,ol=il'"""
    cribs = {}
    if crib_string:
        for pair in crib_string.split(','):
            if '=' in pair:
                glyph, phoneme = pair.split('=', 1)
                # Map each character in glyph to corresponding phoneme character
                for g, p in zip(glyph, phoneme):
                    cribs[g] = p
    return cribs


def main():
    parser = argparse.ArgumentParser(description="Evolutionary Glyph-Phoneme Mapper")
    parser.add_argument('--eva', required=True, help='EVA text file')
    parser.add_argument('--generations', type=int, default=1000, help='Number of generations')
    parser.add_argument('--population', type=int, default=50, help='Population size')
    parser.add_argument('--cribs', help='Crib mappings (e.g., "daiin=dei,ol=il")')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    with open(args.eva, 'r', encoding='utf-8') as f:
        text = f.read()
    
    mapper = GlyphMapper(text)
    cribs = parse_cribs(args.cribs)
    
    if cribs:
        print(f"Using cribs: {cribs}")
    
    best_mapping, best_fitness, history = mapper.evolve(
        population_size=args.population,
        generations=args.generations,
        cribs=cribs
    )
    
    print(f"\n{'='*60}")
    print(f"BEST MAPPING (fitness: {best_fitness:.1f})")
    print(f"{'='*60}")
    
    # Sort by frequency
    sorted_mapping = sorted(best_mapping.items(), key=lambda x: -mapper.char_freq.get(x[0], 0))
    for glyph, phoneme in sorted_mapping[:20]:
        freq = mapper.char_freq.get(glyph, 0)
        print(f"  '{glyph}' → '{phoneme}' (freq: {freq})")
    
    print(f"\n{'='*60}")
    print("DECODED SAMPLES")
    print(f"{'='*60}")
    
    for i in range(min(10, len(mapper.words))):
        original = mapper.words[i]
        decoded = mapper.decode_word(original, best_mapping)
        print(f"  {original:15s} → {decoded}")
    
    # Save results
    result = {
        'best_mapping': best_mapping,
        'fitness': best_fitness,
        'fitness_history': history[-100:],
        'decoded_samples': [
            {'original': mapper.words[i], 'decoded': mapper.decode_word(mapper.words[i], best_mapping)}
            for i in range(min(50, len(mapper.words)))
        ]
    }
    
    output = args.output or 'research-output/evolutionary-mapping.json'
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else '.', exist_ok=True)
    with open(output, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n✅ Saved to {output}")


if __name__ == "__main__":
    main()
