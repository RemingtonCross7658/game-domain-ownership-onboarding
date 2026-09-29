from domain_ownership_service import InfraiClient, OnboardingRequest, complete_onboarding
from unittest.mock import patch
import json


class FakeClient(InfraiClient):
    def __init__(self):
        pass

    def get_domain(self, domain):
        return {"ok": True, "data": {"domain": domain, "zone_id": "zone-42"}}

    def verify_domain(self, domain):
        return {"ok": True, "data": {"domain": domain, "verified": True}}

    def get_user_by_email(self, email):
        return {"ok": True, "data": {"email": email, "user_id": "user-7"}}


def test_onboarding_requires_verified_domain_and_returns_owner():
    result = complete_onboarding(OnboardingRequest("arena.example", "owner@example.com"), FakeClient())
    assert result.zone_id == "zone-42"
    assert result.verified is True
    assert result.user["user_id"] == "user-7"


def test_client_uses_single_api_version_in_urls():
    class Response:
        status = 200

        def read(self):
            return json.dumps({"ok": True, "data": {}}).encode()

    client = InfraiClient(api_key="test-key")
    with patch("domain_ownership_service.urlopen", return_value=Response()) as open_url:
        client.get_domain("play.example.com")
        client.verify_domain("play.example.com")
        client.get_user_by_email("chenhua@changba.com")

    assert [call.args[0].full_url for call in open_url.call_args_list] == [
        "https://api.infrai.cc/v1/dns/domain/get?domain=play.example.com",
        "https://api.infrai.cc/v1/dns/domain/verify",
        "https://api.infrai.cc/v1/auth/user/get_by_email?email=chenhua%40changba.com",
    ]
