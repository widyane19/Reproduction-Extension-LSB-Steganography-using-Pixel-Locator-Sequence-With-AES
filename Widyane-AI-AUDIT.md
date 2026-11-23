# AI_AUDIT— Team AI Verification Log

CS 4379H Cryptography, Fall 2026

**Team name / number:** Allen Eduardo Hernandez-Bas, Sid Singh, and Widyane Kasbi / Grp 6

**Paper:** LSB Steganography Using Pixel Locator Sequence with AES

**AI assistant(s) used (name and version, e.g., "ChatGPT (GPT-5), Claude (Sonnet 5)"):** Gemini (Flash3.6)

## How to use this log

AI use in this project is required, not banned. Every AI output your team relies on (a claim you repeat, a citation you include, code you commit, an idea you adopt) must appear here as one row, whether or not it turned out to be correct. You do not need to log throwaway drafts or outputs you discarded without using.

One log per team, kept in the root of your GitHub repository and updated as you work, not reconstructed at the end. Commit history should show it growing over the semester. The completeness and honesty of this log is graded under Project Code. Catching an AI error earns credit, hiding one costs it.

## Categories

| **Code** | **Category**                                                                                       |
| -------- | -------------------------------------------------------------------------------------------------- |
| FC       | Fabricated citation (paper, author, or venue that does not exist or does not say what was claimed) |
| NA       | Nonexistent API or function (library, method, flag, or parameter that does not exist)              |
| MR       | Misstated result (real source, but the number, finding, or claim is wrong)                         |
| CW       | Code runs but is wrong (executes without error, output is incorrect)                               |
| OC       | Overclaim (true in a narrow case, stated as general)                                               |
| OK       | Verified correct (the output survived verification)                                                |

## Log

_Role is one of: Reviewer, Archaeologist, Student Researcher, Reproducibility Checker, Quanta Correspondent. Add rows as needed._

| **#** | **Date** | **Role** | **What the AI claimed or produced (short quote or summary)** | **Category** | **Verified? (yes / no / partially)** | **How you checked it (source, test, experiment)** | **Team member** |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|


| 1 | 10/4/2026 | Quanta Correspondent | Suggestions of symmetric encryption algorithms to compare against AES | OK | yes | Researched the tools | Widyane Kasbi |

| 2 | 10/7/2026 | Reviewer | Produced an image for our quanta correspondence reflecting the process of LSB steganography with PLS and AES | OK | Yes | Compared it against the paper description of the process | Widyane Kasbi |

| 3 | 11/15/2026 | Reproducibility Checker | The AI’s first version mapped pixels incorrectly for non-square images | CW | yes | Checked with a 4×3 image test; corrected the mapping and added a test | Widyane Kasbi

| 4 | 11/21/2026 | Reproducibility Checker | The AI-assisted runner compares five images and checks text/PLS recovery | OK | yes | Four tests passed; all five images passed recovery; repeated outputs matched. The paper’s MSE/PSNR numbers still differ, and the cause is unresolved | Widyane Kasbi

| 5 | 11/22/2026 | Student Researcher | Compares repository AES-256 CTR with ChaCha20 and sequential with seeded-random PLS | OK | yes | Six tests passed; both ciphers recovered the message with equal output length; both PLS orders recovered the payload in all five images; tables saved in extension-results | Widyane Kasbi |

| 6 | 11/22/2026 | Student Researcher | Reorganized the extension into three security experiments: AES-CTR counter reuse, tamper detection compared with ChaCha20-Poly1305, and bounded recovery of a predictable PLS seed | OK | yes | Seven unit tests passed; terminal run reproduced all three findings and saved three CSV tables | Widyane Kasbi |


## End-of-semester summary (fill in before the final demo)

- Total AI outputs logged: \_**\_** Verified correct: \_**\_** Failed verification: \_**\_**
- The two most consequential AI failures (present these in Task 6, lessons learned):

Failure 1:

Failure 2:

- Which verification habit saved your team the most time?
