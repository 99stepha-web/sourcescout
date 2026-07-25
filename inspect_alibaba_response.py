import json
import os

import requests
from dotenv import load_dotenv

load_dotenv(".env")

api_key = os.getenv("PILOTERR_API_KEY")

response = requests.get(
    "https://api.piloterr.com/v2/alibaba/search",
    headers={
        "x-api-key": api_key,
    },
    params={
        "query": "portable solar power station",
    },
    timeout=30,
)

print("STATUS:", response.status_code)
print()

data = response.json()

print(
    json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    )[:15000]
)
