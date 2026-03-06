#!/bin/bash

echo "🧪 Starting Orthogonal Protecting Groups Test Suite"
echo "================================================="
echo ""

echo "--- Test 1: Boc-protected amino acid (Selective ester hydrolysis) ---"
echo "Target: N-Boc-L-alanine"
chem-cli -p "CC(NC(=O)OC(C)(C)C)C(=O)O" -d 1 -m "gemini/gemini-2.5-flash" --nocache
echo ""

echo "--- Test 2: TBDMS-protected alcohol with a free ketone (Selective deprotection) ---"
echo "Target: 4-((tert-butyldimethylsilyl)oxy)cyclohexan-1-one"
chem-cli -p "O=C1CCC(O[Si](C)(C)C(C)(C)C)CC1" -d 1 -m "gemini/gemini-2.5-flash" --nocache
echo ""

echo "--- Test 3: Fmoc amino acid with a free carboxylic acid (Orthogonal selectivity) ---"
echo "Target: Fmoc-L-phenylalanine"
chem-cli -p "OC(=O)[C@@H](Cc1ccccc1)NC(=O)OCC1c2ccccc2-c2ccccc21" -d 1 -m "gemini/gemini-2.5-flash" --nocache
echo ""

echo "================================================="
echo "✨ Protecting groups testing complete."