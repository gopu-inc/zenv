---
layout: default
title: "Badges Zenv"
description: "Générateur et galerie de badges"
---

# Badges Zenv 🛡️

<div class="badge-workshop">
  <h2>Atelier de création</h2>
  
  <div class="workshop-controls">
    <div class="form-group">
      <label for="badge-label">Label (gauche):</label>
      <input type="text" id="badge-label" value="Zenv" placeholder="ex: Version">
    </div>
    
    <div class="form-group">
      <label for="badge-value">Valeur (droite):</label>
      <input type="text" id="badge-value" value="2.1.0" placeholder="ex: 1.0.0">
    </div>
    
    <div class="form-group">
      <label for="badge-color">Couleur:</label>
      <select id="badge-color">
        <option value="blue">Bleu</option>
        <option value="green">Vert</option>
        <option value="red">Rouge</option>
        <option value="orange">Orange</option>
        <option value="yellow">Jaune</option>
        <option value="purple">Violet</option>
        <option value="gray">Gris</option>
      </select>
    </div>
    
    <div class="form-group">
      <label for="badge-logo">Logo (optionnel):</label>
      <input type="text" id="badge-logo" placeholder="github, python, docker, ou base64...">
      <small class="help-text">Noms supportés: github, gitlab, python, docker, etc.</small>
    </div>
  </div>
  
  <button onclick="generateCustomBadge()" class="btn-generate">🎨 Générer le badge</button>
  
  <div id="badge-preview" class="badge-preview">
    <h3>Prévisualisation</h3>
    <div id="badge-image">
      <img src="{{ site.zenv_hub.api_url }}/badge/custom/Zenv/2.1.0/blue" alt="Badge preview">
    </div>
    
    <div class="badge-code">
      <h4>Code Markdown:</h4>
      <pre><code id="markdown-code">![Zenv: 2.1.0]({{ site.zenv_hub.api_url }}/badge/custom/Zenv/2.1.0/blue)</code></pre>
      
      <h4>URL SVG:</h4>
      <input type="text" id="svg-url" readonly value="{{ site.zenv_hub.api_url }}/badge/custom/Zenv/2.1.0/blue" class="url-display">
      
      <button onclick="copyToClipboard('svg-url')" class="btn-copy">📋 Copier l'URL</button>
    </div>
  </div>
</div>

<div class="badge-gallery">
  <h2>Galerie de badges</h2>
  
  <div id="badges-loading">
    <p>Chargement des badges...</p>
  </div>
  
  <div id="badges-grid" class="badges-grid" style="display: none;">
    <!-- Les badges seront injectés ici -->
  </div>
</div>

<div class="shields-info">
  <h2>Format Shields.io</h2>
  <p>Les badges sont compatibles avec le format shields.io. Exemple:</p>
  
  <pre><code>{{ site.zenv_hub.api_url }}/badge/shields/Zenv/2.1.0/blue/github/flat</code></pre>
  
  <p>Paramètres disponibles:</p>
  <ul>
    <li><strong>label</strong>: Texte de gauche</li>
    <li><strong>value</strong>: Texte de droite</li>
    <li><strong>color</strong>: Couleur du badge</li>
    <li><strong>logo</strong>: Nom du logo (optionnel)</li>
    <li><strong>style</strong>: Style (flat, plastic, flat-square, for-the-badge)</li>
  </ul>
</div>

<script>
let allBadges = [];

document.addEventListener('DOMContentLoaded', function() {
  loadBadges();
  
  // Mettre à jour la prévisualisation en temps réel
  document.getElementById('badge-label').addEventListener('input', updatePreview);
  document.getElementById('badge-value').addEventListener('input', updatePreview);
  document.getElementById('badge-color').addEventListener('change', updatePreview);
  document.getElementById('badge-logo').addEventListener('input', updatePreview);
  
  // Prévisualisation initiale
  updatePreview();
});

function updatePreview() {
  const label = document.getElementById('badge-label').value || 'Zenv';
  const value = document.getElementById('badge-value').value || '2.1.0';
  const color = document.getElementById('badge-color').value;
  const logo = document.getElementById('badge-logo').value;
  
  let url = `{{ site.zenv_hub.api_url }}/badge/custom/${encodeURIComponent(label)}/${encodeURIComponent(value)}/${color}`;
  if (logo) {
    url += `/${encodeURIComponent(logo)}`;
  }
  
  const img = document.getElementById('badge-image');
  img.innerHTML = `<img src="${url}" alt="${label}: ${value}" onerror="this.src='{{ site.zenv_hub.api_url }}/badge/custom/Error/Invalid/red'">`;
  
  // Mettre à jour le code Markdown
  document.getElementById('markdown-code').textContent = `![${label}: ${value}](${url})`;
  
  // Mettre à jour l'URL
  document.getElementById('svg-url').value = url;
}

function generateCustomBadge() {
  updatePreview();
  
  // Afficher un message de succès
  const preview = document.getElementById('badge-preview');
  const successMsg = document.createElement('div');
  successMsg.className = 'success-message';
  successMsg.textContent = 'Badge généré avec succès!';
  successMsg.style.cssText = `
    background: #d4edda;
    color: #155724;
    padding: 0.5rem;
    border-radius: 5px;
    margin: 1rem 0;
    text-align: center;
  `;
  
  preview.prepend(successMsg);
  
  // Supprimer le message après 3 secondes
  setTimeout(() => successMsg.remove(), 3000);
}

