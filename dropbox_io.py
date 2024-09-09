import os.path
import re
import time
import zipfile
from datetime import datetime

import dropbox
from dropbox.files import ListFolderResult, FileMetadata

import app_logging
from capture import CaptureSessionResult

logger = app_logging.create_logger()


def _create_new_session_zip_path() -> str:  # returns path to new session folder
    return "/" + str(int(time.time())) + ".zip"


def _get_path_to_frame(folder_path, filename) -> str:  # returns path to frame
    return f"{folder_path}/{filename}"


def _get_path_to_meta(folder_path) -> str:  # returns path to meta file
    return f"{folder_path}/meta.json"


def _extract_session_folders_and_timestamps(list_folder_results: list[ListFolderResult]) \
        -> list[tuple[FileMetadata, datetime]]:  # returns list of zip file and timestamps
    lst = []
    for result in list_folder_results:
        for entry in result.entries:
            stem, ext = os.path.splitext(entry.name)
            if ext != ".zip":
                continue
            if not re.fullmatch(r"\d+", stem):
                continue
            lst.append((entry, datetime.fromtimestamp(int(stem))))
    return lst


def upload_capture_session(dbx: dropbox.Dropbox, capture_result: CaptureSessionResult):
    zip_path = capture_result.meta_path.parent / "tmp.zip"

    # create zip file
    logger.info(f"Creating zip file: {zip_path!s}")
    logger.info("Creating zip file with frames and metadata")
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_STORED) as zf:
        # frames
        for frame_path in capture_result.frame_path_list:
            logger.debug(f"Adding frame: {frame_path}")
            with frame_path.open(mode="rb") as f:
                with zf.open(frame_path.name, mode="w") as f_out:
                    f_out.write(f.read())
        # metadata
        with capture_result.meta_path.open(mode="rb") as f:
            logger.debug("Adding metadata")
            with zf.open("meta.json", mode="w") as f_out:
                f_out.write(f.read())

    # upload zip file
    logger.info(f"Uploading zip file to Dropbox: {zip_path}")
    with open(zip_path, mode="rb") as f:
        dbx.files_upload(f.read(), _create_new_session_zip_path())

    logger.info(f"Finished to upload capture session to Dropbox: {zip_path}")


def remove_old_capture_sessions(dbx: dropbox.Dropbox, max_upload_sessions: int):
    # retrieve all contents of the folder
    results = []
    result: ListFolderResult = dbx.files_list_folder("")
    results.append(result)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        results.append(result)

    # extract timestamps
    session_folders_and_timestamps = _extract_session_folders_and_timestamps(results)

    # remember the number of uploaded sessions
    n_before = len(session_folders_and_timestamps)

    # sort by timestamp
    sorted_session_folders_and_timestamps = sorted(
        session_folders_and_timestamps,
        key=lambda x: x[1],
        reverse=True,
    )

    # remove old sessions
    n_deleted = 0
    for file_meta, _ in sorted_session_folders_and_timestamps[max_upload_sessions:]:
        dbx.files_delete_v2(file_meta.path_lower)
        n_deleted += 1

    logger.info(f"Detected {n_before} uploaded sessions, deleted {n_deleted} sessions")
