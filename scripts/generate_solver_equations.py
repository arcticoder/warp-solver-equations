#!/usr/bin/env python3
r"""
Reads stencil .tex files and generates an RK4 solver update formulas document (solver_update.tex).

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

def clean_function_args(args_str):
    """Clean up function arguments to use standard mathematical notation."""
    # Handle patterns like "- h + r" -> "r - h"
    args_str = re.sub(r'- h \+ r', r'r - h', args_str)
    args_str = re.sub(r'- 2h \+ r', r'r - 2h', args_str)
    args_str = re.sub(r'- ([0-9]*h) \+ r', r'r - \1', args_str)
    args_str = re.sub(r'h \+ r', r'r + h', args_str)
    args_str = re.sub(r'2h \+ r', r'r + 2h', args_str)
    args_str = re.sub(r'([0-9]*h) \+ r', r'r + \1', args_str)
    
    # Handle theta patterns  
    args_str = re.sub(r'- h \+ \\theta', r'\\theta - h', args_str)
    args_str = re.sub(r'h \+ \\theta', r'\\theta + h', args_str)
    
    # Remove any remaining \left and \right
    args_str = re.sub(r'\\left\(', r'', args_str)
    args_str = re.sub(r'\\right\)', r'', args_str)
    
    return args_str.strip()

def clean_latex_expression(expr):
    """
    Clean LaTeX expression by removing problematic operatorname patterns
    and fixing delimiter balancing issues.
    """
    # Step 1: Handle problematic \operatorname{bigl} patterns with nested \left...\right 
    # Use a pattern that can handle nested structures
    pattern = r'\\operatorname\{bigl\}\{\\left\((.*\\right.*?)\\right\)\}'
    
    def replace_operatorname(match):
        content = match.group(1)
        # Extract the innermost content by removing the outer \right) and finding the matching \left(
        # This handles cases like: r,\left( t + \Delta t \right)
        return f'\\bigl({content}\\bigr)'
    
    # Apply the replacement
    while re.search(pattern, expr):
        expr = re.sub(pattern, replace_operatorname, expr)
    
    # Step 1b: Handle simpler operatorname patterns without nested structures
    simple_pattern = r'\\operatorname\{bigl\}\{([^}]*)\}'
    expr = re.sub(simple_pattern, r'\\bigl(\1\\bigr)', expr)
    
    # Step 2: Fix mathematical notation - ensure proper spacing and formatting
    expr = re.sub(r'dtheta', r'd\\theta', expr)  # Fix theta notation
    expr = re.sub(r'\\,\\,', r'\\,', expr)  # Remove double spacing
    
    # Step 3: Clean up function calls  
    # Handle the special case where "bigr" appears before function names in the original text
    # This is not a LaTeX command but part of the mathematical expression
    expr = re.sub(r'- bigr f\{', r'-\\,f{', expr)
    expr = re.sub(r'\\bbigr f\{', r'f{', expr)
    
    # Handle f{\left(...\right)} patterns and clean up the arguments
    def clean_function_call(match):
        args = match.group(1)
        cleaned_args = clean_function_args(args)
        return f'f({cleaned_args})'
    
    # Match f{...} patterns with various LaTeX constructs inside
    expr = re.sub(r'f\{\\left\(([^}]*)\)\\right\}', clean_function_call, expr)
    expr = re.sub(r'f\{([^}]*)\}', clean_function_call, expr)
    
    return expr

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
    
    # Extract the approximation equation - look for content between \approx and \quad
    # This should capture the mathematical expression but stop before accuracy notes
    approx_match = re.search(r'\\approx\s*(.*?)(?=\\quad|\\\\|\$|\n|$)', text, re.DOTALL)
    
    if not approx_match:
        print(f"Warning: Could not find approximation in {path}")
        return None
    
    approximation = approx_match.group(1).strip()
    
    # Clean up any remaining LaTeX document structure that got included
    approximation = re.sub(r'\\end\{document\}.*', '', approximation, flags=re.DOTALL)
    approximation = re.sub(r'\\begin\{.*?\}', '', approximation)
    approximation = re.sub(r'\\end\{.*?\}', '', approximation)
    
    # Clean the LaTeX expression
    cleaned_approximation = clean_latex_expression(approximation)
    
    return {
        'variable': variable,
        'order': order,
        'path': path,
        'approximation': cleaned_approximation
    }

def validate_latex_balance(latex_content):
    """
    Validate that LaTeX delimiters are properly balanced.
    """
    # Count math block delimiters
    math_open = latex_content.count(r'\[')
    math_close = latex_content.count(r'\]')
    
    # Count bigl/bigr pairs
    bigl_count = len(re.findall(r'\\bigl\(', latex_content))
    bigr_count = len(re.findall(r'\\bigr\)', latex_content))
    
    # Count parentheses within math blocks
    math_blocks = re.findall(r'\\\\.*?\\\\', latex_content, re.DOTALL)
    paren_balance = 0
    for block in math_blocks:
        paren_balance += block.count('(') - block.count(')')
    
    issues = []
    if math_open != math_close:
        issues.append(f"Math blocks unbalanced: {math_open} \\[ vs {math_close} \\]")
    if bigl_count != bigr_count:
        issues.append(f"bigl/bigr unbalanced: {bigl_count} \\bigl( vs {bigr_count} \\bigr)")
    if paren_balance != 0:
        issues.append(f"Parentheses unbalanced in math blocks: {paren_balance}")
    
    if issues:
        return False, "; ".join(issues)
    else:
        return True, "All delimiters balanced"

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
    parser.add_argument(
        "--minimal", "-m",
        action="store_true",
        help="Generate minimal output with no document preamble (for downstream tools)"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true", 
        help="Validate LaTeX syntax balance after generation"
    )
    args = parser.parse_args()

    # Find all stencil files
    stencil_files = []
    for filename in os.listdir(args.input_dir):
        if filename.startswith('stencil_') and filename.endswith('.tex'):
            stencil_files.append(os.path.join(args.input_dir, filename))
    
    if not stencil_files:
        print(f"No stencil_*.tex files found in {args.input_dir}")
        return 1
    
    # Parse all stencil files
    stencils = OrderedDict()
    for path in sorted(stencil_files):
        stencil = parse_stencil_file(path)
        if stencil:
            # Create a key from variable and order
            key = f"{stencil['variable']}_{stencil['order']}"
            stencils[key] = stencil
            if args.debug:
                print(f"Parsed {os.path.basename(path)}: {key}")
                print(f"  Approximation: {stencil['approximation'][:100]}...")
    
    if not stencils:
        print("No valid stencil files could be parsed")
        return 1

    # Generate the LaTeX document
    if args.minimal:
        # Begin minimal LaTeX output (no document preamble for downstream processing)
        with open(args.output, "w", encoding='utf-8') as out:
            # Generate RK4 equations
            out.write("% RK4 Solver Update Equations\n\n")
            
            # Stage k1: Use the finite difference approximations directly
            out.write("% Stage k1: Spatial discretization\n")
            for key, stencil in stencils.items():
                out.write(f"% {stencil['variable']} derivative ({stencil['order']})\n")
                out.write("\\[\n")
                out.write(f"k_1^{{({stencil['variable']})}} = \\Delta t \\cdot \\left( {stencil['approximation']} \\right)\n")
                out.write("\\]\n\n")
            
            # Stages k2, k3, k4: Use functional notation
            out.write("% Stage k2: Half-step using k1\n")
            out.write("\\[\n")
            out.write("k_2 = \\Delta t \\cdot F\\left(X^n + \\frac{k_1}{2}\\right)\n")
            out.write("\\]\n\n")
            
            out.write("% Stage k3: Half-step using k2\n")
            out.write("\\[\n")
            out.write("k_3 = \\Delta t \\cdot F\\left(X^n + \\frac{k_2}{2}\\right)\n")
            out.write("\\]\n\n")
            
            out.write("% Stage k4: Full step using k3\n")
            out.write("\\[\n")
            out.write("k_4 = \\Delta t \\cdot F\\left(X^n + k_3\\right)\n")
            out.write("\\]\n\n")
            
            # Final update
            out.write("% Final RK4 update\n")
            out.write("\\[\n")
            out.write("X^{n+1} = X^n + \\frac{1}{6}\\left(k_1 + 2k_2 + 2k_3 + k_4\\right)\n")
            out.write("\\]\n")
    else:
        # Full LaTeX document
        with open(args.output, "w", encoding='utf-8') as out:
            out.write("\\documentclass{article}\n")
            out.write("\\usepackage{amsmath}\n")
            out.write("\\usepackage{amsfonts}\n")
            out.write("\\usepackage{amssymb}\n")
            out.write("\\title{RK4 Solver Update Equations}\n")
            out.write("\\author{Generated from finite difference stencils}\n")
            out.write("\\date{\\today}\n\n")
            out.write("\\begin{document}\n")
            out.write("\\maketitle\n\n")
            
            out.write("\\section{Fourth-Order Runge-Kutta Time Integration}\n\n")
            
            out.write("This document presents the RK4 solver update equations based on ")
            out.write("finite difference spatial discretizations.\n\n")
            
            # Generate RK4 equations
            out.write("\\subsection{Stage k1: Spatial Discretization}\n\n")
            out.write("The first stage uses the finite difference approximations directly:\n\n")
            
            for key, stencil in stencils.items():
                out.write(f"For {stencil['variable']} derivative ({stencil['order']}):\n")
                out.write("\\[\n")
                out.write(f"k_1^{{({stencil['variable']})}} = \\Delta t \\cdot \\left( {stencil['approximation']} \\right)\n")
                out.write("\\]\n\n")
            
            # Stages k2, k3, k4: Use functional notation
            out.write("\\subsection{Stages k2, k3, k4: Functional Notation}\n\n")
            out.write("For stages k2-k4, we use functional notation F(...) since full expansion ")
            out.write("would require symbolic manipulation of complex expressions:\n\n")
            
            out.write("\\[\n")
            out.write("k_2 = \\Delta t \\cdot F\\left(X^n + \\frac{k_1}{2}\\right)\n")
            out.write("\\]\n\n")
            
            out.write("\\[\n")
            out.write("k_3 = \\Delta t \\cdot F\\left(X^n + \\frac{k_2}{2}\\right)\n")
            out.write("\\]\n\n")
            
            out.write("\\[\n")
            out.write("k_4 = \\Delta t \\cdot F\\left(X^n + k_3\\right)\n")
            out.write("\\]\n\n")
            
            # Final update
            out.write("\\subsection{Final Update}\n\n")
            out.write("\\[\n")
            out.write("X^{n+1} = X^n + \\frac{1}{6}\\left(k_1 + 2k_2 + 2k_3 + k_4\\right)\n")
            out.write("\\]\n\n")
            
            out.write("\\end{document}\n")

    print(f"Generated {args.output} with {len(stencils)} stencils.")
    
    # Validate LaTeX syntax if requested
    if args.validate:
        with open(args.output, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for any remaining problematic patterns
        operatorname_count = len(re.findall(r'\\operatorname\{bigl\}', content))
        if operatorname_count > 0:
            print(f"Warning: {operatorname_count} unresolved \\operatorname{{bigl}} patterns found")
        
        # Validate delimiter balance
        is_valid, message = validate_latex_balance(content)
        if is_valid:
            print(f"✓ LaTeX validation passed: {message}")
        else:
            print(f"✗ LaTeX validation failed: {message}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
