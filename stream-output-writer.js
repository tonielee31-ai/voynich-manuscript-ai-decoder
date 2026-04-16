// =============================================================================
// OUTPUT STREAMING UTILITY FOR LARGE DECODING RUNS
// =============================================================================
// Use this module instead of collecting lines in memory for full-manuscript runs.
// Prevents memory overflow and enables per-line progress reporting.
//
// Usage:
//   const StreamWriter = require('./stream-output-writer');
//   const writer = new StreamWriter('output.txt', { bufferSize: 100 });
//   writer.write('[Line 1] EVA: ...\n');
//   writer.write('  Caspari-Faccini[45] ...\n');
//   writer.flush(); // Optional flush during run
//   writer.close(); // Must call at end
//
// =============================================================================

const fs = require('fs');
const path = require('path');

class StreamWriter {
  constructor(filepath, options = {}) {
    this.filepath = filepath;
    this.bufferSize = options.bufferSize || 50;
    this.buffer = [];
    this.lineCount = 0;
    this.startTime = Date.now();
    
    // Ensure directory exists
    const dir = path.dirname(filepath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    // Initialize file (truncate if exists)
    try {
      fs.writeFileSync(filepath, '', 'utf8');
    } catch (err) {
      console.error(`StreamWriter ERROR: Cannot write to ${filepath}`);
      throw err;
    }
  }
  
  write(text) {
    this.buffer.push(text);
    this.lineCount += (text.match(/\n/g) || []).length;
    
    if (this.buffer.length >= this.bufferSize) {
      this.flush();
    }
  }
  
  flush() {
    if (this.buffer.length === 0) return;
    
    try {
      fs.appendFileSync(this.filepath, this.buffer.join(''), 'utf8');
      this.buffer = [];
    } catch (err) {
      console.error(`StreamWriter ERROR: Cannot flush to ${this.filepath}`);
      throw err;
    }
  }
  
  close() {
    this.flush();
    const elapsed = ((Date.now() - this.startTime) / 1000).toFixed(2);
    console.log(`[StreamWriter] Wrote ${this.lineCount} lines to ${this.filepath} (${elapsed}s)`);
  }
  
  // Helper: report progress every N lines
  reportProgress(currentLine, totalLines) {
    if (currentLine % 100 === 0) {
      const pct = ((currentLine / totalLines) * 100).toFixed(1);
      const elapsed = ((Date.now() - this.startTime) / 1000).toFixed(1);
      console.log(`  [${pct}%] Line ${currentLine}/${totalLines} (${elapsed}s elapsed)`);
    }
  }
}

module.exports = StreamWriter;
