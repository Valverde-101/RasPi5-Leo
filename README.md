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
uvicorn app:app --reload --port 8010
```

En producción se usa Docker (ver `Dockerfile` y `docker-compose.yml`).

## Ejecución en Raspberry Pi 5

### Opción A: Python directamente
1. (Opcional) Instala dependencias del sistema:
   ```bash
   sudo apt update && sudo apt install -y python3-venv python3-dev libgpiod-dev
   ```
2. Dentro del repositorio, crea y activa un entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Instala las dependencias del proyecto:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Ejecuta el servidor (usa `config/io.yaml` por defecto, o cambia la ruta con `IO_CONFIG_PATH`):
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8010
   # Ejemplo con otro YAML
   IO_CONFIG_PATH=/ruta/a/archivo.yaml uvicorn app:app --host 0.0.0.0 --port 8010
   ```

### Opción B: Docker / Docker Compose
1. Asegúrate de tener Docker y docker-compose instalados en la Pi.
2. Construye la imagen:
   ```bash
   docker compose build
   ```
3. Arranca el servicio (expone el puerto 8010 -> 8010):
   ```bash
   docker compose up -d
   ```
4. Abre la interfaz en `http://<IP_de_tu_Pi>:8010`.

Si obtienes un error de arranque relacionado con dispositivos (por ejemplo, `runc create failed`), revisa qué GPIO están disponibles en tu Pi y ajusta la lista en `docker-compose.yml`:

```bash
ls /dev/gpiochip* /dev/gpiomem*
```

Deja solo los que existan (por defecto se usan `/dev/gpiochip0` y `/dev/gpiomem`).

Para rehacer el contenedor desde cero (por ejemplo, tras editar el código o el `Dockerfile`), ejecuta estos comandos **desde la carpeta del proyecto en la Pi**:
```bash
docker compose down
docker compose build --no-cache
docker compose up -d --force-recreate
```

**Nota:** Si `entrypoint.sh` se edita en Windows, normaliza los finales de línea y marca el script como ejecutable:
```bash
sed -i 's/\r$//' entrypoint.sh
chmod +x entrypoint.sh
```
