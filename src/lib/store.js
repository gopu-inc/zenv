import { writable } from 'svelte/store';

// État global de l'application
export const user = writable(null);
export const packages = writable([]);
export const badges = writable([]);
export const serverStatus = writable({ status: 'checking' });
export const loading = writable(false);
export const notifications = writable([]);

// Fonctions utilitaires
export function addNotification(message, type = 'info', duration = 3000) {
  const id = Date.now();
  notifications.update(n => [...n, { id, message, type }]);
  
  if (duration > 0) {
    setTimeout(() => {
      removeNotification(id);
    }, duration);
  }
  
  return id;
}

export function removeNotification(id) {
  notifications.update(n => n.filter(notification => notification.id !== id));
}
