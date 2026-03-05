const fs = require('fs');

const text = fs.readFileSync('/root/.openclaw/workspace/voynich-analysis/eva-takahashi.txt', 'utf8');

// Remove comment lines and metadata
const lines = text.split('\n').filter(l => !l.startsWith('#') && l.trim().length > 0);
const cleanText = lines.join(' ');

// Extract words (split by spaces and dots)
const words = cleanText.split(/[\s.]+/).filter(w => w.length > 0 && !w.startsWith('*') && !w.startsWith('!') && !w.includes('='));

console.log(`Total lines: ${lines.length}`);
console.log(`Total words: ${words.length}`);
console.log(`Unique words: ${new Set(words).size}`);

// Word frequency
const freq = {};
words.forEach(w => { freq[w] = (freq[w] || 0) + 1; });

const sorted = Object.entries(freq).sort((a, b) => b[1] - a[1]);

console.log('\n=== TOP 50 MOST FREQUENT WORDS ===');
sorted.slice(0, 50).forEach(([w, c], i) => {
    console.log(`${i+1}. "${w}" → ${c} times`);
});

// Character frequency
const chars = {};
cleanText.replace(/[\s.!*=#{}]/g, '').split('').forEach(c => { chars[c] = (chars[c] || 0) + 1; });
const charSorted = Object.entries(chars).sort((a, b) => b[1] - a[1]);

console.log('\n=== CHARACTER FREQUENCY ===');
charSorted.forEach(([c, n]) => {
    console.log(`'${c}' → ${n}`);
});

// Bigram analysis
const bigrams = {};
const allChars = cleanText.replace(/[\s.!*=#{}]/g, '');
for (let i = 0; i < allChars.length - 1; i++) {
    const bg = allChars[i] + allChars[i+1];
    bigrams[bg] = (bigrams[bg] || 0) + 1;
}
const bgSorted = Object.entries(bigrams).sort((a, b) => b[1] - a[1]);

console.log('\n=== TOP 30 BIGRAMS ===');
bgSorted.slice(0, 30).forEach(([bg, c]) => {
    console.log(`"${bg}" → ${c}`);
});

// Word length distribution
const lenDist = {};
words.forEach(w => { const l = w.length; lenDist[l] = (lenDist[l] || 0) + 1; });
console.log('\n=== WORD LENGTH DISTRIBUTION ===');
Object.keys(lenDist).sort((a,b) => a-b).forEach(l => {
    console.log(`Length ${l}: ${lenDist[l]} words (${(lenDist[l]/words.length*100).toFixed(1)}%)`);
});

// Zipf's law check
console.log('\n=== ZIPF LAW CHECK (top 10) ===');
sorted.slice(0, 10).forEach(([w, c], i) => {
    const expected = sorted[0][1] / (i + 1);
    console.log(`Rank ${i+1}: "${w}" freq=${c}, Zipf expected≈${expected.toFixed(0)}, ratio=${(c/expected).toFixed(2)}`);
});

// Words starting with 'dai'
const daiWords = sorted.filter(([w]) => w.startsWith('dai'));
console.log('\n=== ALL "dai*" WORDS ===');
daiWords.forEach(([w, c]) => {
    console.log(`"${w}" → ${c}`);
});

// Words starting with 'qo'
const qoWords = sorted.filter(([w]) => w.startsWith('qo'));
console.log('\n=== ALL "qo*" WORDS ===');
qoWords.slice(0, 20).forEach(([w, c]) => {
    console.log(`"${w}" → ${c}`);
});

// Save analysis
fs.writeFileSync('/root/.openclaw/workspace/voynich-analysis/word-frequency.json', JSON.stringify(sorted.slice(0, 200), null, 2));
console.log('\nSaved top 200 word frequencies to word-frequency.json');
