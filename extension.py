import csv
import getpass
import os

from Cryptodome.Cipher import ChaCha20_Poly1305
from PIL import Image

import AES as aes
import LSB as lsb
from reproduce import BASE_DIR


RESULTS_DIR = BASE_DIR / "extension-results"
DEMO_SEED = 42
SEED_SEARCH_LIMIT = 64


def compare_nonce_reuse(password):
    # Reusing an AES-CTR key and counter lets known plaintext reveal the other message.
    known = "known demo plaintext for CTR reuse"
    target = "other demo plaintext for CTR reuse"
    first = bytes.fromhex(aes.encrypt(known, password))
    second = bytes.fromhex(aes.encrypt(target, password))
    recovered = bytes(a ^ b ^ c for a, b, c in zip(first, second, known.encode()))
    return [{
        "plaintext A (known)": known,
        "plaintext B (target)": target,
        "same key and counter": "yes",
        "ciphertext XOR = plaintext XOR": "yes" if (
            bytes(a ^ b for a, b in zip(first, second))
            == bytes(a ^ b for a, b in zip(known.encode(), target.encode()))
        ) else "no",
        "recovered B": recovered.decode(),
        "outcome": "vulnerable" if recovered.decode() == target else "not reproduced",
    }]


def compare_tamper_detection(password):
    # Compare unauthenticated CTR with authenticated encryption after changing one bit.
    message = "authenticated demo message"
    ctr = bytearray.fromhex(aes.encrypt(message, password))
    ctr[0] ^= 1
    changed_plaintext = aes.decrypt(ctr.hex(), password) != message

    key = aes.pbkdf2.PBKDF2(password, aes.passwordSalt).read(32)
    nonce = b"authdemo1234"
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode())
    altered = bytearray(ciphertext)
    altered[0] ^= 1
    verifier = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    try:
        verifier.decrypt_and_verify(bytes(altered), tag)
        chacha_result = "accepted"
    except ValueError:
        chacha_result = "rejected"
    return [
        {"scheme": "Repository AES-CTR", "ciphertext bit flipped": 1, "decryption result": "changed plaintext" if changed_plaintext else "unchanged", "tamper detected": "no"},
        {"scheme": "ChaCha20-Poly1305", "ciphertext bit flipped": 1, "decryption result": chacha_result, "tamper detected": "yes" if chacha_result == "rejected" else "no"},
    ]


def test_pls_recovery():
    # Compare sequential reading with trying a small range of possible PLS seeds.
    payload = "demo payload"
    cover = Image.new("RGB", (64, 64), color=(100, 120, 140))
    pls = lsb.PLSgen(*cover.size, len(payload), seed=DEMO_SEED)
    stego = lsb.embed_text(cover, payload, pls)
    sequential_works = lsb.extract_text(stego, list(range(len(payload) * 3))) == payload
    found_seed = None
    attempts = 0
    for seed in range(SEED_SEARCH_LIMIT):
        attempts += 1
        candidate = lsb.PLSgen(*cover.size, len(payload), seed=seed)
        if lsb.extract_text(stego, candidate) == payload:
            found_seed = seed
            break
    return [{
        "payload length (characters)": len(payload),
        "embedding seed": DEMO_SEED,
        "sequential extraction": "recovered" if sequential_works else "failed",
        "seeds searched": f"0-{SEED_SEARCH_LIMIT - 1}",
        "candidates tested": attempts,
        "seed found": found_seed if found_seed is not None else "none",
        "outcome": "seed recovered" if found_seed == DEMO_SEED else "not recovered",
    }]


def write_csv(path, rows):
    # Save result dictionaries as a headered CSV table.
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def print_table(title, rows):
    # Calculate column widths so the results line up in the terminal.
    print(f"\n{title}")
    columns = list(rows[0])
    widths = {col: max(len(col), *(len(str(row[col])) for row in rows)) for col in columns}
    print("  ".join(col.ljust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        print("  ".join(str(row[col]).ljust(widths[col]) for col in columns))


def print_report(nonce_rows, integrity_rows, pls_rows):
    # Explain what each experiment measured and what its output means.
    print("SECURITY EXTENSION RESULTS")
    print("=" * 80)
    print("1. Confidentiality: What if the AES-CTR counter is reused?")
    print("Comparison: two same-length messages encrypted with the same password")
    print("and fixed counter; known message A is used to recover message B.")
    print_table("Measured values and outcome", nonce_rows)
    print("Finding: if B is recovered, counter reuse exposed its contents.\n")

    print("2. Integrity: Can someone change the ciphertext without being caught?")
    print("Comparison: same demo message, one ciphertext bit flipped in each scheme.")
    print_table("AES-CTR vs. ChaCha20-Poly1305", integrity_rows)
    print("Finding: AES-CTR has no tamper check; ChaCha20-Poly1305 rejected the")
    print("modified ciphertext.\n")

    print("3. PLS contribution: Does a less obvious pixel order protect the hidden data?")
    print("Comparison: sequential extraction versus searching the tested seed range.")
    print("The test knows the expected demo payload to identify a successful seed.")
    print_table("Measured values and outcome", pls_rows)
    print("Finding: this small search tests predictable seed exposure only; it")
    print("does not test recovery of the paper's AES-encrypted PLS.\n")

    print("Keyword guide (meaning in these tables)")
    print("vulnerable = known message A let the test recover message B")
    print("changed plaintext = altered ciphertext decrypted to altered text")
    print("yes / no = the stated property was / was not observed")
    print("none = AES-CTR has no built-in integrity check")
    print("rejected / detected = authentication caught the change; no plaintext returned")
    print("failed = sequential pixel reading did not recover this payload")
    print("seed recovered = a candidate in the stated search range reproduced it")


def main():
    # Run all three demonstrations, print their results, and save each as a CSV.
    password = os.environ.get("REPRODUCTION_PASSWORD")
    if password is None:
        password = getpass.getpass("Enter a throwaway demo password: ")
    if not password:
        raise ValueError("A non-empty demo password is required.")

    nonce_rows = compare_nonce_reuse(password)
    integrity_rows = compare_tamper_detection(password)
    pls_rows = test_pls_recovery()
    RESULTS_DIR.mkdir(exist_ok=True)

    print_report(nonce_rows, integrity_rows, pls_rows)

    write_csv(RESULTS_DIR / "confidentiality-nonce-reuse.csv", nonce_rows)
    write_csv(RESULTS_DIR / "integrity-comparison.csv", integrity_rows)
    write_csv(RESULTS_DIR / "pls-security.csv", pls_rows)
    print(f"\nThree result tables saved in: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
