# RP2040 and ESP8285 devboard operating runbook

Use this runbook with the [programming reference](DEVBOARD-PROGRAMMING-REFERENCE.md)
and [accepted board contract](BOARD-CONTRACT.md). It describes the source-built
tools already qualified on Boards A and B. It is an operating reference, not a
script to execute from top to bottom. Choose the section needed for the current
task; reading documentation does not require connecting or reflashing boards.

Commands below are **templates**. Resolve private paths, board identities,
application mode, approved image hashes and fresh ports before running them.
Persistent writes are explicitly separated from discovery and SRAM operations.
This documentation update itself performed no board operations.

Quick navigation: [prepare](#1-session-preparation),
[discover](#2-read-only-discovery-and-target-confirmation),
[build RP](#3-build-rp2040-diagnostics-without-touching-hardware),
[build ESP](#4-build-esp8285-diagnostics-without-touching-hardware),
[preserve](#5-preserve-originals-when-preservation-is-needed),
[load SRAM](#6-load-an-rp-sram-image),
[write or restore flash](#7-persistent-flash-deployment-or-exact-restoration),
[verify](#8-task-specific-verification),
[troubleshoot](#9-tool-catalogue-and-failure-diagnosis),
[handoff](#10-offline-checks-and-handoff).

## 1. Session preparation

**Run tool/build commands from the separate pinned upstream firmware checkout,
not from this documentation repository.** Tool paths such as `tools/hardware/`
and `diagnostics/` belong there. Follow [UPSTREAM-TOOLS.md](UPSTREAM-TOOLS.md)
to acquire that checkout and its verified dependencies. A new checkout will not
contain another machine's `.deps` directory or private board records.

Use native Windows PowerShell and native Windows Python for these helpers.
`pwsh`, picotool, the appropriate USB driver and the pinned Python packages must
be available. Linux build commands in the upstream `docs/05-BUILDING.md` do not grant a Linux or
WSL environment access to the Windows USB devices.

Start with repository state and read the owning task. No hardware access occurs
in these commands:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
$Python = (Resolve-Path '.deps/hardware/python/Scripts/python.exe').Path
& $Python -c 'import esptool, serial; print(esptool.__version__, serial.__version__)'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency inspection failed' }
```

Expected hardware-package versions are esptool 4.8.1 and pyserial 3.5. Do not
upgrade them in place to get a command past a version guard. Qualify any tool
upgrade as a separate change, preserving the working environment.

Prepare session-specific variables. Replace every quoted angle-bracket value;
these are not real paths, IDs or approved artifacts:

```powershell
$PrivateRoot = '<absolute-private-evidence-directory-outside-Git>'
$Identities = Join-Path $PrivateRoot 'board-identities.json'
$Board = 'A'  # Select the physical unit deliberately.
$Picotool = (Resolve-Path '.deps/hardware/picotool-2.2.0/picotool/picotool.exe').Path
$PicotoolSha = 'cba868e55e30bf717196d5b6a3bb5ab3d8ffea8d56afe182d5c4243dfa39d714'
$RunRoot = Join-Path $PrivateRoot ('session-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $RunRoot -ErrorAction Stop | Out-Null
```

The picotool digest above identifies the Windows executable used in the
campaign, not every official picotool build. On another host, acquire and
validate an appropriate binary rather than assigning this digest to it.

Private identities contain per-board `location_path` and `flash_id` fields.
Use the preserved records; do not fabricate values from USB enumeration order.
Radio MAC/chip identity comes from the board's preserved radio backup and live
ROM/application observations. Full raw records must not be pasted into public
issues. Existing output paths are rejected to preserve earlier results.

On the original Windows user profile, locate the campaign directory read-only:

```powershell
$CampaignRoot = Join-Path $env:USERPROFILE '.codex/hardware-private/FNR-002/2026-10-11'
Test-Path -LiteralPath $CampaignRoot
```

If present, it contains `board-identities.json` and the immutable original
backups. A's original pairs are under `board-A-rp2040-original` and
`board-A-radio-original-dtr`; B's are under `board-B-rp2040-original` and
`board-B-radio-original`. Additional remapped RP read pairs were captured when
ports changed. Validate the actual manifests and hashes before selecting any
directory for a guarded operation. The `-dtr` suffix identifies the accepted
A radio read procedure; earlier failed radio dumps are not substitutes.
On another account/machine, obtain the preserved private records deliberately;
public curated evidence cannot reconstruct the original firmware.

**Check native exit codes before dependent operations.** PowerShell can continue
after a failed native command. Every mutating command below has a separate exit
check. For file writes in Python, explicitly use `encoding='utf-8'`; never
submit a generated file to GitHub before verifying successful generation and
nonempty content. This avoids both silent command continuation and Windows
default-encoding failures encountered during the campaign.

## 2. Read-only discovery and target confirmation

Capture a fresh inventory privately:

```powershell
& pwsh -NoProfile -File tools/hardware/discover_windows.ps1 `
  -OutputPath (Join-Path $RunRoot 'inventory.json')
if ($LASTEXITCODE -ne 0) { throw 'Inventory failed' }
```

Inspect the target's location path, driver/interface state, USB mode and COM
port. Compare with the private map. Do not assume that COM7 is still A or COM6
is still B. The recorded BOOTSEL USB serial is shared, while picotool's `--ser`
selector uses the main flash UID. The RP helpers require one selected ROM
target; the RF pair helper separately requires two labeled CDC fixtures.

If the topology moved, stop the write path. Identify the unit read-only by its
known main flash UID and then update the private topology mapping. The original
backup remains immutable. The RP flash helper compares backup identity metadata
with the current mapping; a legitimate move requires a new matching backup
record under the new mapping, or a deliberately reviewed migration procedure.
Do not edit the original backup's metadata to satisfy the guard.

When there is no USB device, first resolve the cable/port/power observation.
No USB enumeration is not itself evidence that flash was corrupted. Ask for
one specific board/cable action if physical intervention is essential.

## 3. Build RP2040 diagnostics without touching hardware

Use the verified SDK, compiler, CMake and Ninja. Add their verified directories
to the current shell's PATH according to the local installation; do not use
an arbitrary compiler found first on PATH. Set `PICO_SDK_PATH` to the accepted
SDK checkout. `picotool_DIR` is a **CMake package directory**, not the executable.

### Input-only observer in SRAM

```powershell
$env:PICO_SDK_PATH = (Resolve-Path '.deps/pico-sdk').Path
$PicotoolCmake = '<absolute-picotool-CMake-package-directory>'
cmake -S diagnostics/rp2040-observer -B build/observer -G Ninja `
  -DPICO_PLATFORM=rp2040 -DPICO_BOARD=pico -DPICO_NO_FLASH=1 `
  "-Dpicotool_DIR=$PicotoolCmake" -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE -ne 0) { throw 'Observer configure failed' }
cmake --build build/observer
if ($LASTEXITCODE -ne 0) { throw 'Observer build failed' }
& $Python tools/hardware/check_ram_uf2.py build/observer/fnr_observer.uf2
if ($LASTEXITCODE -ne 0) { throw 'Observer is not a valid SRAM UF2' }
```

The observer keeps GPIO0–29 as inputs with pulls disabled. `INFO` reads flash
JEDEC/UID and output-enable state. `EDGES ms` samples transitions; `RX pin baud ms`
is bounded input-only PIO capture. Those are correlation tools, not calibrated
edge counts or a complete pinout measurement. See its [README](https://github.com/techrote/faikeow-now-reciever/blob/2777c90bfb13194feaeb6f7410c8029417af8da4/diagnostics/rp2040-observer/README.md).

### Transparent UART bridge in SRAM

```powershell
cmake -S diagnostics/rp2040-candidate-bridge -B build/candidate-bridge -G Ninja `
  -DPICO_PLATFORM=rp2040 -DPICO_BOARD=pico -DPICO_NO_FLASH=1 `
  -DFNR_ALLOW_CANDIDATE_UART=1 "-Dpicotool_DIR=$PicotoolCmake" `
  -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE -ne 0) { throw 'Bridge configure failed' }
cmake --build build/candidate-bridge
if ($LASTEXITCODE -ne 0) { throw 'Bridge build failed' }
& $Python tools/hardware/check_ram_uf2.py build/candidate-bridge/fnr_candidate_bridge.uf2
if ($LASTEXITCODE -ne 0) { throw 'Bridge is not a valid SRAM UF2' }
```

This enables only the proven UART route, GP0/GP1, with GP0 2 mA drive. The
`FNR_ALLOW_CANDIDATE_UART` name is historical; the route is now independently
verified. [Bridge details](https://github.com/techrote/faikeow-now-reciever/blob/2777c90bfb13194feaeb6f7410c8029417af8da4/diagnostics/rp2040-candidate-bridge/README.md)
explain DTR handling and bounded forwarding.

For the SRAM UART checker, use source `diagnostics/rp2040-link`, a separate
build directory such as `build/rp-link`, and `PICO_NO_FLASH=1`. Its artifact
is `fnr_link_diag.uf2`. Do not load the checker when a transparent radio ROM
bridge is needed; they provide different protocols.

### Optional persistent labeled bridge

Use a separate build directory and explicit configuration:

```powershell
cmake -S diagnostics/rp2040-candidate-bridge -B build/bridge-A-flash -G Ninja `
  -DPICO_PLATFORM=rp2040 -DPICO_BOARD=pico -DPICO_NO_FLASH=0 `
  -DFNR_ALLOW_CANDIDATE_UART=1 -DFNR_DIAG_BOARD_LABEL=A `
  -DFNR_BRIDGE_FLASH_RECOVERY_TEST=1 "-Dpicotool_DIR=$PicotoolCmake" `
  -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE -ne 0) { throw 'Flash bridge configure failed' }
cmake --build build/bridge-A-flash
if ($LASTEXITCODE -ne 0) { throw 'Flash bridge build failed' }
```

For B use label B and a different directory. These builds **replace RP
application flash when deployed**, so use the guarded flash path in section 7,
not the SRAM loader. Keep the flash bridge only when the current task needs a
persistent recovery fixture. The label distinguishes USB interfaces, not silicon.

## 4. Build ESP8285 diagnostics without touching hardware

The portable Arduino CLI configuration must refer to the verified
`esp8266:esp8266@3.1.2` installation. For the UART diagnostic:

```powershell
$ArduinoCli = '<absolute-verified-arduino-cli.exe>'
$ArduinoConfig = '<absolute-portable-arduino-cli-config>'
$CommonInclude = (Resolve-Path 'diagnostics/common').Path.Replace('\', '/')
& $ArduinoCli --config-file $ArduinoConfig compile `
  --fqbn 'esp8266:esp8266:esp8285:xtal=80,CrystalFreq=26,eesz=1M,wipe=none' `
  --build-property "compiler.cpp.extra_flags=-I$CommonInclude" `
  --build-path build/esp-link diagnostics/esp-link/esp_link
if ($LASTEXITCODE -ne 0) { throw 'ESP UART diagnostic build failed' }
```

For the RF diagnostic, select sketch `diagnostics/esp-rf/esp_rf` and output
`build/esp-rf`. Preserve the same qualified ESP8285 board configuration and
common include path. Record source commit/dirty state, CLI/core/compiler
identities, full build arguments and image SHA-256. If include paths contain
spaces, validate compiler argument quoting for that installation.

The radio helper verifies image checksum and the DOUT / 1 MiB / 40 MHz header.
An ESP32 binary, a 4 MiB image layout or an arbitrary downloaded ESP8266 image
does not meet this contract. Review source and intended configuration before
approving an image hash. A SHA-256 calculated from an unknown binary is not
provenance. See [diagnostic-builds.json](../evidence/FNR-002/diagnostic-builds.json)
for historical artifact identities; a rebuild may legitimately have a new hash.

## 5. Preserve originals when preservation is needed

Reuse the existing unchanged backups when their identity and integrity are
established. Do not relabel today's diagnostic flash as the board's original.
If a new baseline is needed, name it according to its actual installed state.

### RP2040 complete read pair

Precondition: the selected board is in BOOTSEL and its identity mapping is
current. For the characterized blank A, use explicit range mode:

```powershell
$RpBackup = Join-Path $RunRoot 'rp-preserved'
& $Python tools/hardware/rp2040_backup.py --board $Board --identities $Identities `
  --picotool $Picotool --picotool-sha256 $PicotoolSha `
  --expected-size 2097152 --explicit-range --output $RpBackup
if ($LASTEXITCODE -ne 0) { throw 'RP preservation failed; do not write' }
```

For a nonblank image with known complete extent, the helper also supports its
`save -a` path by omitting `--explicit-range`. Require both complete reads and
matching hashes. An RPI-RP2 volume is a bootloader interface, not a flash dump.

### Radio complete read pair

Precondition: radio ROM entered physically, RP transparent bridge running,
mapped CDC positively identified. `$Port` and `$ExpectedMac` must come from
fresh discovery and the selected board's known identity.

```powershell
$Port = '<fresh-mapped-COM-port>'
$ExpectedMac = '<private-selected-radio-MAC>'
$BridgeSha = '<approved-deployed-bridge-SHA256>'
$RadioBackup = Join-Path $RunRoot 'radio-preserved'
& $Python tools/hardware/radio_backup.py --board $Board --identities $Identities `
  --port $Port --expected-mac $ExpectedMac --expected-flash-id 0x14325e `
  --expected-size 1048576 --bridge-sha256 $BridgeSha --output $RadioBackup
if ($LASTEXITCODE -ne 0) { throw 'Radio preservation failed; do not write' }
```

The integer `0x14325e` is the esptool representation of JEDEC bytes `5e 32 14`.
Do not reverse it based only on visual byte ordering. The helper uses the
official RAM stub, DTR true, target/MAC/flash checks and two full reads.
An all-zero bare-ROM flash ID was an unsuccessful initial observation on B;
the stub provided its valid identity. Short or mismatching reads are unusable
as restoration inputs.

## 6. Load an RP SRAM image

Precondition: selected RP in BOOTSEL; image reviewed and independently hashed.
This path validates every UF2 SRAM destination and rejects flash images.

```powershell
$Image = (Resolve-Path 'build/candidate-bridge/fnr_candidate_bridge.uf2').Path
$ImageSha = '<approved-this-build-SHA256>'
& $Python tools/hardware/load_ram.py --board $Board --identities $Identities `
  --picotool $Picotool --picotool-sha256 $PicotoolSha `
  --image $Image --image-sha256 $ImageSha --output (Join-Path $RunRoot 'ram-load')
if ($LASTEXITCODE -ne 0) { throw 'SRAM deployment failed' }
```

Check expected USB/application identity after load. Power loss removes the SRAM
application, returning control to whatever is in RP flash. Verified SRAM load
does not prove that the installed flash application is usable.

## 7. Persistent flash deployment or exact restoration

Use these sections only when the task calls for persistent deployment. Each
write targets one positively identified board with its own intact backup pair.
Use fresh output directories; leave failed attempts intact. The helpers verify
image bytes independently after writing and report boot as a separate claim.

### RP2040 flash

Precondition: selected RP in BOOTSEL. `$RpBackup` refers to its preserved pair,
and `$Geometry` to its private measured observation containing `board`,
`flash_id`, `jedec_hex` and `size_bytes`.

```powershell
$Geometry = '<private-selected-board-geometry.json>'
$Image = '<absolute-reviewed-RP-flash-UF2>'
$ImageSha = '<approved-image-SHA256>'
& $Python tools/hardware/rp2040_flash.py --board $Board --identities $Identities `
  --backup $RpBackup --geometry $Geometry --picotool $Picotool `
  --picotool-sha256 $PicotoolSha --image $Image --image-sha256 $ImageSha `
  --mode diagnostic --output (Join-Path $RunRoot 'rp-write')
if ($LASTEXITCODE -ne 0) { throw 'RP write/readback failed; inspect retained logs' }
```

The existing `diagnostic` mode means a reviewed flash UF2 deployment; its name
does not grant production acceptance. UF2 family, block consistency, duplicate
destinations, flash base and measured capacity are checked.

For exact restoration, set `$Image` to that board's `original-1.bin`, `$ImageSha`
to its preserved backup digest, change mode to `restore`, and use a new output
directory. Restore mode requires the complete 2 MiB binary at `0x10000000`.
Confirm resulting ROM/application behavior separately. Blank A should return
to RPI-RP2; B's pre-existing application previously offered no USB interface.

### ESP8285 flash

Precondition: radio ROM/stub and transparent RP bridge, fresh port/topology,
selected radio identity, intact original radio backup pair. No RP GPIO reset
assumption is made.

```powershell
$Image = '<absolute-reviewed-ESP8285-image.bin>'
$ImageSha = '<approved-image-SHA256>'
& $Python tools/hardware/radio_flash.py --board $Board --identities $Identities `
  --port $Port --expected-mac $ExpectedMac --backup $RadioBackup `
  --image $Image --image-sha256 $ImageSha --mode diagnostic `
  --output (Join-Path $RunRoot 'radio-write')
if ($LASTEXITCODE -ne 0) { throw 'Radio write/readback failed; inspect retained logs' }
```

For exact restoration, select that radio's complete `original-1.bin` and backup
digest, use `--mode restore` and a new output directory. Do not restore A's
image onto B or substitute a generic image. Keep all original header bytes.
Readback success establishes restoration of bytes; original application silence
is not a reason to erase or repeatedly retry an otherwise exact restoration.

After deployment, use `radio_app_probe.py` for the UART diagnostic or
`rf_app_probe.py` for the RF diagnostic. Their `--help` lists the required
write/deployment records and identity arguments. Choose `--boot-kind software`
unless a real power reconnection was confirmed. A UART probe cannot validate an
RF diagnostic just because both run on the same chip.

## 8. Task-specific verification

### UART smoke or integrity run

Requires the RP UART checker and ESP UART diagnostic, not the transparent
bridge or RF image. `$RadioChipId` comes from the selected radio's private
identity; `$RadioWrite` is the corresponding deployment `result.json`.

```powershell
$RadioChipId = '<private-ROM-chip-ID-as-integer-or-hex>'
$RadioWrite = '<private-matching-radio-write-result.json>'
$RpCheckerSha = '<approved-deployed-RP-checker-SHA256>'
& $Python tools/hardware/link_capture.py --board $Board --identities $Identities `
  --port $Port --seconds 10 --expected-radio-chip-id $RadioChipId `
  --rp-image-sha256 $RpCheckerSha --radio-write-result $RadioWrite `
  --output (Join-Path $RunRoot 'uart-smoke')
if ($LASTEXITCODE -ne 0) { throw 'UART smoke failed' }
```

Use `--seconds 600` only when a new integrity qualification is warranted. The
helper enforces counts, duration, complete final markers, matching counters and
zero unexplained errors. `uart_fault_capture.py` separately tests damage/reset
recovery; use its required SRAM bridge, tool hashes and deployment arguments.
It is not a production framing acceptance test.

### Focused RF follow-up

Requires both radios running the same approved RF diagnostic, two separately
labeled persistent RP bridges, current mapping, and verified deployment records.
This helper makes runtime RF configuration changes but performs no flash write.
For a focused reproduction of the known reverse channel result:

```powershell
$PortA = '<fresh-A-COM-port>'
$PortB = '<fresh-B-COM-port>'
$BackupA = '<private-A-radio-backup-directory>'
$BackupB = '<private-B-radio-backup-directory>'
$WriteA = '<private-A-RF-write-result.json>'
$WriteB = '<private-B-RF-write-result.json>'
$RfImageSha = '<approved-common-deployed-RF-image-SHA256>'
& $Python tools/hardware/rf_pair_capture.py --identities $Identities `
  --port-A $PortA --port-B $PortB --backup-A $BackupA --backup-B $BackupB `
  --radio-write-A $WriteA --radio-write-B $WriteB --radio-image-sha256 $RfImageSha `
  --direction B-to-A --case reject_source --case wrong_channel `
  --output (Join-Path $RunRoot 'rf-focused')
if ($LASTEXITCODE -ne 0) { throw 'RF case failed; preserve and inspect this capture' }
```

Failure is an expected possible outcome of this channel-negative case; it
must not be converted to PASS or followed by unrelated writes. The historical
focused 1,000-packet experiment used an additional private observer; this
reusable command runs the repository's selected-case recipes, not that identical
1,000-packet capture. Omit selection only when a full campaign is needed.
The helper stops on first failure, retains captures, and sends OFF in cleanup.
Do not rerun earlier passes solely to hide a retained failure.

The later [distance/power investigation](RF-CHANNEL-BEHAVIOR.md) establishes
that a channel mismatch is not a reliable exclusion boundary. Its new helper
options belong to the [follow-up tool revision](UPSTREAM-TOOLS.md#rf-follow-up-revision),
not the historical FNR-002 checkout. With reviewed POWER-capable diagnostics
already deployed and exact per-board write/readback records, use the same
guarded command above with `--case burst --case reject_source --case wrong_channel`,
`--receive-channel 1 --mismatch-channel 6 --mismatch-count 1000`,
`--separation-cm <actual-operator-reported-distance>` and
`--power-limit-qdbm <requested-0-to-82-ceiling>`. Select a fresh output directory
for each run and retain the selected direction. The tool records configuration
and verifies final reported channels/ceilings. An older image cannot acknowledge
POWER; do not bypass that guard or infer calibration from the field.

A useful task-specific comparison keeps geometry/image fixed and includes
same-channel integrity and source-reject controls around high/low/high power.
Residual mismatch packets still fail the negative test; the completed campaign
already demonstrated this. Repeating it is unnecessary unless a new change or
specific failure warrants the comparison. Cleanup sends OFF and closes handles;
confirm final state rather than assuming an exception stopped all activity.

### USB observations

With accepted HID firmware deployed and its record available:

- `hid_probe_windows.py`: exact mapped collection, parsed capabilities and
  read-only GET_REPORT attempt. Requires either a flash write record or a
  verified `--ram-load-record`.
- `usb_descriptors_windows.py`: device/configuration descriptors from the
  selected hub port, given `--vid 0xcafe --pid 0xf003` for that development image.
- `hid_idle_windows.py`: target-only Raw Input observation for 20 or 60 seconds,
  using the preceding probe record. No desktop injection or suppression.

Read each helper's `--help` before invocation. Descriptor/idle tests do not
validate active movement, released buttons, timeout neutralization or sleep/wake.
Plan controlled active stimuli before attempting them; production firmware has
no synthetic mouse generator.

## 9. Tool catalogue and failure diagnosis

| Tool under `tools/hardware/` | Use |
|---|---|
| `discover_windows.ps1` | Read-only raw USB/driver/COM inventory, outside Git |
| `check_ram_uf2.py` | Offline SRAM UF2 validation |
| `rp2040_backup.py` | Two complete mapped RP flash reads |
| `load_ram.py` | Guarded SRAM UF2 load |
| `rp2040_flash.py` | Guarded RP flash UF2 / exact original restoration |
| `radio_backup.py` | Guarded radio identity and full paired reads |
| `radio_flash.py` | Guarded ESP image write/restoration and exact readback |
| `radio_app_probe.py`, `rf_app_probe.py` | Application-specific identity observations |
| `link_capture.py`, `uart_fault_capture.py` | UART smoke/soak and separate fault campaign |
| `rf_pair_capture.py` | Focused/full two-board RF recipes |
| `hid_probe_windows.py` | Parsed HID capabilities/GET_REPORT attempt |
| `usb_descriptors_windows.py` | Raw USB device/configuration descriptor capture |
| `hid_idle_windows.py` | Bounded target-only mouse idle observation |
| `test_guards.py`, `test_esptool_integration.py` | Offline helper regressions |

| Symptom | First action |
|---|---|
| Topology/UID/MAC mismatch | Stop writes; inspect fresh discovery and physical mapping |
| No RPI-RP2 or USB device | Check requested board, known data cable and button sequence |
| picotool cannot access present ROM | Inspect RP2 Boot Interface 1 driver; preserve MSC/parent drivers |
| Radio SYNC fails | Verify radio ROM entry, transparent bridge and selected port; DTR/RTS do not reset radio |
| Short full radio read | Treat dump as invalid; inspect DTR/bridge counters and interrupted stub state |
| Application boot probe fails | Check correct image/probe/baud and readback; do not infer failed restoration from AT silence |
| UART error/drop counters rise | Retain capture, compare task load, USB service and bounded ring behavior |
| Wrong-channel RF reception | Preserve negative result and live channel samples; use issue #5, no assumed cause |
| Windows GET_REPORT error 1 | Retain limitation; it did not establish a neutral report or firmware defect |

## 10. Offline checks and handoff

For changes to hardware tools, use appropriate offline checks before hardware:

```powershell
& $Python tools/hardware/test_guards.py
if ($LASTEXITCODE -ne 0) { throw 'Guard regressions failed' }
& $Python tools/hardware/test_esptool_integration.py
if ($LASTEXITCODE -ne 0) { throw 'Pinned integration regression failed' }
& $Python -m compileall -q tools/hardware
if ($LASTEXITCODE -ne 0) { throw 'Python syntax check failed' }
git diff --check
if ($LASTEXITCODE -ne 0) { throw 'Whitespace check failed' }
```

Documentation-only edits need link/claim/command review and whitespace checks,
not a fresh hardware campaign. Verify public evidence hashes from committed Git
blobs or an LF-normalized checkout; Windows checkout line-ending conversion
can otherwise change byte hashes despite unchanged committed evidence.

Before ending a hardware session, record:

- Source branch/full commit, dirty state, build arguments and image/tool hashes.
- Board and MCU touched, memory domain, identity/mapping/deployment records.
- Tests and measured counters; distinguish deliberate loss, failed attempts
  and untested behavior.
- Actual firmware on each MCU, connected/unplugged state, current observed
  USB/COM mapping, whether test traffic is stopped, and closed host handles.
- Original backup location privately; public evidence paths and remaining gates.
- One specific next manual operation only if needed to continue the task.

Do not imply that work will continue unattended. Do not restore/reflash merely
to reproduce the historical fixture snapshot. Leave the boards in the state
needed by the authorized task and describe that state accurately.
