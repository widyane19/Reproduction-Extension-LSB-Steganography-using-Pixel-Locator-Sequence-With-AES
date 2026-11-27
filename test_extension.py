import unittest

import extension


class SecurityExtensionTests(unittest.TestCase):
    # Verify that known plaintext exposes a second message when CTR reuses its counter.
    def test_ctr_counter_reuse_recovers_second_plaintext(self):
        row = extension.compare_nonce_reuse("test-only")[0]
        self.assertEqual(row["recovered B"], "other demo plaintext for CTR reuse")
        self.assertEqual(row["outcome"], "vulnerable")

    # Confirm authenticated encryption rejects a modified ciphertext.
    def test_chacha_poly1305_detects_tampering(self):
        rows = extension.compare_tamper_detection("test-only")
        self.assertEqual(rows[0]["decryption result"], "changed plaintext")
        self.assertEqual(rows[1]["decryption result"], "rejected")

    # Check that sequential reading fails but the known seed is found in the search.
    def test_predictable_pls_seed_is_recovered(self):
        row = extension.test_pls_recovery()[0]
        self.assertEqual(row["seed found"], extension.DEMO_SEED)
        self.assertEqual(row["sequential extraction"], "failed")


if __name__ == "__main__":
    unittest.main()
