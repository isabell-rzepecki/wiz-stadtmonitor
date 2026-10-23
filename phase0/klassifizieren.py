"""Explorationsskript Phase 0: Einladungs-PDFs (WP-REST-API) nach Gremium klassifizieren.
Aufruf: python3 -I phase0/klassifizieren.py media_all.json inv_rows.json"""
import json,re,sys,collections
a=json.load(open(sys.argv[1]))
inv=[x for x in a if 'einladung' in x['source_url'].lower()]
def gremium(fn):
    f=fn.lower()
    if 'jagd' in f: return 'FREMD'
    m=re.search(r'einladung[-_](.*?)(?:-\d{1,2}-\d{1,2}-\d{4})?(?:-\d+)?\.pdf$',f)
    s=m.group(1) if m else f
    s=s.replace('nicht-oeffentlich-','').replace('-konstituierung','').replace('konstituierende-sitzung-','')
    if s.startswith('ob-') or s.startswith('ortsbeirat'): return 'OB-'+s.split('-',1)[1].split('-')[0].capitalize() if '-' in s else 'OB-?'
    for k,v in [('stvv','STVV'),('stv','STVV'),('hfr','HFR'),('soz','SozA'),('bv','BV'),('ste','STE'),('ab','AB'),('jugend','Jugendrat'),('senior','Seniorenrat'),('auslaender','AB')]:
        if s.startswith(k): return v
    return '??:'+s
c=collections.Counter(); rows=[]
for x in inv:
    fn=x['source_url'].rsplit('/',1)[1]; g=gremium(fn); c[g]+=1; rows.append((g,x['date'][:10],fn,x['source_url']))
for k,v in sorted(c.items(),key=lambda t:-t[1]): print(v,k)
json.dump(rows,open(sys.argv[2],'w'),ensure_ascii=False)
