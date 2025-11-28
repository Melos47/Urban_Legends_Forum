#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check line 586"""

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Line 586 (index 585): {repr(lines[585])}")
print(f"Line 586 length: {len(lines[585])}")
print(f"Line 586 bytes: {lines[585].encode('utf-8')}")

# Remove the exclamation mark if it exists
if lines[585].strip().endswith('!'):
    lines[585] = lines[585].replace('!', '').rstrip() + '\n'
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Fixed!")
