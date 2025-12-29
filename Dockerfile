# Image de base ZENV avec version
FROM python:latest

# Définir le répertoire de travail
WORKDIR /app

# Mettre à jour le système et installer Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copier le code source
COPY . .

# Installer les dépendances Python
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install -e .
# Labels pour branding et traçabilité
LABEL org.opencontainers.image.title="ZENV"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.description="Image ZENV avec Python intégré"
LABEL org.opencontainers.image.authors="Ceose"
LABEL org.opencontainers.image.licenses="MIT"

# Exposer la version ZENV comme variable d'environnement
ENV ZENV_VERSION=1.0.0
ENV PYTHONUNBUFFERED=1

# Healthcheck pour vérifier que Python et ZENV sont disponibles
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python3 --version && zenv --version || exit 1

# Entrypoint pour lancer ton CLI ZENV
ENTRYPOINT ["zenv"]

# Commande par défaut
CMD [""]
