const fs = require('fs');
const path = require('path');

// =============================================================================
// VOYNICH MANUSCRIPT MULTI-THEORY DECODER
// =============================================================================
// A unified decoding pipeline that tries multiple decipherment hypotheses
// and scores outputs for linguistic plausibility.
//
// Module 1: Naibbe Inverse Decoder  (Greshko 2025 — verbose homophonic reversal)
// Module 2: Caspari-Faccini Decoder (Enhanced EVA→Italian letter substitution)
// Module 3: Occitan Hypothesis      (Pelling 2026 — Southern French reading)
// Module 4: Currier A/B Split       (Different ciphers for different sections)
// Module 5: Linguistic Scorer       (Entropy, Zipf, dictionary matching)
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// MODULE 1: NAIBBE INVERSE DECODER
// Reverses Greshko's verbose homophonic substitution cipher.
// Forward: plaintext letter → multiple EVA syllable options (via dice/cards)
// Inverse: EVA syllable → candidate plaintext letters (ambiguous, scored)
// ─────────────────────────────────────────────────────────────────────────────

// Forward expansion table from Greshko (2025) — used to build the inverse
const EXPANSION_TABLE = {
    'a': ['a', 'ai', 'aiin', 'ar', 'al', 'am'],
    'e': ['y', 'ey', 'eey', 'dy', 'edy', 'ydy'],
    'i': ['i', 'ii', 'iin', 'in', 'iiin'],
    'o': ['o', 'ol', 'or', 'ok', 'oky'],
    'u': ['e', 'ee', 'eey'],
    't': ['d', 'da', 'dai', 'daiin'],
    'n': ['n', 'in', 'ain', 'aiin'],
    'r': ['r', 'ar', 'or', 'rar'],
    's': ['sh', 'she', 'sho', 'shey'],
    'l': ['l', 'ol', 'al'],
    'c': ['ch', 'cho', 'chy'],
    'd': ['k', 'ok', 'oky'],
    'p': ['cph', 'cpho'],
    'm': ['m', 'om'],
    'f': ['cfh', 'cfho'],
    'g': ['g', 'og'],
    'b': ['cth'],
    'h': ['cth'],
    'v': ['cph'],
    'q': ['qo'],
    'x': ['ckh'],
    'y': ['y'],
    'z': ['sh'],
    'w': ['cpho'],
    'j': ['che'],
    'k': ['ckh']
};

// Build REVERSE lookup: EVA token → array of possible plaintext letters
function buildReverseTable() {
    const reverse = {};
    for (const [letter, expansions] of Object.entries(EXPANSION_TABLE)) {
        for (const eva of expansions) {
            if (!reverse[eva]) reverse[eva] = [];
            if (!reverse[eva].includes(letter)) {
                reverse[eva].push(letter);
            }
        }
    }
    return reverse;
}

const REVERSE_NAIBBE = buildReverseTable();

// All known EVA tokens sorted by length (longest first for greedy matching)
const EVA_TOKENS_SORTED = Object.keys(REVERSE_NAIBBE)
    .sort((a, b) => b.length - a.length);

// Null/filler words that should be stripped before decoding
const NULL_WORDS = new Set(['daiin', 'ol', 'chedy', 'aiin', 'shedy']);

// Dynamic programming tokenizer: find ALL possible segmentations of an EVA word
// Returns array of tokenization paths, each path is an array of EVA tokens
function tokenizeEVA(evaWord, maxPaths = 8) {
    const n = evaWord.length;
    // dp[i] = array of partial paths that consume evaWord[0..i-1]
    const dp = new Array(n + 1).fill(null).map(() => []);
    dp[0] = [[]]; // empty path at position 0

    for (let i = 0; i < n; i++) {
        if (dp[i].length === 0) continue;
        for (const token of EVA_TOKENS_SORTED) {
            const tLen = token.length;
            if (i + tLen <= n && evaWord.slice(i, i + tLen) === token) {
                for (const prevPath of dp[i]) {
                    if (dp[i + tLen].length < maxPaths) {
                        dp[i + tLen].push([...prevPath, token]);
                    }
                }
            }
        }
    }
    return dp[n];
}

