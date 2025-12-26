# .zv — Transpileur brandé vers Python

Ce dépôt fournit un transpileur strict pour le langage `.zv`, dérivé de Python, avec une syntaxe mythologique et gouvernée. Il lit du `.zv` et génère du Python exécutable.

## Installation locale

- Option 1: exécuter la CLI directement
```bash
python -m zenv_transpiler.cli examples/hello.zv --run
```

• Option 2: écrire le Python généré

```
python -m zenv_transpiler.cli examples/lists.zv -o out.py
python out.py
```

Règles principales

• Imports: zen[imoprt pkg], zen[import a.b from as c]
• Affectation: var ==> expr
• List append: list:apend[(item)]
• Print: zncv.[('text')]
• Interpolation: zncv.[('text $s' $ var)] → print(f"text {var}")
• Accès: second~name = name{{1}} → second_name = name[1]


Voir lock.znv pour la grammaire complète.


---

## Ce que ce transpilateur gère

- Imports brandés, y compris `from A.B import C` avec `from as`.
- Affectations simples et forme narrative commentée.
- Listes et append brandé `:apend[(...)]`.
- Indexation `{n}` → `[n]` partout.
- `zncv.[(...)]` pour print, avec interpolation via `$` en f-string.
- Alias avec `~` pour combiner des noms (`second~name` → `second_name`).

---

## Prochaines extensions possibles

- Interpolation multiple avec texte entre variables et support des doubles quotes.
- Opérateurs narratifs supplémentaires (`=+`, `~-`, pipelines brandés).
- Validation via un linter `.zv` et manifest enrichi (mots-clés réservés, version du langage).
- Packaging CLI avec entry point (`zenv`) via `pyproject.toml`.

---