import unittest

from PIL import Image

import LSB as lsb


class ReproductionTests(unittest.TestCase):
    def test_seeded_pls_is_repeatable_and_unique(self):
        first = lsb.PLSgen(20, 20, 5, seed=7)
        second = lsb.PLSgen(20, 20, 5, seed=7)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 15)
        self.assertEqual(len(set(first)), len(first))

    def test_embedded_text_can_be_extracted(self):
        cover = Image.new("RGB", (20, 20), color=(100, 120, 140))
        message = "paper"
        pls = lsb.PLSgen(20, 20, len(message), seed=7)

        stego = lsb.embed_text(cover, message, pls)

        self.assertEqual(lsb.extract_text(stego, pls), message)
        self.assertEqual(cover.getpixel((0, 0)), (100, 120, 140))

    def test_pixel_locations_follow_row_major_image_order(self):
        cover = Image.new("RGB", (4, 3), color=(100, 100, 100))

        stego = lsb.embed_text(cover, "\xff", [0, 1, 2])

        self.assertEqual(stego.getpixel((1, 0)), (99, 99, 99))
        self.assertEqual(stego.getpixel((0, 1)), (100, 100, 100))

    def test_pls_generation_rejects_payload_that_is_too_large(self):
        with self.assertRaises(ValueError):
            lsb.PLSgen(2, 2, 2, seed=7)


if __name__ == "__main__":
    unittest.main()
