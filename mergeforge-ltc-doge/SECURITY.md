# Security Policy

MergeForge is non-custodial. Never enter private keys, seed phrases, mnemonics, or wallet files into the app.

Public receiving addresses are sufficient for mining configuration and support gifts.

Security goals:
- expose only Umbrel UI and Stratum;
- never expose node/admin RPC or internal APIs to LAN;
- no Docker socket;
- no privileged containers;
- persistent data survives updates;
- configuration-changing APIs remain behind Umbrel authentication;
- fail closed if the mining backend is not ready.

Report security issues privately to the project owner before public disclosure.
