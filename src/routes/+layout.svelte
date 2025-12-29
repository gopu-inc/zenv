<script>
  import { page } from '$app/stores';
  import { user, notifications } from '$lib/store';
  import Nav from '$lib/components/Nav.svelte';
  import Notifications from '$lib/components/Notifications.svelte';
  
  let currentUser = null;
  $user.subscribe(value => currentUser = value);
</script>

<svelte:head>
  <title>Zenv Package Hub</title>
  <meta name="description" content="Gestionnaire de packages Zenv avec dépôt privé et accès public" />
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚀</text></svg>">
</svelte:head>

<div class="app">
  <Nav user={currentUser} />
  
  <main>
    <slot />
  </main>
  
  <footer>
    <p>Zenv Package Hub v2.1.0 | API: https://zenv-hub.onrender.com</p>
  </footer>
  
  <Notifications />
</div>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: #f8f9fa;
    color: #333;
  }
  
  main {
    flex: 1;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
  }
  
  footer {
    background: #2c3e50;
    color: white;
    text-align: center;
    padding: 1rem;
    margin-top: auto;
  }
  
  @media (max-width: 768px) {
    main {
      padding: 1rem;
    }
  }
</style>
