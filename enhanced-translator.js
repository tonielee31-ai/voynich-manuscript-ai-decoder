const fs = require('fs');

// Advanced EVA → Italian mapping based on Caspari & Faccini (2025)
const MAP = {
    // Digraphs & Trigraphs
    'cth': 'ct',  'ckh': 'cd',  'cph': 'cf',  'cfh': 'cf',
    'ch': 'c',    'sh': 's',    'qo': 'qo',
    'ee': 'ue',   'ii': 'ii',   'in': 'in',
    // Single characters
    'a': 'a',  'o': 'o',  'e': 'u',  'y': 'e',
    'd': 't',  'l': 'l',  'r': 'r',  'i': 'i',
    'n': 'n',  's': 's',  'q': 'q',  't': 'c',
    'k': 'd',  'p': 'p',  'f': 'f',  'm': 'm',
    'g': 'g',  'h': 'h',  'x': 'x',  'v': 'v',
};

// Heuristic Italian -> EN / ZH Dictionary (Based on Caspari's lexical list + Romance roots)
const DICT = {
    // Core Nouns
    'cuor':  { en: 'heart', zh: '心臟' },
    'cuore': { en: 'heart', zh: '心臟' },
    'cor':   { en: 'heart/Corvus', zh: '心/烏鴉座' },
    'sol':   { en: 'sun', zh: '太陽' },
    'sole':  { en: 'sun', zh: '太陽' },
    'suol':  { en: 'sun/soil', zh: '太陽/土壤' },
    'cute':  { en: 'skin', zh: '皮膚' },
    'cuute': { en: 'skin', zh: '皮膚/表皮' },
    'dolor': { en: 'pain', zh: '疼痛' },
    'tol':   { en: 'pain(dolor)', zh: '疼痛' },
    'odor':  { en: 'smell', zh: '氣味' },
    'color': { en: 'color', zh: '顏色' },
    'fiore': { en: 'flower', zh: '花朵' },
    'arbor': { en: 'tree', zh: '樹木' },
    'sorore': { en: 'sister/nun', zh: '修女/姊妹' },
    'suore':  { en: 'sister/nun', zh: '修女/姊妹' },
    'sore':   { en: 'sister/nun', zh: '修女/姊妹' },
    'palmo': { en: 'palm', zh: '手掌' },
    'ovui':  { en: 'eggs', zh: '蛋' },
    ' faces': { en: 'face/appearance', zh: '面容/外觀' },
    'facues':{ en: 'face/appearance', zh: '面容/外觀' },
    
    // Core Verbs & Actions
    'dare':  { en: 'to give', zh: '給予' },
    'taiin': { en: 'dose/given', zh: '劑量/給出' },
    'dain':  { en: 'dose/given', zh: '劑量/給出' },
    'fornar':{ en: 'to bake', zh: '烘烤' },
    'oliar': { en: 'to oil', zh: '塗油' },
    'so':    { en: 'I know', zh: '我知道' },
    'suo':   { en: 'I know/his', zh: '我知道/他的' },
    
    // Grammatical
    'che':   { en: 'that', zh: '那個' },
    'cue':   { en: 'that', zh: '那個' },
    'ce':    { en: 'that', zh: '那個' },
    'quo':   { en: 'which', zh: '哪個' },
    'qo':    { en: 'which', zh: '哪個' },
    'il':    { en: 'the', zh: '(定冠詞)' },
    'ol':    { en: 'the', zh: '(定冠詞)' },
    'o':     { en: 'the', zh: '(定冠詞)' },
    'tale':  { en: 'such', zh: '如此' },
    'tal':   { en: 'such', zh: '如此' },
    'di':    { en: 'of', zh: '的' },
    'te':    { en: 'of/to', zh: '的/給' },
    'col':   { en: 'with the', zh: '與...' },
    'cuol':  { en: 'with the', zh: '與...' },
    'per':   { en: 'for', zh: '為了' },
    'con':   { en: 'with', zh: '與' },
    
    // Common Prefix Combinations (o- = the, qo- = which)
    'osole':  { en: 'the sun', zh: '這太陽' },
    'ocute':  { en: 'the skin', zh: '這皮膚' },
    'ocor':   { en: 'the heart', zh: '這心臟' },
    'qodaiin':{ en: 'which dose', zh: '哪個劑量' },
    'ocaiin': { en: 'the dose', zh: '這劑量' },
    'qocute': { en: 'which skin', zh: '哪處皮膚' },
    'qocol':  { en: 'which with', zh: '與哪個' },
    
    // Astronomy
    'polar': { en: 'North Star', zh: '北極星' },
    'toare': { en: 'Taurus', zh: '金牛座' },
    'expe':  { en: 'Venus', zh: '金星' },
    'cete':  { en: 'Cetus', zh: '鯨魚座' },
};

