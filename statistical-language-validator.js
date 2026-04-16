const fs = require('fs');
const path = require('path');

// =============================================================================
// STATISTICAL LANGUAGE VALIDATOR — Ponnaluri (2024)
// =============================================================================
// Based on: "The Voynich Manuscript was written in a single, natural language"
// Published: Cryptologia, Vol 49, No 6, 2024
// Author: Ponnaluri
//
// KEY FINDINGS:
// 1. Challenges Currier's two-language theory (A vs B are NOT different languages)
// 2. Challenges Davis's five-scribe theory (scribes ≠ distinct dialects)
// 3. Uses Zipf's Law, Brevity Law (word length vs frequency), and Heap's Law
//    (vocabulary growth) to argue VM contains a SINGLE natural language
//
// This module independently validates these laws on the raw EVA transcription,
// on each Currier section, and on each scribe's subset — testing whether the
// data supports one language or many.
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// MATHEMATICAL FOUNDATIONS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * ZIPF'S LAW: frequency(r) ∝ 1/r^α
 * Natural language: α ≈ 1.0, R² > 0.90
 * Returns: { exponent, r2, topWords }
 */
function zipfAnalysis(words, topN = 100) {
    const freq = {};
    for (const w of words) {
        const lower = w.toLowerCase();
        if (lower.length > 0) freq[lower] = (freq[lower] || 0) + 1;
    }

    const sorted = Object.entries(freq)
        .sort((a, b) => b[1] - a[1]);

    const n = Math.min(topN, sorted.length);
    if (n < 5) return { exponent: 0, r2: 0, topWords: [], vocabSize: sorted.length };

    // Linear regression on log-log scale
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    for (let i = 0; i < n; i++) {
        const x = Math.log(i + 1);
        const y = Math.log(sorted[i][1]);
        sumX += x; sumY += y; sumXY += x * y; sumX2 += x * x;
    }
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    const meanY = sumY / n;
    let ssTot = 0, ssRes = 0;
    for (let i = 0; i < n; i++) {
        const x = Math.log(i + 1);
        const y = Math.log(sorted[i][1]);
        const pred = slope * x + intercept;
        ssTot += (y - meanY) ** 2;
        ssRes += (y - pred) ** 2;
    }
    const r2 = ssTot > 0 ? 1 - ssRes / ssTot : 0;

    return {
        exponent: -slope,
        r2,
        topWords: sorted.slice(0, 20).map(([word, count]) => ({ word, count })),
        vocabSize: sorted.length,
        totalWords: words.length,
    };
}

/**
 * BREVITY LAW (Zipf's Law of Abbreviation):
 * More frequent words tend to be shorter.
 * Correlation between word length and log(frequency) should be negative.
 * Natural language: r < -0.3 (typically -0.4 to -0.7)
 */
function brevityLaw(words) {
    const freq = {};
    for (const w of words) {
        const lower = w.toLowerCase();
        if (lower.length > 0) freq[lower] = (freq[lower] || 0) + 1;
    }

    const entries = Object.entries(freq).filter(([w]) => w.length > 0);
    if (entries.length < 10) return { correlation: 0, n: 0 };

    const lengths = entries.map(([w]) => w.length);
    const logFreqs = entries.map(([, f]) => Math.log(f));
    const n = entries.length;

    const meanL = lengths.reduce((s, v) => s + v, 0) / n;
    const meanF = logFreqs.reduce((s, v) => s + v, 0) / n;

    let cov = 0, varL = 0, varF = 0;
    for (let i = 0; i < n; i++) {
        const dL = lengths[i] - meanL;
        const dF = logFreqs[i] - meanF;
        cov += dL * dF;
        varL += dL * dL;
        varF += dF * dF;
    }

    const correlation = (varL > 0 && varF > 0) ? cov / Math.sqrt(varL * varF) : 0;
    const avgWordLength = meanL;

    return { correlation, n: entries.length, avgWordLength };
}

/**
 * HEAP'S LAW (Herdan's Law):
 * V(n) = K * n^β  where V = vocabulary size, n = corpus size
 * Natural language: β ≈ 0.4-0.6
 * This measures how quickly new words appear as we read more text.
 * If β is very low, vocabulary saturates fast (meaningless repetition).
 * If β is very high, every word is unique (random).
 */
