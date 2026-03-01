# Module: LinkedIn API Constants

## Overview

`constants.py` defines the LinkedIn Marketing API version, OAuth URLs, API base URL, and required OAuth scopes. These constants are used across the `linkedin/` and `core/security.py` modules.

---

## File Path

`backend/app/linkedin/constants.py`

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `LINKEDIN_API_VERSION` | `"202602"` | API versioning header (February 2026) |
| `OAUTH2_BASE_URL` | `"https://www.linkedin.com/oauth/v2"` | OAuth authorization and token endpoints |
| `INTROSPECT_URL` | `"https://www.linkedin.com/oauth/v2/introspectToken"` | Token introspection endpoint |
| `API_BASE_URL` | `"https://api.linkedin.com/rest"` | Marketing REST API base |
| `SCOPES` | `["r_ads", "r_ads_reporting", "r_basicprofile"]` | Required OAuth scopes |

---

## Code Snippet

```python
from app.linkedin.constants import API_BASE_URL, LINKEDIN_API_VERSION

headers = {
    "LinkedIn-Version": LINKEDIN_API_VERSION,  # "202602"
    "Authorization": f"Bearer {token}",
}
url = f"{API_BASE_URL}/adAccounts"  # https://api.linkedin.com/rest/adAccounts
```

---

## Relationships

- **Used by**: `core/security.py` (OAuth URLs, scopes, API version), `linkedin/client.py` (API base URL, version header)
