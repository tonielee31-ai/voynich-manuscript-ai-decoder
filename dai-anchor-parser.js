const fs = require('fs');
const path = require('path');

// =============================================================================
// DAI ANCHOR PARSER — Graves 2025 Semantic Anchor Method
// Based on Shane Matthew Graves's 2025 decipherment approach
// =============================================================================
// Theory: The Voynichese trigram 'dai' functions as a recurring semantic anchor.
// Instead of purely statistical models, this method uses historical cryptanalysis
// and linguistic pattern recognition around 'dai' to unlock surrounding content
// in botanical, astronomical, and pharmaceutical sections.
//
// This script:
//   1. Locates ALL occurrences of the 'dai' trigram in the EVA text
//   2. Extracts N-word context windows around each occurrence
//   3. Builds co-occurrence frequency maps to identify semantic clusters
//   4. Groups findings by manuscript section (herbal, astro, pharma)
//   5. Identifies syntactic patterns (what word classes surround 'dai'?)
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// CONFIGURABLE PARAMETERS
// ─────────────────────────────────────────────────────────────────────────────

const CONFIG = {
    // Context window: how many words before/after 'dai' to capture
    WINDOW_SIZE: 5,

    // The anchor trigram to search for
    ANCHOR: 'dai',

    // Whether to match 'dai' as a standalone trigram, as a substring inside
    // words (e.g., 'daiin', 'odain'), or both
    MATCH_MODE: 'both',  // 'exact' | 'substring' | 'both'

    // Manuscript section boundaries (approximate line ranges in eva-takahashi.txt)
    // These correspond to the known manuscript organization:
    SECTIONS: {
        'Herbal A (f1r-f57v)':         { start: 0,    end: 1500 },
        'Herbal B (f58r-f66v)':         { start: 1500, end: 1900 },
        'Astronomical (f67r-f73v)':     { start: 1900, end: 2600 },
        'Cosmological (f75r-f84v)':     { start: 2600, end: 3200 },
        'Biological (f85r-f86v)':       { start: 3200, end: 3500 },
        'Pharmaceutical (f87r-f102v)':  { start: 3500, end: 4500 },
        'Stars/Recipes (f103r-f116v)':  { start: 4500, end: 5211 }
    },

    // Top N results to display in each analysis
    TOP_N: 20,

    // Minimum co-occurrence count to consider significant
    MIN_COOCCURRENCE: 3
};

// ─────────────────────────────────────────────────────────────────────────────
// TEXT LOADING & PREPROCESSING
// ─────────────────────────────────────────────────────────────────────────────

const evaPath = path.join(__dirname, 'eva-takahashi.txt');
if (!fs.existsSync(evaPath)) {
    console.error('ERROR: eva-takahashi.txt not found. Place it in the same directory as this script.');
    process.exit(1);
}

const rawText = fs.readFileSync(evaPath, 'utf8');
const allLines = rawText.split('\n');
const lines = allLines.map((l, idx) => ({
    lineNum: idx,
    raw: l,
    clean: l.replace(/[!*=%{}]/g, '').trim()
})).filter(l => !l.raw.startsWith('#') && !l.raw.startsWith('<') && l.clean.length > 0);

// Build a flat word array with positional metadata
const wordList = [];
lines.forEach(line => {
    const words = line.clean.split(/[\s.]+/).filter(w => w.length > 0);
    words.forEach(w => {
        wordList.push({
            word: w,
            lineNum: line.lineNum
        });
    });
});

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  DAI ANCHOR PARSER — Graves 2025 Semantic Anchor Method         ║');
console.log('║  Searching for trigram anchor: "' + CONFIG.ANCHOR + '"                           ║');
console.log('╚══════════════════════════════════════════════════════════════════╝\n');

console.log(`Total words in corpus: ${wordList.length}`);
console.log(`Context window size:   ±${CONFIG.WINDOW_SIZE} words`);
console.log(`Match mode:            ${CONFIG.MATCH_MODE}\n`);

// ─────────────────────────────────────────────────────────────────────────────
// ANCHOR DETECTION
// ─────────────────────────────────────────────────────────────────────────────

function matchesAnchor(word, anchor, mode) {
    if (mode === 'exact') return word === anchor;
    if (mode === 'substring') return word.includes(anchor) && word !== anchor;
    // 'both'
    return word.includes(anchor);
}

