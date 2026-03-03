import requests
from chem_utils import resolve_chemical_name, resolve_by_cid

def run_tests():
    print("🧪 Starting Raw API Network Tests...\n" + "="*40)

    print("Testing basic name resolution (Aspirin)...")
    try:
        name, smiles = resolve_chemical_name("aspirin")
        assert "C" in smiles, "Invalid SMILES returned"
        print(f"  [✓] Success! SMILES: {smiles}")
    except Exception as e:
        print(f"  [X] Failed: {e}")

    print("\nTesting CID resolution (Aspirin CID 2244)...")
    try:
        smiles_from_cid = resolve_by_cid("2244")
        assert smiles_from_cid is not None, "Failed to resolve CID 2244"
        print(f"  [✓] Success! SMILES: {smiles_from_cid}")
    except Exception as e:
        print(f"  [X] Failed: {e}")

    print("\nTesting internal benchmark fixture (Halichondrin B)...")
    try:
        name, smiles = resolve_chemical_name("Halichondrin B")
        assert len(smiles) > 100, "Fixture failed"
        print("  [✓] Success! Fixture loaded perfectly.")
    except Exception as e:
        print(f"  [X] Failed: {e}")

    print("\nTesting hallucination rejection ('flibbertigibbet')...")
    try:
        resolve_chemical_name("flibbertigibbet")
        print("  [X] Failed: The tool accepted a fake molecule!")
    except ValueError:
        print("  [✓] Success! Fake molecule correctly rejected.")

    print("\n" + "="*40 + "\n✨ All network and logic tests complete.")

if __name__ == "__main__":
    run_tests()