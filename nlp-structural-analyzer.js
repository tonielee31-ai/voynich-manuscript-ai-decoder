const fs = require('fs');
const path = require('path');

// =============================================================================
// NLP STRUCTURAL ANALYZER — Inspired by brianmg (2025)
// =============================================================================
// Based on: brianmg/voynich-nlp-analysis (GitHub, May 2025)
// Modern NLP structural analysis WITHOUT external dependencies.
//
// Instead of SBERT embeddings (which require Python/transformers), we implement
// equivalent techniques purely in Node.js:
//
// 1. Suffix-stripping root extraction (like brianmg's preprocessing)
// 2. TF-IDF based word clustering (approximates SBERT spatial similarity)
// 3. Markov transition analysis (bigram state transitions between clusters)
// 4. POS-like role inference (function words vs content words)
// 5. Section-based structural mapping (botanical, biological, etc.)
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// STEP 1: SUFFIX STRIPPING (Root Extraction)
// Common Voynich "suffixes" that appear to be morphological variants
// Stripping reveals candidate root forms for clustering.
// ─────────────────────────────────────────────────────────────────────────────

const SUFFIXES = [
    'aiin', 'ain', 'iin', 'in', 'an', 'am',      // -aiin family
    'edy', 'ody', 'ady', 'dy',                     // -dy family
    'eey', 'oey', 'ey',                            // -ey family
    'airy', 'ary', 'ory', 'iry',                   // -ry family
    'chy', 'shy', 'thy',                            // -hy family
    'ol', 'al', 'or', 'ar', 'os', 'es',           // single suffix
    'y',                                            // bare -y
];

// Sort by length descending for greedy matching
const SORTED_SUFFIXES = [...SUFFIXES].sort((a, b) => b.length - a.length);

function stripSuffix(word) {
    const clean = word.replace(/[!*=%{}]/g, '').toLowerCase();
    if (clean.length <= 2) return { root: clean, suffix: '' };

    for (const suf of SORTED_SUFFIXES) {
        if (clean.endsWith(suf) && clean.length > suf.length + 1) {
            return { root: clean.slice(0, -suf.length), suffix: suf };
        }
    }
    return { root: clean, suffix: '' };
}


// ─────────────────────────────────────────────────────────────────────────────
// STEP 2: WORD FREQUENCY & TF-IDF COMPUTATION (for clustering)
// ─────────────────────────────────────────────────────────────────────────────

function buildCorpusStats(lines) {
    const globalFreq = {};
    const rootFreq = {};
    const suffixFreq = {};
    const wordToRoot = {};
    const rootToWords = {};
    const lineData = [];

    for (let i = 0; i < lines.length; i++) {
        const words = lines[i].replace(/<[^>]+>/g, '').replace(/[!*=%{}]/g, '')
            .split(/[\s.]+/).filter(w => w.length > 0);

        const lineWords = [];
        for (const word of words) {
            const lower = word.toLowerCase();
            globalFreq[lower] = (globalFreq[lower] || 0) + 1;

            const { root, suffix } = stripSuffix(lower);
            rootFreq[root] = (rootFreq[root] || 0) + 1;
            if (suffix) suffixFreq[suffix] = (suffixFreq[suffix] || 0) + 1;

            wordToRoot[lower] = root;
            if (!rootToWords[root]) rootToWords[root] = new Set();
            rootToWords[root].add(lower);

            lineWords.push({ word: lower, root, suffix });
        }
        lineData.push(lineWords);
    }

    return { globalFreq, rootFreq, suffixFreq, wordToRoot, rootToWords, lineData };
}


// ─────────────────────────────────────────────────────────────────────────────
// STEP 3: K-MEANS STYLE CLUSTERING (without SBERT)
// Uses character n-gram features instead of embeddings.
// Each root is represented as a vector of character bigram/trigram frequencies.
// Then we cluster via iterative k-means.
// ─────────────────────────────────────────────────────────────────────────────

