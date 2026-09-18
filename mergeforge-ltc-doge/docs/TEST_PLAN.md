# MergeForge 0.1.2 Physical Acceptance Test

1. Build both local images.
2. Install/start only through Umbrel lifecycle controls.
3. Confirm dashboard `/api/health` returns version 0.1.2.
4. Confirm host listens on 3333 and does not expose c2pool API 8080 directly.
5. Wait until c2pool reports backend readiness.
6. Configure LG07 to `stratum+tcp://UMBREL_IP:3333`, username = `LTC_ADDRESS,DOGE_ADDRESS.LG07`, password = `x`.
7. Confirm subscribe/authorize and incoming jobs.
8. Run for at least 60 minutes.
9. Record accepted, rejected, stale and duplicate shares.
10. Restart app through `umbreld client apps.restart.mutate` and confirm persistent state survives.
11. Verify no wallet private key or seed is stored anywhere in app data.
12. Do not publish as production until LTC/DOGE reward behavior is verified from authoritative backend records.
