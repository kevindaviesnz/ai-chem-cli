import sys
import os
import json
import hashlib
import warnings
import contextlib
import io
import re
import litellm
from litellm import completion
from rdkit import Chem
from rdkit import RDLogger

RDLogger.DisableLog('rdApp.*')

# Suppress LiteLLM's internal terminal spam
litellm.suppress_debug_info = True
litellm.set_verbose = False

CACHE_DIR = os.path.expanduser("~/.chem-cli")
CACHE_FILE = os.path.join(CACHE_DIR, "cache.json")

def _get_cache(key: str) -> str:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        return cache.get(key)
    except Exception:
        return None

def _set_cache(key: str, value: str):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        except Exception:
            pass
    cache[key] = value
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass

def _call_llm(prompt: str, model: str, nocache: bool = False, verbose: bool = False, print_output: bool = True, timeout: int = 45, suppress_errors: bool = False) -> str:
    cache_key = hashlib.md5(f"{model}_{prompt}".encode('utf-8')).hexdigest()
    
    if not nocache:
        cached_response = _get_cache(cache_key)
        if cached_response:
            if print_output:
                display_result(cached_response, verbose, print_output)
            return cached_response

    warnings.filterwarnings("ignore", category=FutureWarning)
    
    try:
        # Swallow stdout/stderr to hide LiteLLM's debug prints on timeouts
        f = io.StringIO()
        with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            response = completion(
                model=model, 
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout
            )
        result = response.choices[0].message.content.strip()
        
        if not nocache:
            _set_cache(cache_key, result)
        
        if print_output:
            display_result(result, verbose, print_output)
        return result
    
    except Exception as e:
        raw_err = str(e).strip()
        err_msg = raw_err.split('\n')[0] if raw_err else repr(e)
        
        if not suppress_errors:
            print(f"\n\033[91m[!] API ERROR:\033[0m {err_msg}")
            sys.exit(1)
        return None

def display_result(text, verbose, print_output):
    if verbose:
        print(f"\n--- RAW AI OUTPUT ---\n{text}\n---------------------")
    elif print_output:
        lines = text.split('\n')
        print("\n" + "=" * 60)
        print("🧪 AI Analysis Complete.") 
        print("Summary of Pathways Identified:")
        
        count = 0
        valid_prefixes = ["RELATION:", "CONVERGENT:", "REACTION:", "STEP:"]
        
        for line in lines:
            clean_line = line.strip()
            prefix = next((p for p in valid_prefixes if clean_line.startswith(p) or p in clean_line), None)
            
            if prefix:
                parts = clean_line.split(prefix, 1)
                if len(parts) > 1:
                    print(f"  • {parts[1].strip()}")
                    count += 1
                        
        if count == 0:
            for line in lines:
                if "->" in line and "[" in line:
                     print(f"  • {line.strip()}")
                     count += 1
            
        if count == 0:
            print("  (See full report for detailed synthesis narrative)")
        print("=" * 60 + "\n")

def validate_pathway_logic(raw_output: str, target: str, target_smiles: str, model: str, nocache: bool):
    """The Gatekeeper: Returns valid pathways and a list of errors for the retry loop."""
    if not raw_output:
        err = "AI returned an empty response. (Possible generation failure)"
        print(f"  \033[93m[🚧] Gatekeeper dropped pathway: {err}\033[0m")
        return "", [err]
        
    pathways = []
    for line in raw_output.split('\n'):
        if "RELATION:" in line or "->" in line:
            pathways.append(line.strip())

    if not pathways:
        err = "Output formatting failed. No 'RELATION:' tags found."
        print(f"  \033[93m[🚧] Gatekeeper dropped pathway: {err}\033[0m")
        return "", [err]

    valid_pathways = []
    errors = []
    
    for pathway in pathways:
        reaction_core = pathway.split("using")[0] if "using" in pathway else pathway
        
        # 1. RDKit Syntax Check
        tokens = re.split(r'\s+|\+|\->', reaction_core.replace("RELATION:", ""))
        rdkit_pass = True
        for token in tokens:
            clean_smi = token.strip('[]`*:,.')
            if not clean_smi or (clean_smi.isalpha() and len(clean_smi) > 2): continue
                
            if Chem.MolFromSmiles(clean_smi) is None:
                if any(c in clean_smi for c in "=@#()[]1234567890+-"):
                    rdkit_pass = False
                    err_msg = f"Invalid SMILES structure generated: '{clean_smi}'"
                    print(f"  \033[93m[🚧] Gatekeeper dropped pathway: {err_msg}\033[0m")
                    errors.append(err_msg)
                    break
        
        if not rdkit_pass: continue

        # 2. Strict Target Identity Match
        target_match_pass = True
        if "->" in reaction_core and target_smiles and Chem.MolFromSmiles(target_smiles):
            try:
                product_side = reaction_core.split("->")[1]
                prod_tokens = re.split(r'\s+|\+', product_side)
                product_smi = None
                
                for token in prod_tokens:
                    clean = token.strip('[]`*:,.')
                    if Chem.MolFromSmiles(clean):
                        product_smi = clean
                        break
                        
                if product_smi:
                    target_mol = Chem.MolFromSmiles(target_smiles)
                    prod_mol = Chem.MolFromSmiles(product_smi)
                    can_target = Chem.MolToSmiles(target_mol, isomericSmiles=True)
                    can_prod = Chem.MolToSmiles(prod_mol, isomericSmiles=True)
                    
                    if can_target != can_prod:
                        target_match_pass = False
                        err_msg = f"Target identity mismatch: Product is {can_prod} but required target is {can_target}"
                        print(f"  \033[93m[🚧] Gatekeeper dropped pathway: {err_msg}\033[0m")
                        errors.append(err_msg)
            except Exception:
                pass
                
        if not target_match_pass: continue

        # 3. Adversarial Chemoselectivity Check
        critic_prompt = (
            f"You are an adversarial Chemoselectivity Validator.\n"
            f"Evaluate this proposed reaction: {pathway}\n"
            f"Target molecule: {target} (SMILES: {target_smiles})\n"
            f"Check for:\n"
            f"1. Cross-reactivity & Incompatibilities: e.g., using strong acids (like refluxing H2SO4) on free aromatic amines risks sulfonation.\n"
            f"2. Stereoselective Feasibility: If the target has specific stereocenters, ensure the proposed reagents can actually achieve that specific diastereomer. (e.g., heterogeneous Ru/C hydrogenation of a pyridine ring cannot selectively yield a single threo/erythro diastereomer). If it produces a mixture when a pure isomer is requested, FAIL IT.\n"
            f"3. Hallucinated mass balance or functional group interconversions.\n"
            f"Reply ONLY with 'PASS' if strictly valid, or 'FAIL: [Reason]' if invalid."
        )
        
        critic_res = _call_llm(critic_prompt, model, nocache=nocache, print_output=False, timeout=30, suppress_errors=True)
        
        if critic_res and critic_res.upper().startswith("PASS"):
            valid_pathways.append(pathway)
        else:
            reason = critic_res if critic_res else "Critic Timeout/Unknown Error"
            err_msg = reason.replace('FAIL:', '').strip()
            print(f"  \033[93m[🚧] Gatekeeper dropped pathway: {err_msg[:80]}...\033[0m")
            errors.append(err_msg)

    return "\n".join(valid_pathways), errors

