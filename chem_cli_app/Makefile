# Variables
BINARY_NAME=chem-cli
VERSION=1.4.2
CACHE_PATH=~/.chem-cli/cache.json
PUBCHEM_URL=https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/water/cids/JSON

.PHONY: build install clean clear-cache help release test-complex check-api

# 1. Connectivity Check
check-api:
	@echo "Checking PubChem API connectivity..."
	@curl -s --head $(PUBCHEM_URL) | head -n 1 | grep "200" > /dev/null || \
		(echo "\033[91m[!] Error: PubChem API is unreachable.\033[0m" && exit 1)
	@echo "\033[92m[✓] PubChem API is Online.\033[0m"

# 2. Build - Restored the missing requests, certifi, and numpy flags!
build:
	@echo "Building standalone binary for version $(VERSION)..."
	pyinstaller --onefile --name $(BINARY_NAME) \
		--add-data "hazards.json:." \
		--collect-all tiktoken \
		--collect-all litellm \
		--collect-all graphviz \
		--collect-all numpy \
		--collect-all fpdf \
		--collect-all markdown \
		--collect-all requests \
		--collect-all certifi \
		--hidden-import tiktoken_ext.openai_public \
		--hidden-import tiktoken_ext \
		--copy-metadata tiktoken \
		main.py
	@echo "Build complete."

# 3. Install
install: check-api build
	@echo "Installing $(BINARY_NAME) to /usr/local/bin..."
	@mkdir -p dist
	sudo mv ./dist/$(BINARY_NAME) /usr/local/bin/
	sudo chmod +x /usr/local/bin/$(BINARY_NAME)
	xattr -d com.apple.quarantine /usr/local/bin/$(BINARY_NAME) || true
	@echo "\033[92m[✓] Installation successful.\033[0m"

# 4. Benchmark
test-complex: check-api
	@echo "Running Stress Tests..."
	@echo "--- Target: Halichondrin B (CID-First Strategy) ---"
	$(BINARY_NAME) -p "Halichondrin B" -m "gemini/gemini-2.5-flash" --nocache

clear-cache:
	rm -f $(CACHE_PATH)

clean:
	@echo "Cleaning artifacts..."
	rm -rf build dist __pycache__ *.spec *.png report.* mol_*.png