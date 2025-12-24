# RasPi5-Leo

Pequeño panel web con FastAPI para gestionar entradas/salidas GPIO en Raspberry Pi 5 usando `gpiozero` con `lgpio`.

## Configuración

- El archivo de configuración por defecto es `config/io.yaml`. Define las entradas y salidas con sus BCM, tipos y opciones (`active_high`, `pull_up`, etc.).
- Puedes cambiar la ruta con la variable de entorno `IO_CONFIG_PATH` o desde la propia interfaz web escribiendo la ruta y pulsando **Recargar config**.

Ejemplo de `config/io.yaml`:

```yaml
outputs:
  - id: led1
    name: "LED Principal"
    bcm: 17
    type: led
    active_high: true

inputs:
  - id: in1
    name: "Entrada demo"
    bcm: 22
    type: button
    pull_up: true
```

## Ejecución local

```bash
uvicorn app:app --reload --port 8000
```

En producción se usa Docker (ver `Dockerfile` y `docker-compose.yml`).
