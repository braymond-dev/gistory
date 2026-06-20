from pathlib import Path

import yaml


ROOT = Path(__file__).parent.parent


def test_composite_action_metadata() -> None:
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))

    assert action["runs"]["using"] == "composite"
    assert action["inputs"]["provider"]["required"] is True
    assert "append" not in action["inputs"]
    assert action["outputs"]["changed"]["value"] == "${{ steps.result.outputs.changed }}"
    assert action["outputs"]["diagnostic-log"]["value"] == "${{ steps.diagnostics.outputs.log-file }}"

    steps = action["runs"]["steps"]
    upload_step = next(step for step in steps if step.get("name") == "Upload Gistory log")
    assert upload_step["if"] == "${{ always() }}"
    assert upload_step["uses"] == "actions/upload-artifact@v4"
    assert upload_step["with"]["retention-days"] == 14

    success_step = next(step for step in steps if step.get("name") == "Summarize success")
    assert success_step["if"] == "${{ success() }}"

    action_text = (ROOT / "action.yml").read_text(encoding="utf-8")
    assert "tee -a \"$GISTORY_LOG_FILE\"" in action_text
    assert "GITHUB_STEP_SUMMARY" in action_text
    assert "gistory-log-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}" in action_text


def test_consumer_workflow_uses_full_git_history() -> None:
    workflow = (ROOT / "examples/github-actions/gistory.yml").read_text(encoding="utf-8")

    assert "fetch-depth: 0" in workflow
    assert "uses: braymond-dev/gistory@v1" in workflow
    assert "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}" in workflow
    assert "if: steps.gistory.outputs.changed == 'true'" in workflow


def test_gistory_output_is_not_ignored() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "GISTORY.md" not in ignored