function heapsLaw(words, samplePoints = 50) {
    if (words.length < 100) return { beta: 0, K: 0, r2: 0 };

    const vocab = new Set();
    const points = []; // [corpusSize, vocabSize]

    const step = Math.max(1, Math.floor(words.length / samplePoints));
    for (let i = 0; i < words.length; i++) {
        vocab.add(words[i].toLowerCase());
        if ((i + 1) % step === 0 || i === words.length - 1) {
            points.push([i + 1, vocab.size]);
        }
    }

    // Linear regression on log-log scale: log(V) = log(K) + β*log(n)
    const n = points.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    for (const [corpSize, vocSize] of points) {
        const x = Math.log(corpSize);
        const y = Math.log(vocSize);
        sumX += x; sumY += y; sumXY += x * y; sumX2 += x * x;
    }
    const beta = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const logK = (sumY - beta * sumX) / n;
    const K = Math.exp(logK);

    const meanY = sumY / n;
    let ssTot = 0, ssRes = 0;
    for (const [corpSize, vocSize] of points) {
        const x = Math.log(corpSize);
        const y = Math.log(vocSize);
        const pred = beta * x + logK;
        ssTot += (y - meanY) ** 2;
        ssRes += (y - pred) ** 2;
    }
    const r2 = ssTot > 0 ? 1 - ssRes / ssTot : 0;

    return { beta, K, r2, finalVocab: vocab.size, corpusSize: words.length };
}

/**
 * ENTROPY ANALYSIS (Shannon 1948):
 * H1 = first-order character entropy (unigram)
 * H2 = second-order conditional entropy (bigram)
 * Natural language: H1 ≈ 4.0-4.5, H2 ≈ 2.5-3.5
 */
function entropyAnalysis(text) {
    const chars = text.toLowerCase().replace(/[^a-z]/g, '').split('');
    if (chars.length < 10) return { h1: 0, h2: 0 };

    // H1: unigram entropy
    const uniFreq = {};
    for (const c of chars) uniFreq[c] = (uniFreq[c] || 0) + 1;
    let h1 = 0;
    for (const count of Object.values(uniFreq)) {
        const p = count / chars.length;
        if (p > 0) h1 -= p * Math.log2(p);
    }

    // H2: conditional entropy H(X|Y) = H(X,Y) - H(Y)
    const biFreq = {};
    for (let i = 0; i < chars.length - 1; i++) {
        const bi = chars[i] + chars[i + 1];
        biFreq[bi] = (biFreq[bi] || 0) + 1;
    }
    let hBi = 0;
    const biTotal = chars.length - 1;
    for (const count of Object.values(biFreq)) {
        const p = count / biTotal;
        if (p > 0) hBi -= p * Math.log2(p);
    }
    const h2 = hBi - h1;

    return { h1, h2, charCount: chars.length, alphabetSize: Object.keys(uniFreq).length };
}

/**
 * TYPE-TOKEN RATIO (TTR) and Hapax Legomena ratio:
 * TTR = unique words / total words
 * Hapax ratio = words appearing only once / total unique words
 * Natural language: TTR decreases with corpus size, Hapax ~ 40-60%
 */
function typeTokenAnalysis(words) {
    const freq = {};
    for (const w of words) {
        const lower = w.toLowerCase();
        if (lower.length > 0) freq[lower] = (freq[lower] || 0) + 1;
    }
    const types = Object.keys(freq).length;
    const tokens = words.length;
    const hapax = Object.values(freq).filter(c => c === 1).length;
    const disLeg = Object.values(freq).filter(c => c === 2).length; // Dis legomena

    return {
        types,
        tokens,
        ttr: types / Math.max(tokens, 1),
        hapax,
        hapaxRatio: hapax / Math.max(types, 1),
        disLeg,
        disLegRatio: disLeg / Math.max(types, 1),
    };
}


// ─────────────────────────────────────────────────────────────────────────────
// PONNALURI'S KEY TEST: Compare A vs B and per-scribe subsets
// If the manuscript is ONE language, statistical properties should be
// consistent across sections and scribes.
// ─────────────────────────────────────────────────────────────────────────────

