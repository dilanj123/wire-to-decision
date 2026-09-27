# WIRE-002 — External Protocol Specification Lock

Status: PASS — specification/source evidence only. No implementation was performed.

## A. Sources retrieved

All listed sources were inspected during this task. RFC artifacts were read from RFC Editor representations; Nasdaq PDFs were downloaded temporarily, inspected, hashed, and deleted.

| Source | Canonical location | Role |
|---|---|---|
| RFC 894 | https://www.rfc-editor.org/rfc/rfc894.txt | IPv4-over-Ethernet II encapsulation |
| RFC 791 | https://www.rfc-editor.org/rfc/rfc791.txt | IPv4 header and fragmentation semantics |
| RFC 768 | https://www.rfc-editor.org/rfc/rfc768.html | UDP format and checksum semantics |
| MoldUDP64 | https://nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/moldudp64.pdf | Nasdaq downstream packetization and sequencing |
| TotalView-ITCH 5.0 | Current asset linked by Nasdaq Trader DTN2025-22 | ITCH encoding and displayed-book semantics |

The Wire-to-Decision repository was verified at branch `main`, starting HEAD `2417ae8f338e6ee2c4df88be62b927c7f5a95bac`, with a clean working tree. No reference repository was modified.

## B. Source fingerprints

Exact hashes and retrieval metadata are in `docs/SPEC_SOURCES.md` and `results/raw/spec_sources/`. Retrieval time was 2026-09-27T11:42:10Z.

## C. Source metadata discrepancies

The live Nasdaq notice DTN2025-22 links the current ITCH artifact and identifies a 2025 update. The linked PDF itself declares Version 5.0 and contains a 2025-06-16 revision entry for an additional listing-market value `M`. Therefore no unresolved website/PDF revision-date discrepancy remains for the current linked artifact. An older classic Nasdaq URL serves an older representation whose revision log stops in 2023; it was not used as the authoritative current artifact. The MoldUDP64 PDF declares V 1.00 and its Version Control table ends with an 2024-08-02 formatting entry.

## D. Ethernet II / IPv4-over-Ethernet facts

- SOURCE-DERIVED: RFC 894 identifies Ethernet type `0x0800` for IPv4 datagrams and places the IP header/data in the Ethernet data field.
- SOURCE-DERIVED: RFC 894's verified errata correct the data-field wording to a maximum of 1500 octets.
- PROJECT RESTRICTION: the MVP accepts Ethernet II with IPv4 EtherType only and does not support VLAN-tagged frames.
- PROJECT RESTRICTION: the mandatory processing boundary remains after MAC/PHY concerns; preamble, SFD, FCS, PHY handling, and MAC implementation are out of scope.

The no-VLAN decision is a Wire-to-Decision scope restriction, not a claim that Ethernet generally lacks VLANs.

## E. IPv4 facts and MVP restrictions

- SOURCE-DERIVED: Version 4 identifies IPv4; IHL is measured in 32-bit words and a valid minimum header value is 5.
- PROJECT RESTRICTION: accept `Version=4` and `IHL=5` only, therefore no IPv4 options and no options-dependent parsing.
- SOURCE-DERIVED: Total Length includes header and data and is measured in octets.
- PROJECT VALIDATION RULE: reject a datagram if Total Length is smaller than the header, exceeds the available datagram bytes, or is otherwise inconsistent with the received frame boundary.
- SOURCE-DERIVED: Protocol value 17 identifies UDP.
- SOURCE-DERIVED: the header checksum verifies the IPv4 header.
- PROJECT VALIDATION RULE: the IPv4 header checksum must validate before downstream state mutation.
- SOURCE-DERIVED: a non-fragmented datagram has `MF=0` and `Fragment Offset=0`; offset units are 8-octet blocks.
- PROJECT VALIDATION RULE: accept only `(MF == 0) AND (Fragment Offset == 0)`. The DF bit is not required to be set for this classification.
- PROJECT RESTRICTION: reject fragmented datagrams; do not implement reassembly.
- PROJECT RESTRICTION: destination IPv4 address is configurable/filterable.

## F. UDP facts and MVP restrictions

- SOURCE-DERIVED: UDP protocol number is 17; the UDP header is at least 8 octets; UDP Length includes header and payload.
- PROJECT VALIDATION RULE: validate UDP Length is at least 8, is consistent with the IPv4 payload, and does not exceed available bytes.
- PROJECT RESTRICTION: destination port is configurable/filterable.
- SOURCE-DERIVED: for IPv4, a transmitted UDP checksum of zero means the transmitter generated no checksum; a nonzero checksum has UDP checksum semantics over the pseudo-header, UDP header, and data.
- PROJECT RESTRICTION: accept checksum zero; reject nonzero checksums before ITCH state mutation. This is not a claim that RFC 768 requires zero checksums; it is a deliberate initial-parser restriction to avoid a whole-datagram checksum dependency.

