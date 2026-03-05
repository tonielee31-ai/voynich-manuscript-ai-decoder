const fs = require('fs');
const pdf = require('./node_modules/pdf-parse');

async function run() {
  const dataBuffer = fs.readFileSync('/root/.openclaw/workspace/Voynich-Manuscript.pdf');
  try {
    // Attempt using common ways pdf-parse is structured
    const parser = (typeof pdf === 'function') ? pdf : pdf.default || pdf.PDFParse;
    
    if (typeof parser !== 'function') {
        console.log('Available keys:', Object.keys(pdf));
        throw new Error('Could not find parsing function');
    }

    const data = await parser(dataBuffer);
    console.log('Pages:', data.numpages);
    fs.writeFileSync('/root/.openclaw/workspace/Voynich-Text.txt', data.text);
  } catch (err) {
    console.error('Error:', err);
  }
}

run();
