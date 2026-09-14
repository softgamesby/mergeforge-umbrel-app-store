# MergeForge 0.1.0 Architecture

## Container flow

```text
Umbrel app_proxy
      |
      v
MergeForge web :8096  ----HTTP----> c2pool API :8080
                                     |
LAN LG07 ---- Stratum :3333 ---------+
                                     |
                           embedded LTC + DOGE SPV
                           LTC parent / DOGE AuxPoW
```

## External exposure

| Port | Exposure | Purpose |
|---|---|---|
| Umbrel app URL | Umbrel proxy | Authenticated dashboard |
| 3333/tcp | LAN | Scrypt Stratum for LG07 |
| 8080/tcp | Internal only | c2pool API/dashboard backend |

## Persistence

- `${APP_DATA_DIR}/data/c2pool` — c2pool state, logs and found-block database.
- `${APP_DATA_DIR}/data/app` — MergeForge public configuration (no wallet secrets).

## Security boundary

- No Docker socket.
- No host networking.
- All capabilities dropped.
- `no-new-privileges` enabled.
- No RPC/passwords exposed to LAN.
- No seed/private-key fields.
- Umbrel authentication protects the custom UI.

## Why this differs from the long-form specification

The long-form design requests pruned full Litecoin/Dogecoin nodes plus a bespoke AuxPoW Stratum implementation. For the first physical milestone, MergeForge instead uses c2pool's current LTC+DOGE merged-mining path to minimize protocol-critical custom code. Full-node mode remains a Phase-2 feature after LG07 acceptance testing.
