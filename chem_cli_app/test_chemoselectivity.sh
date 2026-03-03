#!/bin/bash

echo "🧪 Starting Chemoselectivity Stress Test Suite (v1.8.3 Baseline)"
echo "================================================="
echo ""
echo "--- Test 1: Procaine (Amine + Ester) ---"
chem-cli -p "procaine" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o procaine.html
echo ""
echo "--- Test 2: Methylphenidate (Amine + Ester) ---"
chem-cli -p "methylphenidate" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o ritalin.html
echo ""
echo "--- Test 3: Testosterone (Ketone + Secondary Alcohol) ---"
chem-cli -p "testosterone" -d 1 -m "gemini/gemini-2.5-flash" --nocache -o testosterone.html
echo ""
echo "================================================="
echo "✨ Chemoselectivity testing complete."