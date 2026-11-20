"""Load and validate the local Snare configuration."""

import shutil
import tomllib
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from snare.models import NetworkMode

NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConfigSection(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LibvirtConfig(ConfigSection):
    uri: NonBlank


class VmConfig(ConfigSection):
    name: NonBlank
    clean_snapshot: NonBlank


class PathsConfig(ConfigSection):
    runs: NonBlank
    samples: NonBlank


class NetworkConfig(ConfigSection):
    default_mode: NetworkMode
    bridge: NonBlank


class ToolsConfig(ConfigSection):
    volatility: NonBlank
    memprocfs: NonBlank
    zeek: NonBlank
    suricata: NonBlank


class SnareSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")

    libvirt: LibvirtConfig
    vm: VmConfig
    paths: PathsConfig
    network: NetworkConfig
    tools: ToolsConfig

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Check the selected file even when similarly named environment variables exist.
        return (init_settings,)


def load_config(path: Path) -> SnareSettings:
    """Load an explicit TOML file as the sole settings source."""
    with path.open("rb") as file:
        data = tomllib.load(file)
    for key in data:
        if key.startswith("_"):
            raise ValueError(f"Unknown top-level setting: {key}")
    return SnareSettings(**data)


def missing_tools(settings: ToolsConfig, config_dir: Path) -> dict[str, str]:
    """Check executable availability without launching any of the tools."""
    missing = {}
    for name, executable in settings:
        command = str(executable)
        if "/" in command or "\\" in command or Path(command).drive:
            command = str(config_dir / command)
        if shutil.which(command) is None:
            missing[name] = str(executable)
    return missing


app = typer.Typer(help="Validate local configuration.")


@app.command()
def check(
    config: Annotated[
        Path, typer.Option("--config", "-c", help="Path to the Snare TOML file.")
    ] = Path("snare.toml"),
) -> None:
    """Validate the TOML file and check external tools."""
    try:
        settings = load_config(config)
    except (OSError, ValueError) as error:
        typer.echo(f"Configuration error in {config}:", err=True)
        if isinstance(error, ValidationError):
            for issue in error.errors(include_input=False, include_url=False):
                field = ".".join(map(str, issue["loc"]))
                typer.echo(f"  {field}: {issue['msg']}", err=True)
        else:
            typer.echo(f"  {error}", err=True)
        raise typer.Exit(1) from error

    typer.echo(f"Configuration valid: {config}")
    missing = missing_tools(settings.tools, config.resolve().parent)
    if missing:
        for name, executable in missing.items():
            typer.echo(f"Tool unavailable: tools.{name} ({executable})", err=True)
        raise typer.Exit(1)
    typer.echo("All configured external tools are available.")
