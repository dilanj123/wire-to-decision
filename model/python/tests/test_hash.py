import unittest

from wire_to_decision import order_set_index
from wire_to_decision.errors import CanonicalDataError


class OrderSetIndexTests(unittest.TestCase):
    VECTORS = {
        0x0000000000000000: 0x000,
        0x0000000000000001: 0x001,
        0x0000000000000100: 0x100,
        0x0000000000000200: 0x001,
        0x0000000000040000: 0x001,
        0x8000000000000000: 0x001,
        0xFFFFFFFFFFFFFFFF: 0x1FE,
        0x0123456789ABCDEF: 0x1DA,
        0xFEDCBA9876543210: 0x024,
        0x13579BDF2468ACE0: 0x104,
        0x0001002004008000: 0x14A,
    }

    def test_fixed_vectors(self):
        for order_ref, expected in self.VECTORS.items():
            with self.subTest(order_ref=hex(order_ref)):
                self.assertEqual(order_set_index(order_ref), expected)

    def test_output_is_nine_bits(self):
        for order_ref in self.VECTORS:
            self.assertGreaterEqual(order_set_index(order_ref), 0)
            self.assertLessEqual(order_set_index(order_ref), 0x1FF)

    def test_rejects_out_of_range_values(self):
        with self.assertRaises(CanonicalDataError):
            order_set_index(-1)
        with self.assertRaises(CanonicalDataError):
            order_set_index(1 << 64)


if __name__ == "__main__":
    unittest.main()
