#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix encoding issues in app.py"""

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace full-width exclamation mark with half-width
content = content.replace('！', '!')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed encoding issues!")
