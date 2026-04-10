const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// =============================================================================
// NAIBBE CIPHER GENERATOR — Forward Encryption Simulator
// Based on Michael A. Greshko's 2025 Cryptologia paper "The Naibbe cipher"
// =============================================================================
// This script encrypts plaintext (English/Italian) into pseudo-Voynichese
// by simulating the historical dice-and-card mechanics Greshko identified.
//
// The Naibbe cipher uses:
//   1. A homophonic substitution table (multiple ciphertext options per letter)
//   2. 15th-century dice (d6) to select which homophonic variant is used
//   3. Naibbe/Tarot card draws to select table row/column offsets
//
// The result is verbose, repetitive ciphertext whose entropy appears low
// (like Voynichese) but whose underlying plaintext has normal entropy.
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// CONFIGURABLE PARAMETERS
// Tweak these to test different variations of Greshko's theory.
// ─────────────────────────────────────────────────────────────────────────────

const CONFIG = {
    // Dice configuration: standard 15th-century d6
    DICE_FACES: 6,

    // Naibbe deck configuration (15th-century Italian playing cards)
    // Standard Tarot: 22 Major Arcana + 56 Minor Arcana (4 suits × 14 cards)
    DECK_SIZE: 78,
    MAJOR_ARCANA: 22,
    MINOR_ARCANA: 56,
    SUITS: ['Cups', 'Coins', 'Swords', 'Batons'],  // Italian suits
    CARDS_PER_SUIT: 14,  // Ace through King + Knight

    // How many homophonic variants per plaintext letter (Greshko's key insight)
    // More frequent letters get MORE variants to flatten frequency distribution
    HOMOPHONIC_DEPTH: {
        'a': 6, 'e': 6, 'i': 5, 'o': 5, 'u': 3,
        't': 4, 'n': 4, 'r': 4, 's': 4, 'l': 3,
        'c': 3, 'd': 3, 'p': 2, 'm': 2, 'f': 2,
        'g': 2, 'b': 1, 'h': 1, 'v': 1, 'q': 1,
        'x': 1, 'y': 1, 'z': 1, 'w': 1, 'j': 1, 'k': 1
    },

    // Verbose expansion syllables (how single letters become multi-character
    // Voynichese "words" — the core of the homophonic inflation)
    // Each letter maps to an array of possible EVA expansions
    EXPANSION_TABLE: {
        'a': ['a', 'ai', 'aiin', 'ar', 'al', 'am'],
        'e': ['y', 'ey', 'eey', 'dy', 'edy', 'ydy'],
        'i': ['i', 'ii', 'iin', 'in', 'iiin'],
        'o': ['o', 'ol', 'or', 'ok', 'oky'],
        'u': ['e', 'ee', 'eey'],
        't': ['d', 'da', 'dai', 'daiin'],
        'n': ['n', 'in', 'ain', 'aiin'],
        'r': ['r', 'ar', 'or', 'rar'],
        's': ['sh', 'she', 'sho', 'shey'],
        'l': ['l', 'ol', 'al'],
        'c': ['ch', 'cho', 'chy'],
        'd': ['k', 'ok', 'oky'],
        'p': ['cph', 'cpho'],
        'm': ['m', 'om'],
        'f': ['cfh', 'cfho'],
        'g': ['g', 'og'],
        'b': ['cth'],
        'h': ['cth'],
        'v': ['cph'],
        'q': ['qo'],
        'x': ['ckh'],
        'y': ['y'],
        'z': ['sh'],
        'w': ['cpho'],
        'j': ['che'],
        'k': ['ckh']
    },

    // Number of card draws per encryption block (Greshko suggests 3-5 letter blocks)
    BLOCK_SIZE: 4,

    // Whether to add null/filler words (15th-century camouflage technique)
    ADD_NULLS: true,
    NULL_PROBABILITY: 0.15,  // 15% chance of inserting a null after each word
    NULL_WORDS: ['daiin', 'ol', 'chedy', 'aiin', 'shedy', 'chol'],

    // Random seed for reproducible results (null = truly random)
    SEED: null
};

// ─────────────────────────────────────────────────────────────────────────────
// CRYPTOGRAPHICALLY SEEDED RANDOM NUMBER GENERATOR
// ─────────────────────────────────────────────────────────────────────────────

class NaibbeRNG {
    constructor(seed) {
        if (seed !== null && seed !== undefined) {
            // Seeded PRNG using a simple xorshift128+ for reproducibility
            const hash = crypto.createHash('sha256').update(String(seed)).digest();
            this.s0 = hash.readUInt32BE(0);
            this.s1 = hash.readUInt32BE(4);
            this.seeded = true;
        } else {
            this.seeded = false;
        }
    }

