layout: default
title: "Documentation API"
description: "Documentation complète de l'API Zenv Hub"
---

# Documentation API Zenv Hub 📚

**URL de base:** `{{ site.zenv_hub.api_url }}`

## Table des matières
1. [Authentification](#authentification)
2. [Packages](#packages)
3. [Badges](#badges)
4. [Documentation](#documentation)
5. [Utilisateurs](#utilisateurs)
6. [Zenv CLI](#zenv-cli)

## Authentification

### Login
```http
POST /api/auth/login
```

Body:

```json
{
  "username": "votre_username",
  "password": "votre_mot_de_passe"
}
```

Register

```http
POST /api/auth/register
```

Body:

```json
{
  "username": "nouvel_utilisateur",
  "email": "email@example.com",
  "password": "mot_de_passe"
}
```

Vérifier un token

```http
GET /api/tokens/verify?token=zenv_...
```
