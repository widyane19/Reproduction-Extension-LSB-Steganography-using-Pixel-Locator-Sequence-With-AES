import unittest

import numpy as np
from PIL import Image

import pls_v2


def make_cover(width=60, height=60):
    # A noisy test image, closer to a real photo than a single solid color.
    rng = np.random.default_rng(1)
    return Image.fromarray(rng.integers(0, 256, (height, width, 3), dtype=np.uint8))


def flip_one_hidden_bit(stego, password):
    # Flip the low bit of one pixel that holds the ciphertext.
    # Bits 0-255 are the length, nonce and tag, so bit 300 is in the ciphertext.
    pixels = pls_v2.image_to_pixels(stego)
    salt = pls_v2.read_salt(pixels)
    _, orderKey = pls_v2.make_keys(password, salt)
    order = pls_v2.pixel_order(orderKey, len(pixels))
    pixels[order[300 // 3], 300 % 3] ^= 1
    width, height = stego.size
    return Image.fromarray(pixels.reshape(height, width, 3))


class PlsV2Tests(unittest.TestCase):
    def test_message_round_trip(self):
        stego = pls_v2.hide_message(make_cover(), "meet at the library at 5", "test-only")
        self.assertEqual(pls_v2.reveal_message(stego, "test-only"), "meet at the library at 5")

    def test_wrong_password_is_rejected(self):
        stego = pls_v2.hide_message(make_cover(), "meet at the library at 5", "test-only")
        with self.assertRaises(ValueError):
            pls_v2.reveal_message(stego, "wrong-password")

    def test_changed_image_is_rejected(self):
        stego = pls_v2.hide_message(make_cover(), "meet at the library at 5", "test-only")
        changed = flip_one_hidden_bit(stego, "test-only")
        with self.assertRaises(ValueError):
            pls_v2.reveal_message(changed, "test-only")

    def test_message_too_large_is_rejected(self):
        with self.assertRaises(ValueError):
            pls_v2.hide_message(make_cover(10, 10), "x" * 200, "test-only")

    def test_only_low_bits_change(self):
        cover = make_cover()
        stego = pls_v2.hide_message(cover, "meet at the library at 5", "test-only")
        difference = np.abs(np.asarray(cover, dtype=int) - np.asarray(stego, dtype=int))
        self.assertLessEqual(difference.max(), 1)

    def test_same_message_twice_gives_different_images(self):
        # A new salt and nonce each time, so the AES-CTR reuse problem does not happen.
        cover = make_cover()
        first = pls_v2.hide_message(cover, "same message", "test-only")
        second = pls_v2.hide_message(cover, "same message", "test-only")
        self.assertFalse(np.array_equal(np.asarray(first), np.asarray(second)))

    def test_pixel_order_uses_each_pixel_once(self):
        order = pls_v2.pixel_order(b"k" * 32, 400)
        self.assertEqual(sorted(order), list(range(pls_v2.SALT_PIXELS, 400)))
        self.assertEqual(order, pls_v2.pixel_order(b"k" * 32, 400))
        self.assertNotEqual(order, pls_v2.pixel_order(b"j" * 32, 400))


if __name__ == "__main__":
    unittest.main()
