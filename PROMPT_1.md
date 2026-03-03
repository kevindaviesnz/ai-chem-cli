Role & Context: > Act as an expert Python developer and computational chemist. Your task is to develop a command-line interface (CLI) application named chem that performs chemical calculations, reaction simulations, and synthesis planning.
Core Requirements:
Tech Stack: Use Python. Use argparse or Click for the Unix-style CLI framework. Use RDKit for deterministic chemical parsing (e.g., validating SMILES strings, calculating molar mass).
AI Integration: Integrate the litellm library (or similar) so the user can dynamically switch between major AI models (e.g., OpenAI, Anthropic, Gemini, open-source via Ollama) using an environment variable or a CLI switch (e.g., --model gpt-4o). The AI should be used to predict reaction outcomes or suggest synthesis pathways when deterministic methods aren't enough.
CLI Design: It must work like a standard Unix command. Required switches to implement:
-r, --reactants [list of reactants]: Parse inputs (names or SMILES).
-s, --simulate: Simulate the reaction between provided reactants and output the predicted products.
-p, --pathway [target molecule]: Propose a chemical synthesis pathway for the target.
-m, --model [model_name]: Specify the AI model to handle complex generative tasks.
Error Handling: Include elegant error handling for invalid chemical inputs or missing API keys.
Deliverable Format:
Since you cannot output a raw .zip file directly, provide a complete, executable bash script. When I run this script on my local machine, it must:
Create the necessary directory structure for the app.
Write all the required Python source code files (main.py, chem_utils.py, ai_router.py, requirements.txt) into those directories.
Bundle the entire directory into a file named chem_cli_app.zip.