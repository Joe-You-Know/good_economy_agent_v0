import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List


class LiveHttpClient:
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = int(timeout_seconds)

    def get_json(self, url: str, headers: Dict[str, str] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if params:
            query = urllib.parse.urlencode({key: value for key, value in params.items() if value is not None})
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{query}"
        return self._request_json("GET", url, headers=headers)

    def post_form_json(self, url: str, headers: Dict[str, str] = None, form: Dict[str, Any] = None) -> Dict[str, Any]:
        body = urllib.parse.urlencode(form or {}).encode("utf-8")
        request_headers = {"Content-Type": "application/x-www-form-urlencoded", **(headers or {})}
        return self._request_json("POST", url, headers=request_headers, data=body)

    def _request_json(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        data: bytes = None,
    ) -> Dict[str, Any]:
        request_headers = {"Accept": "application/json", **(headers or {})}
        request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw) if raw else {}
                return {
                    "ok": True,
                    "status": response.status,
                    "url": _redact_url(url),
                    "data": parsed,
                }
        except urllib.error.HTTPError as exc:
            return {
                "ok": False,
                "status": exc.code,
                "url": _redact_url(url),
                "error": _safe_error_body(exc),
            }
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return {
                "ok": False,
                "status": None,
                "url": _redact_url(url),
                "error": str(exc),
            }


class CourtListenerClient:
    def __init__(self, base_url: str, token: str = "", http: LiveHttpClient = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.http = http or LiveHttpClient()

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    def search_case_law(self, query: str, page_size: int = 5, semantic: bool = False) -> Dict[str, Any]:
        if not self.configured:
            return _not_configured("CourtListener token or base URL is missing.")
        response = self.http.get_json(
            f"{self.base_url}/search/",
            headers=self._headers(),
            params={
                "q": query,
                "type": "o",
                "semantic": "true" if semantic else None,
                "page_size": int(page_size),
            },
        )
        if not response["ok"]:
            return response
        results = response["data"].get("results", [])
        return {
            "ok": True,
            "status": response["status"],
            "count": response["data"].get("count"),
            "results": [_normalize_courtlistener_result(item) for item in results[:page_size]],
        }

    def citation_lookup_text(self, text: str) -> Dict[str, Any]:
        if not self.configured:
            return _not_configured("CourtListener token or base URL is missing.")
        return self.http.post_form_json(
            f"{self.base_url}/citation-lookup/",
            headers=self._headers(),
            form={"text": text},
        )

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Token {self.token}"}


class GitHubClient:
    def __init__(self, base_url: str, token: str = "", http: LiveHttpClient = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.http = http or LiveHttpClient()

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def search_issues(self, query: str, limit: int = 5) -> Dict[str, Any]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.http.get_json(
            f"{self.base_url}/search/issues",
            headers=headers,
            params={"q": query, "per_page": int(limit)},
        )
        if not response["ok"]:
            return response
        items = response["data"].get("items", [])
        return {
            "ok": True,
            "status": response["status"],
            "count": response["data"].get("total_count"),
            "results": [_normalize_github_issue(item) for item in items[:limit]],
        }


class OpenLawsClient:
    def __init__(self, base_url: str, token: str = "", http: LiveHttpClient = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.http = http or LiveHttpClient()

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        if not self.configured:
            return _not_configured("OpenLaws base URL is missing. Set OPENLAWS_API_BASE_URL or config.openlaws_api_base_url.")
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.http.get_json(
            f"{self.base_url}/search",
            headers=headers,
            params={"q": query, "limit": int(limit)},
        )
        if not response["ok"]:
            return response
        data = response["data"]
        raw_results = data.get("results", data if isinstance(data, list) else [])
        return {
            "ok": True,
            "status": response["status"],
            "count": data.get("count") if isinstance(data, dict) else len(raw_results),
            "results": raw_results[:limit] if isinstance(raw_results, list) else [],
        }


def _normalize_courtlistener_result(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "case_name": item.get("caseName") or item.get("caseNameFull"),
        "court": item.get("court"),
        "date_filed": item.get("dateFiled"),
        "citations": item.get("citation", []),
        "absolute_url": item.get("absolute_url"),
        "status": item.get("status"),
        "snippet": _strip_markup(_first_opinion_snippet(item)),
    }


def _normalize_github_issue(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": item.get("title"),
        "html_url": item.get("html_url"),
        "repository_url": item.get("repository_url"),
        "state": item.get("state"),
        "labels": [label.get("name") for label in item.get("labels", []) if isinstance(label, dict)],
        "body_excerpt": str(item.get("body") or "")[:4000],
        "comments": item.get("comments"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def _first_opinion_snippet(item: Dict[str, Any]) -> str:
    opinions = item.get("opinions") or []
    if opinions and isinstance(opinions[0], dict):
        return opinions[0].get("snippet") or ""
    return item.get("snippet") or ""


def _strip_markup(value: str) -> str:
    return str(value or "").replace("<mark>", "").replace("</mark>", "").strip()


def _not_configured(reason: str) -> Dict[str, Any]:
    return {"ok": False, "status": "not_configured", "error": reason, "results": []}


def _safe_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return "no response body"
    return body[:500] + ("..." if len(body) > 500 else "")


def _redact_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted_query = urllib.parse.urlencode([
        (key, "REDACTED" if "token" in key.lower() or "key" in key.lower() else value)
        for key, value in query
    ])
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, redacted_query, parsed.fragment))
