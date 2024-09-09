from contextlib import contextmanager

import cv2


class ClosedCameraError(RuntimeError):
    pass


@contextmanager
def open_video(video_id):
    cap = cv2.VideoCapture(video_id)
    if not cap.isOpened():
        raise ClosedCameraError()
    try:
        yield cap
    finally:
        cap.release()
