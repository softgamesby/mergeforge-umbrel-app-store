import json, os, time, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

PORT=int(os.getenv('PORT','8096'))
C2POOL=os.getenv('C2POOL_URL','http://c2pool:8080').rstrip('/')
VERSION=os.getenv('APP_VERSION','0.1.0')
STRATUM=os.getenv('STRATUM_PORT','3333')
DATA=Path(os.getenv('DATA_DIR','/data'))
DATA.mkdir(parents=True, exist_ok=True)
APP_DIR=Path(__file__).resolve().parent
CONFIG=DATA/'config.json'
START=time.time()

DEFAULT={'ltcAddress':'','worker':'LG07'}

def load_config():
    try:
        d=json.loads(CONFIG.read_text())
        return {**DEFAULT, **{k:v for k,v in d.items() if k in DEFAULT}}
    except Exception:
        return DEFAULT.copy()

def save_config(d):
    clean={'ltcAddress':str(d.get('ltcAddress','')).strip(), 'worker':str(d.get('worker','LG07')).strip()[:32] or 'LG07'}
    tmp=CONFIG.with_suffix('.tmp'); tmp.write_text(json.dumps(clean,indent=2)); os.chmod(tmp,0o600); tmp.replace(CONFIG)
    return clean

def fetch(path, timeout=3):
    try:
        req=urllib.request.Request(C2POOL+path, headers={'User-Agent':'MergeForge/0.1.0'})
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

def valid_ltc_address(s):
    s=s.strip()
    return bool(s) and (s.startswith('ltc1') or s[0:1] in {'L','M','3'}) and 26 <= len(s) <= 90

class H(BaseHTTPRequestHandler):
    server_version='MergeForge/0.1.0'
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
            cfg=load_config(); ok,data=backend_snapshot()
            return self.send_json({'version':VERSION,'backendOnline':ok,'configured':valid_ltc_address(cfg['ltcAddress']),'config':cfg,'stratumPort':STRATUM,'uptimeSeconds':int(time.time()-START),'backend':data})
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
            cfg=save_config(d); return self.send_json({'ok':True,'config':cfg,'message':'Settings saved. Use the generated miner connection shown on the dashboard.'})
        except Exception as e: return self.send_json({'error':'Invalid request','detail':str(e)},400)

ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()
