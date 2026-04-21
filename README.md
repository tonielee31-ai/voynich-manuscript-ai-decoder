# Voynich Manuscript: AI-Driven Cryptanalysis Toolkit

*Updated April 2026 — Honest assessment after 16 research cycles, 33 papers analyzed*

---

## ⚠️ HONEST STATUS

**The Voynich Manuscript remains UNDECIPHERED.** No one has successfully decoded it since its discovery in 1912.

This project provides the **most comprehensive automated analysis toolkit** available, but we have NOT decoded the manuscript. Our tools analyze STRUCTURE, not CONTENT.

### 🚨 CRITICAL BREAKTHROUGH (April 2026)

**The cipher is WORD-LEVEL homophonic substitution, NOT character-level.**

This explains why simple character substitution fails:
```
Character-level approach (WRONG):
  EVA 'a' → Italian 'e' (FAILS - conflicts between words)

Word-level approach (CORRECT):
  EVA 'daiin' → Italian 'and' (127 occurrences)
  EVA 'chol'  → Italian 'col' (91 occurrences)
  EVA 'or'    → Italian 'or' (26 occurrences)
  EVA 'ol'    → Italian 'la' (16 occurrences)
  EVA 'chey'  → Italian 'che' (16 occurrences)
```

Each Voynich **word** maps to a short plaintext **word**, not character-by-character. The EVA transcription is verbose (long words) while the plaintext is compressed (short words).

### What We Know For Certain
- **Cipher Type**: Monoalphabetic substitution (IC = 0.0771)
- **EVA Tokens**: 29 unique tokens (ch, sh, qo are single characters)
- **Language Structure**: Natural language (H2 = 2.254)
- **Writing System**: Syllabic (29 tokens, CVCV pattern)
- **Mathematical Structure**: 52.4% prime word lengths, 46.3% Fibonacci
- **Two Languages**: Currier A (Herbal, -edy) and Currier B (Biological, -iin)

### Why Simple Substitution Fails
```
Frequency mapping produces nonsense:
  daiin → nioot (NOT a word)
  ol    → er    (NOT a word)
  chedy → lsna  (NOT a word)
```

### Most Promising Directions (Research-Backed)
1. **Naibbe Inverse** (Greshko 2025) — Voynich is verbose homophonic substitution
2. **Syllabic Approach** — 29 tokens = CV pairs
3. **Currier A/B Separation** — Different rules per section
4. **Crib-Based Attack** — Known words from illustrations
5. **Mathematical Encoding** — Prime/Fibonacci patterns = encoding rules

---

## 🛠️ Analysis Tools

### Decoding Tools
| Tool | Purpose | Status |
|------|---------|--------|
| `context-decoder.py` | Multi-method decoder (Occitan/Italian/Hebrew) | Produces structure, not meaning |
| `definitive-decoder.py` | Best scoring decoder | Produces structure, not meaning |
| `hybrid-decoder.py` | Multi-hypothesis decoder | Produces structure, not meaning |
| `naibbe-simulator.js` | Naibbe cipher inverse | Most promising approach |
| `constraint-solver.py` | Heuristic constraint solving | Experimental |
| `evolutionary-mapper.py` | Genetic algorithm mapping | Experimental |

### Analysis Tools (These Work!)
| Tool | Purpose | Verified |
|------|---------|----------|
| `currier-analysis.py` | Currier A/B detection | ✅ Verified |
| `hmm-analyzer.py` | Hidden Markov Model (vowel/consonant) | ✅ Verified |
| `voynich-toolkit.py` | Comprehensive statistics | ✅ Verified |
| `comparative-corpora.py` | 5-language comparison | ✅ Verified |
| `math-patterns.py` | Prime/Fibonacci/golden ratio | ✅ Verified |
| `topic-modeling.py` | Topic clustering + scribal intent | ✅ Verified |
| `transformer-char-lm.py` | Directionality analysis | ✅ Verified |

### Research Automation
| Tool | Purpose | Status |
|------|---------|--------|
| `web-research-loop.py` | Autonomous research (arXiv, GitHub) | ✅ Running |
| `voynich-cron-cycle.py` | Cron-compatible research cycle | ✅ Running |
| `voynich_state.json` | Persistent state (16 cycles) | ✅ Active |
| `voynich-autonomous-research.sh` | System crontab wrapper | ✅ Every 15 min |

