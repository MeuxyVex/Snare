from pathlib import Path
from shutil import which
from sys import executable

import pytest
from typer.testing import CliRunner

from snare.cli import app
from snare.config import load_config

EXAMPLE = Path(__file__).resolve().parents[1] / "snare.example.toml"


def test_example_is_valid() -> None:
    settings = load_config(EXAMPLE)
    assert settings.network.default_mode == "cut"
    assert settings.paths.runs == "runs"


def test_config_check_with_tools_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "snare.toml"
    sample = EXAMPLE.read_text(encoding="utf-8").split("[tools]", 1)[0]
    command = Path(executable).name
    monkeypatch.setenv("PATH", str(Path(executable).parent))
    assert which(command) is not None
    config.write_text(
        sample
        + f"""[tools]
volatility = "{command}"
memprocfs = "{command}"
zeek = "{command}"
suricata = "{command}"
""",
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["config", "check", "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert "All configured external tools are available." in result.output


def test_config_check_lists_missing_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    # Avoid picking up an executable from the caller's current directory on Windows.
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "snare.toml"
    config.write_bytes(EXAMPLE.read_bytes())

    result = CliRunner().invoke(app, ["config", "check"])

    assert result.exit_code == 1
    assert "Configuration valid" in result.stdout
    for name in ("volatility", "memprocfs", "zeek", "suricata"):
        assert f"tools.{name}" in result.stderr


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("[broken", "Configuration error"),
        ("_cli_parse_args = true", "Unknown top-level setting: _cli_parse_args"),
        (
            EXAMPLE.read_text(encoding="utf-8").replace('"cut"', '"invalid"'),
            "network.default_mode",
        ),
    ],
)
def test_config_check_rejects_invalid_files(
    content: str, expected: str, tmp_path: Path
) -> None:
    config = tmp_path / "invalid.toml"
    config.write_text(content, encoding="utf-8")

    result = CliRunner().invoke(app, ["config", "check", "-c", str(config)])

    assert result.exit_code == 1
    assert expected in result.stderr


def test_config_check_reports_missing_file(tmp_path: Path) -> None:
    config = tmp_path / "missing.toml"

    result = CliRunner().invoke(app, ["config", "check", "-c", str(config)])

    assert result.exit_code == 1
    assert "missing.toml" in result.stderr
