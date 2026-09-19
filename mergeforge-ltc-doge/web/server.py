import json, os, time, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

PORT=int(os.getenv('PORT','8096'))
C2POOL=os.getenv('C2POOL_URL','http://c2pool:8080').rstrip('/')
NODE_STATUS=os.getenv('NODE_STATUS_URL','http://node_status:8097').rstrip('/')
VERSION=os.getenv('APP_VERSION','0.1.4')
STRATUM=os.getenv('STRATUM_PORT','3333')
DATA=Path(os.getenv('DATA_DIR','/data'))
DATA.mkdir(parents=True, exist_ok=True)
APP_DIR=Path(__file__).resolve().parent
CONFIG=DATA/'config.json'
START=time.time()

DEFAULT={'ltcAddress':'','dogeAddress':'','worker':'ScryptMiner'}

def load_config():
    try:
        d=json.loads(CONFIG.read_text())
        return {**DEFAULT, **{k:v for k,v in d.items() if k in DEFAULT}}
    except Exception:
        return DEFAULT.copy()

def save_config(d):
    clean={'ltcAddress':str(d.get('ltcAddress','')).strip(), 'dogeAddress':str(d.get('dogeAddress','')).strip(), 'worker':str(d.get('worker','ScryptMiner')).strip()[:32] or 'ScryptMiner'}
    tmp=CONFIG.with_suffix('.tmp'); tmp.write_text(json.dumps(clean,indent=2)); os.chmod(tmp,0o600); tmp.replace(CONFIG)
    return clean

