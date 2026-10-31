"""
Opens a local page for correcting the labels of real CVs.

    python -m scripts.real_cv_label_app

It shows each CV's PDF next to a form (companies, roles, schools, degrees,
skills ...), saves into the label files under data/real_cv_eval, and can mark
a label as reviewed. It listens on 127.0.0.1 only and sends nothing anywhere.
Stop it with Ctrl+C.
"""

import argparse
import json
import webbrowser
from pathlib import Path

from app.evaluation.label_editor import create_server
from app.evaluation.real_cvs import INDEX_NAME


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", default="data/real_cv_eval")
    parser.add_argument("--cv-folder", help="default: the folder recorded by `real_cv_prepare draft`")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    labels = Path(args.labels)
    folder = args.cv_folder

    if folder is None:
        index = labels / INDEX_NAME

        if not index.is_file():
            raise SystemExit("Run `python -m scripts.real_cv_prepare draft` first.")

        folder = json.loads(index.read_text(encoding="utf-8"))["cv_folder"]

    server = create_server(labels, Path(folder), args.port)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"

    print(f"Label editor at {url}  (Ctrl+C to stop)")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
