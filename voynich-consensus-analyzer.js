const fs = require('fs');
const path = require('path');

const outputPath = path.join(__dirname, 'decoded-output-v5.txt');
if (!fs.existsSync(outputPath)) {
  console.error('ERROR: decoded-output-v5.txt not found. Run voynich-decoder-v5.js --full --output=decoded-output-v5.txt first.');
  process.exit(1);
}

const raw = fs.readFileSync(outputPath, 'utf8');
const lines = raw.split('\n');

const blocks = [];
let current = null;
for (const line of lines) {
  const headerMatch = line.match(/^\[Line\s+(\d+)\] EVA:\s*(.*)$/);
  if (headerMatch) {
    if (current) blocks.push(current);
    current = {
      line: parseInt(headerMatch[1], 10),
      eva: headerMatch[2].trim(),
      methods: [],
    };
    continue;
  }
  const methodMatch = line.match(/^\s{2}(★| )\s*([^\[]+)\[(\d+)\]\s+(.*)$/);
  if (methodMatch && current) {
    const method = methodMatch[2].trim();
    const score = parseInt(methodMatch[3], 10);
    const plaintext = methodMatch[4].trim();
    const top = methodMatch[1] === '★';
    current.methods.push({ method, score, plaintext, top });
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

function firstToken(text) {
  return normalize(text).split(' ')[0] || '';
}

const stats = {
  totalLines: blocks.length,
  exactConsensus3: 0,
  exactConsensus2: 0,
  exactConsensus1: 0,
  firstTokenConsensus3: 0,
  firstTokenConsensus2: 0,
  methodWins: {},
  methodPairAgreements: {},
};

for (const block of blocks) {
  const texts = block.methods.map(m => normalize(m.plaintext));
  const firstTokens = block.methods.map(m => firstToken(m.plaintext));
  const counts = {};
  texts.forEach(t => { counts[t] = (counts[t] || 0) + 1; });
  const maxCount = Math.max(...Object.values(counts));
  if (maxCount >= 3) stats.exactConsensus3 += 1;
  else if (maxCount === 2) stats.exactConsensus2 += 1;
  else stats.exactConsensus1 += 1;

  const ftCounts = {};
  firstTokens.forEach(t => { ftCounts[t] = (ftCounts[t] || 0) + 1; });
  const maxFT = Math.max(...Object.values(ftCounts));
  if (maxFT >= 3) stats.firstTokenConsensus3 += 1;
  else if (maxFT === 2) stats.firstTokenConsensus2 += 1;

  const topMethod = block.methods.find(m => m.top);
  if (topMethod) stats.methodWins[topMethod.method] = (stats.methodWins[topMethod.method] || 0) + 1;

  for (let i = 0; i < block.methods.length; i++) {
    for (let j = i + 1; j < block.methods.length; j++) {
      const a = block.methods[i];
      const b = block.methods[j];
      const pair = [a.method, b.method].sort().join(' <> ');
      const match = normalize(a.plaintext) === normalize(b.plaintext);
      stats.methodPairAgreements[pair] = stats.methodPairAgreements[pair] || 0;
      if (match) stats.methodPairAgreements[pair] += 1;
    }
  }
}

const exactConsensus3Lines = blocks.filter(block => {
  const counts = {};
  block.methods.map(m => normalize(m.plaintext)).forEach(t => { counts[t] = (counts[t] || 0) + 1; });
  return Math.max(...Object.values(counts)) >= 3;
});

const exactConsensus2Lines = blocks.filter(block => {
  const counts = {};
  block.methods.map(m => normalize(m.plaintext)).forEach(t => { counts[t] = (counts[t] || 0) + 1; });
  return Math.max(...Object.values(counts)) === 2;
});

const outputReport = [];
outputReport.push('Voynich Consensus Analyzer Report');
outputReport.push('=================================');
outputReport.push(`Total lines analyzed: ${stats.totalLines}`);
outputReport.push(`Exact consensus (>=3 methods): ${stats.exactConsensus3}`);
outputReport.push(`Exact consensus (2 methods): ${stats.exactConsensus2}`);
outputReport.push(`No exact consensus: ${stats.exactConsensus1}`);
outputReport.push(`First-token consensus (>=3 methods): ${stats.firstTokenConsensus3}`);
outputReport.push(`First-token consensus (2 methods): ${stats.firstTokenConsensus2}`);
outputReport.push('');
outputReport.push('Top method wins:');
Object.entries(stats.methodWins)
  .sort((a, b) => b[1] - a[1])
  .forEach(([method, count]) => outputReport.push(`- ${method}: ${count} wins`));
outputReport.push('');
outputReport.push('Pairwise exact agreement counts:');
Object.entries(stats.methodPairAgreements)
  .sort((a, b) => b[1] - a[1])
  .forEach(([pair, count]) => outputReport.push(`- ${pair}: ${count}`));
outputReport.push('');

outputReport.push('Top 20 lines with >=3-method exact consensus:');
exactConsensus3Lines.slice(0, 20).forEach(block => {
  const consensus = Object.entries(block.methods.reduce((acc, m) => {
    const key = normalize(m.plaintext);
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {})).sort((a, b) => b[1] - a[1])[0];
  outputReport.push(`Line ${block.line}: ${consensus[1]} methods agree on “[${consensus[0]}]”`);
});

const reportPath = path.join(__dirname, 'voynich-consensus-report.txt');
fs.writeFileSync(reportPath, outputReport.join('\n'));
console.log(`Wrote consensus report to ${reportPath}`);
console.log(outputReport.join('\n'));