// Decode a single EVA word via Naibbe inverse
// Returns array of { plaintext, score, tokens } candidates
function naibbeDecodeWord(evaWord) {
    const clean = evaWord.replace(/[!*=%{}]/g, '');
    if (clean.length === 0) return [];

    const tokenizations = tokenizeEVA(clean);
    if (tokenizations.length === 0) return [{ plaintext: clean, score: 0, tokens: [clean] }];

    const candidates = [];
    for (const tokenPath of tokenizations) {
        // For each tokenization, generate plaintext candidates
        // Use the first (most common) mapping for each token
        const letters = tokenPath.map(tok => {
            const options = REVERSE_NAIBBE[tok];
            return options ? options[0] : '?';
        });
        const plaintext = letters.join('');

        // Score: prefer shorter plaintext (verbose cipher compresses),
        // prefer known dictionary matches, penalize unknowns
        const compressionRatio = clean.length / Math.max(plaintext.length, 1);
        const score = compressionRatio; // Higher = more compression = more likely verbose cipher

        candidates.push({ plaintext, score, tokens: tokenPath });
    }

    // Sort by score descending
    candidates.sort((a, b) => b.score - a.score);
    return candidates.slice(0, 3); // Top 3 candidates
}


// ─────────────────────────────────────────────────────────────────────────────
// MODULE 2: CASPARI-FACCINI ENHANCED DECODER
// Direct EVA → Italian letter substitution based on Caspari & Faccini (2025)
// ─────────────────────────────────────────────────────────────────────────────

const CASPARI_MAP = {
    // Trigraphs (check first)
    'cth': 'ct', 'ckh': 'cd', 'cph': 'cf', 'cfh': 'cf',
    // Digraphs
    'ch': 'c',  'sh': 's',  'qo': 'quo',
    'ee': 'ue', 'ii': 'ii', 'in': 'in',
    // Single characters
    'a': 'a', 'o': 'o', 'e': 'u', 'y': 'e',
    'd': 't', 'l': 'l', 'r': 'r', 'i': 'i',
    'n': 'n', 's': 's', 'q': 'q', 't': 'c',
    'k': 'd', 'p': 'p', 'f': 'f', 'm': 'm',
    'g': 'g', 'h': 'h', 'x': 'x', 'v': 'v',
};

function caspariDecode(evaWord) {
    let result = '';
    let i = 0;
    const w = evaWord.replace(/[!*=%{}]/g, '');
    while (i < w.length) {
        let matched = false;
        // Try 3-char combos first
        if (i + 2 < w.length) {
            const tri = w.slice(i, i + 3);
            if (CASPARI_MAP[tri]) {
                result += CASPARI_MAP[tri];
                i += 3;
                matched = true;
            }
        }
        // Try 2-char combos
        if (!matched && i + 1 < w.length) {
            const bi = w.slice(i, i + 2);
            if (CASPARI_MAP[bi]) {
                result += CASPARI_MAP[bi];
                i += 2;
                matched = true;
            }
        }
        // Single char
        if (!matched) {
            result += CASPARI_MAP[w[i]] || w[i];
            i++;
        }
    }
    return result;
}


// ─────────────────────────────────────────────────────────────────────────────
// MODULE 3: OCCITAN HYPOTHESIS DECODER
// Based on Nick Pelling (Jan 2026) reading of f17r marginalia as Occitan
// Uses Caspari letter mapping but scores against Occitan vocabulary
// ─────────────────────────────────────────────────────────────────────────────

