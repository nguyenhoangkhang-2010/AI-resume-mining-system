from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from app.core.exceptions import ConflictError, NotFoundError
from app.core.identifiers import parse_object_id
from app.database.mongodb.connection import mongo_db
from app.schemas.page import Page
from app.schemas.resume_schema import ResumeDetail, ResumeListItem

KNOWN_STATUSES = {"pending", "processing", "processed", "needs_review", "failed"}

# Fields left out of listings: large, and not part of the API.
LIST_PROJECTION = {"extracted_data": 0, "raw_text": 0, "file_path": 0}


class ResumeCatalogService:
    """Listing, reading and deleting uploaded resumes."""

    def __init__(self, vector_store, upload_dir: Path = Path("data/uploads")):
        self.vector_store = vector_store
        self.upload_dir = upload_dir

    @property
    def resumes_col(self):
        return mongo_db.get_db()["resumes"]

    @property
    def candidates_col(self):
        return mongo_db.get_db()["candidates"]

    def list_resumes(
        self,
        status: Optional[str],
        limit: int,
        offset: int,
    ) -> Page[ResumeListItem]:

        query: Dict[str, Any] = {"upload_status": status} if status else {}

        documents = (
            self.resumes_col.find(query, LIST_PROJECTION)
            .sort([("created_at", -1), ("_id", -1)])
            .skip(offset)
            .limit(limit)
        )

        return Page[ResumeListItem](
            items=[self._list_item(document) for document in documents],
            total=self.resumes_col.count_documents(query),
            limit=limit,
            offset=offset,
        )

    def get_resume(self, resume_id: str) -> ResumeDetail:
        object_id = parse_object_id(resume_id, "Resume")

        document = self.resumes_col.find_one({"_id": object_id}, LIST_PROJECTION)

        if not document:
            raise NotFoundError(f"Resume not found: {resume_id}")

        candidate = self.candidates_col.find_one(
            {"resume_id": str(object_id)},
            {"_id": 1},
        )

        return ResumeDetail(
            **self._list_item(document).model_dump(),
            candidate_id=str(candidate["_id"]) if candidate else None,
        )

    def delete_resume(self, resume_id: str) -> None:
        """
        Removes the resume, the candidate built from it, the candidate's
        vector and the uploaded file.
        """

        object_id = parse_object_id(resume_id, "Resume")

        document = self.resumes_col.find_one(
            {"_id": object_id},
            {"upload_status": 1, "file_path": 1},
        )

        if not document:
            raise NotFoundError(f"Resume not found: {resume_id}")

        if document.get("upload_status") == "processing":
            raise ConflictError(
                "The resume is being processed; try again when it has finished."
            )

        candidates = list(
            self.candidates_col.find({"resume_id": str(object_id)}, {"faiss_id": 1})
        )

        self.candidates_col.delete_many({"resume_id": str(object_id)})

        for candidate in candidates:
            if candidate.get("faiss_id") is not None:
                self.vector_store.remove_candidate_embedding(candidate["faiss_id"])

        self.resumes_col.delete_one({"_id": object_id})

        self._remove_file(document.get("file_path"))

    def _remove_file(self, file_path: Optional[str]) -> None:
        if not file_path:
            return

        try:
            path = Path(file_path).resolve()

            # Never delete outside the upload directory, whatever the
            # stored path says.
            if self.upload_dir.resolve() not in path.parents:
                logger.warning("Not deleting a file outside the upload directory.")
                return

            path.unlink(missing_ok=True)

        except OSError as exc:
            logger.warning("Could not delete an uploaded file: {}", type(exc).__name__)

    @staticmethod
    def _list_item(document: Dict[str, Any]) -> ResumeListItem:
        status = document.get("upload_status", "pending")

        return ResumeListItem(
            id=str(document["_id"]),
            filename=document.get("filename", ""),
            status=status if status in KNOWN_STATUSES else "pending",
            reason=document.get("status_reason"),
            warnings=document.get("warnings") or [],
            created_at=document["created_at"],
        )
