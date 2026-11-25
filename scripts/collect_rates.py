import json, re, datetime
from urllib.request import urlopen, Request
from html.parser import HTMLParser

class Visible(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip+=1
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)

def get(url):
    with urlopen(Request(url,headers={'User-Agent':'ArbScanner/4.1 public rate reader'}),timeout=30) as r:
        return r.read().decode('utf-8')
def swap():
    p=Visible(); p.feed(get('https://swapgo.me/yerevan-arm'))
    t=' '.join(' '.join(p.parts).split())
    rows=[]
    for coin in ('USDT','USD','EUR','RUB','GEL','GBP'):
        m=re.search(r'\b'+coin+r'\s+([0-9]+(?:[.,][0-9]+)?)\s*/\s*([0-9]+(?:[.,][0-9]+)?)\s*AMD',t)
        if m:
            a,b=map(lambda x:float(x.replace(',','.')),m.groups())
            if 0<a<=b: rows.append(dict(name='Yerevan indicative average',pair=coin+'/AMD',buy=a,sell=b))
    if not rows: raise ValueError('No recognized public quote rows')
    return rows
def central():
    d=json.loads(get('https://cb.am/latest.json.php'))
    if not isinstance(d,dict): raise ValueError('Unknown response format')
    rows=[]
    for c in ('USD','EUR','RUB'):
        v=float(d[c])
        if v>0: rows.append(dict(name='Reference only, not exchange quote',pair=c+'/AMD',buy=v,sell=v))
    return rows
sources=[]
for name,fn in [('SwapGo public indicative averages',swap),('CB.am reference rates',central)]:
    try: sources.append(dict(name=name,rows=fn()))
    except Exception as e: sources.append(dict(name=name,error=str(e),rows=[]))
with open('rates.json','w',encoding='utf-8') as f:
    json.dump(dict(fetched=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=sources),f,ensure_ascii=False,indent=2)
