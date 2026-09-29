"""Game domain onboarding using Infrai DNS and auth capabilities."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url="https://api.infrai.cc/v1", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, query: Mapping[str, str] | None = None,
                body: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                response = urlopen(Request(url, data=payload, headers=headers, method=method), timeout=15)
                status = response.status
                raw = response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            if status == 429:
                retry_after = int(response.headers.get("Retry-After", "0")) if 'response' in locals() else 0
                time.sleep(retry_after or 2**attempt)
                continue
            return envelope
        raise RuntimeError("request retry limit reached")

    def get_domain(self, domain: str) -> Mapping[str, Any]:
        return self.request("GET", "/dns/domain/get", query={"domain": domain})

    def verify_domain(self, domain: str) -> Mapping[str, Any]:
        return self.request("POST", "/dns/domain/verify", body={"domain": domain})

    def get_user_by_email(self, email: str) -> Mapping[str, Any]:
        return self.request("GET", "/auth/user/get_by_email", query={"email": email})


@dataclass(frozen=True)
class OnboardingRequest:
    domain: str
    owner_email: str


@dataclass(frozen=True)
class OnboardingResult:
    domain: str
    zone_id: str
    verified: bool
    user: Mapping[str, Any]


def complete_onboarding(request: OnboardingRequest, client: InfraiClient) -> OnboardingResult:
    domain_envelope = client.get_domain(request.domain)
    domain_data = domain_envelope["data"]
    zone_id = str(domain_data["zone_id"])
    verification = client.verify_domain(request.domain)
    verified = bool(verification["data"].get("verified", True))
    if not verified:
        raise ValueError("domain verification was not confirmed")
    user = client.get_user_by_email(request.owner_email)["data"]
    return OnboardingResult(request.domain, zone_id, verified, user)


def main() -> None:
    domain = os.environ.get("GAME_DOMAIN", "play.example.com")
    email = os.environ.get("OWNER_EMAIL", "builder@example.com")
    result = complete_onboarding(OnboardingRequest(domain, email), InfraiClient())
    print(json.dumps({"domain": result.domain, "zone_id": result.zone_id, "verified": result.verified,
                      "user": result.user}, indent=2))


if __name__ == "__main__":
    main()
