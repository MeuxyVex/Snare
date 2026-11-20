# Set up the Snare analysis lab

Use a dedicated Intel x86-64 host running Ubuntu 24.04 LTS or Debian 12. Snare's initial lab uses KVM, QEMU and libvirt. The steps below build an offline Windows 10 x64 compatibility guest with a single local qcow2 disk and a powered-off baseline snapshot. A spare GPU is optional for this verification. A separate adapter must remain available for the host if you assign a GPU.

The guest starts with no network adapter. Keep it disconnected until the roadmap's host-side network controls are installed and verified. Use official installation media and benign test files for setup. Keep guest images, snapshots and test artifacts outside the Git checkout.

## 1. Enable hardware virtualization

In the host firmware, enable **Intel Virtualization Technology (VT-x)** and **Intel VT-d**. Save and boot Linux.

**Verify on the host:**

```sh
grep -m1 -o -w vmx /proc/cpuinfo
```

Expected: `vmx`. If it is absent, confirm the host CPU supports VT-x and that virtualization is enabled in firmware. Verify VT-d after booting with the IOMMU settings below.

## 2. Enable the Intel IOMMU

For a GRUB host, edit `/etc/default/grub` as an administrator. Append `intel_iommu=on iommu=pt` inside the existing `GRUB_CMDLINE_LINUX_DEFAULT` quotes. Preserve the other boot arguments. These flags enable Intel IOMMU support and use passthrough domains by default for host devices where applicable. Rebuild the boot configuration and restart the host:

```sh
sudo update-grub
sudo reboot
```

For another bootloader, add the flags using that bootloader's documented procedure.

**Verify after restart:**

```sh
grep -oE 'intel_iommu=on|iommu=pt' /proc/cmdline
sudo dmesg | grep -Ei 'DMAR|IOMMU' | head -n 15
find /sys/kernel/iommu_groups -mindepth 1 -maxdepth 1 -type d | head
```

