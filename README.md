# Group 6 Project: LSB Steganography Reproduction and Security Extension

**Team:** Allen Eduardo Hernandez-Bas, Sid Singh, and Widyane Kasbi<br>
**Course:** CS 4379H Cryptography, Fall 2026<br>
**Paper:** [LSB Steganography Using Pixel Locator Sequence with AES](https://arxiv.org/abs/2012.02494)

## What we did

- **Reproduction:** Ran the paper's sample ciphertext and Pixel Locator Sequence (PLS) through five cover images. Checked recovery and compared our image MSE/PSNR measurements with the paper's reported values.
- **Security extension:** Tested AES-CTR counter reuse, compared AES-CTR with ChaCha20-Poly1305 when ciphertext is changed, and tested sequential extraction versus searching a small PLS seed range.

## Project files

- `reproduce.py` runs the five-image reproduction, checks message and PLS recovery, calculates MSE/PSNR, and saves output images and a results CSV.
- `test_reproduction.py` checks PLS repeatability, embedding and extraction, pixel mapping, and payload-size handling.
- `extension.py` runs the three security experiments, prints comparison tables and findings, and saves their CSV results.
- `test_extension.py` checks the expected result of each security experiment.
- `reproduction-results/` and `extension-results/` contain generated images and result tables from runs.
- `Widyane-AI-AUDIT.md` records AI assistance used for the project.

## Run the project

From the repository folder in PowerShell, create the environment and install dependencies once:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the tests, reproduction, and extension:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe reproduce.py
.\.venv\Scripts\python.exe extension.py
```

The reproduction and extension scripts prompt for a password. Use the same throwaway demo password when you want consistent runs; do not enter a real password. The paper's MSE/PSNR values are stored as comparison baselines, while this run's metrics and experiment outcomes are calculated when the scripts execute. The extension's PLS search is a bounded demonstration using a known payload; it does not test recovery of the paper's AES-encrypted PLS.

## Scholarly References

- **Foundational research:** Thangadurai and Devi analyze LSB-based image steganography techniques, providing background for the LSB method used in this project [1].
- **Contemporary related work:** Kumar and Maiti present a later PLS-and-AES method that adds cryptographically secure sequence generation and key exchange, providing a technical comparison to this paper [2].


[1] K. Thangadurai and G. S. Devi, "An analysis of LSB based image steganography techniques," in *2014 International Conference on Computer Communication and Informatics*, Coimbatore, India, 2014, pp. 1-4, doi: [10.1109/ICCCI.2014.6921751](https://doi.org/10.1109/ICCCI.2014.6921751).

[2] S. Kumar and S. Maiti, "Improving Security of LSB Image Steganography for Pixel Locator Sequence Using Cryptographic Techniques with AES," in *2025 IEEE International Conference on Computer Vision and Machine Intelligence (CVMI)*, Rourkela, India, 2025, pp. 1-6, doi: [10.1109/CVMI66673.2025.11337562](https://doi.org/10.1109/CVMI66673.2025.11337562).

---

## Original repository README

The following repository description and illustrations are retained from the original README. Use the setup and run commands in the Group 6 section above for this project checkout.

# Improved LSB Steganography

> Improvised LSB Steganography technique using Pixel Locator Sequence with AES

This is the implementation of our research paper based on <b>LSB Steganography</b> submitted at [Second International Conference on Cyber Computing and Communications](https://www.nitj.ac.in/icsccc2021/) arxiv preprint: [2012.02494](https://arxiv.org/abs/2012.02494).

## Original Development Setup

The original repository instructions were:

```sh
pip3 install Pillow pyaes hashlib numpy Cryptodome pbkdf2 binascii
git clone https://github.com/lostmartian/Improved-LSB-Steganography.git
python3 main.py
```

## What is it all about?

Image steganography hides data, such as messages, audio, or images, inside a cover image. Least Significant Bit (LSB) methods hide data in the least significant bits of image pixels. This project combines LSB data hiding with AES encryption and a Pixel Locator Sequence (PLS) that specifies where data is embedded and recovered.

<p align="center">
  <img width="250" height="300" src="images/sample_cmd/encryption.PNG">
  <br>
  Encryption Procedure
</p>

<p align="center">
  <img width="250" height="300" src="images/sample_cmd/decryption.PNG">
  <br>
  Decryption Procedure
</p>

## Original repository creators

<b>Sahil Gangurde</b> – [@lost_martian_](https://twitter.com/lost_martian_) – sahilgangurde08@gmail.com<br>
<b>Krishnakant Tiwari</b> – [@Iamkkant](https://twitter.com/Iamkkant) – kkant5401@gmail.com

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/fooBar`).
3. Commit your changes (`git commit -am 'Add some fooBar'`).
4. Push to the branch (`git push origin feature/fooBar`).
5. Create a pull request.
