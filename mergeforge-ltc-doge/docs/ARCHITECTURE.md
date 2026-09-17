# MergeForge 0.1.1 Architecture

## Container flow

```text
Umbrel app_proxy
      |
      v
MergeForge web :8096  ----HTTP----> c2pool API :8080
                                     |
LAN LG07 ---- Stratum :3333 ---------+
                                     |
                    +----------------+----------------+
                    |                                 |
                    v                                 v
          Litecoin Core :9332              Dogecoin Core :22555
          pruned authoritative             pruned authoritative
          parent-chain node                AuxPoW merged-chain node
```

## External exposure

| Port | Exposure | Purpose |
|---|---|---|
| Umbrel app URL | Umbrel proxy | Authenticated dashboard |
| 3333/tcp | LAN | Scrypt Stratum for LG07 |
| 8080/tcp | Internal only | c2pool API/dashboard backend |

## Persistence

- `${APP_DATA_DIR}/data/litecoin` — pruned Litecoin Core blockchain state.
- `${APP_DATA_DIR}/data/dogecoin` — pruned Dogecoin Core blockchain state.
- `${APP_DATA_DIR}/data/c2pool` — c2pool state, logs and found-block database.
- `${APP_DATA_DIR}/data/app` — MergeForge public configuration (no wallet secrets).
- `${APP_DATA_DIR}/config` — generated private node and c2pool configuration.
- `${APP_DATA_DIR}/secrets` — generated private RPC credentials.

## Security boundary

- No Docker socket.
- No host networking.
- All capabilities dropped.
- `no-new-privileges` enabled.
- No RPC/passwords exposed to LAN.
- No seed/private-key fields.
- Umbrel authentication protects the custom UI.

## Runtime design

MergeForge uses dedicated pruned Litecoin Core and Dogecoin Core containers as the authoritative chain nodes. c2pool provides Stratum V1, VARDIFF, solo-mining coordination and Litecoin/Dogecoin merged mining.

The Core RPC interfaces are available only on the dedicated MergeForge backend network. Litecoin and Dogecoin use outbound-only P2P synchronization and do not publish node RPC or P2P ports on the host. The only host-published MergeForge service port is Stratum TCP 3333 for the miner.