def fetch(path, timeout=3):
    try:
        req=urllib.request.Request(C2POOL+path, headers={'User-Agent':'MergeForge/0.1.4'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw=r.read()
            ctype=r.headers.get('content-type','')
            if 'json' in ctype or raw[:1] in (b'{',b'['): return json.loads(raw)
            return {'text': raw.decode('utf-8','replace')[:5000]}
    except Exception as e:
        return {'_error':str(e)}

def backend_snapshot():
    candidates=['/api/status','/local_stats','/global_stats','/api/explorer']
    out={}
    reachable=False
    for p in candidates:
        d=fetch(p)
        if '_error' not in d: reachable=True
        out[p]=d
    return reachable,out

def node_snapshot(timeout=5):
    try:
        req=urllib.request.Request(
            NODE_STATUS + '/status',
            headers={'User-Agent':'MergeForge/0.1.4'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {
            'litecoin': {'online':False,'ready':False,'error':str(e)[:200]},
            'dogecoin': {'online':False,'ready':False,'error':str(e)[:200]}
        }

def mining_snapshot(cfg):
    stats = fetch('/stratum_stats')
    best = fetch('/best_share')

    out = {
        'available': False,
        'hashrate': None,
        'workers': None,
        'acceptedShares': None,
        'rejectedShares': None,
        'staleShares': None,
        'shareDifficulty': None,
        'bestShareDifficulty': None,
        'bestSharePctOfBlock': None,
    }

    if isinstance(stats, dict) and '_error' not in stats:
        pool = stats.get('pool')
        workers = stats.get('workers')

        if isinstance(pool, dict):
            out['available'] = True
            out['hashrate'] = pool.get('hashrate')
            out['workers'] = pool.get('workers')
            out['acceptedShares'] = pool.get('total_accepted')
            out['rejectedShares'] = pool.get('total_rejected')
            out['staleShares'] = pool.get('total_stale')

        if isinstance(workers, dict) and workers:
            ltc = str(cfg.get('ltcAddress', '')).strip()
            doge = str(cfg.get('dogeAddress', '')).strip()
            worker_name = str(cfg.get('worker', 'ScryptMiner')).strip() or 'ScryptMiner'

            selected = None

            if valid_ltc_address(ltc) and valid_doge_address(doge):
                expected = ltc + ',' + doge + '.' + worker_name
                selected = workers.get(expected)

            # Useful before payout setup, or if only one Stratum worker exists.
            if not isinstance(selected, dict) and len(workers) == 1:
                selected = next(iter(workers.values()))

            if isinstance(selected, dict):
                out['shareDifficulty'] = selected.get('difficulty')

    if isinstance(best, dict) and '_error' not in best:
        session = best.get('session')
        if isinstance(session, dict):
            out['bestShareDifficulty'] = session.get('difficulty')
            out['bestSharePctOfBlock'] = session.get('pct_of_block')

    return out

def blocks_snapshot():
    data = fetch('/recent_blocks')

    empty = {
        'available': False,
        'litecoin': {'count': 0, 'last': None},
        'dogecoin': {'count': 0, 'last': None},
        'total': 0,
        'last': None,
    }

    if not isinstance(data, list):
        return empty

    confirmed = []

    for item in data:
        if not isinstance(item, dict):
            continue

        chain = str(item.get('chain', '')).upper()
        status = str(item.get('status', '')).lower()

        if chain not in {'LTC', 'DOGE'}:
            continue
        if item.get('verified') is not True or status != 'confirmed':
            continue

        try:
            height = int(item.get('height', item.get('number', 0)) or 0)
        except (TypeError, ValueError):
            height = 0

        try:
            ts = int(item.get('ts', 0) or 0)
        except (TypeError, ValueError):
            ts = 0

        try:
            confirmations = int(item.get('confirmations', 0) or 0)
        except (TypeError, ValueError):
            confirmations = 0

        confirmed.append({
            'chain': chain,
            'height': height,
            'hash': str(item.get('hash', ''))[:128],
            'ts': ts,
            'confirmations': confirmations,
        })

    confirmed.sort(key=lambda block: block['ts'], reverse=True)

    ltc = [block for block in confirmed if block['chain'] == 'LTC']
    doge = [block for block in confirmed if block['chain'] == 'DOGE']

    return {
        'available': True,
        'litecoin': {
            'count': len(ltc),
            'last': ltc[0] if ltc else None,
        },
        'dogecoin': {
            'count': len(doge),
            'last': doge[0] if doge else None,
        },
        'total': len(confirmed),
        'last': confirmed[0] if confirmed else None,
    }

def valid_ltc_address(s):
    s=s.strip()
    return bool(s) and (s.startswith('ltc1') or s[0:1] in {'L','M','3'}) and 26 <= len(s) <= 90

def valid_doge_address(s):
    s=s.strip()
    return bool(s) and s[0:1] in {'D','A','9'} and 26 <= len(s) <= 35

class H(BaseHTTPRequestHandler):
    server_version='MergeForge/0.1.4'
    def log_message(self, fmt,*args): print('[web]',fmt%args,flush=True)
    def send_json(self,obj,code=200):
        b=json.dumps(obj,separators=(',',':')).encode(); self.send_response(code); self.headers_common(); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def headers_common(self):
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','SAMEORIGIN'); self.send_header('Referrer-Policy','no-referrer'); self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()'); self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
    def static(self,path,ctype):
        b=Path(path).read_bytes(); self.send_response(200); self.headers_common(); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/health': return self.send_json({'ok':True,'version':VERSION})
        if p=='/api/status':
            cfg=load_config(); ok,data=backend_snapshot(); nodes=node_snapshot(); blocks=blocks_snapshot(); mining=mining_snapshot(cfg)
            return self.send_json({'version':VERSION,'backendOnline':ok,'configured':valid_ltc_address(cfg['ltcAddress']) and valid_doge_address(cfg['dogeAddress']),'config':cfg,'stratumPort':STRATUM,'uptimeSeconds':int(time.time()-START),'backend':data,'nodes':nodes,'blocksFound':blocks,'mining':mining})
        if p.startswith('/api/backend/'):
            sub='/' + p[len('/api/backend/'):]
            d=fetch(sub); return self.send_json(d,502 if '_error' in d else 200)
        if p=='/' or p=='/index.html': return self.static(APP_DIR/'index.html','text/html; charset=utf-8')
        if p=='/icon.svg': return self.static(APP_DIR/'icon.svg','image/svg+xml')
        if p.startswith('/support/') and p.split('/')[-1] in {'btc.png','eth.png','doge.png','ltc.png','dgb.png'}: return self.static(APP_DIR/p.lstrip('/'),'image/png')
        self.send_error(404)
    def do_POST(self):
        if self.path!='/api/setup': return self.send_error(404)
        try:
            n=int(self.headers.get('content-length','0')); assert n<=4096
            d=json.loads(self.rfile.read(n) or b'{}')
            if d.get('ltcAddress') and not valid_ltc_address(str(d['ltcAddress'])): return self.send_json({'error':'Enter a valid Litecoin mainnet receiving address.'},400)
            if d.get('dogeAddress') and not valid_doge_address(str(d['dogeAddress'])): return self.send_json({'error':'Enter a valid Dogecoin mainnet receiving address.'},400)
            cfg=save_config(d); return self.send_json({'ok':True,'config':cfg,'message':'Settings saved. Use the generated LTC + DOGE miner login shown on the dashboard.'})
        except Exception as e: return self.send_json({'error':'Invalid request','detail':str(e)},400)

ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()
