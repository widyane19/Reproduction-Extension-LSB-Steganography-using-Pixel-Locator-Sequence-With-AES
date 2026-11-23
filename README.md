# Improved LSB Steganography 
> Improvised LSB Steganography technique using Pixel Locator Sequence with AES

This is the implementation of our research paper based on <b>LSB Steganography</b> submitted at [Second International Conference on Cyber Computing and Communications](https://www.nitj.ac.in/icsccc2021/) arxiv preprint : [2012.02494](https://arxiv.org/abs/2012.02494).

## Development Setup

First-time setup, from the repository folder in the VS Code terminal:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For each run:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe reproduce.py
```

The reproduction script uses the five cover images in `images/`, embeds the
exact encrypted sample text printed in the paper, and checks that the ciphertext
and encrypted Pixel Locator Sequence can be recovered. It separately checks
that this repository's AES code can encrypt and decrypt the sample message.
It writes new images and a metrics CSV to `reproduction-results/` without
replacing the existing images. Enter the same throwaway demo password each time
to repeat the run; never use a real password.

The program prints the paper's values beside this run's values. Its MSE is the
mean squared difference across RGB channel values; the paper does not specify
how it combines color channels. The paper also does not give the random seed.
So the comparison is useful, but not a claim that every condition is identical.

All five images passed text/PLS recovery. The measured PSNR/MSE values differ
from the paper's; the cause of the gap is not established. The repository
images have the paper's listed dimensions, but their exact pixel-by-pixel
identity to the paper's sample images has not been verified. The paper's claim
that decoding is impossible without the PLS was not tested by this experiment.

## What is it all about ?

Image steganography is the art of hiding data into images. Secret data such as messages, audio, images can be hidden inside the cover image. This is mainly achieved by hiding the data into the LSB(Least Significant Bit) of the image pixels. To improve the security of steganography, we studied data encryption with AES(Advanced Encryption Standard) and LSB based data hiding technique with advanced user-defined encrypted data distribution in pixels other than the common linear computational method of storing data in a linear form. The pixel locater sequence will contain the location of the data(in form of pixel numbers) to be encrypted/decrypted which is further encrypted with AES thus providing double encryption for data and its location stored over pixels. Steganography has many applications such as medical, military, copyright information, etc.

<p align="center">
  <img width="250" height="300" src="images/sample_cmd/encryption.PNG">
  <br>
  Encrytion Procedure
</p>

<p align="center">
  <img width="250" height="300" src="images/sample_cmd/decryption.PNG">
  <br>
  Decryption Procedure
</p>

## Creators

<b>Sahil Gangurde</b> – [@lost_martian_](https://twitter.com/lost_martian_) – sahilgangurde08@gmail.com
<br>
<b>Krishnakant Tiwari</b> – [@Iamkkant](https://twitter.com/Iamkkant) – kkant5401@gmail.com

## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request
