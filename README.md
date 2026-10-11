# RP2040 and ESP8285N08 clone Pico W devboard

Hardware reference, programming procedures and measured characterization for
clone Pico W devboards built around **RP2040 + ESP8285N08**. This repository
documents the board independently of any one application, for developers and
coding agents reusing it in future projects.

**ESP8285N08 provides Wi-Fi and ESP-NOW, without Bluetooth.** It is an
ESP8266-family chip with embedded flash. These boards do not contain the
CYW43439 wireless chip expected by genuine Pico W software. A Bluetooth
application would need an additional Bluetooth controller and suitable firmware.

The measurements below apply to two independently characterized units, A and B,
tested on **11 October 2026**. Other boards sold under similar names may differ;
their markings, revision and routing must not be assumed identical.

## Start here

| Document | Purpose |
|---|---|
| [Programming reference](docs/DEVBOARD-PROGRAMMING-REFERENCE.md) | Detailed hardware/software capabilities, resource ownership, toolchains, recovery, measured limits, future projects and reusable agent context |
| [Operating runbook](docs/DEVBOARD-OPERATING-RUNBOOK.md) | Guarded discovery, build, backup, SRAM-load, flash/restore and verification command templates |
| [Board contract](docs/BOARD-CONTRACT.md) | Accepted physical observations, recovery procedures and limitations for A and B |
| [Upstream tools](docs/UPSTREAM-TOOLS.md) | Where firmware and helper scripts live, how to obtain the exact qualified checkout and which directory commands run in |
| [Evidence and provenance](docs/EVIDENCE-AND-PROVENANCE.md) | Measurement origin, immutable public snapshot, acceptance boundaries and privacy |
| [Physical test matrix](evidence/FNR-002/test-matrix.md) | PASS / FAIL / BLOCKED / NOT TESTED by case and board |
| [Agent instructions](AGENTS.md) | Rules for maintaining this reference and using it in programming tasks |

## Established hardware

| Resource | Independently established on both boards |
|---|---|
| Main MCU | RP2040 B2 |
| RP flash | 2 MiB external; JEDEC `68 40 15`; exact part unverified |
| Radio MCU | ESP8285N08 |
| Radio flash | 1 MiB embedded; JEDEC `5e 32 14` |
| Reported radio crystal | 26 MHz |
| Onboard link | RP2040 UART0 GP0 TX → radio RX; GP1 RX ← radio TX |
| Qualified link configuration | 115200 baud, 8N1, no flow control |
| USB | Connected to RP2040; ROM, CDC or HID identity depends on mode/firmware |
| Near-USB button | RP2040 BOOTSEL when held during USB reconnection |
| Far-from-USB button | Radio ROM download entry when held during USB reconnection |
| RP-controlled radio reset/download pins | Unknown; do not drive assumed GPIOs |
| Complete header routing / electrical measurements | Not established |

```text
Wireless sender ~~~ ESP-NOW ~~~ ESP8285N08
                                   |
                         existing onboard UART
                         GP0 TX / GP1 RX on RP2040
                                   |
                                RP2040
                                   |
                                  USB
                                   |
                                  PC
```

No external wiring is needed for the established RP2040–radio link. GP numbers
are RP2040 GPIO numbers, not a verified complete header pinout.

## Measured results and limits

- **Independent recovery passed:** matching complete original backup pairs for
  both MCUs on both boards, reversible deployment and byte-for-byte restoration.
- **UART integrity passed:** each board ran ten active minutes with 11,998
  matching request/echo pairs and 12,039 independent radio stream frames
  including drain, with zero unexplained integrity errors or drops. Both passed
  burst/damage/resynchronization and independent MCU restart/recovery cases.
- **ESP-NOW exchange worked in both directions:** 19/20 campaign cases passed,
  including 6,000-packet sustained runs in each direction. Reverse
  software-channel-mismatch isolation failed and reproduced; its cause remains
  unresolved in the historical campaign. See the
  [anomaly record](evidence/FNR-002/rf-channel-anomaly.json) and
  [upstream follow-up](https://github.com/techrote/faikeow-now-reciever/issues/5#issuecomment-6109075436).
- **USB mouse enumeration/cold re-enumeration passed on both:** active controls,
  complete neutral/fail-safe behavior and suspend/resume were not fully
  physically accepted. The full integrated wireless receiver and reference
  sender interoperability remain separate application work.

These results establish useful hardware facts, not maximum throughput, range,
latency or complete application acceptance. Read the test matrix before reusing
a result. Existing firmware differed because one unit had previously been used;
its original application protocol and factory provenance are unknown.

## Programming workflow

1. Read the reference, board contract and task-relevant runbook section.
2. Obtain the pinned [upstream tools checkout](docs/UPSTREAM-TOOLS.md).
3. Identify the selected physical unit from fresh topology plus private main
   flash UID/radio MAC. COM numbers and shared BOOTSEL strings are insufficient.
4. Reuse intact original backups and accepted evidence. Prefer SRAM for
   temporary RP diagnostics; use guarded writes and exact readback when flash
   deployment is required.
5. Verify the behavior affected by the change and record the final fixture
   state. Repeat a long qualification only when the change or a failure warrants it.

This repository contains documentation and public evidence. Source-built
diagnostics, firmware and Windows hardware helpers remain in
[techrote/faikeow-now-reciever](https://github.com/techrote/faikeow-now-reciever)
at the qualified baseline documented here. Private firmware dumps, identifiers,
raw host inventory and credentials are excluded.

## Maintaining this reference

Run `python tools/check_docs.py` to validate local links, public evidence
hashes and JSON syntax. GitHub Actions runs the same check for pushes and pull
requests. Follow [AGENTS.md](AGENTS.md) when adding measurements: preserve the
original snapshot, identify the exact board/firmware/tool configuration, and
keep measured facts distinct from silicon capabilities and proposed projects.
