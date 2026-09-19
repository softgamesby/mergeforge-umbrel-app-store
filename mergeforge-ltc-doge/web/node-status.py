import base64
import json
import os
import urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

PORT = int(os.getenv("NODE_STATUS_PORT", "8097"))
CONFIG_DIR = Path(os.getenv("CONFIG_DIR", "/config"))

CHAINS = {
    "litecoin": {
        "host": os.getenv("LITECOIN_RPC_HOST", "litecoin"),
        "conf": CONFIG_DIR / "litecoin.conf",
        "default_port": 9332,
    },
    "dogecoin": {
        "host": os.getenv("DOGECOIN_RPC_HOST", "dogecoin"),
        "conf": CONFIG_DIR / "dogecoin.conf",
        "default_port": 22555,
    },
}


def read_conf(path):
    values = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def rpc(chain):
    cfg = CHAINS[chain]
    conf = read_conf(cfg["conf"])

    user = conf["rpcuser"]
    password = conf["rpcpassword"]
    port = int(conf.get("rpcport", cfg["default_port"]))

    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "mergeforge-node-status",
        "method": "getblockchaininfo",
        "params": [],
    }).encode()

    auth = base64.b64encode(f"{user}:{password}".encode()).decode()

    req = urllib.request.Request(
        f"http://{cfg['host']}:{port}/",
        data=payload,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "User-Agent": "MergeForge-NodeStatus/0.1.3",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=4) as response:
        body = json.loads(response.read())

    if body.get("error"):
        raise RuntimeError(str(body["error"]))

    d = body["result"]
    progress = float(d.get("verificationprogress", 0.0))

    return {
        "online": True,
        "blocks": int(d.get("blocks", 0)),
        "headers": int(d.get("headers", 0)),
        "verificationProgress": progress,
        "syncPercent": round(progress * 100, 2),
        "initialBlockDownload": bool(d.get("initialblockdownload", True)),
        "pruned": bool(d.get("pruned", False)),
        "ready": not bool(d.get("initialblockdownload", True)),
    }


def snapshot():
    result = {}
    for chain in CHAINS:
        try:
            result[chain] = rpc(chain)
        except Exception as exc:
            result[chain] = {
                "online": False,
                "ready": False,
                "error": str(exc)[:200],
            }
    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "MergeForge-NodeStatus/0.1.3"

    def log_message(self, fmt, *args):
        print("[node-status]", fmt % args, flush=True)

    def send_json(self, obj, code=200):
        body = json.dumps(obj, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            return self.send_json({"ok": True})
        if path == "/status":
            return self.send_json(snapshot())
        self.send_error(404)


ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
