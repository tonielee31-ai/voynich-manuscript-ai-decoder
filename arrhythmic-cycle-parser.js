const fs = require('fs');
const path = require('path');

// =============================================================================
// ARRHYTHMIC CYCLE PARSER — Burgos Córdova (2025)
// =============================================================================
// Based on "An Integral Framework for Translating the Voynich Manuscript:
// The EVA–Romance Lexicon, the Arrhythmic Principle, and a Complete Token Corpus"
// Published: Zenodo, Sept 2025 — David Aarón Burgos Córdova (Tec de Monterrey)
//
// KEY INSIGHT: Meaning only emerges when decoded EVA tokens are grouped into
// 3–4 word "arrhythmic cycles" that mirror medieval ritual/herbal formulae.
// Without rhythmic grouping, text collapses into incoherent lists.
// When grouped, recognizable micro-clauses appear: herba radix folia facit amen
//
// The framework achieves 78% functional micro-formulae in botanical folios
// with a 0.60 coherence threshold.
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// EVA → ROMANCE LEXICON (Codex EVA–Romance v2.0)
// Stable phonetic-syllabic correspondences mapped to Romance/Latin roots
// Source: Burgos Córdova's ~12,000 token lexicon (core subset)
// ─────────────────────────────────────────────────────────────────────────────