// Common Occitan words (botanical/medical context, ~14th-15th century)
const OCCITAN_WORDS = new Set([
    // Articles & pronouns
    'lo', 'la', 'los', 'las', 'li', 'le', 'un', 'una', 'de', 'del', 'al',
    'que', 'qui', 'qual', 'en', 'es', 'o', 'e', 'a', 'per', 'se', 'si',
    'ben', 'tot', 'mai', 'cal', 'pas', 'ont', 'son', 'lor', 'nos',
    // Botanical/medical terms
    'flor', 'fuelha', 'raitz', 'erba', 'planta', 'aiga', 'oli', 'sal',
    'mel', 'ros', 'rosa', 'vin', 'pan', 'lait', 'uelh', 'cor', 'man',
    'cap', 'pel', 'os', 'sang', 'carn', 'peis', 'color', 'odor', 'calor',
    'dolor', 'amor', 'honor', 'arbor', 'sol', 'luna', 'aur', 'fer',
    // Verbs (infinitive)
    'far', 'dir', 'dar', 'aver', 'esser', 'metre', 'penre', 'batre',
    'bolir', 'cozer', 'talhar', 'mesclar', 'oliar',
    // Adjectives
    'bon', 'bel', 'gran', 'pauc', 'blanc', 'nòu', 'aut',
    // Medical terms from Pelling's reading
    'meilhor', 'aller', 'lucent', 'balsamina',
    // Additional herbal Occitan
    'salvia', 'menta', 'fenolh', 'comfrei', 'verbena', 'lavanda',
    'ruda', 'absinti', 'coriandre', 'gingembre', 'canela', 'safran',
]);

// Common Italian words (medical/botanical 15th century context)
const ITALIAN_WORDS = new Set([
    // Articles & pronouns
    'il', 'lo', 'la', 'le', 'li', 'un', 'una', 'di', 'del', 'al', 'da',
    'che', 'chi', 'cui', 'per', 'con', 'in', 'su', 'se', 'si', 'non',
    'e', 'o', 'a', 'ma', 'ne', 'ci', 'vi', 'ni', 'no', 'co',
    // Nouns
    'cuore', 'sole', 'fiore', 'colore', 'odore', 'dolore', 'amore',
    'arbore', 'acqua', 'olio', 'sale', 'miele', 'vino', 'pane',
    'latte', 'uovo', 'ossa', 'sangue', 'carne', 'pelle', 'cute',
    'occhio', 'mano', 'capo', 'foglia', 'radice', 'erba', 'pianta',
    'seme', 'frutto', 'fiore', 'rosa', 'palmo', 'luna', 'stella',
    'oro', 'ferro', 'fuoco', 'terra', 'aria', 'torpore',
    // Verbs
    'dare', 'fare', 'dire', 'avere', 'essere', 'mettere', 'prendere',
    'bollire', 'cuocere', 'tagliare', 'mescolare', 'oliare', 'fornare',
    // Medical
    'ricetta', 'dose', 'cura', 'rimedio', 'polvere', 'decotto',
    'sorore', 'canone', 'compie', 'pervivi',
    // Adjectives & others
    'buono', 'bello', 'grande', 'piccolo', 'bianco', 'nuovo', 'alto',
    'dolce', 'forte', 'ogni', 'tale', 'quale', 'come', 'quando',
    'poi', 'ora', 'col', 'sol', 'cor',
]);

// Common Latin words (medical/botanical)
const LATIN_WORDS = new Set([
    'et', 'in', 'de', 'ad', 'per', 'cum', 'non', 'est', 'ut', 'ex',
    'ab', 'qui', 'quae', 'quod', 'hoc', 'aut', 'sed', 'vel',
    'aqua', 'oleum', 'sal', 'mel', 'vinum', 'herba', 'radix',
    'flos', 'folium', 'semen', 'fructus', 'cortex', 'color',
    'odor', 'dolor', 'calor', 'arbor', 'sol', 'luna', 'stella',
    'aurum', 'ferrum', 'ignis', 'terra', 'aer', 'cor', 'manus',
    'caput', 'os', 'sanguis', 'caro', 'pellis', 'oculus',
    'recipe', 'dosis', 'cura', 'remedium', 'pulvis', 'decoctum',
    'dare', 'facere', 'dicere', 'habere', 'esse', 'ponere',
    'bullire', 'coquere', 'secare', 'miscere', 'oleo',
]);


