#!/usr/bin/env python3
"""Script simple pour ajouter 'from exc' aux raise HTTPException."""

import re
from pathlib import Path


def fix_file(file_path):
    """Corrige un fichier en ajoutant 'from exc' aux raise."""
    content = Path(file_path).read_text()
    original = content

    # Pattern 1: raise HTTPException(status_code=...) sur une ligne
    # Cherche les raise HTTPException qui n'ont pas déjà 'from'
    pattern1 = r'(raise HTTPException\([^)]+\))(?!\s+from)'
    content = re.sub(pattern1, r'\1 from exc', content)

    # Pattern 2: raise HTTPException( sur plusieurs lignes (plus difficile)
    # On doit trouver la fermeture de la parenthèse
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Si on trouve un raise HTTPException( sans from
        if 'raise HTTPException(' in line and ' from ' not in line:
            # Collecter toutes les lignes jusqu'à la fermeture
            block = [line]
            j = i + 1
            paren_count = line.count('(') - line.count(')')

            while j < len(lines) and paren_count > 0:
                block.append(lines[j])
                paren_count += lines[j].count('(') - lines[j].count(')')
                j += 1

            # Vérifier si le bloc complet n'a pas déjà 'from'
            full_block = '\n'.join(block)
            if ' from ' not in full_block:
                # Ajouter 'from exc' à la dernière ligne du bloc
                block[-1] = block[-1].rstrip()
                if block[-1].endswith(')'):
                    block[-1] += ' from exc'

            result.extend(block)
            i = j
        else:
            result.append(line)
            i += 1

    content = '\n'.join(result)

    if content != original:
        Path(file_path).write_text(content)
        return True
    return False


def main():
    """Point d'entrée."""
    files = [
        'src/geneweb_py/api/routers/events.py',
        'src/geneweb_py/api/routers/genealogy.py',
        'src/geneweb_py/api/routers/persons.py',
        'src/geneweb_py/api/routers/families.py',
        'src/geneweb_py/formats/xml.py',
        'src/geneweb_py/formats/json.py',
        'src/geneweb_py/formats/gedcom.py',
        'src/geneweb_py/core/parser/gw_parser.py',
        'src/geneweb_py/core/parser/syntax.py',
        'src/geneweb_py/core/parser/streaming.py',
    ]

    fixed = 0
    for file_path in files:
        if Path(file_path).exists():
            if fix_file(file_path):
                print(f"✅ {file_path}")
                fixed += 1

    print(f"\n{fixed} fichiers corrigés")


if __name__ == '__main__':
    main()

