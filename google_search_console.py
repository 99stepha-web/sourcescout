from pathlib import Path
import json
import sys
import time

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_URL = "https://sourcescout.store/"
DOMAIN_PROPERTY = "sc-domain:sourcescout.store"
SITEMAP_URL = "https://sourcescout.store/sitemap.xml"

ROOT = Path(__file__).resolve().parent
CREDENTIALS_FILE = ROOT / "google_credentials.json"
TOKEN_FILE = ROOT / "google_token.json"
INSPECTED_STATE_FILE = ROOT / "data" / "google_inspected_urls.json"

SCOPES = [
    "https://www.googleapis.com/auth/webmasters",
]


def authenticate():
    creds = None

    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                SCOPES,
            )
        except Exception:
            creds = None

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not CREDENTIALS_FILE.exists():
            raise SystemExit(
                "\n❌ Missing google_credentials.json\n"
                "Create/download an OAuth Desktop App credential "
                "from Google Cloud Console and place it at:\n"
                f"{CREDENTIALS_FILE}\n"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES,
        )

        creds = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent",
        )

        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return creds


def build_service():
    creds = authenticate()

    return build(
        "searchconsole",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )


def submit_sitemap(service):
    print("\n========== SITEMAP SUBMISSION ==========")

    service.sitemaps().submit(
        siteUrl=DOMAIN_PROPERTY,
        feedpath=SITEMAP_URL,
    ).execute()

    print(f"✅ Sitemap submitted: {SITEMAP_URL}")


def inspect_url(service, url):
    result = (
        service.urlInspection()
        .index()
        .inspect(
            body={
                "inspectionUrl": url,
                "siteUrl": DOMAIN_PROPERTY,
                "languageCode": "en-US",
            }
        )
        .execute()
    )

    inspection = result.get(
        "inspectionResult",
        {},
    )

    status = inspection.get(
        "indexStatusResult",
        {},
    )

    print("\n----------------------------------------")
    print(f"URL: {url}")
    print(
        f"Verdict: "
        f"{status.get('verdict', 'UNKNOWN')}"
    )
    print(
        f"Coverage: "
        f"{status.get('coverageState', 'UNKNOWN')}"
    )
    print(
        f"Robots: "
        f"{status.get('robotsTxtState', 'UNKNOWN')}"
    )
    print(
        f"Indexing: "
        f"{status.get('indexingState', 'UNKNOWN')}"
    )
    print(
        f"Last crawl: "
        f"{status.get('lastCrawlTime', 'UNKNOWN')}"
    )

    return result


def get_sitemap(service):
    print("\n========== SITEMAP STATUS ==========")

    result = (
        service.sitemaps()
        .get(
            siteUrl=DOMAIN_PROPERTY,
            feedpath=SITEMAP_URL,
        )
        .execute()
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


def load_inspected_state():
    if not INSPECTED_STATE_FILE.exists():
        return {}

    try:
        return json.loads(INSPECTED_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_inspected_state(state):
    INSPECTED_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    INSPECTED_STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def filter_new_urls(urls):
    """Return only URLs never previously inspected."""
    state = load_inspected_state()
    return [url for url in urls if url not in state]


def inspect_new_urls(service, urls):
    """
    Inspect only URLs not already marked as inspected, then record
    them as inspected. Distinguishes never-inspected / previously
    inspected / newly published without re-checking old URLs.
    """
    state = load_inspected_state()
    new_urls = [url for url in urls if url not in state]

    if not new_urls:
        print("\nℹ️ No newly published URLs to inspect.")
        return []

    results = []

    for url in new_urls:
        result = inspect_url(service, url)
        results.append(result)
        state[url] = {"status": "inspected", "last_checked": time.strftime("%Y-%m-%d")}

    save_inspected_state(state)

    return results


def main():
    service = build_service()

    submit_sitemap(service)

    if len(sys.argv) > 1:
        for url in sys.argv[1:]:
            inspect_url(service, url)

    get_sitemap(service)

    print(
        "\n✅ Google Search Console automation complete."
    )


if __name__ == "__main__":
    main()
