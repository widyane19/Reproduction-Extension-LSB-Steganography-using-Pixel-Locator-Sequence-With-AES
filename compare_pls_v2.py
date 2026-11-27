import getpass
import hashlib
import math
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

import AES as aes
import LSB as lsb
import PLShandler as plsh
import pls_v2
from extension import print_table, write_csv
from reproduce import BASE_DIR, IMAGE_DIR, MESSAGE, PLS_SEED, image_metrics


RESULTS_DIR = BASE_DIR / "pls-v2-results"
MESSAGE_LENGTHS = [53, 500, 2000, 5000]


def make_message(length):
    # Repeat the paper's sample message until it is the length we want.
    return ((MESSAGE + " ") * (length // len(MESSAGE) + 1))[:length]


def load_cover(imageNumber):
    with Image.open(IMAGE_DIR / f"in{imageNumber}.png") as source:
        return source.convert("RGB")


def encrypted_pls_size(pls, password):
    # Save and encrypt the PLS the same way the original code does,
    # then measure the size of the file that has to be sent.
    key = hashlib.sha256(password.encode()).digest()
    with tempfile.TemporaryDirectory() as tempDir:
        plainPath = Path(tempDir) / "pls.txt"
        np.savetxt(plainPath, np.array(pls), delimiter="\t")
        plsh.encrypt_file(key, str(plainPath))
        return os.path.getsize(str(plainPath) + ".enc")


def run_original(cover, message, password):
    hexText = aes.encrypt(message, password)
    width, height = cover.size
    pls = lsb.PLSgen(width, height, len(hexText), PLS_SEED)
    stego = lsb.embed_text(cover, hexText, pls)
    if aes.decrypt(lsb.extract_text(stego, pls), password) != message:
        raise AssertionError("The original method did not recover the message.")
    return stego, pls, len(hexText), len(pls), encrypted_pls_size(pls, password)


def run_v2(cover, message, password):
    stego = pls_v2.hide_message(cover, message, password)
    if pls_v2.reveal_message(stego, password) != message:
        raise AssertionError("PLS v2 did not recover the message.")
    hiddenBytes = pls_v2.hidden_size(message)
    pixelsUsed = pls_v2.SALT_PIXELS + math.ceil((hiddenBytes - pls_v2.SALT_SIZE) * 8 / 3)
    return stego, hiddenBytes, pixelsUsed, 0


def result_row(imageName, message, method, cover, stego, hiddenBytes, pixelsUsed, extraFileBytes):
    mse, psnr = image_metrics(cover, stego)
    valuesChanged = int(np.count_nonzero(np.asarray(cover) != np.asarray(stego)))
    return {
        "image": imageName,
        "message chars": len(message),
        "method": method,
        "bytes hidden": hiddenBytes,
        "pixels used": pixelsUsed,
        "values changed": valuesChanged,
        "MSE": f"{mse:.6f}",
        "PSNR (dB)": f"{psnr:.2f}",
        "extra file to send (bytes)": extraFileBytes,
    }


def compare_images(password):
    # Same paper message in all five images, original method vs PLS v2.
    rows = []
    for imageNumber in range(1, 6):
        cover = load_cover(imageNumber)
        name = f"in{imageNumber}.png"
        stego, _, hiddenBytes, pixelsUsed, plsBytes = run_original(cover, MESSAGE, password)
        rows.append(result_row(name, MESSAGE, "original", cover, stego, hiddenBytes, pixelsUsed, plsBytes))
        stego, hiddenBytes, pixelsUsed, extraBytes = run_v2(cover, MESSAGE, password)
        rows.append(result_row(name, MESSAGE, "PLS v2", cover, stego, hiddenBytes, pixelsUsed, extraBytes))
    return rows


def compare_message_lengths(password):
    # One image, longer and longer messages, to see how the overhead grows.
    rows = []
    cover = load_cover(3)
    for length in MESSAGE_LENGTHS:
        message = make_message(length)
        stego, _, hiddenBytes, pixelsUsed, plsBytes = run_original(cover, message, password)
        rows.append(result_row("in3.png", message, "original", cover, stego, hiddenBytes, pixelsUsed, plsBytes))
        stego, hiddenBytes, pixelsUsed, extraBytes = run_v2(cover, message, password)
        rows.append(result_row("in3.png", message, "PLS v2", cover, stego, hiddenBytes, pixelsUsed, extraBytes))
    return rows


def compare_wrong_password(password):
    # What does the receiver see if they type the wrong password?
    cover = load_cover(1)
    wrongPassword = password + "-wrong"

    stego, pls, _, _, _ = run_original(cover, MESSAGE, password)
    hexText = lsb.extract_text(stego, pls)
    try:
        originalResult = "returned text: " + repr(aes.decrypt(hexText, wrongPassword)[:20])
    except UnicodeDecodeError:
        originalResult = "crashed with UnicodeDecodeError (garbage bytes)"

    stego, _, _, _ = run_v2(cover, MESSAGE, password)
    try:
        pls_v2.reveal_message(stego, wrongPassword)
        v2Result = "returned text"
    except ValueError as error:
        v2Result = f"rejected: {error}"

    return [
        {"method": "original", "wrong password result": originalResult, "clear warning": "no"},
        {"method": "PLS v2", "wrong password result": v2Result,
         "clear warning": "yes" if v2Result.startswith("rejected") else "no"},
    ]


def main():
    password = os.environ.get("REPRODUCTION_PASSWORD")
    if password is None:
        password = getpass.getpass("Enter a throwaway demo password: ")
    if not password:
        raise ValueError("A non-empty demo password is required.")

    imageRows = compare_images(password)
    lengthRows = compare_message_lengths(password)
    passwordRows = compare_wrong_password(password)

    print("PLS v2 COMPARISON")
    print("=" * 80)
    print("Original: AES-CTR hex text + PLS file locked with a second password.")
    print("PLS v2:   AES-GCM raw bytes, pixel order made from the password, no PLS file.")
    print_table("1. Paper message in all five images", imageRows)
    print_table("2. Longer messages in in3.png", lengthRows)
    print_table("3. Receiver types the wrong password", passwordRows)

    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(RESULTS_DIR / "images.csv", imageRows)
    write_csv(RESULTS_DIR / "message-lengths.csv", lengthRows)
    write_csv(RESULTS_DIR / "wrong-password.csv", passwordRows)
    print(f"\nResults saved in: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
