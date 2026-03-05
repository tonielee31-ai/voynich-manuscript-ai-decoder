const fs = require('fs');

// Enhanced Caspari & Faccini mapping (EVA → Italian)
// Based on their Table 1 + contextual analysis
const MAP = {
    // 3-char combos (check first)
    'cth': 'ct',  'ckh': 'cd',  'cph': 'cf',  'cfh': 'cf',
    
    // 2-char combos
    'ch': 'c',  'sh': 's',  'qo': 'qo',
    'ee': 'ue', 'ii': 'ii',  'in': 'in',
    
    // Single chars
    'a': 'a',  'o': 'o',  'e': 'u',  'y': 'e',
    'd': 't',  'l': 'l',  'r': 'r',  'i': 'i',
    'n': 'n',  's': 's',  'q': 'q',  't': 'c',
    'k': 'd',  'p': 'p',  'f': 'f',  'm': 'm',
    'g': 'g',  'h': 'h',  'x': 'x',  'v': 'v',
};

function translate(evaWord) {
    let result = '';
    let i = 0;
    const w = evaWord.replace(/[!*=%{}]/g, '');
    while (i < w.length) {
        let matched = false;
        // Try 3-char
        if (i + 2 < w.length) {
            const tri = w.slice(i, i+3);
            if (MAP[tri]) { result += MAP[tri]; i += 3; matched = true; }
        }
        if (!matched && i + 1 < w.length) {
            const bi = w.slice(i, i+2);
            if (MAP[bi]) { result += MAP[bi]; i += 2; matched = true; }
        }
        if (!matched) {
            result += MAP[w[i]] || w[i];
            i++;
        }
    }
    return result;
}

// Italian word dictionary for matching
const ITALIAN_HINTS = {
    'color': 'colore (color)',
    'cuor': 'cuore (heart)',
    'sol': 'sole (sun)',
    'cute': 'cute (skin)',
    'dolor': 'dolore (pain)',
    'odor': 'odore (smell)',
    'fiore': 'fiore (flower)',
    'arbor': 'arbore (tree)',
    'sorore': 'sorore (sister/nun)',
    'torpor': 'torpore (numbness)',
    'polar': 'polar (north star)',
    'palm': 'palmo (palm)',
    'fornar': 'fornare (to bake)',
    'olio': 'olio (oil)',
    'ovo': 'ovo (egg)',
    'tale': 'tale (such)',
    'suo': 'suo (his/her)',
    'per': 'per (for)',
    'con': 'con (with)',
    'qo': 'quo (which)',
    'canol': 'canola (a plant)',
};

// Load and translate sections of the manuscript
const text = fs.readFileSync('/root/.openclaw/workspace/voynich-analysis/eva-takahashi.txt', 'utf8');
const lines = text.split('\n').filter(l => !l.startsWith('#') && l.trim().length > 0);

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  VOYNICH AUTO-TRANSLATOR v0.1 (Caspari-Faccini Framework)     ║');
console.log('╚══════════════════════════════════════════════════════════════════╝\n');

// Translate first 20 lines (Herbal section, f1r)
console.log('=== HERBAL SECTION — First 20 lines (f1r) ===\n');
for (let i = 0; i < Math.min(20, lines.length); i++) {
    const words = lines[i].split(/[\s.]+/).filter(w => w.length > 0);
    const translated = words.map(w => translate(w));
    
    console.log(`Line ${i+1}:`);
    console.log(`  EVA:     ${lines[i].trim()}`);
    console.log(`  Italian: ${translated.join(' ')}`);
    console.log('');
}

// Translate lines from middle (roughly astronomical section ~line 2600)
const astroStart = Math.floor(lines.length * 0.50);
console.log(`\n=== ASTRONOMICAL SECTION — Lines ${astroStart}-${astroStart+10} ===\n`);
for (let i = astroStart; i < Math.min(astroStart + 10, lines.length); i++) {
    const words = lines[i].split(/[\s.]+/).filter(w => w.length > 0);
    const translated = words.map(w => translate(w));
    
    console.log(`Line ${i+1}:`);
    console.log(`  EVA:     ${lines[i].trim()}`);
    console.log(`  Italian: ${translated.join(' ')}`);
    console.log('');
}

// Translate lines from pharmaceutical section (~line 3800)
const pharmaStart = Math.floor(lines.length * 0.73);
console.log(`\n=== PHARMACEUTICAL SECTION — Lines ${pharmaStart}-${pharmaStart+10} ===\n`);
for (let i = pharmaStart; i < Math.min(pharmaStart + 10, lines.length); i++) {
    const words = lines[i].split(/[\s.]+/).filter(w => w.length > 0);
    const translated = words.map(w => translate(w));
    
    console.log(`Line ${i+1}:`);
    console.log(`  EVA:     ${lines[i].trim()}`);
    console.log(`  Italian: ${translated.join(' ')}`);
    console.log('');
}

// Summary statistics
console.log('\n=== TRANSLATION QUALITY ASSESSMENT ===');
const allWords = lines.join(' ').split(/[\s.]+/).filter(w => w.length > 0);
const allTranslated = allWords.map(w => translate(w));

// Check how many translated words look like Italian
let possibleItalian = 0;
const italianPatterns = [
    /ore$/, /are$/, /ire$/, /olo$/, /ole$/, /ola$/,
    /ino$/, /ina$/, /ato$/, /ata$/, /ure$/, /one$/,
    /^qo/, /^o[a-z]/, /lor/, /dor/, /cor/, /sor/,
];

allTranslated.forEach(w => {
    if (italianPatterns.some(p => p.test(w))) possibleItalian++;
});

console.log(`Total words translated: ${allTranslated.length}`);
console.log(`Words matching Italian patterns: ${possibleItalian} (${(possibleItalian/allTranslated.length*100).toFixed(1)}%)`);
console.log(`Average translated word length: ${(allTranslated.reduce((s,w) => s + w.length, 0) / allTranslated.length).toFixed(2)} chars`);

// Save full translation
const fullTranslation = lines.map((line, i) => {
    const words = line.split(/[\s.]+/).filter(w => w.length > 0);
    const translated = words.map(w => translate(w));
    return `[Line ${i+1}] EVA: ${line.trim()}\n         ITA: ${translated.join(' ')}`;
}).join('\n\n');

fs.writeFileSync('/root/.openclaw/workspace/voynich-analysis/full-translation-v01.txt', fullTranslation);
console.log('\n✅ Full translation saved to full-translation-v01.txt');
console.log(`File size: ${(fullTranslation.length / 1024).toFixed(0)} KB`);
