# ESP-NOW channel-mismatch reception on characterized A/B units

## Measured conclusion

On 11 October 2026, the two characterized ESP8285N08 boards delivered valid
ESP-NOW payloads despite different software-reported channels. The effect
varied substantially with user-reported separation and requested SDK power
ceiling. **Channel selection is not a reliable packet-exclusion or security
boundary on these fixtures.** Lower power and greater separation did not
eliminate every mismatch reception.

The investigation resolves the practical programming contract and interpretation
of the earlier anomaly. It does not establish physical over-the-air frequency
or a precise RF circuit/SDK mechanism. Strong-signal/finite-selectivity effects
are a plausible explanation, not an instrumented root-cause diagnosis. A
failed transmit callback is not proof that no receiver received the packet.

## Evidence and reproducibility

The receiver project owns the diagnostic/helper source and application acceptance.
Its frozen [follow-up ledger](https://github.com/techrote/faikeow-now-reciever/blob/f202cb56474791cee2bb70a74a25df4949d5b3f1/evidence/FNR-004/README.md),
[all 58 cases](https://github.com/techrote/faikeow-now-reciever/blob/f202cb56474791cee2bb70a74a25df4949d5b3f1/evidence/FNR-004/channel-comparisons.json),
[provenance](https://github.com/techrote/faikeow-now-reciever/blob/f202cb56474791cee2bb70a74a25df4949d5b3f1/evidence/FNR-004/provenance.json)
and [manifest](https://github.com/techrote/faikeow-now-reciever/blob/f202cb56474791cee2bb70a74a25df4949d5b3f1/evidence/FNR-004/SHA256SUMS)
retain every failed negative case and digests of private captures. The original
[FNR-002 anomaly](../evidence/FNR-002/rf-channel-anomaly.json) is unchanged.

Hardware reference used: `8d48cdde71ccba824436635858265cb31c4ed88f` in this
repository. Host was native Windows 11 Pro, with fresh labeled USB/topology and
live radio-MAC guards. Accepted original backup pairs, recovery, wiring and
UART integrity evidence were reused. No multimeter, new RP firmware write,
original-firmware investigation or repeated ten-minute UART test was needed.

| Experiment | Result |
|---|---|
| Original image, 20 cm, bidirectional channel 1/6/11 matrix | Ten of twelve mismatch cases received packets; all eight 300-packet same-channel controls passed |
| Same image, 180 cm, same matrix | Two mismatch cases received 5/300 and 6/300; other ten received zero; all eight same-channel controls passed |
| Same image, 180 cm, focused RX1/TX6 | Zero of 1,000 in each direction; both 100-packet source-rejection controls passed |
| New power-capable image, fixed 20 cm, B-to-A RX1/TX6, high/low/high | Accepted 36/300, 2/1,000, 12/300 at requested ceilings 82/0/82 quarter dBm |
| Low-power reverse A-to-B RX1/TX6 | Zero of 1,000 received |

All four power-experiment same-channel burst controls checked 500/500 payloads;
all four unexpected-source controls rejected 100/100. Active-case SDK samples
reported station mode, disconnected station status and disabled auto-connect/
auto-reconnect. This does not constitute a continuous RF or scan-state trace.

Distance matrices used original RF diagnostic SHA-256
`83e67685b82f4f2a5b90cb6356ff26377ab4ca67656893c4853ce976b2f1c3c3`,
source `81de11045e729f5bf194074c042e1b31d6f1eee1`.
Power-capable image source is `5f9f5e7c312c746df4ed138ddf7a9514131432c9`, clean
at build, SHA-256
`aa68778ae10238417c92739f506f09c93a796ee1e61ad0f2fd60e7d6d6bd084d`
(285264 bytes). Both radios passed exact readback and software-boot identity.
The new image was not separately cold-boot qualified. Build used Arduino CLI
1.5.1, ESP8266 core 3.1.2/NONOS 22x_190703, Xtensa GCC 10.3, CPU 80 MHz,
reported 26 MHz crystal, DOUT/1 MiB/40 MHz flash; Python 3.12.10, esptool 4.8.1
and pyserial 3.5. Exact tool/driver hashes are in the provenance ledger.

Distances were operator reported, not instrumented. The requested power ceiling
was applied to both radios; 82 means 20.5 dBm and zero means 0 dBm at the API.
Neither radiated power nor actual physical channel/RSSI/spectrum was measured.
The small sequential samples are not a calibrated threshold, statistical range
specification or maximum-performance measurement. Residual reception means the
low-power negative test and the full 180 cm matrix remain FAIL.

## Guidance for future firmware agents

- Configure and verify the SDK channel, but do not equate that value with
  per-datagram physical-channel admission. The pinned NONOS callback exposes
  source MAC, bytes and length, without packet-channel metadata.
- Enforce explicit bounded source/length/application policy. Exact MAC matching
  is not cryptographic authentication. Security requirements need an explicitly
  designed and validated cryptographic policy in the application.
- For channel-negative testing, record geometry, requested power, channels,
  exact artifacts and receiver counters. Include same-channel integrity and
  unexpected-source controls so silent/dead reception cannot look like a pass.
- Any valid mismatch reception remains a negative-test failure, even when all
  send callbacks fail. Preserve successful send callbacks too; do not infer
  application acceptance from their status alone.
- Do not promise isolation by reducing power, separating boards or changing
  channels. Reuse this evidence when the hardware/artifact assumptions apply;
  further physical mechanism work requires a specifically scoped experiment
  and suitable RF measurement equipment.

At the end of this campaign both boards remained connected with the unchanged
labeled RP bridges and the new RF diagnostic. A final identity-guarded OFF check
confirmed Wi-Fi OFF, RX/TX inactive, no outstanding packet and closed serial
handles. Their last requested ceiling was 82. See the frozen
[final fixture record](https://github.com/techrote/faikeow-now-reciever/blob/f202cb56474791cee2bb70a74a25df4949d5b3f1/evidence/FNR-004/final-state.json).
Future sessions must discover current state again; this is a historical handoff.
