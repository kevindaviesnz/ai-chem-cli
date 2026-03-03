import os
import re
import json
import urllib.parse
import sys
from rdkit import Chem
from rdkit.Chem import Draw, Descriptors
from rdkit import RDLogger 
from graphviz import Digraph
from fpdf import FPDF
import markdown

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RDLogger.DisableLog('rdApp.*')

def _safe_get(url):
    headers = {'User-Agent': 'ChemCLI/1.6.0', 'Accept': 'application/json'}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
        
        if res.status_code == 404:
            return None
            
        print(f"\n  [!] API Error {res.status_code}: {res.text.strip()[:100]}")
        return None
        
    except requests.exceptions.SSLError:
        try:
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"\n  [!] Fallback Network Error: {e}")
    except Exception as e:
        print(f"\n  [!] Native Network Error: {e}")
        
    return None

def extract_smiles(props):
    for key, value in props.items():
        if 'SMILES' in key.upper() and isinstance(value, str):
            return value
    return None

def resolve_chemical_name(query):
    fixtures = {
        "halichondrin b": "C[C@@H]1C[C@@H]2CC[C@H]3C(=C)C[C@@H](O3)CC[C@]45C[C@@H]6[C@H](O4)[C@H]7[C@@H](O6)[C@@H](O5)[C@@H]8[C@@H](O7)CC[C@@H](O8)CC(=O)O[C@@H]9[C@H]([C@H]3[C@H](C[C@@H]4[C@H](O3)C[C@@]3(O4)C[C@H]4[C@@H](O3)[C@H](C[C@]3(O4)C[C@@H]([C@H]4[C@@H](O3)C[C@H](O4)[C@H](C[C@H](CO)O)O)C)C)O[C@H]9C[C@H](C1=C)O2)C",
        "taxol": "CC1=C2[C@H](C(=O)[C@@]3([C@H](C[C@@H]4[C@]([C@H]3[C@@H]([C@@](C2(C)C)(C[C@@H]1OC(=O)[C@@H]([C@H](C5=CC=CC=C5)NC(=O)C6=CC=CC=C6)O)O)OC(=O)C)(CO4)OC(=O)C)O)C)C"
    }
    
    if query.lower() in fixtures:
        return query, fixtures[query.lower()]

    if Chem.MolFromSmiles(query): return query, query
    
    safe = urllib.parse.quote(query)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{safe}/property/IsomericSMILES,CanonicalSMILES/JSON"
    
    data = _safe_get(url)
    
    if data and 'PropertyTable' in data:
        props = data['PropertyTable']['Properties'][0]
        smiles = extract_smiles(props)
        if smiles:
            return query, smiles
            
    raise ValueError("Not found")

def resolve_by_cid(cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IsomericSMILES,CanonicalSMILES/JSON"
    data = _safe_get(url)
    
    if data and 'PropertyTable' in data:
        props = data['PropertyTable']['Properties'][0]
        return extract_smiles(props)
    return None

def check_target_complexity(smiles):
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            mw = round(Descriptors.MolWt(mol), 2)
            chiral = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
            if mw > 500 or chiral > 5:
                print(f"\033[93m[⚠️] COMPLEXITY ALERT: Target is {mw} g/mol with {chiral} stereocenters.\033[0m")
    except:
        pass

def save_all_smiles_to_images(text, output_dir="."):
    smiles_pattern = r"([A-Za-z0-9@+\-\[\]\\/=#()$%.]{10,})"
    unique_smiles = set(re.findall(smiles_pattern, text))
    data = {}
    for s in unique_smiles:
        if any(kw in s for kw in ["RELATION", "using", "Level", "STEP", "CONVERGENT"]): continue
        try:
            mol = Chem.MolFromSmiles(s)
            if mol:
                img_name = f"mol_{hash(s)}.png"
                path = os.path.join(output_dir, img_name)
                Draw.MolToFile(mol, path, size=(400, 400))
                mw = round(Descriptors.MolWt(mol), 2)
                chiral = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
                if mw > 500 or chiral > 5:
                    print(f"\033[94m[🚧] INTERMEDIATE WARNING: {s[:15]}... is {mw} g/mol with {chiral} stereocenters.\033[0m")
                data[s] = {'img': path, 'mw': mw, 'price': 25.0}
        except: pass 
    return data

def generate_reaction_tree(molecule_data, connections, output_dir="."):
    dot = Digraph(comment='Tree'); dot.attr(rankdir='BT')
    for smi, info in molecule_data.items():
        img_filename = os.path.basename(info['img'])
        dot.node(str(hash(smi)), label=f"MW: {info['mw']}", image=img_filename, shape='box')
    for p, t, r in connections:
        dot.edge(str(hash(p)), str(hash(t)), label=r[:15])
    
    render_path = os.path.join(output_dir, "reaction_map")
    dot.render(render_path, format='png', cleanup=True)
    return "reaction_map.png"

def check_safety_hazards(text):
    hazards = []
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    try:
        with open(os.path.join(base_path, "hazards.json"), 'r') as f:
            db = json.load(f)
            for k, v in db.items():
                if k in text.lower(): hazards.append(v)
    except: pass
    return hazards

def generate_html_report(text, mol_data, tree_img, hazards, target, filename="report.html"):
    content = markdown.markdown(text)
    hazard_html = "".join([f'<p style="color:red; font-weight:bold;">{h}</p>' for h in hazards])
    with open(filename, "w") as f:
        f.write(f"<html><body style='font-family:sans-serif;'><h1>{target}</h1>{hazard_html}<img src='{tree_img}'>{content}</body></html>")
    return os.path.abspath(filename)

def generate_pdf_report(text, mol_data, tree_img, hazards, target, filename="report.pdf"):
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Report: {target}", ln=1)
    pdf.image(tree_img, x=10, w=190)
    pdf.multi_cell(0, 5, txt=text.encode('latin-1', 'replace').decode('latin-1'))
    pdf.output(filename)
    return os.path.abspath(filename)