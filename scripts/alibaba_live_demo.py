from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from connectors.http.fetcher import ProductFetcher

url = input("Alibaba Product URL: ").strip()

fetcher = ProductFetcher()

html = fetcher.fetch(url)

Path("sample_alibaba.html").write_text(html, encoding="utf-8")

print(f"Saved HTML ({len(html)} bytes)")
