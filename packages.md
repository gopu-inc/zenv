---
layout: default
title: "Packages Zenv"
description: "Explorer et gérer les packages Zenv"
---

# Packages Zenv 📦

<div class="package-controls">
  <input type="text" id="package-search" placeholder="Rechercher un package..." class="search-input">
  <button onclick="refreshPackages()" class="btn btn-refresh">🔄 Actualiser</button>
  <a href="/upload/" class="btn btn-primary">📤 Uploader un package</a>
</div>

<div id="packages-loading">
  <p>Chargement des packages...</p>
</div>

<div id="packages-container" style="display: none;">
  <div id="packages-stats" class="package-stats">
    <span id="total-packages">0</span> packages disponibles
  </div>
  
  <div id="packages-grid" class="packages-grid">
    <!-- Les packages seront injectés ici -->
  </div>
</div>

## API Endpoints pour les packages

<div class="api-endpoints">
  <div class="endpoint">
    <code>GET {{ site.zenv_hub.api_url }}/api/packages</code>
    <p>Lister tous les packages</p>
  </div>
  <div class="endpoint">
    <code>GET {{ site.zenv_hub.api_url }}/api/packages/download/&lt;name&gt;/&lt;version&gt;</code>
    <p>Télécharger un package</p>
  </div>
  <div class="endpoint">
    <code>GET {{ site.zenv_hub.api_url }}/api/readme/&lt;package&gt;</code>
    <p>Obtenir le README d'un package</p>
  </div>
  <div class="endpoint">
    <code>GET {{ site.zenv_hub.api_url }}/api/license/&lt;package&gt;</code>
    <p>Obtenir la licence d'un package</p>
  </div>
</div>

<script>
let allPackages = [];

document.addEventListener('DOMContentLoaded', function() {
  loadPackages();
  
  // Recherche en temps réel
  document.getElementById('package-search').addEventListener('input', function(e) {
    filterPackages(e.target.value);
  });
});

async function loadPackages() {
  try {
    const response = await fetch('{{ site.zenv_hub.api_url }}/api/packages');
    const data = await response.json();
    
    allPackages = data.packages || [];
    
    document.getElementById('packages-loading').style.display = 'none';
    document.getElementById('packages-container').style.display = 'block';
    
    document.getElementById('total-packages').textContent = allPackages.length;
    
    displayPackages(allPackages);
  } catch (error) {
    console.error('Erreur chargement packages:', error);
    document.getElementById('packages-loading').innerHTML = 
      '<p class="error">❌ Impossible de charger les packages. Vérifiez la connexion au serveur.</p>';
  }
}

function displayPackages(packages) {
  const grid = document.getElementById('packages-grid');
  
  if (packages.length === 0) {
    grid.innerHTML = '<p class="no-results">Aucun package trouvé.</p>';
    return;
  }
  
  let html = '';
  
  packages.forEach(pkg => {
    html += `
      <div class="package-card">
        <div class="package-header">
          <h3>${pkg.name}</h3>
          <span class="package-version">v${pkg.version}</span>
        </div>
        
        <div class="package-body">
          <p class="package-description">${pkg.description || 'Pas de description'}</p>
          
          <div class="package-meta">
            <span class="meta-item">👤 ${pkg.author || 'Unknown'}</span>
            <span class="meta-item">📜 ${pkg.license || 'MIT'}</span>
            <span class="meta-item">📥 ${pkg.downloads_count || 0} téléchargements</span>
          </div>
          
          <div class="package-size">
            <span class="size-label">Taille:</span>
            <span class="size-value">${formatBytes(pkg.size || 0)}</span>
          </div>
        </div>
        
        <div class="package-footer">
          <a href="${pkg.download_url || '#'}" class="btn-download" target="_blank">
            ⬇️ Télécharger
          </a>
          <a href="/api/#package-${pkg.name}" class="btn-info">
            ℹ️ Détails
          </a>
        </div>
      </div>
    `;
  });
  
  grid.innerHTML = html;
}

function filterPackages(searchTerm) {
  if (!searchTerm) {
    displayPackages(allPackages);
    return;
  }
  
  const filtered = allPackages.filter(pkg => 
    pkg.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (pkg.description && pkg.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (pkg.author && pkg.author.toLowerCase().includes(searchTerm.toLowerCase()))
  );
  
  displayPackages(filtered);
}

function refreshPackages() {
  document.getElementById('packages-loading').style.display = 'block';
  document.getElementById('packages-container').style.display = 'none';
  loadPackages();
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
</script>

<style>
.package-controls {
  display: flex;
  gap: 1rem;
  margin: 2rem 0;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #dee2e6;
  border-radius: 5px;
  font-size: 1rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn-primary {
  background: #0066ff;
  color: white;
}

.btn-refresh {
  background: #6c757d;
  color: white;
}

.btn:hover {
  opacity: 0.9;
}

.package-stats {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 5px;
  margin: 1rem 0;
  font-size: 1.1rem;
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.package-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 10px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.package-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.package-header {
  background: #0066ff;
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.package-header h3 {
  margin: 0;
  font-size: 1.2rem;
}

.package-version {
  background: rgba(255,255,255,0.2);
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
}

.package-body {
  padding: 1.5rem;
}

.package-description {
  margin: 0 0 1rem 0;
  color: #666;
  line-height: 1.5;
}

.package-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin: 1rem 0;
  font-size: 0.85rem;
  color: #888;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.package-size {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 5px;
}

.size-label {
  font-weight: bold;
}

.size-value {
  color: #0066ff;
  font-weight: bold;
}

.package-footer {
  padding: 1rem 1.5rem;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
  display: flex;
  gap: 1rem;
}

.btn-download, .btn-info {
  flex: 1;
  padding: 0.5rem;
  text-align: center;
  text-decoration: none;
  border-radius: 5px;
  font-size: 0.9rem;
}

.btn-download {
  background: #28a745;
  color: white;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.no-results {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-style: italic;
}

.error {
  color: #dc3545;
  text-align: center;
  padding: 2rem;
}

.api-endpoints {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 2px solid #dee2e6;
}

.endpoint {
  background: #f8f9fa;
  padding: 1rem;
  margin: 0.5rem 0;
  border-radius: 5px;
  font-family: 'Courier New', monospace;
  border-left: 3px solid #0066ff;
}

.endpoint p {
  margin: 0.5rem 0 0 0;
  color: #666;
  font-family: inherit;
}
</style>
