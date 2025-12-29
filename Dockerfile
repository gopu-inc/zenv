# Image de base ZENV avec version
FROM zenv:1.0.0

# Définir le répertoire de travail
WORKDIR /app

# Copier le code source
COPY . .

# Installer les dépendances Python (si ton projet en utilise)
RUN pip install --no-cache-dir -r requirements.txt

# Ajouter des labels pour le branding et la traçabilité
LABEL org.opencontainers.image.title="ZENV"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.description="Image officielle ZENV pour déploiement"
LABEL org.opencontainers.image.authors="Ceose"
LABEL org.opencontainers.image.licenses="MIT"

# Définir la variable d'environnement VERSION
ENV ZENV_VERSION=1.0.0

# Healthcheck pour vérifier que le service est vivant
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD zenv --version || exit 1

# Définir l’entrypoint pour lancer ton CLI ZENV
ENTRYPOINT ["zenv"]

# Commande par défaut
CMD [""]
