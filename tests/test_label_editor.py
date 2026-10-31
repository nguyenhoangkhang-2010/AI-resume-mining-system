import http.client
import threading
from urllib.parse import urlencode

import pytest

from app.evaluation.field_eval import FIELDS
from app.evaluation.label_editor import apply_form, create_server, render_editor
from app.evaluation.real_cvs import DRAFT, REVIEWED, LabelFile, load_labels, save_label

PDF = b"%PDF-1.4\n% minimal\n"
EVIL = "<script>alert(1)</script>"


def make_label(cv_id, **entities):
    base = {name: [] for name in FIELDS}
    base.update(entities)

    return LabelFile(
        id=cv_id,
        file=f"{cv_id}.pdf",
        status=DRAFT,
        tags={"language": "en", "industry": "finance", "layout": "single", "pages": "1"},
        sections_present=["experience"],
        entities=base,
    )


@pytest.fixture
def editor(tmp_path):
    labels = tmp_path / "labels"
    cvs = tmp_path / "cvs"
    cvs.mkdir()

    for number in (1, 2, 3):
        cv_id = f"cv-00{number}"
        save_label(labels, make_label(cv_id, companies=[f"Acme {number}"], roles=[EVIL] if number == 1 else []))
        (cvs / f"{cv_id}.pdf").write_bytes(PDF)

    (tmp_path / "secret.pdf").write_bytes(b"%PDF secret")

    server = create_server(labels, cvs)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    class Editor:
        port = server.server_address[1]
        token = server.editor_config.token
        labels_dir = labels
        cv_dir = cvs
        root = tmp_path

        @staticmethod
        def request(method, path, body=None, headers=None, host=None):
            connection = http.client.HTTPConnection("127.0.0.1", Editor.port, timeout=10)
            sent = {"Host": host or f"127.0.0.1:{Editor.port}", **(headers or {})}

            if body is not None and "Content-Type" not in sent:
                sent["Content-Type"] = "application/x-www-form-urlencoded"

            connection.putrequest(method, path, skip_host=True)

            for key, value in sent.items():
                connection.putheader(key, value)

            data = body.encode("utf-8") if isinstance(body, str) else body
            connection.putheader("Content-Length", str(len(data or b"")))
            connection.endheaders(data)
            response = connection.getresponse()
            payload = response.read()
            connection.close()

            return response.status, dict(response.getheaders()), payload

        @staticmethod
        def save(cv_id, fields, token=None, **kwargs):
            form = {"token": Editor.token if token is None else token, **fields}

            return Editor.request("POST", f"/save/{cv_id}", urlencode(form, doseq=True), **kwargs)

    yield Editor

    server.shutdown()
    server.server_close()


def stored(editor, cv_id):
    return next(label for label in load_labels(editor.labels_dir) if label.id == cv_id)


# ------------------------------------------------------------------ pages


def test_the_index_lists_every_cv_and_progress(editor):
    status, _, body = editor.request("GET", "/")

    assert status == 200
    text = body.decode()
    assert all(f"cv-00{n}" in text for n in (1, 2, 3))
    assert "0 / 3" in text


def test_the_editor_shows_the_pdf_and_the_current_label(editor):
    status, _, body = editor.request("GET", "/cv/cv-002")
    text = body.decode()

    assert status == 200
    assert "<iframe src='/pdf/cv-002'" in text
    assert "Acme 2" in text
    assert "name='ent_companies'" in text and "name='token'" in text


def test_values_from_the_labels_cannot_inject_markup(editor):
    _, _, body = editor.request("GET", "/cv/cv-001")
    text = body.decode()

    assert "<script>alert(1)</script>" not in text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in text


def test_the_system_s_suggestions_can_be_hidden(editor):
    _, _, body = editor.request("GET", "/cv/cv-002?blank=1")

    assert "Acme 2" not in body.decode()


def test_the_first_and_last_cv_have_one_neighbour_each(editor):
    first = editor.request("GET", "/cv/cv-001")[2].decode()
    last = editor.request("GET", "/cv/cv-003")[2].decode()

    assert "/cv/cv-002" in first and "&larr; trước" not in first
    assert "/cv/cv-002" in last and "sau &rarr;" not in last


def test_the_pdf_is_served_with_safe_headers(editor):
    status, headers, body = editor.request("GET", "/pdf/cv-001")

    assert (status, body) == (200, PDF)
    assert headers["Content-Type"] == "application/pdf"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'none'" in headers["Content-Security-Policy"]


@pytest.mark.parametrize("path", ["/cv/nope", "/cv/..%2Fx", "/pdf/cv-999", "/other", "/cv/a/b"])
def test_unknown_pages_are_404(editor, path):
    assert editor.request("GET", path)[0] == 404


