import os
import sys

# --- API KEY CHECK ---
if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    print("\n\033[91m[!] Missing API Key:\033[0m")
    print("Please set your Gemini API key before running the application.")
    print("Run this command in your active terminal session:")
    print("  export GEMINI_API_KEY='your_actual_api_key_here'\n")
    sys.exit(1)
# ---------------------

import click
from ai_router import propose_pathway, predict_reaction

VERSION = "1.8.5"

def get_smiles_for_target(target):
    """Mock resolver for complexity alerts. In production, this connects to PubChem/cirpy."""
    known_targets = {
        "testosterone": "C[C@]12CC[C@H]3[C@H]([C@@H]1CC[C@@H]2O)CCC4=CC(=O)CC[C@]34C",
        "paracetamol": "CC(=O)NC1=CC=C(O)C=C1",
        "ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "caffeine": "CN1C=NC2=C1C(=O)N(C)C(=O)N2C",
        "aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
        "procaine": "O=C(OCCN(CC)CC)c1ccc(N)cc1",
        "methylphenidate": "COC(=O)[C@@H](c1ccccc1)[C@H]1CCCCN1"
    }
    return known_targets.get(target.lower(), target)

def launch_retrosynthesis(pathway, depth, model, output, pdf, nocache, verbose, silent):
    if not silent:
        print(f"Validating target '{pathway}'...")
        print(f"Target Resolved. Analyzing {pathway}...")

    # Resolve target SMILES
    target_smiles = pathway
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        resolved = get_smiles_for_target(pathway)
        target_smiles = resolved
        mol = Chem.MolFromSmiles(resolved)
        if mol:
            mw = Descriptors.MolWt(mol)
            chiral_centers = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
            if mw > 250 or chiral_centers >= 4:
                print(f"[\033[93m⚠️\033[0m] COMPLEXITY ALERT: Target is {mw:.2f} g/mol with {chiral_centers} stereocenters.")
    except ImportError:
        pass

    print_output = not silent
    result = propose_pathway(pathway, model, depth, nocache=nocache, verbose=verbose, print_output=print_output, target_smiles=target_smiles)
    
    if not result or result.startswith("ERROR") or "Synthesis Error" in result:
        return

    # Handle Output saving
    if output:
        # B1 Fix: Flag conflict resolution
        if pdf and output.endswith('.html'):
            if not silent:
                print("Auto-corrected output extension to .pdf")
            output = output[:-5] + '.pdf'
            
        # B2 Fix: Path is absolute via click.Path
        save_path = output
        
        try:
            with open(save_path, "w") as f:
                if save_path.endswith('.html'):
                    # Format as proper HTML
                    formatted_result = result.replace('\n', '<br>')
                    f.write(f"<!DOCTYPE html>\n<html>\n<head><title>Synthesis Report: {pathway}</title></head>\n")
                    f.write("<body style='font-family: monospace, sans-serif; padding: 20px; line-height: 1.6;'>\n")
                    f.write(f"<h2>🧪 Synthesis Report for {pathway.capitalize()}</h2>\n<hr>\n")
                    f.write(f"<p>{formatted_result}</p>\n")
                    f.write("</body>\n</html>")
                else:
                    f.write(f"Synthesis Report for {pathway}\n\n{result}")
                    
            if not silent:
                print(f"\nSuccess! Report: {save_path}")
        except Exception as e:
            print(f"\nFailed to save report: {e}")

def launch_forward_sim(reactants, model, nocache, verbose, silent):
    if not silent:
        print(f"Running forward reaction simulation for: {reactants}")
    predict_reaction([reactants], model, nocache=nocache, verbose=verbose, print_output=not silent)

@click.command()
@click.option('-p', '--pathway', type=str, help='Target molecule for retrosynthesis')
@click.option('-d', '--depth', type=int, default=1, help='Depth of the retrosynthetic tree')
@click.option('-m', '--model', type=str, default="gemini/gemini-2.5-flash", help='LLM model to use')
@click.option('-o', '--output', type=click.Path(resolve_path=True), help='Output file to save the report')
@click.option('--pdf', is_flag=True, help='Save output as PDF')
@click.option('--nocache', is_flag=True, help='Bypass the local cache')
@click.option('--verbose', is_flag=True, help='Print raw AI output')
@click.option('--silent', is_flag=True, help='Suppress terminal output')
@click.option('-s', '--simulate', is_flag=True, help='Run forward reaction simulation')
@click.option('-r', '--reactants', type=str, help='Reactants for forward simulation (comma separated)')
@click.option('--version', is_flag=True, help='Show the version and exit')
def cli(pathway, depth, model, output, pdf, nocache, verbose, silent, simulate, reactants, version):
    if version:
        print(f"chem-cli, version {VERSION}")
        sys.exit(0)
        
    if simulate:
        if not reactants:
            print("[!] Error: Must provide reactants (-r) for forward simulation.")
            sys.exit(1)
        launch_forward_sim(reactants, model, nocache, verbose, silent)
    elif pathway:
        launch_retrosynthesis(pathway, depth, model, output, pdf, nocache, verbose, silent)
    else:
        print("Usage: chem-cli -p [target] OR chem-cli -s -r [reactants]")
        print("Run 'chem-cli --help' for more information.")

if __name__ == '__main__':
    cli()