async function loadBadges() {
  try {
    const response = await fetch('{{ site.zenv_hub.api_url }}/api/badges');
    const data = await response.json();
    
    allBadges = data.badges || [];
    
    document.getElementById('badges-loading').style.display = 'none';
    document.getElementById('badges-grid').style.display = 'grid';
    
    displayBadges(allBadges);
  } catch (error) {
    console.error('Erreur chargement badges:', error);
    document.getElementById('badges-loading').innerHTML = 
      '<p class="error">❌ Impossible de charger les badges.</p>';
  }
}

function displayBadges(badges) {
  const grid = document.getElementById('badges-grid');
  
  if (badges.length === 0) {
    grid.innerHTML = '<p class="no-badges">Aucun badge créé.</p>';
    return;
  }
  
  let html = '';
  
  badges.forEach(badge => {
    const badgeUrl = badge.svg_url || `{{ site.zenv_hub.api_url }}/badge/svg/${badge.name}`;
    
    html += `
      <div class="badge-item">
        <div class="badge-image">
          <img src="${badgeUrl}" alt="${badge.label}: ${badge.value}">
        </div>
        
        <div class="badge-info">
          <h4>${badge.label}: ${badge.value}</h4>
          <p><strong>Nom:</strong> ${badge.name}</p>
          <p><strong>Couleur:</strong> ${badge.color || 'blue'}</p>
          ${badge.logo ? `<p><strong>Logo:</strong> ${badge.logo}</p>` : ''}
          <p><strong>Créé par:</strong> ${badge.created_by || 'System'}</p>
          <p><strong>Utilisations:</strong> ${badge.usage_count || 0}</p>
          
          <div class="badge-actions">
            <button onclick="copyBadgeCode('${badge.name}')" class="btn-small">
              📋 Copier
            </button>
            <a href="${badgeUrl}" target="_blank" class="btn-small">
              🔗 Lien
            </a>
          </div>
        </div>
      </div>
    `;
  });
  
  grid.innerHTML = html;
}

function copyBadgeCode(badgeName) {
  const url = `{{ site.zenv_hub.api_url }}/badge/svg/${badgeName}`;
  copyToClipboard(url, `![Badge](${url})`);
  
  // Feedback visuel
  alert('Code du badge copié dans le presse-papier!');
}

function copyToClipboard(elementId) {
  const element = document.getElementById(elementId);
  element.select();
  element.setSelectionRange(0, 99999);
  navigator.clipboard.writeText(element.value);
  
  // Feedback visuel
  const btn = event.target;
  const originalText = btn.textContent;
  btn.textContent = '✅ Copié!';
  setTimeout(() => btn.textContent = originalText, 2000);
}
</script>

<style>
.badge-workshop {
  background: #f8f9fa;
  padding: 2rem;
  border-radius: 10px;
  margin: 2rem 0;
}

.workshop-controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin: 1.5rem 0;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 2px solid #dee2e6;
  border-radius: 5px;
  font-size: 1rem;
}

.help-text {
  margin-top: 0.25rem;
  color: #666;
  font-size: 0.85rem;
}

.btn-generate {
  background: #0066ff;
  color: white;
  padding: 1rem 2rem;
  border: none;
  border-radius: 5px;
  font-size: 1rem;
  cursor: pointer;
  margin: 1rem 0;
}

.btn-generate:hover {
  background: #0056cc;
}

.badge-preview {
  background: white;
  padding: 2rem;
  border-radius: 10px;
  margin-top: 2rem;
  border: 2px solid #dee2e6;
}

.badge-preview h3 {
  margin-top: 0;
}

#badge-image {
  text-align: center;
  padding: 2rem;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  margin: 1rem 0;
}

#badge-image img {
  max-width: 100%;
  height: auto;
}

.badge-code {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #dee2e6;
}

.badge-code pre {
  background: #2d2d2d;
  color: #f8f9fa;
  padding: 1rem;
  border-radius: 5px;
  overflow-x: auto;
}

.url-display {
  width: 100%;
  padding: 0.75rem;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  margin: 0.5rem 0;
  font-family: 'Courier New', monospace;
}

.btn-copy {
  background: #6c757d;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-top: 0.5rem;
}

.btn-copy:hover {
  background: #5a6268;
}

.badge-gallery {
  margin: 3rem 0;
}

.badges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.badge-item {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 10px;
  overflow: hidden;
}

.badge-image {
  padding: 2rem;
  text-align: center;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.badge-image img {
  max-width: 100%;
  height: auto;
}

.badge-info {
  padding: 1.5rem;
}

.badge-info h4 {
  margin-top: 0;
  color: #0066ff;
}

.badge-info p {
  margin: 0.5rem 0;
  font-size: 0.9rem;
}

.badge-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-small {
  flex: 1;
  padding: 0.5rem;
  text-align: center;
  background: #6c757d;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  font-size: 0.85rem;
  border: none;
  cursor: pointer;
}

.btn-small:hover {
  background: #5a6268;
}

.no-badges {
  text-align: center;
  padding: 3rem;
  color: #666;
  font-style: italic;
}

.shields-info {
  background: #e7f1ff;
  padding: 2rem;
  border-radius: 10px;
  margin: 2rem 0;
}

.shields-info pre {
  background: #2d2d2d;
  color: #f8f9fa;
  padding: 1rem;
  border-radius: 5px;
  overflow-x: auto;
}

.shields-info ul {
  columns: 2;
  margin: 1rem 0;
}

.shields-info li {
  margin-bottom: 0.5rem;
}
</style>
