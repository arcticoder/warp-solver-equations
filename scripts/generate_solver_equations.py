#!/usr/bin/env python3
"""
Reads stencil .tex files and generates an RK4 time‐integration update formulas document (solver_update.tex).
"""

import argparse
import os
import re
from collections import OrderedDict

def parse_stencil_file(path):
    """
    Parse a stencil .tex file to extract a mapping from grid offset to coefficient.
    Looks for patterns like '0.5 X_{i+1}' in the LaTeX.
    """
    text = open(path, encoding='utf-8').read()
    # Regex: coefficient (e.g. -1.0, +0.25) followed by X_{i+offset}
    pattern = re.compile(r'([+-]?\d*\.?\d+)\s*X_\{i([+-]?\d+)\}')
    coefs = OrderedDict()
    for coef, offset in pattern.findall(text):
        coefs[int(offset)] = float(coef)
    return coefs

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
        stencils[key] = parse_stencil_file(path)

    # Begin LaTeX document
    with open(args.output, "w", encoding='utf-8') as out:
        out.write("\\documentclass{article}\n")
        out.write("\\usepackage{amsmath}\n\\begin{document}\n\n")
        for var, coefs in stencils.items():
            out.write(f"% Stencil for derivative '{var}'\n")
            # RK4 stages
            out.write("\\[\n")
            out.write(f"k_1^{{{var}}} = ")
            terms = []
            for offset, coef in coefs.items():
                terms.append(f"{coef:+g}X_{{n{offset:+d}}}")
            out.write(" ".join(terms))
            out.write("\n\\]\n\n")

            out.write("\\[\n")
            out.write(f"k_2^{{{var}}} = F\\bigl(X^n + \\tfrac{{\\Delta t}}2 k_1\\bigr)\n\\]\n\n")

            out.write("\\[\n")
            out.write(f"k_3^{{{var}}} = F\\bigl(X^n + \\tfrac{{\\Delta t}}2 k_2\\bigr)\n\\]\n\n")

            out.write("\\[\n")
            out.write(f"k_4^{{{var}}} = F\\bigl(X^n + \\Delta t k_3\\bigr)\n\\]\n\n")

            out.write("\\[\n")
            out.write(
                "X^{n+1} = X^n + "
                "\\tfrac{\\Delta t}6 (k_1 + 2k_2 + 2k_3 + k_4)\n"
            )
            out.write("\\]\n\n")

        out.write("\\end{document}\n")

if __name__ == "__main__":
    main()
