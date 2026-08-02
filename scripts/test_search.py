from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from affiliate.alibaba.search import AlibabaSearch

search = AlibabaSearch()


html = search.search("wireless earbuds")

with open("alibaba_result.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved HTML to alibaba_result.html")
