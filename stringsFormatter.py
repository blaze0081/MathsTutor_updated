import re

def should_skip_text(text):
    # Pattern to match mathematical expressions
    math_patterns = [
        # Basic arithmetic operations
        r'\d+\s*÷\s*\d+\s*=\s*\d+',    # division with equals
        r'\d+\s*×\s*\d+\s*=\s*\d+',    # multiplication with equals
        r'\d+\s*\+\s*\d+\s*=\s*\d+',   # addition with equals
        r'\d+\s*-\s*\d+\s*=\s*\d+',    # subtraction with equals
        r'\d+\s*=\s*\d+\s*×\s*\d+',    # equations with multiplication
        r'\d+\s*=\s*\d+\s*\^\s*\d+',   # equations with powers
        
        # LaTeX-style functions and notations
        r'\\sqrt\{[^}]+\}',            # square root
        r'\\frac\{[^}]+\}\{[^}]+\}',   # fractions
        r'\\cdot',                      # multiplication dot
        r'\\times',                     # multiplication cross
        r'\\div',                       # division symbol
        r'\\pm',                        # plus-minus symbol
        r'\\leq',                       # less than or equal to
        r'\\geq',                       # greater than or equal to
        r'\\neq',                       # not equal to
        r'\\approx',                    # approximately equal to
        
        # Powers, subscripts, and superscripts
        r'\^[0-9]+',                    # simple powers
        r'\^\{[^}]+\}',                # complex powers
        r'_[0-9]+',                     # simple subscripts
        r'_\{[^}]+\}',                 # complex subscripts
        
        # Common mathematical functions
        r'\\sin',                       # sine
        r'\\cos',                       # cosine
        r'\\tan',                       # tangent
        r'\\csc',                       # cosecant
        r'\\sec',                       # secant
        r'\\cot',                       # cotangent
        r'\\log',                       # logarithm
        r'\\ln',                        # natural logarithm
        r'\\exp',                       # exponential
        
        # Sets and logic
        r'\\in',                        # element of
        r'\\subset',                    # subset
        r'\\subseteq',                  # subset or equal
        r'\\cup',                       # union
        r'\\cap',                       # intersection
        r'\\emptyset',                  # empty set
        r'\\forall',                    # for all
        r'\\exists',                    # exists
        
        # Brackets and parentheses
        r'\\left[\(\[\{].*?\\right[\)\]\}]',  # matched brackets with \left and \right
        r'\([^)]*\)',                   # regular parentheses
        r'\{[^}]*\}',                   # curly braces
        r'\[[^\]]*\]',                  # square brackets
        
        # Common mathematical symbols
        r'\\infty',                     # infinity
        r'\\partial',                   # partial derivative
        r'\\nabla',                     # nabla/del operator
        r'\\int',                       # integral
        r'\\sum',                       # summation
        r'\\prod',                      # product
        r'\\lim',                       # limit
        
        # Arrows and relations
        r'\\rightarrow',                # right arrow
        r'\\leftarrow',                 # left arrow
        r'\\Rightarrow',                # implies
        r'\\Leftarrow',                 # implied by
        r'\\leftrightarrow',            # double arrow
        r'\\Leftrightarrow',            # if and only if
        
        # Matrices and vectors
        r'\\begin\{matrix\}.*?\\end\{matrix\}',      # matrix
        r'\\begin\{pmatrix\}.*?\\end\{pmatrix\}',    # parentheses matrix
        r'\\begin\{bmatrix\}.*?\\end\{bmatrix\}',    # bracket matrix
        r'\\vec\{[^}]+\}',              # vector notation
        
        # Additional patterns for common equation forms
        r'\d+\s*=\s*[^=]+',            # any equation with numbers
        r'[a-zA-Z]\s*=\s*[^=]+',       # any equation with variables
        r'\\boxed\{[^}]+\}',           # boxed equations
        
        # Greek letters (commonly used in math)
        r'\\alpha|\\beta|\\gamma|\\delta|\\epsilon|\\zeta|\\eta|\\theta|\\iota|\\kappa|\\lambda|\\mu|\\nu|\\xi|\\pi|\\rho|\\sigma|\\tau|\\upsilon|\\phi|\\chi|\\psi|\\omega',
        
        # Additional mathematical operators
        r'\\oplus|\\otimes|\\odot',     # circle operators
        r'\\star|\\ast',                # star operators
        r'\\perp|\\parallel',           # perpendicular and parallel
        
        # Common equation patterns with variables
        r'[a-zA-Z]\s*=\s*\\frac\{[^}]+\}\{[^}]+\}',  # equations with fractions
        r'[a-zA-Z]\s*=\s*\\sqrt\{[^}]+\}',           # equations with square roots
        
        # Number systems and sets
        r'\\mathbb\{[NZQRC]\}',         # number system symbols
        r'\\varnothing',                # empty set alternative
    ]
    
    return any(re.search(pattern, text.strip()) for pattern in math_patterns)