const EVA_ROMANCE_LEXICON = {
    // ── HIGH-FREQUENCY FUNCTION TOKENS ──
    'daiin':   { latin: 'amen',     italian: 'amen',      role: 'closing',    gloss: 'amen / so be it' },
    'aiin':    { latin: 'amen',     italian: 'amen',      role: 'closing',    gloss: 'amen / closing formula' },
    'ol':      { latin: 'cum',      italian: 'con',       role: 'prep',       gloss: 'with' },
    'or':      { latin: 'vel',      italian: 'o/oppure',  role: 'conj',       gloss: 'or' },
    'ar':      { latin: 'ad',       italian: 'a/al',      role: 'prep',       gloss: 'to / at' },
    'al':      { latin: 'alius',    italian: 'altro',     role: 'adj',        gloss: 'other' },
    'dar':     { latin: 'dare',     italian: 'dare',      role: 'verb',       gloss: 'to give' },
    'dal':     { latin: 'de illo',  italian: 'dal',       role: 'prep',       gloss: 'from the' },
    'dy':      { latin: 'dei',      italian: 'dei',       role: 'prep',       gloss: 'of the (pl.)' },
    'y':       { latin: 'et',       italian: 'e',         role: 'conj',       gloss: 'and' },
    's':       { latin: 'est',      italian: 'è',         role: 'verb',       gloss: 'is' },
    'ok':      { latin: 'hoc',      italian: 'qui',       role: 'pron',       gloss: 'this / here' },
    'oky':     { latin: 'id',       italian: 'ciò',       role: 'pron',       gloss: 'that / it' },
    'qo':      { latin: 'quo',      italian: 'dove',      role: 'adv',        gloss: 'where / whither' },

    // ── BOTANICAL / HERBAL TERMS ──
    'shedy':   { latin: 'herba',    italian: 'erba',      role: 'noun',       gloss: 'herb / plant' },
    'chedy':   { latin: 'radix',    italian: 'radice',    role: 'noun',       gloss: 'root' },
    'chol':    { latin: 'folia',    italian: 'foglia',    role: 'noun',       gloss: 'leaf / foliage' },
    'chor':    { latin: 'cor',      italian: 'cuore',     role: 'noun',       gloss: 'heart / core' },
    'shol':    { latin: 'sol',      italian: 'sole',      role: 'noun',       gloss: 'sun' },
    'sho':     { latin: 'suco',     italian: 'succo',     role: 'noun',       gloss: 'juice / sap' },
    'cho':     { latin: 'caulis',   italian: 'caule',     role: 'noun',       gloss: 'stem / stalk' },
    'shod':    { latin: 'semen',    italian: 'seme',      role: 'noun',       gloss: 'seed' },
    'shor':    { latin: 'soror',    italian: 'sorella',   role: 'noun',       gloss: 'sister (nun)' },
    'chey':    { latin: 'cortex',   italian: 'corteccia', role: 'noun',       gloss: 'bark / rind' },
    'shey':    { latin: 'species',  italian: 'spezie',    role: 'noun',       gloss: 'spice / kind' },
    'okaiin':  { latin: 'oleum',    italian: 'olio',      role: 'noun',       gloss: 'oil' },
    'otaiin':  { latin: 'aquam',    italian: 'acqua',     role: 'noun',       gloss: 'water' },
    'qokaiin': { latin: 'coquere',  italian: 'cuocere',   role: 'verb',       gloss: 'to cook / decoct' },
    'qokedy':  { latin: 'facit',    italian: 'fa/produce',role: 'verb',       gloss: 'makes / produces' },
    'qokeey':  { latin: 'coquat',   italian: 'cuocia',    role: 'verb',       gloss: 'cook (subj.)' },
    'qokeedy': { latin: 'conficit', italian: 'confeziona', role: 'verb',      gloss: 'prepares / compounds' },
    'dain':    { latin: 'dosis',    italian: 'dose',      role: 'noun',       gloss: 'dose / portion' },
    'dan':     { latin: 'datur',    italian: 'si dà',     role: 'verb',       gloss: 'is given' },
    'oteey':   { latin: 'unguentum',italian: 'unguento',  role: 'noun',       gloss: 'ointment / salve' },
    'oteos':   { latin: 'remedium', italian: 'rimedio',   role: 'noun',       gloss: 'remedy' },
    'chod':    { latin: 'calor',    italian: 'calore',    role: 'noun',       gloss: 'heat / warmth' },
    'chodaiin':{ latin: 'calorem',  italian: 'calore',    role: 'noun',       gloss: 'heat (acc.)' },
    'shodaiin':{ latin: 'sudorem',  italian: 'sudore',    role: 'noun',       gloss: 'sweat / perspiration' },
    'oksho':   { latin: 'hortus',   italian: 'orto',      role: 'noun',       gloss: 'garden' },
    'okcho':   { latin: 'oculus',   italian: 'occhio',    role: 'noun',       gloss: 'eye' },

    // ── MEDICAL / PHARMACEUTICAL ──
    'qokain':  { latin: 'recipe',   italian: 'ricetta',   role: 'verb',       gloss: 'take (recipe)' },
    'chy':     { latin: 'cura',     italian: 'cura',      role: 'noun',       gloss: 'cure / care' },
    'cthy':    { latin: 'cutis',    italian: 'cute',      role: 'noun',       gloss: 'skin' },
    'kos':     { latin: 'corpus',   italian: 'corpo',     role: 'noun',       gloss: 'body' },
    'kol':     { latin: 'collum',   italian: 'collo',     role: 'noun',       gloss: 'neck' },
    'kor':     { latin: 'color',    italian: 'colore',    role: 'noun',       gloss: 'color' },
    'kod':     { latin: 'codex',    italian: 'codice',    role: 'noun',       gloss: 'codex / book' },
    'dol':     { latin: 'dolor',    italian: 'dolore',    role: 'noun',       gloss: 'pain' },
    'dor':     { latin: 'donum',    italian: 'dono',      role: 'noun',       gloss: 'gift / preparation' },
    'lor':     { latin: 'illorum',  italian: 'loro',      role: 'pron',       gloss: 'their / them' },
    'por':     { latin: 'pro',      italian: 'per',       role: 'prep',       gloss: 'for' },
    'tos':     { latin: 'tussis',   italian: 'tosse',     role: 'noun',       gloss: 'cough' },
    'tal':     { latin: 'talis',    italian: 'tale',      role: 'adj',        gloss: 'such / of this kind' },
    'sol':     { latin: 'sol',      italian: 'sole',      role: 'noun',       gloss: 'sun' },
    'sal':     { latin: 'sal',      italian: 'sale',      role: 'noun',       gloss: 'salt' },
    'mel':     { latin: 'mel',      italian: 'miele',     role: 'noun',       gloss: 'honey' },
    'ros':     { latin: 'ros/rosa', italian: 'rosa/rugiada', role: 'noun',    gloss: 'rose / dew' },

    // ── ASTRONOMICAL / COSMOLOGICAL ──
    'otol':    { latin: 'stella',   italian: 'stella',    role: 'noun',       gloss: 'star' },
    'otal':    { latin: 'caelum',   italian: 'cielo',     role: 'noun',       gloss: 'sky / heaven' },
    'okal':    { latin: 'luna',     italian: 'luna',      role: 'noun',       gloss: 'moon' },
    'okol':    { latin: 'orbis',    italian: 'orbe',      role: 'noun',       gloss: 'orb / sphere' },
    'otan':    { latin: 'tempus',   italian: 'tempo',     role: 'noun',       gloss: 'time / season' },
    'odar':    { latin: 'astrum',   italian: 'astro',     role: 'noun',       gloss: 'star / heavenly body' },
    'otor':    { latin: 'aurora',   italian: 'aurora',    role: 'noun',       gloss: 'dawn' },
    'odal':    { latin: 'occidens', italian: 'occidente', role: 'noun',       gloss: 'west / setting' },

    // ── BATHING / BALNEOLOGICAL ──
    'otol':    { latin: 'balneum',  italian: 'bagno',     role: 'noun',       gloss: 'bath' },
    'orain':   { latin: 'ablutio',  italian: 'abluzione', role: 'noun',       gloss: 'washing / ablution' },
    'shodary': { latin: 'sudarium', italian: 'sudario',   role: 'noun',       gloss: 'sweat cloth' },

    // ── VERB FORMS / ACTIONS ──
    'dary':    { latin: 'datur',    italian: 'è dato',    role: 'verb',       gloss: 'is given' },
    'chary':   { latin: 'curatur',  italian: 'si cura',   role: 'verb',       gloss: 'is cured' },
    'shary':   { latin: 'sanatur',  italian: 'si sana',   role: 'verb',       gloss: 'is healed' },
    'oldy':    { latin: 'oleat',    italian: 'olia',      role: 'verb',       gloss: 'anoint / oil' },
    'sholdy':  { latin: 'solvit',   italian: 'dissolve',  role: 'verb',       gloss: 'dissolves' },
    'chodairy':{ latin: 'coagulat', italian: 'coagula',   role: 'verb',       gloss: 'coagulates' },

    // ── ADJECTIVE / DESCRIPTIVE ──
    'okey':    { latin: 'bonus',    italian: 'buono',     role: 'adj',        gloss: 'good' },
    'ochy':    { latin: 'rubeus',   italian: 'rosso',     role: 'adj',        gloss: 'red' },
    'oty':     { latin: 'albus',    italian: 'bianco',    role: 'adj',        gloss: 'white' },
    'oky':     { latin: 'siccus',   italian: 'secco',     role: 'adj',        gloss: 'dry' },
    'shy':     { latin: 'humidus',  italian: 'umido',     role: 'adj',        gloss: 'wet / moist' },
    'kal':     { latin: 'calidus',  italian: 'caldo',     role: 'adj',        gloss: 'hot / warm' },

    // ── CONNECTORS & MORPHOLOGICAL VARIANTS ──
    'oiin':    { latin: '-onis',    italian: '-one',      role: 'suffix',     gloss: 'augmentative suffix' },
    'aiir':    { latin: '-aris',    italian: '-are',      role: 'suffix',     gloss: 'verbal suffix' },
    'airy':    { latin: '-arius',   italian: '-ario',     role: 'suffix',     gloss: 'agent suffix' },
    'iin':     { latin: '-inum',    italian: '-ino',      role: 'suffix',     gloss: 'diminutive suffix' },
};

