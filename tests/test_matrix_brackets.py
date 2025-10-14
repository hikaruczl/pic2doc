#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from latex2mathml.converter import convert as latex_to_mathml
import xml.etree.ElementTree as ET

# Test different matrix environments
matrices = {
    'pmatrix': r'\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}',
    'bmatrix': r'\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}',
    'vmatrix': r'\begin{vmatrix} 1 & 2 \\ 3 & 4 \end{vmatrix}',
    'Vmatrix': r'\begin{Vmatrix} 1 & 2 \\ 3 & 4 \end{Vmatrix}',
}

print("=" * 80)
print("Matrix bracket conversion test")
print("=" * 80)

for matrix_type, latex in matrices.items():
    print("")
    print(matrix_type + ":")
    print("LaTeX: " + latex)

    try:
        mathml = latex_to_mathml(latex)
        print("MathML (first 200 chars): " + mathml[:200] + "...")

        # Parse MathML and find mfenced elements
        root = ET.fromstring(mathml)

        # Recursively find all mfenced elements
        def find_mfenced(elem, depth=0):
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag == 'mfenced':
                open_attr = elem.get('open', '(')
                close_attr = elem.get('close', ')')
                print("  Found mfenced: open='" + open_attr + "', close='" + close_attr + "'")
            for child in elem:
                find_mfenced(child, depth + 1)

        find_mfenced(root)

    except Exception as e:
        print("  Conversion failed: " + str(e))

print("")
print("=" * 80)
