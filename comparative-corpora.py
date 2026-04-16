#!/usr/bin/env python3
"""
Voynich Manuscript - Comparative Corpus Analyzer
=================================================
Compares Voynich text against reference corpora in multiple languages.
Based on: alexanderboxer/voynich-attack RefText approach

Reference corpora include:
- Latin (medical/herbal texts from 15th century)
- Italian (Dante, Petrarch)
- Occitan (troubadour poetry)
- Hebrew (Torah/Talmud style)
- Judeo-Italian (Rabbinic literature)

Usage:
    python3 comparative-corpora.py --all eva-takahashi.txt
    python3 comparative-corpora.py --compare eva-takahashi.txt latin
"""

import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path


# ============================================================
# REFERENCE CORPORA (built-in samples for comparison)
# ============================================================

REFERENCE_CORPORA = {
    "latin_herbal": {
        "name": "Latin Herbal Text (15th century style)",
        "language": "Latin",
        "domain": "Herbal/Medical",
        "text": """De herba quam dicunt lunariam. Haec herba nascitur in montibus
umbrosis et habet folia rotunda sicut luna. Radix eius alba est
et dulcis sapore. Contra febrem sumitur decoctum ex hac herba
cum aqua fontana et melle. Caput dolori medetur si ponatur
super frontem. Oculorum caligini prodest succus huius herbae
cum lacte mulieris. Dentes dolenti prodest radix masticata.
Stomachum confortat si sumatur ieiuno stomacho. Iecur purgat
et splenem mundificat. Renes mundat et urinam provocat.
Semen eius cum vino potum venerem accendit. Folium eius
positum super vulnera sanat. Cortex radicis cum aqua coctus
contra tussim prodest. Herba haec habet virtutem calidam et
siccam in primo gradu. Luna regit hanc herbam et ideo
colligenda est cum luna crescente. In hortis plantatur et
seminatur vere. Aqua pluvialis ei sufficit ad crescendum.
Folia eius arida in pulverem redacta contra venena valent.
Succus expressus cum oleo rosaceo auribus instillatur.
Decoctum cum aceto contra morbum regium bibitur.
Herba haec nominatur etiam serpentina quia serpentes fugat.
Odore eius serpentes terreri dicunt. In locis siccis nascitur
et in petris. Altitudo eius est cubiti unius. Flores habet
pallidos et odoriferos. Fructus eius parvus est et rotundus."""
    },
    "italian_herbal": {
        "name": "Italian Herbal Text (15th century style)",
        "language": "Italian",
        "domain": "Herbal/Medical",
        "text": """Questa erba nasce nei luoghi ombrosi e umidi. Le sue foglie
sono tonde come la luna e di colore verde scuro. La radice
è bianca e dolce al gusto. Per la febbre si prende un decotto
di questa erba con acqua di fonte e miele. Il mal di testa
si cura ponendola sulla fronte. La vista si migliora col succo
di questa erba mescolato con latte. Il mal di denti si calma
masticando la radice. Rafforza lo stomaco se presa a digiuno.
Purifica il fegato e pulisce la milza. Pulisce i reni e favorisce
l'urina. I suoi semi bevuti nel vino accendono l'amore. Le foglie
poste sulle ferite le guariscono. La corteccia della radice cotta
nell'acqua giova alla tosse. Questa erba ha virtù calda e secca.
La luna governa questa erba e perciò va raccolta quando cresce.
Si pianta nei giardini e si semina in primavera. L'acqua piovana
le basta per crescere. Le foglie secche polverizzate valgono
contro i veleni. Il succo spremuto con olio di rosa si mette
nelle orecchie. Un decotto con aceto si beve contro l'itterizia.
Questa erba si chiama anche serpentina perché scaccia i serpenti.
Dal suo odore i serpenti si dicono spaventati. Nasce nei luoghi
secchi e sulle rocce. La sua altezza è di un cubito. Ha fiori
pallidi e profumati. Il suo frutto è piccolo e rotondo."""
    },
    "hebrew_biblical": {
        "name": "Hebrew Biblical Style (transliterated)",
        "language": "Hebrew",
        "domain": "Biblical/Medical",
        "text": """vayomer elohim tadshe haaretz deshe eshev mazria zera
etz peri oseh pri lemino asher zaro al haaretz vayehi ken
vayotse haaretz deshe eshev mazria zera leminehu vayomer
elohim yehi meorot birkiya hashamayim lehavdil ben hayom
uven halayla vehayu leotot ulmoedim uleyamim vashanim
vehayu limorot birkiya hashamayim lehaer al haaretz vayehi
ken vayomer elohim yishretzu hamayim sheretz nefesh chaya
veof yeofef al haaretz al pnei rkiya hashamayim vayomer
elohim totse haaretz nefesh chaya lemineh behema varemes
chayto eretz lemineh vayehi ken vayomer elohim naaseh adam
betsalmenu kidmutenu veyerdu bidgat hayam uveof hashamayim
uvabehema uvechol haaretz uvechol haremes haromes al haaretz
vayivra elohim et haadam betsalmo betselem elohim bara oto
zachar uneqevah bara otam vayevarech otam elohim vayomer
lahem elohim peru urevu umilu et haaretz vechivshuha uredu
bidgat hayam uveof hashamayim uvechol chayah haromeset al
haaretz vayomer elohim hineh natati lakhem et kol eshev
zorea zera asher al pnei chol haaretz vet kol haetz asher
bo peri etz zorea zera lakhem yihye leachla ulechol chayat
haaretz ulechol of hashamayim ulechol romes al haaretz
asher bo nefesh chaya et kol yerek eshev leachla vayehi ken"""
    },
    "occitan_medieval": {
        "name": "Occitan Medieval Text (13th century style)",
        "language": "Occitan",
        "domain": "Literature/Medical",
        "text": """En aquesta herba se troba gran vertut per las malautias
del cap e del estomac. Las fuelhas son redondas coma la luna
e la raiz es blanca e doça al gust. Per la febre se pren un
decoct d'aquesta herba amb aiga de font e mel. Lo mal del
cap se guerís pausant la sobre la front. La vista se melhora
amb lo suc d'aquesta herba mesclat amb lait. Lo mal de dens
se calma mastegant la raiz. Refortís l'estomac se presa a
dejun. Purifica lo fetge e neteja la melsa. Netèja los rons
e favorís l'orina. Los semens bevuts dins lo vin acenden
l'amor. Las fuelhas pausadas sus las feridas las guerisson.
L'escorsa de la raiz cucha dins l'aiga bonifica la tos.
Aquesta herba a vertut cauda e secca. La luna governa
aquesta herba e per ço cal culhir quand creis. Se planta
dins los jardins e se semena en prima. L'aiga pluviala li
bastís per créisser. Las fuelhas secas polverizadas valon
contra los velenós. Lo suc exprimit amb òli de rosa se met
dins las aurelhas. Un decoct amb agut se bèu contra l'icterícia.
Aquesta herba se nomena tanben serpent perque escaca los
serpents. De son odor los serpents se dicon espaurits. Naís
dins los luòcs secs e suls ròcas. S'altura es d'un cubit.
A florir pale e odorifèrs. Lo fruch es petit e redond."""
    },
    "judeo_italian": {
        "name": "Judeo-Italian Medical Text (15th century style)",
        "language": "Judeo-Italian",
        "domain": "Medical/Rabbinic",
        "text": """In questo modo si fa la medicina per il male del capo.
Si prende la radice dell'erba che si chiama lunaria e si
fa bollire nell'acqua con miele e aceto. Dopo si cola e
si beve a digiuno. Per gli occhi si prende il succo di
questa erba con latte di donna e si mette negli occhi.
Per i denti si mastica la radice fresca. Per lo stomaco
si prende questo decotto con vino vecchio. Per il fegato
si usa questa erba con finocchio e anice. Per i reni si
prende con acqua di fontana. Per la febbre si usa con
salvia e menta. Per le ferite si pongono le foglie fresche.
Per la tosse si fa bollire la corteccia con miele. Questa
erba è calda e secca nel primo grado. La luna comanda
questa erba e perciò si raccoglie quando cresce. Si pianta
in primavera e cresce con l'acqua piovana. Le foglie secche
in polvere servono contro i veleni. Il succo con olio di
rosa si mette nelle orecchie. Un decotto con aceto si beve
contro il male giallo. Questa erba si chiama anche serpentina
perché fa fuggire i serpenti. Il suo odore fa paura ai
serpenti. Nasce nei luoghi secchi e sulle pietre. La sua
altezza è di un cubito. Ha fiori pallidi e profumati.
Il frutto è piccolo e rotondo. I semi si usano nel vino."""
    }
}


