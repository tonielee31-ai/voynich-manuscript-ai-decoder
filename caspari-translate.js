// Caspari & Faccini (2025) EVA → Italian Letter Mapping
// Based on "A Key to the Voynich Manuscript" (Max Planck Institute)

const CASPARI_MAP = {
    // EVA → Italian letter (based on their Table 1)
    // Note: EVA uses composite chars like 'ch', 'sh', 'cth' etc.
    
    // Gallows characters
    't': 'C',      // EVA 't' (gallows) = Italian C (e.g. "color")
    'k': 'D',      // EVA 'k' (gallows) = Italian D (e.g. "odore") 
    'p': 'F/P',    // EVA 'p' (gallows) = Italian F or P
    'f': 'F/P',    // EVA 'f' (gallows) = Italian F or P
    
    // Basic letters
    'a': 'A',      // EVA 'a' = Italian A
    'o': 'O',      // EVA 'o' = Italian O (also article "o'" before nouns)
    'e': 'U',      // EVA 'e' (looks like 'c') = Italian U
    'y': 'E',      // EVA 'y' (number 9) = Italian E (mirrored e)
    'd': 'T',      // EVA 'd' (number 8) = Italian T (e.g. "torpore")
    'l': 'L',      // EVA 'l' (lambda) = Italian L
    'r': 'R',      // EVA 'r' = Italian R
    'i': 'I',      // EVA 'i' = Italian I
    'n': 'N',      // EVA 'n' = Italian N (often misread as a-r)
    's': 'S',      // EVA 's' = Italian S (one loop)
    'q': 'Q',      // EVA 'q' (number 4) = Italian Q (always before 'o')
    
    // Composite/special
    'ch': 'CU',    // ch ligature
    'sh': 'SU',    // sh ligature  
    'cth': 'CD',   // cth = combined gallows
    'ckh': 'CD',   // ckh = combined gallows
    'cph': 'CF',   // cph = combined gallows
    'cfh': 'CF',   // cfh = combined gallows
};

// Apply mapping to top Voynich words
function translateWord(evaWord) {
    let result = '';
    let i = 0;
    while (i < evaWord.length) {
        // Try 3-char combos first
        if (i + 2 < evaWord.length) {
            const tri = evaWord.slice(i, i+3);
            if (CASPARI_MAP[tri]) {
                result += CASPARI_MAP[tri];
                i += 3;
                continue;
            }
        }
        // Try 2-char combos
        if (i + 1 < evaWord.length) {
            const bi = evaWord.slice(i, i+2);
            if (CASPARI_MAP[bi]) {
                result += CASPARI_MAP[bi];
                i += 2;
                continue;
            }
        }
        // Single char
        if (CASPARI_MAP[evaWord[i]]) {
            result += CASPARI_MAP[evaWord[i]];
        } else {
            result += evaWord[i]; // unknown
        }
        i++;
    }
    return result;
}

// Top 50 most frequent Voynich words
const topWords = [
    'daiin', 'ol', 'chedy', 'aiin', 'shedy', 'chol', 'or', 'ar',
    'chey', 'qokeey', 'qokeedy', 'dar', 'shey', 'qokedy', 'qokaiin',
    'al', 'dal', 'dy', 'chor', 'okaiin', 'qokal', 'shol', 'cheey',
    'okeey', 'cheol', 'otedy', 'otaiin', 'qokar', 'qol', 'chdy',
    'sheey', 'qoky', 'otar', 'oteey', 'chy', 'otal', 'okal',
    'chckhy', 'okar', 'sho', 'saiin', 'okedy', 'sheol', 'dol',
    'oty', 'lchedy', 'daiin', 'okeedy', 'cthy', 'otol'
];

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  CASPARI & FACCINI MAPPING → TOP VOYNICH WORDS TRANSLATION    ║');
console.log('╚══════════════════════════════════════════════════════════════════╝\n');

console.log('EVA Word'.padEnd(15) + '→ Italian Letters'.padEnd(20) + 'Possible Italian Word');
console.log('-'.repeat(65));

