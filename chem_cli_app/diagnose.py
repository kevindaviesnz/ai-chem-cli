import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/property/IsomericSMILES/JSON"
headers = {'User-Agent': 'ChemCLI/Diagnostic', 'Accept': 'application/json'}

print("🕵️ Direct Network Diagnostic")
print("===========================")

print("\n--- 1. Standard Request (verify=True) ---")
try:
    res = requests.get(url, headers=headers, timeout=5)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:100]}")
except Exception as e:
    print(f"Error: {type(e).__name__} - {e}")

print("\n--- 2. Unverified Request (verify=False) ---")
try:
    res = requests.get(url, headers=headers, timeout=5, verify=False)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:100]}")
except Exception as e:
    print(f"Error: {type(e).__name__} - {e}")