def predict_reaction(reactants: list, model: str, **kwargs) -> str:
    prompt = (
        f"Act as an expert Industrial Chemist. Predict the major product of the reaction between: {', '.join(reactants)}. "
        f"CRITICAL RULES: \n"
        f"1. You MUST use exact, correct SMILES strings for all reactants and products. Do not hallucinate chain lengths or ring substituents. \n"
        f"2. Format your answer EXACTLY as: RELATION: [Reactant SMILES] -> [Product SMILES] using [Conditions]. "
    )
    return _call_llm(prompt, model, suppress_errors=False, **kwargs)

def propose_pathway(target: str, model: str, depth: int, target_smiles: str = "", **kwargs) -> str:
    base_prompt = (
        f"Act as an expert Industrial Organic Chemist. Propose a branching retrosynthetic tree for: {target} (SMILES: {target_smiles}). Depth: {depth}.\n"
        f"CRITICAL CHEMISTRY RULES:\n"
        f"1. Global Chemoselectivity: Avoid harsh conditions (like refluxing strong acids on aromatic amines) that destroy sensitive groups.\n"
        f"2. Isomeric Accuracy & Diastereoselectivity: You MUST include stereochemical encoding (@/@@). The reaction MUST be stereoselective enough to realistically yield the requested diastereomer in industry.\n"
        f"3. Strict Target Match: Your product SMILES must mathematically match the target SMILES.\n"
        f"Format EXACTLY as: RELATION: [Precursor SMILES] + [Precursor SMILES] -> [Target SMILES] using [Reagents]. DO NOT add reaction names before the SMILES."
    )
    
    should_print = kwargs.pop('print_output', True)
    nocache = kwargs.get('nocache', False)
    
    max_retries = 2
    current_prompt = base_prompt
    
    for attempt in range(max_retries + 1):
        if should_print and attempt > 0:
            print(f"  \033[95m[🔄] AI Self-Correction Loop Triggered (Attempt {attempt}/{max_retries})...\033[0m")
            
        raw_result = _call_llm(current_prompt, model, print_output=False, suppress_errors=False, **kwargs)
        
        if should_print and attempt == 0:
            print("  \033[96m[🔬] Gatekeeper Active: Validating SMILES syntax and Chemoselectivity...\033[0m")
        
        valid_result, errors = validate_pathway_logic(raw_result, target, target_smiles, model, nocache)
        
        if valid_result.strip():
            if should_print:
                display_result(valid_result, kwargs.get('verbose', False), True)
            return valid_result
            
        if attempt < max_retries:
            current_prompt = base_prompt + "\n\nYOUR PREVIOUS ATTEMPT FAILED. The Gatekeeper rejected it for these reasons:\n" + "\n".join(f"- {e}" for e in set(errors)) + "\n\nFix the SMILES syntax, target identity, and stereoselective/chemoselective errors. Output ONLY the corrected RELATION lines."
            
    if should_print:
        print(f"\n\033[91m[!] Synthesis Error: AI failed to generate valid pathways after self-correction.\033[0m")
    return ""