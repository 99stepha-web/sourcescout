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