const translations = {};
topWords.forEach(w => {
    const italian = translateWord(w);
    translations[w] = italian;
    
    // Try to guess Italian meanings
    let guess = '';
    const low = italian.toLowerCase();
    if (low === 'taiin') guess = '→ ? (common function word)';
    if (low === 'ol') guess = '→ OL (article "il"?)';
    if (w === 'daiin') guess = '→ TAIIN → ? (most frequent - possibly "dare/dati"?)';
    if (w === 'chedy') guess = '→ CUTE → "cute" (skin)';
    if (w === 'shedy') guess = '→ SUTE → ? ';
    if (w === 'chol') guess = '→ CUOL → "col" (with)?';
    if (w === 'qokeey') guess = '→ QODUUE → "qo duce" (which leader)?';
    if (w === 'qokaiin') guess = '→ QODAIIN → "qo dare" (which to give)?';
    if (w === 'dar') guess = '→ TAR → ? ';
    if (w === 'dal') guess = '→ TAL → "tale" (such)?';
    if (w === 'chor') guess = '→ CUOR → "cuore" (heart)!';
    if (w === 'chey') guess = '→ CUE → "che" (that/which)?';
    if (w === 'shol') guess = '→ SOL → "sole" (sun)!';
    if (w === 'otar') guess = '→ OTAR → ? ';
    if (w === 'otal') guess = '→ OTAL → ? ';
    if (w === 'otol') guess = '→ OTOL → ? ';
    if (w === 'sho') guess = '→ SO → "so" (I know)?';
    if (w === 'chy') guess = '→ CUE → "che" (that)?';
    if (w === 'dol') guess = '→ TOL → "dolor" (pain)?';
    
    console.log(`${w.padEnd(15)}→ ${italian.padEnd(20)}${guess}`);
});

// Special analysis: "qo" prefix
console.log('\n\n=== SPECIAL: "qo" = "quo" = "which/that which" (relative pronoun) ===');
console.log('Caspari identifies "qo" as a shortened form of "quo" (which/that which)');
console.log('This explains why qo- words are so frequent (14% of all words)');
console.log('Examples from their paper:');
console.log('  qo exfoliare = "which to exfoliate"');
console.log('  qo sorore = "which sister/nun"');

// Key insight about "o" prefix
console.log('\n\n=== SPECIAL: "o" prefix = definite article (the) ===');
console.log('Caspari: "o" often appears in front of nouns as an article');
console.log('Examples:');
console.log('  o\'sole = "the sun"');
console.log('  o\'colore = "the color"');
console.log('  o\'dolor = "the pain"');
console.log('  o\'cute = "the skin"');
console.log('  o\'cefal = "the head"');

console.log('\n\n=== KEY CASPARI TRANSLATIONS FROM PAPER ===');
const casparExamples = [
    ['POLAR', 'Polaris (North Star)'],
    ['TOARE', 'Taurus (constellation)'],
    ['EXPE', 'Experia (Venus, Evening Star)'],
    ['O\'CETE', 'Cetus (constellation)'],
    ['O\'COR', 'Corvus (constellation)'],
    ['color(e)', 'color'],
    ['o\'colore', 'the color'],
    ['sorore', 'sister, nun'],
    ['odore', 'smell'],
    ['torpore', 'dizziness'],
    ['porpor', 'purple, crimson'],
    ['o\'sole', 'the sun'],
    ['fiore', 'flower'],
    ['palmo', 'palm'],
    ['fornare', 'to bake, to roast'],
    ['compie', 'to complete, to fill'],
    ['p(er)vivi', 'for the living'],
    ['arbor', 'tree'],
    ['oliar', 'to oil'],
    ['ovui', 'eggs'],
    ['exfol(ie)', 'without leaves'],
    ['o\'g(a)mo', 'marriage, sex'],
    ['o\'cute', 'the skin'],
    ['c(a)none', 'canon'],
    ['piente', 'abundant'],
];
casparExamples.forEach(([it, en]) => {
    console.log(`  ${it.padEnd(20)} = "${en}"`);
});

// Apply to first line of manuscript
console.log('\n\n=== FIRST LINE OF MANUSCRIPT (f1r) ===');
const firstLine = 'fachys ykal ar ataiin shol shory';
const firstWords = firstLine.split(' ');
console.log(`EVA: ${firstLine}`);
console.log(`Mapped: ${firstWords.map(w => translateWord(w)).join(' ')}`);
console.log('Caspari reading: "fachys" → possibly "facies" (face/appearance)');