// All lexicon keys sorted by length (longest first for greedy matching)
const LEXICON_KEYS = Object.keys(EVA_ROMANCE_LEXICON)
    .sort((a, b) => b.length - a.length);


// ─────────────────────────────────────────────────────────────────────────────
// ARRHYTHMIC CYCLE ENGINE
// Groups translated tokens into 3-4 word "rhythmic windows" and scores
// each window for coherence as a medieval micro-formula.
// ─────────────────────────────────────────────────────────────────────────────

// Role-based coherence patterns (what sequences "make sense" in herbal texts)
const COHERENT_PATTERNS = [
    // noun-noun-verb-closing: "herba radix facit amen"
    ['noun', 'noun', 'verb', 'closing'],
    ['noun', 'noun', 'verb'],
    ['noun', 'noun', 'noun'],
    // prep-noun-verb: "cum herba coquat"
    ['prep', 'noun', 'verb'],
    ['prep', 'noun', 'noun'],
    // noun-adj-verb: "radix sicca facit"
    ['noun', 'adj', 'verb'],
    // verb-noun-prep: "dare herba cum"
    ['verb', 'noun', 'prep'],
    ['verb', 'noun', 'noun'],
    ['verb', 'noun', 'closing'],
    // noun-verb-closing: "erba facit amen"
    ['noun', 'verb', 'closing'],
    // conj-noun-verb: "et herba facit"
    ['conj', 'noun', 'verb'],
    ['conj', 'noun', 'noun'],
    // noun-prep-noun: "radice con acqua"
    ['noun', 'prep', 'noun'],
    // adj-noun-verb: "buono rimedio facit"
    ['adj', 'noun', 'verb'],
    ['adj', 'noun', 'noun'],
];