## G. MoldUDP64 format and sequencing

- SOURCE-DERIVED: all Mold sequence, count, and length fields are big-endian; message data content has its own protocol interpretation.
- SOURCE-DERIVED: the downstream header is 20 octets: Session offset 0 length 10; Sequence Number offset 10 length 8; Message Count offset 18 length 2.
- SOURCE-DERIVED: the sequence number is the sequence of the first message in the packet; messages following it are implicitly sequential.
- SOURCE-DERIVED: each message block begins with a 2-octet Message Length. The value counts message-data octets and excludes the length field, so block size is `2 + Message Length`.
- SOURCE-DERIVED: Message Count zero is a heartbeat; `0xFFFF` is end of session. These packets carry the next expected sequence number.
- SOURCE-DERIVED: the protocol defines Request Packets to a re-request server for sequence gaps; a response is a standard downstream packet.
- PROJECT RESTRICTION: on session or sequence discontinuity, invalidate/fail closed, suppress decisions, and require external recovery/re-arm. The MVP does not generate Request Packets, implement re-request interaction, or implement GLIMPSE recovery.

## H. ITCH common data representation

- SOURCE-DERIVED: integer fields are big-endian unless explicitly noted; alpha fields are ASCII and padded as specified.
- SOURCE-DERIVED: Stock Locate is 2 octets at the common message offset 1 and is dynamically assigned daily; it does not change intraday, but should not be assumed stable across trading days. Stock Directory communicates the assignment.
- SOURCE-DERIVED: Tracking Number is 2 octets at offset 3; Timestamp is 6 octets at offset 5 and is nanoseconds since midnight.
- SOURCE-DERIVED: Order Reference Number is 8 octets; Shares quantity is 4 octets; Buy/Sell is one octet; Price (4) is a four-octet integer with four implied decimal places.
- PROJECT RESTRICTION: track one configured Stock Locate at a time and ignore other locate values for state mutation. No Stock Directory subsystem is added to this MVP.

## I. Supported ITCH mutation-message table

Lengths and offsets are from the current official TotalView-ITCH 5.0 artifact, not from implementation or third-party libraries.

| Type | Message | Total length | Fields (offset: width) | MVP state effect |
|---|---|---:|---|---|
| A | Add Order — No MPID Attribution | 36 | Locate 1:2; Tracking 3:2; Timestamp 5:6; Order Ref 11:8; Buy/Sell 19:1; Shares 20:4; Stock 24:8; Price 32:4 | Add displayed order |
| F | Add Order with MPID Attribution | 40 | A fields plus Attribution 36:4 | Add displayed order; attribution need not be retained |
| E | Order Executed | 31 | Locate 1:2; Tracking 3:2; Timestamp 5:6; Order Ref 11:8; Executed Shares 19:4; Match Number 23:8 | Reduce displayed quantity |
| C | Order Executed With Price | 36 | E fields plus Printable 31:1; Execution Price 32:4 | Reduce displayed quantity; execution price is additional trade information |
| X | Order Cancel | 23 | Locate 1:2; Tracking 3:2; Timestamp 5:6; Order Ref 11:8; Cancelled Shares 19:4 | Reduce displayed quantity |
| D | Order Delete | 19 | Locate 1:2; Tracking 3:2; Timestamp 5:6; Order Ref 11:8 | Remove displayed order |
| U | Order Replace | 35 | Locate 1:2; Tracking 3:2; Timestamp 5:6; Original Ref 11:8; New Ref 19:8; Shares 27:4; Price 31:4 | Replace original with new reference, quantity, and price; side/stock/attribution inherited |

A and F are both displayable-book additions; F's MPID attribution is not required by the proposed bounded state. E and C are both executions reducing resting displayed quantity. C's execution price is not to be conflated with the stored display price. U supplies a new reference, shares, and price; source semantics retain side, stock, and attribution from the original.

Trade Message P is 44 octets in the current artifact and represents a non-displayable match. SOURCE-DERIVED: Nasdaq states it does not affect the book and may be ignored by firms tracking the Nasdaq execution-system display. PROJECT VALIDATION RULE: P does not mutate the tracked displayed-order state; it remains a legitimate ITCH message outside this subset.

## J. Explicit unsupported protocol features

PROJECT RESTRICTION: VLAN, IPv6, IPv4 options, fragmented datagrams/reassembly, nonzero UDP checksum verification, Mold retransmission generation, GLIMPSE, SoupBinTCP, full ITCH coverage, multi-symbol books, full exchange recovery/connectivity, MAC/PHY implementation, order entry, and trading strategy are not added by WIRE-002.

## K. Requirement-vs-restriction matrix