function charNgramVector(word, n = 2) {
    const vec = {};
    const padded = '^' + word + '$'; // Start/end markers
    for (let i = 0; i <= padded.length - n; i++) {
        const ng = padded.slice(i, i + n);
        vec[ng] = (vec[ng] || 0) + 1;
    }
    return vec;
}

function cosineSimilarity(vecA, vecB) {
    const allKeys = new Set([...Object.keys(vecA), ...Object.keys(vecB)]);
    let dotProduct = 0, normA = 0, normB = 0;
    for (const key of allKeys) {
        const a = vecA[key] || 0;
        const b = vecB[key] || 0;
        dotProduct += a * b;
        normA += a * a;
        normB += b * b;
    }
    return (normA > 0 && normB > 0) ? dotProduct / (Math.sqrt(normA) * Math.sqrt(normB)) : 0;
}

function kMeansCluster(roots, k = 12, maxIter = 15) {
    // Build feature vectors for each root
    const vectors = {};
    const rootList = Object.keys(roots);

    for (const root of rootList) {
        vectors[root] = charNgramVector(root);
    }

    // Initialize centroids: pick k roots spread across frequency spectrum
    const sorted = rootList.sort((a, b) => roots[b] - roots[a]);
    const step = Math.max(1, Math.floor(sorted.length / k));
    let centroids = [];
    for (let i = 0; i < k; i++) {
        const idx = Math.min(i * step, sorted.length - 1);
        centroids.push({ ...vectors[sorted[idx]] });
    }

    let assignments = new Array(rootList.length).fill(0);

    for (let iter = 0; iter < maxIter; iter++) {
        // Assign each root to nearest centroid
        const newAssignments = [];
        for (let i = 0; i < rootList.length; i++) {
            let bestCluster = 0;
            let bestSim = -1;
            for (let c = 0; c < k; c++) {
                const sim = cosineSimilarity(vectors[rootList[i]], centroids[c]);
                if (sim > bestSim) {
                    bestSim = sim;
                    bestCluster = c;
                }
            }
            newAssignments.push(bestCluster);
        }

        // Converged?
        let changed = 0;
        for (let i = 0; i < rootList.length; i++) {
            if (newAssignments[i] !== assignments[i]) changed++;
        }
        assignments = newAssignments;
        if (changed === 0) break;

        // Update centroids (average of cluster members)
        centroids = Array.from({ length: k }, () => ({}));
        const clusterSizes = new Array(k).fill(0);
        for (let i = 0; i < rootList.length; i++) {
            const c = assignments[i];
            clusterSizes[c]++;
            for (const [key, val] of Object.entries(vectors[rootList[i]])) {
                centroids[c][key] = (centroids[c][key] || 0) + val;
            }
        }
        for (let c = 0; c < k; c++) {
            if (clusterSizes[c] > 0) {
                for (const key of Object.keys(centroids[c])) {
                    centroids[c][key] /= clusterSizes[c];
                }
            }
        }
    }

    // Build cluster info
    const clusters = Array.from({ length: k }, () => []);
    for (let i = 0; i < rootList.length; i++) {
        clusters[assignments[i]].push({
            root: rootList[i],
            freq: roots[rootList[i]],
        });
    }

    // Sort each cluster by frequency
    for (const cluster of clusters) {
        cluster.sort((a, b) => b.freq - a.freq);
    }

    return clusters;
}


// ─────────────────────────────────────────────────────────────────────────────
// STEP 4: POS-LIKE ROLE INFERENCE
// Determine if a word behaves like a "function word" or "content word"
// based on frequency distribution, positional preferences, etc.
// ─────────────────────────────────────────────────────────────────────────────

