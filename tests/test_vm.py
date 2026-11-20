from xml.etree.ElementTree import fromstring

import pytest
from typer.testing import CliRunner

from snare.cli import app

RUNNER = CliRunner()
DISK = "/var/lib/libvirt/images/snare & test.qcow2"
COMMAND = ["vm", "render-xml", "--disk", DISK]


def test_render_guest_is_offline_and_local() -> None:
    result = RUNNER.invoke(app, COMMAND + ["--memory-mib", "6144", "--vcpus", "2"])
    assert result.exit_code == 0, result.output
    root = fromstring(result.stdout)

    assert root.tag == "domain"
    assert root.get("type") == "kvm"
    assert root.findtext("name") == "snare-windows"
    assert root.findtext("memory") == "6144"
    assert root.findtext("vcpu") == "2"
    assert root.find(f"./devices/disk/source[@file='{DISK}']") is not None
    assert root.find("./devices/disk/driver[@type='qcow2']") is not None
    assert root.find("./devices/disk/boot[@order='1']") is not None
    assert root.find("./devices/graphics/listen[@type='none']") is not None
    assert root.find("./devices/graphics/clipboard[@copypaste='no']") is not None
    assert root.find("./devices/graphics/filetransfer[@enable='no']") is not None
    for device in ("interface", "filesystem", "hostdev", "channel"):
        assert root.find(f"./devices/{device}") is None


def test_installer_iso_is_read_only_and_boots_first() -> None:
    iso = "/var/lib/libvirt/images/windows.iso"
    result = RUNNER.invoke(app, COMMAND + ["--iso", iso])
    assert result.exit_code == 0, result.output
    root = fromstring(result.stdout)
    cdrom = "./devices/disk[@device='cdrom']"
    assert root.find(f"{cdrom}/source[@file='{iso}']") is not None
    assert root.find(f"{cdrom}/readonly") is not None
    assert root.find(f"{cdrom}/boot[@order='1']") is not None
    assert root.find("./devices/disk[@device='disk']/boot[@order='2']") is not None


@pytest.mark.parametrize(
    ("args", "option"),
    [
        (["--disk", "guest.qcow2"], "--disk"),
        (["--iso", "windows.iso"], "--iso"),
        (["--iso", DISK], "--iso"),
        (["--name", "../guest"], "--name"),
        (["--memory-mib", "0"], "--memory-mib"),
        (["--vcpus", "0"], "--vcpus"),
    ],
)
def test_invalid_guest_arguments_are_reported(args: list[str], option: str) -> None:
    result = RUNNER.invoke(app, COMMAND + args)
    assert result.exit_code == 2
    assert option in result.output
    assert not result.stdout
