import json
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar, Iterable, Iterator

import cv2

import app_logging
from camera_io import open_video, ClosedCameraError
from env import env

logger = app_logging.create_logger()


@dataclass
class _CaptureSessionMeta:
    success: bool
    reason: str | None
    timestamps: list[datetime]

    def to_json(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "reason": self.reason,
            "timestamps": [timestamp.isoformat() for timestamp in self.timestamps],
            "count": len(self.timestamps),
        }

    @classmethod
    def create_failure(cls, reason: str) -> "_CaptureSessionMeta":
        return cls(
            success=False,
            reason=reason,
            timestamps=[],
        )

    @classmethod
    def create_success(cls, timestamps: list[datetime]) -> "_CaptureSessionMeta":
        return cls(
            success=True,
            reason=None,
            timestamps=timestamps,
        )


@dataclass
class CaptureSessionResult:
    meta_path: Path
    frame_path_list: list[Path]


T = TypeVar("T")


def iter_with_interval(
        it: Iterable[T],
        interval_seconds: float,
        minimum_interval_seconds: float,
) -> Iterator[T]:
    for item in it:
        t_start = time.time()
        yield item
        t_end = time.time()
        t_delta = t_end - t_start
        t_sleep = max(interval_seconds - t_delta, minimum_interval_seconds)
        time.sleep(t_sleep)


def retrieve_captures_and_save_session(
        video_id: int,
        capture_interval_seconds: float,
        n_captures: int,
) -> CaptureSessionResult:
    save_dir_path = Path(env.capture_tmp_folder_path)

    if save_dir_path.exists():
        shutil.rmtree(save_dir_path)
    save_dir_path.mkdir(parents=True, exist_ok=True)

    frame_path_list = []

    try:
        with open_video(video_id) as cap:
            assert isinstance(cap, cv2.VideoCapture), cap
            timestamps = []
            for i in iter_with_interval(
                    range(n_captures),
                    interval_seconds=capture_interval_seconds,
                    minimum_interval_seconds=0.01,
            ):
                logger.debug(f"Retrieving capture {i}/{n_captures}")

                # retrieve capture
                ret, frame = cap.read()
                if not ret:
                    raise ClosedCameraError()

                # create frame path and save frame to it
                frame_path = save_dir_path / f"{i:03d}.jpeg"
                cv2.imwrite(str(frame_path), frame)
                frame_path_list.append(frame_path)

                # record timestamp
                timestamps.append(datetime.now())
    except ClosedCameraError as e:
        logger.debug(f"Error occurred: {str(e)}")
        meta = _CaptureSessionMeta.create_failure("Failed to open camera")
    except Exception as e:
        meta = _CaptureSessionMeta.create_failure(f"Error occurred: {str(e)}")
        logger.exception("Unexpected error occurred while retrieving capture")
    else:
        meta = _CaptureSessionMeta.create_success(timestamps=timestamps)

    # save metadata as a json
    logger.info("Saving metadata")
    meta_path = save_dir_path / "meta.json"
    with meta_path.open(mode="w", encoding="utf-8") as f:
        json.dump(
            meta.to_json(),
            f,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
        )

    # create result and return it
    return CaptureSessionResult(meta_path=meta_path, frame_path_list=frame_path_list)