function inferRoles(globalFreq, lineData) {
    const totalTokens = Object.values(globalFreq).reduce((s, v) => s + v, 0);
    const vocabSize = Object.keys(globalFreq).length;

    // Position tracking: how often does word appear at start/end of line?
    const positionStats = {};
    for (const lineWords of lineData) {
        if (lineWords.length === 0) continue;
        for (let p = 0; p < lineWords.length; p++) {
            const w = lineWords[p].word;
            if (!positionStats[w]) positionStats[w] = { start: 0, end: 0, total: 0 };
            positionStats[w].total++;
            if (p === 0) positionStats[w].start++;
            if (p === lineWords.length - 1) positionStats[w].end++;
        }
    }

    // Neighbor diversity: how many different words appear adjacent?
    const leftNeighbors = {};
    const rightNeighbors = {};
    for (const lineWords of lineData) {
        for (let p = 0; p < lineWords.length; p++) {
            const w = lineWords[p].word;
            if (!leftNeighbors[w]) leftNeighbors[w] = new Set();
            if (!rightNeighbors[w]) rightNeighbors[w] = new Set();
            if (p > 0) leftNeighbors[w].add(lineWords[p - 1].word);
            if (p < lineWords.length - 1) rightNeighbors[w].add(lineWords[p + 1].word);
        }
    }

    // Classify each word
    const roles = {};
    for (const [word, freq] of Object.entries(globalFreq)) {
        const relFreq = freq / totalTokens;
        const pos = positionStats[word] || { start: 0, end: 0, total: 0 };
        const leftDiv = (leftNeighbors[word] || new Set()).size;
        const rightDiv = (rightNeighbors[word] || new Set()).size;
        const avgDiv = (leftDiv + rightDiv) / 2;

        // Function words: very high frequency + high neighbor diversity
        // Content words: lower frequency + lower neighbor diversity
        // Punctuation-like: very short, appears at specific positions
        let role = 'content';

        if (relFreq > 0.01 && avgDiv > 20) {
            role = 'function';  // Like articles/prepositions
        } else if (relFreq > 0.005 && avgDiv > 15) {
            role = 'semi-function'; // Like common verbs/adjectives
        } else if (word.length <= 2 && relFreq > 0.002) {
            role = 'particle'; // Short function-like particles
        } else if (pos.start / Math.max(pos.total, 1) > 0.3 && freq > 5) {
            role = 'opening'; // Sentence/clause openers
        } else if (pos.end / Math.max(pos.total, 1) > 0.3 && freq > 5) {
            role = 'closing'; // Sentence closers
        }

        roles[word] = {
            role,
            freq,
            relFreq,
            startPct: (pos.start / Math.max(pos.total, 1) * 100),
            endPct: (pos.end / Math.max(pos.total, 1) * 100),
            leftDiversity: leftDiv,
            rightDiversity: rightDiv,
        };
    }

    return roles;
}


// ─────────────────────────────────────────────────────────────────────────────
// STEP 5: MARKOV TRANSITION ANALYSIS
// Build a transition matrix between word clusters.
// Natural language shows structured transitions (noun→verb, adj→noun).
// Random text shows uniform transitions.
// ─────────────────────────────────────────────────────────────────────────────

function buildTransitionMatrix(lineData, wordToCluster, numClusters) {
    // Matrix[i][j] = count of transitions from cluster i to cluster j
    const matrix = Array.from({ length: numClusters }, () => new Array(numClusters).fill(0));
    let totalTransitions = 0;

    for (const lineWords of lineData) {
        for (let p = 0; p < lineWords.length - 1; p++) {
            const from = wordToCluster[lineWords[p].root];
            const to = wordToCluster[lineWords[p + 1].root];
            if (from !== undefined && to !== undefined) {
                matrix[from][to]++;
                totalTransitions++;
            }
        }
    }

    // Normalize to probabilities
    const probMatrix = matrix.map(row => {
        const rowSum = row.reduce((s, v) => s + v, 0);
        return row.map(v => rowSum > 0 ? v / rowSum : 0);
    });

    // Calculate transition entropy (lower = more structured)
    let transitionEntropy = 0;
    for (const row of probMatrix) {
        for (const p of row) {
            if (p > 0) transitionEntropy -= p * Math.log2(p);
        }
    }
    transitionEntropy /= numClusters; // Average per-state entropy

    return { matrix, probMatrix, totalTransitions, transitionEntropy };
}


// ─────────────────────────────────────────────────────────────────────────────
// STEP 6: SECTION-BASED STRUCTURAL ANALYSIS
// Analyze how vocabulary and structure change across manuscript sections.
// ─────────────────────────────────────────────────────────────────────────────