def test_a_label_that_points_outside_the_cv_folder_gets_no_file(editor):
    traversal = make_label("cv-004")
    traversal.file = "../secret.pdf"
    save_label(editor.labels_dir, traversal)

    status, _, body = editor.request("GET", "/pdf/cv-004")

    assert status == 404 and b"secret" not in body
    assert b"Kh" in editor.request("GET", "/cv/cv-004")[2]  # page says the PDF is missing


# --------------------------------------------------------- who may connect


def test_a_request_with_a_foreign_host_name_is_refused(editor):
    assert editor.request("GET", "/", host="evil.example")[0] == 403
    assert editor.request("GET", "/pdf/cv-001", host="evil.example:80")[0] == 403


def test_saving_needs_the_token(editor):
    assert editor.save("cv-001", {"ent_companies": "Hacked"}, token="wrong")[0] == 403
    assert editor.save("cv-001", {"ent_companies": "Hacked"}, token="")[0] == 403
    assert stored(editor, "cv-001").entities["companies"] == ["Acme 1"]


def test_saving_from_another_origin_is_refused(editor):
    status, *_ = editor.save(
        "cv-001", {"ent_companies": "Hacked"}, headers={"Origin": "http://evil.example"}
    )

    assert status == 403
    assert stored(editor, "cv-001").entities["companies"] == ["Acme 1"]


def test_an_oversized_form_is_refused(editor):
    # Only the declared size is sent: the server must refuse before reading.
    connection = http.client.HTTPConnection("127.0.0.1", editor.port, timeout=10)
    connection.putrequest("POST", "/save/cv-001", skip_host=True)
    connection.putheader("Host", f"127.0.0.1:{editor.port}")
    connection.putheader("Content-Length", "2000000")
    connection.endheaders()
    status = connection.getresponse().status
    connection.close()

    assert status == 413


# ----------------------------------------------------------------- saving


def test_save_updates_the_label_file(editor):
    status, _, body = editor.save(
        "cv-002",
        {
            "ent_companies": "Acme Corp\n\n  Globex  \nAcme Corp",
            "ent_roles": "Backend Engineer",
            "ent_skills": "python\nsql",
            "section": ["experience", "education"],
            "tag_language": "vi",
            "tag_industry": " marketing ",
            "notes": "checked",
            "action": "save",
        },
    )

    saved = stored(editor, "cv-002")

    assert status == 200 and "Đã lưu" in body.decode()
    assert saved.entities["companies"] == ["Acme Corp", "Globex"]
    assert saved.entities["roles"] == ["Backend Engineer"]
    assert saved.entities["skills"] == ["python", "sql"]
    assert saved.entities["schools"] == []
    assert saved.sections_present == ["experience", "education"]
    assert saved.tags["language"] == "vi" and saved.tags["industry"] == "marketing"
    assert saved.notes == "checked"
    assert saved.status == DRAFT
    assert saved.file == "cv-002.pdf"


def test_review_marks_the_label_reviewed(editor):
    editor.save("cv-002", {"ent_companies": "Acme Corp", "action": "review"})

    assert stored(editor, "cv-002").status == REVIEWED


def test_review_is_refused_when_nothing_was_entered(editor):
    status, _, body = editor.save("cv-002", {"ent_companies": "", "action": "review"})

    assert status == 200 and "reviewed but has no entities" in body.decode()
    assert stored(editor, "cv-002").status == DRAFT
    assert stored(editor, "cv-002").entities["companies"] == ["Acme 2"]


def test_review_and_next_goes_to_the_next_cv(editor):
    status, headers, _ = editor.save(
        "cv-001", {"ent_companies": "Acme Corp", "action": "review_next"}
    )

    assert (status, headers["Location"]) == (303, "/cv/cv-002")
    assert stored(editor, "cv-001").status == REVIEWED


def test_saving_an_unknown_cv_is_404(editor):
    assert editor.save("cv-404", {"ent_companies": "x"})[0] == 404
    assert editor.save("..", {"ent_companies": "x"})[0] == 404


# ------------------------------------------------------------ pure pieces


def test_apply_form_does_not_change_the_original():
    original = make_label("cv-009", companies=["Keep"])

    updated = apply_form(original, {"ent_companies": ["New"]})

    assert original.entities["companies"] == ["Keep"]
    assert updated.entities["companies"] == ["New"]


def test_render_editor_marks_problems_and_messages():
    text = render_editor(make_label("cv-009"), "tok", problems=["cv-009: broken"], message="done")

    assert "cv-009: broken" in text and "done" in text
