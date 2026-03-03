#!/bin/bash

echo "🧪 Starting Scientific Stress Test Suite (v1.6.1)"
echo "================================================="

# 1. Retrosynthesis: Paracetamol
# Testing practical pathways (No Buchwald-Hartwig overkill)
echo -e "\n--- Test 1: Paracetamol Retrosynthesis (Depth 1) ---"
chem-cli -p "paracetamol" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o paracetamol.html

# 2. Retrosynthesis: Ibuprofen
# Testing strict functional group validity (No amine hydrolysis)
echo -e "\n--- Test 2: Ibuprofen Retrosynthesis (Depth 1) ---"
chem-cli -p "ibuprofen" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o ibuprofen.html

# 3. Retrosynthesis: Caffeine
# Testing complex heterocyclic ring systems.
echo -e "\n--- Test 3: Caffeine Retrosynthesis (Depth 1) ---"
chem-cli -p "caffeine" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o caffeine.html

# 4. Forward Simulation: Paracetamol Synthesis
# PROOF: Must return exact SMILES strings, not common names.
echo -e "\n--- Test 4: Forward Simulation (Paracetamol Synthesis) ---"
chem-cli -s -r "4-aminophenol, acetic anhydride" -m "gemini/gemini-2.5-flash" --nocache

# 5. Forward Simulation: Friedel-Crafts Acylation
# PROOF: Must return exact SMILES strings, not common names.
echo -e "\n--- Test 5: Forward Simulation (Friedel-Crafts on Isobutylbenzene) ---"
chem-cli -s -r "isobutylbenzene, acetyl chloride, AlCl3" -m "gemini/gemini-2.5-flash" --nocache

# 6. Flag Conflict Resolution (B1 Fix Check)
echo -e "\n--- Test 6: Flag Conflict Resolution (B1 Fix Check) ---"
chem-cli -p "aspirin" -d 1 -m "gemini/gemini-2.5-flash" -o conflict_test.html --pdf --nocache

# 7. Working Directory Proof (B2 Fix Check)
echo -e "\n--- Test 7: Working Directory Sandbox Proof (B2 Fix Check) ---"
echo "Creating temporary folder at /tmp/chem_cli_sandbox..."
mkdir -p /tmp/chem_cli_sandbox
cd /tmp/chem_cli_sandbox

echo "Running chem-cli from inside /tmp/chem_cli_sandbox..."
chem-cli -p "aspirin" -d 1 -m "gemini/gemini-2.5-flash" -o pwd_proof.html --nocache

echo -e "\nVerifying file location..."
if [ -f "pwd_proof.html" ]; then
    echo "✅ SUCCESS: pwd_proof.html successfully saved to Current Working Directory (/tmp/chem_cli_sandbox)!"
else
    echo "❌ FAILED: File did not save to the Current Working Directory."
fi

# Clean up and return
cd - > /dev/null
rm -rf /tmp/chem_cli_sandbox

echo -e "\n================================================="
echo "✨ Scientific stress testing complete."