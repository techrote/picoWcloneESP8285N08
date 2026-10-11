# RP2040 and ESP8285 devboard programming reference

This reference is for people and coding agents developing firmware for the two
clone Pico W boards characterized in FNR-002 on 11 October 2026. It covers the
hardware available, which software belongs on each MCU, verified resources,
recovery, measured limits, and how to reuse the existing tooling. Use it with
the [operating runbook](DEVBOARD-OPERATING-RUNBOOK.md) for concrete commands.

**These boards contain RP2040 + ESP8285N08. They support Wi-Fi and ESP-NOW;
they have no onboard Bluetooth controller.** The host USB connection belongs
to RP2040. The two MCUs communicate through an existing onboard UART connection.
No external wiring is needed for that connection.

Quick navigation: [chip identity and Bluetooth](#2-chip-identity-and-the-bluetooth-distinction),
[pins and resources](#3-verified-architecture-and-resource-ownership),
[USB selection](#4-usb-identities-and-device-selection),
[firmware and tools](#5-firmware-lanes-and-build-selection),
[recovery](#6-recovery-and-preservation-contract),
[measured limits](#8-measured-performance-and-its-interpretation),
[future projects](#9-reuse-for-other-projects),
[agent context](#10-agent-operating-policy),
[evidence](#11-evidence-index-and-remaining-questions).

## 1. Authority and evidence

The accepted physical baseline is squash commit
`2777c90bfb13194feaeb6f7410c8029417af8da4`, from
[PR #17](https://github.com/techrote/faikeow-now-reciever/pull/17).
Reviewed source head was `455723b47d05ec2fa7597303766310d1471825f8`.
FNR-002 / [issue #3](https://github.com/techrote/faikeow-now-reciever/issues/3)
was accepted and closed after exact-head and post-merge CI passed all four jobs.
Those historical CI results do not qualify a subsequent firmware build.

Use these sources in this order for hardware decisions:

1. [BOARD-CONTRACT.md](BOARD-CONTRACT.md): accepted observations and procedures
   for these particular boards.
2. [FNR-002 test matrix](../evidence/FNR-002/test-matrix.md) and its linked JSON:
   scope, artifacts, results and limitations of each physical test.
3. This reference and the runbook: reusable interpretation and operating guidance.
4. Official chip documentation: silicon capabilities, not proof of PCB routing.
5. Similar-board projects: hypotheses requiring local verification.

This dedicated repository documents the hardware independently of any one
application. Its local `AGENTS.md` governs documentation work. Firmware paths,
FNR issue numbers and production architecture in this reference refer to the
[upstream receiver project](https://github.com/techrote/faikeow-now-reciever),
whose own `AGENTS.md`, `RAG.md` and programme docs govern changes to that project.
See [UPSTREAM-TOOLS.md](UPSTREAM-TOOLS.md) before using command examples. This
reference does not freeze that project's framing/envelope formats or imply
that an integrated receiver is complete.

Throughout this reference, **measured** means tested on these units;
**silicon capability** means specified for the chip; **proposed** means an
engineering option requiring implementation and acceptance. The board revision,
complete header routing and electrical measurements are not established.

## 2. Chip identity and the Bluetooth distinction

| Property | Board A | Board B | Basis |
|---|---|---|---|
| Main MCU | RP2040 B2 | RP2040 B2 | ROM identity |
| Main flash | 2 MiB external, JEDEC `68 40 15` | Same, independently measured | Observer and full reads |
| Main flash exact part | Unverified | Unverified | Do not assign a vendor part from capacity alone |
| Radio MCU | ESP8285N08 | ESP8285N08 | esptool ROM/efuse identity |
| Radio flash | 1 MiB embedded, JEDEC `5e 32 14` | Same, independently measured | Stub identity and full reads |
| Reported radio crystal | 26 MHz | 26 MHz | esptool measurement/report |
| Unique main flash ID | Privately recorded | Different, privately recorded | Target selection |
| Station MAC | Privately recorded | Different, privately recorded | Radio identity |
| Original main flash | All `ff` in the accepted 2 MiB backup | Pre-existing image with `picowutooth` metadata | Full matching backup pairs |
| Original radio image | Preserved | Preserved; differs from A | Full matching backup pairs |

The user reported visually identical boards bought in one order, with one board
previously used. Different original images are expected. Preserve them as
**pre-existing firmware**, without assuming factory provenance, intended
protocol, compatibility or successful boot.

ESP8285 belongs to the ESP8266 family and integrates flash in the package. Its
radio is 2.4 GHz 802.11 b/g/n Wi-Fi, without Bluetooth BR/EDR or Bluetooth LE.
Espressif lists ESP8285N08 under the ESP8266 series; see the
[official product catalogue](https://www.espressif.com/en/products/socs/esp3)
and [ESP8285 datasheet](https://documentation.espressif.com/0a-esp8285_datasheet_en.html).
References in that datasheet to Bluetooth interference coexistence or a clock
output for an external Bluetooth chip do not establish a Bluetooth controller.

RP2040 itself has no RF controller. A board sales name, `pico_w` build metadata,
or the string `picowutooth` does not establish the presence of a CYW43439 or
Bluetooth hardware. Firmware written for the genuine Pico W wireless chip is
not a drop-in radio driver for these units.

### What a future Bluetooth project would require

A Bluetooth project would need an **additional, identified Bluetooth controller**
with appropriate firmware and a verified electrical interface. Distinguish:

| Intended result | Additional requirements |
|---|---|
| Standard USB Bluetooth adapter for the PC | Bluetooth controller, USB HCI transport/descriptor implementation, controller startup/reset/flow control, host-stack compatibility tests |
| Bluetooth peripheral translated to USB HID | Bluetooth controller plus an embedded host/profile implementation; RP2040 translates events into its own USB HID profile |
| Application-specific Bluetooth serial bridge | Compatible Bluetooth module and its application protocol; USB CDC application on RP2040 |

The first option is more than a transparent USB CDC UART bridge. Bluetooth's
[USB HCI transport specification](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/host-controller-interface/usb-transport-layer.html)
defines host/controller packet transport and endpoint behavior. Merely changing
USB descriptors cannot add an RF controller. These are proposed projects;
none has been implemented or tested on these boards. Decide whether LE,
Classic or both are required before selecting additional hardware.

## 3. Verified architecture and resource ownership

```text
Remote ESP-NOW sender
        ~~~ 2.4 GHz Wi-Fi radio ~~~
                   ESP8285N08
                RX          TX
                 ^           |
                 |           v
            RP2040 GP0   RP2040 GP1
              UART0 TX     UART0 RX
                    RP2040
                       |
                 USB device
                       |
                      PC
```

This map is independently proven by ROM commands, complete radio flash reads,
and CRC/pattern-checked application traffic on both boards.

| Resource | Verified use | Programming consequence |
|---|---|---|
| RP2040 UART0 / GP0 | TX to radio RX | Reserve GP0 while using the onboard radio link |
| RP2040 UART0 / GP1 | RX from radio TX | Reserve GP1 while using the onboard radio link |
| RP2040 USB | BOOTSEL, CDC diagnostics and HID device applications | USB descriptors and functionality depend on the RP image |
| Near-USB button | RP2040 BOOTSEL when held during reconnection | Recovery survives an unusable RP application |
| Far-from-USB button | Radio ROM download entry when held during reconnection | Use the measured physical sequence |
| RP-controlled radio reset/download | Unknown | Do not invent GPIO assignments or drive candidate pins |
| RTS/CTS wiring | Unknown; unused | Tested UART configuration has no hardware flow control |
| Headers, LEDs, voltage/current | Not characterized | Verify routing before attaching peripherals or claiming measurements |

GP numbers are RP2040 GPIO numbers, not physical header pin numbers or ESP GPIO
numbers. Standard Pico header positions are not an accepted complete clone
pinout. ESP package signal names can be checked in its datasheet; package-to-PCB
header routing still requires separate evidence.

The chip provides other UART/SPI/I2C/PIO resources, but their availability on
this PCB is not established by UART qualification. Keep USB and radio ownership
explicit in a resource table for each new application. Avoid a serial console
on UART0 when UART0 carries radio protocol data.

### Minimal RP2040 UART initialization

The following is an illustrative Pico SDK initialization for the established
route. It is not a complete transport, buffering or recovery implementation.

```c
#include "pico/stdlib.h"
#include "hardware/uart.h"

static void radio_uart_init(void) {
    uart_init(uart0, 115200);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_hw_flow(uart0, false, false);
    gpio_set_function(0, GPIO_FUNC_UART);
    gpio_set_function(1, GPIO_FUNC_UART);
    gpio_set_drive_strength(0, GPIO_DRIVE_STRENGTH_2MA);
}
```

Link `hardware_uart`. Production receive buffering must service traffic while
USB is busy; a blocking UART/USB forwarding loop is insufficient. The tested
bridge uses an interrupt-driven 8,192-byte ring and foreground USB ownership.
See [its source](https://github.com/techrote/faikeow-now-reciever/blob/2777c90bfb13194feaeb6f7410c8029417af8da4/diagnostics/rp2040-candidate-bridge/main.c).

## 4. USB identities and device selection

| Mode | Observed VID:PID | Meaning |
|---|---|---|
| RP2040 ROM / RPI-RP2 | `2e8a:0003` | UF2 bootloader 3.0; ROM recovery |
| Source-built observer/bridge CDC | `2e8a:000a` | Diagnostic USB serial interface |
| Accepted development mouse firmware | `cafe:f003` | FNR-003 mouse-only USB HID |

Both boards expose the same BOOTSEL USB serial string. It is unsuitable as a
unique board selector. In picotool 2.2.0, `--ser` selects the **64-bit external
flash unique ID**, not that shared USB string. USB topology, physical board
label and MCU identity must agree before a write. COM numbers, mass-storage
drive letters, enumeration order and libusb addresses are transient.

Two-board RF fixtures use explicit RP USB serial labels `FNR002A` and `FNR002B`.
These make enumeration distinguishable; they do not replace topology and radio
MAC checks. A moved cable invalidates a location mapping. Re-identify the board
read-only and rebind the private map; do not bypass a guard to continue.

Windows required WinUSB on **RP2 Boot Interface 1**, USB ID `2e8a:0003`, `MI 01`,
for picotool access. The user installed it with Zadig 2.9. The mass-storage
interface remained USBSTOR and the composite parent retained its driver. Do not
repeat a driver installation unless access is actually missing, or replace
unrelated interfaces/controllers. Native hardware operations used Windows
PowerShell/Python, without substituting WSL or CI for USB access.

### Last recorded fixture state

At the end of the 11 October campaign, A was on mapped root port 3 / COM7 and B
on mapped root port 1 / COM6. Both had labeled flash-resident RP recovery bridges
and the same ESP RF diagnostic. The host stopped test transmissions and closed
serial handles. These are a **historical snapshot**, not current discovery or a
guarantee that radio behavior stays stopped after reset. Neither fixture was
then running the integrated USB receiver or HID application.

## 5. Firmware lanes and build selection

There are two independent firmware images. Flashing RP2040 does not update the
ESP radio, and flashing the ESP does not install a USB application on RP2040.

| Lane | Accepted tools | Target/configuration |
|---|---|---|
| RP2040 | Pico SDK 2.2.0, TinyUSB 0.18.0, Arm GNU 13.3.Rel1 / GCC 13.3.1 | `PICO_PLATFORM=rp2040`, `PICO_BOARD=pico`; select RAM or flash deliberately |
| ESP8285 | ESP8266 Arduino core 3.1.2, Xtensa GCC 10.3 | ESP8285 target, CPU 80 MHz, crystal 26 MHz, 1 MiB flash; qualified DOUT/40 MHz image header |
| Hardware host tools | Python 3.12.10, pyserial 3.5, esptool 4.8.1, picotool 2.2.0 | Native Windows USB/serial |
| Supplemental Windows builds | CMake 3.31.6, Ninja 1.11.1.4, Arduino CLI 1.5.1 | Provenance recorded in FNR-002 evidence |

The three ESP frequencies have different meanings: **80 MHz CPU**, **26 MHz
crystal**, and **40 MHz flash header**. Do not replace all three with one value.
`--chip esp8266` is the correct family selector for pinned esptool operations on
this ESP8285; it does not contradict the detected chip model.

Use the [upstream dependency lock](https://github.com/techrote/faikeow-now-reciever/blob/2777c90bfb13194feaeb6f7410c8029417af8da4/dependencies.lock.json) for exact source pins
and artifact digests. The locked Linux acquisition/build lane and supplemental
Windows host tools are distinct. The hardware campaign did not silently replace
the dependency lock. See [05-BUILDING.md](https://github.com/techrote/faikeow-now-reciever/blob/2777c90bfb13194feaeb6f7410c8029417af8da4/docs/05-BUILDING.md) for production builds
and [the runbook](DEVBOARD-OPERATING-RUNBOOK.md) for diagnostic commands.

### Existing production software

- `firmware/rp2040/`: FNR-003 TinyUSB integration and selected HID profile.
- `firmware/esp8266/`: FNR-004 profile-neutral ESP-NOW ingress, default
  unprovisioned/fail-closed; no production internal forwarding.
- `shared/`: portable bounded datagram/HID logic and profiles.
- FNR-005/006/007 own production framing, receiver envelope/core and provisioning.
  At the accepted hardware baseline, the complete receiver was not implemented.

Choose `PICO_BOARD=pico` to avoid selecting an unsupported CYW43 radio stack.
That build selection is not a claim that every physical Pico header connection
is identical. MicroPython or other frameworks are possible separate ports,
but the characterization does not qualify their radio drivers, flash layouts
or binary compatibility. Do not load an arbitrary `PICO_W` image based on name.

### Existing isolated diagnostics

| Source | Placement | Purpose |
|---|---|---|
| `diagnostics/rp2040-observer` | RP SRAM | Input-only GPIO observer, JEDEC/flash UID discovery; zero GPIO outputs |
| `diagnostics/rp2040-candidate-bridge` | RP SRAM by default | Transparent CDC-to-UART0 radio ROM/application access |
| Same bridge with explicit A/B label and flash flag | RP flash | Persistent, distinguishable recovery fixtures |
| `diagnostics/rp2040-link` | RP SRAM | UART generator/checker and JSON observation |
| `diagnostics/esp-link/esp_link` | ESP flash | UART echo/independent-stream diagnostic, Wi-Fi disabled |
| `diagnostics/esp-rf/esp_rf` | ESP flash | Temporary ESP-NOW sender/receiver exercising the existing ingress adapter |

Diagnostics are not production framing or a finished receiver. The link
diagnostic uses SLIP + reflected CRC-32/ISO-HDLC. Production FNR-005's preferred
COBS + CRC-16/CCITT design remains separate. An `INFO`, `RUN600` or `BOOTSEL`
command is meaningful only to the image that implements it; the transparent
bridge forwards ordinary bytes to the radio and does not interpret those text
commands. Its **1200-baud CDC request** separately returns RP2040 to ROM.

## 6. Recovery and preservation contract

For either board, two matching full main-flash reads contain **2,097,152 bytes**;
two matching full radio reads contain **1,048,576 bytes**. SHA-256, chip identity,
source/tool provenance and full readback records accompany them. Raw firmware,
MACs, flash UIDs and host inventory stay in the private local evidence directory
outside Git. Public evidence carries curated results and capture digests.

RP flash maps at `0x10000000..0x10200000` (end exclusive). The first A exploration
read a larger XIP address window; that did not establish a larger physical chip.
Blank A required an explicit-capacity range because `picotool save -a` could not
infer an application extent. B's nonblank image supported `save -a`.

Recovery sequences verified on these units:

1. **RP ROM:** unplug the selected board; hold the near-USB BOOTSEL button;
   reconnect; release. Expect RPI-RP2, then re-identify the target.
2. **Radio ROM with a persistent bridge:** unplug; hold the far button;
   reconnect; release. The bridge returns from RP flash while the radio is in
   download mode. Confirm identity with the guarded host tool.
3. **Radio ROM when the RP application offers no USB:** unplug; hold both
   buttons; reconnect; release both. Expect RP BOOTSEL and radio download mode;
   load the reviewed SRAM bridge. This rescued access with B's pre-existing RP
   application, without replacing it first.
4. **Ordinary cold boot:** unplug/reconnect without buttons. Which USB device
   appears depends on RP flash. Do not expect a blank-board behavior from B.

A successful software reboot is not cold-boot evidence. `user-confirmed-cold`
in a probe must correspond to an actual user-confirmed power reconnection.
Pressing the far button while already powered did not establish a reset route.
Application reset commands do not establish ROM entry or an RP reset GPIO.

Both MCUs on both boards were restored from their own original images with
complete byte-for-byte readback. Original radio application behavior remains
unknown: AT probes were silent, and AT was not established as its protocol.
That is not evidence of a damaged radio or an acceptance gate. Do not repeat
original-firmware investigations without a task that needs their behavior.

### Write discipline

- Prefer SRAM for temporary RP diagnostics. SRAM execution disappears after
  power loss; explicitly selected flash builds persist.
- Verify measured capacity, target identity, complete backup pair and image
  hash before a persistent write. Review image source/layout and recovery.
- Use the guarded helpers; a generic file copy or esptool write lacks their
  target/backup checks. Do not issue a separate mass erase.
- Radio writes affect occupied flash sectors, with sector erase granularity;
  partial application writes are not full-image restoration. Preserve the
  entire original image before changing application/configuration regions.
- Exact readback proves bytes, not a successful application boot. Record both.
- Keep the other board available as a reference until the selected board's
  recovery is proven. Do not overwrite both originals simultaneously.

The existing radio helper accepts reviewed ESP8266-format diagnostic images
with a valid checksum and DOUT / 1 MiB / 40 MHz header. Restore mode requires
the exact complete original image and preserves its header. It is not a generic
installer for arbitrary offset/partition schemes. Extend a tool deliberately
and review it if a future framework needs another layout.

## 7. USB and serial implementation lessons

The functioning bridge forwards raw binary data, without inserting logs into
the UART stream. UART interrupt input and USB foreground output have bounded
buffers and explicit error/drop counters. It consumes UART ring bytes only
after TinyUSB accepts them. Earlier polling and incorrect forwarding lost data
during flash-read responses, despite working for small identity transactions.

Pico USB stdio normally gates connection on DTR; the diagnostic disables that
gate. TinyUSB 0.18's CDC TX FIFO can nevertheless be overwritable with DTR
deasserted. esptool 4.8.1 normally opens with DTR/RTS false. The qualified radio
helpers keep **DTR true through an already-open serial object** and retain
binary data until accepted. Disabling the stdio gate alone was insufficient.

On this bridge, DTR/RTS have no electrical reset/download effect on the radio.
Do not rely on automatic-reset wiring used by other ESP devboards. Use pinned
esptool `no_reset` behavior and the measured physical ROM sequence. USB BREAK
requests a bridge counter line rather than driving a UART break; use it only
between transactions because the response shares the CDC byte stream.

An interrupted stub transaction can leave the radio's RAM stub awaiting an
acknowledgement. Restart radio ROM and reconnect cleanly before retrying. Keep
failed dumps as failed evidence and exclude them from restoration inputs. A
second failure arose when esptool tried to upload an already resident stub;
the corrected integration confirms stub SYNC before writing. The pinned
integration regression exercises that object path without attached hardware.

## 8. Measured performance and its interpretation

### Board-internal UART

Both boards independently ran 600 active seconds plus two seconds of drain:

| Metric per board | Result |
|---|---|
| RP requests / matching echoes | 11,998 / 11,998 |
| Independent radio stream frames | 12,039 including drain |
| Payload sizes | Cycling 1 / 32 / 128 / 250 bytes |
| Unexplained CRC, pattern, sequence, UART, ring errors/drops | Zero |
| Counter agreement | RP and radio counters matched |
| Active request payload load | Approximately 2,054 B/s RP to radio |
| Echo + stream receive payload load | Approximately 4,102 B/s including drain |

Each board also passed contiguous bursts, deliberate CRC damage/truncation/
bounded overflow and resynchronization, radio application restart, RP ROM/SRAM
restart while radio streaming, and clean post-reset recovery bursts. Intentional
reset losses are separate from clean-run integrity.

115200 8N1 has a calculated ceiling of **11,520 serial bytes/s in each
direction** (ten wire bits per byte), before framing and software overhead.
This is arithmetic, not a measured sustained application maximum. For example,
250 payload bytes at 50 packets/s is already 12,500 payload bytes/s, exceeding
that ceiling before metadata/escaping. Choose production cadence, packet size,
framing and bounded drop/coalescing policy together. Higher UART rates were not
qualified; the bridge's accepted baud-setting range is not a reliability test.

### ESP-NOW RF

The two-direction campaign passed 19 of 20 cases: 1/32/128/250-byte integrity,
500-packet bursts, exact-peer handling, bounded backpressure, adapter restart,
and 6,000 packets of 250 bytes at configured 20 ms spacing in each direction.
Normal same-channel runs checked all payloads without unexplained corruption,
loss or duplicate frames. Intentional receiver pauses produced 256 and 274
accounted drops in the two directions.

**Software-reported channel isolation is not accepted.** A-to-B wrong-channel
testing received zero packets, but B-to-A received 6/100 valid packets with
reported A=1/B=6; a focused repetition received 78/1,000 while sampled SDK
channels remained 1/6 and transmit callbacks reported failure. The later
[distance/power follow-up](RF-CHANNEL-BEHAVIOR.md) reproduced mismatch reception,
including residual packets at low requested power and at 180 cm. It resolves
the programming contract: SDK channel selection is not per-packet exclusion.
The precise RF mechanism remains unmeasured; every negative failure is retained.
Do not infer the actual over-the-air channel solely from an SDK channel query,
or equate a transmit callback with application-level delivery acknowledgement.

The fixture did not deliberately join an infrastructure network or configure
credentials. Bench distance, RF environment and per-packet latency were not
instrumented. No range, maximum throughput, latency, encryption, isolation or
production security guarantee follows from these results. Keep the total
ESP-NOW application datagram within the repository's **250-byte** interoperability
limit, including any platform envelope.

### USB HID

Both boards passed accepted-image readback, Windows mouse enumeration and
cold re-enumeration. Parsed usage was page 1 / usage 2, one button capability
range and two axis value capabilities, without output/feature reports. Windows
reported a four-byte input buffer including its report-ID prefix; the on-wire
FNR-003 report is three bytes without a report ID. Do not insert a fourth byte
into USB firmware merely to match the Windows API buffer length.

B additionally passed raw device/configuration descriptor capture and a
20-second target-only Raw Input idle observation without motion, removal or
errors. The Windows hub API could not retrieve an interface-recipient HID report
descriptor. `HidD_GetInputReport` failed with Windows error 1 on both; no neutral
report was observed and the cause was not isolated. Active axes/buttons,
fail-safe neutral behavior and suspend/resume still require physical acceptance.
Native HID tests and descriptor source are separate software evidence.

## 9. Reuse for other projects

| Project | Hardware basis | Additional work |
|---|---|---|
| ESP-NOW to USB HID receiver | RF, onboard UART and USB enumeration proven | Production framing/core/provisioning, profile behavior, complete physical acceptance |
| ESP-NOW telemetry to USB CDC | RF + UART + CDC bridge proven separately | Versioned application protocol, bounded queues, host software and integrated tests |
| Wi-Fi application with USB control/logging | ESP silicon Wi-Fi capability + existing UART/USB route | Explicitly owned Wi-Fi firmware, credentials/configuration policy, integrated validation |
| RP2040 USB peripheral or protocol adapter | RP silicon USB/PIO resources; mouse subset measured | Suitable backend, verified external pin use and project-specific tests |
| GPIO/sensor/control application | Two programmable MCUs | Verify each chosen header/net and electrical requirements |
| Bluetooth dongle or peripheral | No onboard Bluetooth controller | Additional hardware and a separately scoped implementation |

These are feasibility directions, not claims that corresponding firmware ships.
The present repository keeps radio ingress and internal framing profile-neutral.
For a new mouse/keyboard/gamepad backend, preserve those boundaries and put HID
payload semantics and neutralization in the profile. Infrastructure Wi-Fi and
other applications belong in explicitly owned later work or a separate project.

## 10. Agent operating policy

At the beginning of a programming session:

1. Read the working firmware repository's `AGENTS.md` and task authority, this reference, the contract and
   the relevant runbook section. Identify the task's owning issue/scope.
2. Inspect Git state and current USB state read-only. Load the private identity
   map if available. Treat historical port numbers as hints only.
3. Determine installed firmware from device/application identity, not just a
   familiar VID/PID. Record which MCU and which memory domain will change.
4. Reuse prior accepted evidence for unchanged hardware and exact artifacts.
   Run a short task-relevant smoke check after deployment; repeat a long soak
   only when the change or a failure warrants it.
5. Before persistent writes, verify recovery and the correct board's preserved
   backup pair. Missing original backups block preservation-sensitive writes;
   do safe preparation while resolving that specific dependency.
6. Ask for one concrete physical operation only when software cannot perform
   it. Identify the board, button, cable action and expected observation.
7. Record exact source, dirty state, tool/image hashes, live identity and result.
   A cold-boot label requires actual cold-boot confirmation.
8. Stop test traffic, close handles and write an accurate final fixture-state
   handoff. A handoff describes reality; it is not an instruction to reflash.

Do not repeat the entire preservation/restoration campaign merely because an
old image is different or silent. Do not request a multimeter measurement for
the already-proven onboard UART. Electrical discovery is needed only when a
new task actually depends on an unknown net, header function or voltage.

### Reusable task context

```text
Target: the characterized RP2040 B2 + ESP8285N08 clone boards, not CYW43 Pico W.
Read the firmware repository instructions and task authority, then this repo's
docs/BOARD-CONTRACT.md,
docs/DEVBOARD-PROGRAMMING-REFERENCE.md and docs/DEVBOARD-OPERATING-RUNBOOK.md.
UART0 GP0 TX -> ESP RX, GP1 RX <- ESP TX is independently proven at 115200 8N1.
No onboard Bluetooth. Radio reset/download GPIO mapping is unknown.
Use fresh topology plus private RP flash UID / radio MAC for target selection.
Preserve full original pairs; use guarded RAM/flash helpers and exact readback.
Reuse existing evidence; perform only checks relevant to this task's changes.
Keep diagnostics distinct from production and report remaining physical gates.
```

## 11. Evidence index and remaining questions

| Evidence | Contents |
|---|---|
| [board-inventory.json](../evidence/FNR-002/board-inventory.json) | Per-board identity and host observations |
| [radio-identification.json](../evidence/FNR-002/radio-identification.json) | ROM/model/flash identification and original-app limitations |
| [interconnect-verification.json](../evidence/FNR-002/interconnect-verification.json) | GPIO routing and unsupported controls |
| [flash-recovery.json](../evidence/FNR-002/flash-recovery.json) | Independent deployment/restoration and readbacks |
| [link-integrity.json](../evidence/FNR-002/link-integrity.json) | UART counters, timings and fault recovery |
| [usb-enumeration.json](../evidence/FNR-002/usb-enumeration.json) | Windows USB/HID observations and limitations |
| [rf-preparation.json](../evidence/FNR-002/rf-preparation.json) | RF deployment/identity |
| [rf-integrity.json](../evidence/FNR-002/rf-integrity.json) | Original RF campaign, including failure |
| [rf-channel-anomaly.json](../evidence/FNR-002/rf-channel-anomaly.json) | Focused reproduction |
| [rf-completion.json](../evidence/FNR-002/rf-completion.json) | Two remaining cases, preserved separately |
| [diagnostic-builds.json](../evidence/FNR-002/diagnostic-builds.json) | Source/artifact hashes and build provenance |
| [raw-log-index.json](../evidence/FNR-002/raw-log-index.json) | Digests of private raw capture snapshots |
| [SHA256SUMS](../evidence/FNR-002/SHA256SUMS) | Public evidence integrity manifest |

Remaining questions are bounded: board revision/markings, complete header and
reset/download routing, measured electrical/current behavior, higher UART rates
if needed, the precise RF mechanism, complete USB/profile lifecycle, integrated receiver
and reference sender acceptance. FNR-002's established identity/recovery/UART
contract remains accepted. None of those open questions adds onboard Bluetooth.

## 12. Official references

- [Espressif ESP8285 datasheet](https://documentation.espressif.com/0a-esp8285_datasheet_en.html)
  and [SoC catalogue](https://www.espressif.com/en/products/socs/esp3): chip family
  and silicon capabilities.
- [Raspberry Pi RP2040 documentation](https://www.raspberrypi.com/documentation/microcontrollers/microcontroller-chips.html#rp2040):
  silicon resources; not a clone PCB schematic.
- [Pico SDK 2.2.0](https://github.com/raspberrypi/pico-sdk/tree/2.2.0): RP build API.
- [ESP8266 Arduino 3.1.2](https://github.com/esp8266/Arduino/tree/3.1.2): radio build API.
- [esptool 4.8.1](https://github.com/espressif/esptool/tree/v4.8.1): pinned host implementation.
- [picotool 2.2.0](https://github.com/raspberrypi/picotool/tree/2.2.0): RP ROM tooling.
- [Bluetooth HCI USB transport](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/host-controller-interface/usb-transport-layer.html):
  requirements for a separately implemented Bluetooth controller adapter.
