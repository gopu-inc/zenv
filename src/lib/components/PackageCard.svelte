<script>
  import { downloadPackage } from '$lib/api';
  import { addNotification } from '$lib/store';
  
  export let pkg;
  
  async function handleDownload() {
    try {
      const blob = await downloadPackage(pkg.name, pkg.version);
      if (blob) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = pkg.filename || `${pkg.name}-${pkg.version}.zv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        addNotification(`Package ${pkg.name} téléchargé!`, 'success');
      }
    } catch (error) {
      addNotification('Erreur de téléchargement', 'error');
    }
  }
  
  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
</script>

<div class="package-card">
  <div class="package-header">
    <h3>{pkg.name}</h3>
    <span class="version">v{pkg.version}</span>
  </div>
  
  <div class="package-body">
    <p class="description">{pkg.description || 'No description'}</p>
    
    <div class="meta">
      <span class="meta-item">
        <i class="fas fa-user"></i>
        {pkg.author || 'Unknown'}
      </span>
      <span class="meta-item">
        <i class="fas fa-file-alt"></i>
        {pkg.license || 'MIT'}
      </span>
      <span class="meta-item">
        <i class="fas fa-download"></i>
        {pkg.downloads_count || 0}
      </span>
    </div>
    
    <div class="size">
      <i class="fas fa-weight"></i>
      {formatBytes(pkg.size || 0)}
    </div>
  </div>
  
  <div class="package-footer">
    <button on:click={handleDownload} class="btn-download">
      <i class="fas fa-download"></i>
      Télécharger
    </button>
    
    <a href={`/packages/${pkg.name}`} class="btn-details">
      <i class="fas fa-info-circle"></i>
      Détails
    </a>
  </div>
</div>

<style>
  .package-card {
    background: white;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.3s, box-shadow 0.3s;
    display: flex;
    flex-direction: column;
  }
  
  .package-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.15);
  }
  
  .package-header {
    background: #0066ff;
    color: white;
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .package-header h3 {
    margin: 0;
    font-size: 1.2rem;
  }
  
  .version {
    background: rgba(255,255,255,0.2);
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
  }
  
  .package-body {
    padding: 1.5rem;
    flex: 1;
  }
  
  .description {
    color: #666;
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }
  
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
    font-size: 0.85rem;
    color: #888;
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 0.3rem;
  }
  
  .meta-item i {
    font-size: 0.8rem;
  }
  
  .size {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #0066ff;
    font-weight: 500;
    padding: 0.5rem;
    background: #f0f7ff;
    border-radius: 5px;
    font-size: 0.9rem;
  }
  
  .package-footer {
    padding: 1rem 1.5rem;
    background: #f8f9fa;
    border-top: 1px solid #eee;
    display: flex;
    gap: 0.75rem;
  }
  
  .btn-download, .btn-details {
    flex: 1;
    padding: 0.6rem;
    border: none;
    border-radius: 5px;
    font-size: 0.9rem;
    cursor: pointer;
    text-align: center;
    text-decoration: none;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all 0.3s;
  }
  
  .btn-download {
    background: #28a745;
    color: white;
  }
  
  .btn-download:hover {
    background: #218838;
  }
  
  .btn-details {
    background: #17a2b8;
    color: white;
  }
  
  .btn-details:hover {
    background: #138496;
  }
</style>
