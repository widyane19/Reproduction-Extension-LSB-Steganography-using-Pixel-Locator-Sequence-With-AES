import csv
import getpass
import hashlib
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

import AES as cipher
import LSB as lsb
import PLShandler as plsh


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
RESULTS_DIR = BASE_DIR / "reproduction-results"
MESSAGE = "This secret message has to be embedded into the image"
PAPER_CIPHERTEXT = (
    "74890293687ebfa135e17563dc222c17696db16f6378f1a4e41e"
    "2ae71929b41199b441f70a75b212914c0f9a64b3f3f18aec3fda5d379238"
)
PLS_SEED = 2026
PAPER_RESULTS = {
    1: (1.68467, 45.86564),
    2: (2.27218, 44.56635),
    3: (0.95186, 48.34506),
    4: (1.19884, 47.34317),
    5: (2.24326, 44.62198),
}


def round_trip_pls(pls, password):
    # Encrypt and decrypt the PLS in temporary files, then confirm it is unchanged.
    key = hashlib.sha256(password.encode()).digest()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        plain_path = temp_path / "pls.txt"
        encrypted_path = temp_path / "pls.txt.enc"
        decrypted_path = temp_path / "pls-decoded.txt"
        np.savetxt(plain_path, np.array(pls), delimiter="\t")
        plsh.encrypt_file(key, str(plain_path), str(encrypted_path))
        plsh.decrypt_file(key, str(encrypted_path), str(decrypted_path))
        recovered = np.atleast_1d(
            np.genfromtxt(decrypted_path, delimiter="\t")
        ).astype(int).tolist()
    if recovered != pls:
        raise AssertionError("The encrypted PLS did not round-trip.")
    return recovered


def image_metrics(original, stego):
    # Measure pixel error and convert it to PSNR for comparison with the paper.
    originalPixels = np.asarray(original, dtype=np.float64)
    stegoPixels = np.asarray(stego, dtype=np.float64)
    mse = float(np.mean((originalPixels - stegoPixels) ** 2))
    psnr = float("inf") if mse == 0 else 20 * np.log10(255 / np.sqrt(mse))
    return mse, psnr


def main():
    # Use an environment password when supplied; otherwise ask without displaying it.
    password = os.environ.get("REPRODUCTION_PASSWORD")
    if password is None:
        password = getpass.getpass(
            "Enter a throwaway demo password (never use a real password): "
        )
    if not password:
        raise ValueError("A non-empty demo password is required.")

    testCiphertext = cipher.encrypt(MESSAGE, password)
    if cipher.decrypt(testCiphertext, password) != MESSAGE:
        raise AssertionError("The message encryption did not round-trip.")

    RESULTS_DIR.mkdir(exist_ok=True)
    csv_path = RESULTS_DIR / "results.csv"
    rows = []

    for image_number in range(1, 6):
        # Embed the paper's ciphertext, recover it, and record image-quality metrics.
        image_path = IMAGE_DIR / f"in{image_number}.png"
        with Image.open(image_path) as source:
            cover = source.convert("RGB")

        width, height = cover.size
        pls = lsb.PLSgen(width, height, len(PAPER_CIPHERTEXT), PLS_SEED)
        recoveredPls = round_trip_pls(pls, password)
        stego = lsb.embed_text(cover, PAPER_CIPHERTEXT, pls)
        recoveredMessage = lsb.extract_text(stego, recoveredPls)
        if recoveredMessage != PAPER_CIPHERTEXT:
            raise AssertionError(f"Ciphertext round-trip failed for {image_path.name}.")

        mse, psnr = image_metrics(cover, stego)
        output_path = RESULTS_DIR / f"out{image_number}.png"
        stego.save(output_path)
        paperMse, paperPsnr = PAPER_RESULTS[image_number]
        rows.append({
            "image": image_path.name,
            "width": width,
            "height": height,
            "seed": PLS_SEED,
            "paper_mse": f"{paperMse:.5f}",
            "reproduction_mse": f"{mse:.6f}",
            "paper_psnr_db": f"{paperPsnr:.5f}",
            "reproduction_psnr_db": f"{psnr:.6f}",
            "round_trip": "passed",
        })

    with csv_path.open("w", newline="", encoding="utf-8") as results_file:
        writer = csv.DictWriter(results_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("\nImage   Paper MSE   Our MSE   Paper PSNR   Our PSNR   Recovery")
    for row in rows:
        image_number = row["image"][2:-4]
        print(
            f"{image_number:<7}"
            f"{row['paper_mse']:>10}   "
            f"{row['reproduction_mse']:>8}   "
            f"{row['paper_psnr_db']:>10}   "
            f"{row['reproduction_psnr_db']:>8}   "
            f"{row['round_trip']}"
        )
    print(f"\nResults saved in: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
