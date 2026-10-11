# Characterization evidence and provenance

## Origin and scope

The measurements originated in the FNR-002 dual-board hardware campaign in
[techrote/faikeow-now-reciever](https://github.com/techrote/faikeow-now-reciever),
on 11 October 2026 using native Windows 11 Pro USB/serial access. Two units,
physically designated A and B, were independently identified, preserved,
programmed, recovered and UART-qualified.

Accepted upstream commit:
`2777c90bfb13194feaeb6f7410c8029417af8da4`.
The reviewed pre-squash source tree was
`455723b47d05ec2fa7597303766310d1471825f8`.
See [PR #17](https://github.com/techrote/faikeow-now-reciever/pull/17) and
[issue #3](https://github.com/techrote/faikeow-now-reciever/issues/3) for the
accepted hardware record.

This repository adds application-independent reference prose and agent/runbook
guidance. The programming reference and runbook were prepared from that accepted
campaign after merge; they are documentation adaptations, not newly measured
hardware or newly qualified firmware. No device operations were performed to
populate this repository.

## Immutable public snapshot

Every file in `evidence/FNR-002/` was copied directly from the accepted upstream
Git blobs, preserving bytes and the original `SHA256SUMS`. The validator checks
the manifest's own pinned digest, all manifest entries and JSON syntax. The
manifest SHA-256 is
`03b9dfe7e2e48571ee04673c96e545d2085a859ba05ffd9dc3b3a091060f938b`.
The evidence README and matrix retain
their historical acceptance wording. Unqualified references to FNR issue
numbers in those files refer to the upstream receiver project, not issues in
this dedicated repository.

| Evidence group | Local record |
|---|---|
| Per-board inventory | [board-inventory.json](../evidence/FNR-002/board-inventory.json) |
| Radio ROM/flash identity | [radio-identification.json](../evidence/FNR-002/radio-identification.json) |
| Onboard wiring | [interconnect-verification.json](../evidence/FNR-002/interconnect-verification.json) |
| Flashing/restoration | [flash-recovery.json](../evidence/FNR-002/flash-recovery.json) |
| UART integrity and faults | [link-integrity.json](../evidence/FNR-002/link-integrity.json) |
| USB subset | [usb-enumeration.json](../evidence/FNR-002/usb-enumeration.json) |
| RF deployment | [rf-preparation.json](../evidence/FNR-002/rf-preparation.json) |
| Original RF campaign | [rf-integrity.json](../evidence/FNR-002/rf-integrity.json) |
| Retained RF anomaly | [rf-channel-anomaly.json](../evidence/FNR-002/rf-channel-anomaly.json) |
| Remaining RF cases | [rf-completion.json](../evidence/FNR-002/rf-completion.json) |
| Build provenance | [diagnostic-builds.json](../evidence/FNR-002/diagnostic-builds.json) |
| Private capture digests | [raw-log-index.json](../evidence/FNR-002/raw-log-index.json) |
| Per-case result | [test-matrix.md](../evidence/FNR-002/test-matrix.md) |

## Acceptance boundaries

FNR-002's hardware identity, UART0 GP0/GP1 route, physical recovery, reversible
deployment/restoration, diagnostic cold boot and ten-minute UART integrity/fault
recovery passed independently on both boards.

Additional RF testing passed 19/20 cases. Reverse software-channel isolation
failed and reproduced. Additional USB testing proved enumeration/cold
re-enumeration on both and descriptor/idle subsets on B, with incomplete neutral,
active and lifecycle observations. These results do not accept a complete
wireless USB receiver, reference TiltMouse interoperability, maximum bandwidth,
latency, RF range or a Bluetooth feature.

The boards' original firmware differed; one had previously been used. Full
original bytes were preserved/restored, but the original radio application's
protocol/function and factory provenance remain unknown. Silent AT probes do
not establish a defect or require repeated restoration experiments.

## Later RF follow-up

The subsequent [RF channel investigation](RF-CHANNEL-BEHAVIOR.md) links a frozen
receiver-side FNR-004 ledger with all 58 cases, image/tool/driver hashes and
private capture digests. It adds measured distance/power sensitivity and a
channel-selection limitation without rewriting this repository's immutable
FNR-002 snapshot. Receiver-specific implementation and acceptance remain upstream.

## Private data

Full original RP/radio dumps, raw captures, complete host paths, flash UIDs,
radio MACs and credentials are excluded from this repository. Public ledgers
use curated fields and hashed identifiers. Raw-log digests identify private
capture snapshots without publishing their contents. A checksum is an integrity
identifier; it does not make the underlying private file publicly available.

## Adding later evidence

Preserve this snapshot unchanged. Add new campaigns in separate directories
with date, board designation/revision, host, exact source/tool/image identities,
commands/configuration, raw-capture digests and explicit per-case outcomes.
Update the reference where new evidence changes a practical conclusion, linking
the new record and retaining the earlier result's date and scope. A different
board revision requires its own verification; do not generalize from a shared
sales description.
