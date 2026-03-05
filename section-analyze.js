const fs = require('fs');

const text = fs.readFileSync('/root/.openclaw/workspace/voynich-analysis/eva-takahashi.txt', 'utf8');
const lines = text.split('\n');

// Parse the EVA file - identify sections based on folio numbers
// Herbal: f1r-f57v (plant illustrations)
// Astronomical: f67r-f73v (zodiac, stars)
// Biological/Balneological: f75r-f84v (bathing women)
// Cosmological: f85r-f86v (rosettes, maps)
// Pharmaceutical: f87r-f102v (jars, plant parts)
// Recipes/Stars: f103r-f116v (text with star margins)

const sections = {
    herbal: { folios: [], words: [], range: 'f1-f57' },
    astronomical: { folios: [], words: [], range: 'f67-f73' },
    biological: { folios: [], words: [], range: 'f75-f84' },
    cosmological: { folios: [], words: [], range: 'f85-f86' },
    pharmaceutical: { folios: [], words: [], range: 'f87-f102' },
    recipes: { folios: [], words: [], range: 'f103-f116' }
};

function getFolioNum(folio) {
    const m = folio.match(/f(\d+)/);
    return m ? parseInt(m[1]) : 0;
}

function classifyFolio(folio) {
    const num = getFolioNum(folio);
    if (num >= 1 && num <= 57) return 'herbal';
    if (num >= 67 && num <= 73) return 'astronomical';
    if (num >= 75 && num <= 84) return 'biological';
    if (num >= 85 && num <= 86) return 'cosmological';
    if (num >= 87 && num <= 102) return 'pharmaceutical';
    if (num >= 103 && num <= 116) return 'recipes';
    return null;
}

// Parse lines - look for folio markers and collect words per section
let currentFolio = '';
let currentSection = null;

lines.forEach(line => {
    // Check for folio header
    const folioMatch = line.match(/<f(\d+[rv]\d?)>/);
    if (folioMatch) {
        currentFolio = 'f' + folioMatch[1];
        currentSection = classifyFolio(currentFolio);
        if (currentSection) {
            sections[currentSection].folios.push(currentFolio);
        }
        return;
    }
    
    // Skip comments
    if (line.startsWith('#') || line.trim().length === 0) return;
    
    // If we have a current section, extract words
    if (currentSection) {
        const words = line.split(/[\s.]+/).filter(w => w.length > 0 && !w.startsWith('#') && !w.startsWith('<'));
        sections[currentSection].words.push(...words);
    }
});

// If no folio markers found, try alternative parsing
if (sections.herbal.words.length === 0) {
    console.log('No folio markers detected. Trying line-based heuristic...');
    // Use all words together since we can't separate by folio
    const allWords = [];
    lines.forEach(line => {
        if (line.startsWith('#') || line.trim().length === 0) return;
        const words = line.split(/[\s.]+/).filter(w => w.length > 0);
        allWords.push(...words);
    });
    
    // Split roughly into sections by position (approximation)
    const total = allWords.length;
    const herbalEnd = Math.floor(total * 0.50);    // ~50% herbal
    const astroEnd = Math.floor(total * 0.57);      // ~7% astronomical
    const bioEnd = Math.floor(total * 0.65);        // ~8% biological
    const cosmoEnd = Math.floor(total * 0.70);      // ~5% cosmological
    const pharmaEnd = Math.floor(total * 0.85);     // ~15% pharmaceutical
    
    sections.herbal.words = allWords.slice(0, herbalEnd);
    sections.astronomical.words = allWords.slice(herbalEnd, astroEnd);
    sections.biological.words = allWords.slice(astroEnd, bioEnd);
    sections.cosmological.words = allWords.slice(bioEnd, cosmoEnd);
    sections.pharmaceutical.words = allWords.slice(cosmoEnd, pharmaEnd);
    sections.recipes.words = allWords.slice(pharmaEnd);
}

// Analyze each section
console.log('╔══════════════════════════════════════════════════════════════╗');
console.log('║   VOYNICH MANUSCRIPT — SECTION-BY-SECTION ANALYSIS        ║');
console.log('╚══════════════════════════════════════════════════════════════╝\n');