def latex_to_symbols(text):
    # Dictionary mapping LaTeX commands to symbols
    latex_symbols = {
        r'\\div': '÷',
        r'\\times': '×',
        r'\\cdot': '⋅',
        r'\\pm': '±',
        r'\\leq': '≤',
        r'\\geq': '≥',
        r'\\neq': '≠',
        r'\\approx': '≈',
        r'\\infty': '∞',
        r'\\partial': '∂',
        r'\\nabla': '∇',
        r'\\int': '∫',
        r'\\sum': '∑',
        r'\\prod': '∏',
        r'\\rightarrow': '→',
        r'\\leftarrow': '←',
        r'\\Rightarrow': '⇒',
        r'\\Leftarrow': '⇐',
        r'\\leftrightarrow': '↔',
        r'\\Leftrightarrow': '⇔',
        r'\\alpha': 'α',
        r'\\beta': 'β',
        r'\\gamma': 'γ',
        r'\\delta': 'δ',
        r'\\epsilon': 'ε',
        r'\\zeta': 'ζ',
        r'\\eta': 'η',
        r'\\theta': 'θ',
        r'\\iota': 'ι',
        r'\\kappa': 'κ',
        r'\\lambda': 'λ',
        r'\\mu': 'μ',
        r'\\nu': 'ν',
        r'\\xi': 'ξ',
        r'\\pi': 'π',
        r'\\rho': 'ρ',
        r'\\sigma': 'σ',
        r'\\tau': 'τ',
        r'\\upsilon': 'υ',
        r'\\phi': 'φ',
        r'\\chi': 'χ',
        r'\\psi': 'ψ',
        r'\\omega': 'ω',
        r'\\perp': '⊥',
        r'\\parallel': '∥',
        r'\\in': '∈',
        r'\\subset': '⊂',
        r'\\subseteq': '⊆',
        r'\\cup': '∪',
        r'\\cap': '∩',
        r'\\emptyset': '∅',
        r'\\forall': '∀',
        r'\\exists': '∃',
    }
    
    # Convert fraction patterns like \frac{a}{b} to a/b
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', text)
    
    # Convert sqrt patterns like \sqrt{a} to √a
    text = re.sub(r'\\sqrt\{([^}]+)\}', r'√\1', text)
    
    # Convert power patterns like a^{b} to aᵇ (for simple cases)
    text = re.sub(r'\^\{([0-9])\}', lambda m: str.translate(m.group(1), str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')), text)
    
    # Convert subscript patterns like a_{b} to aᵢ (for simple cases)
    text = re.sub(r'_\{([0-9])\}', lambda m: str.translate(m.group(1), str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')), text)
    
    # Replace all other LaTeX commands with their symbols
    for pattern, symbol in latex_symbols.items():
        text = re.sub(pattern, symbol, text)
    
    return text
