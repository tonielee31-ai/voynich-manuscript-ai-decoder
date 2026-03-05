const fs = require('fs');

const text = fs.readFileSync('/root/.openclaw/workspace/voynich-analysis/eva-takahashi.txt', 'utf8');
const lines = text.split('\n').filter(l => !l.startsWith('#') && l.trim().length > 0);
const cleanText = lines.join(' ');
const words = cleanText.split(/[\s.]+/).filter(w => w.length > 0 && !w.startsWith('*'));

// === PATTERN ANALYSIS ===

// 1. Word-initial character distribution
const initial = {};
words.forEach(w => { const c = w[0]; initial[c] = (initial[c] || 0) + 1; });
console.log('=== WORD-INITIAL CHARACTER DISTRIBUTION ===');
Object.entries(initial).sort((a,b) => b[1]-a[1]).forEach(([c,n]) => {
    console.log(`'${c}' → ${n} (${(n/words.length*100).toFixed(1)}%)`);
});

// 2. Word-final character distribution
const final_ = {};
words.forEach(w => { const c = w[w.length-1]; final_[c] = (final_[c] || 0) + 1; });
console.log('\n=== WORD-FINAL CHARACTER DISTRIBUTION ===');
Object.entries(final_).sort((a,b) => b[1]-a[1]).forEach(([c,n]) => {
    console.log(`'${c}' → ${n} (${(n/words.length*100).toFixed(1)}%)`);
});

// 3. "daiin" context analysis - what words appear before and after "daiin"?
const wordList = cleanText.split(/[\s.]+/).filter(w => w.length > 0);
const beforeDaiin = {};
const afterDaiin = {};
for (let i = 0; i < wordList.length; i++) {
    if (wordList[i] === 'daiin') {
        if (i > 0) beforeDaiin[wordList[i-1]] = (beforeDaiin[wordList[i-1]] || 0) + 1;
        if (i < wordList.length - 1) afterDaiin[wordList[i+1]] = (afterDaiin[wordList[i+1]] || 0) + 1;
    }
}

console.log('\n=== TOP 20 WORDS BEFORE "daiin" ===');
Object.entries(beforeDaiin).sort((a,b) => b[1]-a[1]).slice(0, 20).forEach(([w,c]) => {
    console.log(`"${w}" → ${c}`);
});

console.log('\n=== TOP 20 WORDS AFTER "daiin" ===');
Object.entries(afterDaiin).sort((a,b) => b[1]-a[1]).slice(0, 20).forEach(([w,c]) => {
    console.log(`"${w}" → ${c}`);
});

// 4. Repeated word sequences (consecutive duplicates)
let consecutiveCount = 0;
const consecutivePairs = {};
for (let i = 0; i < wordList.length - 1; i++) {
    if (wordList[i] === wordList[i+1]) {
        consecutiveCount++;
        consecutivePairs[wordList[i]] = (consecutivePairs[wordList[i]] || 0) + 1;
    }
}
console.log(`\n=== CONSECUTIVE WORD REPETITIONS: ${consecutiveCount} total ===`);
Object.entries(consecutivePairs).sort((a,b) => b[1]-a[1]).slice(0, 15).forEach(([w,c]) => {
    console.log(`"${w}" repeated consecutively ${c} times`);
});

// 5. Suffix analysis
const suffixes = {};
words.forEach(w => {
    if (w.length >= 3) {
        const s = w.slice(-2);
        suffixes[s] = (suffixes[s] || 0) + 1;
    }
});
console.log('\n=== TOP 20 WORD SUFFIXES (last 2 chars) ===');
Object.entries(suffixes).sort((a,b) => b[1]-a[1]).slice(0, 20).forEach(([s,c]) => {
    console.log(`"-${s}" → ${c} (${(c/words.length*100).toFixed(1)}%)`);
});

// 6. Prefix analysis
const prefixes = {};
words.forEach(w => {
    if (w.length >= 3) {
        const p = w.slice(0, 2);
        prefixes[p] = (prefixes[p] || 0) + 1;
    }
});
console.log('\n=== TOP 20 WORD PREFIXES (first 2 chars) ===');
Object.entries(prefixes).sort((a,b) => b[1]-a[1]).slice(0, 20).forEach(([p,c]) => {
    console.log(`"${p}-" → ${c} (${(c/words.length*100).toFixed(1)}%)`);
});

// 7. Entropy calculation (second-order conditional entropy h2)
const allChars = cleanText.replace(/[\s.!*=#{}]/g, '');
const trigramFreq = {};
const bigramFreq = {};
for (let i = 0; i < allChars.length - 2; i++) {
    const tri = allChars.slice(i, i+3);
    const bi = allChars.slice(i, i+2);
    trigramFreq[tri] = (trigramFreq[tri] || 0) + 1;
    bigramFreq[bi] = (bigramFreq[bi] || 0) + 1;
}
// h2 = -sum over all trigrams xyz of P(xyz) * log2(P(xyz)/P(xy))
let h2 = 0;
const totalTri = Object.values(trigramFreq).reduce((a,b) => a+b, 0);
Object.entries(trigramFreq).forEach(([tri, count]) => {
    const bi = tri.slice(0, 2);
    const pTri = count / totalTri;
    const pBi = bigramFreq[bi] / totalTri;
    if (pTri > 0 && pBi > 0) {
        h2 -= pTri * Math.log2(pTri / pBi);
    }
});
console.log(`\n=== SECOND-ORDER CONDITIONAL ENTROPY (h2) ===`);
console.log(`h2 = ${h2.toFixed(4)} bits/char`);
console.log(`(Natural languages typically: 3-4 bits/char)`);
console.log(`(Voynichese expected: ~2 bits/char)`);
