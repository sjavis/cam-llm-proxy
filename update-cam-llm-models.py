#!/usr/bin/env python3

import json
import os
import shutil
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = "https://llm.hpc.cam.ac.uk"
SETTINGS_FILE = Path.home() / ".claude" / "settings.json"


def get_models():
    api_key = os.environ.get("CAMLLM_API_KEY")

    if not api_key:
        print("Error: CAMLLM_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    url = f"{BASE_URL}/v1/models"

    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as e:
        print(f"Error: /v1/models returned HTTP {e.code}", file=sys.stderr)
        print(e.read().decode(errors="replace"), file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error connecting to {url}: {e}", file=sys.stderr)
        sys.exit(1)

    models = [
        item["id"]
        for item in data.get("data", [])
        if isinstance(item, dict) and item.get("id")
    ]

    if not models:
        print("Error: /v1/models returned no models", file=sys.stderr)
        sys.exit(1)

    return sorted(set(models), key=str.casefold)


def update_settings(models):
    if not SETTINGS_FILE.exists():
        print(f"Error: {SETTINGS_FILE} does not exist", file=sys.stderr)
        sys.exit(1)

    # Parse the existing settings first. This means a failed/invalid
    # settings file won't be overwritten.
    try:
        with SETTINGS_FILE.open() as f:
            settings = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {SETTINGS_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    # Create a backup.
    backup = SETTINGS_FILE.with_suffix(".json.bak")
    shutil.copy2(SETTINGS_FILE, backup)

    # Ensure modelPicker exists.
    model_picker = settings.setdefault("modelPicker", {})

    # Preserve any other modelPicker settings, replacing only options.
    model_picker["options"] = [
        {"model": model}
        for model in models
    ]

    # Write atomically via a temporary file.
    temp = SETTINGS_FILE.with_suffix(".json.tmp")

    with temp.open("w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")

    temp.replace(SETTINGS_FILE)

    print(f"Updated {SETTINGS_FILE}")
    print(f"Found {len(models)} models:")
    for model in models:
        print(f"  {model}")
    print(f"Backup: {backup}")


def main():
    models = get_models()
    update_settings(models)


if __name__ == "__main__":
    main()