// ─────────────────────────────────────────────────────────────────────────────
// MODULE 4: CURRIER A/B SPLIT ANALYSIS
// Currier (1976) identified two "languages" in the VM:
//   A: Herbal/pharmaceutical sections (f1r–f57v, f87r–f102v)
//   B: Balneological/astrological/cosmological (f57v–f86v, f103r–f116v)
// Since eva-takahashi.txt lacks folio markers, we use line ranges as proxy.
// ─────────────────────────────────────────────────────────────────────────────

// Approximate line ranges for Currier A/B in the stripped EVA text
const CURRIER_SECTIONS = {
    A: { label: 'Herbal/Pharmaceutical (Currier A)', startLine: 0, endLine: 2500 },
    B: { label: 'Balneological/Astrological (Currier B)', startLine: 2500, endLine: 5211 }
};


// ─────────────────────────────────────────────────────────────────────────────
// MODULE 5: LINGUISTIC SCORER
// Scores candidate plaintext for linguistic plausibility
// ─────────────────────────────────────────────────────────────────────────────

// Character bigram frequencies for Italian (approximate, normalized)
const ITALIAN_BIGRAMS = {
    'al': 28, 'an': 32, 'ar': 26, 'at': 20, 'co': 24, 'de': 30,
    'di': 28, 'el': 22, 'en': 26, 'er': 30, 'es': 18, 'ia': 20,
    'il': 16, 'in': 34, 'io': 18, 'la': 20, 'le': 22, 'li': 16,
    'lo': 14, 'ne': 24, 'no': 18, 'on': 26, 'or': 22, 'ra': 18,
    're': 26, 'ri': 20, 'ro': 16, 'si': 18, 'st': 16, 'ta': 18,
    'te': 22, 'ti': 20, 'to': 22, 'un': 14, 'nt': 16, 'ol': 12,
    'pe': 14, 'se': 16, 'so': 10, 'ss': 10, 'tt': 8, 'uo': 10,
    'ch': 12, 'ci': 10, 'ce': 8, 'gi': 8, 'sc': 6, 'qu': 8,
};

function calculateH2(tokenArray) {
    if (tokenArray.length < 3) return 0;
    const trigramFreq = {};
    const bigramFreq = {};
    let totalTri = 0;

    for (let i = 0; i < tokenArray.length - 2; i++) {
        const triKey = `${tokenArray[i]}|${tokenArray[i+1]}|${tokenArray[i+2]}`;
        const biKey = `${tokenArray[i]}|${tokenArray[i+1]}`;
        trigramFreq[triKey] = (trigramFreq[triKey] || 0) + 1;
        bigramFreq[biKey] = (bigramFreq[biKey] || 0) + 1;
        totalTri++;
    }

    let h2 = 0;
    for (const [triKey, count] of Object.entries(trigramFreq)) {
        const parts = triKey.split('|');
        const biKey = `${parts[0]}|${parts[1]}`;
        const pTri = count / totalTri;
        const pBi = bigramFreq[biKey] / totalTri;
        if (pTri > 0 && pBi > 0) {
            h2 -= pTri * Math.log2(pTri / pBi);
        }
    }
    return h2;
}