// Score a cycle (window of translated tokens) for coherence
function scoreCycle(tokens) {
    if (tokens.length < 2) return { score: 0, pattern: 'too-short' };

    const roles = tokens.map(t => t.role || 'unknown');
    let bestScore = 0;
    let bestPattern = 'none';

    // Check against known coherent patterns
    for (const pattern of COHERENT_PATTERNS) {
        if (pattern.length > roles.length) continue;

        // Sliding window matching within the cycle
        for (let offset = 0; offset <= roles.length - pattern.length; offset++) {
            let matches = 0;
            for (let j = 0; j < pattern.length; j++) {
                if (roles[offset + j] === pattern[j]) matches++;
            }
            const matchRatio = matches / pattern.length;
            if (matchRatio > bestScore) {
                bestScore = matchRatio;
                bestPattern = pattern.join('-');
            }
        }
    }

    // Bonus: semantic domain coherence (all tokens from same domain?)
    const domains = new Set();
    for (const t of tokens) {
        if (t.latin) {
            if (['herba', 'radix', 'folia', 'semen', 'cortex', 'flos', 'caulis', 'suco'].some(d => t.latin.includes(d))) {
                domains.add('botanical');
            }
            if (['balneum', 'aquam', 'sudorem', 'ablutio', 'cutis'].some(d => t.latin.includes(d))) {
                domains.add('bathing');
            }
            if (['stella', 'luna', 'sol', 'caelum', 'astrum'].some(d => t.latin.includes(d))) {
                domains.add('astro');
            }
            if (['recipe', 'dosis', 'cura', 'remedium', 'coquere'].some(d => t.latin.includes(d))) {
                domains.add('medical');
            }
        }
    }
    // If all tokens share a domain, bonus coherence
    if (domains.size === 1 && tokens.length >= 2) bestScore += 0.15;

    return { score: Math.min(1.0, bestScore), pattern: bestPattern };
}


// ─────────────────────────────────────────────────────────────────────────────
// LINE PARSER: Translate EVA line → tokens → cycles → coherence scores
// ─────────────────────────────────────────────────────────────────────────────

function translateWord(evaWord) {
    const clean = evaWord.replace(/[!*=%{}]/g, '');
    if (clean.length === 0) return null;

    // Direct lexicon match (exact)
    if (EVA_ROMANCE_LEXICON[clean]) {
        return { ...EVA_ROMANCE_LEXICON[clean], eva: clean, matchType: 'exact' };
    }

    // Greedy longest-prefix match
    for (const key of LEXICON_KEYS) {
        if (clean.startsWith(key)) {
            const remainder = clean.slice(key.length);
            const entry = EVA_ROMANCE_LEXICON[key];
            // Check if remainder is a known suffix
            if (remainder.length === 0) {
                return { ...entry, eva: clean, matchType: 'exact' };
            }
            if (EVA_ROMANCE_LEXICON[remainder]) {
                const suffEntry = EVA_ROMANCE_LEXICON[remainder];
                return {
                    latin: entry.latin + suffEntry.latin,
                    italian: entry.italian + suffEntry.italian,
                    role: entry.role,
                    gloss: entry.gloss + ' + ' + suffEntry.gloss,
                    eva: clean,
                    matchType: 'compound'
                };
            }
            return {
                ...entry,
                latin: entry.latin + '(' + remainder + ')',
                italian: entry.italian + '(' + remainder + ')',
                eva: clean,
                matchType: 'partial'
            };
        }
    }

    // No match — return as unknown
    return { latin: clean, italian: clean, role: 'unknown', gloss: '?', eva: clean, matchType: 'none' };
}

