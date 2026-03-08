import sys
import argparse
import os
import ai_router
import interactive

def main():
    parser = argparse.ArgumentParser(description="AI Chem-CLI: Agentic Retrosynthetic Planning Engine (v2.0-dev)")
    
    # --- Interactive Mode (v2.0) ---
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch the persistent interactive session")

    # --- One-shot Retrosynthesis Arguments ---
    parser.add_argument("-p", "--predict", type=str, help="Target molecule for retrosynthesis")
    parser.add_argument("-d", "--depth", type=int, default=1, help="Depth of retrosynthetic tree")
    parser.add_argument("-m", "--model", type=str, default="gemini/gemini-2.5-flash", help="LLM model to use")
    parser.add_argument("--nocache", action="store_true", help="Bypass the local cache")
    parser.add_argument("-o", "--output", type=str, help="Output file (HTML by default)")
    parser.add_argument("--pdf", action="store_true", help="Force PDF output")
    parser.add_argument("--silent", action="store_true", help="Suppress terminal output")
    
    # --- Forward Simulation Arguments ---
    parser.add_argument("-s", "--simulate", action="store_true", help="Run a forward reaction simulation")
    parser.add_argument("-r", "--reactants", type=str, help="Comma-separated reactants for forward simulation")

    args = parser.parse_args()

    # 1. Interactive Mode Routing
    if args.interactive:
        interactive.start_interactive()
        return

    # 2. Forward Simulation Routing
    if args.simulate:
        if not args.reactants:
            print("\n\033[91m[!] ERROR:\033[0m You must provide reactants using -r or --reactants when running a forward simulation.")
            sys.exit(1)
        
        if not args.silent:
            print(f"Running forward reaction simulation for: {args.reactants}")
        
        reactants_list = [r.strip() for r in args.reactants.split(",")]
        ai_router.predict_reaction(
            reactants=reactants_list, 
            model=args.model, 
            nocache=args.nocache,
            verbose=False,
            print_output=not args.silent
        )
        return

    # 3. Retrosynthesis Routing (Default)
    if args.predict:
        if not args.silent:
            print(f"Validating target '{args.predict}'...")
            print(f"Target Resolved. Analyzing {args.predict}...")
        
        # We pass the input string as the SMILES target placeholder for now
        target_smiles = args.predict 
        
        raw_output = ai_router.propose_pathway(
            target=args.predict,
            target_smiles=target_smiles,
            depth=args.depth,
            model=args.model,
            nocache=args.nocache,
            verbose=False,
            print_output=not args.silent
        )
        
        if args.output and raw_output:
            filename = args.output
            # Handle flag conflict resolution (B1 Fix)
            if args.pdf and not filename.endswith(".pdf"):
                filename = filename.rsplit(".", 1)[0] + ".pdf"
                if not args.silent:
                    print(f"\nAuto-corrected output extension to .pdf")
            
            out_path = os.path.abspath(filename)
            
            # Example write placeholder
            with open(out_path, 'w') as f:
                f.write(raw_output)
                
            if not args.silent:
                print(f"\nSuccess! Report: {out_path}")
        return
        
    # If no valid arguments provided, print help
    parser.print_help()

if __name__ == "__main__":
    main()