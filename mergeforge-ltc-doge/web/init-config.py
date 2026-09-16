#!/usr/bin/env python3

import os
import secrets
import stat
from pathlib import Path

APP_DATA = Path(os.environ.get("APP_DATA_ROOT", "/app-data"))

SECRETS_DIR = APP_DATA / "secrets"
CONFIG_DIR = APP_DATA / "config"
DATA_DIR = APP_DATA / "data"

LITECOIN_DATA = DATA_DIR / "litecoin"
DOGECOIN_DATA = DATA_DIR / "dogecoin"
C2POOL_DATA = DATA_DIR / "c2pool"
WEB_DATA = DATA_DIR / "app"

BACKEND_SUBNET = "172.29.37.0/24"

LTC_RPC_USER = "mergeforge_ltc"
DOGE_RPC_USER = "mergeforge_doge"

SERVICE_UID = 1000
SERVICE_GID = 1000


def set_service_owner(path: Path) -> None:
    if os.geteuid() == 0:
        os.chown(path, SERVICE_UID, SERVICE_GID)


def ensure_directory(path: Path, mode: int = 0o700) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, mode)
    set_service_owner(path)


def load_or_create_secret(name: str) -> str:
    path = SECRETS_DIR / name

    if os.path.lexists(path):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise RuntimeError(f"Refusing unsafe secret path: {path}")

        os.chmod(path, 0o600)
        set_service_owner(path)
        value = path.read_text(encoding="utf-8").strip()

        if not value:
            raise RuntimeError(f"Secret file is empty: {path}")

        if ":" in value:
            raise RuntimeError(f"Secret contains unsupported ':' delimiter: {path}")

        return value

    value = secrets.token_urlsafe(32)

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    fd = os.open(path, flags, 0o600)

    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(value + "\n")

    os.chmod(path, 0o600)
    set_service_owner(path)
    return value


def write_private(path: Path, content: str) -> None:
    temp = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    fd = os.open(temp, flags, 0o600)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp, path)
        os.chmod(path, 0o600)
        set_service_owner(path)
    finally:
        if temp.exists():
            temp.unlink()


def main() -> None:
    for directory in (
        SECRETS_DIR,
        CONFIG_DIR,
        DATA_DIR,
        LITECOIN_DATA,
        DOGECOIN_DATA,
        C2POOL_DATA,
        WEB_DATA,
    ):
        ensure_directory(directory)

    ltc_password = load_or_create_secret("litecoin-rpc-password")
    doge_password = load_or_create_secret("dogecoin-rpc-password")

    litecoin_conf = f"""server=1
listen=0
daemon=0
printtoconsole=1
disablewallet=1
prune=8192
dbcache=512
txindex=0
rpcbind=0.0.0.0
rpcallowip={BACKEND_SUBNET}
rpcport=9332
rpcuser={LTC_RPC_USER}
rpcpassword={ltc_password}
"""

    dogecoin_conf = f"""server=1
listen=0
daemon=0
printtoconsole=1
disablewallet=1
prune=8192
dbcache=512
txindex=0
rpcbind=0.0.0.0
rpcallowip={BACKEND_SUBNET}
rpcport=22555
rpcuser={DOGE_RPC_USER}
rpcpassword={doge_password}
"""

    c2pool_conf = f"""solo: true
embedded_ltc: false
embedded_doge: false
blockchain: litecoin
stratum_port: 3333
web_port: 8080
http_host: "0.0.0.0"
ltc_rpc_host: litecoin
ltc_rpc_port: 9332
ltc_rpc_user: {LTC_RPC_USER}
ltc_rpc_password: "{ltc_password}"
coind_p2p_port: 0
merged:
  - "DOGE:98:dogecoin:22555:{DOGE_RPC_USER}:{doge_password}:0"
"""

    write_private(CONFIG_DIR / "litecoin.conf", litecoin_conf)
    write_private(CONFIG_DIR / "dogecoin.conf", dogecoin_conf)
    write_private(CONFIG_DIR / "c2pool.yml", c2pool_conf)

    print("MergeForge runtime directories and private configuration initialized.")


if __name__ == "__main__":
    main()
