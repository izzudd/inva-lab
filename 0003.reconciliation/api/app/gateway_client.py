import json
import os
import urllib.request

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://gateway:8000")


def fetch_settlement(day: str) -> list[dict]:
    """Ambil seluruh halaman laporan settlement satu hari dari gateway."""
    payments: list[dict] = []
    page = 1

    while True:
        url = f"{GATEWAY_URL}/settlements/{day}?page={page}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())

        payments.extend(data["payments"])

        if page >= data["pages"]:
            return payments

        page += 1