function parseLine(evaLine, lineIndex) {
    const words = evaLine.replace(/<[^>]+>/g, '').trim()
        .split(/[\s.]+/)
        .filter(w => w.length > 0 && !w.startsWith('<'));

    if (words.length === 0) return null;

    // Step 1: Translate each word
    const tokens = words.map(w => translateWord(w)).filter(t => t !== null);

    // Step 2: Group into arrhythmic cycles (windows of 3-4 tokens)
    const cycles = [];
    for (let windowSize = 4; windowSize >= 3; windowSize--) {
        for (let i = 0; i <= tokens.length - windowSize; i++) {
            const window = tokens.slice(i, i + windowSize);
            const cycleScore = scoreCycle(window);
            if (cycleScore.score >= 0.50) { // Coherence threshold
                cycles.push({
                    tokens: window,
                    start: i,
                    end: i + windowSize,
                    score: cycleScore.score,
                    pattern: cycleScore.pattern,
                    latin: window.map(t => t.latin).join(' '),
                    italian: window.map(t => t.italian).join(' '),
                    gloss: window.map(t => t.gloss).join(' | '),
                });
            }
        }
    }

    // Sort cycles by score, remove overlapping (keep best)
    cycles.sort((a, b) => b.score - a.score);
    const usedPositions = new Set();
    const bestCycles = [];
    for (const cycle of cycles) {
        let overlaps = false;
        for (let p = cycle.start; p < cycle.end; p++) {
            if (usedPositions.has(p)) { overlaps = true; break; }
        }
        if (!overlaps) {
            bestCycles.push(cycle);
            for (let p = cycle.start; p < cycle.end; p++) usedPositions.add(p);
        }
    }

    // Full line translation
    const fullLatin = tokens.map(t => t.latin).join(' ');
    const fullItalian = tokens.map(t => t.italian).join(' ');

    // Calculate line-level coherence
    const matchedTokens = tokens.filter(t => t.matchType === 'exact' || t.matchType === 'compound').length;
    const lineCoherence = matchedTokens / Math.max(tokens.length, 1);

    return {
        lineIndex,
        eva: evaLine.trim(),
        tokens,
        cycles: bestCycles,
        fullLatin,
        fullItalian,
        coherence: lineCoherence,
        lexiconHits: matchedTokens,
        totalWords: tokens.length,
    };
}


// ─────────────────────────────────────────────────────────────────────────────
// NEGATIVE CONTROL: Shuffle test (Burgos Córdova's validation method)
// If meaning depends on sequential order, shuffled versions should score
// below the coherence threshold.
// ─────────────────────────────────────────────────────────────────────────────

