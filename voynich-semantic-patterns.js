const fs = require('fs');
const path = require('path');

const v5Output = path.join(__dirname, 'decoded-output-v5.txt');
if (!fs.existsSync(v5Output)) {
  console.error('ERROR: decoded-output-v5.txt not found. Run voynich-decoder-v5.js --full --output=decoded-output-v5.txt first.');
  process.exit(1);
}

const raw = fs.readFileSync(v5Output, 'utf8');
const lines = raw.split('\n');

const blocks = [];
let current = null;
for (const line of lines) {
  const headerMatch = line.match(/^\[Line\s+(\d+)\] EVA:\s*(.*)$/);
  if (headerMatch) {
    if (current) blocks.push(current);
    current = { line: parseInt(headerMatch[1], 10), eva: headerMatch[2].trim(), methods: [] };
    continue;
  }
  const methodMatch = line.match(/^\s{2}(★| )\s*([^\[]+)\[(\d+)\]\s+(.*)$/);
  if (methodMatch && current) {
    current.methods.push({ method: methodMatch[2].trim(), score: parseInt(methodMatch[3], 10), plaintext: methodMatch[4].trim(), top: methodMatch[1] === '★' });
  }
}
if (current) blocks.push(current);

function normalize(text) {
  return text.toLowerCase()
    .replace(/[\[\]()*]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function tokenize(text) {
  return normalize(text).split(' ').filter(Boolean);
}

function firstToken(text) {
  return tokenize(text)[0] || '';
}

function lastToken(text) {
  const toks = tokenize(text);
  return toks[toks.length - 1] || '';
}

const consensusLines = [];
for (const block of blocks) {
  const counts = {};
  for (const method of block.methods) {
    const norm = normalize(method.plaintext);
    counts[norm] = (counts[norm] || 0) + 1;
  }
  const winner = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  if (winner && winner[1] >= 3) {
    consensusLines.push({
      line: block.line,
      eva: block.eva,
      consensus: winner[0],
      methods: block.methods,
      count: winner[1],
    });
  }
}

function topEntries(map, limit = 20) {
  return Object.entries(map).sort((a, b) => b[1] - a[1]).slice(0, limit);
}

const tokenFreq = {};
const firstFreq = {};
const lastFreq = {};
const bigramFreq = {};
const anchorTokens = ['sol', 'cor', 'col', 'daiin', 'aiin', 'otaiin', 'chedy', 'shol', 'chor', 'chol', 'chey', 'shey', 'otai', 'qokedy'];
const anchorCounts = {};

for (const line of consensusLines) {
  const tokens = tokenize(line.consensus);
  tokens.forEach(token => { tokenFreq[token] = (tokenFreq[token] || 0) + 1; });
  const first = firstToken(line.consensus);
  if (first) firstFreq[first] = (firstFreq[first] || 0) + 1;
  const last = lastToken(line.consensus);
  if (last) lastFreq[last] = (lastFreq[last] || 0) + 1;
  tokens.forEach((t, i) => {
    if (i < tokens.length - 1) {
      const bigram = `${t} ${tokens[i + 1]}`;
      bigramFreq[bigram] = (bigramFreq[bigram] || 0) + 1;
    }
  });
  anchorTokens.forEach(anchor => {
    if (line.consensus.includes(` ${anchor} `) || line.consensus.startsWith(`${anchor} `) || line.consensus.endsWith(` ${anchor}`)) {
      anchorCounts[anchor] = (anchorCounts[anchor] || 0) + 1;
    }
  });
}

const reportLines = [];
reportLines.push('Voynich Semantic Pattern Mining Report');
reportLines.push('=======================================');
reportLines.push(`Consensus lines (>=3 matching methods): ${consensusLines.length}`);
reportLines.push(`Total V5 lines: ${blocks.length}`);
reportLines.push('');
reportLines.push('Top 25 consensus tokens:');
for (const [token, count] of topEntries(tokenFreq, 25)) {
  reportLines.push(`- ${token}: ${count}`);
}
reportLines.push('');
reportLines.push('Top 20 consensus first tokens:');
for (const [token, count] of topEntries(firstFreq, 20)) {
  reportLines.push(`- ${token}: ${count}`);
}
reportLines.push('');
reportLines.push('Top 20 consensus last tokens:');
for (const [token, count] of topEntries(lastFreq, 20)) {
  reportLines.push(`- ${token}: ${count}`);
}
reportLines.push('');
reportLines.push('Top 25 consensus bigrams:');
for (const [bigram, count] of topEntries(bigramFreq, 25)) {
  reportLines.push(`- ${bigram}: ${count}`);
}
reportLines.push('');
reportLines.push('Anchor token counts in consensus lines:');
for (const anchor of anchorTokens) {
  if (anchorCounts[anchor]) reportLines.push(`- ${anchor}: ${anchorCounts[anchor]}`);
}
reportLines.push('');
reportLines.push('Top 20 high-consensus line examples:');
for (const line of consensusLines.slice(0, 20)) {
  reportLines.push(`Line ${line.line} (count=${line.count}): EVA=${line.eva}`);
  reportLines.push(`  Consensus: ${line.consensus}`);
}

const reportPath = path.join(__dirname, 'voynich-semantic-patterns-report.txt');
fs.writeFileSync(reportPath, reportLines.join('\n'));
console.log(`Wrote semantic patterns report to ${reportPath}`);
console.log(reportLines.slice(0, 25).join('\n'));
