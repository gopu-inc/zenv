<script>
  import { onMount } from 'svelte';
  import { getPackages, getServerStatus } from '$lib/api';
  import { packages, serverStatus, loading } from '$lib/store';
  import PackageCard from '$lib/components/PackageCard.svelte';
  
  let recentPackages = [];
  let stats = { packages: 0, badges: 0, apiVersion: '2.1.0' };
  let status = {};
  
  $packages.subscribe(value => {
    recentPackages = value.slice(0, 5);
    stats.packages = value.length;
  });
  
  $serverStatus.subscribe(value => status = value);
  $loading.subscribe(value => loading = value);
  
  onMount(async () => {
    await Promise.all([
      loadPackages(),
      loadServerStatus()
    ]);
  });
  
  async function loadPackages() {
    const data = await getPackages();
    packages.set(data);
  }
  
  async function loadServerStatus() {
    const data = await getServerStatus();
    serverStatus.set(data);
  }
</script>

<div class="home">
  <section class="hero">
    <h1>🚀 Zenv Package Hub</h1>
    <p class="subtitle">Gestionnaire de packages Zenv avec dépôt privé et accès public</p>
    
    <div class="server-info">
      <div class="info-item">
        <strong>API:</strong> https://zenv-hub.onrender.com
      </div>
      <div class="info-item">
        <strong>Version:</strong> 2.1.0
      </div>
      <div class="info-item">
        <strong>Mode:</strong> Dépôt privé, accès public
      </div>
    </div>
  </section>
  
  <section class="status-section">
    <h2>Statut du serveur</h2>
    <div class="status-card {status.status === 'ok' ? 'connected' : 'error'}">
      <div class="status-icon">
        {#if status.status === 'ok'}
          <i class="fas fa-check-circle"></i>
        {:else}
          <i class="fas fa-exclamation-circle"></i>
        {/if}
      </div>
      <div class="status-content">
        <h3>{status.status === 'ok' ? '✅ Connecté' : '❌ Problème de connexion'}</h3>
        <p>GitHub: {status.github || 'checking'} | Dernière vérification: {new Date().toLocaleTimeString()}</p>
      </div>
    </div>
  </section>
  
  <section class="stats-section">
    <h2>Statistiques</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number">{stats.packages}</div>
        <div class="stat-label">Packages</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{stats.badges}</div>
        <div class="stat-label">Badges</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{stats.apiVersion}</div>
        <div class="stat-label">Version API</div>
      </div>
    </div>
  </section>
  
  <section class="packages-section">
    <div class="section-header">
      <h2>Derniers packages</h2>
      <a href="/packages" class="btn-link">Voir tous →</a>
    </div>
    
    {#if loading}
      <div class="loading">Chargement...</div>
    {:else if recentPackages.length > 0}
      <div class="packages-grid">
        {#each recentPackages as pkg}
          <PackageCard {pkg} />
        {/each}
      </div>
    {:else}
      <div class="empty-state">
        <i class="fas fa-box-open"></i>
        <p>Aucun package disponible</p>
      </div>
    {/if}
  </section>
  
  <section class="features-section">
    <h2>Fonctionnalités</h2>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">
          <i class="fas fa-box"></i>
        </div>
        <h3>Gestion des Packages</h3>
        <ul>
          <li>Upload de packages .zv</li>
          <li>Téléchargement public</li>
          <li>Documentation automatique</li>
          <li>Gestion des versions</li>
        </ul>
      </div>
      
      <div class="feature-card">
        <div class="feature-icon">
          <i class="fas fa-shield-alt"></i>
        </div>
        <h3>Système de Badges</h3>
        <ul>
          <li>Badges SVG personnalisés</li>
          <li>Support logos intégrés</li>
          <li>Format shields.io</li>
          <li>Atelier de création</li>
        </ul>
      </div>
      
      <div class="feature-card">
        <div class="feature-icon">
          <i class="fas fa-lock"></i>
        </div>
        <h3>Sécurité</h3>
        <ul>
          <li>Tokens zenv_*</li>
          <li>Authentification JWT</li>
          <li>Rôles utilisateurs</li>
          <li>API sécurisée</li>
        </ul>
      </div>
    </div>
  </section>
</div>

<style>
  .home {
    display: flex;
    flex-direction: column;
    gap: 3rem;
  }
  
  .hero {
    text-align: center;
    padding: 3rem 1rem;
    background: linear-gradient(135deg, #0066ff 0%, #0099ff 100%);
    color: white;
    border-radius: 15px;
    margin-bottom: 2rem;
  }
  
  .hero h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
  
  .subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
    margin-bottom: 2rem;
  }
  
  .server-info {
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
    background: rgba(255,255,255,0.1);
    padding: 1rem;
    border-radius: 10px;
    max-width: 800px;
    margin: 0 auto;
  }
  
  .info-item {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  
  .status-section {
    margin-top: 2rem;
  }
  
  .status-card {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem;
    border-radius: 10px;
    background: white;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }
  
  .status-card.connected {
    border-left: 5px solid #28a745;
  }
  
  .status-card.error {
    border-left: 5px solid #dc3545;
  }
  
  .status-icon {
    font-size: 2.5rem;
  }
  
  .status-card.connected .status-icon {
    color: #28a745;
  }
  
  .status-card.error .status-icon {
    color: #dc3545;
  }
  
  .status-content h3 {
    margin: 0 0 0.5rem 0;
  }
  
  .stats-section {
    margin-top: 2rem;
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-top: 1rem;
  }
  
  .stat-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.3s;
  }
  
  .stat-card:hover {
    transform: translateY(-5px);
  }
  
  .stat-number {
    font-size: 3rem;
    font-weight: bold;
    color: #0066ff;
    margin-bottom: 0.5rem;
  }
  
  .stat-label {
    color: #666;
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .btn-link {
    background: #0066ff;
    color: white;
    padding: 0.5rem 1.5rem;
    border-radius: 5px;
    text-decoration: none;
    transition: background 0.3s;
  }
  
  .btn-link:hover {
    background: #0056cc;
  }
  
  .packages-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  
  .loading {
    text-align: center;
    padding: 3rem;
    color: #666;
  }
  
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #666;
  }
  
  .empty-state i {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.3;
  }
  
  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 1rem;
  }
  
  .feature-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border-top: 4px solid #0066ff;
  }
  
  .feature-icon {
    font-size: 2.5rem;
    color: #0066ff;
    margin-bottom: 1rem;
  }
  
  .feature-card h3 {
    margin-bottom: 1rem;
  }
  
  .feature-card ul {
    list-style: none;
    padding: 0;
  }
  
  .feature-card li {
    padding: 0.3rem 0;
    color: #666;
  }
  
  .feature-card li:before {
    content: "✓";
    color: #28a745;
    margin-right: 0.5rem;
  }
  
  @media (max-width: 768px) {
    .hero h1 {
      font-size: 2rem;
    }
    
    .server-info {
      flex-direction: column;
      gap: 1rem;
      text-align: left;
    }
    
    .status-card {
      flex-direction: column;
      text-align: center;
    }
    
    .packages-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
