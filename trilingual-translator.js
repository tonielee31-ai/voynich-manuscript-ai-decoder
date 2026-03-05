const fs = require('fs');
const process = require('process');

// Parse command line arguments for language selection
const args = process.argv.slice(2);
let targetLang = 'en'; // Default to English
let showAll = false;

if (args.includes('--lang=zh')) targetLang = 'zh';
else if (args.includes('--lang=yue')) targetLang = 'yue';
else if (args.includes('--lang=all')) showAll = true;

// -----------------------------------------------------------------------------
// Advanced EVA → Italian mapping based on Caspari & Faccini (2025)
// -----------------------------------------------------------------------------
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

// Heuristic Italian -> EN / ZH (Trad) / YUE (Cantonese) Dictionary
const DICT = {
    // Core Nouns
    'cuor':  { en: 'heart', zh: '心臟', yue: '心臟/個心' },
    'cuore': { en: 'heart', zh: '心臟', yue: '心臟/個心' },
    'cor':   { en: 'heart', zh: '心', yue: '心臟/個心' },
    'sol':   { en: 'sun', zh: '太陽', yue: '太陽/個太陽' },
    'sole':  { en: 'sun', zh: '太陽', yue: '太陽/個太陽' },
    'suol':  { en: 'sun/soil', zh: '太陽/土壤', yue: '太陽/泥土' },
    'cute':  { en: 'skin', zh: '皮膚', yue: '皮膚/表皮' },
    'cuute': { en: 'skin', zh: '皮膚', yue: '皮膚/表皮' },
    'dolor': { en: 'pain', zh: '疼痛', yue: '痛楚/好痛' },
    'tol':   { en: 'pain', zh: '疼痛', yue: '痛/病痛' },
    'odor':  { en: 'smell', zh: '氣味', yue: '陣味/香氣' },
    'color': { en: 'color', zh: '顏色', yue: '隻色/顏色' },
    'fiore': { en: 'flower', zh: '花朵', yue: '花/朵花' },
    'arbor': { en: 'tree', zh: '樹木', yue: '樹/棵樹' },
    'sorore': { en: 'sister/nun', zh: '修女/姊妹', yue: '修女/阿妹/師姊' },
    'suore':  { en: 'sister/nun', zh: '修女/姊妹', yue: '修女/阿妹/師姊' },
    'sore':   { en: 'sister/nun', zh: '修女/姊妹', yue: '修女/阿妹/師姊' },
    'palmo': { en: 'palm', zh: '手掌', yue: '手板' },
    'ovui':  { en: 'eggs', zh: '蛋', yue: '蛋/雞蛋' },
    'faces':  { en: 'face/appearance', zh: '面容/外觀', yue: '塊面/樣貌' },
    'facues': { en: 'face/appearance', zh: '面容/外觀', yue: '塊面/樣貌' },
    
    // Medical / Recipe Commands
    'dare':  { en: 'to give', zh: '給予', yue: '畀/落藥' },
    'taiin': { en: 'dose', zh: '劑量/配方', yue: '份量/幾多劑' },
    'dain':  { en: 'dose', zh: '劑量/配方', yue: '份量/幾多劑' },
    'fornar':{ en: 'to bake', zh: '烘烤', yue: '攞去焗/燒' },
    'oliar': { en: 'to oil', zh: '塗油', yue: '搽油/落油' },
    
    // Grammatical
    'che':   { en: 'that', zh: '那個', yue: '嗰個' },
    'cue':   { en: 'that', zh: '那個', yue: '嗰個' },
    'ce':    { en: 'that', zh: '那個', yue: '嗰個' },
    'quo':   { en: 'which', zh: '哪個', yue: '邊個' },
    'qo':    { en: 'which', zh: '哪個', yue: '邊個' },
    'il':    { en: 'the', zh: '(定冠詞)', yue: '(隻/個)' },
    'ol':    { en: 'the', zh: '(定冠詞)', yue: '(隻/個)' },
    'o':     { en: 'the', zh: '(定冠詞)', yue: '(隻/個)' },
    'tale':  { en: 'such', zh: '如此', yue: '咁樣/呢隻' },
    'tal':   { en: 'such', zh: '如此', yue: '咁樣/呢隻' },
    'di':    { en: 'of', zh: '的', yue: '嘅' },
    'te':    { en: 'of/to', zh: '的/給', yue: '嘅/畀' },
    'col':   { en: 'with the', zh: '與...', yue: '同埋...' },
    'cuol':  { en: 'with the', zh: '與...', yue: '同埋...' },
    'per':   { en: 'for', zh: '為了', yue: '為咗' },
    'con':   { en: 'with', zh: '與', yue: '同埋' },
    
    // Astronomy
    'polar': { en: 'North Star', zh: '北極星', yue: '北極星' },
    'toare': { en: 'Taurus', zh: '金牛座', yue: '金牛座' },
    'expe':  { en: 'Venus', zh: '金星', yue: '金星' },
    'cete':  { en: 'Cetus', zh: '鯨魚座', yue: '鯨魚座' },
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

// Map Italianish back to trilingual representations
function translateLanguage(italianWord) {
    const w = italianWord.toLowerCase();
    
    if (DICT[w]) return DICT[w];
    if (w.startsWith('qo') && DICT[w.slice(2)]) {
        const root = DICT[w.slice(2)];
        return { en: `which ${root.en}`, zh: `哪個[${root.zh}]`, yue: `邊個[${root.yue}]` };
    }
    if (w.startsWith('o') && DICT[w.slice(1)]) {
        const root = DICT[w.slice(1)];
        return { en: `the ${root.en}`, zh: `這[${root.zh}]`, yue: `呢個[${root.yue}]` };
    }
    if (w.endsWith('te') && DICT[w.slice(0, -2)]) {
        const root = DICT[w.slice(0, -2)];
        return { en: `${root.en}(verb)`, zh: `${root.zh}(動作)`, yue: `${root.yue}(做嘢)` };
    }
    
    return { en: '?', zh: '?', yue: '?' };
}

// Build Output
const text = fs.readFileSync('/root/.openclaw/workspace/voynich-analysis/eva-takahashi.txt', 'utf8');
const lines = text.split('\n').filter(l => !l.startsWith('#') && l.trim().length > 0);

function processSection(name, startLine, count) {
    let output = `\n=== ${name} ===\n`;
    
    for (let i = startLine; i < Math.min(startLine + count, lines.length); i++) {
        const words = lines[i].split(/[\s.]+/).filter(w => w.length > 0 && !w.match(/^<f/));
        if(words.length === 0) continue;
        
        const itas = words.map(w => translateEVA(w));
        const langs = itas.map(w => translateLanguage(w));
        
        let outEn = ''; let outZh = ''; let outYue = '';
        
        langs.forEach((lang, idx) => {
            if(lang.en !== '?') {
                outEn += `[${lang.en}] `;
                outZh += `[${lang.zh}] `;
                outYue += `[${lang.yue}] `;
            } else {
                outEn += itas[idx] + ' ';
                outZh += itas[idx] + ' ';
                outYue += itas[idx] + ' ';
            }
        });
        
        output += `[Line ${i+1}] EVA: ${lines[i].replace(/<[^>]+>/g, '').trim()}\n`;
        output += `        ITA: ${itas.join(' ')}\n`;
        
        if (showAll) {
            output += `        ENG: ${outEn.trim()}\n`;
            output += `        ZHO: ${outZh.trim()}\n`;
            output += `        YUE: ${outYue.trim()}\n\n`;
        } else {
            if (targetLang === 'en') output += `        ENG: ${outEn.trim()}\n\n`;
            if (targetLang === 'zh') output += `        ZHO: ${outZh.trim()}\n\n`;
            if (targetLang === 'yue') output += `        YUE: ${outYue.trim()}\n\n`;
        }
    }
    return output;
}

let fullOut = "VOYNICH MANUSCRIPT AI TRANSLATOR\n";
fullOut += "=========================================================\n";
if (showAll) {
    fullOut += "Mode: Multilingual (ENG, ZHO, YUE)\n";
} else {
    fullOut += `Mode: Target Language Code -> ${targetLang.toUpperCase()}\n`;
}
fullOut += "=========================================================\n";
fullOut += processSection("Folio 1r: Herbal Section", 0, 10);
fullOut += processSection("Folio 67r: Astronomical Section", 2550, 10);
fullOut += processSection("Folio 88r: Pharmaceutical Section", 3803, 10);

console.log(fullOut);
fs.writeFileSync('/root/.openclaw/workspace/voynich-repo/translation-output.txt', fullOut);
