import hashlib
import random
import os
import numpy as np
from PIL import Image

import PLShandler as plsh

PLS = []
img = Image.open(r"images/in1.png")
[row, col] = img.size


def DataListInBit(data):
    dataBits = list(format(c, '08b') for c in bytearray(data.encode('latin-1')))
    return dataBits


def PLSgen(row, col, lenEncodedText, seed=None):
    requiredPixels = lenEncodedText * 3
    if requiredPixels > row * col:
        raise ValueError("The encoded text is too large for this image.")

    new = list(range(row * col))
    rng = random.Random(seed)
    for i in range(len(new) - 1, 0, -1):
        j = rng.randrange(i + 1)
        new[i], new[j] = new[j], new[i]
    PLS.clear()
    PLS.extend(new[:requiredPixels])
    return PLS.copy()


def embed_text(image, encodedText, pls):
    if image.mode != 'RGB':
        raise ValueError("The cover image must be RGB.")
    if len(pls) != len(encodedText) * 3:
        raise ValueError("The PLS must contain three pixel locations per character.")

    width, _ = image.size
    stegoImage = image.copy()
    dataBits = DataListInBit(encodedText)

    for charIndex, bits in enumerate(dataBits):
        pixelLocations = pls[charIndex * 3:charIndex * 3 + 3]
        pixels = []
        for location in pixelLocations:
            x = int(location) % width
            y = int(location) // width
            pixels.append(list(stegoImage.getpixel((x, y))))

        values = [value for pixel in pixels for value in pixel]
        for bitIndex, bit in enumerate(bits):
            value = values[bitIndex]
            if bit == '0' and value % 2:
                values[bitIndex] -= 1
            elif bit == '1' and value % 2 == 0:
                values[bitIndex] += 1 if value == 0 else -1

        for pixelIndex, location in enumerate(pixelLocations):
            x = int(location) % width
            y = int(location) // width
            start = pixelIndex * 3
            stegoImage.putpixel((x, y), tuple(values[start:start + 3]))

    return stegoImage


def extract_text(stegoImage, pls):
    if stegoImage.mode != 'RGB':
        raise ValueError("The stego image must be RGB.")
    if len(pls) % 3:
        raise ValueError("The PLS length must be a multiple of three.")

    width, _ = stegoImage.size
    decodedChars = []
    for offset in range(0, len(pls), 3):
        values = []
        for location in pls[offset:offset + 3]:
            x = int(location) % width
            y = int(location) // width
            values.extend(stegoImage.getpixel((x, y)))

        bits = ''.join('1' if value & 1 else '0' for value in values[:8])
        decodedChars.append(chr(int(bits, 2)))

    return ''.join(decodedChars)


def LsbEncoding(encodedText):
    pls = PLSgen(row, col, len(encodedText))
    np.savetxt("pls.txt", np.array(pls), delimiter="\t")
    stegoImage = embed_text(img, encodedText, pls)
    stegoImage.save("images/out1.png")
    plsPassword = input("Insert Password for pls encyption :")
    key = hashlib.sha256(plsPassword.encode()).digest()
    plsh.encrypt_file(key, 'pls.txt')


def LsbDecoding():
    plspassword = input("Insert Password for pls decryption :")
    key = hashlib.sha256(plspassword.encode()).digest()
    plsh.decrypt_file(key, 'pls.txt.enc', 'out.txt')
    pls = np.genfromtxt('out.txt', delimiter='\t')
    if os.path.exists("out.txt"):
        os.remove("out.txt")
    if os.path.exists("pls.txt.enc"):
        os.remove("pls.txt.enc")
    stegoImage = Image.open(r"images/out1.png")
    pls = np.atleast_1d(pls).astype(int).tolist()
    return extract_text(stegoImage, pls)