const CONTENT_SECTIONS = [
    { start: 0,    end: 1600,  label: 'Herbal A (f1-f57)' },
    { start: 1600, end: 2000,  label: 'Pharmaceutical (f57v-f66r)' },
    { start: 2000, end: 2500,  label: 'Herbal B (f67r-f84v)' },
    { start: 2500, end: 3200,  label: 'Astronomical (f67r2-f73v)' },
    { start: 3200, end: 3800,  label: 'Cosmological (f75-f86v)' },
    { start: 3800, end: 4200,  label: 'Balneological (f75-f84v)' },
    { start: 4200, end: 4800,  label: 'Pharmaceutical B (f88r-f102v)' },
    { start: 4800, end: 5211,  label: 'Recipes/Stars (f103-f116)' },
];

function analyzeSection(sectionLines) {
    const words = [];
    for (const line of sectionLines) {
        const w = line.replace(/<[^>]+>/g, '').replace(/[!*=%{}]/g, '')
            .split(/[\s.]+/).filter(w => w.length > 0);
        words.push(...w);
    }

    const roots = {};
    for (const w of words) {
        const { root } = stripSuffix(w.toLowerCase());
        roots[root] = (roots[root] || 0) + 1;
    }

    const sortedRoots = Object.entries(roots).sort((a, b) => b[1] - a[1]);

    return {
        wordCount: words.length,
        vocabSize: new Set(words.map(w => w.toLowerCase())).size,
        rootCount: Object.keys(roots).length,
        topRoots: sortedRoots.slice(0, 10),
        avgWordLength: words.reduce((s, w) => s + w.length, 0) / Math.max(words.length, 1),
    };
}


// ─────────────────────────────────────────────────────────────────────────────
// MAIN EXECUTION
// ─────────────────────────────────────────────────────────────────────────────

const evaPath = path.join(__dirname, 'eva-takahashi.txt');
if (!fs.existsSync(evaPath)) {
    console.error('ERROR: eva-takahashi.txt not found in project directory');
    process.exit(1);
}

const rawText = fs.readFileSync(evaPath, 'utf8');
const lines = rawText.split('\n').filter(l => l.trim().length > 0 && !l.startsWith('#') && !l.startsWith('<'));

const args = process.argv.slice(2);
let outputFile = null;
for (const arg of args) {
    if (arg.startsWith('--output=')) outputFile = arg.split('=')[1];
}

let output = '';
function out(str) { console.log(str); output += str + '\n'; }

out('╔══════════════════════════════════════════════════════════════════════╗');
out('║  NLP STRUCTURAL ANALYZER — Inspired by brianmg (2025)               ║');
out('║  Root Extraction · K-Means Clustering · Markov Transitions           ║');
out('║  POS Inference · Section Structure Mapping                           ║');
out('╚══════════════════════════════════════════════════════════════════════╝\n');


// ── Build corpus stats ──────────────────────────────────────────────────

out('Building corpus statistics...');
const stats = buildCorpusStats(lines);

out(`Total lines:          ${lines.length}`);
out(`Total word tokens:    ${Object.values(stats.globalFreq).reduce((s, v) => s + v, 0)}`);
out(`Unique words:         ${Object.keys(stats.globalFreq).length}`);
out(`Unique roots:         ${Object.keys(stats.rootFreq).length}`);
out(`Suffix types found:   ${Object.keys(stats.suffixFreq).length}`);


// ════════════════════════════════════════════════════════════════════════
// ANALYSIS 1: SUFFIX MORPHOLOGY
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ ANALYSIS 1: SUFFIX MORPHOLOGY (Root Extraction)\n');

const sortedSuffixes = Object.entries(stats.suffixFreq).sort((a, b) => b[1] - a[1]);
out('Suffix'.padEnd(10) + 'Count'.padEnd(10) + 'Example words');
out('─'.repeat(72));

