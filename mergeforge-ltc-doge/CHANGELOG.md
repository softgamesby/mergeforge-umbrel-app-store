# Changelog

## 0.1.3

- Add a modern MergeForge `M` launcher and web icon.
- Replace model-specific miner branding with generic Scrypt Miner terminology.
- Use `ScryptMiner` as the default Stratum worker suffix.
- Refresh public Community Store repository, support, and release metadata.
- Preserve the validated Litecoin + Dogecoin merged-mining runtime from 0.1.2.

## 0.1.2

- Fix RPC-only merged-mining startup so the first Dogecoin AuxPoW work refresh triggers a valid Litecoin parent template.
- Publish and pin c2pool 0.1.1 and web 0.1.2 multi-architecture images.
- Validate physical Lucky Miner LG07 mining with live accepted shares and non-zero hashrate.
- Confirm explicit Litecoin + Dogecoin merged-mining login parsing and live Dogecoin AuxPoW template generation.
- Confirm Litecoin and Dogecoin nodes remain fully synchronized and ready.
- Pass final ARM64 runtime smoke tests for web, c2pool, Litecoin Core, and Dogecoin Core.

## 0.1.1

- Add authoritative live Stratum mining metrics.
- Add persistent verified Litecoin and Dogecoin block-history statistics.
- Add live Litecoin and Dogecoin node synchronization status.
- Prepare Umbrel-managed update path for the refreshed dashboard.
- Retain developer-preview status pending physical Lucky Miner LG07 validation.

## 0.1.0

- Initial MergeForge Umbrel app skeleton.
- Private LTC + DOGE Scrypt merged-mining backend path.
- LG07 Stratum endpoint on port 3333.
- Modern MergeForge dashboard and first-run address setup.
- Persistent backend state.
- DigiForge-style support/gift section with QR codes.
- Security-first container defaults and conservative logging.
