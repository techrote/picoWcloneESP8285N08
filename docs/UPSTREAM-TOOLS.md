# Obtaining and using the qualified firmware tools

This repository is the hardware documentation home. The existing source-built
diagnostics, firmware lanes and guarded Windows host helpers live in
[techrote/faikeow-now-reciever](https://github.com/techrote/faikeow-now-reciever).
They are referenced rather than duplicated here so their safety fixes,
dependency lock and implementation history retain one source of authority.

## Qualified baseline

| Identity | Value |
|---|---|
| Accepted upstream commit | `2777c90bfb13194feaeb6f7410c8029417af8da4` |
| Reviewed source head before squash | `455723b47d05ec2fa7597303766310d1471825f8` |
| Hardware PR | [#17](https://github.com/techrote/faikeow-now-reciever/pull/17) |
| Exact source-head CI | [38139692927](https://github.com/techrote/faikeow-now-reciever/actions/runs/38139692927), four jobs passed |
| Post-merge CI | [38139869569](https://github.com/techrote/faikeow-now-reciever/actions/runs/38139869569), four jobs passed |

Those are historical qualification identities. If using a newer upstream
version, inspect its changes, manifests and evidence rather than assigning this
baseline's physical acceptance to a new artifact.

## Obtain a separate checkout

For a new checkout, choose a new local directory; do not replace an existing
working tree or reset its changes. The following PowerShell template fetches
the source, not private backups or build dependencies:

```powershell
$ToolCheckout = '<new-absolute-directory-for-qualified-tools>'
git clone https://github.com/techrote/faikeow-now-reciever.git $ToolCheckout
if ($LASTEXITCODE -ne 0) { throw 'Upstream clone failed' }
git -C $ToolCheckout switch --detach 2777c90bfb13194feaeb6f7410c8029417af8da4
if ($LASTEXITCODE -ne 0) { throw 'Qualified baseline checkout failed' }
Set-Location -LiteralPath $ToolCheckout
git rev-parse HEAD
```

**Run the operating runbook's `tools/hardware/`, `diagnostics/`, CMake and
Arduino commands from this checkout.** These paths do not exist as firmware
tools in the dedicated documentation repository. Its own `tools/check_docs.py`
is only a documentation validator.

If the original qualified workspace is already available and suitable, reuse
it after inspecting its branch, dirty state and dependency identities. A
detached baseline is useful for reproduction; use a deliberately selected
branch before implementing new firmware changes.

## Dependencies and host access

Read the upstream [build documentation](https://github.com/techrote/faikeow-now-reciever/blob/2777c90bfb13194feaeb6f7410c8029417af8da4/docs/05-BUILDING.md)
and [dependency lock](https://github.com/techrote/faikeow-now-reciever/blob/2777c90bfb13194feaeb6f7410c8029417af8da4/dependencies.lock.json).
The accepted Linux acquisition/build lane is distinct from the supplemental
native Windows toolchain used for physical USB/serial access. `.deps/` and
`build/` are generated locally and are not included in a clone.

Hardware helper pins are picotool 2.2.0, esptool 4.8.1 and pyserial 3.5. Verify
publisher/source provenance and executable hashes. Follow the board contract
for the native Windows SDK/compiler/Arduino identities. Do not silently
substitute newer tooling or assume WSL can see native Windows USB devices.

`tools/acquire_deps.py` is an explicit dependency acquisition tool, not a device
flasher. Firmware build commands do not implicitly acquire SDKs. No build,
dependency download or CI result substitutes for observed target operation.

Private mappings and original backup pairs are separately required for actual
board operations. They are deliberately unavailable from this public repository.
The runbook records where the original account stored them; on another machine,
transfer preserved records through an appropriate private channel and verify
their hashes before using them.

## Source directories

| Upstream path | Use |
|---|---|
| `tools/hardware/` | Guarded discovery, backup, RAM loading, flashing and captures |
| `diagnostics/rp2040-observer/` | Input-only observer |
| `diagnostics/rp2040-candidate-bridge/` | Transparent UART0 recovery bridge |
| `diagnostics/rp2040-link/` | UART generator/checker |
| `diagnostics/esp-link/esp_link/` | Radio UART diagnostic |
| `diagnostics/esp-rf/esp_rf/` | Isolated ESP-NOW test sender/receiver |
| `firmware/rp2040/` | TinyUSB firmware integration |
| `firmware/esp8266/` | ESP8266-family radio ingress firmware |
| `shared/` | Portable bounded datagram/HID logic |

Read upstream `AGENTS.md` and application authority before modifying these
components. The documentation repository does not change their production
ownership, wire formats or acceptance rules.
