# MergeForge Community Store — Initial Developer Package

This archive contains a first installable/developer-ready Umbrel Community App for **MergeForge**, a private Litecoin + Dogecoin Scrypt merged-mining hub inspired by the engineering discipline used for DigiForge.

## Important status

Version **0.1.0 is a developer preview**. It is designed to be installed, started, and tested with a real Lucky Miner LG07, but it is **not yet a public production release**. Do not treat accepted shares as proof that LTC or DOGE block payout behavior has been fully validated. Physical acceptance testing is still required before public release.

## Initial backend choice

The original specification requested two pruned full nodes plus a custom AuxPoW Stratum engine. That remains a valid long-term architecture, but it is not the simplest safe first milestone. This initial package uses **c2pool** in private solo mode because its current LTC implementation includes Scrypt Stratum, VARDIFF, embedded Litecoin/Dogecoin SPV backends, and LTC+DOGE merged mining. This keeps the first app small enough to validate on real hardware before we add optional full-node mode.

This is a deliberate simplification, not a silent change.

## What is included

- Umbrel app manifest and Compose packaging
- MergeForge custom dark dashboard
- c2pool source-build container pinned to `v0.2.0`
- Persistent c2pool state under `${APP_DATA_DIR}/data/c2pool`
- LG07-facing Scrypt Stratum on host port `3333`
- Umbrel-authenticated dashboard via `app_proxy`
- No wallet private keys, seeds, or Docker socket
- No privileged containers
- Conservative Docker log limits
- Public gift/support addresses and QR codes, styled like DigiForge
- Local setup storage with restrictive permissions
- Build and validation scripts
- Refined master project prompt in `docs/MASTER_PROMPT.md`

## First install workflow

This package intentionally uses locally built images until the images are physically tested and published to GHCR by the project owner.

```bash
cd mergeforge-initial/mergeforge-ltc-doge
./scripts/build-images.sh
```

After the images build, copy the community-store directory into your private development repository or Umbrel Community App Store workflow. Do not develop directly inside Umbrel's managed app-store checkout.

## LG07 initial settings

- Pool: `stratum+tcp://YOUR-UMBREL-IP:3333`
- Username: your Litecoin receiving address
- Password: `x`

The first physical test should confirm the exact worker/payout behavior used by the selected c2pool release before public release.

## Planned refinement after first physical test

1. Confirm LG07 subscribe/authorize/job/share flow.
2. Confirm server-side accepted/rejected shares.
3. Confirm LTC and DOGE merged-mining candidate behavior.
4. Verify payout/address behavior on a safe network path before trusting mainnet rewards.
5. Decide whether to retain embedded SPV mode or add an **Advanced Full Node Mode** with official pruned Litecoin Core and Dogecoin Core containers.
6. Pin final multi-arch production images by immutable registry digest.
7. Add richer charts/history only after authoritative backend fields are mapped.

## Security

MergeForge never asks for seed phrases or private keys. Support/gift addresses in the dashboard are public receiving addresses only.
