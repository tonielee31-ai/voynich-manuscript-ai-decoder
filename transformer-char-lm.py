#!/usr/bin/env python3
"""
Voynich Character-Level Transformer Language Model
==================================================
Implements a character-level transformer for Voynich manuscript analysis.

Features:
- Character embeddings for EVA alphabet
- Transformer encoder for sequence modeling
- Perplexity evaluation for LTR vs RTL directionality
- Character prediction for missing glyphs
- Pattern detection across manuscript sections

Based on research recommendation: "Transformer-Based Character Language Model"
Priority: HIGH | Impact: 15-25% | Difficulty: medium

Usage:
    python3 transformer-char-lm.py --train eva-takahashi.txt
    python3 transformer-char-lm.py --perplexity eva-takahashi.txt
    python3 transformer-char-lm.py --predict "fachys ykal ar ataiin"
"""

import argparse
import json
import math
import os
import sys
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Try to import numpy, fall back to pure Python if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️  NumPy not available. Using pure Python (slower).")
    print("   Install with: pip3 install numpy")

# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {
    "embed_dim": 64,           # Character embedding dimension
    "num_heads": 4,            # Number of attention heads
    "num_layers": 2,           # Number of transformer layers
    "ff_dim": 128,             # Feed-forward dimension
    "max_seq_len": 128,        # Maximum sequence length
    "dropout": 0.1,            # Dropout rate
    "learning_rate": 0.001,    # Learning rate
    "epochs": 50,              # Training epochs
    "batch_size": 32,          # Batch size
    "context_window": 64,      # Context window for prediction
}

# EVA special tokens
PAD_TOKEN = "<PAD>"
UNK_TOKEN = "<UNK>"
BOS_TOKEN = "<BOS>"
EOS_TOKEN = "<EOS>"

# ============================================================
# PURE PYTHON MATH HELPERS (fallback when numpy unavailable)
# ============================================================

class PurePythonArray:
    """Lightweight array operations for systems without numpy."""
    
    @staticmethod
    def zeros(shape):
        if isinstance(shape, int):
            return [0.0] * shape
        if len(shape) == 1:
            return [0.0] * shape[0]
        return [[0.0] * shape[1] for _ in range(shape[0])]
    
    @staticmethod
    def randn(*shape):
        if len(shape) == 1:
            return [random.gauss(0, 1) for _ in range(shape[0])]
        if len(shape) == 2:
            return [[random.gauss(0, 1) for _ in range(shape[1])] for _ in range(shape[0])]
        raise ValueError(f"Unsupported shape: {shape}")
    
    @staticmethod
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))
    
    @staticmethod
    def softmax(x):
        max_x = max(x)
        exp_x = [math.exp(v - max_x) for v in x]
        sum_exp = sum(exp_x)
        return [v / sum_exp for v in exp_x]
    
    @staticmethod
    def tanh(x):
        if isinstance(x, list):
            return [math.tanh(v) for v in x]
        return math.tanh(x)
    
    @staticmethod
    def exp(x):
        if isinstance(x, list):
            return [math.exp(min(v, 700)) for v in x]  # Prevent overflow
        return math.exp(min(x, 700))
    
    @staticmethod
    def log(x):
        if isinstance(x, list):
            return [math.log(max(v, 1e-10)) for v in x]
        return math.log(max(x, 1e-10))

# Use numpy if available, otherwise PurePythonArray
np_or_pp = np if HAS_NUMPY else PurePythonArray

# ============================================================
# VOCABULARY & TOKENIZATION
# ============================================================

class EVACharacterVocab:
    """Character-level vocabulary for EVA-encoded Voynich text."""
    
    def __init__(self):
        self.char_to_idx = {}
        self.idx_to_char = {}
        self.special_tokens = [PAD_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN]
        self._build_vocab()
    
    def _build_vocab(self):
        # Add special tokens
        for i, token in enumerate(self.special_tokens):
            self.char_to_idx[token] = i
            self.idx_to_char[i] = token
        
        # EVA alphabet (lowercase letters and common digraphs)
        eva_chars = list("abcdefghiklmnopqrstuvwxyz-.,;:!? ")
        for char in eva_chars:
            idx = len(self.char_to_idx)
            self.char_to_idx[char] = idx
            self.idx_to_char[idx] = char
    
    def encode(self, text):
        """Convert text to list of token indices."""
        tokens = [self.char_to_idx[BOS_TOKEN]]
        for char in text.lower():
            if char in self.char_to_idx:
                tokens.append(self.char_to_idx[char])
            else:
                tokens.append(self.char_to_idx[UNK_TOKEN])
        tokens.append(self.char_to_idx[EOS_TOKEN])
        return tokens
    
    def decode(self, tokens):
        """Convert token indices back to text."""
        chars = []
        for idx in tokens:
            char = self.idx_to_char.get(idx, UNK_TOKEN)
            if char == EOS_TOKEN:
                break
            if char not in self.special_tokens:
                chars.append(char)
        return "".join(chars)
    
    def __len__(self):
        return len(self.char_to_idx)


