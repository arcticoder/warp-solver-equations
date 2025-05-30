#!/usr/bin/env python3
"""
Reads stencil .tex files and generates an RK4 time‐integration update formulas document (solver_update.tex).

This script:
1. Parses finite difference stencil files to extract the spatial discretization expressions
2. Uses these as the k1 stage of RK4 time integration
3. Uses functional notation F(...) for stages k2-k4 since full expansion would be extremely complex

Note: For stages k2-k4, we use F(X^n + dt*k_prev) notation rather than expanding the full 
finite difference expressions, as this would require symbolic manipulation of the complex
expressions involving functions like f(r±h, t) and trigonometric terms.

For full expansion of all RK4 stages, a symbolic mathematics library like SymPy would be needed.
"""

import argparse
import os
import re
from collections import OrderedDict

def parse_stencil_file(path):
    """
    Parse a stencil .tex file to extract the finite difference approximation.
    Extracts the RHS of the approximation equation.
    """
    with open(path, encoding='utf-8') as f:
        text = f.read()
    
    # Extract variable, order, and the approximation equation
    variable_match = re.search(r'% Variable: (\w+)', text)
    order_match = re.search(r'% Order: (.+)', text)
    
    variable = variable_match.group(1) if variable_match else "unknown"
    order = order_match.group(1) if order_match else "unknown"
    
    # Find the approximation equation (RHS after \approx)
    approx_match = re.search(r'\\approx\s+(.+?)\s+\\quad', text, re.DOTALL)
    if approx_match:
        approximation = approx_match.group(1).strip()
        # Clean up the approximation (remove extra whitespace and newlines)
        approximation = re.sub(r'\s+', ' ', approximation)
    else:
        approximation = "\\text{No approximation found}"
    
    return {
        'variable': variable,
        'order': order,
        'approximation': approximation
    }

def debug_print_stencil(name, stencil_data):
    """Debug function to print parsed stencil data."""
    print(f"\n--- Stencil: {name} ---")
    print(f"Variable: {stencil_data['variable']}")
    print(f"Order: {stencil_data['order']}")
    print(f"Approximation: {stencil_data['approximation'][:100]}...")  # First 100 chars

def main():
    parser = argparse.ArgumentParser(
        description="Generate RK4 solver update LaTeX from stencil .tex files."
    )
    parser.add_argument(
        "--input-dir", "-i",
        required=True,
        help="Directory containing stencil_*.tex files"
    )
    parser.add_argument(
        "--output", "-o",
        default="solver_update.tex",
        help="Output LaTeX filename"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Print debug information about parsed stencils"
    )
    args = parser.parse_args()

    # Find stencil files
    stencil_files = sorted(
        f for f in os.listdir(args.input_dir)
        if f.startswith("stencil_") and f.endswith(".tex")
    )
    if not stencil_files:
        print("No stencil files found in", args.input_dir)
        return

    # Parse each stencil
    stencils = {}
    for fname in stencil_files:
        key = fname.replace("stencil_", "").replace(".tex", "")
        path = os.path.join(args.input_dir, fname)
        stencil_data = parse_stencil_file(path)
        stencils[key] = stencil_data
        
        if args.debug:
            debug_print_stencil(key, stencil_data)

    # Begin LaTeX document
    with open(args.output, "w", encoding='utf-8') as out:
        out.write("\\documentclass{article}\n")
        out.write("\\usepackage{amsmath}\n")
        out.write("\\usepackage[margin=0.5in]{geometry}\n")
        out.write("\\begin{document}\n\n")
        out.write("\\title{Warp Solver RK4 Time Integration Equations}\n")
        out.write("\\maketitle\n\n")
        
        for key, stencil_data in stencils.items():
            var = stencil_data['variable']
            order = stencil_data['order']
            approx = stencil_data['approximation']
            
            out.write(f"\\section*{{Stencil: {key} ({var}, {order})}}\n\n")
            
            # Check if approximation is trivial (placeholder)
            if "a begin i m p t x" in approx:
                out.write("\\textit{Placeholder stencil - no finite difference approximation available.}\n\n")
                continue
            
            # RK4 stage 1: Use the finite difference approximation directly
            out.write("\\textbf{RK4 Stage 1:}\n")
            out.write("\\[\n")
            out.write(f"k_1^{{{key}}} = {approx}\n")
            out.write("\\]\n\n")

            # For stages 2-4, we'll use the functional form since expanding
            # the full finite difference would be extremely complex
            out.write("\\textbf{RK4 Stage 2:}\n")
            out.write("\\[\n")
            out.write(f"k_2^{{{key}}} = F_{{{key}}}\\left(X^n + \\frac{{\\Delta t}}{{2}} k_1\\right)\n")
            out.write("\\]\n\n")

            out.write("\\textbf{RK4 Stage 3:}\n")
            out.write("\\[\n")
            out.write(f"k_3^{{{key}}} = F_{{{key}}}\\left(X^n + \\frac{{\\Delta t}}{{2}} k_2\\right)\n")
            out.write("\\]\n\n")

            out.write("\\textbf{RK4 Stage 4:}\n")
            out.write("\\[\n")
            out.write(f"k_4^{{{key}}} = F_{{{key}}}\\left(X^n + \\Delta t \\, k_3\\right)\n")
            out.write("\\]\n\n")

            out.write("\\textbf{Update:}\n")
            out.write("\\[\n")
            out.write("X^{n+1} = X^n + "
                     "\\frac{\\Delta t}{6} \\left(k_1^{" + key + "} + 2k_2^{" + key + "} + 2k_3^{" + key + "} + k_4^{" + key + "}\\right)\n")
            out.write("\\]\n\n")
            out.write("\\pagebreak\n\n")

        out.write("\\end{document}\n")

    print(f"Generated {args.output} with {len(stencils)} stencils.")

if __name__ == "__main__":
    main()