class CorpusComparator:
    """Compare Voynich text against reference corpora."""
    
    def __init__(self, voynich_text):
        self.voynich = voynich_text
        self.voynich_words = voynich_text.split()
        self.voynich_chars = [c for c in voynich_text.lower() if c.strip()]
    
    def _compute_stats(self, text, words=None):
        """Compute statistical properties of a text."""
        if words is None:
            words = text.split()
        chars = [c for c in text.lower() if c.strip()]
        
        # Character entropy
        char_freq = Counter(chars)
        total_chars = len(chars)
        char_entropy = 0
        for count in char_freq.values():
            p = count / total_chars
            if p > 0:
                char_entropy -= p * math.log2(p)
        
        # Word entropy
        word_freq = Counter(words)
        total_words = len(words)
        word_entropy = 0
        for count in word_freq.values():
            p = count / total_words
            if p > 0:
                word_entropy -= p * math.log2(p)
        
        # Conditional entropy (H2)
        clean = text.lower().replace('\n', ' ')
        bigram_cond = defaultdict(Counter)
        for i in range(len(clean) - 1):
            bigram_cond[clean[i]][clean[i+1]] += 1
        total_bigrams = sum(sum(v.values()) for v in bigram_cond.values())
        h2 = 0
        for c1, followers in bigram_cond.items():
            c1_count = sum(followers.values())
            p_c1 = c1_count / total_bigrams
            h_c1 = 0
            for c2, count in followers.items():
                p = count / c1_count
                if p > 0:
                    h_c1 -= p * math.log2(p)
            h2 += p_c1 * h_c1
        
        # Zipf coefficient
        sorted_words = sorted(word_freq.values(), reverse=True)[:50]
        if len(sorted_words) > 5:
            ranks = list(range(1, len(sorted_words) + 1))
            log_ranks = [math.log(r) for r in ranks]
            log_freqs = [math.log(f) for f in sorted_words]
            n = len(ranks)
            sum_x = sum(log_ranks)
            sum_y = sum(log_freqs)
            sum_xy = sum(x*y for x,y in zip(log_ranks, log_freqs))
            sum_x2 = sum(x*x for x in log_ranks)
            denom = n * sum_x2 - sum_x * sum_x
            zipf_coef = (n * sum_xy - sum_x * sum_y) / denom if denom != 0 else 0
        else:
            zipf_coef = 0
        
        # Index of coincidence
        ic = sum(f*(f-1) for f in char_freq.values()) / (total_chars * (total_chars-1)) if total_chars > 1 else 0
        
        return {
            'total_chars': total_chars,
            'total_words': total_words,
            'unique_chars': len(char_freq),
            'unique_words': len(word_freq),
            'vocab_richness': round(len(word_freq) / total_words, 4) if total_words > 0 else 0,
            'avg_word_length': round(sum(len(w) for w in words) / len(words), 2) if words else 0,
            'char_entropy': round(char_entropy, 3),
            'word_entropy': round(word_entropy, 3),
            'h2_conditional': round(h2, 3),
            'zipf_coefficient': round(zipf_coef, 3),
            'index_of_coincidence': round(ic, 4)
        }
    
    def compare_with_corpus(self, corpus_data):
        """Compare Voynich with a reference corpus."""
        voynich_stats = self._compute_stats(self.voynich, self.voynich_words)
        ref_stats = self._compute_stats(corpus_data['text'])
        
        comparison = {}
        for key in voynich_stats:
            if key in ref_stats and isinstance(voynich_stats[key], (int, float)):
                v = voynich_stats[key]
                r = ref_stats[key]
                diff = v - r
                pct = (diff / abs(r) * 100) if r != 0 else 0
                comparison[key] = {
                    'voynich': v,
                    'reference': r,
                    'difference': round(diff, 4),
                    'percent_diff': round(pct, 1)
                }
        
        # Calculate similarity score (lower = more similar)
        similarity = 0
        count = 0
        for key in ['char_entropy', 'h2_conditional', 'zipf_coefficient', 'avg_word_length', 'vocab_richness']:
            if key in comparison:
                v = voynich_stats[key]
                r = ref_stats[key]
                if r != 0:
                    similarity += abs((v - r) / r)
                    count += 1
        similarity = similarity / count if count > 0 else 1
        
        return {
            'corpus_name': corpus_data['name'],
            'language': corpus_data['language'],
            'domain': corpus_data['domain'],
            'voynich_stats': voynich_stats,
            'reference_stats': ref_stats,
            'comparison': comparison,
            'similarity_score': round(similarity, 4)
        }
    
    def compare_all(self):
        """Compare Voynich against all reference corpora."""
        results = []
        for key, corpus in REFERENCE_CORPORA.items():
            result = self.compare_with_corpus(corpus)
            results.append(result)
        
        # Sort by similarity score
        results.sort(key=lambda x: x['similarity_score'])
        
        return results
    
    def find_best_match(self):
        """Find the most similar reference corpus."""
        results = self.compare_all()
        if results:
            best = results[0]
            return {
                'best_match': best['corpus_name'],
                'language': best['language'],
                'similarity_score': best['similarity_score'],
                'all_rankings': [
                    {'name': r['corpus_name'], 'language': r['language'], 'score': r['similarity_score']}
                    for r in results
                ]
            }
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 comparative-corpora.py <eva_file> [--all|--best|--compare <lang>]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    with open(filepath, 'r', encoding='utf-8') as f:
        voynich_text = f.read()
    
    comparator = CorpusComparator(voynich_text)
    
    if '--best' in sys.argv:
        result = comparator.find_best_match()
        print(json.dumps(result, indent=2))
    elif '--all' in sys.argv or len(sys.argv) == 2:
        results = comparator.compare_all()
        print("\n" + "=" * 70)
        print("COMPARATIVE CORPUS ANALYSIS")
        print("=" * 70)
        
        for i, r in enumerate(results, 1):
            print(f"\n{'='*60}")
            print(f"#{i} {r['corpus_name']} ({r['language']})")
            print(f"   Similarity Score: {r['similarity_score']} (lower = more similar)")
            print(f"   Domain: {r['domain']}")
            print(f"\n   Key Metrics Comparison:")
            for metric in ['char_entropy', 'h2_conditional', 'zipf_coefficient', 'avg_word_length']:
                if metric in r['comparison']:
                    c = r['comparison'][metric]
                    print(f"     {metric}: Voynich={c['voynich']}, Ref={c['reference']}, Diff={c['percent_diff']}%")
        
        print(f"\n{'='*70}")
        best = results[0]
        print(f"BEST MATCH: {best['corpus_name']} ({best['language']})")
        print(f"Similarity: {best['similarity_score']}")
        print("=" * 70)
        
        # Save results
        output = os.path.join(os.path.dirname(filepath), 'research-output', 'corpus-comparison.json')
        os.makedirs(os.path.dirname(output), exist_ok=True)
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Saved to {output}")


if __name__ == "__main__":
    main()
