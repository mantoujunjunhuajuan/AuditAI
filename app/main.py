"""AuditAI Streamlit application entrypoint.

M1: provides multi-file upload to GCS bucket via `services.storage_service`.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import List

# Ensure root directory is importable before local packages
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from services.storage_service import get_storage_service

# ---------------------------------------------------------------------------
# Streamlit page config
# ---------------------------------------------------------------------------

import streamlit as st

# ---------------------------------------------------------------------------
# Streamlit page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="AuditAI – Document Upload", page_icon="📄", layout="centered")

storage_service = get_storage_service()

BUCKET_NAME = os.getenv("GCS_BUCKET", "<missing>")

st.title("📄 AuditAI – Upload Insurance Claim Documents")

st.markdown(
    """
    Upload PDF, PNG or JPG files for automated claim pre-assessment.
    Files are stored **securely** in the private GCS bucket and processed by the AI pipeline.
    """
)

uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile] = st.file_uploader(  # type: ignore[attr-defined]
    "Select one or more files", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg"], key="file_uploader"
)

case_id: str = st.text_input("Case identifier (optional)")

if st.button("Upload", disabled=not uploaded_files):
    if not BUCKET_NAME or BUCKET_NAME == "<missing>":
        st.error("GCS_BUCKET environment variable not set.")
    else:
        with st.spinner("Uploading files …"):
            results: list[str] = []
            for file in uploaded_files:
                # Save to a temporary file first
                temp_path = Path(st.experimental_get_query_params().get("temp_dir", ["."])[0])
                temp_path.mkdir(parents=True, exist_ok=True)
                file_path = temp_path / file.name
                file_path.write_bytes(file.getbuffer())

                dest_name = f"{case_id or 'uncategorised'}/{file.name}"
                uri = storage_service.upload_file(file_path=file_path, destination=dest_name)
                results.append(uri)

                # Clean up local temp file
                file_path.unlink(missing_ok=True)

        st.success("Upload completed!")
        st.write("Stored URIs:")
        for uri in results:
            st.code(uri)

        st.balloons() 