#!/usr/bin/env python3
"""
Voynich Hidden Markov Model Analysis
======================================
Following Gemini's recommendation:
- Use hmmlearn or scikit-learn (not hand-written math)
- Analyze Voynichese structure for hidden states
- Detect vowel/consonant patterns, word boundaries, prefixes

The HMM tries to discover "hidden states" in the character sequence:
- State A might represent "vowel positions"
- State B might represent "consonant positions"
- Transitions reveal the underlying phonological structure

Usage:
    python3 hmm-analyzer.py --eva eva-takahashi.txt
    python3 hmm-analyzer.py --eva eva-takahashi.txt --states 3
"""

import json
import os
import sys
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_DIR = "/Users/zensis/Documents/tonielee31/voynich-manuscript-ai-decoder"
EVA_FILE = os.path.join(PROJECT_DIR, "eva-takahashi.txt")
STATE_FILE = os.path.join(PROJECT_DIR, "voynich_state.json")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "research-output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Try to import HMM libraries
try:
    import numpy as np
    from hmmlearn import hmm
    HAS_HMMLEARN = True
    print("✅ hmmlearn available")
except ImportError:
    HAS_HMMLEARN = False
    print("⚠️  hmmlearn not available. Using pure Python implementation.")
    print("   Install with: pip3 install hmmlearn numpy")

try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ============================================================
# PURE PYTHON HMM (fallback when hmmlearn not available)
# ============================================================

class SimpleHMM:
    """Simple HMM implementation using pure Python."""
    
    def __init__(self, n_states=2):
        self.n_states = n_states
        self.transition_matrix = None
        self.emission_matrix = None
        self.initial_probs = None
        self.states = [f"state_{i}" for i in range(n_states)]
    
    def fit(self, sequences, n_iter=50):
        """Train HMM using Baum-Welch (simplified)."""
        # Get unique observations
        all_obs = sorted(set(obs for seq in sequences for obs in seq))
        n_obs = len(all_obs)
        obs_to_idx = {o: i for i, o in enumerate(all_obs)}
        
        # Initialize matrices randomly but evenly
        self.transition_matrix = [
            [1.0/self.n_states] * self.n_states for _ in range(self.n_states)
        ]
        self.emission_matrix = [
            [1.0/n_obs] * n_obs for _ in range(self.n_states)
        ]
        self.initial_probs = [1.0/self.n_states] * self.n_states
        
        # Simple EM iterations
        for iteration in range(n_iter):
            # E-step: compute state probabilities (simplified)
            # M-step: update matrices based on counts
            
            state_counts = [[0] * n_obs for _ in range(self.n_states)]
            transition_counts = [[0] * self.n_states for _ in range(self.n_states)]
            
            for seq in sequences:
                if len(seq) < 2:
                    continue
                
                # Assign observations to states based on current emission probs
                for i, obs in enumerate(seq):
                    obs_idx = obs_to_idx.get(obs, 0)
                    # Simple assignment: most likely state
                    best_state = 0
                    best_prob = 0
                    for s in range(self.n_states):
                        prob = self.emission_matrix[s][obs_idx]
                        if prob > best_prob:
                            best_prob = prob
                            best_state = s
                    state_counts[best_state][obs_idx] += 1
                    
                    # Count transitions
                    if i > 0:
                        prev_obs_idx = obs_to_idx.get(seq[i-1], 0)
                        prev_state = 0
                        prev_best = 0
                        for s in range(self.n_states):
                            if self.emission_matrix[s][prev_obs_idx] > prev_best:
                                prev_best = self.emission_matrix[s][prev_obs_idx]
                                prev_state = s
                        transition_counts[prev_state][best_state] += 1
            
            # Update emission matrix
            for s in range(self.n_states):
                total = sum(state_counts[s])
                if total > 0:
                    self.emission_matrix[s] = [c/total for c in state_counts[s]]
            
            # Update transition matrix
            for s in range(self.n_states):
                total = sum(transition_counts[s])
                if total > 0:
                    self.transition_matrix[s] = [c/total for c in transition_counts[s]]
        
        self.observations = all_obs
        return self
    
    def predict_states(self, sequence):
        """Predict hidden states for a sequence using Viterbi (simplified)."""
        if not self.emission_matrix:
            return []
        
        states = []
        for obs in sequence:
            obs_idx = self.observations.index(obs) if obs in self.observations else 0
            best_state = 0
            best_prob = 0
            for s in range(self.n_states):
                prob = self.emission_matrix[s][obs_idx]
                if prob > best_prob:
                    best_prob = prob
                    best_state = s
            states.append(best_state)
        
        return states
    
    def get_state_profiles(self):
        """Get emission profiles for each state."""
        profiles = {}
        for s in range(self.n_states):
            profile = {}
            for i, obs in enumerate(self.observations):
                profile[obs] = round(self.emission_matrix[s][i], 4)
            # Sort by probability
            sorted_profile = sorted(profile.items(), key=lambda x: -x[1])
            profiles[f"state_{s}"] = sorted_profile[:10]
        return profiles


