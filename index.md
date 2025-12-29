# 🚀 ZENV Hub

<img src="assets/IMG_7694.png" alt="ZENV Logo" width="200" />

---
layout: default
title: "Zenv Package Hub"
description: "Gestionnaire de packages Zenv avec dépôt privé et accès public"
---

# Zenv Package Hub 🚀

**Interface web officielle pour le gestionnaire de packages Zenv**

<div class="hero">
  <div class="hero-content">
    <h2>Connecté à: <code>https://zenv-hub.onrender.com</code></h2>
    <p>Version API: <strong>2.1.0</strong> | Mode: <strong>Dépôt privé, accès public</strong></p>
  </div>
</div>

## Fonctionnalités principales

<div class="features">
  <div class="feature">
    <h3>📦 Gestion des Packages</h3>
    <ul>
      <li>Upload de packages .zv</li>
      <li>Téléchargement public</li>
      <li>Documentation automatique</li>
      <li>Gestion des versions</li>
    </ul>
  </div>
  
  <div class="feature">
    <h3>🛡️ Système de Badges</h3>
    <ul>
      <li>Badges SVG personnalisés</li>
      <li>Support logos intégrés</li>
      <li>Format shields.io</li>
      <li>Atelier de création</li>
    </ul>
  </div>
  
  <div class="feature">
    <h3>🔐 Sécurité</h3>
    <ul>
      <li>Tokens zenv_*</li>
      <li>Authentification JWT</li>
      <li>Rôles utilisateurs</li>
      <li>API sécurisée</li>
    </ul>
  </div>
</div>

## Statut du serveur

<div id="server-status" class="status-loading">
  <p>Vérification de la connexion au serveur...</p>
</div>

## Derniers packages

<div id="recent-packages">
  <p>Chargement des packages...</p>
</div>

## Statistiques rapides

<div class="stats">
  <div class="stat">
    <div class="stat-number" id="package-count">0</div>
    <div class="stat-label">Packages</div>
  </div>
  <div class="stat">
    <div class="stat-number" id="badge-count">0</div>
    <div class="stat-label">Badges</div>
  </div>
  <div class="stat">
    <div class="stat-number" id="api-version">2.1.0</div>
    <div class="stat-label">API Version</div>
  </div>
</div>

<script>
// Script pour charger les données dynamiques
document.addEventListener('DOMContentLoaded', function() {
  loadServerStatus();
  loadRecentPackages();
  loadStats();
});

async function loadServerStatus() {
  try {
    const response = await fetch('{{ site.zenv_hub.api_url }}/api/health');
    const data = await response.json();
    
    const statusDiv = document.getElementById('server-status');
    if (data.status === 'ok') {
      statusDiv.className = 'status-connected';
      statusDiv.innerHTML = `
        <p><strong>✅ Serveur connecté</strong></p>
        <p>GitHub: ${data.github} | Dernière vérification: ${new Date(data.timestamp).toLocaleString()}</p>
      `;
    } else {
      statusDiv.className = 'status-error';
      statusDiv.innerHTML = `<p><strong>❌ Problème de connexion</strong></p>`;
    }
  } catch (error) {
    const statusDiv = document.getElementById('server-status');
    statusDiv.className = 'status-error';
    statusDiv.innerHTML = `<p><strong>❌ Impossible de contacter le serveur</strong></p>`;
  }
}

async function loadRecentPackages() {
  try {
    const response = await fetch('{{ site.zenv_hub.api_url }}/api/packages');
    const data = await response.json();
    
    const packagesDiv = document.getElementById('recent-packages');
    if (data.packages && data.packages.length > 0) {
      let html = '<div class="package-list">';
      data.packages.slice(0, 5).forEach(pkg => {
        html += `
          <div class="package-item">
            <h4>${pkg.name} v${pkg.version}</h4>
            <p>${pkg.description || 'Pas de description'}</p>
            <a href="/packages/#${pkg.name}">Voir détails</a>
          </div>
        `;
      });
      html += '</div>';
      packagesDiv.innerHTML = html;
    } else {
      packagesDiv.innerHTML = '<p>Aucun package disponible.</p>';
    }
  } catch (error) {
    console.error('Erreur chargement packages:', error);
  }
}

async function loadStats() {
  try {
    const packagesRes = await fetch('{{ site.zenv_hub.api_url }}/api/packages');
    const packagesData = await packagesRes.json();
    document.getElementById('package-count').textContent = packagesData.count || 0;
    
    const badgesRes = await fetch('{{ site.zenv_hub.api_url }}/api/badges');
    const badgesData = await badgesRes.json();
    document.getElementById('badge-count').textContent = badgesData.count || 0;
    
    const versionRes = await fetch('{{ site.zenv_hub.api_url }}/api/version');
    const versionData = await versionRes.json();
    document.getElementById('api-version').textContent = versionData.api_version;
  } catch (error) {
    console.error('Erreur chargement stats:', error);
  }
}
</script>

<style>
.hero {
  background: linear-gradient(135deg, #0066ff 0%, #0099ff 100%);
  color: white;
  padding: 2rem;
  border-radius: 10px;
  margin: 2rem 0;
}

.hero-content h2 {
  margin-top: 0;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin: 3rem 0;
}

.feature {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #0066ff;
}

.status-connected {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
  padding: 1rem;
  border-radius: 5px;
  margin: 1rem 0;
}

.status-error {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 1rem;
  border-radius: 5px;
  margin: 1rem 0;
}

.status-loading {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  color: #856404;
  padding: 1rem;
  border-radius: 5px;
  margin: 1rem 0;
}

.stats {
  display: flex;
  gap: 2rem;
  margin: 2rem 0;
}

.stat {
  text-align: center;
  flex: 1;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: bold;
  color: #0066ff;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.package-list {
  margin: 1rem 0;
}

.package-item {
  background: white;
  border: 1px solid #dee2e6;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 5px;
}

.package-item h4 {
  margin-top: 0;
  color: #0066ff;
}
</style>