function shuffleArray(arr) {
    const shuffled = [...arr];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

function negativeControlTest(tokens, trials = 50) {
    // Score the original order
    let originalCoherentCycles = 0;
    for (let windowSize = 4; windowSize >= 3; windowSize--) {
        for (let i = 0; i <= tokens.length - windowSize; i++) {
            const window = tokens.slice(i, i + windowSize);
            const s = scoreCycle(window);
            if (s.score >= 0.50) originalCoherentCycles++;
        }
    }

    // Score shuffled versions
    let shuffledTotal = 0;
    for (let t = 0; t < trials; t++) {
        const shuffled = shuffleArray(tokens);
        let shuffledCycles = 0;
        for (let windowSize = 4; windowSize >= 3; windowSize--) {
            for (let i = 0; i <= shuffled.length - windowSize; i++) {
                const window = shuffled.slice(i, i + windowSize);
                const s = scoreCycle(window);
                if (s.score >= 0.50) shuffledCycles++;
            }
        }
        shuffledTotal += shuffledCycles;
    }

    const avgShuffled = shuffledTotal / trials;
    return {
        original: originalCoherentCycles,
        shuffledAvg: avgShuffled,
        ratio: avgShuffled > 0 ? originalCoherentCycles / avgShuffled : Infinity,
        meaningful: originalCoherentCycles > avgShuffled * 1.5,
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

const text = fs.readFileSync(evaPath, 'utf8');
const lines = text.split('\n').filter(l => l.trim().length > 0 && !l.startsWith('#') && !l.startsWith('<'));

// Parse CLI arguments
const args = process.argv.slice(2);
let startLine = 0;
let numLines = 30;
let fullRun = false;
let outputFile = null;
let showDetail = false;

for (const arg of args) {
    if (arg.startsWith('--start=')) startLine = parseInt(arg.split('=')[1]) || 0;
    else if (arg.startsWith('--lines=')) numLines = parseInt(arg.split('=')[1]) || 30;
    else if (arg === '--full') fullRun = true;
    else if (arg.startsWith('--output=')) outputFile = arg.split('=')[1];
    else if (arg === '--detail') showDetail = true;
}

if (fullRun) { numLines = lines.length; startLine = 0; }
const endIdx = Math.min(startLine + numLines, lines.length);

let output = '';
function out(str) { console.log(str); output += str + '\n'; }

out('╔══════════════════════════════════════════════════════════════════════╗');
out('║  ARRHYTHMIC CYCLE PARSER — Burgos Córdova (2025)                    ║');
out('║  EVA→Romance Lexicon + 3-4 Word Rhythmic Micro-Formulae            ║');
out('║  Coherence Scoring + Negative Control Validation                    ║');
out('╚══════════════════════════════════════════════════════════════════════╝\n');

out(`Processing lines ${startLine + 1} to ${endIdx} of ${lines.length} total`);
out('═'.repeat(72) + '\n');

// Aggregate statistics
let totalCoherence = 0;
let totalCycles = 0;
let totalLexiconHits = 0;
let totalWords = 0;
let linesAboveThreshold = 0;
const COHERENCE_THRESHOLD = 0.60;
const roleDistribution = {};
const topCycles = [];

for (let i = startLine; i < endIdx; i++) {
    const result = parseLine(lines[i], i);
    if (!result) continue;

    totalCoherence += result.coherence;
    totalCycles += result.cycles.length;
    totalLexiconHits += result.lexiconHits;
    totalWords += result.totalWords;
    if (result.coherence >= COHERENCE_THRESHOLD) linesAboveThreshold++;

    // Track role distribution
    for (const token of result.tokens) {
        const role = token.role || 'unknown';
        roleDistribution[role] = (roleDistribution[role] || 0) + 1;
    }

    // Collect top cycles
    for (const cycle of result.cycles) {
        topCycles.push({ ...cycle, lineIndex: i });
    }

    // Display
    if (showDetail || (!fullRun && numLines <= 50)) {
        out(`[Line ${i + 1}] EVA: ${result.eva.slice(0, 70)}${result.eva.length > 70 ? '…' : ''}`);
        out(`  Latin:   ${result.fullLatin.slice(0, 70)}${result.fullLatin.length > 70 ? '…' : ''}`);
        out(`  Italian: ${result.fullItalian.slice(0, 70)}${result.fullItalian.length > 70 ? '…' : ''}`);
        out(`  Coherence: ${(result.coherence * 100).toFixed(1)}% | Lexicon hits: ${result.lexiconHits}/${result.totalWords}`);

        if (result.cycles.length > 0) {
            out(`  Micro-formulae (${result.cycles.length}):`);
            for (const c of result.cycles) {
                out(`    ⟨${c.latin}⟩ = "${c.gloss}" [${c.pattern}] score=${c.score.toFixed(2)}`);
            }
        }
        out('');
    }
}

const processedLines = endIdx - startLine;

// ── Summary Statistics ──────────────────────────────────────────────────

out('═'.repeat(72));
out('\n=== AGGREGATE STATISTICS ===\n');
out(`Lines processed:          ${processedLines}`);
out(`Total words:              ${totalWords}`);
out(`Lexicon matches:          ${totalLexiconHits} (${(totalLexiconHits / Math.max(totalWords, 1) * 100).toFixed(1)}%)`);
out(`Average line coherence:   ${(totalCoherence / Math.max(processedLines, 1) * 100).toFixed(1)}%`);
out(`Lines above ${(COHERENCE_THRESHOLD * 100).toFixed(0)}% threshold:  ${linesAboveThreshold} / ${processedLines} (${(linesAboveThreshold / Math.max(processedLines, 1) * 100).toFixed(1)}%)`);
out(`Total micro-formulae:     ${totalCycles}`);

// ── Role Distribution ──────────────────────────────────────────────────

out('\n=== TOKEN ROLE DISTRIBUTION ===\n');
const sortedRoles = Object.entries(roleDistribution).sort((a, b) => b[1] - a[1]);
out('Role'.padEnd(15) + 'Count'.padEnd(10) + 'Percentage');
out('─'.repeat(40));
for (const [role, count] of sortedRoles) {
    out(`${role.padEnd(15)}${String(count).padEnd(10)}${(count / Math.max(totalWords, 1) * 100).toFixed(1)}%`);
}

// ── Top Coherent Cycles ────────────────────────────────────────────────

out('\n=== TOP 20 MOST COHERENT MICRO-FORMULAE ===\n');
topCycles.sort((a, b) => b.score - a.score);
const displayCycles = topCycles.slice(0, 20);
out('Score  Pattern                  Latin                         Gloss');
out('─'.repeat(90));
for (const c of displayCycles) {
    out(`${c.score.toFixed(2)}   ${c.pattern.padEnd(24)} ${c.latin.padEnd(30)} ${c.gloss.slice(0, 60)}`);
}

// ── Negative Control Test ──────────────────────────────────────────────

out('\n=== NEGATIVE CONTROL TEST (Shuffled vs Original) ===\n');
out('If meaning depends on word ORDER (not just vocabulary), original\n' +
    'sequences should produce more coherent cycles than shuffled ones.\n');

// Run negative control on a sample of lines
const controlSample = Math.min(100, processedLines);
let controlOriginalTotal = 0;
let controlShuffledTotal = 0;
let controlMeaningfulCount = 0;

for (let i = startLine; i < startLine + controlSample && i < endIdx; i++) {
    const result = parseLine(lines[i], i);
    if (!result || result.tokens.length < 3) continue;

    const control = negativeControlTest(result.tokens, 20);
    controlOriginalTotal += control.original;
    controlShuffledTotal += control.shuffledAvg;
    if (control.meaningful) controlMeaningfulCount++;
}

out(`Sample size:                ${controlSample} lines`);
out(`Original coherent cycles:   ${controlOriginalTotal}`);
out(`Shuffled avg cycles:        ${controlShuffledTotal.toFixed(1)}`);
out(`Ratio (original/shuffled):  ${controlShuffledTotal > 0 ? (controlOriginalTotal / controlShuffledTotal).toFixed(2) : '∞'}x`);
out(`Lines where order matters:  ${controlMeaningfulCount}/${controlSample} (${(controlMeaningfulCount / Math.max(controlSample, 1) * 100).toFixed(1)}%)`);

if (controlOriginalTotal > controlShuffledTotal * 1.5) {
    out('\n✅ POSITIVE: Sequential order produces significantly more coherent cycles');
    out('   than random shuffling, supporting the arrhythmic principle.');
} else if (controlOriginalTotal > controlShuffledTotal) {
    out('\n⚠ MARGINAL: Original produces more cycles than shuffled, but difference');
    out('   is not dramatic. More data or refined lexicon may be needed.');
} else {
    out('\n❌ NEGATIVE: Shuffled text produces similar coherence. This suggests');
    out('   the lexicon may need refinement, or the text may not follow this pattern.');
}

// ── Output file ────────────────────────────────────────────────────────

if (outputFile) {
    fs.writeFileSync(outputFile, output);
    console.log(`\nOutput written to ${outputFile}`);
}

out('\n=== ARRHYTHMIC CYCLE PARSING COMPLETE ===');
out('Based on Burgos Córdova (2025) Codex EVA–Romance v2.0');
out('Use --detail for per-line breakdown | --full for all lines | --output=file.txt');