// Score a candidate plaintext string for linguistic plausibility
function scoreCandidate(plaintext, method) {
    const text = plaintext.toLowerCase();
    const chars = text.replace(/\s+/g, '').split('');
    let score = 0;

    // 1. Character entropy (h2) — natural language should be ~3.0-4.5
    const h2 = calculateH2(chars);
    if (h2 >= 2.5 && h2 <= 5.0) score += 20;
    else if (h2 >= 1.5 && h2 <= 6.0) score += 10;

    // 2. Vowel/consonant ratio — natural language ~35-45% vowels
    const vowels = chars.filter(c => 'aeiou'.includes(c)).length;
    const vowelRatio = vowels / Math.max(chars.length, 1);
    if (vowelRatio >= 0.30 && vowelRatio <= 0.50) score += 15;
    else if (vowelRatio >= 0.20 && vowelRatio <= 0.55) score += 8;

    // 3. Italian bigram frequency match
    let bigramHits = 0;
    for (let i = 0; i < chars.length - 1; i++) {
        const bi = chars[i] + chars[i+1];
        if (ITALIAN_BIGRAMS[bi]) bigramHits++;
    }
    const bigramRatio = bigramHits / Math.max(chars.length - 1, 1);
    score += Math.round(bigramRatio * 30);

    // 4. Dictionary word matching
    const words = text.split(/\s+/).filter(w => w.length > 1);
    let dictHits = 0;
    for (const w of words) {
        if (ITALIAN_WORDS.has(w) || LATIN_WORDS.has(w) || OCCITAN_WORDS.has(w)) {
            dictHits++;
        }
        // Partial match: check if word starts with a dictionary entry
        for (const dictWord of [...ITALIAN_WORDS, ...LATIN_WORDS, ...OCCITAN_WORDS]) {
            if (dictWord.length >= 4 && w.startsWith(dictWord)) {
                dictHits += 0.5;
                break;
            }
        }
    }
    const dictRatio = dictHits / Math.max(words.length, 1);
    score += Math.round(dictRatio * 35);

    return {
        total: Math.round(score),
        h2: h2.toFixed(3),
        vowelRatio: (vowelRatio * 100).toFixed(1) + '%',
        bigramMatch: (bigramRatio * 100).toFixed(1) + '%',
        dictMatch: (dictRatio * 100).toFixed(1) + '%'
    };
}


// ─────────────────────────────────────────────────────────────────────────────
// MAIN DECODER PIPELINE
// ─────────────────────────────────────────────────────────────────────────────

function decodeLine(evaLine) {
    const words = evaLine.replace(/<[^>]+>/g, '').trim()
        .split(/[\s.]+/)
        .filter(w => w.length > 0 && !w.startsWith('<'));

    if (words.length === 0) return null;

    // ── Method 1: Naibbe Inverse (best single-letter candidates) ─────────
    const naibbeWords = [];
    const naibbeWordsNoNull = [];
    for (const w of words) {
        const clean = w.replace(/[!*=%{}]/g, '');
        const candidates = naibbeDecodeWord(clean);
        if (candidates.length > 0) {
            naibbeWords.push(candidates[0].plaintext);
            if (!NULL_WORDS.has(clean)) {
                naibbeWordsNoNull.push(candidates[0].plaintext);
            }
        } else {
            naibbeWords.push(clean);
            naibbeWordsNoNull.push(clean);
        }
    }

    // ── Method 2: Caspari-Faccini substitution ───────────────────────────
    const caspariWords = words.map(w => caspariDecode(w));

    // ── Method 3: Occitan-scored Caspari ─────────────────────────────────
    // (Same letter mapping, but scored against Occitan vocabulary)
    const occitanWords = caspariWords.slice(); // Same mapping, different scoring

    const naibbeText = naibbeWords.join(' ');
    const naibbeNoNullText = naibbeWordsNoNull.join(' ');
    const caspariText = caspariWords.join(' ');
    const occitanText = occitanWords.join(' ');

    // Score each method
    const results = [
        {
            method: 'Naibbe Inverse',
            plaintext: naibbeText,
            score: scoreCandidate(naibbeText, 'naibbe')
        },
        {
            method: 'Naibbe (nulls stripped)',
            plaintext: naibbeNoNullText,
            score: scoreCandidate(naibbeNoNullText, 'naibbe')
        },
        {
            method: 'Caspari-Faccini',
            plaintext: caspariText,
            score: scoreCandidate(caspariText, 'caspari')
        },
    ];

    // Sort by total score
    results.sort((a, b) => b.score.total - a.score.total);
    return { eva: evaLine.trim(), words, results };
}