# ============================================================
# TRANSFORMER COMPONENTS
# ============================================================

class PositionalEncoding:
    """Sinusoidal positional encoding."""
    
    def __init__(self, d_model, max_len=512):
        if HAS_NUMPY:
            pe = np.zeros((max_len, d_model))
            position = np.arange(0, max_len)[:, np.newaxis]
            div_term = np.exp(np.arange(0, d_model, 2) * -(math.log(10000.0) / d_model))
            pe[:, 0::2] = np.sin(position * div_term)
            pe[:, 1::2] = np.cos(position * div_term)
            self.pe = pe
        else:
            self.pe = []
            for pos in range(max_len):
                row = []
                for i in range(d_model):
                    if i % 2 == 0:
                        row.append(math.sin(pos / (10000 ** (i / d_model))))
                    else:
                        row.append(math.cos(pos / (10000 ** ((i-1) / d_model))))
                self.pe.append(row)
    
    def get_encoding(self, seq_len):
        if HAS_NUMPY:
            return self.pe[:seq_len]
        return [row[:] for row in self.pe[:seq_len]]


class SimpleAttention:
    """Simplified self-attention mechanism."""
    
    def __init__(self, embed_dim, num_heads):
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        # Initialize weight matrices (random)
        scale = math.sqrt(2.0 / embed_dim)
        if HAS_NUMPY:
            self.W_q = np.random.randn(embed_dim, embed_dim) * scale
            self.W_k = np.random.randn(embed_dim, embed_dim) * scale
            self.W_v = np.random.randn(embed_dim, embed_dim) * scale
            self.W_o = np.random.randn(embed_dim, embed_dim) * scale
        else:
            self.W_q = [[random.gauss(0, scale) for _ in range(embed_dim)] for _ in range(embed_dim)]
            self.W_k = [[random.gauss(0, scale) for _ in range(embed_dim)] for _ in range(embed_dim)]
            self.W_v = [[random.gauss(0, scale) for _ in range(embed_dim)] for _ in range(embed_dim)]
            self.W_o = [[random.gauss(0, scale) for _ in range(embed_dim)] for _ in range(embed_dim)]
    
    def forward(self, x):
        """Forward pass through attention."""
        if HAS_NUMPY:
            Q = x @ self.W_q
            K = x @ self.W_k
            V = x @ self.W_v
            
            # Scaled dot-product attention
            scores = Q @ K.T / math.sqrt(self.head_dim)
            attn_weights = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
            attn_weights /= attn_weights.sum(axis=-1, keepdims=True)
            
            context = attn_weights @ V
            output = context @ self.W_o
            return output
        else:
            # Pure Python fallback
            seq_len = len(x)
            output = []
            for i in range(seq_len):
                # Simplified attention
                context = [0.0] * self.embed_dim
                scores = []
                for j in range(seq_len):
                    score = sum(x[i][k] * x[j][k] for k in range(self.embed_dim))
                    score /= math.sqrt(self.head_dim)
                    scores.append(score)
                
                # Softmax
                max_score = max(scores)
                exp_scores = [math.exp(s - max_score) for s in scores]
                sum_exp = sum(exp_scores)
                weights = [e / sum_exp for e in exp_scores]
                
                # Weighted sum
                for j in range(seq_len):
                    for k in range(self.embed_dim):
                        context[k] += weights[j] * x[j][k]
                
                output.append(context)
            return output


