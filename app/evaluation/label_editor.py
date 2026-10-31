"""
A small web page for correcting the label files of real CVs.

It shows the CV's PDF next to a form, so labels are corrected without editing
JSON by hand. It is meant to run on the machine that holds the CVs:

- it listens on 127.0.0.1 only and checks the Host header, so other machines
  and (through DNS rebinding) other web pages cannot reach it;
- every change needs a token generated at start-up, so another web page open in
  the same browser cannot submit a form to it;
- the PDF is served only for a label whose file name resolves inside the CV
  folder;
- nothing is loaded from the internet and nothing is sent anywhere.

The label files stay what they were: plain JSON that `real_cv_prepare` and
`evaluate_real_cvs` read.
"""

import html
import re
import secrets
from dataclasses import dataclass
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse

from app.evaluation.field_eval import FIELDS
from app.evaluation.real_cvs import (
    DRAFT,
    REVIEWED,
    SECTIONS,
    LabelFile,
    load_labels,
    save_label,
    validate,
)

MAX_FORM_BYTES = 1_000_000
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,40}$")

FIELD_HELP = {
    "name": "Tên người trong CV",
    "companies": "Các công ty đã làm việc",
    "roles": "Các chức danh",
    "schools": "Trường học",
    "degrees": "Bằng cấp / chương trình học",
    "skills": "Kỹ năng CV liệt kê",
    "certifications": "Chứng chỉ, giấy phép",
}

TAG_FIELDS = (
    ("language", "Ngôn ngữ chính (vi, en, ...)"),
    ("industry", "Ngành (tự đặt, giữ cách viết nhất quán)"),
    ("layout", "Bố cục (single hoặc multi_column)"),
    ("pages", "Số trang"),
)

