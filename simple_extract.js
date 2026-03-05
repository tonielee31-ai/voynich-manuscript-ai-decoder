const fs = require('fs');
const pdf = require('pdf-parse');

async function run() {
  const dataBuffer = fs.readFileSync('/root/.openclaw/workspace/Voynich-Manuscript.pdf');
  try {
    const data = await pdf(dataBuffer);
    console.log('Pages:', data.numpages);
    fs.writeFileSync('/root/.openclaw/workspace/Voynich-Text.txt', data.text);
    console.log('Saved to Voynich-Text.txt');
  } catch (err) {
    console.error('Extraction Error:', err);
  }
}

run();
