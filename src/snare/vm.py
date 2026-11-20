"""Render a standard offline guest definition for the lab."""

import re
from pathlib import PurePosixPath
from typing import Annotated
from xml.etree.ElementTree import Element, SubElement, indent, tostring

import typer

app = typer.Typer(help="Prepare an offline virtual machine definition.")


def host_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not path.is_absolute()
        or not path.name
        or path.anchor != "/"
        or "\\" in value
        or not value.isprintable()
    ):
        raise typer.BadParameter(
            "Use an absolute Linux path to a file on the lab host."
        )
    return value


def guest_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
        raise typer.BadParameter("Use letters, digits, dots, underscores, or hyphens.")
    return value


def _file_disk(
    devices: Element, *, source: str, target: str, boot_order: int, cdrom: bool = False
) -> None:
    disk = SubElement(devices, "disk", type="file", device="cdrom" if cdrom else "disk")
    SubElement(disk, "driver", name="qemu", type="raw" if cdrom else "qcow2")
    SubElement(disk, "source", file=source)
    SubElement(disk, "target", dev=target, bus="sata")
    if cdrom:
        SubElement(disk, "readonly")
    SubElement(disk, "boot", order=str(boot_order))


@app.command()
def render_xml(
    disk: Annotated[
        str, typer.Option(callback=host_path, help="Host path to a qcow2 disk.")
    ],
    iso: Annotated[
        str | None,
        typer.Option(help="Optional host path to the Windows installer ISO."),
    ] = None,
    name: Annotated[str, typer.Option(callback=guest_name)] = "snare-windows",
    memory_mib: Annotated[int, typer.Option(min=1024)] = 8192,
    vcpus: Annotated[int, typer.Option(min=1)] = 4,
) -> None:
    """Print a libvirt domain XML definition without contacting the host."""
    if iso is not None:
        try:
            iso = host_path(iso)
        except typer.BadParameter as error:
            error.param_hint = "--iso"
            raise
        if PurePosixPath(disk) == PurePosixPath(iso):
            raise typer.BadParameter(
                "The system disk and ISO must differ.", param_hint="--iso"
            )

    domain = Element("domain", type="kvm")
    SubElement(domain, "name").text = name
    SubElement(domain, "memory", unit="MiB").text = str(memory_mib)
    SubElement(domain, "vcpu").text = str(vcpus)
    os = SubElement(domain, "os")
    SubElement(os, "type", arch="x86_64", machine="q35").text = "hvm"
    features = SubElement(domain, "features")
    SubElement(features, "acpi")
    SubElement(features, "apic")
    SubElement(domain, "clock", offset="localtime")

    devices = SubElement(domain, "devices")
    _file_disk(devices, source=disk, target="sda", boot_order=2 if iso else 1)
    if iso is not None:
        _file_disk(devices, source=iso, target="sdb", boot_order=1, cdrom=True)
    graphics = SubElement(devices, "graphics", type="spice")
    SubElement(graphics, "listen", type="none")
    SubElement(graphics, "clipboard", copypaste="no")
    SubElement(graphics, "filetransfer", enable="no")
    SubElement(SubElement(devices, "video"), "model", type="vga")

    indent(domain)
    typer.echo(tostring(domain, encoding="unicode"))
