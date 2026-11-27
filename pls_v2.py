import hashlib
import hmac
import struct

import numpy as np
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from PIL import Image


# PLS v2: the pixel order is made from the password, so no PLS file is sent.
#
# What gets hidden in the image:
#   salt   (16 bytes) - first pixels, in normal order (the salt is not secret)
#   length (4 bytes)  - how many bytes come after it
#   nonce  (12 bytes) - random value AES-GCM needs for each message
#   tag    (16 bytes) - AES-GCM's tamper check
#   ciphertext        - the encrypted message as raw bytes (not hex)
# Everything after the salt is written in the secret pixel order.

SALT_SIZE = 16
LENGTH_SIZE = 4
NONCE_SIZE = 12
TAG_SIZE = 16
PBKDF2_ROUNDS = 200000

# The salt needs 128 bits. Each pixel holds 3 bits (R, G, B), so 43 pixels.
SALT_PIXELS = (SALT_SIZE * 8 + 2) // 3

REJECTED = "Wrong password, or the image was changed."


def bytes_to_bits(data):
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits):
    data = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i:i + 8]:
            byte = (byte << 1) | bit
        data.append(byte)
    return bytes(data)


def make_keys(password, salt):
    # One slow PBKDF2 call gives 64 bytes: the first half is the AES key,
    # the second half is the key that decides the pixel order.
    keyBytes = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, PBKDF2_ROUNDS, dklen=64)
    return keyBytes[:32], keyBytes[32:]


def pixel_order(orderKey, totalPixels):
    # Give every pixel a secret score with HMAC-SHA256, then sort by score.
    # Sender and receiver get the same order because they have the same key.
    # Without the key the order cannot be guessed. The salt pixels are skipped.
    def score(pixel):
        return hmac.new(orderKey, pixel.to_bytes(4, 'big'), hashlib.sha256).digest()

    pixels = list(range(SALT_PIXELS, totalPixels))
    pixels.sort(key=score)
    return pixels


def write_bits(pixels, pixelList, bits):
    # Bit i goes into pixel number i // 3, color channel i % 3 (R, G, then B).
    for i, bit in enumerate(bits):
        pixel = pixelList[i // 3]
        channel = i % 3
        pixels[pixel, channel] = (pixels[pixel, channel] & 254) | bit


def read_bits(pixels, pixelList, count):
    bits = []
    for i in range(count):
        pixel = pixelList[i // 3]
        channel = i % 3
        bits.append(int(pixels[pixel, channel]) & 1)
    return bits


def read_salt(pixels):
    saltBits = read_bits(pixels, list(range(SALT_PIXELS)), SALT_SIZE * 8)
    return bits_to_bytes(saltBits)


def image_to_pixels(image):
    # Turn the image into a list of [R, G, B] rows, one row per pixel.
    if image.mode != 'RGB':
        raise ValueError("The image must be RGB.")
    return np.array(image, dtype=np.uint8).reshape(-1, 3)


def hide_message(image, message, password):
    pixels = image_to_pixels(image)
    width, height = image.size

    salt = get_random_bytes(SALT_SIZE)
    aesKey, orderKey = make_keys(password, salt)

    # AES-GCM encrypts the message and also makes a tag to catch changes.
    nonce = get_random_bytes(NONCE_SIZE)
    cipher = AES.new(aesKey, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))

    # The length goes first so the receiver knows when to stop reading.
    body = nonce + tag + ciphertext
    data = struct.pack('>I', len(body)) + body
    dataBits = bytes_to_bits(data)

    order = pixel_order(orderKey, len(pixels))
    if len(dataBits) > len(order) * 3:
        raise ValueError("The message is too large for this image.")

    write_bits(pixels, list(range(SALT_PIXELS)), bytes_to_bits(salt))
    write_bits(pixels, order, dataBits)
    return Image.fromarray(pixels.reshape(height, width, 3))


def reveal_message(image, password):
    pixels = image_to_pixels(image)

    salt = read_salt(pixels)
    aesKey, orderKey = make_keys(password, salt)
    order = pixel_order(orderKey, len(pixels))

    # Read the 4-byte length first. With a wrong password this is a random
    # number, so check it is possible before reading that many bytes.
    lengthBits = read_bits(pixels, order, LENGTH_SIZE * 8)
    bodyLength = struct.unpack('>I', bits_to_bytes(lengthBits))[0]
    maxBodyLength = len(order) * 3 // 8 - LENGTH_SIZE
    if bodyLength < NONCE_SIZE + TAG_SIZE or bodyLength > maxBodyLength:
        raise ValueError(REJECTED)

    dataBits = read_bits(pixels, order, (LENGTH_SIZE + bodyLength) * 8)
    body = bits_to_bytes(dataBits)[LENGTH_SIZE:]
    nonce = body[:NONCE_SIZE]
    tag = body[NONCE_SIZE:NONCE_SIZE + TAG_SIZE]
    ciphertext = body[NONCE_SIZE + TAG_SIZE:]

    # decrypt_and_verify raises ValueError if the tag does not match,
    # which happens with a wrong password or a changed image.
    cipher = AES.new(aesKey, AES.MODE_GCM, nonce=nonce)
    try:
        message = cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError:
        raise ValueError(REJECTED)
    return message.decode('utf-8')


def hidden_size(message):
    # Total bytes written into the image for a message of this length.
    return SALT_SIZE + LENGTH_SIZE + NONCE_SIZE + TAG_SIZE + len(message.encode('utf-8'))