// Core transliteration logic
function translateEVA(evaWord) {
    let result = '';
    let i = 0;
    const w = evaWord.replace(/[!*=%{}]/g, ''); // Clean artifacts
    while (i < w.length) {
        let matched = false;
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

// Map Italianish back to English/Chinese
function translateLanguage(italianWord) {
    const w = italianWord.toLowerCase();
    
    // Exact match
    if (DICT[w]) return DICT[w];
    
    // Prefix handler (o- / qo-)
    if (w.startsWith('qo') && DICT[w.slice(2)]) {
        const root = DICT[w.slice(2)];
        return { en: `which ${root.en}`, zh: `哪個[${root.zh}]` };
    }
    if (w.startsWith('o') && DICT[w.slice(1)]) {
        const root = DICT[w.slice(1)];
        return { en: `the ${root.en}`, zh: `這[${root.zh}]` };
    }
    
    // Suffix handler (-te / -in)
    if (w.endsWith('te') && DICT[w.slice(0, -2)]) {
        const root = DICT[w.slice(0, -2)];
        return { en: `${root.en}(verb)`, zh: `${root.zh}(動作)` };
    }
    
    return { en: '?', zh: '?' };
}

// Build Output
const text = fs.readFileSync('/root/.openclaw/workspace/voynich-analysis/eva-takahashi.txt', 'utf8');
const lines = text.split('\n').filter(l => !l.startsWith('#') && l.trim().length > 0);

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  VOYNICH ENHANCED MULTILINGUAL TRANSLATOR v0.5               ║');
console.log('╚══════════════════════════════════════════════════════════════════╝\n');

function processSection(name, startLine, count) {
    console.log(`\n=== ${name} SECTION ===`);
    let translatedLines = [];
    
    for (let i = startLine; i < Math.min(startLine + count, lines.length); i++) {
        const words = lines[i].split(/[\s.]+/).filter(w => w.length > 0 && !w.match(/^<f/));
        if(words.length === 0) continue;
        
        const itas = words.map(w => translateEVA(w));
        const langs = itas.map(w => translateLanguage(w));
        
        let enLine = '';
        let zhLine = '';
        
        langs.forEach((lang, idx) => {
            if(lang.en !== '?') {
                enLine += `[${lang.en}] `;
                zhLine += `[${lang.zh}] `;
            } else {
                enLine += itas[idx] + ' ';
                zhLine += itas[idx] + ' ';
            }
        });
        
        console.log(`\n[Line ${i+1}]`);
        console.log(`EVA: ${lines[i].replace(/<[^>]+>/g, '').trim()}`);
        console.log(`ITA: ${itas.join(' ')}`);
        console.log(`EN:  ${enLine.trim()}`);
        console.log(`ZH:  ${zhLine.trim()}`);
        
        translatedLines.push(`[Line ${i+1}] EVA: ${lines[i].replace(/<[^>]+>/g, '').trim()}\nITA: ${itas.join(' ')}\nEN: ${enLine.trim()}\nZH: ${zhLine.trim()}\n`);
    }
    return translatedLines.join('\n');
}

let fullOut = "";
fullOut += processSection("HERBAL (Botany/Recipes - f1r)", 0, 8) + "\n";
fullOut += processSection("ASTRONOMICAL (Stars/Zodiac - f67r)", 2550, 8) + "\n";
fullOut += processSection("PHARMACEUTICAL (Jars/Roots - f88r)", 3803, 8) + "\n";

fs.writeFileSync('/root/.openclaw/workspace/voynich-analysis/translation-multilingual.txt', fullOut);
console.log('\n✅ Enhanced Multilingual Translation saved to translation-multilingual.txt');