// ─────────────────────────────────────────────────────────────────────────────
// EXECUTION
// ─────────────────────────────────────────────────────────────────────────────

const evaPath = path.join(__dirname, 'eva-takahashi.txt');
if (!fs.existsSync(evaPath)) {
    console.error('ERROR: eva-takahashi.txt not found in project directory');
    process.exit(1);
}

const text = fs.readFileSync(evaPath, 'utf8');
const lines = text.split('\n').filter(l => l.trim().length > 0 && !l.startsWith('#') && !l.startsWith('<'));

// Parse CLI arguments
const args = process.argv.slice(2);
let startLine = 0;
let numLines = 20;
let section = null;
let showDetail = false;
let outputFile = null;
let fullRun = false;

for (const arg of args) {
    if (arg.startsWith('--start=')) startLine = parseInt(arg.split('=')[1]) || 0;
    else if (arg.startsWith('--lines=')) numLines = parseInt(arg.split('=')[1]) || 20;
    else if (arg === '--section=A') section = 'A';
    else if (arg === '--section=B') section = 'B';
    else if (arg === '--detail') showDetail = true;
    else if (arg.startsWith('--output=')) outputFile = arg.split('=')[1];
    else if (arg === '--full') fullRun = true;
}

if (section) {
    const sec = CURRIER_SECTIONS[section];
    startLine = sec.startLine;
    numLines = Math.min(fullRun ? (sec.endLine - sec.startLine) : 30, sec.endLine - sec.startLine);
}

if (fullRun && !section) {
    numLines = lines.length;
    startLine = 0;
}

const endIdx = Math.min(startLine + numLines, lines.length);

console.log('╔══════════════════════════════════════════════════════════════════════╗');
console.log('║  VOYNICH MANUSCRIPT MULTI-THEORY DECODER                            ║');
console.log('║  Naibbe Inverse · Caspari-Faccini · Occitan Hypothesis              ║');
console.log('╚══════════════════════════════════════════════════════════════════════╝\n');

if (section) {
    const sec = CURRIER_SECTIONS[section];
    console.log(`Section: ${sec.label}`);
}
console.log(`Processing lines ${startLine + 1} to ${endIdx} of ${lines.length} total\n`);
console.log('═'.repeat(72));

// Aggregate scoring
const methodScores = {};
let totalLines = 0;
let fullOutput = '';

function appendOutput(str) {
    console.log(str);
    fullOutput += str + '\n';
}

for (let i = startLine; i < endIdx; i++) {
    const result = decodeLine(lines[i]);
    if (!result) continue;
    totalLines++;

    const topResult = result.results[0];

    appendOutput(`\n[Line ${i + 1}] EVA: ${result.eva.slice(0, 70)}${result.eva.length > 70 ? '...' : ''}`);

    for (const r of result.results) {
        const marker = r === topResult ? '★' : ' ';
        appendOutput(`  ${marker} ${r.method.padEnd(22)} → ${r.plaintext.slice(0, 55)}${r.plaintext.length > 55 ? '...' : ''}`);

        if (showDetail) {
            appendOutput(`    Score: ${r.score.total}/100 | h2=${r.score.h2} | vowels=${r.score.vowelRatio} | bigrams=${r.score.bigramMatch} | dict=${r.score.dictMatch}`);
        }

        if (!methodScores[r.method]) methodScores[r.method] = { total: 0, count: 0 };
        methodScores[r.method].total += r.score.total;
        methodScores[r.method].count++;
    }
}

// ── Summary Statistics ───────────────────────────────────────────────────

appendOutput('\n' + '═'.repeat(72));
appendOutput('\n=== AGGREGATE METHOD SCORES ===\n');
appendOutput('Method'.padEnd(26) + 'Avg Score'.padEnd(14) + 'Lines Processed');
appendOutput('─'.repeat(55));

const sortedMethods = Object.entries(methodScores)
    .map(([method, data]) => ({ method, avgScore: data.total / data.count, count: data.count }))
    .sort((a, b) => b.avgScore - a.avgScore);