// Approximate Currier A/B line ranges (same as voynich-decoder.js)
const CURRIER_SECTIONS = {
    A: { label: 'Herbal/Pharmaceutical (Currier A)', startLine: 0, endLine: 2500 },
    B: { label: 'Balneological/Astrological (Currier B)', startLine: 2500, endLine: 5211 }
};

// Approximate per-folio scribe assignments (from scribe-cluster-analyzer.js)
// Scribe line ranges (approximate, since no folio markers in stripped text)
const SCRIBE_RANGES = {
    1: { label: 'Scribe 1 (f1r–f24v: Main herbal A)', start: 0, end: 960 },
    2: { label: 'Scribe 2 (f25r–f56v: Herbal B)', start: 960, end: 2240 },
    3: { label: 'Scribe 3 (f57r–f66v: Pharma/Astro)', start: 2240, end: 2640 },
    4: { label: 'Scribe 4 (f67r–f84v: Cosmological)', start: 2640, end: 3400 },
    5: { label: 'Scribe 5 (f85r–f116v: Recipes/Stars)', start: 3400, end: 5211 },
};

function extractWords(text) {
    return text.replace(/<[^>]+>/g, '')
        .replace(/[!*=%{}#]/g, '')
        .split(/[\s.]+/)
        .filter(w => w.length > 0 && !w.startsWith('<'));
}


// ─────────────────────────────────────────────────────────────────────────────
// MAIN EXECUTION
// ─────────────────────────────────────────────────────────────────────────────

const evaPath = path.join(__dirname, 'eva-takahashi.txt');
if (!fs.existsSync(evaPath)) {
    console.error('ERROR: eva-takahashi.txt not found in project directory');
    process.exit(1);
}

const text = fs.readFileSync(evaPath, 'utf8');
const lines = text.split('\n').filter(l => l.trim().length > 0 && !l.startsWith('#') && !l.startsWith('<'));

let output = '';
function out(str) { console.log(str); output += str + '\n'; }

out('╔══════════════════════════════════════════════════════════════════════╗');
out('║  STATISTICAL LANGUAGE VALIDATOR — Ponnaluri (2024)                   ║');
out('║  Zipf\'s Law · Brevity Law · Heap\'s Law · Entropy · TTR              ║');
out('║  Tests: Single Language? Same across Currier A/B? Same per Scribe?  ║');
out('╚══════════════════════════════════════════════════════════════════════╝\n');

// ════════════════════════════════════════════════════════════════════════
// TEST 1: FULL CORPUS ANALYSIS
// ════════════════════════════════════════════════════════════════════════

const fullText = lines.join(' ');
const allWords = extractWords(fullText);
const fullRawText = lines.join('');

out('═'.repeat(72));
out('\n█ TEST 1: FULL CORPUS STATISTICAL PROFILE\n');

const zipfFull = zipfAnalysis(allWords);
const brevityFull = brevityLaw(allWords);
const heapsFull = heapsLaw(allWords);
const entropyFull = entropyAnalysis(fullRawText);
const ttrFull = typeTokenAnalysis(allWords);

out(`Total lines:          ${lines.length}`);
out(`Total words (tokens): ${allWords.length}`);
out(`Unique words (types): ${ttrFull.types}`);
out(`Type-Token Ratio:     ${ttrFull.ttr.toFixed(4)}`);
out(`Hapax Legomena:       ${ttrFull.hapax} (${(ttrFull.hapaxRatio * 100).toFixed(1)}% of vocab)`);
out(`Dis Legomena:         ${ttrFull.disLeg} (${(ttrFull.disLegRatio * 100).toFixed(1)}% of vocab)`);

out(`\n── Zipf's Law ──`);
out(`Exponent α:           ${zipfFull.exponent.toFixed(4)} ${zipfFull.exponent > 0.7 && zipfFull.exponent < 1.5 ? '✅ natural language range' : '⚠ outside typical range'}`);
out(`R² (goodness of fit): ${zipfFull.r2.toFixed(4)} ${zipfFull.r2 > 0.90 ? '✅ excellent fit' : zipfFull.r2 > 0.80 ? '⚠ decent fit' : '❌ poor fit'}`);
out(`Top 10 words:`);
for (const { word, count } of zipfFull.topWords.slice(0, 10)) {
    out(`  ${word.padEnd(15)} ${count}`);
}

out(`\n── Brevity Law ──`);
out(`Correlation (length vs log-freq): ${brevityFull.correlation.toFixed(4)} ${brevityFull.correlation < -0.3 ? '✅ negative (natural language)' : '⚠ unexpected direction'}`);
out(`Average word length:              ${brevityFull.avgWordLength.toFixed(2)} chars`);

out(`\n── Heap's Law ──`);
out(`β (vocab growth rate): ${heapsFull.beta.toFixed(4)} ${heapsFull.beta > 0.3 && heapsFull.beta < 0.7 ? '✅ natural language range' : '⚠ outside typical range'}`);
out(`K (scaling constant):  ${heapsFull.K.toFixed(2)}`);
out(`R² (goodness of fit):  ${heapsFull.r2.toFixed(4)}`);
out(`Final vocabulary:      ${heapsFull.finalVocab} types in ${heapsFull.corpusSize} tokens`);

out(`\n── Entropy ──`);
out(`H1 (unigram entropy):  ${entropyFull.h1.toFixed(4)} bits/char`);
out(`H2 (conditional):      ${entropyFull.h2.toFixed(4)} bits/char`);
out(`Alphabet size used:    ${entropyFull.alphabetSize} characters`);
out(`Natural language H1:   ~4.0-4.5 | H2: ~2.5-3.5`);
out(`Voynich H1 is low due to restricted EVA alphabet (not real letters)`);


// ════════════════════════════════════════════════════════════════════════
// TEST 2: CURRIER A vs B COMPARISON (Ponnaluri's key challenge)
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ TEST 2: CURRIER A vs B — ONE LANGUAGE OR TWO?\n');
out('Ponnaluri (2024) argues: "no evidence for two languages or dialects"\n');

const sectionResults = {};

for (const [section, range] of Object.entries(CURRIER_SECTIONS)) {
    const sectionLines = lines.slice(range.startLine, range.endLine);
    const sectionText = sectionLines.join(' ');
    const sectionWords = extractWords(sectionText);
    const sectionRaw = sectionLines.join('');

    const zipf = zipfAnalysis(sectionWords);
    const brevity = brevityLaw(sectionWords);
    const heaps = heapsLaw(sectionWords);
    const entropy = entropyAnalysis(sectionRaw);
    const ttr = typeTokenAnalysis(sectionWords);

    sectionResults[section] = { zipf, brevity, heaps, entropy, ttr, wordCount: sectionWords.length };

    out(`── Section ${section}: ${range.label} ──`);
    out(`  Words:      ${sectionWords.length} | Types: ${ttr.types} | TTR: ${ttr.ttr.toFixed(4)}`);
    out(`  Zipf α:     ${zipf.exponent.toFixed(4)} (R²=${zipf.r2.toFixed(4)})`);
    out(`  Brevity r:  ${brevity.correlation.toFixed(4)}`);
    out(`  Heap's β:   ${heaps.beta.toFixed(4)} (R²=${heaps.r2.toFixed(4)})`);
    out(`  H1:         ${entropy.h1.toFixed(4)} | H2: ${entropy.h2.toFixed(4)}`);
    out(`  Hapax:      ${ttr.hapax} (${(ttr.hapaxRatio * 100).toFixed(1)}%)`);
    out('');
}

// Compare A vs B
const zA = sectionResults.A;
const zB = sectionResults.B;

out('── Comparison: A vs B ──');
out('Metric'.padEnd(25) + 'Section A'.padEnd(15) + 'Section B'.padEnd(15) + 'Δ (difference)');
out('─'.repeat(70));

const comparisons = [
    ['Zipf α', zA.zipf.exponent, zB.zipf.exponent],
    ['Zipf R²', zA.zipf.r2, zB.zipf.r2],
    ['Brevity r', zA.brevity.correlation, zB.brevity.correlation],
    ['Heap\'s β', zA.heaps.beta, zB.heaps.beta],
    ['H1 (entropy)', zA.entropy.h1, zB.entropy.h1],
    ['H2 (cond. entropy)', zA.entropy.h2, zB.entropy.h2],
    ['TTR', zA.ttr.ttr, zB.ttr.ttr],
    ['Hapax ratio', zA.ttr.hapaxRatio, zB.ttr.hapaxRatio],
    ['Avg word length', zA.brevity.avgWordLength, zB.brevity.avgWordLength],
];

let significantDifferences = 0;
for (const [name, valA, valB] of comparisons) {
    const delta = Math.abs(valA - valB);
    const avg = (Math.abs(valA) + Math.abs(valB)) / 2;
    const pctDiff = avg > 0 ? (delta / avg * 100) : 0;
    const sig = pctDiff > 15 ? ' ⚠ SIGNIFICANT' : ' ✅ similar';
    if (pctDiff > 15) significantDifferences++;
    out(`${name.padEnd(25)}${valA.toFixed(4).padEnd(15)}${valB.toFixed(4).padEnd(15)}${delta.toFixed(4)} (${pctDiff.toFixed(1)}%)${sig}`);
}

out(`\nVerdict: ${significantDifferences} of ${comparisons.length} metrics show >15% divergence`);
if (significantDifferences <= 2) {
    out('✅ SUPPORTS Ponnaluri: Currier A and B appear to be the SAME language.');
    out('   Statistical properties are remarkably consistent across sections.');
} else if (significantDifferences <= 4) {
    out('⚠  MIXED EVIDENCE: Some divergence between A and B, but several metrics');
    out('   remain similar. Could be same language with different vocabulary domains.');
} else {
    out('❌ CONTRADICTS Ponnaluri: Significant statistical divergence between');
    out('   sections A and B. Currier\'s two-language hypothesis may have merit.');
}


// ════════════════════════════════════════════════════════════════════════
// TEST 3: PER-SCRIBE ANALYSIS (challenges Davis's 5-scribe theory)
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ TEST 3: PER-SCRIBE STATISTICAL COMPARISON\n');
out('Ponnaluri: Scribes 1-4 distributed workload equitably; Scribe 5 may be late entrant\n');

const scribeResults = {};

out('Scribe'.padEnd(8) + 'Words'.padEnd(8) + 'Types'.padEnd(8) + 'Zipf α'.padEnd(10) + 'Brevity r'.padEnd(12) + 'Heap β'.padEnd(10) + 'H1'.padEnd(8) + 'H2');
out('─'.repeat(72));

for (const [scribeNum, range] of Object.entries(SCRIBE_RANGES)) {
    const scribeLines = lines.slice(range.start, Math.min(range.end, lines.length));
    const scribeText = scribeLines.join(' ');
    const scribeWords = extractWords(scribeText);
    const scribeRaw = scribeLines.join('');

    const zipf = zipfAnalysis(scribeWords);
    const brevity = brevityLaw(scribeWords);
    const heaps = heapsLaw(scribeWords);
    const entropy = entropyAnalysis(scribeRaw);

    scribeResults[scribeNum] = { zipf, brevity, heaps, entropy, wordCount: scribeWords.length };

    out(`  ${scribeNum}    `.padEnd(8) +
        `${scribeWords.length}`.padEnd(8) +
        `${zipf.vocabSize}`.padEnd(8) +
        `${zipf.exponent.toFixed(3)}`.padEnd(10) +
        `${brevity.correlation.toFixed(3)}`.padEnd(12) +
        `${heaps.beta.toFixed(3)}`.padEnd(10) +
        `${entropy.h1.toFixed(3)}`.padEnd(8) +
        `${entropy.h2.toFixed(3)}`);
}

// Calculate coefficient of variation for each metric across scribes
out('\n── Cross-Scribe Variability (Coefficient of Variation) ──\n');

function coeffOfVariation(values) {
    const n = values.length;
    const mean = values.reduce((s, v) => s + v, 0) / n;
    const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / n;
    const stdDev = Math.sqrt(variance);
    return { mean, stdDev, cv: mean !== 0 ? stdDev / Math.abs(mean) : 0 };
}

const scribeNums = Object.keys(scribeResults);
const metricsToCompare = {
    'Zipf α': scribeNums.map(s => scribeResults[s].zipf.exponent),
    'Brevity r': scribeNums.map(s => scribeResults[s].brevity.correlation),
    'Heap\'s β': scribeNums.map(s => scribeResults[s].heaps.beta),
    'H1 (entropy)': scribeNums.map(s => scribeResults[s].entropy.h1),
    'H2 (cond.)': scribeNums.map(s => scribeResults[s].entropy.h2),
};

out('Metric'.padEnd(18) + 'Mean'.padEnd(12) + 'Std Dev'.padEnd(12) + 'CV%'.padEnd(10) + 'Assessment');
out('─'.repeat(62));

let scribeSignificant = 0;
for (const [metric, values] of Object.entries(metricsToCompare)) {
    const cv = coeffOfVariation(values);
    const cvPct = cv.cv * 100;
    const assessment = cvPct < 10 ? '✅ Very consistent' : cvPct < 20 ? '⚠ Moderate' : '❌ High variability';
    if (cvPct > 20) scribeSignificant++;
    out(`${metric.padEnd(18)}${cv.mean.toFixed(4).padEnd(12)}${cv.stdDev.toFixed(4).padEnd(12)}${cvPct.toFixed(1).padEnd(10)}${assessment}`);
}

out(`\nVerdict: ${scribeSignificant} of ${Object.keys(metricsToCompare).length} metrics show high (>20%) cross-scribe variability`);
if (scribeSignificant <= 1) {
    out('✅ SUPPORTS Ponnaluri: All 5 scribes produce statistically similar language.');
    out('   This suggests equal workload distribution within a single text.');
} else if (scribeSignificant <= 2) {
    out('⚠  PARTIAL SUPPORT: Mostly consistent, but some differences (possibly Scribe 5).');
} else {
    out('❌ CONTRADICTS Ponnaluri: Significant variability across scribes suggestsaltern');
    out('   different language characteristics per scribe.');
}


// ════════════════════════════════════════════════════════════════════════
// TEST 4: COMPARISON WITH KNOWN LANGUAGES
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ TEST 4: COMPARISON WITH KNOWN LANGUAGE BENCHMARKS\n');

// Reference values for natural languages
const LANGUAGE_BENCHMARKS = {
    'English':  { zipfAlpha: 1.01, heapsBeta: 0.54, h1: 4.11, brevityR: -0.42 },
    'Italian':  { zipfAlpha: 1.04, heapsBeta: 0.52, h1: 3.95, brevityR: -0.38 },
    'Latin':    { zipfAlpha: 1.08, heapsBeta: 0.50, h1: 4.00, brevityR: -0.35 },
    'French':   { zipfAlpha: 1.02, heapsBeta: 0.53, h1: 3.98, brevityR: -0.40 },
    'German':   { zipfAlpha: 1.05, heapsBeta: 0.49, h1: 4.08, brevityR: -0.33 },
    'Arabic':   { zipfAlpha: 1.10, heapsBeta: 0.55, h1: 4.15, brevityR: -0.30 },
    'Hebrew':   { zipfAlpha: 1.07, heapsBeta: 0.51, h1: 4.05, brevityR: -0.32 },
    'Random':   { zipfAlpha: 0.50, heapsBeta: 0.95, h1: 4.70, brevityR: 0.05 },
};

out('Language'.padEnd(14) + 'Zipf α'.padEnd(10) + 'Heap β'.padEnd(10) + 'H1'.padEnd(8) + 'Brevity r'.padEnd(12) + 'Distance');
out('─'.repeat(64));

const voynichProfile = {
    zipfAlpha: zipfFull.exponent,
    heapsBeta: heapsFull.beta,
    h1: entropyFull.h1,
    brevityR: brevityFull.correlation,
};

const distances = [];
for (const [lang, bench] of Object.entries(LANGUAGE_BENCHMARKS)) {
    // Euclidean distance in normalized feature space
    const dZipf = (voynichProfile.zipfAlpha - bench.zipfAlpha) / 0.2; // normalize by typical range
    const dHeaps = (voynichProfile.heapsBeta - bench.heapsBeta) / 0.2;
    const dH1 = (voynichProfile.h1 - bench.h1) / 0.5;
    const dBrev = (voynichProfile.brevityR - bench.brevityR) / 0.2;
    const dist = Math.sqrt(dZipf ** 2 + dHeaps ** 2 + dH1 ** 2 + dBrev ** 2);

    distances.push({ lang, dist, ...bench });

    out(`${lang.padEnd(14)}${bench.zipfAlpha.toFixed(3).padEnd(10)}${bench.heapsBeta.toFixed(3).padEnd(10)}${bench.h1.toFixed(3).padEnd(8)}${bench.brevityR.toFixed(3).padEnd(12)}${dist.toFixed(3)}`);
}

out(`${'─'.repeat(64)}`);
out(`${'VOYNICH'.padEnd(14)}${voynichProfile.zipfAlpha.toFixed(3).padEnd(10)}${voynichProfile.heapsBeta.toFixed(3).padEnd(10)}${voynichProfile.h1.toFixed(3).padEnd(8)}${voynichProfile.brevityR.toFixed(3).padEnd(12)}(reference)`);

distances.sort((a, b) => a.dist - b.dist);
out(`\nClosest match: ${distances[0].lang} (distance: ${distances[0].dist.toFixed(3)})`);
out(`Runner-up:     ${distances[1].lang} (distance: ${distances[1].dist.toFixed(3)})`);

if (distances[distances.length - 1].lang === 'Random' || distances.find(d => d.lang === 'Random').dist > distances[0].dist * 2) {
    out('\n✅ Voynich text is significantly closer to NATURAL LANGUAGES than to random text.');
    out('   This supports the hypothesis that the manuscript contains real language.');
} else {
    out('\n⚠ Voynich text does not clearly separate from random in this metric space.');
}


// ════════════════════════════════════════════════════════════════════════
// OVERALL CONCLUSION
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ OVERALL CONCLUSION\n');
out('Ponnaluri (2024) claims: "The Voynich Manuscript was written in a');
out('single, natural language"');
out('');
out('Our independent validation:');
out(`  1. Zipf's Law:    α = ${zipfFull.exponent.toFixed(3)}, R² = ${zipfFull.r2.toFixed(3)} — ${zipfFull.exponent > 0.7 && zipfFull.exponent < 1.5 && zipfFull.r2 > 0.85 ? 'SUPPORTS natural language' : 'INCONCLUSIVE'}`);
out(`  2. Brevity Law:   r = ${brevityFull.correlation.toFixed(3)} — ${brevityFull.correlation < -0.2 ? 'SUPPORTS (frequent words are shorter)' : 'INCONCLUSIVE'}`);
out(`  3. Heap's Law:    β = ${heapsFull.beta.toFixed(3)} — ${heapsFull.beta > 0.3 && heapsFull.beta < 0.7 ? 'SUPPORTS vocabulary growth rate' : 'OUTSIDE natural language range'}`);
out(`  4. A vs B:        ${significantDifferences} / ${comparisons.length} significant differences — ${significantDifferences <= 2 ? 'SUPPORTS single language' : 'MIXED'}`);
out(`  5. Scribes:       ${scribeSignificant} / ${Object.keys(metricsToCompare).length} high-variability metrics — ${scribeSignificant <= 1 ? 'SUPPORTS equal distribution' : 'MIXED'}`);
out(`  6. Closest lang:  ${distances[0].lang} (distance: ${distances[0].dist.toFixed(3)})`);
out('');

const supportCount = [
    zipfFull.exponent > 0.7 && zipfFull.exponent < 1.5 && zipfFull.r2 > 0.85,
    brevityFull.correlation < -0.2,
    heapsFull.beta > 0.3 && heapsFull.beta < 0.7,
    significantDifferences <= 2,
    scribeSignificant <= 1,
].filter(Boolean).length;

if (supportCount >= 4) {
    out('✅ STRONG SUPPORT for Ponnaluri\'s hypothesis: The Voynich Manuscript');
    out('   is very likely written in a single natural language, not gibberish.');
} else if (supportCount >= 3) {
    out('⚠  MODERATE SUPPORT: Most tests support natural language hypothesis,');
    out('   but some metrics show anomalies worth further investigation.');
} else {
    out('❌ WEAK SUPPORT: Statistical tests show mixed results. The manuscript');
    out('   may contain language but doesn\'t cleanly fit standard models.');
}

// ── Output file ──────────────────────────────────────────────────────

const cliArgs = process.argv.slice(2);
const outputArg = cliArgs.find(a => a.startsWith('--output='));
if (outputArg) {
    const outFile = outputArg.split('=')[1];
    fs.writeFileSync(outFile, output);
    console.log(`\nOutput written to ${outFile}`);
}

out('\n=== STATISTICAL LANGUAGE VALIDATION COMPLETE ===');
out('Based on Ponnaluri (2024) Cryptologia Vol 49 No 6');
out('Use --output=file.txt to save results');
