#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from latex2mathml.converter import convert as latex_to_mathml
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

# Test bmatrix (should have square brackets)
latex = r'\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}'

print("=" * 80)
print("Testing bmatrix structure")
print("=" * 80)
print("LaTeX:", latex)
print()

mathml = latex_to_mathml(latex)

# Pretty print the MathML
dom = minidom.parseString(mathml)
pretty_mathml = dom.toprettyxml(indent="  ")
print("MathML:")
print(pretty_mathml)

print("=" * 80)