for (const [suf, count] of sortedSuffixes.slice(0, 15)) {
    // Find example words with this suffix
    const examples = [];
    for (const [word, root] of Object.entries(stats.wordToRoot)) {
        const { suffix } = stripSuffix(word);
        if (suffix === suf && examples.length < 4) {
            examples.push(word);
        }
    }
    out(`${('-' + suf).padEnd(10)}${String(count).padEnd(10)}${examples.join(', ')}`);
}

// Root family analysis
out('\n── Root Families (roots with most variants) ──\n');
const rootFamilies = Object.entries(stats.rootToWords)
    .map(([root, words]) => ({ root, variants: [...words], count: words.size }))
    .filter(rf => rf.count > 3)
    .sort((a, b) => b.count - a.count)
    .slice(0, 15);

out('Root'.padEnd(12) + 'Variants'.padEnd(8) + 'Forms');
out('─'.repeat(72));
for (const rf of rootFamilies) {
    out(`${rf.root.padEnd(12)}${String(rf.count).padEnd(8)}${rf.variants.slice(0, 6).join(', ')}`);
}


// ════════════════════════════════════════════════════════════════════════
// ANALYSIS 2: WORD CLUSTERING (K-Means on character n-gram vectors)
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ ANALYSIS 2: ROOT WORD CLUSTERING (K-Means, k=12)\n');

// Only cluster roots with freq >= 3 to reduce noise
const rootsForClustering = {};
for (const [root, freq] of Object.entries(stats.rootFreq)) {
    if (freq >= 3 && root.length >= 2) rootsForClustering[root] = freq;
}

out(`Roots eligible for clustering: ${Object.keys(rootsForClustering).length} (freq ≥ 3, len ≥ 2)`);

const clusters = kMeansCluster(rootsForClustering, 12, 20);

// Build word→cluster mapping
const wordToCluster = {};
for (let c = 0; c < clusters.length; c++) {
    for (const item of clusters[c]) {
        wordToCluster[item.root] = c;
    }
}

out('\nCluster  Size  Top roots');
out('─'.repeat(72));
for (let c = 0; c < clusters.length; c++) {
    if (clusters[c].length === 0) continue;
    const topRoots = clusters[c].slice(0, 6).map(item => `${item.root}(${item.freq})`);
    out(`  ${String(c).padEnd(6)} ${String(clusters[c].length).padEnd(6)}${topRoots.join(', ')}`);
}


// ════════════════════════════════════════════════════════════════════════
// ANALYSIS 3: POS-LIKE ROLE INFERENCE
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ ANALYSIS 3: POS-LIKE ROLE INFERENCE\n');

const roles = inferRoles(stats.globalFreq, stats.lineData);

const roleCounts = {};
for (const { role } of Object.values(roles)) {
    roleCounts[role] = (roleCounts[role] || 0) + 1;
}

out('Role classification distribution:');
out('─'.repeat(50));
for (const [role, count] of Object.entries(roleCounts).sort((a, b) => b[1] - a[1])) {
    out(`  ${role.padEnd(16)} ${String(count).padEnd(8)} (${(count / Object.keys(roles).length * 100).toFixed(1)}%)`);
}

out('\n── Function Words (most grammar-like) ──\n');
const functionWords = Object.entries(roles)
    .filter(([, r]) => r.role === 'function')
    .sort((a, b) => b[1].freq - a[1].freq)
    .slice(0, 15);

out('Word'.padEnd(15) + 'Freq'.padEnd(8) + 'Start%'.padEnd(10) + 'End%'.padEnd(10) + 'L-div'.padEnd(8) + 'R-div');
out('─'.repeat(60));
for (const [word, r] of functionWords) {
    out(`${word.padEnd(15)}${String(r.freq).padEnd(8)}${r.startPct.toFixed(1).padEnd(10)}${r.endPct.toFixed(1).padEnd(10)}${String(r.leftDiversity).padEnd(8)}${r.rightDiversity}`);
}

out('\n── Opening Words (frequent at line start) ──\n');
const openers = Object.entries(roles)
    .filter(([, r]) => r.role === 'opening')
    .sort((a, b) => b[1].startPct - a[1].startPct)
    .slice(0, 10);