| Item | External source | Source fact | Wire-to-Decision treatment | Classification |
|---|---|---|---|---|
| EtherType IPv4 | RFC 894 | IPv4 Ethernet type `0x0800` | Accept only this EtherType | PROJECT VALIDATION RULE |
| IPv4 Version | RFC 791 | Version field identifies IPv4 | Require 4 | SOURCE REQUIREMENT |
| IPv4 IHL | RFC 791 | IHL is 32-bit words; minimum 5 | Accept 5 only | PROJECT RESTRICTION |
| IPv4 options | RFC 791 | Options occur beyond the minimum header | Reject by IHL=5 | PROJECT RESTRICTION |
| IPv4 fragmentation | RFC 791 | Unfragmented means MF=0 and offset=0 | Reject unless both conditions hold | PROJECT VALIDATION RULE |
| IPv4 header checksum | RFC 791 | Header checksum validates header | Must validate | PROJECT VALIDATION RULE |
| IPv4 protocol | RFC 791 | UDP protocol is 17 | Require 17 | SOURCE REQUIREMENT |
| UDP destination port | RFC 768 | Destination port is a 16-bit field | Configurable filter | PROJECT RESTRICTION |
| UDP length | RFC 768 | Includes header and data; minimum 8 | Validate consistency | PROJECT VALIDATION RULE |
| UDP checksum | RFC 768 | Zero means no checksum generated over IPv4 | Accept zero; reject nonzero | PROJECT RESTRICTION |
| Mold session | MoldUDP64 | 10-octet session field | Detect mismatch and fail closed | PROJECT VALIDATION RULE |
| Mold sequence | MoldUDP64 | First message sequence; later messages implicit | Detect discontinuity and fail closed | PROJECT VALIDATION RULE |
| Mold heartbeat | MoldUDP64 | Count zero | No ITCH state mutation | SOURCE REQUIREMENT |
| Mold end-of-session | MoldUDP64 | Count `0xFFFF` | Stop/suppress state until external re-arm | PROJECT RESTRICTION |
| Mold retransmission | MoldUDP64 | Request Packet mechanism exists | Do not generate requests | PROJECT RESTRICTION |
| ITCH byte order | TotalView-ITCH 5.0 | Integers are big-endian | Use as source basis later | SOURCE REQUIREMENT |
| ITCH Stock Locate | TotalView-ITCH 5.0 | 2 octets, common offset 1, daily assignment | One configured locate | PROJECT RESTRICTION |
| ITCH A | TotalView-ITCH 5.0 | Adds displayable order | Track mutation | SOURCE REQUIREMENT |
| ITCH F | TotalView-ITCH 5.0 | Adds attributed displayable order | Track mutation; omit attribution storage | PROJECT RESTRICTION |
| ITCH E | TotalView-ITCH 5.0 | Execution reduces order quantity | Track mutation | SOURCE REQUIREMENT |
| ITCH C | TotalView-ITCH 5.0 | Execution with price detail | Track quantity; do not replace display price with execution price | PROJECT VALIDATION RULE |
| ITCH X | TotalView-ITCH 5.0 | Partial cancel quantity | Track mutation | SOURCE REQUIREMENT |
| ITCH D | TotalView-ITCH 5.0 | Delete order | Track mutation | SOURCE REQUIREMENT |
| ITCH U | TotalView-ITCH 5.0 | Replace reference, shares, price; inherit side/stock/attribution | Defer atomic state implementation | PROJECT VALIDATION RULE |
| ITCH P | TotalView-ITCH 5.0 | Non-displayable trade, no book effect | Ignore for book mutation | PROJECT VALIDATION RULE |
| Single instrument | TotalView-ITCH 5.0 | Locate identifies instrument and is daily assigned | Track one configured locate | PROJECT RESTRICTION |

## L. Conflicts with current Wire-to-Decision definition

No external-source conflict requiring a technical scope change was found. The sources support the proposed post-MAC, IPv4/UDP, MoldUDP64, and single-locate ITCH subset. The zero-only UDP checksum policy, no-recovery policy, no-VLAN policy, and single-instrument policy are project restrictions rather than protocol requirements.

## M. Open questions

- The later implementation/specification tasks must define how a configured daily Stock Locate is supplied; WIRE-002 does not add Stock Directory processing.
- The later implementation task must define exact external recovery/re-arm control semantics without adding live re-request infrastructure.
- The post-MAC boundary and treatment of Ethernet frame bookkeeping remain project design details, not WIRE-002 source requirements.

## N. WIRE-002 conclusion

The authoritative external protocol basis is locked as specification/source evidence. The agreed MVP restrictions are explicitly separated from source requirements, and no unsupported protocol feature was silently added. WIRE-002 does not establish parser, model, simulation, formal, synthesis, timing, performance, CDC, or integration results.