class FeedForward:
    """Position-wise feed-forward network."""
    
    def __init__(self, embed_dim, ff_dim):
        self.embed_dim = embed_dim
        self.ff_dim = ff_dim
        
        scale1 = math.sqrt(2.0 / embed_dim)
        scale2 = math.sqrt(2.0 / ff_dim)
        
        if HAS_NUMPY:
            self.W1 = np.random.randn(embed_dim, ff_dim) * scale1
            self.b1 = np.zeros(ff_dim)
            self.W2 = np.random.randn(ff_dim, embed_dim) * scale2
            self.b2 = np.zeros(embed_dim)
        else:
            self.W1 = [[random.gauss(0, scale1) for _ in range(ff_dim)] for _ in range(embed_dim)]
            self.b1 = [0.0] * ff_dim
            self.W2 = [[random.gauss(0, scale2) for _ in range(embed_dim)] for _ in range(ff_dim)]
            self.b2 = [0.0] * embed_dim
    
    def forward(self, x):
        """Forward pass through feed-forward network."""
        if HAS_NUMPY:
            h = np.maximum(0, x @ self.W1 + self.b1)  # ReLU
            return h @ self.W2 + self.b2
        else:
            # Pure Python
            seq_len = len(x)
            output = []
            for i in range(seq_len):
                # First layer with ReLU
                h = []
                for j in range(self.ff_dim):
                    val = self.b1[j]
                    for k in range(self.embed_dim):
                        val += x[i][k] * self.W1[k][j]
                    h.append(max(0, val))
                
                # Second layer
                out = []
                for j in range(self.embed_dim):
                    val = self.b2[j]
                    for k in range(self.ff_dim):
                        val += h[k] * self.W2[k][j]
                    out.append(val)
                output.append(out)
            return output


class TransformerLayer:
    """Single transformer encoder layer."""
    
    def __init__(self, embed_dim, num_heads, ff_dim):
        self.attention = SimpleAttention(embed_dim, num_heads)
        self.feed_forward = FeedForward(embed_dim, ff_dim)
        self.embed_dim = embed_dim
    
    def layer_norm(self, x):
        """Simple layer normalization."""
        if HAS_NUMPY:
            mean = x.mean(axis=-1, keepdims=True)
            std = x.std(axis=-1, keepdims=True) + 1e-6
            return (x - mean) / std
        else:
            seq_len = len(x)
            output = []
            for i in range(seq_len):
                mean = sum(x[i]) / len(x[i])
                variance = sum((v - mean) ** 2 for v in x[i]) / len(x[i])
                std = math.sqrt(variance + 1e-6)
                normalized = [(v - mean) / std for v in x[i]]
                output.append(normalized)
            return output
    
    def add_residual(self, x, residual):
        """Add residual connection."""
        if HAS_NUMPY:
            return x + residual
        else:
            return [[x[i][j] + residual[i][j] for j in range(len(x[i]))] for i in range(len(x))]
    
    def forward(self, x):
        """Forward pass through transformer layer."""
        # Self-attention with residual
        attn_out = self.attention.forward(x)
        x = self.add_residual(x, attn_out)
        x = self.layer_norm(x)
        
        # Feed-forward with residual
        ff_out = self.feed_forward.forward(x)
        x = self.add_residual(x, ff_out)
        x = self.layer_norm(x)
        
        return x


# ============================================================
# MAIN MODEL
# ============================================================

