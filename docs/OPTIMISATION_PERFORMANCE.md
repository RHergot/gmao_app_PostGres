# Optimisations Performance Windows - GMAO

## Configuration PostgreSQL Windows

1. **postgresql.conf** :
```ini
# Mémoire
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Checkpoints
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Parallélisme
max_worker_processes = 4
max_parallel_workers_per_gather = 2
```

2. **Variables d'environnement Python** :
```env
# Dans .env
PYTHONOPTIMIZE=1
PYTHONDONTWRITEBYTECODE=1
QT_SCALE_FACTOR=1.0
QT_AUTO_SCREEN_SCALE_FACTOR=0
```

## Optimisations code Python

1. **Connexions DB** - Pool de connexions :
```python
# Dans app/config.py
DATABASE_POOL_SIZE = 5
DATABASE_POOL_MAX_OVERFLOW = 10
```

2. **Cache de requêtes** :
```python
# Cache pour les requêtes fréquentes
from functools import lru_cache

@lru_cache(maxsize=100)
def get_machines_cached():
    # Requête mise en cache
    pass
```

3. **Threading pour UI** :
```python
# Requêtes en background
QTimer.singleShot(0, self.load_data_async)
```

## Configuration système Windows

1. **Services à désactiver** :
- Windows Search
- Superfetch/SysMain
- Windows Defender (si antivirus tiers)

2. **Configuration réseau** :
```
# Si PostgreSQL en local
host = localhost au lieu de 127.0.0.1
```

3. **SSD optimisé** :
- TRIM activé
- Indexation désactivée pour le dossier projet

## Monitoring performance

```python
# Ajout de métriques dans le dashboard
import time
import psutil

def log_performance_metrics():
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    logger.info(f"CPU: {cpu}%, RAM: {memory}%")
```
