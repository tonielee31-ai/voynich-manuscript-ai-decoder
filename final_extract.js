const fs = require('fs');
const pdf = require('./node_modules/pdf-parse');

async function run() {
  const dataBuffer = fs.readFileSync('/root/.openclaw/workspace/Voynich-Manuscript.pdf');
  try {
    const data = await new pdf.PDFParse(dataBuffer);
    console.log('Pages:', data.numpages);
    fs.writeFileSync('/root/.openclaw/workspace/Voynich-Text.txt', data.text || '');
  } catch (err) {
    console.error('Final attempt error:', err);
  }
}

run();