Expected: both flags, Intel DMAR/IOMMU initialization messages, and numbered IOMMU groups. Address firmware or kernel errors before assigning any PCI device. See the [Linux kernel VFIO documentation](https://docs.kernel.org/driver-api/vfio.html) for the relationship between devices and groups.

## 3. Install KVM, QEMU and libvirt

```sh
sudo apt update
sudo apt install qemu-system-x86 qemu-utils libvirt-daemon-system libvirt-clients virt-manager pciutils
sudo systemctl enable --now libvirtd
sudo usermod -aG libvirt,kvm "$USER"
```

Sign out of the Linux session and sign back in so the group membership takes effect. Give libvirt access only to trusted lab accounts because they can manage the host's virtual machines.

**Verify:**

```sh
test -c /dev/kvm && echo '/dev/kvm available'
virt-host-validate qemu
virsh -c qemu:///system list --all
```

Expected: `/dev/kvm available`, successful hardware virtualization and KVM access checks, and a domain list without a connection or permission error. Optional capabilities can produce warnings on some hosts.

## 4. Install a Windows guest with no network adapter

Open Virtual Machine Manager (`virt-manager`) and select the local system QEMU/KVM connection. Create a VM from a legitimate Windows ISO. Before starting the installation, enable **Customize configuration before install**. Use these choices:

| Setting | Value |
| --- | --- |
| VM name | `snare-windows` |
| Guest for this snapshot procedure | Windows 10 x64 and legacy BIOS firmware |
| Memory and CPU | 8 GiB and 4 vCPUs for setup if the host has capacity |
| Storage | One local qcow2 disk, about 80 GiB virtual capacity, on a libvirt storage pool |
| Display | A local virtual display for setup |
| Network | Remove the network device from the configuration |

Complete the Windows installation using the local console, then eject the installer ISO. The legacy BIOS guest is for offline compatibility testing. Windows 10 22H2 reached the end of routine updates. If you need Windows 11, use its required UEFI and TPM settings and validate a snapshot strategy that includes firmware and TPM state separately. See [Windows servicing status](https://learn.microsoft.com/windows/release-health/supported-versions-windows-client) and [Windows 11 requirements](https://learn.microsoft.com/en-us/windows/whats-new/windows-11-requirements).

**Verify on the host:**

```sh
virsh -c qemu:///system domstate snare-windows
virsh -c qemu:///system domblklist snare-windows --details
virsh -c qemu:///system domiflist snare-windows
```

Expected: `running`, a local system disk with a qcow2 path, and no interfaces below the `domiflist` header.

**Verify inside Windows using PowerShell:**

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, OSArchitecture
Get-NetIPConfiguration
```

Expected: Windows 10 and 64-bit architecture, with no active Ethernet connection or default gateway configured for the guest.

## 5. Optional: assign a spare GPU through VFIO

Identify the spare GPU and its companion functions:

```sh
lspci -Dnn | grep -Ei 'VGA|3D controller|Audio'
```

After confirming the PCI address, set `GPU` to the spare adapter's address. The value below is an example.

```sh
GPU=0000:03:00.0
test -L "/sys/bus/pci/devices/$GPU/iommu_group" &&
    ls -l "/sys/bus/pci/devices/$GPU/iommu_group/devices/"
lspci -Dnnk -s "$GPU"
```

Expected: the selected GPU and its IOMMU group members. Stop if the group contains the host display adapter, a storage controller, a host network device or any other device the host needs. Check all functions before attaching them.

Shut Windows down normally. In Virtual Machine Manager, use **Add Hardware → PCI Host Device** to add the spare GPU and any required companion functions, such as HDMI audio. Use libvirt's managed PCI assignment so it binds the device to `vfio-pci` while the guest uses it and reattaches it on shutdown. Keep the local virtual display during setup. See the [libvirt managed PCI device documentation](https://www.libvirt.org/manpages/virsh.html#nodedev-detach).

**Verify the saved assignment and then start the guest:**

```sh
virsh -c qemu:///system dumpxml snare-windows --inactive | grep -A6 '<hostdev'
virsh -c qemu:///system start snare-windows
lspci -Dnnk -s "$GPU"
```

Expected: the device XML contains a managed PCI host device, the guest starts, and the hardware listing shows `Kernel driver in use: vfio-pci` for the spare GPU. In Windows, `Get-PnpDevice -PresentOnly -Class Display` should list the assigned display adapter. Driver installation may be needed before Windows reports the vendor name. If the guest cannot start, inspect the domain log and confirm that every required function is available to VFIO. Remove the PCI assignment while the guest is off to fall back to the virtual display.

## 6. Create and test the clean snapshot

Finish installing any benign test software, remove installation media, and shut the guest down normally. This procedure requires the offline legacy BIOS VM and one local qcow2 disk. Confirm the state before creating the snapshot.

```sh
virsh -c qemu:///system domstate snare-windows
virsh -c qemu:///system dumpxml snare-windows --inactive
virsh -c qemu:///system domblklist snare-windows --details
```

Expected: `shut off`, a single writable disk with a `qcow2` driver in the XML, no mounted installer ISO, and no UEFI NVRAM or TPM state to include. Then create the internal snapshot and list it:

```sh
virsh -c qemu:///system snapshot-create-as snare-windows clean --description 'Clean offline Windows baseline'
virsh -c qemu:///system snapshot-list snare-windows --name --inactive
```

Expected: the create command reports that `clean` was created, and the inactive snapshot list contains `clean`. See the [virsh snapshot command reference](https://www.libvirt.org/manpages/virsh.html#snapshot-create-as).

To verify restoration, boot the VM and create a disposable file in the guest:

```powershell
Set-Content -LiteralPath "$env:PUBLIC\snare-restore-check.txt" -Value "restore check"
Test-Path -LiteralPath "$env:PUBLIC\snare-restore-check.txt"
```

Expected: `True`. Shut down the guest normally. Reverting discards the VM disk changes since the snapshot. Use this only on the dedicated lab VM and keep any data you need outside the guest first.

```sh
virsh -c qemu:///system domstate snare-windows
# Continue only after the previous command reports "shut off".
virsh -c qemu:///system snapshot-revert snare-windows clean
virsh -c qemu:///system snapshot-current snare-windows --name
virsh -c qemu:///system start snare-windows
```

Expected: `clean` is current and the guest boots. Inside the guest, run `Test-Path -LiteralPath "$env:PUBLIC\snare-restore-check.txt"`. Expected: `False`. Shut the guest down again. Record the host OS, `virsh --version`, guest edition, and the results of the checks in your local lab notes.

Use `qemu:///system`, `snare-windows`, and `clean` for the matching settings in [snare.example.toml](../snare.example.toml). Set the actual network bridge when host-side network controls are available.
