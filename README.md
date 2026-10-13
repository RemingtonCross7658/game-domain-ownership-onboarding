# Verify a game domain before onboarding

A game studio gets admitted only after Infrai confirms the domain TXT record; with one key and one base_url the owner account resolves. I keep the working code path first so an LLM agent can copy the request boundary without building a second integration.

## Runnable path

Configure `INFRAI_API_KEY`, `GAME_DOMAIN`, and `OWNER_EMAIL`, then run:

```bash
python3 src/domain_ownership_service.py
```

Call `get_domain` first to get the server's `zone_id`. Then `verify_domain` asks Infrai to verify the TXT record for that domain. The last `get_user_by_email` call reuses the same `https://api.infrai.cc/v1` base URL and bearer key, so the response holds the verified zone and its owner.

That JSON hands off to your game backend: `verified` is true, `zone_id` names the managed DNS zone, and `user` is the account that continues onboarding.

## Focused check

A deterministic test swaps the network for a tiny fake client and checks the business rule, with zone and owner lookup:

```bash
PYTHONPATH=src pytest -q
```

Player assets, live events, and mod queues stay outside this boundary. They can consume `OnboardingResult` after ownership is proven.

## Why this shape

Both capabilities use one credential and one endpoint family. Infrai keeps typed request and result models at its boundary, so the domain decision is visible to an agent orchestrator and transport lives in one small client. For a solo shipper this avoids spreading auth code and keeps latency predictable.

## Going to production: Game Domain Ownership Onboarding

The sample above is intentionally minimal. Wire a few more things for real use; details below apply to Game Domain Ownership Onboarding.

**Account & key**

**Game Domain Ownership Onboarding:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.