STYLE = """
body{font:15px/1.4 system-ui,sans-serif;margin:0;color:#1b1b1b;background:#f6f6f4}
header{padding:10px 16px;background:#fff;border-bottom:1px solid #ddd;display:flex;gap:16px;align-items:center}
header a{color:#0b5cad;text-decoration:none}
main.split{display:flex;height:calc(100vh - 49px)}
.pdf{flex:1 1 55%;border-right:1px solid #ddd}
.pdf iframe{width:100%;height:100%;border:0}
form{flex:1 1 45%;overflow:auto;padding:12px 16px;background:#fff}
label{display:block;margin:10px 0 2px;font-weight:600}
small{display:block;color:#666;font-weight:400}
textarea,input[type=text]{width:100%;box-sizing:border-box;font:inherit;padding:6px;border:1px solid #bbb;border-radius:4px}
.row{display:flex;gap:12px}.row>div{flex:1}
.sections label{display:inline-block;margin-right:12px;font-weight:400}
button{font:inherit;padding:8px 14px;margin:14px 8px 0 0;border:1px solid #0b5cad;background:#fff;color:#0b5cad;border-radius:4px;cursor:pointer}
button.primary{background:#0b5cad;color:#fff}
.msg{padding:8px 12px;margin:10px 0;border-radius:4px}.ok{background:#e6f4ea}.bad{background:#fdecea}
table{border-collapse:collapse;margin:16px}td,th{padding:6px 14px;border-bottom:1px solid #ddd;text-align:left}
.reviewed{color:#1e7a34}.draft{color:#a35a00}
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang='vi'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(title)}</title><style>{STYLE}</style></head>"
        f"<body>{body}</body></html>"
    )


# ------------------------------------------------------------------ pages


def render_index(labels: Sequence[LabelFile]) -> str:
    done = sum(label.status == REVIEWED for label in labels)
    rows = "".join(
        f"<tr><td><a href='/cv/{esc(label.id)}'>{esc(label.id)}</a></td>"
        f"<td class='{esc(label.status)}'>{esc(label.status)}</td>"
        f"<td>{esc(label.tags.get('language', ''))}</td>"
        f"<td>{esc(label.tags.get('industry', ''))}</td></tr>"
        for label in labels
    )

    return page(
        "Sửa nhãn CV",
        "<header><b>Sửa nhãn CV</b>"
        f"<span>{done} / {len(labels)} đã duyệt</span></header>"
        "<table><tr><th>CV</th><th>Trạng thái</th><th>Ngôn ngữ</th><th>Ngành</th></tr>"
        f"{rows}</table>",
    )


def _lines(values: Sequence[str]) -> str:
    return "\n".join(values)


def render_editor(
    label: LabelFile,
    token: str,
    neighbours: Tuple[Optional[str], Optional[str]] = (None, None),
    message: str = "",
    problems: Sequence[str] = (),
    blank: bool = False,
    has_pdf: bool = True,
) -> str:
    previous_id, next_id = neighbours

    fields = "".join(
        f"<label for='ent_{name}'>{esc(name)}<small>{esc(FIELD_HELP[name])} - mỗi dòng một mục</small></label>"
        f"<textarea id='ent_{name}' name='ent_{name}' rows='{'6' if name == 'skills' else '3'}'>"
        f"{'' if blank else esc(_lines(label.entities.get(name, [])))}</textarea>"
        for name in FIELDS
    )
    tags = "".join(
        f"<div><label for='tag_{key}'>{esc(text)}</label>"
        f"<input type='text' id='tag_{key}' name='tag_{key}' value='{esc(label.tags.get(key, ''))}'></div>"
        for key, text in TAG_FIELDS
    )
    sections = "".join(
        f"<label><input type='checkbox' name='section' value='{esc(section)}'"
        f"{' checked' if section in label.sections_present and not blank else ''}> {esc(section)}</label>"
        for section in SECTIONS
    )
    banner = ""

    if message:
        banner += f"<div class='msg ok'>{esc(message)}</div>"

    for problem in problems:
        banner += f"<div class='msg bad'>{esc(problem)}</div>"

    pdf = (
        f"<iframe src='/pdf/{esc(label.id)}' title='CV'></iframe>"
        if has_pdf
        else "<p style='padding:16px'>Không tìm thấy file PDF của CV này.</p>"
    )
    nav = "".join(
        f"<a href='/cv/{esc(other)}'>{text}</a>"
        for other, text in ((previous_id, "&larr; trước"), (next_id, "sau &rarr;"))
        if other
    )
    toggle = (
        f"<a href='/cv/{esc(label.id)}'>Hiện gợi ý của hệ thống</a>"
        if blank
        else f"<a href='/cv/{esc(label.id)}?blank=1'>Ẩn gợi ý (tự điền từ đầu)</a>"
    )

    return page(
        f"{label.id} - sửa nhãn",
        "<header><a href='/'>Danh sách</a>"
        f"<b>{esc(label.id)}</b><span class='{esc(label.status)}'>{esc(label.status)}</span>"
        f"{nav}{toggle}</header>"
        "<main class='split'>"
        f"<section class='pdf'>{pdf}</section>"
        f"<form method='post' action='/save/{esc(label.id)}'>"
        f"<input type='hidden' name='token' value='{esc(token)}'>"
        f"{banner}{fields}"
        f"<label>Các mục CV thực sự có</label><div class='sections'>{sections}</div>"
        f"<div class='row'>{tags}</div>"
        "<label for='notes'>Ghi chú</label>"
        f"<textarea id='notes' name='notes' rows='2'>{esc(label.notes)}</textarea>"
        "<button name='action' value='save'>Lưu</button>"
        "<button class='primary' name='action' value='review'>Lưu và đánh dấu đã duyệt</button>"
        "<button class='primary' name='action' value='review_next'>Duyệt và sang CV sau</button>"
        "</form></main>",
    )


# ------------------------------------------------------------------ forms


def _clean_lines(text: str) -> List[str]:
    seen: Dict[str, None] = {}

    for line in text.splitlines():
        value = " ".join(line.split())

        if value:
            seen.setdefault(value, None)

    return list(seen)


def apply_form(label: LabelFile, form: Mapping[str, Sequence[str]]) -> LabelFile:
    """A copy of `label` with the values of a submitted form applied."""

    def first(name: str, default: str = "") -> str:
        values = form.get(name)

        return values[0] if values else default

    return LabelFile(
        id=label.id,
        file=label.file,
        status=label.status,
        tags={
            key: " ".join(first(f"tag_{key}").split())
            for key, _ in TAG_FIELDS
        },
        sections_present=[
            section for section in SECTIONS if section in form.get("section", [])
        ],
        entities={name: _clean_lines(first(f"ent_{name}")) for name in FIELDS},
        notes=first("notes").strip(),
    )


# ----------------------------------------------------------------- server


@dataclass
class EditorConfig:
    labels_dir: Path
    cv_folder: Path
    token: str
    allowed_hosts: Tuple[str, ...] = ()


def resolve_pdf(config: EditorConfig, label: LabelFile) -> Optional[Path]:
    """The label's PDF, only if it lies inside the CV folder."""

    if not label.file:
        return None

    folder = config.cv_folder.resolve()
    path = (folder / label.file).resolve()

    if folder not in path.parents or path.suffix.lower() != ".pdf":
        return None

    return path if path.is_file() else None


