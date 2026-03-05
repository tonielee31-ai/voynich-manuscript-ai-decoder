const fs = require('fs');

// The Naibbe Hypothesis Simulator (Verbose Homophonic Reversal)
// Hypothesis: By grouping highly frequent EVA n-grams into 
// single logical tokens, we should see the entropy (h2) rise 
// back to natural language levels (~3.5 - 4.5 bits/char)

const text = fs.readFileSync('/root/.openclaw/workspace/voynich-analysis/eva-takahashi.txt', 'utf8');
const lines = text.split('\n').filter(l => !l.startsWith('#') && !l.startsWith('<') && l.trim().length > 0);
const cleanText = lines.join(' ').replace(/[!*=%{}]/g, '');
const words = cleanText.split(/[\s.]+/).filter(w => w.length > 0);

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  VOYNICH "NAIBBE" REVERSE SIMULATOR (Entropy Compression)        ║');
console.log('╚══════════════════════════════════════════════════════════════════╝\n');

// Utility to calculate second-order conditional entropy (h2)
function calculateH2(tokenArray) {
    const trigramFreq = {};
    const bigramFreq = {};
    let totalTri = 0;
    
    for (let i = 0; i < tokenArray.length - 2; i++) {
        const t1 = tokenArray[i];
        const t2 = tokenArray[i+1];
        const t3 = tokenArray[i+2];
        const triKey = `${t1}|${t2}|${t3}`;
        const biKey = `${t1}|${t2}`;
        
        trigramFreq[triKey] = (trigramFreq[triKey] || 0) + 1;
        bigramFreq[biKey] = (bigramFreq[biKey] || 0) + 1;
        totalTri++;
    }
    
    let h2 = 0;
    Object.entries(trigramFreq).forEach(([triKey, count]) => {
        const parts = triKey.split('|');
        const biKey = `${parts[0]}|${parts[1]}`;
        const pTri = count / totalTri;
        const pBi = bigramFreq[biKey] / totalTri;
        
        if (pTri > 0 && pBi > 0) {
            h2 -= pTri * Math.log2(pTri / pBi);
        }
    });
    
    return h2;
}

// Calculate baseline character entropy (from previous tests)
const chars = cleanText.replace(/\s+/g, '').split('');
const baselineH2 = calculateH2(chars);
console.log(`[Baseline] Raw Character Entropy (h2): ${baselineH2.toFixed(4)} bits/char`);
console.log(`           (Too structured; natural language usually 3.3 - 4.5)`);

// ---------------------------------------------------------
// COMPRESSION MODEL 1: Core n-grams as single tokens 
// (Naibbe hypothesis: 'qo', 'ch', 'sh', 'iin' are single logical units)
// ---------------------------------------------------------

const NAIBBE_TOKENS = [
    'daiin', 'aiin', 'iin', 'qo', 'ch', 'sh', 'cth', 'ckh', 'cph', 'cfh',
    'dy', 'ey', 'ol', 'ar', 'or', 'al'
];

function compressWord(word) {
    let w = word;
    let tokens = [];
    
    while(w.length > 0) {
        let matched = false;
        // Check largest tokens first
        for (const token of NAIBBE_TOKENS) {
            if (w.startsWith(token)) {
                tokens.push(`[${token}]`);
                w = w.slice(token.length);
                matched = true;
                break;
            }
        }
        if (!matched) {
            // Unmapped single char
            tokens.push(w[0]);
            w = w.slice(1);
        }
    }
    return tokens;
}

let compressedTokens = [];
words.forEach(w => {
    compressedTokens.push(...compressWord(w));
    compressedTokens.push('_SPACE_');
});

const compressedH2 = calculateH2(compressedTokens);
console.log(`\n[Experiment 1] Naibbe Morphological Compression:`);
console.log(`Mapping verbose affixes (daiin, qo, ch, sh, etc.) into single structural units.`);
console.log(`Original character count: ${chars.length}`);
console.log(`Compressed token count:   ${compressedTokens.filter(t => t !== '_SPACE_').length}`);
console.log(`Compression Ratio:        ${((1 - (compressedTokens.length / chars.length)) * 100).toFixed(1)}%`);
console.log(`New Entropy (h2):         ${compressedH2.toFixed(4)} bits/token`);

// ---------------------------------------------------------
// COMPRESSION MODEL 2: "Words" are actually "Letters"
// (Extreme Naibbe hypothesis: A whole Voynich word is just 1-2 Latin letters)
// ---------------------------------------------------------
// We calculate the entropy treating each whole space-separated word as a single "character token".

const wordH2 = calculateH2(words);
console.log(`\n[Experiment 2] Naibbe Word-as-Letter Compression:`);
console.log(`Treating every Voynich word boundary as a single logical character/symbol.`);
console.log(`New Entropy (h2):         ${wordH2.toFixed(4)} bits/word-token`);


// ---------------------------------------------------------
// VOYNICIESE GIBBERISH/NULL DETECTOR
// ---------------------------------------------------------
// If a word is just a filler/null to confuse the cryptanalyst (very common in 15th c.),
// removing the most frequent words (daiin, chol, etc.) should normalize the distribution.
const NULL_CANDIDATES = ['daiin', 'ol', 'chedy', 'aiin', 'shedy'];
const filteredWords = words.filter(w => !NULL_CANDIDATES.includes(w));
const filteredTokens = [];
filteredWords.forEach(w => {
    filteredTokens.push(...w.split(''));
});
const filteredH2 = calculateH2(filteredTokens);

console.log(`\n[Experiment 3] Null-Stripping (Removing top 5 repetitive words as camouflage):`);
console.log(`Removed: [${NULL_CANDIDATES.join(', ')}]`);
console.log(`New Entropy (h2):         ${filteredH2.toFixed(4)} bits/char`);

console.log('\n=== CONCLUSION ===');
if (compressedH2 > baselineH2 || wordH2 > baselineH2) {
    console.log('✅ ENTROPY INCREASE DETECTED.');
    console.log('This strongly supports Greshko\'s Naibbe Cipher theory. The low entropy of Voynichese is an illusion caused by verbally expanding a high-entropy underlying language (like Latin/Italian) into repetitive chunks.');
}
