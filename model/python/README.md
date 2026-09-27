# Python reference-model skeleton

This package is the original, project-owned foundation for the independent
Wire-to-Decision functional oracle. It is governed by the authoritative
requirements and microarchitecture documents, especially WIRE-D006 through
WIRE-D008.

Run its standard-library tests from the repository root with:

```bash
PYTHONPATH=model/python python3 -m unittest discover -s model/python/tests -v
```

WIRE-008 implements canonical data representations, the WIRE-D008 normalized
event validity contract, validation primitives and the frozen order-reference
hash. Ethernet/IP/UDP/MoldUDP64 parsing, ITCH decoding, bounded order-state
mutation and decision logic remain deliberately unimplemented. The Python
model is intended to become the independent functional oracle for RTL
verification, but WIRE-008 alone does not establish reference-model
correctness.
