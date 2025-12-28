<img width="1024" height="1024" alt="IMG_7694" src="https://github.com/user-attachments/assets/4a57a174-fcf5-498e-b3b7-95a0b6e05015" />

# 🚀 Zenv - Écosystème de développement complet
![Badge](https://zenv-hub.onrender.com/badge/svg/version)
![Zenv Version](https://img.shields.io/badge/Zenv-1.0.0-blue)
![Python Version](https://img.shields.io/badge/Python-3.7%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Zenv** est un écosystème complet de développement qui combine un runtime, un CLI et un gestionnaire de packages, conçu pour simplifier le développement avec une syntaxe Zenv intuitive.

## ✨ Fonctionnalités principales

- **🔄 Runtime Zenv** - Exécute directement les fichiers `.zv` et `.py`
- **📦 Gestionnaire de packages** - Installe, publie et gère les packages depuis Zenv Hub
- **⚡ Transpileur** - Convertit la syntaxe Zenv simplifiée en Python
- **🌱 Environnements virtuels** - Crée des environnements isolés
- **🏗️ Système de build** - Construit des packages depuis des manifestes `.zcf`
- **🔗 Hub intégré** - Publie et installe depuis [zenv-hub.onrender.com](https://zenv-hub.onrender.com)

## 🚀 Installation rapide

```bash
# Clonez le dépôt
git clone https://github.com/gopu-inc/zenv.git
cd zenv

# Installation
pip install -e .

# Vérifiez l'installation
zenv version
```
## ou via python 🐍
```
pip install zenv
```

📖 Guide d'utilisation

Commande de base

```bash
zenv [commande] [options]
```

Commandes disponibles

Commande Description Exemple
run Exécute un fichier .zv ou .py zenv run app.zv
build Construit un package depuis .zcf zenv build -f package.zcf
publish Publie sur Zenv Hub zenv publish dist/mon-package.zcf.gs
install Installe depuis le hub zenv install mon-package
venv Crée un environnement virtuel zenv venv mon-projet
init Initialise un projet zenv init mon-package
search Recherche des packages zenv search "web"
list Liste les packages installés zenv list
remove Supprime un package zenv remove mon-package
info Infos détaillées zenv info mon-package
hub Gestion du hub zenv hub status
version Affiche la version zenv version

🎯 Syntaxe Zenv

La syntaxe Zenv est une simplification de Python :

```zv
# Syntaxe Zenv simplifiée
print "Bonjour depuis Zenv!"

def saluer(nom):
    return "Bonjour " + nom + "!"

# Exécution
if __name__ == "__main__":
    resultat = saluer("Monde")
    print resultat
```

Transpilé en Python :

```python
print("Bonjour depuis Zenv!")

def saluer(nom):
    return "Bonjour " + nom + "!"

if __name__ == "__main__":
    resultat = saluer("Monde")
    print(resultat)
```

📦 Manifeste de package (.zcf)

Créez un fichier package.zcf :

```ini
[Zenv]
name = mon-package
version = 1.0.0
author = Votre Nom
description = Mon package Zenv
license = MIT

[File-build]
main = src/main.zv
include = 
    src/**/*.zv
    src/**/*.py
    README.md
exclude =
    tests/
    __pycache__/

[Dep.zv]
# Dépendances Zenv
zenv-utils = latest
zenv-web = 2.0.0

[Dep.py]
# Dépendances Python
requests = latest
flask = >=2.0.0

[Build]
type = zenv
output = dist/{name}-{version}.zcf.gs
compression = gzip
```

🛠️ Créer et publier un package

1. Initialiser un projet

```bash
zenv init mon-package
cd mon-package
```

2. Éditer les fichiers

· Modifiez src/main.zv (votre code Zenv)
· Configurez package.zcf (manifeste)

3. Construire le package

```bash
zenv build -f package.zcf
# Crée dist/mon-package-1.0.0.zcf.gs
```

4. Se connecter au hub

```bash
zenv hub login votre_token_zenv
```

5. Publier

```bash
zenv publish dist/mon-package-1.0.0.zcf.gs
```

🔧 Installation depuis Zenv Hub

```bash
# Se connecter (optionnel, pour packages privés)
zenv hub login votre_token_zenv

# Installer un package
zenv install mon-package

# Installer une version spécifique
zenv install mon-package@1.0.0
zenv install mon-package==1.0.0

# Vérifier l'installation
zenv list
zenv info mon-package

# Exécuter
zenv run ~/.zenv/packages/mon-package/src/main.zv
```

🌐 Zenv Hub

Le hub Zenv est disponible à : https://zenv-hub.onrender.com

Endpoints API

· GET /api/packages - Liste tous les packages
· GET /api/packages/download/{name}/{version} - Télécharge un package
· POST /api/packages/upload - Upload un package (authentification requise)
· GET /api/health - Vérifie l'état du serveur

Token d'authentification

Obtenez un token via :

· Interface web du hub
· Commande zenv hub login
· Token prédéfini admin : zenv_ead27bf9d1b91e30729eb574a82e7287d4c9f35df9f8feb4f581452444350a5b

🌱 Environnements virtuels

```bash
# Créer un environnement
zenv venv mon-env

# Activer
source mon-env/bin/zenv-activate

# Vérifier
echo $ZENV_ENV

# Installer des packages dans l'environnement
zenv install requests

# Désactiver
deactivate
```

📁 Structure des fichiers

```
~/.zenv/
├── packages/          # Packages installés
│   └── mon-package/
│       ├── src/
│       │   ├── main.zv
│       │   └── main.py
│       ├── package.json
│       └── __init__.py
├── cache/            # Cache système
└── token             # Token d'authentification
```

🧪 Exemples

Exemple 1 : Script simple

hello.zv :

```zv
print "Hello World!"
print "Version:", 1.0

def calculer(a, b):
    return a + b * 2

result = calculer(5, 3)
print "Résultat:", result
```

Exécution :

```bash
zenv run hello.zv
```

Exemple 2 : Package complet

Structure :

```
mon-app/
├── package.zcf
├── README.md
└── src/
    ├── __init__.zv
    ├── main.zv
    ├── utils.zv
    └── config.zv
```

🔍 Recherche de packages

```bash
# Rechercher
zenv search "utils"
zenv search "web"
zenv search ""  # Tous les packages

# Infos détaillées
zenv info zenv-utils
```

🗑️ Gestion des packages

```bash
# Lister
zenv list

# Supprimer
zenv remove mon-package

# Vérifier
zenv info mon-package  # "Package non trouvé"
```

🐛 Dépannage

Problèmes courants

1. "Token manquant"
   ```bash
   zenv hub login votre_token
   ```
2. Package non trouvé
   ```bash
   # Vérifier les packages disponibles
   zenv search ""
   # ou
   curl https://zenv-hub.onrender.com/api/packages
   ```
3. Erreur de transpilation
   · Vérifiez la syntaxe Zenv
   · Les fichiers doivent être UTF-8
4. Erreur d'exécution
   ```bash
   # Mode debug
   export ZENV_DEBUG=1
   zenv run fichier.zv
   ```

📚 API de développement

Importer dans Python

```python
from zenv.runtime.run import ZenvRuntime
from zenv.transpiler.tra import ZenvTranspiler
from zenv.builder.build import ZenvBuilder

# Runtime
runtime = ZenvRuntime()
runtime.execute("script.zv")

# Transpileur
transpiler = ZenvTranspiler()
python_code = transpiler.transpile(zv_code)

# Builder
builder = ZenvBuilder()
builder.build_from_manifest("package.zcf")
```

Extension du CLI

```python
from zenv.command.com import ZenvCLI

class MonCLI(ZenvCLI):
    def cmd_macommande(self, args):
        print("Ma commande personnalisée!")
        return 0
```

🏗️ Architecture

```
zenv/
├── __init__.py          # Configuration globale
├── __main__.py          # Point d'entrée
├── runtime/             # Runtime d'exécution
│   ├── __init__.py
│   └── run.py
├── command/             # Commandes CLI
│   ├── __init__.py
│   └── com.py
├── transpiler/          # Transpileur Zenv→Python
│   ├── __init__.py
│   └── tra.py
├── builder/             # Système de build
│   ├── __init__.py
│   └── build.py
└── tests/               # Tests unitaires
```

🤝 Contribution

1. Forkez le projet
2. Créez une branche (git checkout -b feature/ma-fonctionnalite)
3. Commitez (git commit -am 'Ajout de ma fonctionnalité')
4. Pushez (git push origin feature/ma-fonctionnalite)
5. Créez une Pull Request

📄 License

MIT License - Voir le fichier LICENSE pour plus de détails.

🙏 Remerciements

· Python - Le langage de base
· Render - Hébergement du Zenv Hub
· GitHub - Hébergement du code

📞 Support

· Issues GitHub : https://github.com/gopu-inc/zenv/issues
· Email : support@zenv.dev

---

Zenv - Simplifiez votre développement avec une syntaxe intuitive et un écosystème complet. 🚀
---

## 🎉 Prochaines étapes

1. **Ajouter plus de syntaxe Zenv** - Plus de simplifications
2. **Interface web pour le hub** - Interface utilisateur graphique
3. **Plugins** - Système d'extensions
4. **Intégration CI/CD** - Tests automatiques
5. **Documentation API** - Documentation détaillée
