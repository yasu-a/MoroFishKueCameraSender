import time

import dropbox

import app_logging
from capture import retrieve_captures_and_save_session
from dropbox_io import upload_capture_session, remove_old_capture_sessions
from env import env

logger = app_logging.create_logger()


def get_dbx_session() -> dropbox.Dropbox:
    dbx = dropbox.Dropbox(env.dropbox_access_token)
    return dbx


def print_credential_info():
    dbx = get_dbx_session()
    current_user = dbx.users_get_current_account()
    # noinspection PyProtectedMember
    logger.info(
        f"Active dropbox account: \n"
        + "\n".join(
            f" - {name}={getattr(current_user, name)}"
            for name in current_user._all_field_names_
        )
    )


def main():
    while True:
        logger.info("Session begin")

        dbx = get_dbx_session()

        logger.info("Retrieving and save captures")
        capture_result = retrieve_captures_and_save_session(
            video_id=env.camera_id,
            capture_interval_seconds=env.session_capture_interval_seconds,
            n_captures=env.session_n_captures,
        )

        logger.info("Uploading captures to dropbox")
        upload_capture_session(
            dbx=dbx,
            capture_result=capture_result,
        )

        logger.info("Removing old capture sessions from dropbox")
        remove_old_capture_sessions(
            dbx=dbx,
            max_upload_sessions=env.max_upload_sessions,
        )

        logger.info("Session end")

        # Wait for the next session
        logger.info(f"Waiting {env.interval_session_seconds} seconds before next session")
        time.sleep(env.interval_session_seconds)


if __name__ == '__main__':
    main()
