const process = require('process');

// -----------------------------------------------------------------------------
// HEURISTIC ENCODER: English -> Voynichese (EVA)
// -----------------------------------------------------------------------------
// This script provides a simple heuristic encoding to turn basic English nouns 
// into pseudo-Voynichese following the statistical rules of the manuscript.
// It leverages the mapping generated from the Naibbe & Caspari theories.

const args = process.argv.slice(2);
const inputText = args.length > 0 ? args.join(' ') : "sun sister given heart pain";

// Caspari Inverse Map (Italian -> EVA)
// Notes:
// c -> ch / tch
// s -> sh / s
// cu -> ch
// o -> o
const INV_MAP = {
    'c': 'ch',
    's': 'sh',
    'o': 'o',
    'u': 'e',
    'e': 'y',
    'a': 'a',
    'r': 'r',
    'l': 'l',
    't': 'd',
    'd': 'k',
    'n': 'n',
    'i': 'i'
};

// Simple English -> Italian Root Dictionary (For encoding logic)
const EN_TO_ITA = {
    'the': 'ol',        // usually 'o' prefix or 'ol'
    'heart': 'cuor',
    'sun': 'sol',
    'skin': 'cute',
    'pain': 'dolor',
    'smell': 'odor',
    'color': 'color',
    'flower': 'fiore',
    'tree': 'arbor',
    'sister': 'sore',
    'nun': 'sore',
    'dose': 'taiin',   // phonetic placeholder from prior decoding
    'given': 'taiin',
    'that': 'che',
    'which': 'qo',
    'with': 'col',
    'for': 'per',
    'and': 'ar',       // very common conjunction in text
    'oil': 'olio',
    'gold': 'oro',
    'bull': 'toro',
    'eight': 'otto'
};

// Encode an Italian root into Voynichese (EVA)
function encodeItalianToEVA(itaWord) {
    // Special common Voynich word overrides based on frequency stats
    if (itaWord === 'taiin') return 'daiin';
    if (itaWord === 'che') return 'chey';
    if (itaWord === 'cuor') return 'chor';
    if (itaWord === 'sol') return 'shol';
    if (itaWord === 'cute') return 'chedy';
    if (itaWord === 'dolor') return 'dolol'; // approximate pseudo-suffix
    
    let eva = '';
    let w = itaWord.toLowerCase();
    
    for (let i = 0; i < w.length; i++) {
        const char = w[i];
        if (INV_MAP[char]) {
            eva += INV_MAP[char];
        } else {
            eva += char; 
        }
    }
    
    // Add fake suffix rules to make it look authentic (Zipf's law camouflage)
    if (!eva.endsWith('y') && !eva.endsWith('n') && !eva.endsWith('l') && !eva.endsWith('r')) {
        // Force a Voynich-like ending if it lacks one
        eva += 'y'; 
    }
    
    return eva;
}

// Full Pipeline: English -> Italian Root -> EVA
function encodeEnglishToVoynichese(text) {
    const words = text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/);
    let outEVA = [];
    
    words.forEach(word => {
        if (!word) return;
        
        let itaRoot = EN_TO_ITA[word];
        if (itaRoot) {
            outEVA.push(encodeItalianToEVA(itaRoot));
        } else {
            // Unrecognized English word - fallback to rough phonetic transliteration
            outEVA.push(`*${encodeItalianToEVA(word)}*`); 
        }
    });
    
    return outEVA.join(' ');
}

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  VOYNICH ENCODER (English -> Voynichese / EVA)                   ║');
console.log('╚══════════════════════════════════════════════════════════════════╝\n');

console.log(`Original English: "${inputText}"`);
const encoded = encodeEnglishToVoynichese(inputText);
console.log(`Encoded EVA:      "${encoded}"\n`);
console.log('(Note: Words marked with *asterisks* are unrecognized English words phonetically guessed)');
