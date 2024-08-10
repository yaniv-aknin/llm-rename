from pathlib import Path
from textwrap import dedent
import os
import contextlib
import pytest

from llm_rename import process_plan, MARKER


@pytest.fixture
def plan_path(tmp_path: Path):
    plan_path = tmp_path / "plan"
    plan_path.write_text("initial plan content")
    return plan_path


@contextlib.contextmanager
def fake_editor(plan_path: Path, post_edit_content: str = ""):
    tmp_path = plan_path.parent
    editor = tmp_path / "editor"
    editor.write_text(
        dedent(f"""\
        #!/bin/bash

        cp "$1" "{tmp_path}"/pre_edit
        [ -f "{tmp_path}"/post_edit ] && cp "{tmp_path}"/post_edit "$1"
    """)
    )
    editor.chmod(0o755)
    old_editor = os.environ.get("EDITOR", "")
    os.environ["EDITOR"] = str(editor)
    try:
        if post_edit_content:
            (tmp_path / "post_edit").write_text(post_edit_content)
        yield
    finally:
        os.environ["EDITOR"] = old_editor


def test_process_plan_basic(plan_path: Path):
    with fake_editor(
        plan_path,
        post_edit_content=f"initial plan content{MARKER}desired system prompt with user changes",
    ):
        process_plan(plan_path, "desired system prompt", lambda x, y: "llm result")
    pre_edit = (plan_path.parent / "pre_edit").read_text()
    assert MARKER in pre_edit
    assert "desired system prompt" in pre_edit
    processed_plan = plan_path.read_text()
    assert processed_plan == "llm result"


def test_process_plan_no_marker(plan_path: Path):
    with fake_editor(plan_path, post_edit_content="initial plan content"):
        with pytest.raises(SystemExit):
            process_plan(plan_path, "desired system prompt", lambda x, y: "llm result")


def test_process_plan_multiple_markers(plan_path: Path):
    with fake_editor(
        plan_path,
        post_edit_content=f"initial plan content{MARKER}desired system prompt\n{MARKER}",
    ):
        with pytest.raises(SystemExit):
            process_plan(plan_path, "desired system prompt", lambda x, y: "llm result")
