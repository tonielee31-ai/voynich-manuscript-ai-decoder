#!/usr/bin/env python3
"""
Voynich Manuscript - Topic Modeling & Scribal Intent Analyzer
=============================================================
Based on arxiv:2107.02858 - Topic Modeling Analysis
Based on arxiv:2404.13069 - Subtle Signs of Scribal Intent

Implements:
1. LDA-style topic clustering by page/section
2. Scribal intent analysis (token distribution near boundaries)
3. Illustration-text alignment detection
4. Page similarity matrix

Usage:
    python3 topic-modeling.py --eva eva-takahashi.txt
    python3 topic-modeling.py --eva eva-takahashi.txt --pages
"""

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict


class TopicModelingAnalyzer:
    """Topic modeling and scribal intent analysis for Voynich manuscript."""
    
    def __init__(self, text):
        self.text = text
        self.lines = [l.strip() for l in text.split('\n') if l.strip()]
        self.words = text.split()
        
        # Parse pages (lines starting with 'f' followed by digits and r/v)
        self.pages = self._parse_pages()
        
        # Word frequency per page
        self.page_word_freqs = {}
        for page_name, page_words in self.pages.items():
            self.page_word_freqs[page_name] = Counter(page_words)
    
    def _parse_pages(self):
        """Parse manuscript into pages based on folio markers."""
        pages = {}
        current_page = 'f1r'
        current_words = []
        
        for line in self.lines:
            # Detect page markers
            if line.startswith('f') and len(line) > 2:
                parts = line.split()
                if parts:
                    marker = parts[0]
                    if ('r' in marker[:4] or 'v' in marker[:4]) and marker[1:].replace('r','').replace('v','').isdigit():
                        if current_words:
                            pages[current_page] = current_words
                        current_page = marker
                        current_words = []
                        continue
            
            current_words.extend(line.split())
        
        if current_words:
            pages[current_page] = current_words
        
        return pages
    
    def tf_idf_by_page(self):
        """Calculate TF-IDF scores for words across pages."""
        # Term frequency per page
        tf = {}
        for page, freq in self.page_word_freqs.items():
            total = sum(freq.values())
            tf[page] = {word: count/total for word, count in freq.items()}
        
        # Document frequency
        df = Counter()
        for page, freq in self.page_word_freqs.items():
            for word in freq:
                df[word] += 1
        
        num_pages = len(self.pages)
        
        # TF-IDF
        tfidf = {}
        for page, tf_scores in tf.items():
            tfidf[page] = {}
            for word, tf_val in tf_scores.items():
                idf = math.log(num_pages / (df[word] + 1))
                tfidf[page][word] = round(tf_val * idf, 6)
        
        return tfidf
    
    def page_similarity_matrix(self):
        """Calculate cosine similarity between pages."""
        # Build page vectors (word frequencies)
        all_words = set()
        for freq in self.page_word_freqs.values():
            all_words.update(freq.keys())
        
        word_list = sorted(all_words)
        
        def page_vector(page):
            freq = self.page_word_freqs.get(page, {})
            total = sum(freq.values()) or 1
            return [freq.get(w, 0) / total for w in word_list]
        
        def cosine_sim(v1, v2):
            dot = sum(a*b for a, b in zip(v1, v2))
            mag1 = math.sqrt(sum(a*a for a in v1))
            mag2 = math.sqrt(sum(a*a for a in v2))
            return dot / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0
        
        pages = list(self.pages.keys())[:30]  # Limit to first 30 pages
        vectors = {p: page_vector(p) for p in pages}
        
        similarity = {}
        for p1 in pages:
            similarity[p1] = {}
            for p2 in pages:
                similarity[p1][p2] = round(cosine_sim(vectors[p1], vectors[p2]), 3)
        
        return similarity
    
    def topic_clustering(self, num_topics=5):
        """Simple topic clustering using word co-occurrence."""
        # Group pages by similar vocabulary
        page_vectors = {}
        for page, freq in self.page_word_freqs.items():
            top_words = [w for w, _ in freq.most_common(20)]
            page_vectors[page] = set(top_words)
        
        # Simple clustering: group pages sharing most vocabulary
        clusters = defaultdict(list)
        assigned = set()
        
        pages = list(page_vectors.keys())
        for i, page in enumerate(pages):
            if page in assigned:
                continue
            
            cluster_id = f"topic_{len(clusters)}"
            clusters[cluster_id].append(page)
            assigned.add(page)
            
            for j in range(i+1, len(pages)):
                other = pages[j]
                if other in assigned:
                    continue
                
                overlap = len(page_vectors[page] & page_vectors[other])
                union = len(page_vectors[page] | page_vectors[other])
                jaccard = overlap / union if union > 0 else 0
                
                if jaccard > 0.15:
                    clusters[cluster_id].append(other)
                    assigned.add(other)
        
        # Get representative words per cluster
        cluster_words = {}
        for cluster_id, cluster_pages in clusters.items():
            combined_freq = Counter()
            for page in cluster_pages:
                combined_freq.update(self.page_word_freqs.get(page, {}))
            cluster_words[cluster_id] = combined_freq.most_common(10)
        
        return {
            'num_clusters': len(clusters),
            'clusters': {k: v for k, v in clusters.items()},
            'cluster_keywords': {k: v for k, v in cluster_words.items()}
        }
    
    def scribal_intent_analysis(self):
        """Analyze token distribution near paragraph/line boundaries.
        Based on arxiv:2404.13069 - Subtle Signs of Scribal Intent"""
        
        # First/last words of lines
        first_words = Counter()
        last_words = Counter()
        middle_words = Counter()
        
        for line in self.lines:
            words = line.split()
            if len(words) > 0:
                first_words[words[0]] += 1
                last_words[words[-1]] += 1
                if len(words) > 2:
                    for w in words[1:-1]:
                        middle_words[w] += 1
        
        # Words that appear disproportionately at boundaries
        boundary_bias = {}
        total_first = sum(first_words.values())
        total_last = sum(last_words.values())
        total_middle = sum(middle_words.values())
        
        all_words = set(first_words.keys()) | set(last_words.keys()) | set(middle_words.keys())
        
        for word in all_words:
            first_ratio = first_words.get(word, 0) / total_first if total_first > 0 else 0
            last_ratio = last_words.get(word, 0) / total_last if total_last > 0 else 0
            middle_ratio = middle_words.get(word, 0) / total_middle if total_middle > 0 else 0
            
            # Boundary bias score
            if middle_ratio > 0:
                bias = (first_ratio + last_ratio) / (2 * middle_ratio)
            else:
                bias = float('inf') if (first_ratio + last_ratio) > 0 else 1
            
            if bias > 2.0:  # Appears 2x more at boundaries
                boundary_bias[word] = {
                    'first_pct': round(first_ratio * 100, 2),
                    'last_pct': round(last_ratio * 100, 2),
                    'middle_pct': round(middle_ratio * 100, 2),
                    'bias_score': round(bias, 2)
                }
        
        # Sort by bias
        sorted_bias = sorted(boundary_bias.items(), key=lambda x: -x[1]['bias_score'])[:20]
        
        return {
            'total_lines': len(self.lines),
            'first_word_frequencies': first_words.most_common(10),
            'last_word_frequencies': last_words.most_common(10),
            'boundary_biased_words': dict(sorted_bias),
            'interpretation': (
                "Words appearing disproportionately at line beginnings/endings "
                "may indicate structural markers, section dividers, or scribal conventions."
            )
        }
    
    def illustration_alignment(self):
        """Detect potential illustration-text alignment patterns.
        Based on research: Currier A (herbal) vs B (balneological) sections."""
        
        # Simple heuristic: detect section changes by vocabulary shift
        section_size = max(1, len(self.lines) // 10)
        section_vocabularies = []
        
        for i in range(0, len(self.lines), section_size):
            section_lines = self.lines[i:i+section_size]
            words = []
            for line in section_lines:
                words.extend(line.split())
            section_vocabularies.append(set(words))
        
        # Find vocabulary shift points (potential illustration boundaries)
        shift_points = []
        for i in range(1, len(section_vocabularies)):
            prev = section_vocabularies[i-1]
            curr = section_vocabularies[i]
            
            if prev and curr:
                jaccard = len(prev & curr) / len(prev | curr)
                if jaccard < 0.3:  # Significant vocabulary shift
                    shift_points.append({
                        'line_approx': i * section_size,
                        'section_before_size': len(prev),
                        'section_after_size': len(curr),
                        'vocabulary_overlap': round(jaccard, 3)
                    })
        
        return {
            'num_sections_analyzed': len(section_vocabularies),
            'vocabulary_shift_points': shift_points,
            'interpretation': (
                "Low vocabulary overlap between sections may indicate "
                "different subject matter or illustration boundaries "
                "(herbal vs balneological vs astronomical sections)."
            )
        }
    
    def full_analysis(self):
        """Run all topic modeling analyses."""
        results = {
            'page_count': len(self.pages),
            'topic_clustering': self.topic_clustering(),
            'scribal_intent': self.scribal_intent_analysis(),
            'illustration_alignment': self.illustration_alignment(),
        }
        
        # TF-IDF for first few pages
        tfidf = self.tf_idf_by_page()
        results['tfidf_top_words'] = {}
        for page in list(tfidf.keys())[:5]:
            sorted_tfidf = sorted(tfidf[page].items(), key=lambda x: -x[1])[:10]
            results['tfidf_top_words'][page] = sorted_tfidf
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Topic Modeling & Scribal Intent Analyzer")
    parser.add_argument('--eva', required=True, help='EVA text file')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--pages', action='store_true', help='Show page details')
    
    args = parser.parse_args()
    
    with open(args.eva, 'r', encoding='utf-8') as f:
        text = f.read()
    
    analyzer = TopicModelingAnalyzer(text)
    results = analyzer.full_analysis()
    
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("=" * 60)
        print("TOPIC MODELING & SCRIBAL INTENT ANALYSIS")
        print("(Based on arxiv:2107.02858 & 2404.13069)")
        print("=" * 60)
        
        print(f"\n📄 Pages detected: {results['page_count']}")
        
        print("\n📊 TOPIC CLUSTERING")
        print("-" * 40)
        tc = results['topic_clustering']
        print(f"  Clusters found: {tc['num_clusters']}")
        for cluster_id, keywords in tc['cluster_keywords'].items():
            words = [w for w, _ in keywords[:5]]
            pages = tc['clusters'].get(cluster_id, [])
            print(f"  {cluster_id}: {', '.join(words)} (pages: {len(pages)})")
        
        print("\n📊 SCRIBAL INTENT ANALYSIS")
        print("-" * 40)
        si = results['scribal_intent']
        print(f"  Total lines: {si['total_lines']}")
        print(f"  Top line-start words: {[w for w, _ in si['first_word_frequencies'][:5]]}")
        print(f"  Top line-end words: {[w for w, _ in si['last_word_frequencies'][:5]]}")
        
        if si['boundary_biased_words']:
            print(f"  Boundary-biased words:")
            for word, data in list(si['boundary_biased_words'].items())[:5]:
                print(f"    '{word}': {data['bias_score']}x more at boundaries")
        
        print("\n📊 ILLUSTRATION ALIGNMENT")
        print("-" * 40)
        ia = results['illustration_alignment']
        print(f"  Sections analyzed: {ia['num_sections_analyzed']}")
        print(f"  Vocabulary shifts detected: {len(ia['vocabulary_shift_points'])}")
        
        for shift in ia['vocabulary_shift_points'][:3]:
            print(f"    Line ~{shift['line_approx']}: overlap={shift['vocabulary_overlap']}")
        
        print(f"\n{'='*60}")
    
    # Save
    output = 'research-output/topic-modeling.json'
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Saved to {output}")


if __name__ == "__main__":
    main()
