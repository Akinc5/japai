import logging
from typing import Any
import requests

from worker.config import worker_settings
from worker.publishers.base import BasePublisher, EngagementMetrics, PublishRequest, PublishResult

logger = logging.getLogger("ja_assure.worker.buffer")


class BufferPublisher(BasePublisher):
    """Buffer API integration for publishing to social platforms (primarily LinkedIn).

    Supports:
    - Profile auto-discovery for connected channels.
    - Direct posting and scheduled posting.
    - Engagement metrics fetching where available.
    - Descriptive error handling for auth failures, missing profiles, and platform limits.
    """

    def __init__(
        self,
        access_token: str | None = None,
        profile_id_linkedin: str | None = None,
        api_base_url: str | None = None,
    ):
        self.access_token = access_token or worker_settings.BUFFER_ACCESS_TOKEN
        self.profile_id_linkedin = profile_id_linkedin or worker_settings.BUFFER_PROFILE_ID_LINKEDIN
        self.api_base_url = (api_base_url or worker_settings.BUFFER_API_URL).rstrip("/")
        self._cached_profiles: dict[str, str] = {}  # service_name -> profile_id

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "JA-Assure-Publisher/1.0",
        }

    def _discover_profile_id(self, platform: str) -> str | None:
        """Finds the connected Buffer profile/channel ID for the specified platform."""
        platform_normalized = platform.lower().strip()
        if platform_normalized == "linkedin" and self.profile_id_linkedin:
            return self.profile_id_linkedin

        if platform_normalized in self._cached_profiles:
            return self._cached_profiles[platform_normalized]

        url = f"{self.api_base_url}/profiles.json"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                profiles = resp.json()
                if isinstance(profiles, list):
                    for p in profiles:
                        service = (p.get("service") or "").lower()
                        pid = p.get("id")
                        if service and pid:
                            self._cached_profiles[service] = str(pid)

                # Return matching profile
                return self._cached_profiles.get(platform_normalized)
            else:
                logger.warning(
                    "Buffer profiles query failed: HTTP %s - %s",
                    resp.status_code,
                    resp.text[:200],
                )
        except Exception as exc:
            logger.error("Failed to query Buffer profiles: %s", exc)

        return None

    def publish(self, request: PublishRequest) -> PublishResult:
        if not self.access_token:
            return PublishResult(
                success=False,
                status="failed",
                error_message="Buffer access token is not configured (BUFFER_ACCESS_TOKEN is missing or empty)",
            )

        platform = request.platform.lower().strip()
        profile_id = self._discover_profile_id(platform)

        if not profile_id:
            return PublishResult(
                success=False,
                status="failed",
                error_message=(
                    f"No connected Buffer profile found for platform '{platform}'. "
                    f"Please connect a {platform.capitalize()} account in Buffer or set BUFFER_PROFILE_ID_{platform.upper()}."
                ),
            )

        url = f"{self.api_base_url}/updates/create.json"
        is_scheduled = request.scheduled_at is not None
        data: dict[str, Any] = {
            "profile_ids[]": profile_id,
            "text": request.text,
        }

        if is_scheduled and request.scheduled_at:
            data["scheduled_at"] = request.scheduled_at.isoformat()
        else:
            data["now"] = "true"

        try:
            resp = requests.post(url, headers=self._get_headers(), data=data, timeout=15)
            status_code = resp.status_code

            if status_code == 401:
                return PublishResult(
                    success=False,
                    status="failed",
                    error_message="Buffer authentication failed (HTTP 401): Invalid or expired BUFFER_ACCESS_TOKEN",
                    raw_response={"status_code": status_code, "body": resp.text[:300]},
                )

            if status_code == 429:
                return PublishResult(
                    success=False,
                    status="failed",
                    error_message="Buffer rate limit exceeded (HTTP 429): Please back off and retry later",
                    raw_response={"status_code": status_code, "body": resp.text[:300]},
                )

            resp_json = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}

            if status_code in (200, 201):
                updates = resp_json.get("updates", [])
                post_id = None
                if updates and isinstance(updates, list) and len(updates) > 0:
                    post_id = updates[0].get("id")

                final_status = "scheduled" if is_scheduled else "published"
                return PublishResult(
                    success=True,
                    status=final_status,
                    external_post_id=post_id or resp_json.get("id"),
                    raw_response=resp_json,
                )
            else:
                err_msg = resp_json.get("message") or resp.text[:250] or f"HTTP {status_code}"
                return PublishResult(
                    success=False,
                    status="failed",
                    error_message=f"Buffer API error ({status_code}): {err_msg}",
                    raw_response=resp_json,
                )

        except requests.exceptions.Timeout:
            return PublishResult(
                success=False,
                status="failed",
                error_message="Buffer request timed out after 15 seconds",
            )
        except requests.exceptions.RequestException as req_err:
            return PublishResult(
                success=False,
                status="failed",
                error_message=f"Network error communicating with Buffer API: {str(req_err)}",
            )
        except Exception as exc:
            return PublishResult(
                success=False,
                status="failed",
                error_message=f"Unexpected error during Buffer publishing: {type(exc).__name__}: {str(exc)}",
            )

    def fetch_analytics(self, external_post_id: str, platform: str) -> EngagementMetrics | None:
        if not self.access_token or not external_post_id:
            return None

        url = f"{self.api_base_url}/updates/{external_post_id}/interactions.json"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                interactions = data.get("interactions", [])
                # Aggregate interactions
                clicks = sum(1 for i in interactions if i.get("event") == "click")
                likes = sum(1 for i in interactions if i.get("event") in ("like", "favorite", "reaction"))
                comments = sum(1 for i in interactions if i.get("event") in ("comment", "reply"))
                shares = sum(1 for i in interactions if i.get("event") in ("retweet", "share"))
                impressions = data.get("reach") or data.get("impressions") or max(clicks + likes + comments + shares, 10)

                rate = round((likes + comments + shares + clicks) / max(impressions, 1) * 100, 2)
                return EngagementMetrics(
                    impressions=impressions,
                    likes=likes,
                    clicks=clicks,
                    comments=comments,
                    shares=shares,
                    engagement_rate=rate,
                    is_simulated=False,
                    raw_data=data,
                )
        except Exception as exc:
            logger.warning("Could not fetch Buffer analytics for post %s: %s", external_post_id, exc)

        return None

    def health_check(self) -> dict[str, Any]:
        if not self.access_token:
            return {"status": "unconfigured", "message": "BUFFER_ACCESS_TOKEN not set"}
        try:
            resp = requests.get(f"{self.api_base_url}/user.json", headers=self._get_headers(), timeout=5)
            if resp.status_code == 200:
                user = resp.json()
                return {
                    "status": "connected",
                    "user_id": user.get("id"),
                    "plan": user.get("plan"),
                }
            return {
                "status": "error",
                "http_status": resp.status_code,
                "message": resp.text[:200],
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}
