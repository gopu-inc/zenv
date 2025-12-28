<img width="280" height="280" alt="IMG_7694" src="https://github.com/user-attachments/assets/4a57a174-fcf5-498e-b3b7-95a0b6e05015" />

# 🚀 Zenv - Écosystème de développement complet
[![PyPI version](https://img.shields.io/pypi/v/zenv-lang.svg)](https://pypi.org/project/zenv-lang/)
![Badge](https://zenv-hub.onrender.com/badge/svg/version)
![Zenv Version](https://img.shields.io/badge/Zenv-1.0.0-blue)
![Python Version](https://img.shields.io/badge/Python-3.7%2B-green)
![License](https://img.shields.io/badge/License-MIT-black)
[![Publish to PyPI](https://github.com/gopu-inc/zenv/actions/workflows/publish-pypi.yml/badge.svg)](https://github.com/gopu-inc/zenv/actions/workflows/publish-pypi.yml)
> **Zenv Programming Language powered by gopu.inc**

<div>
    
Zenv est un langage de programmation moderne et expressif qui transpile vers Python.
Une syntaxe élégante, un système de packages complet et une intégration transparente avec Python.

Installation •
Documentation •
Exemples •
Packages •
Contribution

</div>✨ Fonctionnalités

· Syntaxe moderne - Plus lisible et expressive que Python
· Transpileur rapide - Conversion Zenv → Python en temps réel
· Système de packages - Installation, gestion et publication
· Hub communautaire - Partagez vos packages avec la communauté
· Interopérabilité Python - Utilisez toutes les bibliothèques Python
· Type checking optionnel - Support des annotations de type
· Async/await natif - Programmation asynchrone simplifiée

## 🚀 Installation

Installation directe

```bash
# Clonez le repository
git clone https://github.com/gopu-inc/zenv.git
cd zenv

# Installation
pip install -e .

# Vérifiez l'installation
zenv version
```

Via pip

```bash
pip install zenv-lang
```

## 📖 Documentation Rapide

Syntaxe de base

```zenv
// Commentaire simple
print "Hello Zenv!"

// Variables
var nom = "Alice"
let age = 30
const PI = 3.14159

// Fonctions
function saluer(personne):
    return "Bonjour " + personne + "!"

// Conditions
if age > 18 then:
    print "Majeur"
else:
    print "Mineur"

// Boucles
for i in range(5) do:
    print "Itération: " + i

while x > 0 do:
    print x
    x = x - 1

// Classes
class Personne:
    function __init__(self, nom, age):
        self.nom = nom
        self.age = age
    
    function presentation(self):
        return self.nom + " a " + self.age + " ans"

// String interpolation
let message = "Nom: #{nom}, Age: #{age}"
```

## Structures de données

```zenv
// Listes
let fruits = list("pomme", "banane", "orange")
fruits.append("kiwi")

// Dictionnaires
let personne = dict()
personne["nom"] = "Bob"
personne["age"] = 25

// Sets
let nombres = set(1, 2, 3, 3, 4)  // {1, 2, 3, 4}

// Tuples
let coord = tuple(45.5, -73.5)
```

## Programmation fonctionnelle

```zenv
// Lambdas
let doubler = lambda x => x * 2
let addition = lambda a, b => a + b

// Map/Filter
let nombres = [1, 2, 3, 4, 5]
let carres = map(lambda x => x * x, nombres)
let pairs = filter(lambda x => x % 2 == 0, nombres)

// List comprehensions
let carres = [for x in nombres if x > 2 => x * x]
```

## 🎯 Utilisation

Exécution de code

```bash
# Exécuter un fichier .zv
zenv run programme.zv

# Avec des arguments
zenv run programme.zv arg1 arg2

# Transpiler vers Python
zenv transpile programme.zv -o programme.py

# Valider la syntaxe
zenv validate programme.zv
```

Création de packages

• 1. Initialiser un projet :

```bash
mkdir mon-package
cd mon-package
```

• 1. Créer package.zcf :

```ini
[Zenv]
name = mon-package
version = 1.0.0
author = Votre Nom
description = Description du package
license = MIT

[File-build]
main = main.zv
files = *.zv
        README.md
        LICENSE

[docs]
description = README.md

[dep.zv]
# Dépendances Zenv
zenv-stdlib = 1.0.0

[dep.py]
# Dépendances Python
requests = latest
```

• 1. Créer main.zv :

```zenv
print "Mon package Zenv!"

function hello(name):
    return "Hello " + name + "!"

if __name__ == "__main__":
    print hello("World")
```

• 1. Build le package :

```bash
zenv build -f package.zcf
# Génère: dist/mon-package-1.0.0.zv
```

## Gestion des packages

```bash
# Se connecter au Zenv Hub
zenv hub login zenv_votre_token

# Publier un package
zenv hub publish dist/mon-package-1.0.0.zv

# Rechercher des packages
zenv hub search "web framework"

# Installer un package
zenv pkg install requests

# Lister les packages installés
zenv pkg list

# Supprimer un package
zenv pkg remove package-name
```

## 📦 Zenv Hub

Le Zenv Hub est le registre central des packages Zenv.

## Accès au Hub

· URL: https://zenv-hub.vercel.app
· Token: zenv_d57203aef4ed4584a0e2986bcded9172375d1903887a......

Endpoints API

```bash
# Vérifier le statut
zenv hub status

# Rechercher des packages
zenv hub search "database"

# Publier
zenv hub publish mon-package.zv

# Télécharger (via pkg install)
zenv pkg install nom-package
```

## 🏗️ Architecture

```
zenv/
├── zenv/                    # Code source
│   ├── __init__.py
│   ├── cli.py              # Interface en ligne de commande
│   ├── transpiler.py       # Transpileur Zenv → Python
│   ├── runtime.py          # Runtime d'exécution
│   ├── builder.py          # Système de build de packages
│   ├── hub/                # Client pour Zenv Hub
│   └── utils/              # Utilitaires
├── examples/               # Exemples de code
├── tests/                  # Tests unitaires
├── setup.py               # Configuration d'installation
└── README.md              # Ce fichier
```

## Structure de transpilation

```
Zenv Code (.zv) → Transpileur → Python Code (.py) → Interpréteur Python
     │                              │
     ├── Syntaxe moderne           ├── Compatible Python 3.7+
     ├── String interpolation      ├── Performance native
     └── Mot-clés en français      └── Accès à tout l'écosystème Python
```

## 📚 Exemples Complets

Exemple 1: Application Web

```zenv
// webapp.zv
from flask import Flask, jsonify
import json

app = Flask(__name__)

class Utilisateur:
    function __init__(self, nom, email):
        self.nom = nom
        self.email = email
    
    function to_dict(self):
        return {
            "nom": self.nom,
            "email": self.email
        }

@app.route("/")
function accueil():
    return "Bienvenue sur mon app Zenv!"

@app.route("/api/utilisateurs")
function get_utilisateurs():
    utilisateurs = [
        Utilisateur("Alice", "alice@example.com"),
        Utilisateur("Bob", "bob@example.com")
    ]
    return jsonify([u.to_dict() for u in utilisateurs])

if __name__ == "__main__":
    app.run(debug=true)
```

## Exemple 2: Traitement de données

```zenv
// data_processing.zv
function charger_donnees(fichier):
    with open(fichier, 'r') as f:
        return json.load(f)

function traiter(donnees):
    // Filtre
    let filtrees = filter(lambda x: x["actif"], donnees)
    
    // Transformation
    let transformees = map(lambda x: {
        "nom": x["nom"].upper(),
        "valeur": x["score"] * 2
    }, filtrees)
    
    // Agrégation
    let total = reduce(lambda acc, x: acc + x["valeur"], transformees, 0)
    
    return {
        "nombre": len(transformees),
        "total": total,
        "moyenne": total / len(transformees) if transformees else 0
    }

function main():
    let donnees = charger_donnees("data.json")
    let resultats = traiter(donnees)
    print "Résultats: " + str(resultats)

if __name__ == "__main__":
    main()
```

## Exemple 3: Async/Await

```zenv
// async_demo.zv
import asyncio
import aiohttp

async function fetch_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async function main():
    let urls = [
        "https://api.example.com/data1",
        "https://api.example.com/data2",
        "https://api.example.com/data3"
    ]
    
    // Exécution parallèle
    let tasks = [fetch_url(url) for url in urls]
    let results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print f"Résultat {i}: {len(result)} caractères"

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Configuration

Fichier de configuration utilisateur

```json
// ~/.zenv/config.json
{
    "user": {
        "name": "Votre Nom",
        "email": "votre@email.com"
    },
    "hub": {
        "url": "https://zenv-hub.onrender.com",
        "auto_update": true
    },
    "transpiler": {
        "strict_mode": false,
        "auto_format": true
    }
}
```

Variables d'environnement

```bash
export ZENV_HUB_TOKEN="zenv_votre_token"
export ZENV_DEBUG="true"
export ZENV_CACHE_DIR="$HOME/.zenv/cache"
```

## 📊 Comparaison avec Python

Fonctionnalité Zenv Python
String interpolation "Nom: #{nom}" f"Nom: {nom}"
Déclaration fonction function nom(): def nom():
Condition if x then: if x:
Boucle for for i in range(5) do: for i in range(5):
Variables immuables let x = 5 x = 5
Classes class Nom: class Nom: Import from module import func from module import func

## 🚢 Déploiement

#### Pour les applications

```bash
# 1. Transpiler vers Python
zenv transpile app.zv -o app.py

# 2. Créer requirements.txt
echo "flask==2.3.0" > requirements.txt

# 3. Déployer comme une app Python normale
```

## Pour les packages

```bash
# 1. Build le package
zenv build -f package.zcf

# 2. Publier sur le hub
zenv hub publish dist/*.zv

# 3. Les autres peuvent installer
zenv pkg install votre-package
```

## 🧪 Tests

Tests unitaires

```bash
# Exécuter tous les tests
python -m pytest tests/

# Tests spécifiques
python -m pytest tests/test_transpiler.py

# Avec couverture
python -m pytest --cov=zenv tests/
```

## Exemple de test

```python
# tests/test_basics.py
import pytest
from zenv.transpiler import ZenvTranspiler

def test_print_statement():
    transpiler = ZenvTranspiler()
    zv_code = 'print "Hello"'
    python_code = transpiler.transpile(zv_code)
    assert python_code == 'print("Hello")'
```

## 🤝 Contribution

Les contributions sont les bienvenues !

Processus de contribution

1. Fork le projet
2. Créer une branche (git checkout -b feature/ma-fonctionnalite)
3. Commit les changements (git commit -m 'Ajout de ma fonctionnalité')
4. Push vers la branche (git push origin feature/ma-fonctionnalite)
5. Ouvrir une Pull Request

## Guide de style

· Suivre PEP 8 pour le code Python
· Documenter les nouvelles fonctions
· Ajouter des tests pour les nouvelles fonctionnalités
· Mettre à jour la documentation

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🙏 Remerciements

· Python - Pour l'écosystème incroyable
· Flask - Pour l'inspiration de simplicité
· La communauté open-source - Pour toutes les contributions

## 📞 Support

· Issues GitHub: Signaler un bug
· Documentation: Lire la docs
· Communauté: Rejoindre le Discord

---

<div align="center">Zenv - Écrivez moins, faites plus.
Un langage moderne pour des développeurs modernes.

🚀 Commencer maintenant •
📚 Voir les exemples •
📦 Explorer les packages

</div>📝 Journal des versions

v1.0.0 (Actuel)

· ✅ Transpileur complet Zenv → Python
· ✅ Système de packages fonctionnel
· ✅ Zenv Hub avec publication/téléchargement
· ✅ CLI intuitive avec toutes les commandes
· ✅ Support async/await
· ✅ String interpolation
· ✅ Classes et héritage

Prochaines versions

· Système de modules amélioré
· Type checking statique
· Débogueur intégré
· IDE extensions (VS Code, PyCharm)
· Compilation vers WebAssembly
· Support multi-threading avancé

🔗 Liens utiles

· [📖 Documentation complète](https://zenv-hub.vercel.app/#)
· [🐛 Signaler probleme](https://github.com/gopu-inc/zenv/issues)
· [💡 Suggestions de fonctionnalités](https://pypi.org/project/zenv-lang)
· [📦 Packages populaires](https://zenv-hub.onrender.com/api/packages/download/test-package/1.0.0)
· [👥 Communauté Discord](https://discord.gg/qWx5DszrC)

---

<div align="center">💝 Soutenez le projet

Si Zenv vous est utile, pensez à :

· ⭐ Star le projet sur GitHub
· 🐛 Signaler les bugs
· 💡 Proposer des fonctionnalités
· 📢 Parler de Zenv autour de vous

Ensemble, construisons l'avenir de la programmation !

</div>