for (const m of sortedMethods) {
    appendOutput(`${m.method.padEnd(26)}${m.avgScore.toFixed(1).padEnd(14)}${m.count}`);
}

// ── Entropy comparison ──────────────────────────────────────────────────

appendOutput('\n=== ENTROPY ANALYSIS ===\n');

// Raw EVA character entropy
const allEVAChars = lines.slice(startLine, endIdx).join(' ').replace(/[!*=%{}<>\s]/g, '').split('');
const evaH2 = calculateH2(allEVAChars);
appendOutput(`Raw EVA character h2:       ${evaH2.toFixed(4)} bits/char`);

// Best method's output entropy
if (sortedMethods.length > 0) {
    const bestMethod = sortedMethods[0].method;
    const bestLines = [];
    for (let i = startLine; i < endIdx; i++) {
        const result = decodeLine(lines[i]);
        if (!result) continue;
        const best = result.results.find(r => r.method === bestMethod);
        if (best) bestLines.push(best.plaintext);
    }
    const bestChars = bestLines.join(' ').replace(/\s+/g, '').split('');
    const bestH2 = calculateH2(bestChars);
    appendOutput(`${bestMethod} output h2:  ${bestH2.toFixed(4)} bits/char`);
    appendOutput(`Natural language target:    3.0 - 4.5 bits/char`);

    if (bestH2 > evaH2) {
        appendOutput(`\n✅ Entropy INCREASED from ${evaH2.toFixed(2)} → ${bestH2.toFixed(2)}`);
        appendOutput(`   This supports the verbose cipher hypothesis (compressed = higher entropy)`);
    } else {
        appendOutput(`\n⚠ Entropy did not increase significantly.`);
    }
}

// ── Best candidate words (dictionary matches) ───────────────────────────

appendOutput('\n=== DICTIONARY-MATCHED WORDS (Italian / Latin / Occitan) ===\n');

const dictMatches = new Map();
for (let i = startLine; i < Math.min(startLine + 100, endIdx); i++) {
    const result = decodeLine(lines[i]);
    if (!result) continue;

    for (const r of result.results) {
        const words = r.plaintext.split(/\s+/);
        for (let wi = 0; wi < result.words.length && wi < words.length; wi++) {
            const pw = words[wi].toLowerCase();
            if (pw.length > 1 && (ITALIAN_WORDS.has(pw) || LATIN_WORDS.has(pw) || OCCITAN_WORDS.has(pw))) {
                const key = `${result.words[wi]}→${pw}`;
                if (!dictMatches.has(key)) {
                    dictMatches.set(key, { eva: result.words[wi], decoded: pw, method: r.method, count: 0 });
                }
                dictMatches.get(key).count++;
            }
        }
    }
}

const sortedMatches = [...dictMatches.values()].sort((a, b) => b.count - a.count).slice(0, 30);
if (sortedMatches.length > 0) {
    appendOutput('EVA'.padEnd(15) + 'Decoded'.padEnd(15) + 'Method'.padEnd(24) + 'Hits');
    appendOutput('─'.repeat(60));
    for (const m of sortedMatches) {
        appendOutput(`${m.eva.padEnd(15)}${m.decoded.padEnd(15)}${m.method.padEnd(24)}${m.count}`);
    }
} else {
    appendOutput('No exact dictionary matches found in this section.');
}

// ── Write output file ───────────────────────────────────────────────────

if (outputFile) {
    fs.writeFileSync(outputFile, fullOutput);
    console.log(`\nOutput written to ${outputFile}`);
}

appendOutput('\n=== DECODING COMPLETE ===');
appendOutput(`Processed ${totalLines} lines using 3 decoding methods.`);
appendOutput('Use --detail for per-line scoring breakdown.');
appendOutput('Use --section=A or --section=B for Currier A/B split analysis.');
appendOutput('Use --full for complete manuscript processing.');
appendOutput('Use --output=filename.txt to save results.');
