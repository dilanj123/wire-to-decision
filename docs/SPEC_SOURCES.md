# External Protocol Sources

WIRE-002 freezes the following primary source basis for the proposed MVP. The exact retrieved fingerprints and retrieval notes are in `results/raw/spec_sources/`.

| Source ID | Protocol | Authority / artifact | Declared version | SHA-256 |
|---|---|---|---|---|
| RFC-894 | IPv4 over Ethernet II | RFC Editor, RFC 894 | RFC 894 | `be88b9301e53f986aca3a0e55e488d1d79bae3f88fe3f257640397bc089e7035` |
| RFC-791 | IPv4 | RFC Editor, RFC 791 | IPv4 / RFC 791 | `6cfb387fcecfc1b72f2f69343c5b6951b5d263d708162e2b5c66ab8f394f6265` |
| RFC-768 | UDP | RFC Editor, RFC 768 | RFC 768 | `7dc8880e1ecef9c3f9da0db4b876a16e96bfa4f0953cc9d977d414f8f680c2f0` |
| NASDAQ-MOLDUDP64 | MoldUDP64 | Nasdaq Trader, `moldudp64.pdf` | V 1.00 | `96cdd02b8728a441cb970d1371a96e73c01e1edaffb2891d43667e2a0ad8add5` |
| NASDAQ-ITCH5 | TotalView-ITCH | Nasdaq current linked artifact, `NQTVITCHSpecification__1_.pdf` | Version 5.0 | `4eb5a16abf7f32d6c97896f7c1de4aa51a1241f2da973519722614962f71a130` |

## Authority and metadata

- RFC 894: [RFC Editor copy](https://www.rfc-editor.org/rfc/rfc894.txt); [verified errata](https://www.rfc-editor.org/errata/rfc894). Errata 570 and 5141 correct the Ethernet data-field limit wording to a maximum of 1500 octets.
- RFC 791: [RFC Editor copy](https://www.rfc-editor.org/rfc/rfc791.txt); the RFC Editor information page identifies later updates including RFC 6864.
- RFC 768: [RFC Editor copy](https://www.rfc-editor.org/rfc/rfc768.html); the cited checksum semantics are retained as source facts.
- MoldUDP64: [Nasdaq canonical artifact](https://nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/moldudp64.pdf). The artifact declares V 1.00 and its Version Control table ends with 2024-08-02 formatting.
- TotalView-ITCH: [current Nasdaq notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=DTN2025-22) links the [current PDF artifact](https://assets.ctfassets.net/mx0rke14e5yt/6j4wVwVw76myrW3zid1oay/2444b4b8fc8183ad7aa80154c70bb5cb/NQTVITCHSpecification__1_.pdf). The PDF declares Version 5.0 and includes a 2025-06-16 revision entry.

Retrieval timestamp for this lock: 2026-09-27T11:42:10Z. Source files were downloaded only to temporary locations for hashing and inspection; no copyrighted PDF is committed.