// Find all anchor positions
const anchorHits = [];
wordList.forEach((entry, idx) => {
    if (matchesAnchor(entry.word, CONFIG.ANCHOR, CONFIG.MATCH_MODE)) {
        anchorHits.push({
            index: idx,
            word: entry.word,
            lineNum: entry.lineNum,
            isExact: entry.word === CONFIG.ANCHOR,
            isSubstring: entry.word.includes(CONFIG.ANCHOR) && entry.word !== CONFIG.ANCHOR
        });
    }
});

console.log(`=== ANCHOR DETECTION: "${CONFIG.ANCHOR}" ===`);
console.log(`Total occurrences found:     ${anchorHits.length}`);

// Break down by match type
const exactCount = anchorHits.filter(h => h.isExact).length;
const substringCount = anchorHits.filter(h => h.isSubstring).length;
console.log(`  Exact matches ("${CONFIG.ANCHOR}"):     ${exactCount}`);
console.log(`  Substring matches:         ${substringCount}`);

// Show which words contain 'dai'
const daiWords = {};
anchorHits.forEach(h => {
    daiWords[h.word] = (daiWords[h.word] || 0) + 1;
});
console.log(`\nWords containing "${CONFIG.ANCHOR}":`);
Object.entries(daiWords).sort((a, b) => b[1] - a[1]).forEach(([w, c]) => {
    console.log(`  ${w.padEnd(15)} ${c} occurrences`);
});

// ─────────────────────────────────────────────────────────────────────────────
// CONTEXT WINDOW EXTRACTION
// ─────────────────────────────────────────────────────────────────────────────

console.log(`\n=== CONTEXT WINDOW ANALYSIS (±${CONFIG.WINDOW_SIZE} words) ===`);

const beforeFreq = {};  // Words appearing BEFORE 'dai'
const afterFreq = {};   // Words appearing AFTER 'dai'
const pairFreq = {};    // Bigrams containing 'dai'

anchorHits.forEach(hit => {
    // Extract preceding context
    for (let offset = 1; offset <= CONFIG.WINDOW_SIZE; offset++) {
        const prevIdx = hit.index - offset;
        if (prevIdx >= 0) {
            const prevWord = wordList[prevIdx].word;
            const key = `[-${offset}] ${prevWord}`;
            beforeFreq[prevWord] = (beforeFreq[prevWord] || 0) + 1;
        }
    }

    // Extract following context
    for (let offset = 1; offset <= CONFIG.WINDOW_SIZE; offset++) {
        const nextIdx = hit.index + offset;
        if (nextIdx < wordList.length) {
            const nextWord = wordList[nextIdx].word;
            afterFreq[nextWord] = (afterFreq[nextWord] || 0) + 1;
        }
    }

    // Bigram: word immediately before + anchor
    if (hit.index > 0) {
        const prev = wordList[hit.index - 1].word;
        pairFreq[`${prev} → ${hit.word}`] = (pairFreq[`${prev} → ${hit.word}`] || 0) + 1;
    }
    // Bigram: anchor + word immediately after
    if (hit.index < wordList.length - 1) {
        const next = wordList[hit.index + 1].word;
        pairFreq[`${hit.word} → ${next}`] = (pairFreq[`${hit.word} → ${next}`] || 0) + 1;
    }
});

console.log(`\nTop ${CONFIG.TOP_N} words appearing BEFORE "${CONFIG.ANCHOR}":`);
Object.entries(beforeFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, CONFIG.TOP_N)
    .forEach(([w, c]) => {
        const bar = '█'.repeat(Math.min(Math.round(c / 5), 40));
        console.log(`  ${w.padEnd(15)} ${String(c).padStart(4)} ${bar}`);
    });

console.log(`\nTop ${CONFIG.TOP_N} words appearing AFTER "${CONFIG.ANCHOR}":`);
Object.entries(afterFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, CONFIG.TOP_N)
    .forEach(([w, c]) => {
        const bar = '█'.repeat(Math.min(Math.round(c / 5), 40));
        console.log(`  ${w.padEnd(15)} ${String(c).padStart(4)} ${bar}`);
    });

