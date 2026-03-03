#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

APP_DIR="chem_cli_app"
ZIP_NAME="chem_cli_app.zip"

echo "Creating directory structure for $APP_DIR..."
mkdir -p "$APP_DIR"

# ==========================================
# 1. Generate requirements.txt
# ==========================================
echo "Writing requirements.txt..."
cat << 'EOF' > "$APP_DIR/requirements.txt"
click==8.1.7
rdkit==2023.9.5
litellm==1.35.35
python-dotenv==1.0.1
EOF

# ==========================================
# 2. Generate chem_utils.py (Deterministic RDKit logic)
# ==========================================
echo "Writing chem_utils.py..."
cat << 'EOF' > "$APP_DIR/chem_utils.py"
from rdkit import Chem
from rdkit.Chem import Descriptors

def validate_smiles(smiles: str) -> bool:
    """Validates a SMILES string using RDKit."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")
    return True

def get_molar_mass(smiles: str) -> float:
    """Calculates the exact molar mass of a molecule from its SMILES."""
    mol = Chem.MolFromSmiles(smiles)
    if mol:
        return Descriptors.ExactMolWt(mol)
    return 0.0
EOF

# ==========================================
# 3. Generate ai_router.py (LiteLLM Integration)
# ==========================================
echo "Writing ai_router.py..."
cat << 'EOF' > "$APP_DIR/ai_router.py"
import os
from litellm import completion

def predict_reaction(reactants: list, model: str) -> str:
    """Predicts reaction outcomes using the specified AI model."""
    prompt = (
        f"Act as an expert computational chemist. Predict the major products of the reaction "
        f"between the following reactants: {', '.join(reactants)}. "
        f"Provide the predicted product SMILES and a brief mechanistic explanation."
    )
    return _call_llm(prompt, model)

def propose_pathway(target: str, model: str) -> str:
    """Proposes a synthesis pathway using the specified AI model."""
    prompt = (
        f"Act as an expert computational chemist. Propose a high-yield retrosynthetic "
        f"pathway for the target molecule: {target}. "
        f"Include reagents, reaction conditions, and intermediate chemical names or SMILES."
    )
    return _call_llm(prompt, model)

def _call_llm(prompt: str, model: str) -> str:
    """Handles the LiteLLM routing and basic error handling."""
    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return (
            f"\n[!] AI Request Failed: {str(e)}\n"
            f"Ensure you have set the appropriate environment variable for the model "
            f"(e.g., OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY)."
        )
EOF

# ==========================================
# 4. Generate main.py (Click CLI interface)
# ==========================================
echo "Writing main.py..."
cat << 'EOF' > "$APP_DIR/main.py"
import click
import sys
from chem_utils import validate_smiles, get_molar_mass
from ai_router import predict_reaction, propose_pathway

@click.command()
@click.option('-r', '--reactants', multiple=True, help="Reactants for the simulation (names or SMILES). Use multiple times for multiple reactants.")
@click.option('-s', '--simulate', is_flag=True, help="Simulate the reaction between provided reactants.")
@click.option('-p', '--pathway', help="Target molecule to propose a synthesis pathway for.")
@click.option('-m', '--model', default="gpt-4o", help="Specify the AI model to handle generative tasks (default: gpt-4o).")
def cli(reactants, simulate, pathway, model):
    """Chem CLI: Chemical calculations, simulation, and synthesis planning."""
    
    if not simulate and not pathway:
        click.echo("Error: Please provide an action. Use --help for options.")
        sys.exit(1)

    # Reaction Simulation Logic
    if simulate:
        if not reactants:
            click.echo("Error: --simulate requires at least one --reactants (-r).")
            sys.exit(1)
            
        click.echo(click.style("Validating inputs...", fg="blue"))
        for r in reactants:
            # Simple heuristic to guess if input is SMILES
            if any(c in r for c in ['=', '#', '(', ')']):
                try:
                    validate_smiles(r)
                    mass = get_molar_mass(r)
                    click.echo(f"  [✓] Valid SMILES detected: {r} (Mass: {mass:.2f} g/mol)")
                except ValueError:
                    click.echo(f"  [!] Warning: '{r}' does not appear to be a valid SMILES. Treating as a common name.")
            else:
                 click.echo(f"  [-] Treating '{r}' as a chemical name.")
                 
        click.echo(click.style(f"\nSimulating reaction using model: {model}...\n", fg="green", bold=True))
        result = predict_reaction(reactants, model=model)
        click.echo(result)

    # Synthesis Pathway Logic
    if pathway:
        click.echo(click.style(f"\nProposing synthesis pathway for '{pathway}' using model: {model}...\n", fg="green", bold=True))
        result = propose_pathway(pathway, model=model)
        click.echo(result)

if __name__ == '__main__':
    cli()
EOF

# ==========================================
# 5. Zip the directory
# ==========================================
echo "Zipping the application into $ZIP_NAME..."
zip -r "$ZIP_NAME" "$APP_DIR" > /dev/null

echo "===================================================="
echo "Done! The application has been built and zipped."
echo "You can now extract $ZIP_NAME and run it."
echo "Example usage:"
echo "  cd $APP_DIR"
echo "  pip install -r requirements.txt"
echo "  export OPENAI_API_KEY='your-key-here'"
echo "  python main.py -r 'c1ccccc1' -r 'Br2' --simulate -m gpt-4o"
echo "===================================================="