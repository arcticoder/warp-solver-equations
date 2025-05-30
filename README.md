# warp-solver-equations

**Generates** the Runge–Kutta 4 time‐integration update formulas for each evolved field \(X\) in a warp-bubble simulation, by parsing finite-difference stencil definitions from the [warp-discretization](/arcticoder/warp-discretization) repository and rendering them as LaTeX.

## Features

- **Stencil parsing**:  
  Reads `stencil_*.tex` files, extracts grid‐point coefficients and offsets.
- **Evolution definitions**:  
  Imports metric components \(g_{ij}\) (and any auxiliary fields) from a template/symbolic definition.
- **Discrete RHS construction**:  
  Substitutes parsed stencil formulas into continuum equations \(\partial_t X = F(X,\partial_r X,\partial_\theta X)\) to build a Python function `F(X)`.
- **RK4 embedding**:  
  Symbolically defines and expands the four RK4 stages:
```python
  k1 = F(X_n)
  k2 = F(X_n + dt/2 * k1)
  k3 = F(X_n + dt/2 * k2)
  k4 = F(X_n + dt   * k3)
  X_{n+1} = X_n + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
```

-   **LaTeX output**:  
    Renders the $k_1\!\dots\!k_4$ definitions and final $X^{n+1}$ formula for each field into a standalone `solver_update.tex`.
    

## Dependencies

-   Python 3.7+
    
-   (no external Python libraries required beyond the standard library)
    

## Inputs

Copy or symlink all `.tex` files from the **warp-discretization** repo into an `inputs/` directory:

-   `discretization.tex`
    
-   `stencil_r_2nd_order_001.tex`
    
-   `stencil_r_2nd_order_005.tex`
    
-   `stencil_r_4th_order_002.tex`
    
-   `stencil_r_4th_order_006.tex`
    
-   `stencil_theta_2nd_order_003.tex`
    
-   `stencil_theta_4th_order_004.tex`
    

## Usage

```bash
git clone https://github.com/arcticoder/warp-solver-equations.git
cd warp-solver-equations

# Place or link the stencil .tex files into ./inputs
python generate_solver_equations.py \
  --input-dir inputs \
  --output solver_update.tex
```

-   **`--input-dir`**: directory containing all `*.tex` stencil files.
    
-   **`--output`**: path to the generated LaTeX document (`solver_update.tex`).
    

## Output

-   **`solver_update.tex`**: a self-contained LaTeX file showing, for each evolved variable $X$:
    
```latex
    \[
      k_1^X = F\bigl(X^n,\partial_r X^n,\partial_\theta X^n\bigr)
    \]
    \[
      k_2^X = F\bigl(X^n + \tfrac{\Delta t}{2}k_1,\dots\bigr)
    \]
    % … k_3, k_4 …
    \[
      X^{n+1} = X^n + \tfrac{\Delta t}{6}\bigl(k_1 + 2k_2 + 2k_3 + k_4\bigr)
    \]
```
    

## Dependence

-   This repo depends on [warp-discretization](https://github.com/arcticoder/warp-discretization) for the stencil source files.
    
