from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from scripts.freeze_baseline_training_handoff import readme_text, write_deterministic_zip


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_deterministic_zip_has_stable_members_and_hash(tmp_path: Path) -> None:
    first_source = tmp_path / "first.txt"
    second_source = tmp_path / "second.txt"
    first_source.write_text("first", encoding="utf-8")
    second_source.write_text("second", encoding="utf-8")
    members = [(second_source, "b/second.txt"), (first_source, "a/first.txt")]
    first_zip = tmp_path / "first.zip"
    second_zip = tmp_path / "second.zip"
    generated = {"README.md": b"fixture\n"}
    write_deterministic_zip(first_zip, members, generated)
    write_deterministic_zip(second_zip, list(reversed(members)), generated)
    assert sha(first_zip) == sha(second_zip)
    with zipfile.ZipFile(first_zip) as archive:
        assert archive.namelist() == ["a/first.txt", "b/second.txt", "README.md"]
        assert archive.read("a/first.txt") == b"first"


def test_handoff_readme_uses_git_code_and_one_dataset_zip() -> None:
    text = readme_text()
    assert "Code is delivered through the DeskMate Git repository" in text
    assert "dataset ZIP" in text
    assert "code ZIP" not in text
