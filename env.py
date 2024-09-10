import json
import os
from dataclasses import dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class Environment:
    dropbox_access_token: str
    capture_tmp_folder_path: str
    camera_id: int
    session_capture_interval_seconds: float
    session_n_captures: int
    interval_session_seconds: float
    max_upload_sessions: int

    @classmethod
    def from_environment(cls):
        values = {}
        for f in fields(cls):
            var_name = f.name.upper()
            var_value = os.environ.get(var_name)
            if var_value is None:
                raise ValueError(f"Missing environment variable: {var_name}")
            var_type = f.type
            try:
                var_value_casted = var_type(var_value)
            except ValueError:
                raise ValueError(
                    f"Invalid value for environment variable: {var_name} = {var_value!r}, "
                    f"expected value of {var_type.__name__}"
                )
            values[f.name] = var_value_casted
        return cls(**values)

    @classmethod
    def from_json(cls, json_path):
        with Path(json_path).open(mode="r") as f:
            body = json.load(f)
        values = {}
        for f in fields(cls):
            var_name = f.name.upper()
            var_value = body.get(var_name)
            if var_value is None:
                raise ValueError(f"Missing JSON field: {var_name}")
            var_type = f.type
            try:
                var_value_casted = var_type(var_value)
            except ValueError:
                raise ValueError(
                    f"Invalid value for environment variable: {var_name} = {var_value!r}, "
                    f"expected value of {var_type.__name__}"
                )
            values[f.name] = var_value_casted
        return cls(**values)


env = Environment.from_json("./settings.json")
