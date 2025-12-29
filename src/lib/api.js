import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'https://zenv-hub.onrender.com';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000
});

// Fonctions API
export async function getPackages() {
  try {
    const response = await api.get('/api/packages');
    return response.data.packages || [];
  } catch (error) {
    console.error('Erreur chargement packages:', error);
    return [];
  }
}

export async function getBadges() {
  try {
    const response = await api.get('/api/badges');
    return response.data.badges || [];
  } catch (error) {
    console.error('Erreur chargement badges:', error);
    return [];
  }
}

export async function getServerStatus() {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    return { status: 'error', github: 'disconnected' };
  }
}

export async function downloadPackage(name, version) {
  try {
    const response = await api.get(`/api/packages/download/${name}/${version}`, {
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    console.error('Erreur téléchargement:', error);
    return null;
  }
}

export async function login(username, password) {
  try {
    const response = await api.post('/api/auth/login', {
      username,
      password
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Login failed');
  }
}

export async function register(username, email, password) {
  try {
    const response = await api.post('/api/auth/register', {
      username,
      email,
      password
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Registration failed');
  }
}