class Handler(BaseHTTPRequestHandler):
    config: EditorConfig

    server_version = "LabelEditor"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return  # request lines would name CVs; keep the terminal quiet

    # -- helpers

    def _send(
        self,
        status: int,
        body: bytes,
        content_type: str = "text/html; charset=utf-8",
        extra: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; frame-src 'self'; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'self'",
        )
        self.send_header("X-Frame-Options", "SAMEORIGIN")

        for key, value in (extra or {}).items():
            self.send_header(key, value)

        self.end_headers()
        self.wfile.write(body)

    def _text(self, status: int, text: str) -> None:
        self._send(status, page("Lỗi", f"<p style='padding:16px'>{esc(text)}</p>").encode("utf-8"))

    def _host_ok(self) -> bool:
        return self.headers.get("Host", "") in self.config.allowed_hosts

    def _labels(self) -> List[LabelFile]:
        return load_labels(self.config.labels_dir)

    def _find(self, cv_id: str) -> Optional[Tuple[LabelFile, List[LabelFile]]]:
        if not ID_PATTERN.match(cv_id):
            return None

        labels = self._labels()
        match = next((label for label in labels if label.id == cv_id), None)

        return (match, labels) if match else None

    def _neighbours(self, labels: Sequence[LabelFile], cv_id: str) -> Tuple[Optional[str], Optional[str]]:
        ids = [label.id for label in labels]
        index = ids.index(cv_id)

        return (
            ids[index - 1] if index > 0 else None,
            ids[index + 1] if index + 1 < len(ids) else None,
        )

    def _show(
        self,
        label: LabelFile,
        labels: Sequence[LabelFile],
        message: str = "",
        problems: Sequence[str] = (),
        blank: bool = False,
    ) -> None:
        body = render_editor(
            label,
            self.config.token,
            self._neighbours(labels, label.id),
            message,
            problems,
            blank,
            has_pdf=resolve_pdf(self.config, label) is not None,
        )
        self._send(HTTPStatus.OK, body.encode("utf-8"))

    # -- GET

    def do_GET(self) -> None:  # noqa: N802
        if not self._host_ok():
            return self._text(HTTPStatus.FORBIDDEN, "Host không được phép.")

        url = urlparse(self.path)
        parts = [part for part in url.path.split("/") if part]

        if not parts:
            return self._send(HTTPStatus.OK, render_index(self._labels()).encode("utf-8"))

        if len(parts) == 2 and parts[0] in ("cv", "pdf"):
            found = self._find(parts[1])

            if found is None:
                return self._text(HTTPStatus.NOT_FOUND, "Không có CV này.")

            label, labels = found

            if parts[0] == "cv":
                blank = parse_qs(url.query).get("blank") == ["1"]

                return self._show(label, labels, blank=blank)

            path = resolve_pdf(self.config, label)

            if path is None:
                return self._text(HTTPStatus.NOT_FOUND, "Không tìm thấy PDF.")

            return self._send(HTTPStatus.OK, path.read_bytes(), "application/pdf")

        return self._text(HTTPStatus.NOT_FOUND, "Không có trang này.")

    # -- POST

    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1

        if not 0 <= length <= MAX_FORM_BYTES:
            self.close_connection = True

            return self._text(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Dữ liệu gửi lên không hợp lệ.")

        # Read the (bounded) body first, so that refusing the request does not
        # leave the browser writing into a closed connection.
        raw = self.rfile.read(length).decode("utf-8", "replace")

        if not self._host_ok():
            return self._text(HTTPStatus.FORBIDDEN, "Host không được phép.")

        origin = self.headers.get("Origin")

        if origin and origin.split("://", 1)[-1] not in self.config.allowed_hosts:
            return self._text(HTTPStatus.FORBIDDEN, "Origin không được phép.")

        parts = [part for part in urlparse(self.path).path.split("/") if part]

        if len(parts) != 2 or parts[0] != "save":
            return self._text(HTTPStatus.NOT_FOUND, "Không có trang này.")

        form = parse_qs(raw, keep_blank_values=True)

        if not secrets.compare_digest(
            (form.get("token") or [""])[0].encode(), self.config.token.encode()
        ):
            return self._text(HTTPStatus.FORBIDDEN, "Token không đúng. Tải lại trang.")

        found = self._find(parts[1])

        if found is None:
            return self._text(HTTPStatus.NOT_FOUND, "Không có CV này.")

        original, labels = found
        updated = apply_form(original, form)
        action = (form.get("action") or ["save"])[0]
        reviewing = action in ("review", "review_next")

        updated.status = REVIEWED if reviewing else (
            DRAFT if original.status == "unreadable" else original.status
        )

        problems = validate([updated]) if reviewing else []

        if problems:
            updated.status = original.status

            return self._show(updated, labels, problems=problems)

        save_label(self.config.labels_dir, updated)

        if action == "review_next":
            next_id = self._neighbours(labels, original.id)[1]

            if next_id:
                self._redirect(f"/cv/{next_id}")
                return

        self._show(
            updated,
            labels,
            message="Đã lưu và đánh dấu đã duyệt." if reviewing else "Đã lưu.",
        )

    def _redirect(self, where: str) -> None:
        self._send(HTTPStatus.SEE_OTHER, b"", extra={"Location": where})


def create_server(
    labels_dir: Path,
    cv_folder: Path,
    port: int = 0,
    token: Optional[str] = None,
) -> ThreadingHTTPServer:
    """A server bound to 127.0.0.1; port 0 picks a free port."""

    config = EditorConfig(Path(labels_dir), Path(cv_folder), token or secrets.token_urlsafe(24))
    handler = type("BoundHandler", (Handler,), {"config": config})
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(handler))
    actual = server.server_address[1]
    config.allowed_hosts = (f"127.0.0.1:{actual}", f"localhost:{actual}")
    server.editor_config = config  # type: ignore[attr-defined]

    return server