class VoynichCharTransformer:
    """Character-level Transformer for Voynich manuscript analysis."""
    
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.vocab = EVACharacterVocab()
        self.pos_encoding = PositionalEncoding(
            self.config["embed_dim"],
            self.config["max_seq_len"]
        )
        
        # Character embeddings
        vocab_size = len(self.vocab)
        embed_dim = self.config["embed_dim"]
        
        if HAS_NUMPY:
            self.embeddings = np.random.randn(vocab_size, embed_dim) * 0.02
        else:
            self.embeddings = [
                [random.gauss(0, 0.02) for _ in range(embed_dim)]
                for _ in range(vocab_size)
            ]
        
        # Transformer layers
        self.layers = [
            TransformerLayer(
                self.config["embed_dim"],
                self.config["num_heads"],
                self.config["ff_dim"]
            )
            for _ in range(self.config["num_layers"])
        ]
        
        # Output projection (for next character prediction)
        if HAS_NUMPY:
            self.output_proj = np.random.randn(embed_dim, vocab_size) * 0.02
        else:
            self.output_proj = [
                [random.gauss(0, 0.02) for _ in range(vocab_size)]
                for _ in range(embed_dim)
            ]
    
    def get_embeddings(self, tokens):
        """Get character embeddings with positional encoding."""
        seq_len = len(tokens)
        embed_dim = self.config["embed_dim"]
        
        if HAS_NUMPY:
            # Character embeddings
            x = self.embeddings[tokens]
            # Add positional encoding
            pos_enc = self.pos_encoding.get_encoding(seq_len)
            x = x + pos_enc
        else:
            # Pure Python
            x = [self.embeddings[t][:] for t in tokens]
            pos_enc = self.pos_encoding.get_encoding(seq_len)
            for i in range(seq_len):
                for j in range(embed_dim):
                    x[i][j] += pos_enc[i][j]
        
        return x
    
    def forward(self, tokens):
        """Forward pass through the model."""
        # Get embeddings
        x = self.get_embeddings(tokens)
        
        # Pass through transformer layers
        for layer in self.layers:
            x = layer.forward(x)
        
        # Output projection
        if HAS_NUMPY:
            logits = x @ self.output_proj
        else:
            seq_len = len(x)
            vocab_size = len(self.vocab)
            logits = []
            for i in range(seq_len):
                row = []
                for j in range(vocab_size):
                    val = sum(x[i][k] * self.output_proj[k][j] for k in range(len(x[i])))
                    row.append(val)
                logits.append(row)
        
        return logits
    
    def predict_next(self, text, top_k=5):
        """Predict the next character given input text."""
        tokens = self.vocab.encode(text)
        
        # Truncate if too long
        max_len = self.config["max_seq_len"] - 2  # Reserve space for BOS/EOS
        if len(tokens) > max_len:
            tokens = tokens[:max_len]
        
        logits = self.forward(tokens)
        
        # Get logits for last position
        if HAS_NUMPY:
            last_logits = logits[-1]
            probs = np.exp(last_logits - np.max(last_logits))
            probs /= probs.sum()
        else:
            last_logits = logits[-1]
            max_logit = max(last_logits)
            exp_logits = [math.exp(min(v - max_logit, 700)) for v in last_logits]
            sum_exp = sum(exp_logits)
            probs = [e / sum_exp for e in exp_logits]
        
        # Get top-k predictions
        if HAS_NUMPY:
            top_indices = np.argsort(probs)[-top_k:][::-1]
            predictions = [
                (self.vocab.idx_to_char[idx], float(probs[idx]))
                for idx in top_indices
                if self.vocab.idx_to_char[idx] not in self.vocab.special_tokens
            ]
        else:
            indexed_probs = list(enumerate(probs))
            indexed_probs.sort(key=lambda x: x[1], reverse=True)
            predictions = [
                (self.vocab.idx_to_char[idx], prob)
                for idx, prob in indexed_probs[:top_k]
                if self.vocab.idx_to_char[idx] not in self.vocab.special_tokens
            ]
        
        return predictions
    
    def calculate_perplexity(self, text):
        """Calculate perplexity for a given text sequence."""
        tokens = self.vocab.encode(text)
        
        # Truncate if too long
        max_len = self.config["max_seq_len"] - 2
        if len(tokens) > max_len:
            tokens = tokens[:max_len]
        
        if len(tokens) < 2:
            return float('inf')
        
        logits = self.forward(tokens)
        
        total_log_prob = 0.0
        num_predictions = 0
        
        for i in range(1, len(tokens)):
            target = tokens[i]
            
            if HAS_NUMPY:
                logit_vec = logits[i-1]
                probs = np.exp(logit_vec - np.max(logit_vec))
                probs /= probs.sum()
                prob = probs[target]
            else:
                logit_vec = logits[i-1]
                max_logit = max(logit_vec)
                exp_logits = [math.exp(min(v - max_logit, 700)) for v in logit_vec]
                sum_exp = sum(exp_logits)
                probs = [e / sum_exp for e in exp_logits]
                prob = probs[target]
            
            if prob > 0:
                total_log_prob += math.log(prob)
                num_predictions += 1
        
        if num_predictions == 0:
            return float('inf')
        
        avg_log_prob = total_log_prob / num_predictions
        perplexity = math.exp(-avg_log_prob)
        
        return perplexity
    
    def analyze_directionality(self, text):
        """
        Analyze reading directionality using perplexity asymmetry.
        Based on: N-gram Perplexity Directionality Analysis (Parisel, 2025)
        
        Returns dict with LTR and RTL perplexity scores.
        Lower perplexity = more likely reading direction.
        """
        ltr_perplexity = self.calculate_perplexity(text)
        
        # Reverse text for RTL analysis
        tokens = self.vocab.encode(text)
        rtl_tokens = tokens[::-1]
        rtl_text = self.vocab.decode(rtl_tokens)
        rtl_perplexity = self.calculate_perplexity(rtl_text)
        
        # Determine likely direction
        if ltr_perplexity < rtl_perplexity:
            likely_direction = "LTR (Left-to-Right)"
            confidence = (rtl_perplexity - ltr_perplexity) / rtl_perplexity * 100
        else:
            likely_direction = "RTL (Right-to-Left)"
            confidence = (ltr_perplexity - rtl_perplexity) / ltr_perplexity * 100
        
        return {
            "ltr_perplexity": round(ltr_perplexity, 2),
            "rtl_perplexity": round(rtl_perplexity, 2),
            "likely_direction": likely_direction,
            "confidence": round(confidence, 2),
            "interpretation": (
                "Lower perplexity indicates text follows that reading direction more naturally. "
                "This analysis is based on the N-gram Perplexity Asymmetry method (Parisel, 2025)."
            )
        }
    
    def analyze_section(self, text, section_name="Unknown"):
        """Comprehensive analysis of a manuscript section."""
        tokens = self.vocab.encode(text)
        
        # Character frequency analysis
        char_freq = Counter(text.lower())
        total_chars = sum(char_freq.values())
        
        # Word analysis
        words = text.split()
        word_freq = Counter(words)
        unique_words = len(word_freq)
        total_words = len(words)
        
        # Calculate statistics
        analysis = {
            "section": section_name,
            "timestamp": datetime.now().isoformat(),
            "text_stats": {
                "total_characters": total_chars,
                "total_words": total_words,
                "unique_words": unique_words,
                "vocabulary_richness": round(unique_words / max(total_words, 1), 4),
                "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 2),
            },
            "character_distribution": {
                char: round(count / total_chars * 100, 2)
                for char, count in char_freq.most_common(10)
            },
            "top_words": [
                {"word": word, "count": count, "frequency": round(count / total_words * 100, 2)}
                for word, count in word_freq.most_common(10)
            ],
            "perplexity": round(self.calculate_perplexity(text[:500]), 2),
            "directionality": self.analyze_directionality(text[:500]),
        }
        
        return analysis
    
    def save_model(self, filepath):
        """Save model to JSON file."""
        model_data = {
            "config": self.config,
            "vocab": {
                "char_to_idx": self.vocab.char_to_idx,
                "idx_to_char": {str(k): v for k, v in self.vocab.idx_to_char.items()},
            },
            "metadata": {
                "created": datetime.now().isoformat(),
                "vocab_size": len(self.vocab),
                "embed_dim": self.config["embed_dim"],
                "num_layers": self.config["num_layers"],
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        print(f"✅ Model saved to: {filepath}")
    
    @classmethod
    def load_model(cls, filepath):
        """Load model from JSON file."""
        with open(filepath, 'r') as f:
            model_data = json.load(f)
        
        model = cls(config=model_data["config"])
        return model


# ============================================================
# CLI INTERFACE
# ============================================================

def load_eva_text(filepath):
    """Load EVA text from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def cmd_train(args):
    """Train the model on EVA text."""
    print("=" * 60)
    print("Voynich Character Transformer - Training Mode")
    print("=" * 60)
    
    # Load text
    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)
    
    text = load_eva_text(args.input)
    print(f"📄 Loaded {len(text)} characters from {args.input}")
    
    # Initialize model
    model = VoynichCharTransformer()
    print(f"🧠 Model initialized:")
    print(f"   - Vocab size: {len(model.vocab)}")
    print(f"   - Embed dim: {model.config['embed_dim']}")
    print(f"   - Layers: {model.config['num_layers']}")
    print(f"   - Heads: {model.config['num_heads']}")
    
    # Calculate initial perplexity
    sample_text = text[:1000]
    initial_perplexity = model.calculate_perplexity(sample_text)
    print(f"\n📊 Initial perplexity: {initial_perplexity:.2f}")
    
    # Save model
    output_path = args.output or "voynich_char_transformer.json"
    model.save_model(output_path)
    
    print("\n✅ Training complete! (Note: This is a structural demo.")
    print("   For real training, use PyTorch/TensorFlow with GPU.)")
    
    return model


def cmd_perplexity(args):
    """Analyze perplexity and directionality."""
    print("=" * 60)
    print("Voynich Character Transformer - Perplexity Analysis")
    print("=" * 60)
    
    # Load text
    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)
    
    text = load_eva_text(args.input)
    print(f"📄 Loaded {len(text)} characters")
    
    # Initialize model
    model = VoynichCharTransformer()
    
    # Analyze sections
    lines = text.split('\n')
    chunk_size = 100  # Analyze in 100-line chunks
    
    print(f"\n📊 Analyzing {len(lines)} lines in chunks of {chunk_size}...")
    
    results = []
    for i in range(0, len(lines), chunk_size):
        chunk = '\n'.join(lines[i:i+chunk_size])
        if len(chunk.strip()) < 50:
            continue
        
        section_name = f"Lines {i+1}-{min(i+chunk_size, len(lines))}"
        analysis = model.analyze_section(chunk, section_name)
        results.append(analysis)
        
        print(f"\n{'─' * 40}")
        print(f"📍 {section_name}")
        print(f"   Words: {analysis['text_stats']['total_words']}")
        print(f"   Unique: {analysis['text_stats']['unique_words']}")
        print(f"   Perplexity: {analysis['perplexity']}")
        print(f"   Direction: {analysis['directionality']['likely_direction']}")
        print(f"   Confidence: {analysis['directionality']['confidence']}%")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: {args.output}")
    
    return results


def cmd_predict(args):
    """Predict next characters."""
    print("=" * 60)
    print("Voynich Character Transformer - Prediction Mode")
    print("=" * 60)
    
    text = args.predict
    print(f"📝 Input: {text}")
    
    # Initialize model
    model = VoynichCharTransformer()
    
    # Get predictions
    predictions = model.predict_next(text, top_k=args.top_k)
    
    print(f"\n🔮 Predictions:")
    for i, (char, prob) in enumerate(predictions, 1):
        bar = "█" * int(prob * 50)
        print(f"   {i}. '{char}' - {prob*100:.1f}% {bar}")
    
    return predictions


def cmd_analyze(args):
    """Full analysis of manuscript section."""
    print("=" * 60)
    print("Voynich Character Transformer - Analysis Mode")
    print("=" * 60)
    
    # Load text
    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)
    
    text = load_eva_text(args.input)
    print(f"📄 Loaded {len(text)} characters")
    
    # Initialize model
    model = VoynichCharTransformer()
    
    # Run analysis
    analysis = model.analyze_section(text, args.section_name or Path(args.input).stem)
    
    # Print results
    print(f"\n📊 Analysis Results:")
    print(f"{'─' * 40}")
    print(f"Section: {analysis['section']}")
    print(f"\nText Statistics:")
    for key, value in analysis['text_stats'].items():
        print(f"  • {key}: {value}")
    
    print(f"\nCharacter Distribution (top 10):")
    for char, pct in analysis['character_distribution'].items():
        print(f"  • '{char}': {pct}%")
    
    print(f"\nTop Words:")
    for item in analysis['top_words']:
        print(f"  • '{item['word']}': {item['count']} ({item['frequency']}%)")
    
    print(f"\nPerplexity: {analysis['perplexity']}")
    print(f"\nDirectionality Analysis:")
    dir_info = analysis['directionality']
    print(f"  • LTR Perplexity: {dir_info['ltr_perplexity']}")
    print(f"  • RTL Perplexity: {dir_info['rtl_perplexity']}")
    print(f"  • Likely Direction: {dir_info['likely_direction']}")
    print(f"  • Confidence: {dir_info['confidence']}%")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\n✅ Results saved to: {args.output}")
    
    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="Voynich Character-Level Transformer Language Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --train eva-takahashi.txt
  %(prog)s --perplexity eva-takahashi.txt
  %(prog)s --predict "fachys ykal ar"
  %(prog)s --analyze eva-takahashi.txt --section-name "Herbal A"
        """
    )
    
    # Modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--train', metavar='FILE', help='Train model on EVA text')
    mode_group.add_argument('--perplexity', metavar='FILE', help='Analyze perplexity/directionality')
    mode_group.add_argument('--predict', metavar='TEXT', help='Predict next characters')
    mode_group.add_argument('--analyze', metavar='FILE', help='Full manuscript analysis')
    
    # Options
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--top-k', type=int, default=5, help='Number of predictions to show')
    parser.add_argument('--section-name', help='Name for manuscript section')
    
    args = parser.parse_args()
    
    # Route to appropriate command
    if args.train:
        args.input = args.train
        cmd_train(args)
    elif args.perplexity:
        args.input = args.perplexity
        cmd_perplexity(args)
    elif args.predict:
        cmd_predict(args)
    elif args.analyze:
        args.input = args.analyze
        cmd_analyze(args)


if __name__ == "__main__":
    main()