class HMMAnalyzer:
    """HMM analysis for Voynich manuscript."""
    
    def __init__(self, text):
        self.text = text
        self.lines = [l.strip() for l in text.split('\n') if l.strip()]
        self.words = text.split()
        
        # Character sequences
        self.char_sequences = []
        for word in self.words[:2000]:  # Use first 2000 words
            clean = ''.join(c for c in word if c.isalpha())
            if len(clean) >= 3:
                self.char_sequences.append(list(clean))
    
    def analyze_with_hmmlearn(self, n_states=2):
        """Analyze using hmmlearn library."""
        if not HAS_HMMLEARN:
            return self.analyze_with_simple_hmm(n_states)
        
        # Prepare data
        all_chars = sorted(set(c for seq in self.char_sequences for c in seq))
        char_to_idx = {c: i for i, c in enumerate(all_chars)}
        
        # Convert sequences to indices
        X = []
        lengths = []
        for seq in self.char_sequences:
            indices = [char_to_idx[c] for c in seq]
            X.extend(indices)
            lengths.append(len(indices))
        
        X = np.array(X).reshape(-1, 1)
        
        # Train HMM
        model = hmm.CategoricalHMM(n_components=n_states, n_iter=100, random_state=42)
        model.fit(X, lengths)
        
        # Get state profiles
        emission_probs = model.emissionprob_
        state_profiles = {}
        for s in range(n_states):
            profile = {}
            for i, char in enumerate(all_chars):
                profile[char] = round(emission_probs[s, i], 4)
            sorted_profile = sorted(profile.items(), key=lambda x: -x[1])
            state_profiles[f"state_{s}"] = sorted_profile[:10]
        
        # Get transition matrix
        trans_matrix = model.transmat_.tolist()
        
        # Predict states for sample words
        sample_predictions = []
        for word in self.words[:20]:
            clean = ''.join(c for c in word if c.isalpha())
            if clean:
                indices = [char_to_idx.get(c, 0) for c in clean]
                X_sample = np.array(indices).reshape(-1, 1)
                states = model.predict(X_sample)
                sample_predictions.append({
                    'word': clean,
                    'states': states.tolist(),
                    'state_sequence': ''.join(['V' if s == 0 else 'C' for s in states])
                })
        
        return {
            'method': 'hmmlearn',
            'n_states': n_states,
            'state_profiles': state_profiles,
            'transition_matrix': [[round(x, 3) for x in row] for row in trans_matrix],
            'sample_predictions': sample_predictions,
            'log_likelihood': round(model.score(X, lengths), 2)
        }
    
    def analyze_with_simple_hmm(self, n_states=2):
        """Analyze using pure Python HMM."""
        model = SimpleHMM(n_states=n_states)
        model.fit(self.char_sequences, n_iter=30)
        
        # Get state profiles
        state_profiles = model.get_state_profiles()
        
        # Predict states for sample words
        sample_predictions = []
        for word in self.words[:20]:
            clean = ''.join(c for c in word if c.isalpha())
            if clean:
                states = model.predict_states(list(clean))
                sample_predictions.append({
                    'word': clean,
                    'states': states,
                    'state_sequence': ''.join(['V' if s == 0 else 'C' for s in states])
                })
        
        return {
            'method': 'simple_python',
            'n_states': n_states,
            'state_profiles': state_profiles,
            'transition_matrix': model.transition_matrix,
            'sample_predictions': sample_predictions
        }
    
    def detect_vowel_patterns(self, state_profiles):
        """Interpret HMM states as vowel/consonant patterns."""
        interpretations = {}
        
        for state_name, profile in state_profiles.items():
            top_chars = [char for char, prob in profile[:5]]
            
            # Check if state looks like vowels
            # Vowels tend to appear in middle of words and have high frequency
            middle_chars = set()
            for word in self.words[:500]:
                if len(word) >= 3:
                    for c in word[1:-1]:
                        middle_chars.add(c)
            
            middle_ratio = sum(1 for c in top_chars if c in middle_chars) / len(top_chars) if top_chars else 0
            
            if middle_ratio > 0.6:
                interpretations[state_name] = {
                    'type': 'LIKELY_VOWELS',
                    'top_chars': top_chars,
                    'middle_ratio': round(middle_ratio, 2),
                    'reasoning': 'Characters appear frequently in word middles'
                }
            else:
                interpretations[state_name] = {
                    'type': 'LIKELY_CONSONANTS',
                    'top_chars': top_chars,
                    'middle_ratio': round(middle_ratio, 2),
                    'reasoning': 'Characters appear more at word edges'
                }
        
        return interpretations
    
    def analyze_prefix_patterns(self):
        """Analyze word-initial patterns (prefix detection)."""
        prefixes = Counter()
        for word in self.words:
            if len(word) >= 2:
                prefixes[word[:2]] += 1
            if len(word) >= 3:
                prefixes[word[:3]] += 1
        
        # Find prefixes that appear significantly more than expected
        total_words = len(self.words)
        significant_prefixes = []
        
        for prefix, count in prefixes.most_common(20):
            if count >= 10:
                # Expected frequency if random
                expected = total_words / (27 ** len(prefix))
                enrichment = count / expected if expected > 0 else 0
                
                significant_prefixes.append({
                    'prefix': prefix,
                    'count': count,
                    'expected': round(expected, 1),
                    'enrichment': round(enrichment, 1)
                })
        
        return significant_prefixes
    
    def analyze_suffix_patterns(self):
        """Analyze word-final patterns (suffix detection)."""
        suffixes = Counter()
        for word in self.words:
            if len(word) >= 2:
                suffixes[word[-2:]] += 1
            if len(word) >= 3:
                suffixes[word[-3:]] += 1
        
        total_words = len(self.words)
        significant_suffixes = []
        
        for suffix, count in suffixes.most_common(20):
            if count >= 10:
                expected = total_words / (27 ** len(suffix))
                enrichment = count / expected if expected > 0 else 0
                
                significant_suffixes.append({
                    'suffix': suffix,
                    'count': count,
                    'expected': round(expected, 1),
                    'enrichment': round(enrichment, 1)
                })
        
        return significant_suffixes
    
    def full_analysis(self, n_states=2):
        """Run complete HMM analysis."""
        print(f"Running HMM analysis with {n_states} states...")
        
        # HMM analysis
        if HAS_HMMLEARN:
            hmm_result = self.analyze_with_hmmlearn(n_states)
        else:
            hmm_result = self.analyze_with_simple_hmm(n_states)
        
        # Interpret states
        interpretations = self.detect_vowel_patterns(hmm_result['state_profiles'])
        
        # Prefix/suffix analysis
        prefixes = self.analyze_prefix_patterns()
        suffixes = self.analyze_suffix_patterns()
        
        results = {
            'hmm_analysis': hmm_result,
            'state_interpretations': interpretations,
            'prefix_patterns': prefixes,
            'suffix_patterns': suffixes,
            'summary': {}
        }
        
        # Summary
        results['summary'] = {
            'method': hmm_result['method'],
            'n_states': n_states,
            'vowel_candidates': [
                interp['top_chars'][:3]
                for state, interp in interpretations.items()
                if interp['type'] == 'LIKELY_VOWELS'
            ],
            'top_prefixes': [p['prefix'] for p in prefixes[:5]],
            'top_suffixes': [s['suffix'] for s in suffixes[:5]],
            'prefix_enrichment': round(
                sum(p['enrichment'] for p in prefixes[:5]) / 5, 1
            ) if prefixes else 0
        }
        
        return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 hmm-analyzer.py <eva_file> [--states N]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    n_states = 2
    if '--states' in sys.argv:
        idx = sys.argv.index('--states')
        if idx + 1 < len(sys.argv):
            n_states = int(sys.argv[idx + 1])
    
    with open(filepath, 'r') as f:
        text = f.read()
    
    analyzer = HMMAnalyzer(text)
    results = analyzer.full_analysis(n_states)
    
    # Print results
    print("\n" + "=" * 60)
    print("HIDDEN MARKOV MODEL ANALYSIS")
    print("=" * 60)
    
    print(f"\n📊 HMM Configuration")
    print(f"   Method: {results['hmm_analysis']['method']}")
    print(f"   States: {n_states}")
    if 'log_likelihood' in results['hmm_analysis']:
        print(f"   Log-likelihood: {results['hmm_analysis']['log_likelihood']}")
    
    print(f"\n📊 State Profiles (Top characters per state)")
    for state, profile in results['hmm_analysis']['state_profiles'].items():
        chars = [(c, p) for c, p in profile[:5]]
        print(f"   {state}: {chars}")
    
    print(f"\n📊 State Interpretations")
    for state, interp in results['state_interpretations'].items():
        print(f"   {state}: {interp['type']}")
        print(f"      Top chars: {interp['top_chars']}")
        print(f"      Reasoning: {interp['reasoning']}")
    
    print(f"\n📊 Transition Matrix")
    for i, row in enumerate(results['hmm_analysis']['transition_matrix']):
        print(f"   State {i} → {[round(x, 2) for x in row]}")
    
    print(f"\n📊 Sample Word Predictions")
    for pred in results['hmm_analysis']['sample_predictions'][:10]:
        print(f"   {pred['word']:12s} → {pred['state_sequence']}")
    
    print(f"\n📊 Prefix Patterns (word beginnings)")
    for p in results['prefix_patterns'][:5]:
        print(f"   '{p['prefix']}' appears {p['count']}x (enrichment: {p['enrichment']}x)")
    
    print(f"\n📊 Suffix Patterns (word endings)")
    for s in results['suffix_patterns'][:5]:
        print(f"   '{s['suffix']}' appears {s['count']}x (enrichment: {s['enrichment']}x)")
    
    print(f"\n{'='*60}")
    print("KEY FINDINGS")
    print(f"{'='*60}")
    
    summary = results['summary']
    print(f"  Vowel candidates: {summary['vowel_candidates']}")
    print(f"  Top prefixes: {summary['top_prefixes']}")
    print(f"  Top suffixes: {summary['top_suffixes']}")
    print(f"  Prefix enrichment: {summary['prefix_enrichment']}x average")
    
    # Save
    output = os.path.join(OUTPUT_DIR, 'hmm-analysis.json')
    with open(output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Saved to {output}")
    
    # Update state file
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        state['last_run_findings'] = f"HMM analysis: {summary['vowel_candidates']} identified as vowel candidates"
        state['hmm_completed'] = True
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"✅ State file updated")


if __name__ == "__main__":
    main()