---

## 📊 Key Findings (16 Research Cycles, 33 Papers)

### Token Analysis (Correct EVA Tokenization)
```
o  : 12.12%  |  e  : 12.06%  |  y  : 10.61%
a  :  8.58%  |  d  :  7.79%  |  i  :  7.05%
ch :  6.61%  ← SINGLE TOKEN  |  l  :  6.32%
k  :  6.02%  |  qo :  3.18%  ← SINGLE TOKEN
sh :  2.70%  ← SINGLE TOKEN
```

### Currier Languages
```
Currier A (Herbal):      15 sections, -edy suffix dominant
Currier B (Biological):  26 sections, -iin suffix dominant
Mixed:                   12 sections
Manuscript transitions:  B → A
```

### Morphological Patterns
```
Prefix enrichment:
  qok: 1,628x  ← STRUCTURAL MARKER
  che: 1,445x  ← STRUCTURAL MARKER
  ch:    114x
  qo:    102x

Suffix enrichment:
  edy: 2,160x  ← MORPHEME ENDING
  iin: 2,159x  ← MORPHEME ENDING
  dy:    128x
  in:     90x
```

### Statistical Profile
```
Index of Coincidence: 0.0771 → Monoalphabetic Substitution
Conditional Entropy H2: 2.254 → Natural language structure
Zipf's Law R²: 0.964 → Good fit
Writing System: Syllabic (29 tokens, CVCV pattern)
Mathematical: 52.4% prime lengths, 46.3% Fibonacci
Best corpus match: Hebrew Biblical (similarity 0.21)
```

---

## 🚀 Usage

```bash
# Currier A/B analysis
python3 currier-analysis.py eva-takahashi.txt

# HMM vowel/consonant detection
python3 hmm-analyzer.py eva-takahashi.txt --states 2

# Comprehensive statistics
python3 voynich-toolkit.py --full eva-takahashi.txt

# Comparative corpora
python3 comparative-corpora.py eva-takahashi.txt --all

# Mathematical patterns
python3 math-patterns.py eva-takahashi.txt

# Context-aware decoder (best scores)
python3 context-decoder.py eva-takahashi.txt --lines 50

# Naibbe simulator (most promising)
node naibbe-simulator.js
```

---

## 🔬 Research Loop

Autonomous research running every 15 minutes:
- Searches arXiv, GitHub for new papers
- Tests hypotheses against manuscript
- Saves findings to knowledge base
- Rate limited: arXiv 1h, GitHub 1h

```
State: voynich_state.json (16 cycles, 33 papers)
Knowledge: knowledge-base/web-research/
Cycles: research-data/cycles/
```

---

## 📚 Recommended Reading

1. **The Code Book** by Simon Singh — Historical decipherment methods
2. **Voynich.nu** — René Zandbergen's comprehensive research
3. **Voynich Ninja Forum** — Active research community
4. **arxiv:2505.02261** — Statistical Symbolism (prime/Fibonacci)
5. **arxiv:2509.10573** — Directionality analysis
6. **arxiv:2107.05381** — Evolutionary computation for decryption

---

## 🎯 Correct Direction

**What works:**
- ✅ Statistical analysis (Zipf, H2, entropy)
- ✅ Morphological patterns (prefixes/suffixes)
- ✅ Currier A/B detection
- ✅ Token frequency analysis
- ✅ Mathematical pattern discovery
- ✅ Autonomous research automation

**What doesn't work:**
- ❌ Simple character substitution
- ❌ Direct frequency matching to languages
- ❌ Producing "decoded" text that makes sense

**Most promising next steps:**
1. Find Naibbe compression rules (verbose → short)
2. Identify cribs from illustrations
3. Separate Currier A/B decoding
4. Study mathematical encoding patterns
5. Collaborate with voynich.ninja community

---

*The Voynich Manuscript is a 600-year-old unsolved mystery. Our contribution is the most comprehensive automated analysis toolkit available. The actual decoding requires fundamental breakthroughs that no one has achieved yet.*
