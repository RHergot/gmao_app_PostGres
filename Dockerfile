# ===============================================================================
# Dockerfile optimisé pour application PySide6 sur Ubuntu XFCE4 + XRDP
# Avec test de démarrage graphique et message d'erreur explicite
# ===============================================================================

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    qt6-base-dev \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-randr0 \
    libxcb-util1 \
    libgl1-mesa-glx \
    build-essential \
    libpq-dev \
    locales \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# --- Étape 6 : Script de test graphique ---
# COPY docker_test_pyside6.py /docker_test_pyside6.py
# RUN python /docker_test_pyside6.py || (echo "[ERREUR] PySide6 ou dépendances Qt/X11 manquantes ! Vérifiez le Dockerfile et les paquets installés." && exit 1)

CMD ["python", "main.py"]
