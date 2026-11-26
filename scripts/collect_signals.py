import json, urllib.request, datetime, math, concurrent.futures
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"ArbScanner/7.4"}),timeout=12) as r:
        return json.load(r)
def gate():
    base="https://api.gateio.ws/api/v4"
    s=get(base+"/spot/tickers"); f=get(base+"/futures/usdt/tickers")
    return [(x["currency_pair"],x["lowest_ask"]) for x in s],[(x["contract"],x["highest_bid"]) for x in f]
def bybit():
    base="https://api.bybit.com/v5/market/tickers?category="
    def rows(c):
        try: d=get(base+c)
        except Exception: d=get("https://api.bybitglobal.com/v5/market/tickers?category="+c)
        if d["retCode"]!=0: raise ValueError(d["retMsg"])
        return d["result"]["list"]
    return [(x["symbol"],x["ask1Price"]) for x in rows("spot")],[(x["symbol"],x["bid1Price"]) for x in rows("linear")]
def scan(name,fn):
    s,f=fn(); m={k.replace("_",""):v for k,v in f}; out=[]
    for k,v in s:
        k=k.replace("_","")
        if not k.endswith("USDT") or k not in m: continue
        try: a,b=float(v),float(m[k])
        except (ValueError,TypeError): continue
        if not(math.isfinite(a) and math.isfinite(b) and a>0 and b>a): continue
        pct=100*(b/a-1)
        if pct<0.1: continue
        q=min(90/a,270/(a+b))
        net=pct-.2-.1*b/a-.2
        # Indicative only: assumes convergence, not executable profit.
        out.append(dict(exchange=name,symbol=k,ask=a,bid=b,gross=pct,netEstimate=net,profitEstimate=q*a*net/100,anomaly=pct>5,verified=False,depthVerified=False,fundingVerified=False,exitVerified=False,notional=q*a,estimateAssumesConvergence=True,url="https://sargismuradyan02-max.github.io/Arb-scanner/index.html?v=7.4&symbol="+k+"&exchange="+name+"&capital=300&tp=0.3&sl=0.5&alloc=30#virtual"))
    return out
def main():
    rows=[]; errors={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={n:pool.submit(scan,n,f) for n,f in [("Gate",gate),("Bybit",bybit)]}
        for n,j in jobs.items():
            try: rows.extend(j.result())
            except Exception as e: errors[n]=str(e)
    rows.sort(key=lambda x:(x["anomaly"],-x["gross"]))
    with open("signals.json","w") as f: json.dump(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind="spotFutures",rows=rows[:100],errors=errors,verified=False,capital=300,allocationPct=30,executionReady=False),f,indent=2,allow_nan=False)
if __name__=="__main__": main()
