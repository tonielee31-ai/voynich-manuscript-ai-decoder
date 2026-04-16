# Sample EVA Test Data for Voynich Decoder

This directory contains minimal EVA transcription samples for CI/CD and unit testing without requiring the full 5,211-line manuscript.

## Files

### sample-lines.txt
First 50 lines of eva-takahashi.txt (approximately 500 tokens). Suitable for:
- Quick smoke tests of all 5 decoder methods
- Verifying scoring metrics are computed
- Testing output formatting without long runtime

### test-herbal-section.txt
Lines 1-100 from Currier A (herbal section). Suitable for:
- Testing Currier A-specific domain boosting
- Validating plant/herb vocabulary matching
- Running arrhythmic-cycle-parser on medical terms

### test-balneological-section.txt
Lines 1000-1100 from Currier B (balneological/astronomical section). Suitable for:
- Testing Currier B-specific scoring
- Validating water/bath/celestial vocabulary
- Scribe clustering on smaller subset

## Usage

```bash
# Test V5 decoder on sample data
cp sample-lines.txt eva-takahashi.txt
node voynich-decoder-v5.js --detail

# Test arrhythmic cycle parser on herbal sample
cp test-herbal-section.txt eva-takahashi.txt
node arrhythmic-cycle-parser.js --detail
```

## Notes

- These are NOT complete test cases. They verify I/O and basic scoring logic.
- Full validation requires running against the complete 5,211-line manuscript.
- Line numbers in test files do not correspond to real manuscript line indices.