for (const [word, r] of openers) {
    out(`  ${word.padEnd(15)} start: ${r.startPct.toFixed(1)}% | freq: ${r.freq}`);
}

out('\n── Closing Words (frequent at line end) ──\n');
const closers = Object.entries(roles)
    .filter(([, r]) => r.role === 'closing')
    .sort((a, b) => b[1].endPct - a[1].endPct)
    .slice(0, 10);

for (const [word, r] of closers) {
    out(`  ${word.padEnd(15)} end: ${r.endPct.toFixed(1)}% | freq: ${r.freq}`);
}


// ════════════════════════════════════════════════════════════════════════
// ANALYSIS 4: MARKOV TRANSITION MATRIX
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ ANALYSIS 4: MARKOV TRANSITION MATRIX (Cluster Transitions)\n');

const transition = buildTransitionMatrix(stats.lineData, wordToCluster, 12);

out(`Total transitions analyzed: ${transition.totalTransitions}`);
out(`Average transition entropy: ${transition.transitionEntropy.toFixed(4)} bits`);
out(`(Lower entropy = more structured transitions = more language-like)`);
out(`Natural language: ~2.0-3.0 | Random: ~3.58 (log2(12) for 12 clusters)\n`);

// Show strongest transitions
out('Strongest cluster transitions (highest probability):');
out('─'.repeat(50));
const topTransitions = [];
for (let i = 0; i < 12; i++) {
    for (let j = 0; j < 12; j++) {
        if (transition.probMatrix[i][j] > 0.1 && transition.matrix[i][j] > 20) {
            topTransitions.push({
                from: i, to: j,
                prob: transition.probMatrix[i][j],
                count: transition.matrix[i][j],
            });
        }
    }
}
topTransitions.sort((a, b) => b.prob - a.prob);
for (const t of topTransitions.slice(0, 15)) {
    const fromRoots = clusters[t.from]?.slice(0, 3).map(r => r.root).join(',') || '?';
    const toRoots = clusters[t.to]?.slice(0, 3).map(r => r.root).join(',') || '?';
    out(`  C${t.from}→C${t.to}  p=${t.prob.toFixed(3)}  n=${t.count}  [${fromRoots}] → [${toRoots}]`);
}

// Self-transition analysis (how often does a cluster follow itself?)
out('\n── Self-Transition Rates ──');
out('(High self-transition = words in this cluster appear in runs)\n');
for (let i = 0; i < 12; i++) {
    if (clusters[i].length === 0) continue;
    const selfRate = transition.probMatrix[i][i];
    const topRoot = clusters[i][0]?.root || '?';
    const bar = '█'.repeat(Math.round(selfRate * 40));
    out(`  C${String(i).padEnd(3)} ${topRoot.padEnd(10)} ${(selfRate * 100).toFixed(1).padEnd(8)}% ${bar}`);
}


// ════════════════════════════════════════════════════════════════════════
// ANALYSIS 5: SECTION-BASED STRUCTURAL MAPPING
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ ANALYSIS 5: SECTION-BASED VOCABULARY STRUCTURE\n');

out('Section'.padEnd(36) + 'Words'.padEnd(8) + 'Vocab'.padEnd(8) + 'Roots'.padEnd(8) + 'AvgLen');
out('─'.repeat(72));

const sectionData = [];
for (const section of CONTENT_SECTIONS) {
    const sectionLines = lines.slice(section.start, Math.min(section.end, lines.length));
    const analysis = analyzeSection(sectionLines);
    sectionData.push({ ...section, ...analysis });

    out(`${section.label.padEnd(36)}${String(analysis.wordCount).padEnd(8)}${String(analysis.vocabSize).padEnd(8)}${String(analysis.rootCount).padEnd(8)}${analysis.avgWordLength.toFixed(2)}`);
}

// Find section-distinctive roots (roots that appear mostly in one section)
out('\n── Section-Distinctive Roots ──\n');
out('(Roots that appear disproportionately in specific sections)\n');

