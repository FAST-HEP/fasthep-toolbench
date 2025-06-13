from __future__ import annotations

import hashlib
import inspect
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

DEFAULT_DATE_FORMAT = "%Y.%m.%d"


def mkdir_p(path: Path | str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def register_in_collection(
    collection: dict[str, Any], collection_name: str, name: str, obj: Any
) -> None:
    if name in collection:
        msg = f"{collection_name} {name} already registered."
        raise ValueError(msg)
    collection[name] = obj


def unregister_from_collection(
    collection: dict[str, Any], collection_name: str, name: str
) -> None:
    if name not in collection:
        msg = f"{collection_name} {name} not registered."
        raise ValueError(msg)
    collection[name].pop()


##############################
####### Hash functions #######
##############################


def string_to_short_hash(string: str) -> str:
    """Convert a string to a short hash."""
    return hashlib.sha1(string.encode()).hexdigest()[:8]


def get_file_hash(file: Path) -> str:
    """Reads the config file and returns a shortened hash."""
    with file.open("rb") as f:
        # requires Python 3.11+
        return hashlib.file_digest(f, "sha256").hexdigest()[:8]


def formatted_today() -> str:
    """Return the current date in the format YYYY.MM.DD"""
    return datetime.now().strftime(DEFAULT_DATE_FORMAT)


def calculate_function_hash(func: Callable[..., Any], *args, **kwargs) -> str:  # type: ignore[no-untyped-def]
    """Calculate the hash of a function based on its source code and parameters.
    This is useful for caching or identifying unique function calls."""
    # encode parameter values to hash
    arg_hash = hashlib.sha256(str(args).encode() + str(kwargs).encode()).hexdigest()
    # encode function source code to hash
    func_hash = hashlib.sha256(inspect.getsource(func).encode()).hexdigest()
    # combine both hashes
    return hashlib.sha256(arg_hash.encode() + func_hash.encode()).hexdigest()[:8]


def generate_save_path(base_path: Path, workflow_name: str, config_path: Path) -> Path:
    """
    Creates a save path for the workflow and returns the generated path.

    @param base_path: Base path for the save location.
    @param workflow_name: Name of the workflow.
    @param config_path: Path to the configuration file.

    returns: Path to the save location.
    """
    today = formatted_today()
    config_hash = get_file_hash(config_path)
    return Path(f"{base_path}/{workflow_name}/{today}/{config_hash}/").resolve()
