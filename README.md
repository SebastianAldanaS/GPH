# Steam Price Search

Una aplicación web para buscar precios de videojuegos en múltiples tiendas en línea.

## Características

- Búsqueda en Steam, Nuuvem, Fanatical, GreenManGaming e Instant Gaming
- Interfaz web simple y responsiva
- API RESTful construida con FastAPI
- Despliegue en Vercel

## Instalación Local

1. Clona el repositorio:
   ```bash
   git clone <tu-repo-url>
   cd steam-price-search
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Ejecuta la aplicación:
   ```bash
   python main.py
   ```

5. Abre http://127.0.0.1:8000 en tu navegador.

## Despliegue en Vercel

1. Conecta tu repositorio de GitHub a Vercel.

2. Vercel detectará automáticamente la configuración en `vercel.json` y `requirements.txt`.

3. El despliegue se hará automáticamente en cada push a la rama principal.

## Estructura del Proyecto

- `main.py`: Punto de entrada de la aplicación FastAPI
- `routes.py`: Definición de rutas de la API
- `static/`: Archivos estáticos del frontend (HTML, CSS, JS)
- `api/index.py`: Punto de entrada para Vercel
- `vercel.json`: Configuración de despliegue para Vercel
- `requirements.txt`: Dependencias de Python

## API Endpoints

- `GET /`: Página principal
- `GET /search`: Búsqueda en Steam
- `GET /nuuvem`: Búsqueda en Nuuvem
- `GET /fanatical`: Búsqueda en Fanatical
- `GET /greenmangaming`: Búsqueda en GreenManGaming
- `GET /instantgaming`: Búsqueda en Instant Gaming
- `GET /autocomplete`: Sugerencias de búsqueda

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request