"""
Compression Extension for AES + PLS Steganography

Goal:
    Investigate whether compressing plaintext before AES
    encryption reduces the amount of data that must be
    embedded in the image while maintaining or improving
    image quality.



Proposed workflow:

    Message
        ↓
    Compression
        ↓
    AES Encryption
        ↓
    LSB Embedding

Metrics collected:
    - Ciphertext size
    - Mean Squared Error (MSE)
    - Peak Signal-to-Noise Ratio (PSNR)

"""

import csv
import getpass
import os
import zlib

import numpy as np
from PIL import Image

import AES as aes
import LSB as lsb

from reproduce import BASE_DIR


# Directory containing cover images
IMAGE_DIR = BASE_DIR / "images"

# Directory where experiment results are written
RESULTS_DIR = BASE_DIR / "extension-results"

# Fixed seed so every run uses the same PLS locations
# and therefore remains reproducible
PLS_SEED = 2026

# Repetitive text is used because
# it compresses well and highlights the effect
# of compression on embedding size.
MESSAGE = (
    "The quick brown fox jumps over the lazy dog. "
    * 50
)


def image_metrics(original, stego):
    """
    Compare an original image and a stego image.

    MSE:
        Average squared pixel error.

        Lower MSE means less image distortion.

    PSNR:
        Standard image-quality metric.

        Higher PSNR means the stego image is
        more visually similar to the original.
    """

    original_pixels = np.asarray(
        original,
        dtype=np.float64
    )

    stego_pixels = np.asarray(
        stego,
        dtype=np.float64
    )

    mse = float(
        np.mean(
            (original_pixels - stego_pixels) ** 2
        )
    )

    psnr = (
        float("inf")
        if mse == 0
        else 20 * np.log10(
            255 / np.sqrt(mse)
        )
    )

    return mse, psnr


def compressed_encrypt(message, password):
    """
    Encryption pipeline.

    Step 1:
        Compress plaintext using zlib.

    Step 2:
        Convert compressed bytes into hex because
        the repository AES implementation expects
        string input.

    Step 3:
        Encrypt compressed data with AES.

    Returns:
        AES ciphertext generated from compressed text.
    """

    compressed = zlib.compress(
        message.encode("utf-8")
    )

    compressed_hex = compressed.hex()

    ciphertext = aes.encrypt(
        compressed_hex,
        password
    )

    return ciphertext


def compressed_decrypt(ciphertext, password):
    """
    Reverse the compression pipeline.

    AES decrypt
        ↓
    Convert hex back to bytes
        ↓
    Decompress
        ↓
    Recover original plaintext
    """

    compressed_hex = aes.decrypt(
        ciphertext,
        password
    )

    compressed_bytes = bytes.fromhex(
        compressed_hex
    )

    return zlib.decompress(
        compressed_bytes
    ).decode("utf-8")


def test_original_pipeline(cover, password):
    """
    Run the repository's original system.

    Message
        ↓
    AES Encryption
        ↓
    PLS Generation
        ↓
    LSB Embedding
        ↓
    Extraction
        ↓
    AES Decryption

    The recovered plaintext is compared against
    the original message to verify correctness.
    """

    # Encrypt plaintext
    ciphertext = aes.encrypt(
        MESSAGE,
        password
    )

    # Generate randomized pixel locations
    # used during embedding
    pls = lsb.PLSgen(
        cover.size[0],
        cover.size[1],
        len(ciphertext),
        seed=PLS_SEED
    )

    # Create stego image containing ciphertext
    stego = lsb.embed_text(
        cover,
        ciphertext,
        pls
    )

    # Extract ciphertext back out of image
    recovered_ciphertext = (
        lsb.extract_text(
            stego,
            pls
        )
    )

    # Recover plaintext
    recovered_message = (
        aes.decrypt(
            recovered_ciphertext,
            password
        )
    )

    # Measure visual distortion caused by embedding
    mse, psnr = image_metrics(
        cover,
        stego
    )

    return {
        "ciphertext_size": len(ciphertext),
        "mse": mse,
        "psnr": psnr,
        "recovered":
            recovered_message == MESSAGE
    }


