from importlib.metadata import version

from typer.testing import CliRunner

from snare.cli import app


def test_version_matches_installed_metadata() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == version("snare")
