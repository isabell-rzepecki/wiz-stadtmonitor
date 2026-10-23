"""Explorationsskript Phase 0: Kopf und Tagesordnung aus pdftotext-Ausgaben lesen, grob nach Stufe A/B einordnen.
Nur zur Abschätzung; Stufe B ist hier eine vorläufige Heuristik (bekannte Fehltreffer siehe phase0/BERICHT.md).
Aufruf: python3 -I phase0/parse_stichprobe.py <txt-Verzeichnis> inv_rows.json stichprobe.tsv"""
import re,sys,json,glob,os,collections
OT=['Albshausen','Berlepsch','Ellerode','Hübenthal','Blickershausen','Dohrenbach','Ellingerode','Ermschwerd','Gertenbach','Hubenrode','Hundelshausen','Kleinalmerode','Neuseesen','Roßbach','Rossbach','Unterrieden','Wendershausen','Werleshausen','Ziegenhagen','Bischhausen','Freudenthal','Kernstadt']
PROC=re.compile(r'^(Eröffnung|Begrüßung|Feststellung|Genehmigung der (Tages|Niederschrift)|Verlesen|.*Niederschrift|Mitteilungen|Bericht (des|der)|Verschiedenes|Anfragen|Aktuelle Stunde|Die Gäste|Bürgerfragestunde|Fragestunde|Einwohnerfragestunde|Wahl de|Verpflichtung|Anträge$|Grundstücksangelegenheiten$|Über- und außerplan|Darlehensangelegenheiten$|Personalangelegenheiten)',re.I)
STREET=re.compile(r'\b[A-ZÄÖÜ][\wäöüß\-]*(straße|str\.|weg|gasse|platz|allee|ring|berg|tor|markt)\b',re.U)
def parse(txt):
    h={}; m=re.search(r'Nr\.\s*(\d+)\s*/\s*(\d{4})',txt); h['nr']=m and f'{m.group(1)}/{m.group(2)}'
    m=re.search(r'zur\s+(öffentlichen|nichtöffentlichen|nicht öffentlichen|konstituierenden)?\s*(?:öffentlichen\s+)?Sitzung\s+(de[sr]\s+.+?)(?:\s+am\b|\n\s*\n)',txt,re.S)
    h['gremium']=m and re.sub(r'\s+',' ',m.group(2)).strip()
    h['oeffentlich']=not re.search(r'nicht\s*öffentlich',txt[:800],re.I)
    h['daten']=re.findall(r'\b(\d{2}\.\d{2}\.\d{4}),?\s*(?:,\s*)?(?:\n\s*)?um\s+(\d{1,2}[:.]\d{2})',txt) or re.findall(r'dem\s+(\d{2}\.\d{2}\.\d{4})',txt)
    m=re.search(r'\bim\s+([^\n]+?)\.?\s*\n',txt[txt.find('Uhr'):] if 'Uhr' in txt else ''); h['ort']=m and m.group(1).strip()
    i=txt.find('Tagesordnung'); body=txt[i:] if i>=0 else ''
    body=re.split(r'\n\s*gez\.',body)[0]
    tops=[];cur=None
    for line in body.split('\n')[1:]:
        m=re.match(r'^\s{0,4}(\d{1,2}(?:\.\d{1,2})?)\.?\s{2,}(\S.*)$',line)
        if m: cur={'nr':m.group(1),'titel':m.group(2).strip(),'vorlage':None}; tops.append(cur); continue
        if cur is None or not line.strip(): continue
        v=re.search(r'Vorlage:\s*(\S+)',line)
        if v: cur['vorlage']=v.group(1); continue
        cur['titel']+=' '+line.strip()
    return h,tops
def stufe(g,fn,top):
    t=top['titel']
    if PROC.match(t): return 'P',''
    hits=[o for o in OT if re.search(r'\b'+o,t)]
    m=re.search(r'Gemarkung\s+([A-ZÄÖÜ][\wäöüß\-]+)',t)
    if m: hits.append('Gemarkung '+m.group(1))
    s=STREET.findall(t)
    st=[x.group(0) for x in STREET.finditer(t)]
    if re.search(r'Bebauungsplan|Flächennutzungsplan|B-Plan',t,re.I): hits.append('Bauleitplan')
    if hits or st: return 'B',';'.join(hits+st)
    if g.startswith('OB-'): return 'A',g
    return '-',''
rows=json.load(open(sys.argv[2])); grem={os.path.basename(r[3]):r[0] for r in rows}
out=[];stats=collections.Counter();per=collections.defaultdict(collections.Counter)
for f in sorted(glob.glob(os.path.join(sys.argv[1],'*.txt'))):
    fn=os.path.basename(f)[:-4]+'.pdf'; g=grem.get(fn,'?')
    if g.startswith('??:ob_'): g='OB-'+g[6:].split('_')[0].capitalize()
    h,tops=parse(open(f).read())
    err=[k for k in ('nr','gremium','ort') if not h.get(k)]+([] if h['daten'] else ['datum'])+([] if tops else ['tops'])
    print(f"{fn}\t{g}\t{h['nr']}\t{h['gremium']}\t{h['daten'][:2]}\t{h['ort']}\tTOPs={len(tops)}\tERR={err}")
    for t in tops:
        s,ev=stufe(g,fn,t); stats[s]+=1; per[g.split('-')[0]][s]+=1
        stats['vorlage' if t['vorlage'] else 'novorlage']+=1
        out.append([h['nr'] or '',g,(h['daten'][0][0] if h['daten'] and isinstance(h['daten'][0],tuple) else (h['daten'][0] if h['daten'] else '')),t['nr'],t['titel'],t['vorlage'] or '',s,ev,fn])
print(stats); print({k:dict(v) for k,v in per.items()})
with open(sys.argv[3],'w') as w:
    w.write('bekanntmachung\tgremium\tdatum\ttop\ttitel\tvorlage\tstufe\tfundstelle\tquelle_pdf\n')
    for r in out: w.write('\t'.join(str(x).replace('\t',' ') for x in r)+'\n')