console.log(`\nTop ${CONFIG.TOP_N} bigram pairs involving "${CONFIG.ANCHOR}":`);
Object.entries(pairFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, CONFIG.TOP_N)
    .forEach(([pair, c]) => {
        console.log(`  ${pair.padEnd(30)} ${c}`);
    });

// ─────────────────────────────────────────────────────────────────────────────
// SECTION-BASED ANALYSIS
// ─────────────────────────────────────────────────────────────────────────────

console.log('\n=== SECTION-BASED DISTRIBUTION ===');
console.log('How does "' + CONFIG.ANCHOR + '" distribute across manuscript sections?\n');

function getSection(lineNum) {
    for (const [name, range] of Object.entries(CONFIG.SECTIONS)) {
        if (lineNum >= range.start && lineNum < range.end) return name;
    }
    return 'Unknown';
}

const sectionCounts = {};
const sectionContexts = {};

anchorHits.forEach(hit => {
    const section = getSection(hit.lineNum);
    sectionCounts[section] = (sectionCounts[section] || 0) + 1;

    if (!sectionContexts[section]) sectionContexts[section] = { before: {}, after: {} };

    // Track per-section context words
    for (let offset = 1; offset <= CONFIG.WINDOW_SIZE; offset++) {
        const prevIdx = hit.index - offset;
        if (prevIdx >= 0) {
            const w = wordList[prevIdx].word;
            sectionContexts[section].before[w] = (sectionContexts[section].before[w] || 0) + 1;
        }
        const nextIdx = hit.index + offset;
        if (nextIdx < wordList.length) {
            const w = wordList[nextIdx].word;
            sectionContexts[section].after[w] = (sectionContexts[section].after[w] || 0) + 1;
        }
    }
});

// Compute total words per section for density calculation
const sectionWordCounts = {};
wordList.forEach(entry => {
    const section = getSection(entry.lineNum);
    sectionWordCounts[section] = (sectionWordCounts[section] || 0) + 1;
});

Object.entries(CONFIG.SECTIONS).forEach(([name]) => {
    const count = sectionCounts[name] || 0;
    const totalWords = sectionWordCounts[name] || 1;
    const density = (count / totalWords * 1000).toFixed(2);
    const bar = '█'.repeat(Math.min(Math.round(count / 10), 50));
    console.log(`${name}`);
    console.log(`  Occurrences: ${count}  |  Density: ${density}/1000 words  ${bar}`);

    // Show top 5 context words specific to this section
    if (sectionContexts[name]) {
        const topBefore = Object.entries(sectionContexts[name].before)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([w, c]) => `${w}(${c})`);
        const topAfter = Object.entries(sectionContexts[name].after)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([w, c]) => `${w}(${c})`);

        if (topBefore.length > 0) console.log(`  Top before: ${topBefore.join(', ')}`);
        if (topAfter.length > 0)  console.log(`  Top after:  ${topAfter.join(', ')}`);
    }
    console.log('');
});

// ─────────────────────────────────────────────────────────────────────────────
// SYNTACTIC PATTERN DETECTION
// ─────────────────────────────────────────────────────────────────────────────

console.log('=== SYNTACTIC PATTERN DETECTION ===');
console.log('Searching for recurring structural patterns around "' + CONFIG.ANCHOR + '"...\n');

// Extract 3-word windows centered on anchor: [prev, ANCHOR, next]
const trigramPatterns = {};
anchorHits.forEach(hit => {
    if (hit.index > 0 && hit.index < wordList.length - 1) {
        const prev = wordList[hit.index - 1].word;
        const next = wordList[hit.index + 1].word;
        const pattern = `${prev} [${hit.word}] ${next}`;
        trigramPatterns[pattern] = (trigramPatterns[pattern] || 0) + 1;
    }
});

console.log(`Recurring 3-word patterns (count ≥ ${CONFIG.MIN_COOCCURRENCE}):`);
const significantPatterns = Object.entries(trigramPatterns)
    .filter(([, c]) => c >= CONFIG.MIN_COOCCURRENCE)
    .sort((a, b) => b[1] - a[1]);

if (significantPatterns.length === 0) {
    console.log('  No patterns found above threshold. Try lowering MIN_COOCCURRENCE.');
} else {
    significantPatterns.forEach(([pattern, c]) => {
        console.log(`  ${pattern.padEnd(40)} ${c}`);
    });
}

