from scripts.export_openapi import TARGET, render


def test_the_exported_openapi_file_matches_the_api():
    assert TARGET.read_text(encoding="utf-8") == render(), (
        "frontend/openapi.json is out of date: run `python -m scripts.export_openapi` "
        "and then `npm run gen:api` in frontend/."
    )


def test_the_routes_the_frontend_calls_exist():
    import json

    paths = json.loads(TARGET.read_text(encoding="utf-8"))["paths"]

    expected = {
        "/api/v1/resumes/upload": "post",
        "/api/v1/resumes/": "get",
        "/api/v1/resumes/{resume_id}/status": "get",
        "/api/v1/resumes/{resume_id}/jobs": "get",
        "/api/v1/jobs/": "post",
        "/api/v1/matches/{job_id}": "get",
        "/api/v1/candidates/": "get",
        "/api/v1/candidates/{candidate_id}/jobs": "get",
        "/api/v1/search/candidates": "post",
        "/ready": "get",
    }

    for path, method in expected.items():
        assert method in paths[path], f"{method.upper()} {path} is missing"
