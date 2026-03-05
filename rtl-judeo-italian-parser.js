const fs = require('fs');

// -----------------------------------------------------------------------------------------
// RTL Judeo-Italian Parser for the Voynich Manuscript
// Based on TheDecipherist (Tim Carter Clausen, Feb 2026) Breakthrough
// -----------------------------------------------------------------------------------------
// Theory Core:
// 1. Voynichese is read Right-to-Left (RTL) following Hebrew cursive traditions.
// 2. The underlying language is likely Judeo-Italian.
// 3. Characters with "Loops" (e.g. gallows) act as Hebrew Dagesh (pronunciation/emphasis guides).
// -----------------------------------------------------------------------------------------

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  VOYNICH RTL JUDEO-ITALIAN PARSER (TheDecipherist 2026 Model)    ║');
console.log('╚══════════════════════════════════════════════════════════════════╝\n');

const text = fs.readFileSync('/root/.openclaw/workspace/voynich-analysis/eva-takahashi.txt', 'utf8');
const lines = text.split('\n').filter(l => !l.startsWith('#') && !l.startsWith('<') && l.trim().length > 0);

// Basic mapping framework adapted for RTL scanning
// Treating standard EVA as Left-to-Right representation, we need to reverse the strings first.
const RTL_MAP = {
    // Vowels
    'o': 'O', 'y': 'E', 'a': 'A', 'e': 'I', 
    // Consonants (Hypothetical mapping pending further Judeo-Italian tuning)
    'r': 'R', 'l': 'L', 'n': 'N', 'i': 'I', 'd': 'D/T', 's': 'S', 'c': 'C',
    'k': 'K', 't': 'T', 'p': 'P', 'f': 'F',
    // Known confirmed Italian roots according to the 2026 paper:
    // TORO (Bull), OLIO (Oil), ORO (Gold), LATTE (Milk), OTTO (Eight), OLLA (Pot)
};

// Function to reverse EVA strings (RTL)
function reverseWord(evaWord) {
    // Note: To properly reverse, we should technically keep digraphs like 'ch', 'sh' intact,
    // but for a raw RTL visualizer, we'll reverse character by character first, 
    // then fix known digraphs if needed.
    const clean = evaWord.replace(/[!*=%{}]/g, '');
    return clean.split('').reverse().join('');
}

// Function to attempt matching reversed words to known Italian roots
function matchRoots(rtlWord) {
    const w = rtlWord.toLowerCase();
    
    // Some rough heuristic mappings based on visually reversed Voynich patterns
    // E.g., 'daiin' reversed is 'niiad'. 'chol' reversed is 'lohc'.
    if (w.includes('lo')) return '[OLIO?-like]';
    if (w.includes('ro')) return '[ORO/TORO?-like]';
    if (w.includes('to')) return '[OTTO?-like]';
    if (w.includes('etal')) return '[LATTE?-like]';
    
    return '';
}

// Analyze the top 20 words by frequency, but in RTL
const words = lines.join(' ').replace(/[!*=%{}]/g, '').split(/[\s.]+/).filter(w => w.length > 0);
const freq = {};
words.forEach(w => { freq[w] = (freq[w] || 0) + 1; });
const sorted = Object.entries(freq).sort((a,b) => b[1]-a[1]);

console.log('=== TOP 15 VOYNICH WORDS REVERSED (RIGHT-TO-LEFT) ===');
console.log('LTR Word'.padEnd(12) + 'RTL Word'.padEnd(12) + 'Freq'.padEnd(8) + 'Possible Italian Root Match (Judeo-Italian)');
console.log('-'.repeat(80));

sorted.slice(0, 15).forEach(([w, c]) => {
    const rtl = reverseWord(w);
    const match = matchRoots(rtl);
    console.log(`${w.padEnd(12)}${rtl.padEnd(12)}${String(c).padEnd(8)}${match}`);
});

console.log('\n=== TESTING RTL ON RECIPE/APOTHECARY SECION (Searching for OLIO, LATTE, TORO) ===');
// The paper mentions 'TORO', 'OLIO' appear near apothecary jars and recipe sections 
// Let's grab some lines from the pharma section (~f88r)
const pharmaLines = lines.slice(3800, 3810);
pharmaLines.forEach((line, idx) => {
    const lineWords = line.split(/[\s.]+/).filter(w => w.length > 0);
    const rtlWords = lineWords.map(w => reverseWord(w));
    
    // Look for potential matches
    const highlights = rtlWords.map(rw => {
        const m = matchRoots(rw);
        return m ? `${rw} ${m}` : rw;
    });
    
    console.log(`\nLine ${idx+1} LTR: ${line}`);
    console.log(`Line ${idx+1} RTL: ${highlights.join(' ')}`);
});

console.log('\n✅ RTL parser module initialized. Awaiting comprehensive dictionary mapping.');