// 5-word window patterns (abstract: classify words by first character or suffix)
console.log('\n\nAbstract pattern fingerprints (word → initial+suffix class):');

function classifyWord(w) {
    // Simple structural classifier for pattern detection
    const prefix = w.slice(0, 2);
    const suffix = w.slice(-2);
    const len = w.length <= 3 ? 'S' : w.length <= 5 ? 'M' : 'L';
    return `${prefix}..${suffix}[${len}]`;
}

const abstractPatterns = {};
anchorHits.forEach(hit => {
    if (hit.index >= 2 && hit.index < wordList.length - 2) {
        const p2 = classifyWord(wordList[hit.index - 2].word);
        const p1 = classifyWord(wordList[hit.index - 1].word);
        const n1 = classifyWord(wordList[hit.index + 1].word);
        const n2 = classifyWord(wordList[hit.index + 2].word);
        const pattern = `${p2} ${p1} [DAI] ${n1} ${n2}`;
        abstractPatterns[pattern] = (abstractPatterns[pattern] || 0) + 1;
    }
});

const topAbstract = Object.entries(abstractPatterns)
    .filter(([, c]) => c >= 2)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15);

if (topAbstract.length > 0) {
    topAbstract.forEach(([pat, c]) => {
        console.log(`  ${pat.padEnd(60)} ${c}`);
    });
} else {
    console.log('  No recurring abstract patterns found (threshold: 2).');
}

// ─────────────────────────────────────────────────────────────────────────────
// SAMPLE CONCORDANCE LINES
// ─────────────────────────────────────────────────────────────────────────────

console.log('\n=== SAMPLE CONCORDANCE LINES (first 15 hits) ===');
console.log('Showing ±' + CONFIG.WINDOW_SIZE + ' words of context around each anchor.\n');

anchorHits.slice(0, 15).forEach((hit, idx) => {
    const startIdx = Math.max(0, hit.index - CONFIG.WINDOW_SIZE);
    const endIdx = Math.min(wordList.length - 1, hit.index + CONFIG.WINDOW_SIZE);

    const contextWords = [];
    for (let i = startIdx; i <= endIdx; i++) {
        if (i === hit.index) {
            contextWords.push(`>>>${wordList[i].word}<<<`);
        } else {
            contextWords.push(wordList[i].word);
        }
    }

    const section = getSection(hit.lineNum);
    console.log(`  [${String(idx + 1).padStart(2)}] Line ${String(hit.lineNum + 1).padStart(4)} (${section}):`);
    console.log(`       ${contextWords.join(' ')}\n`);
});

// ─────────────────────────────────────────────────────────────────────────────
// CONCLUSION
// ─────────────────────────────────────────────────────────────────────────────

console.log('=== CONCLUSION ===');
const totalDensity = (anchorHits.length / wordList.length * 1000).toFixed(2);
console.log(`The trigram "${CONFIG.ANCHOR}" appears ${anchorHits.length} times across ${wordList.length} words.`);
console.log(`Global density: ${totalDensity} per 1000 words.\n`);

// Check if density varies significantly by section
const densities = Object.entries(CONFIG.SECTIONS).map(([name]) => {
    const count = sectionCounts[name] || 0;
    const total = sectionWordCounts[name] || 1;
    return { name, density: count / total * 1000 };
});

const maxDensity = densities.reduce((m, d) => d.density > m.density ? d : m, densities[0]);
const minDensity = densities.reduce((m, d) => d.density < m.density ? d : m, densities[0]);

if (maxDensity.density > minDensity.density * 2) {
    console.log(`⚠  SIGNIFICANT DENSITY VARIATION detected across sections:`);
    console.log(`   Highest: ${maxDensity.name} (${maxDensity.density.toFixed(2)}/1000)`);
    console.log(`   Lowest:  ${minDensity.name} (${minDensity.density.toFixed(2)}/1000)`);
    console.log(`   This supports Graves's theory that "${CONFIG.ANCHOR}" functions differently`);
    console.log(`   in different content domains (botanical vs. astronomical vs. recipe).`);
} else {
    console.log(`   Density is relatively uniform across sections.`);
    console.log(`   "${CONFIG.ANCHOR}" may serve a grammatical rather than domain-specific role.`);
}
