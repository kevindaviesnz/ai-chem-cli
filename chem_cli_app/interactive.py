import sys
import os
import json
import requests
from urllib.parse import quote
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger
import ai_router
from state import State, Step

# Suppress RDKit terminal spam for invalid SMILES attempts
RDLogger.DisableLog('rdApp.*')

class ChemSession:
    def __init__(self):
        self.state = State()
        self.use_cache = True  # Caching enabled by default

    def start(self):
        """Initializes the REPL loop for Interactive Mode."""
        print("chem-cli interactive mode (v2.0-dev). Type 'help' for commands.")
        while True:
            try:
                cmd_line = input("> ").strip()
                if not cmd_line:
                    continue
                self.execute(cmd_line)
            except (KeyboardInterrupt, EOFError):
                print("\nExiting session...")
                break  # <--- Graceful exit fix applied here

    def execute(self, cmd_line):
        """Parses and routes user input to the appropriate command logic."""
        parts = cmd_line.split(" ", 1)
        base_cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Handle explicit multi-word commands first
        if cmd_line.lower().startswith("react with "):
            self.cmd_react_with(cmd_line[11:].strip())
            return
            
        if cmd_line.lower().startswith("deprotect"):
            self.cmd_deprotect(cmd_line[9:].strip())
            return

        if cmd_line.lower().startswith("methylate"):
            self.cmd_methylate(cmd_line[9:].strip())
            return
        
        if cmd_line.lower().startswith("set quantity "):
            self.cmd_set_quantity(cmd_line[13:].strip())
            return
            
        if cmd_line.lower().startswith("set cache "):
            self.cmd_set_cache(cmd_line[10:].strip())
            return

        # Route standard single-word commands
        if base_cmd == "load":
            self.cmd_load(args)
        elif base_cmd == "show":
            self.cmd_show()
        elif base_cmd == "analyse":
            self.cmd_analyse(args)
        elif base_cmd == "history":
            self.cmd_history()
        elif base_cmd == "undo":
            self.cmd_undo()
        elif base_cmd == "redo":
            self.cmd_redo()
        elif base_cmd == "save":
            self.cmd_save(args)
        elif base_cmd == "resume":
            self.cmd_resume(args)
        elif base_cmd in ["exit", "quit"]:
            self.cmd_exit()
        elif base_cmd == "help":
            self.cmd_help()
        else:
            print(f"Unknown command: '{base_cmd}'. Type 'help' for a list of commands.")

    def _record_step(self, raw_cmd: str, smiles_before: str, smiles_after: str, gatekeeper_log: list = None):
        """Helper to append a completed action to the history and clear the redo stack."""
        step = Step(
            command=raw_cmd,
            smiles_before=smiles_before,
            smiles_after=smiles_after,
            gatekeeper_log=gatekeeper_log or [],
            quantities_snapshot=self.state.quantities.copy()
        )
        self.state.history.append(step)
        self.state.redo_stack.clear() 

    def cmd_set_cache(self, args):
        val = args.lower()
        if val in ['on', 'true', '1']:
            self.use_cache = True
            print("✓ AI caching enabled.")
        elif val in ['off', 'false', '0']:
            self.use_cache = False
            print("✓ AI caching disabled.")
        else:
            print("Usage: set cache <on|off>")

    def cmd_load(self, args):
        if not args:
            print("Usage: load <molecule>")
            return
            
        print(f"Resolving '{args}'...")
        smiles = None
        
        mol = Chem.MolFromSmiles(args)
        if mol:
            smiles = Chem.MolToSmiles(mol, isomericSmiles=True)
        else:
            try:
                url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(args)}/property/IsomericSMILES,CanonicalSMILES,SMILES/JSON"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    props = data.get('PropertyTable', {}).get('Properties', [])
                    if props:
                        smiles = props[0].get('IsomericSMILES') or \
                                 props[0].get('CanonicalSMILES') or \
                                 props[0].get('SMILES')
            except Exception as e:
                print(f"[!] Network error: {e}")
                return
                
        if not smiles:
            print(f"[!] Error: Could not resolve '{args}'.")
            return
            
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            print(f"[!] Error: Invalid SMILES: {smiles}")
            return
            
        smiles_before = self.state.working_smiles
        self.state.working_smiles = smiles
        self.state.target_smiles = smiles
        self.state.quantities = {}
        
        self._record_step(f"load {args}", smiles_before, self.state.working_smiles, [f"Resolved to {smiles}"])
        print(f"✓ Loaded: {self.state.working_smiles}")

    def cmd_set_quantity(self, args):
        if not self.state.working_smiles:
            print("No working structure loaded.")
            return
        parts = args.split()
        if len(parts) != 2:
            print("Usage: set quantity <value> <unit>")
            return
        try:
            val = float(parts[0])
            unit = parts[1]
            self.state.quantities = {"value": val, "unit": unit}
            self._record_step(f"set quantity {args}", self.state.working_smiles, self.state.working_smiles)
            print(f"✓ Target scale set to {val} {unit}")
        except ValueError:
            print("Invalid quantity value.")

    def cmd_show(self):
        if not self.state.working_smiles:
            print("No working structure loaded.")
            return
        print(f"\nCurrent structure: {self.state.working_smiles}")
        mol = Chem.MolFromSmiles(self.state.working_smiles)
        if mol:
            formula = rdMolDescriptors.CalcMolFormula(mol)
            mw = Descriptors.ExactMolWt(mol)
            print(f"Formula:           {formula}")
            print(f"Molecular Wt:      {mw:.2f} g/mol")
        if self.state.quantities:
            val = self.state.quantities.get('value')
            unit = self.state.quantities.get('unit')
            print(f"Target Scale:      {val} {unit}")
        else:
            print("Target Scale:      Not set")
        print("")

    def cmd_react_with(self, reagent):
        if not self.state.working_smiles:
            print("No working structure loaded.")
            return
        print(f"🧪 Simulating: {self.state.working_smiles} + {reagent}")
        reactants_list = [self.state.working_smiles, reagent]
        try:
            success, new_smiles, logs = ai_router.predict_reaction_interactive(
                reactants=reactants_list,
                model="gemini/gemini-2.5-flash",
                nocache=not self.use_cache
            )
            if success and new_smiles:
                smiles_before = self.state.working_smiles
                self.state.working_smiles = new_smiles
                self._record_step(f"react with {reagent}", smiles_before, new_smiles, logs)
                print(f"✓ Reaction successful! Product: {self.state.working_smiles}")
            else:
                print("[!] Gatekeeper rejected reaction.")
                if logs:
                    for log in logs:
                        print(f"  - {log}")
        except Exception as e:
            print(f"[!] Simulation Error: {e}")

    def cmd_deprotect(self, args):
        if not self.state.working_smiles:
            print("No working structure loaded.")
            return
            
        reagents = args if args else "appropriate deprotection reagents"
        
        print(f"🔓 Simulating deprotection: {self.state.working_smiles} using {reagents}")
        reactants_list = [self.state.working_smiles, reagents]
        try:
            success, new_smiles, logs = ai_router.predict_reaction_interactive(
                reactants=reactants_list,
                model="gemini/gemini-2.5-flash",
                nocache=not self.use_cache
            )
            if success and new_smiles:
                smiles_before = self.state.working_smiles
                self.state.working_smiles = new_smiles
                
                logged_cmd = f"deprotect {args}" if args else "deprotect"
                self._record_step(logged_cmd, smiles_before, new_smiles, logs)
                
                print(f"✓ Deprotection successful! Product: {self.state.working_smiles}")
            else:
                print("[!] Gatekeeper rejected deprotection.")
                if logs:
                    for log in logs:
                        print(f"  - {log}")
        except Exception as e:
            print(f"[!] Simulation Error: {e}")

    def cmd_methylate(self, args):
        if not self.state.working_smiles:
            print("No working structure loaded.")
            return
            
        reagents = args if args else "MeI, K2CO3"
        print(f"📍 Simulating regioselective methylation: {self.state.working_smiles} using {reagents}")
        reactants_list = [self.state.working_smiles, reagents]
        try:
            success, new_smiles, logs = ai_router.predict_reaction_interactive(
                reactants=reactants_list,
                model="gemini/gemini-2.5-flash",
                nocache=not self.use_cache
            )
            if success and new_smiles:
                smiles_before = self.state.working_smiles
                self.state.working_smiles = new_smiles
                
                logged_cmd = f"methylate {args}" if args else "methylate"
                self._record_step(logged_cmd, smiles_before, new_smiles, logs)
                
                print(f"✓ Methylation successful! Product: {self.state.working_smiles}")
            else:
                print("[!] Gatekeeper rejected methylation.")
                if logs:
                    for log in logs:
                        print(f"  - {log}")
        except Exception as e:
            print(f"[!] Simulation Error: {e}")

    def cmd_analyse(self, args):
        if not self.state.working_smiles:
            print("No working structure loaded.")
            return
        depth = 1
        if args:
            try:
                depth = int(args.split()[0])
            except ValueError:
                depth = 1
        print(f"🔬 Analyzing retrosynthetic pathways for: {self.state.working_smiles} (Depth: {depth})")
        ai_router.propose_pathway(
            target=self.state.working_smiles,
            target_smiles=self.state.working_smiles,
            depth=depth,
            model="gemini/gemini-2.5-flash",
            nocache=not self.use_cache,
            print_output=True
        )

    def cmd_history(self):
        if not self.state.history:
            print("History is empty.")
            return
        print("\n--- Session History ---")
        for i, step in enumerate(self.state.history, 1):
            print(f"{i}. {step.command}")
        print("-----------------------\n")

    def cmd_undo(self):
        if not self.state.history:
            print("Nothing to undo.")
            return
        last_step = self.state.history.pop()
        self.state.redo_stack.append(last_step)
        self.state.working_smiles = last_step.smiles_before
        if self.state.history:
            self.state.quantities = self.state.history[-1].quantities_snapshot.copy()
        else:
            self.state.quantities = {}
        print(f"✓ Undid command: '{last_step.command}'")

    def cmd_redo(self):
        if not self.state.redo_stack:
            print("Nothing to redo.")
            return
        next_step = self.state.redo_stack.pop()
        self.state.history.append(next_step)
        self.state.working_smiles = next_step.smiles_after
        self.state.quantities = next_step.quantities_snapshot.copy()
        print(f"✓ Redid command: '{next_step.command}'")

    def cmd_save(self, args):
        filename = args if args else None
        saved_to = self.state.save_session(filename)
        print(f"✓ Session saved to {saved_to}")

    def cmd_resume(self, args):
        if not args:
            print("Usage: resume <filename.json>")
            return
        
        filename = args.strip()
        if not os.path.exists(filename):
            print(f"[!] Error: File '{filename}' not found.")
            return
            
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            self.state.working_smiles = data.get("working_smiles", "")
            self.state.target_smiles = data.get("target_smiles", "")
            self.state.quantities = data.get("quantities", {})
            
            # Reconstruct the history stack
            self.state.history = []
            for step_data in data.get("history", []):
                step = Step(
                    command=step_data.get("command", ""),
                    smiles_before=step_data.get("smiles_before", ""),
                    smiles_after=step_data.get("smiles_after", ""),
                    gatekeeper_log=step_data.get("gatekeeper_log", []),
                    quantities_snapshot=step_data.get("quantities_snapshot", {})
                )
                self.state.history.append(step)
                
            # Reconstruct the redo stack
            self.state.redo_stack = []
            for step_data in data.get("redo_stack", []):
                step = Step(
                    command=step_data.get("command", ""),
                    smiles_before=step_data.get("smiles_before", ""),
                    smiles_after=step_data.get("smiles_after", ""),
                    gatekeeper_log=step_data.get("gatekeeper_log", []),
                    quantities_snapshot=step_data.get("quantities_snapshot", {})
                )
                self.state.redo_stack.append(step)
                
            print(f"✓ Session resumed from {filename}")
            print(f"Current structure: {self.state.working_smiles}")
            
        except Exception as e:
            print(f"[!] Error loading session: {e}")

    def cmd_help(self):
        print("\nAvailable Commands:")
        print("  load <molecule>            - Set working structure")
        print("  set quantity <val> <unit>  - Set target scale")
        print("  set cache <on/off>         - Toggle AI response caching")
        print("  show                       - Display current structure and scale")
        print("  react with <reagent>       - Forward reaction simulation")
        print("  deprotect [conditions]     - Orthogonal deprotection (auto-detects if left blank)")
        print("  methylate [reagents]       - Regioselective methylation (defaults to MeI, K2CO3)")
        print("  analyse [depth]            - Retrosynthetic analysis")
        print("  history                    - Show session steps")
        print("  undo                       - Revert last step")
        print("  redo                       - Reapply undone step")
        print("  save [filename]            - Save session state")
        print("  resume <filename>          - Load a previously saved session")
        print("  exit                       - End the session\n")

    def cmd_exit(self):
        print("Exiting interactive mode. Goodbye!")
        sys.exit(0)

def start_interactive():
    session = ChemSession()
    session.start()

if __name__ == "__main__":
    start_interactive()