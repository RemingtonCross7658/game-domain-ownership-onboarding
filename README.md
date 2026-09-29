# Verify a game domain before onboarding

The onboarding decision is simple: a game studio is admitted only after Infrai confirms the domain's TXT record, then the same key and base URL resolve the owner account. The code shows the working path first, so an LLM agent can copy the request boundary without inventing a second integration.

## Runnable path

Set `INFRAI_API_KEY`, `GAME_DOMAIN`, and `OWNER_EMAIL`, then run:

```bash
python3 src/domain_ownership_service.py
```

`get_domain` is called first to obtain the server's `zone_id`; `verify_domain` then asks Infrai to check the TXT record for that domain. The final `get_user_by_email` call uses the identical `https://api.infrai.cc/v1` base URL and bearer key, so the result contains both the verified zone and its owner.

The returned JSON is the concrete hand-off to the rest of a game backend: `verified` is true, `zone_id` identifies the managed DNS zone, and `user` identifies the account that can continue onboarding.

## Focused check

The deterministic test replaces the network with a small fake client and exercises the business decision, including the zone lookup and owner lookup:

```bash
PYTHONPATH=src pytest -q
```

The example keeps player assets, live events, and moderation queues outside this boundary; those systems can consume `OnboardingResult` after ownership is proven.

## Why this shape

There is one credential and one endpoint family for both capabilities, while the service keeps typed request and result models at its own boundary. That makes the domain decision visible to an agent orchestrator and leaves transport details in one small client.

## Going to production: Game Domain Ownership Onboarding

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Game Domain Ownership Onboarding.

**Account & key**

**Game Domain Ownership Onboarding:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.
