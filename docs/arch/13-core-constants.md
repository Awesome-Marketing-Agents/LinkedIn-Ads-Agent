# Module: Core Constants (API URLs & Scopes)

## Overview

`core/constants.py` holds LinkedIn API URLs, version, and OAuth scopes. These values are used by the auth and ingestion layers and should change only when LinkedIn updates their API.

---

## File Path

`src/linkedin_action_center/core/constants.py`

---

## Components & Explanation

- **`LINKEDIN_API_VERSION`** — API version string (`"202602"`). Sent in `LinkedIn-Version` header on every API call.
- **`OAUTH2_BASE_URL`** — `https://www.linkedin.com/oauth/v2` for authorization and token endpoints.
- **`INTROSPECT_URL`** — `https://www.linkedin.com/oauth/v2/introspectToken` for token introspection.
- **`API_BASE_URL`** — `https://api.linkedin.com/rest` for Marketing API.
- **`SCOPES`** — List of OAuth scopes: `r_ads`, `r_ads_reporting`, `r_basicprofile`.

---

## Relationships

- Used by `auth/manager.py` for OAuth URLs and scopes.
- Used by `ingestion/client.py` for API base URL and version header.
- No runtime configuration; constants only.

---

## Example Code Snippets

```python
from linkedin_action_center.core.constants import (
    API_BASE_URL,
    OAUTH2_BASE_URL,
    SCOPES,
    LINKEDIN_API_VERSION,
)

# Build auth URL
from urllib.parse import urlencode
params = {"response_type": "code", "scope": " ".join(SCOPES), ...}
url = f"{OAUTH2_BASE_URL}/authorization?{urlencode(params)}"

# API request
full_url = f"{API_BASE_URL}/adAccounts"
headers = {"LinkedIn-Version": LINKEDIN_API_VERSION}
```

---

## Edge Cases & Tips

- **API version**: LinkedIn may deprecate older versions; update `LINKEDIN_API_VERSION` when needed.
- **Scopes**: `r_ads` and `r_ads_reporting` are required for ads data; `r_basicprofile` for `/me`.
- **`.env` override**: `LINKEDIN_SCOPES` in `.env.example` is not used by this module; scopes come from `SCOPES` only.

---

## Architecture / Flow

```
auth/manager, ingestion/client
    |
    └── from linkedin_action_center.core.constants import ...
            └── Use URLs and SCOPES in requests
```

---

## Advanced Notes

- OAuth token endpoint: `{OAUTH2_BASE_URL}/accessToken`.
- Rest.li protocol: `X-Restli-Protocol-Version: 2.0.0` is set in the client, not in constants.
- Adding new scopes (e.g. `rw_ads`) requires LinkedIn app approval and user re-authorization.
