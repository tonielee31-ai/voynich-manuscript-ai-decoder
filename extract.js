const fs = require('fs');
const pdf = require('pdf-parse');

const pdfPath = '/root/.openclaw/workspace/Voynich-Manuscript.pdf';
const dataBuffer = fs.readFileSync(pdfPath);

pdf(dataBuffer).then(function(data) {
    if (data.text) {
        console.log('--- Content Found ---');
        fs.writeFileSync('/root/.openclaw/workspace/Voynich-Raw.txt', data.text);
    }
}).catch(err => {
    console.error('Error:', err);
});
