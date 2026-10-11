# Agent instructions

## Purpose and reading order

This is a dedicated hardware documentation repository for the characterized
RP2040 + ESP8285N08 clone Pico W devboards. It is not a firmware application or
a copy of the receiver project's issue tracker.

Before board programming, hardware decisions or substantive documentation edits,
read:

1. `README.md`
2. `docs/DEVBOARD-PROGRAMMING-REFERENCE.md`
3. `docs/BOARD-CONTRACT.md`
4. `docs/UPSTREAM-TOOLS.md`
5. The relevant sections of `docs/DEVBOARD-OPERATING-RUNBOOK.md`
6. `docs/EVIDENCE-AND-PROVENANCE.md` and the relevant evidence record

## Established facts

- Both measured units: RP2040 B2, 2 MiB external flash, ESP8285N08 with 1 MiB
  embedded flash. ESP8285 is ESP8266-family Wi-Fi hardware, without Bluetooth.
- UART0 GP0 TX -> radio RX, GP1 RX <- radio TX is independently proven on both
  at 115200 8N1, without flow control. No external wiring is needed for this link.
- RP-controlled radio reset/download, complete header routing and electrical
  measurements are unknown. Never drive an assumed control pin.
- Physical near-button RP BOOTSEL and far-button radio ROM entry during power
  reconnect are tested. Both-button reconnection enabled recovery when the
  existing RP application offered no USB.
- BOOTSEL USB serial strings are shared. Use current topology plus private RP
  flash UID/radio MAC, not historical COM numbers or enumeration order.

## Scope and reuse

- Documentation work requires no board handling or firmware writes.
- Firmware/helper paths in the runbook belong to a separate qualified upstream
  checkout. Read that project's own instructions before changing its code.
- Keep this reference usable for different applications; do not import a single
  application's architectural restrictions as universal hardware limitations.
- Reuse accepted recovery/UART evidence. Repeat qualification only when a task's
  changes or an observed failure warrants it. Do not investigate original
  firmware solely because it differs or does not answer AT commands.
- A meter is unnecessary for the established onboard UART; request electrical
  discovery only when a task depends on an unknown net or voltage.
- Ask for one concrete physical operation when essential and unavailable in
  software, identifying the board, button/cable action and expected observation.

## Preservation and evidence

- Prefer SRAM for temporary RP programs. Before persistent writes, require
  correct identity, measured geometry, intact original backup pair, reviewed
  image provenance/hash and a working recovery path.
- Use guarded helpers and separate byte-for-byte readback from boot observation.
  Do not issue an unqualified mass erase or overwrite both boards simultaneously.
- Keep firmware dumps, complete UIDs/MACs, host paths, raw logs and credentials
  private outside Git. Public evidence contains curated fields and digests.
- `evidence/FNR-002/` is the immutable upstream snapshot. Do not rewrite it or
  regenerate its checksum manifest to hide changed historical data. New
  campaigns belong in separately named directories with their own manifests.
- Every new physical claim needs date, unit identity, host, source commit/dirty
  state, image/tool hashes, configuration, observed result and acceptance scope.
- Use PASS / FAIL / BLOCKED / NOT TESTED. Preserve failures and intentional-loss
  accounting. Build success is not physical acceptance.
- Keep the RF channel anomaly and incomplete USB/integrated application gates
  explicit until new evidence resolves them. SDK channel queries do not alone
  establish actual over-the-air behavior.
- Read `docs/RF-CHANNEL-BEHAVIOR.md` for the subsequent distance/power evidence:
  SDK channel selection is not a packet-exclusion guarantee, and reduced power
  or greater separation does not establish isolation. The precise RF mechanism
  remains unmeasured. Preserve every historical negative failure.

## Documentation checks and delivery

- Use UTF-8 and LF line endings. Check local links and public evidence integrity
  with `python tools/check_docs.py` and whitespace with `git diff --check`.
- Check native command exit codes before dependent writes or publication.
- Explain verified changes and remaining limits. For hardware work, record
  actual final firmware, connection mapping, stopped test activity and closed
  handles. Do not claim unattended future work.