const rootSectionFreq = {}; // root → { section: count }
for (let s = 0; s < CONTENT_SECTIONS.length; s++) {
    const sectionLines = lines.slice(CONTENT_SECTIONS[s].start, Math.min(CONTENT_SECTIONS[s].end, lines.length));
    for (const line of sectionLines) {
        const words = line.replace(/<[^>]+>/g, '').replace(/[!*=%{}]/g, '')
            .split(/[\s.]+/).filter(w => w.length > 0);
        for (const w of words) {
            const { root } = stripSuffix(w.toLowerCase());
            if (!rootSectionFreq[root]) rootSectionFreq[root] = new Array(CONTENT_SECTIONS.length).fill(0);
            rootSectionFreq[root][s]++;
        }
    }
}

for (let s = 0; s < CONTENT_SECTIONS.length; s++) {
    const distinctive = [];
    for (const [root, freqs] of Object.entries(rootSectionFreq)) {
        const total = freqs.reduce((sum, v) => sum + v, 0);
        if (total < 10) continue;
        const sectionPct = freqs[s] / total;
        if (sectionPct > 0.5) { // >50% in this section
            distinctive.push({ root, pct: sectionPct, count: freqs[s], total });
        }
    }
    distinctive.sort((a, b) => b.pct - a.pct);
    if (distinctive.length > 0) {
        const topDistinctive = distinctive.slice(0, 5).map(d => `${d.root}(${(d.pct * 100).toFixed(0)}%)`);
        out(`  ${CONTENT_SECTIONS[s].label.padEnd(36)} ${topDistinctive.join(', ')}`);
    }
}


// ════════════════════════════════════════════════════════════════════════
// OVERALL FINDINGS
// ════════════════════════════════════════════════════════════════════════

out('\n' + '═'.repeat(72));
out('\n█ OVERALL STRUCTURAL FINDINGS\n');

// Function-to-content word ratio
const funcCount = Object.values(roles).filter(r => r.role === 'function' || r.role === 'semi-function' || r.role === 'particle').length;
const contentCount = Object.values(roles).filter(r => r.role === 'content').length;
const fcRatio = funcCount / Math.max(contentCount, 1);

out(`Function-like words:      ${funcCount} (${(funcCount / Object.keys(roles).length * 100).toFixed(1)}%)`);
out(`Content-like words:       ${contentCount} (${(contentCount / Object.keys(roles).length * 100).toFixed(1)}%)`);
out(`Func/Content ratio:       ${fcRatio.toFixed(3)} ${fcRatio > 0.05 && fcRatio < 0.30 ? '✅ natural language range' : '⚠ unusual'}`);
out(`(Natural language: 0.05 - 0.25)`);

out(`\nRoot families (>3 variants): ${rootFamilies.length}`);
out(`Average variants per root:   ${(Object.values(stats.rootToWords).reduce((s, ws) => s + ws.size, 0) / Math.max(Object.keys(stats.rootToWords).length, 1)).toFixed(2)}`);
out(`This ${rootFamilies.length > 20 ? 'strongly suggests' : 'may suggest'} productive morphological suffixation.`);

out(`\nTransition entropy:          ${transition.transitionEntropy.toFixed(3)} bits`);
out(`Random baseline (12 clusters): ${Math.log2(12).toFixed(3)} bits`);
out(`Structured text shows lower transition entropy than random.`);
const structureRatio = transition.transitionEntropy / Math.log2(12);
if (structureRatio < 0.75) {
    out(`✅ Transition structure is ${((1 - structureRatio) * 100).toFixed(1)}% below random — STRONG structure.`);
} else if (structureRatio < 0.90) {
    out(`⚠  Transition structure is ${((1 - structureRatio) * 100).toFixed(1)}% below random — moderate structure.`);
} else {
    out(`❌ Transitions are near-random — weak syntactic structure.`);
}

// ── Output ──────────────────────────────────────────────────────────────

if (outputFile) {
    fs.writeFileSync(outputFile, output);
    console.log(`\nOutput written to ${outputFile}`);
}

out('\n=== NLP STRUCTURAL ANALYSIS COMPLETE ===');
out('Inspired by brianmg/voynich-nlp-analysis (GitHub, 2025)');
out('Use --output=file.txt to save results');