    // Returns float in [0, 1)
    next() {
        if (!this.seeded) {
            return Math.random();
        }
        // xorshift128+
        let s1 = this.s0;
        let s0 = this.s1;
        this.s0 = s0;
        s1 ^= (s1 << 23) & 0xFFFFFFFF;
        s1 ^= s1 >>> 17;
        s1 ^= s0;
        s1 ^= s0 >>> 26;
        this.s1 = s1;
        return ((this.s0 + this.s1) >>> 0) / 0xFFFFFFFF;
    }

    // Simulate a d6 dice roll → returns 1-6
    rollDice() {
        return Math.floor(this.next() * CONFIG.DICE_FACES) + 1;
    }

    // Draw a card from the Naibbe deck → returns { arcana, index, suit? }
    drawCard() {
        const cardIndex = Math.floor(this.next() * CONFIG.DECK_SIZE);

        if (cardIndex < CONFIG.MAJOR_ARCANA) {
            return {
                type: 'major',
                index: cardIndex,
                name: `Major Arcana ${cardIndex}`
            };
        } else {
            const minorIndex = cardIndex - CONFIG.MAJOR_ARCANA;
            const suitIndex = Math.floor(minorIndex / CONFIG.CARDS_PER_SUIT);
            const cardNum = (minorIndex % CONFIG.CARDS_PER_SUIT) + 1;
            return {
                type: 'minor',
                index: cardNum,
                suit: CONFIG.SUITS[suitIndex],
                name: `${cardNum} of ${CONFIG.SUITS[suitIndex]}`
            };
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// HOMOPHONIC SUBSTITUTION ENGINE
// ─────────────────────────────────────────────────────────────────────────────

class NaibbeCipher {
    constructor(config) {
        this.config = config;
        this.rng = new NaibbeRNG(config.SEED);
        this.stats = {
            diceRolls: 0,
            cardDraws: 0,
            nullsInserted: 0,
            plainChars: 0,
            cipherTokens: 0,
            expansionRatio: 0
        };
    }

    // Select which homophonic variant to use based on dice + card mechanics
    selectVariant(letter, diceRoll, card) {
        const expansions = this.config.EXPANSION_TABLE[letter];
        if (!expansions || expansions.length === 0) return letter;

        const depth = this.config.HOMOPHONIC_DEPTH[letter] || 1;
        const actualVariants = expansions.slice(0, Math.min(depth, expansions.length));

        // Dice roll determines the primary variant group
        // Card draw adds a secondary offset for additional randomness
        const diceOffset = (diceRoll - 1) % actualVariants.length;
        const cardOffset = (card.type === 'major')
            ? card.index % actualVariants.length
            : (card.index + CONFIG.SUITS.indexOf(card.suit)) % actualVariants.length;

        // Combine both sources of randomness
        const finalIndex = (diceOffset + cardOffset) % actualVariants.length;
        return actualVariants[finalIndex];
    }

    // Encrypt a single plaintext letter
    encryptLetter(letter) {
        const lower = letter.toLowerCase();

        if (!this.config.EXPANSION_TABLE[lower]) {
            return lower;  // Pass through unknown characters
        }

        const diceRoll = this.rng.rollDice();
        const card = this.rng.drawCard();

        this.stats.diceRolls++;
        this.stats.cardDraws++;

        return this.selectVariant(lower, diceRoll, card);
    }

    // Encrypt a full plaintext string into Voynichese
    encrypt(plaintext) {
        const clean = plaintext.toLowerCase().replace(/[^a-z\s]/g, '');
        const words = clean.split(/\s+/).filter(w => w.length > 0);
        const cipherWords = [];

        words.forEach(word => {
            // Process in blocks (as Greshko describes)
            const blocks = [];
            for (let i = 0; i < word.length; i += this.config.BLOCK_SIZE) {
                blocks.push(word.slice(i, i + this.config.BLOCK_SIZE));
            }

            blocks.forEach(block => {
                // For each block, draw a "master card" that influences the whole block
                const masterCard = this.rng.drawCard();
                this.stats.cardDraws++;

                let cipherBlock = '';
                for (const ch of block) {
                    const expanded = this.encryptLetter(ch);
                    cipherBlock += expanded;
                    this.stats.plainChars++;
                }

                // The master card can add a Voynichese suffix/prefix
                // (simulating the verbose padding Greshko identified)
                if (masterCard.type === 'major' && masterCard.index < 7) {
                    // Major arcana 0-6: add a common Voynich suffix
                    const suffixes = ['y', 'dy', 'ey', 'in', 'n', 'l', 'r'];
                    cipherBlock += suffixes[masterCard.index];
                }

                cipherWords.push(cipherBlock);
                this.stats.cipherTokens++;
            });

            // Possibly insert null/filler words (15th-c camouflage)
            if (this.config.ADD_NULLS && this.rng.next() < this.config.NULL_PROBABILITY) {
                const nullIdx = Math.floor(this.rng.next() * this.config.NULL_WORDS.length);
                cipherWords.push(this.config.NULL_WORDS[nullIdx]);
                this.stats.nullsInserted++;
                this.stats.cipherTokens++;
            }
        });

        this.stats.expansionRatio = cipherWords.join(' ').length / clean.replace(/\s/g, '').length;
        return cipherWords.join(' ');
    }

    // Calculate h2 entropy of the output to compare with real Voynichese
    calculateH2(tokenArray) {
        const trigramFreq = {};
        const bigramFreq = {};
        let totalTri = 0;

        for (let i = 0; i < tokenArray.length - 2; i++) {
            const t1 = tokenArray[i];
            const t2 = tokenArray[i + 1];
            const t3 = tokenArray[i + 2];
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
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN: ENCRYPTION + STATISTICAL COMPARISON
// ─────────────────────────────────────────────────────────────────────────────

// Sample Latin/Italian medical-herbal text (the kind of content likely in the VMS)
const SAMPLE_PLAINTEXT = [
    "recipe for the oil of roses take fresh petals and press them gently",
    "the root of the plant cures the pain of the stomach and the head",
    "take the leaves at dawn when the dew is still upon them",
    "boil in water with salt and honey give one dose at morning",
    "the flower of the field has virtue against fever and sickness",
    "mix the powder with oil and apply to the skin of the patient",
    "the star that rises in the east guides the preparation of medicine",
    "color of gold indicates the presence of sulfur in the compound"
].join('. ');

console.log('╔══════════════════════════════════════════════════════════════════╗');
console.log('║  NAIBBE CIPHER GENERATOR — Forward Encryption Simulator         ║');
console.log('║  Based on Greshko (2025) "The Naibbe cipher" Cryptologia        ║');
console.log('╚══════════════════════════════════════════════════════════════════╝\n');

// Process CLI argument or use sample
const args = process.argv.slice(2);
const inputText = args.length > 0 ? args.join(' ') : SAMPLE_PLAINTEXT;

console.log(`[Input Plaintext] (${inputText.length} chars):`);
console.log(`"${inputText.slice(0, 200)}${inputText.length > 200 ? '...' : ''}"\n`);

// Encrypt
const cipher = new NaibbeCipher(CONFIG);
const ciphertext = cipher.encrypt(inputText);

console.log(`[Generated Voynichese] (${ciphertext.length} chars):`);
console.log(`"${ciphertext.slice(0, 300)}${ciphertext.length > 300 ? '...' : ''}"\n`);

// ─── Statistical Analysis ────────────────────────────────────────────────

console.log('=== ENCRYPTION STATISTICS ===');
console.log(`Dice Rolls Used:        ${cipher.stats.diceRolls}`);
console.log(`Card Draws Used:        ${cipher.stats.cardDraws}`);
console.log(`Null Words Inserted:    ${cipher.stats.nullsInserted}`);
console.log(`Plaintext Characters:   ${cipher.stats.plainChars}`);
console.log(`Cipher Tokens Output:   ${cipher.stats.cipherTokens}`);
console.log(`Expansion Ratio:        ${cipher.stats.expansionRatio.toFixed(2)}x`);

// ─── Entropy Comparison ──────────────────────────────────────────────────

console.log('\n=== ENTROPY COMPARISON ===');

// 1. Plaintext character-level h2
const plainChars = inputText.toLowerCase().replace(/[^a-z]/g, '').split('');
const plainH2 = cipher.calculateH2(plainChars);
console.log(`Plaintext h2 (chars):        ${plainH2.toFixed(4)} bits/char`);

// 2. Generated ciphertext character-level h2
const cipherChars = ciphertext.replace(/\s+/g, '').split('');
const cipherCharH2 = cipher.calculateH2(cipherChars);
console.log(`Ciphertext h2 (chars):       ${cipherCharH2.toFixed(4)} bits/char`);

// 3. Generated ciphertext word-level h2
const cipherWords = ciphertext.split(/\s+/);
const cipherWordH2 = cipher.calculateH2(cipherWords);
console.log(`Ciphertext h2 (words):       ${cipherWordH2.toFixed(4)} bits/word`);

// 4. Compare with real Voynichese if available
const evaPath = path.join(__dirname, 'eva-takahashi.txt');
if (fs.existsSync(evaPath)) {
    const evaText = fs.readFileSync(evaPath, 'utf8');
    const evaLines = evaText.split('\n').filter(l => !l.startsWith('#') && !l.startsWith('<') && l.trim().length > 0);
    const evaClean = evaLines.join(' ').replace(/[!*=%{}]/g, '');

    const evaChars = evaClean.replace(/\s+/g, '').split('');
    const evaCharH2 = cipher.calculateH2(evaChars);

    const evaWords = evaClean.split(/[\s.]+/).filter(w => w.length > 0);
    const evaWordH2 = cipher.calculateH2(evaWords);

    console.log(`\nReal Voynichese h2 (chars):  ${evaCharH2.toFixed(4)} bits/char`);
    console.log(`Real Voynichese h2 (words):  ${evaWordH2.toFixed(4)} bits/word`);

    const charDelta = Math.abs(cipherCharH2 - evaCharH2);
    const wordDelta = Math.abs(cipherWordH2 - evaWordH2);
    console.log(`\nChar-level h2 delta:         ${charDelta.toFixed(4)} (closer to 0 = better match)`);
    console.log(`Word-level h2 delta:         ${wordDelta.toFixed(4)} (closer to 0 = better match)`);

    // ─── Frequency Distribution Comparison ───────────────────────────────
    console.log('\n=== CHARACTER FREQUENCY COMPARISON ===');
    console.log('Char   Generated%   Real VMS%   Delta');
    console.log('─'.repeat(45));

    const genFreq = {};
    cipherChars.forEach(c => { genFreq[c] = (genFreq[c] || 0) + 1; });
    const evaFreq = {};
    evaChars.forEach(c => { evaFreq[c] = (evaFreq[c] || 0) + 1; });

    const allChars = new Set([...Object.keys(genFreq), ...Object.keys(evaFreq)]);
    const rows = [];
    allChars.forEach(c => {
        const genPct = ((genFreq[c] || 0) / cipherChars.length * 100);
        const evaPct = ((evaFreq[c] || 0) / evaChars.length * 100);
        rows.push({ c, genPct, evaPct, delta: Math.abs(genPct - evaPct) });
    });
    rows.sort((a, b) => b.evaPct - a.evaPct);
    rows.slice(0, 15).forEach(({ c, genPct, evaPct, delta }) => {
        console.log(`  ${c}      ${genPct.toFixed(1).padStart(5)}%      ${evaPct.toFixed(1).padStart(5)}%    ${delta.toFixed(1).padStart(5)}`);
    });
}

// ─── Dice & Card Probability Verification ────────────────────────────────

console.log('\n=== DICE & CARD PROBABILITY VERIFICATION ===');
const testRng = new NaibbeRNG(42);
const diceHist = {};
const cardTypeHist = { major: 0, minor: 0 };
const suitHist = {};
const TRIAL_COUNT = 10000;

for (let i = 0; i < TRIAL_COUNT; i++) {
    const roll = testRng.rollDice();
    diceHist[roll] = (diceHist[roll] || 0) + 1;

    const card = testRng.drawCard();
    cardTypeHist[card.type]++;
    if (card.suit) suitHist[card.suit] = (suitHist[card.suit] || 0) + 1;
}

console.log('Dice Distribution (d6, 10k trials):');
for (let face = 1; face <= 6; face++) {
    const count = diceHist[face] || 0;
    const pct = (count / TRIAL_COUNT * 100).toFixed(1);
    const expected = (100 / 6).toFixed(1);
    console.log(`  Face ${face}: ${pct}% (expected ~${expected}%)`);
}

console.log(`\nCard Type Distribution (10k draws):`);
const majorPct = (cardTypeHist.major / TRIAL_COUNT * 100).toFixed(1);
const minorPct = (cardTypeHist.minor / TRIAL_COUNT * 100).toFixed(1);
console.log(`  Major Arcana: ${majorPct}% (expected ~${(22/78*100).toFixed(1)}%)`);
console.log(`  Minor Arcana: ${minorPct}% (expected ~${(56/78*100).toFixed(1)}%)`);

console.log(`\nSuit Distribution (Minor Arcana only):`);
CONFIG.SUITS.forEach(suit => {
    const count = suitHist[suit] || 0;
    const pct = cardTypeHist.minor > 0 ? (count / cardTypeHist.minor * 100).toFixed(1) : '0.0';
    console.log(`  ${suit.padEnd(8)}: ${pct}% (expected ~25.0%)`);
});

console.log('\n=== CONCLUSION ===');
console.log('If the generated ciphertext\'s character-level h2 is close to real');
console.log('Voynichese (~2.0-2.2 bits/char), this confirms that Greshko\'s');
console.log('dice-and-card homophonic cipher CAN produce text with the exact');
console.log('same statistical fingerprint as the Voynich Manuscript.');