Object.entries(sections).forEach(([name, sec]) => {
    const words = sec.words.filter(w => !w.startsWith('*') && !w.startsWith('!'));
    if (words.length === 0) return;
    
    const unique = new Set(words);
    const freq = {};
    words.forEach(w => { freq[w] = (freq[w] || 0) + 1; });
    const sorted = Object.entries(freq).sort((a,b) => b[1]-a[1]);
    
    // Word-initial distribution
    const initial = {};
    words.forEach(w => { initial[w[0]] = (initial[w[0]] || 0) + 1; });
    
    // Word-final distribution
    const final_ = {};
    words.forEach(w => { final_[w[w.length-1]] = (final_[w[w.length-1]] || 0) + 1; });
    
    // Suffix analysis
    const suffixes = {};
    words.forEach(w => { if (w.length >= 3) { const s = w.slice(-2); suffixes[s] = (suffixes[s] || 0) + 1; } });
    
    // Average word length
    const avgLen = words.reduce((sum, w) => sum + w.length, 0) / words.length;
    
    // Lexical diversity
    const lexDiv = unique.size / words.length;
    
    // "daiin" frequency
    const daiinCount = freq['daiin'] || 0;
    const daiinPct = (daiinCount / words.length * 100).toFixed(2);
    
    // "qo-" prefix count
    const qoCount = words.filter(w => w.startsWith('qo')).length;
    const qoPct = (qoCount / words.length * 100).toFixed(2);
    
    console.log(`\n${'='.repeat(60)}`);
    console.log(`📖 SECTION: ${name.toUpperCase()} (${sec.range})`);
    console.log(`${'='.repeat(60)}`);
    console.log(`Total words: ${words.length}`);
    console.log(`Unique words: ${unique.size}`);
    console.log(`Lexical diversity: ${lexDiv.toFixed(4)}`);
    console.log(`Average word length: ${avgLen.toFixed(2)} chars`);
    console.log(`"daiin" count: ${daiinCount} (${daiinPct}%)`);
    console.log(`"qo-" prefix count: ${qoCount} (${qoPct}%)`);
    
    console.log(`\nTop 15 words:`);
    sorted.slice(0, 15).forEach(([w,c], i) => {
        console.log(`  ${i+1}. "${w}" → ${c} (${(c/words.length*100).toFixed(1)}%)`);
    });
    
    console.log(`\nTop 5 word-initial chars:`);
    Object.entries(initial).sort((a,b) => b[1]-a[1]).slice(0, 5).forEach(([c,n]) => {
        console.log(`  '${c}' → ${(n/words.length*100).toFixed(1)}%`);
    });
    
    console.log(`\nTop 5 word-final chars:`);
    Object.entries(final_).sort((a,b) => b[1]-a[1]).slice(0, 5).forEach(([c,n]) => {
        console.log(`  '${c}' → ${(n/words.length*100).toFixed(1)}%`);
    });
    
    console.log(`\nTop 5 suffixes:`);
    Object.entries(suffixes).sort((a,b) => b[1]-a[1]).slice(0, 5).forEach(([s,c]) => {
        console.log(`  "-${s}" → ${(c/words.length*100).toFixed(1)}%`);
    });
});

// Cross-section comparison
console.log(`\n\n${'='.repeat(60)}`);
console.log(`🔬 CROSS-SECTION COMPARISON`);
console.log(`${'='.repeat(60)}`);

const comparisonTable = [];
Object.entries(sections).forEach(([name, sec]) => {
    const words = sec.words.filter(w => !w.startsWith('*') && !w.startsWith('!'));
    if (words.length === 0) return;
    const unique = new Set(words);
    const freq = {};
    words.forEach(w => { freq[w] = (freq[w] || 0) + 1; });
    const avgLen = words.reduce((sum, w) => sum + w.length, 0) / words.length;
    const daiinPct = ((freq['daiin'] || 0) / words.length * 100).toFixed(1);
    const qoPct = (words.filter(w => w.startsWith('qo')).length / words.length * 100).toFixed(1);
    const yEndPct = (words.filter(w => w.endsWith('y')).length / words.length * 100).toFixed(1);
    
    comparisonTable.push({
        section: name,
        words: words.length,
        unique: unique.size,
        lexDiv: (unique.size / words.length).toFixed(3),
        avgLen: avgLen.toFixed(1),
        daiinPct,
        qoPct,
        yEndPct,
        topWord: Object.entries(freq).sort((a,b) => b[1]-a[1])[0][0]
    });
});

console.log('\nSection      | Words  | Unique | LexDiv | AvgLen | daiin% | qo-%  | -y%   | Top Word');
console.log('-'.repeat(105));
comparisonTable.forEach(r => {
    console.log(`${r.section.padEnd(13)}| ${String(r.words).padEnd(7)}| ${String(r.unique).padEnd(7)}| ${r.lexDiv.padEnd(7)}| ${r.avgLen.padEnd(7)}| ${r.daiinPct.padEnd(7)}| ${r.qoPct.padEnd(6)}| ${r.yEndPct.padEnd(6)}| ${r.topWord}`);
});
