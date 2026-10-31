"""
Writes the API's OpenAPI description to frontend/openapi.json.

    python -m scripts.export_openapi

The frontend's TypeScript types are generated from that file
(`npm run gen:api` in frontend/), so a change to a response shape shows up as a
type error in the frontend instead of a broken page. A test fails when the file
is out of date.
"""

import json
from pathlib import Path

from app.main import app

TARGET = Path("frontend/openapi.json")


def render() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    TARGET.write_text(render(), encoding="utf-8")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
