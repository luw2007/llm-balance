"""
FoxCode third-party relay handler (package query only)
"""

from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, PlatformTokenInfo, ModelTokenInfo, CostInfo
from ..config import PlatformConfig


class FoxCodeHandler(BasePlatformHandler):
    """FoxCode relay platform handler (only model package query is implemented)."""

    @classmethod
    def get_default_config(cls) -> dict:
        """Default configuration for FoxCode package query via cookie auth."""
        return {
            "display_name": "FoxCode",
            "handler_class": "FoxCodeHandler",
            "description": "FoxCode relay (package only)",
            "api_url": "https://foxcode.rjj.cc/api/user/dashboard",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            },
            "params": {},
            "data": {},
            # Keep disabled by default to avoid affecting default cost runs
            "enabled": False,
            # Cookie domain where auth_token is stored
            "cookie_domain": "foxcode.rjj.cc",
        }

    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config

    def get_platform_name(self) -> str:
        return "FoxCode"

    def get_balance(self) -> CostInfo:
        """Return cost info using dashboard history as Spent.

        - Balance display is not applicable for this relay; we mark it as '-'
        - Spent = sum of history plan.price (CNY)
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for FoxCode")

        headers = (self.config.headers or {}).copy()

        # Acquire cookies and auth token (same as in get_model_tokens)
        cookies = {}
        domains_to_try = []
        if getattr(self.config, 'cookie_domain', None):
            domains_to_try.append(self.config.cookie_domain)
        for d in [".foxcode.rjj.cc", ".rjj.cc", "rjj.cc"]:
            if d not in domains_to_try:
                domains_to_try.append(d)

        for domain in domains_to_try:
            try:
                cookies = self._get_cookies(domain)
                if cookies:
                    break
            except Exception:
                continue

        if not cookies:
            raise ValueError(
                f"No authentication cookies found for FoxCode. Please ensure you are logged in to {domains_to_try[0]} in {self.browser} browser."
            )

        auth_token = None
        for key in ["auth_token", "token", "Authorization", "authorization"]:
            if key in cookies and cookies[key]:
                auth_token = cookies[key]
                break
        if not auth_token:
            raise ValueError("FoxCode auth_token not found in cookies. Please login and try again.")

        headers['authorization'] = f"Bearer {auth_token}"

        # Request dashboard
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
        )

        if not response:
            raise ValueError("No response from FoxCode dashboard API")

        # Extract spent from subscription history
        spent = 0.0
        try:
            data = response.get('data', {}) if isinstance(response, dict) else {}
            subscription = data.get('subscription', {}) if isinstance(data, dict) else {}
            history = subscription.get('history', [])
            if isinstance(history, dict):
                history = list(history.values())
            if isinstance(history, list):
                for h in history:
                    if not isinstance(h, dict):
                        continue
                    plan = h.get('plan', {}) if isinstance(h.get('plan'), dict) else {}
                    price = plan.get('price') if plan else h.get('price')
                    try:
                        if price is not None:
                            spent += float(str(price).replace(',', '').strip())
                    except Exception:
                        continue
        except Exception:
            spent = 0.0

        # Balance is not applicable, set '-' (formatters will display '-')
        balance_placeholder = "-"

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance_placeholder,  # type: ignore
            currency='CNY',
            spent=spent,
            spent_currency='CNY',
            raw_data=response
        )

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Query FoxCode dashboard using cookie-derived Bearer token and parse subscription packages.

        Authentication:
            - Read `auth_token` from browser cookies for domain `foxcode.rjj.cc` (or fallbacks)
            - Set header: authorization: Bearer <auth_token>

        Data source:
            - GET https://foxcode.rjj.cc/api/user/dashboard
            - Use data.subscription.active from the response

        Models:
            - This relay serves models: "claude,gpt-5" (reported in the model field)
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for FoxCode")

        headers = (self.config.headers or {}).copy()

        # Acquire cookies from the configured domain, with domain fallbacks
        cookies = {}
        domains_to_try = []
        if getattr(self.config, 'cookie_domain', None):
            domains_to_try.append(self.config.cookie_domain)
        # Additional fallbacks that may store the auth cookie
        for d in [".foxcode.rjj.cc", ".rjj.cc", "rjj.cc"]:
            if d not in domains_to_try:
                domains_to_try.append(d)

        for domain in domains_to_try:
            try:
                cookies = self._get_cookies(domain)
                if cookies:
                    break
            except Exception:
                # Try next domain silently; detailed errors are not helpful across multiple attempts
                continue

        if not cookies:
            raise ValueError(
                f"No authentication cookies found for FoxCode. Please ensure you are logged in to {domains_to_try[0]} in {self.browser} browser."
            )

        # Extract auth token from cookies
        auth_token = None
        for key in ["auth_token", "token", "Authorization", "authorization"]:
            if key in cookies and cookies[key]:
                auth_token = cookies[key]
                break

        if not auth_token:
            raise ValueError("FoxCode auth_token not found in cookies. Please login and try again.")

        headers['authorization'] = f"Bearer {auth_token}"

        # Make the dashboard request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
        )

        if not response:
            raise ValueError("No response from FoxCode dashboard API")

        models = self._extract_models_from_dashboard(response)

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=models,
            raw_data=response
        )

    def _extract_models_from_dashboard(self, response: Dict[str, Any]) -> List[ModelTokenInfo]:
        """Extract ModelTokenInfo list from dashboard response using data.subscription.active.

        The schema is not strictly defined, so this uses a best-effort approach:
            - Look for list at data.subscription.active
            - For each item, attempt to read package name and quotas
            - Map totals/remaining/used from common keys
        """
        data = response if isinstance(response, dict) else {}
        subscription = data.get('data', {}).get('subscription', {}) if isinstance(data.get('data'), dict) else {}
        active = subscription.get('active', [])

        # If active is a dict with items inside, convert to list
        if isinstance(active, dict):
            # Prefer values if it looks like a mapping
            active = list(active.values())

        if not isinstance(active, list):
            active = []

        results: List[ModelTokenInfo] = []
        default_model_name = "claude,gpt-5"

        for item in active:
            if not isinstance(item, dict):
                # Unknown item format; skip
                continue

            # Prefer nested plan info when present
            plan = item.get('plan') if isinstance(item.get('plan'), dict) else {}

            # Package column should only display human name when available
            package_name = str(
                (plan.get('name') if plan else None)
                or item.get('name')
                or item.get('title')
                or item.get('plan_name')
                or item.get('id')
                or 'Subscription'
            )

            # Heuristics to extract numeric fields
            def _num(v) -> float:
                try:
                    if v is None:
                        return 0.0
                    if isinstance(v, (int, float)):
                        return float(v)
                    # Handle strings like "123", "123.45"
                    s = str(v).strip()
                    # Remove common separators
                    s = s.replace(',', '')
                    return float(s)
                except Exception:
                    return 0.0

            # FoxCode-specific mapping with real structure support:
            #  - plan.quotaLimit -> Total
            #  - quotaRemaining  -> Remaining (preferred)
            #  - quotaUsed       -> Used (preferred)
            #  - If missing, fallback: Remaining = plan.duration; Used = Total - Remaining
            total = _num((plan.get('quotaLimit') if plan else None) or item.get('quotaLimit'))
            remaining = _num(item.get('quotaRemaining'))
            used = _num(item.get('quotaUsed'))

            # Common key guesses
            key_candidates = {
                'remaining': ['remaining', 'left', 'balance', 'remains', 'rest', 'available'],
                'used': ['used', 'usage', 'consumed'],
                'total': ['quota', 'limit', 'total', 'tokens', 'credits', 'count', 'amount']
            }

            # Extract direct numeric fields
            if remaining == 0.0:
                for k in key_candidates['remaining']:
                    if k in item:
                        remaining = _num(item.get(k))
                        break
            if used == 0.0:
                for k in key_candidates['used']:
                    if k in item:
                        used = _num(item.get(k))
                        break
            if total == 0.0:
                for k in key_candidates['total']:
                    if k in item:
                        total = _num(item.get(k))
                        break

            # Try nested common structures, e.g., item['quota'] = {'total': 1000, 'used': 100}
            nested_quota = item.get('quota') if isinstance(item.get('quota'), dict) else None
            if nested_quota:
                total = max(total, _num(nested_quota.get('total')))
                used = max(used, _num(nested_quota.get('used')))
                remaining = max(remaining, _num(nested_quota.get('remaining')))

            # Fallback to plan.duration for remaining if still zero and plausible
            if remaining == 0.0 and plan:
                remaining = _num(plan.get('duration'))

            # Infer/finalize values
            if total and remaining:
                used = max(0.0, total - remaining)
            elif total and used and not remaining:
                remaining = max(0.0, total - used)
            elif used and remaining and not total:
                total = used + remaining

            # Clamp negatives defensively
            total = max(0.0, total)
            remaining = max(0.0, remaining)
            used = max(0.0, used)

            results.append(ModelTokenInfo(
                model=default_model_name,
                package=package_name,
                remaining_tokens=remaining,
                used_tokens=used,
                total_tokens=total
            ))

        # Sort by remaining descending for readability
        results.sort(key=lambda x: x.remaining_tokens, reverse=True)
        return results
