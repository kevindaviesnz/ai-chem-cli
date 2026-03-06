#!/bin/bash

echo "🧪 Starting Scientific Stress Test Suite (v1.8.5)"
echo "================================================="
echo ""

echo "--- Test 1: Paracetamol Retrosynthesis (Depth 1) ---"
chem-cli -p "paracetamol" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o paracetamol.html
echo ""

echo "--- Test 2: Ibuprofen Retrosynthesis (Depth 1) ---"
chem-cli -p "ibuprofen" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o ibuprofen.html
echo ""

echo "--- Test 3: Caffeine Retrosynthesis (Depth 1) ---"
chem-cli -p "caffeine" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o caffeine.html
echo ""

echo "--- Test 4: Forward Simulation (Paracetamol Synthesis) ---"
chem-cli -s -r "4-aminophenol, acetic anhydride" -m "gemini/gemini-2.5-flash" --nocache
echo ""

echo "--- Test 5: Forward Simulation (Friedel-Crafts on Isobutylbenzene) ---"
chem-cli -s -r "isobutylbenzene, acetyl chloride, AlCl3" -m "gemini/gemini-2.5-flash" --nocache
echo ""

echo "--- Test 6: Flag Conflict Resolution (B1 Fix Check) ---"
chem-cli -p "aspirin" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o conflict_test.html --pdf
echo ""

echo "--- Test 7: Working Directory Sandbox Proof (B2 Fix Check) ---"
echo "Creating temporary folder at /tmp/chem_cli_sandbox..."
mkdir -p /tmp/chem_cli_sandbox
echo "Running chem-cli from inside /tmp/chem_cli_sandbox..."
cd /tmp/chem_cli_sandbox || exit
chem-cli -p "aspirin" -d 1 -m "gemini/gemini-2.5-flash" --nocache --silent -o pwd_proof.html
echo ""
echo "Verifying file location..."
if [ -f "/tmp/chem_cli_sandbox/pwd_proof.html" ]; then
    echo "✅ SUCCESS: pwd_proof.html successfully saved to Current Working Directory (/tmp/chem_cli_sandbox)!"
else
    echo "❌ FAILED: File not found in the expected directory."
fi

echo ""
echo "================================================="
echo "✨ Scientific stress testing complete."