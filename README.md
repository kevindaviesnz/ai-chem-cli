# AI Chem-CLI (v1.8.5)

An agentic, multi-LLM command-line interface for retrosynthetic chemical planning. 

Traditional LLM wrappers struggle with complex organic chemistry, often hallucinating missing carbon sources or proposing reactions that destroy sensitive functional groups. AI Chem-CLI solves this using an **Adversarial Gatekeeper Architecture**, forcing the AI to validate and correct its own chemistry before outputting results.

## Key Features

* **RDKit Syntax Gating:** Extracts generated SMILES and strictly validates their structural integrity against RDKit. Drops pathways with impossible bonds or invalid syntax.
* **Target Identity Lock:** Canonicalizes the AI's proposed product SMILES and compares it strictly to the intended target SMILES to prevent mass-balance hallucinations (e.g., yielding a hydrolysis product instead of the target).
* **Adversarial Chemoselectivity Critic:** A hidden, secondary LLM call acts as a critic, evaluating surviving pathways for cross-reactivity and functional group compatibility (e.g., flagging the use of harsh bases on conjugated enones).
* **Self-Correction Loop:** When the Gatekeeper catches an error, the specific chemical critique is appended to a retry prompt, forcing the generator to fix its own chemistry iteratively.
* **Complexity Alerts:** Automatically warns the user if the requested target exceeds standard zero-shot context capabilities (>250 g/mol or >4 stereocenters).

## Installation

Ensure you have Python 3.x installed. The application uses a `Makefile` to cleanly package the CLI using PyInstaller.

1. Install dependencies:
   `pip install -r requirements.txt`
2. Build the binary:
   `make clean && make install`
3. Export your Google Gemini API Key:
   `export GEMINI_API_KEY="your_api_key_here"`

## Usage

**Retrosynthetic Planning:**
Run a retrosynthetic breakdown for a target molecule. You can save the output as an HTML or PDF report.

`chem-cli -p "procaine" -d 1 --nocache -o procaine.html`

**Forward Reaction Simulation:**
Simulate the major product of specific reactants.

`chem-cli -s -r "ClC(=O)c1ccc(N)cc1, OCCN(CC)CC"`

## License
This project is licensed under a custom Non-Commercial License. See the `LICENSE` file for details. Commercial use is strictly prohibited without explicit permission.