def test_compressed_pipeline(cover, password):
    """
    Run the proposed compression extension.

    Message
        ↓
    Compression
        ↓
    AES Encryption
        ↓
    PLS Generation
        ↓
    LSB Embedding
        ↓
    Extraction
        ↓
    AES Decryption
        ↓
    Decompression

    The purpose is to reduce ciphertext size so fewer
    pixels must be modified during embedding.
    """

    # Encrypt compressed plaintext
    ciphertext = compressed_encrypt(
        MESSAGE,
        password
    )

    # Generate PLS locations matching ciphertext length
    pls = lsb.PLSgen(
        cover.size[0],
        cover.size[1],
        len(ciphertext),
        seed=PLS_SEED
    )

    # Embed ciphertext into image
    stego = lsb.embed_text(
        cover,
        ciphertext,
        pls
    )

    # Recover ciphertext from image
    recovered_ciphertext = (
        lsb.extract_text(
            stego,
            pls
        )
    )

    # Decrypt and decompress
    recovered_message = (
        compressed_decrypt(
            recovered_ciphertext,
            password
        )
    )

    # Measure image distortion
    mse, psnr = image_metrics(
        cover,
        stego
    )

    return {
        "ciphertext_size": len(ciphertext),
        "mse": mse,
        "psnr": psnr,
        "recovered":
            recovered_message == MESSAGE
    }


def main():

    # Allow an environment variable for automated testing
    password = os.environ.get(
        "REPRODUCTION_PASSWORD"
    )

    if password is None:

        password = getpass.getpass(
            "Enter demo password: "
        )

    RESULTS_DIR.mkdir(
        exist_ok=True
    )

    rows = []

    print("\nCOMPRESSION VS ORIGINAL")
    print("=" * 80)

    # Evaluate each of the five cover images
    for image_number in range(1, 6):

        image_path = (
            IMAGE_DIR /
            f"in{image_number}.png"
        )

        with Image.open(
            image_path
        ) as img:

            cover = img.convert("RGB")

        # Test original repository method
        original = (
            test_original_pipeline(
                cover,
                password
            )
        )

        # Test proposed compression extension
        compressed = (
            test_compressed_pipeline(
                cover,
                password
            )
        )

        # Save measurements for CSV export
        row = {

            "image":
                image_path.name,

            "original_ciphertext":
                original["ciphertext_size"],

            "compressed_ciphertext":
                compressed["ciphertext_size"],

            "ciphertext_saved":
                original["ciphertext_size"]
                - compressed["ciphertext_size"],

            "original_psnr":
                f"{original['psnr']:.4f}",

            "compressed_psnr":
                f"{compressed['psnr']:.4f}",

            "psnr_improvement":
                f"{compressed['psnr'] - original['psnr']:.4f}",

            "original_mse":
                f"{original['mse']:.6f}",

            "compressed_mse":
                f"{compressed['mse']:.6f}",

            "original_recovered":
                original["recovered"],

            "compressed_recovered":
                compressed["recovered"]
        }

        rows.append(row)

        print(f"\n{image_path.name}")

        print(
            f"Ciphertext: "
            f"{original['ciphertext_size']} "
            f"-> "
            f"{compressed['ciphertext_size']}"
        )

        print(
            f"PSNR: "
            f"{original['psnr']:.3f} "
            f"-> "
            f"{compressed['psnr']:.3f}"
        )

        print(
            f"MSE: "
            f"{original['mse']:.6f} "
            f"-> "
            f"{compressed['mse']:.6f}"
        )

    # Write experiment results to a CSV file
    csv_path = (
        RESULTS_DIR /
        "compression-steganography.csv"
    )

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as output:

        writer = csv.DictWriter(
            output,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"\nResults saved to: {csv_path}"
    )


if __name__ == "__main__":
    main()