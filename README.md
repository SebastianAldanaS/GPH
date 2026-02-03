# Steam Price Search

Aplicación web para buscar precios de videojuegos en múltiples tiendas (Steam, Nuuvem, Fanatical, GreenManGaming, Instant Gaming). Incluye web scraping y uso de la API de Steam.

## Resumen del proyecto

- **Backend**: FastAPI que expone una API REST y, opcionalmente, sirve el frontend.
- **Fuentes de datos**:
  - **Steam**: API oficial (`store.steampowered.com/api/storesearch` y `appdetails`).
  - **Nuuvem / GreenManGaming / Instant Gaming**: scraping con `httpx` + BeautifulSoup.
  - **Fanatical**: API de CheapShark.
- **Frontend**: HTML/CSS/JS que consulta los endpoints y muestra resultados por tienda.

El proyecto está preparado para **despliegue separado**: frontend en **Vercel** y backend en **Railway**.

---

## Estructura

```
├── api/
│   ├── main.py          # App FastAPI, CORS, estáticos
│   ├── routes.py        # Rutas /search, /nuuvem, /fanatical, etc.
│   ├── schemas.py       # Modelos Pydantic (GamePrice, Suggestion, Preview)
│   ├── steam.py         # Búsqueda y precios Steam (API)
│   ├── cheapshark.py    # Fanatical vía CheapShark
│   ├── nuuvem.py        # Scraping Nuuvem
│   ├── greenmangaming.py
│   ├── instantgaming.py
│   ├── http_client.py   # Cliente httpx compartido
│   ├── utils.py         # Normalización de texto, similitud
│   └── static/          # Frontend cuando se sirve desde el mismo backend
├── frontend/            # Frontend para Vercel (usa API_BASE configurable)
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── config.js        # window.__API_BASE__ (vacío = mismo origen)
│   ├── package.json     # script build para inyectar VITE_API_URL en config.js
│   └── vercel.json
├── Procfile             # Railway: uvicorn api.main:app
├── railway.json
├── requirements.txt
└── README.md
```

---

## Instalación y ejecución local

1. Clona el repo y entra en la carpeta del proyecto.

2. Entorno virtual e dependencias:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. Ejecutar el backend (sirve API + estáticos en `api/static`):
   ```bash
   uvicorn api.main:app --reload
   ```
   Abre http://127.0.0.1:8000 (página principal y API).

4. Opcional: probar solo el frontend contra el backend local:
   - Abre `frontend/index.html` en el navegador o sirve la carpeta `frontend/` con un servidor estático.
   - Deja `config.js` con `window.__API_BASE__ = ""` y apunta las peticiones al mismo origen donde sirvas el backend (o configura un proxy).

---

## Despliegue: Vercel (frontend) + Railway (backend)

### 1. Backend en Railway

1. Crea un proyecto en [Railway](https://railway.app) y conecta este repositorio.
2. Railway usará el **root del repo** (donde están `api/`, `requirements.txt`, `Procfile`).
3. **Build**: Nixpacks detectará Python e instalará con `pip install -r requirements.txt`.
4. **Start**: el `Procfile` ejecuta:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
   (O configura en Railway el comando: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.)
5. Variables de entorno en Railway:
   - **CORS_ORIGINS**: URL del frontend en Vercel, p. ej. `https://tu-app.vercel.app`. Para permitir cualquier origen (solo desarrollo) puedes usar `*`.
6. Anota la URL pública del servicio (p. ej. `https://tu-proyecto.railway.app`).

### 2. Frontend en Vercel

1. Crea un proyecto en [Vercel](https://vercel.com) y conecta el mismo repositorio.
2. En **Settings → General** del proyecto:
   - **Root Directory**: `frontend` (importante).
   - **Framework Preset**: Other.
3. Variables de entorno:
   - **VITE_API_URL**: URL del backend en Railway, sin barra final (p. ej. `https://tu-proyecto.railway.app`).
4. En cada deploy, el script `npm run build` (en `frontend/package.json`) genera `config.js` con esa URL, y el frontend usará `window.__API_BASE__` para llamar al backend.
5. Despliega; la URL de Vercel será tu frontend (p. ej. `https://tu-app.vercel.app`).

### 3. Resumen de variables

| Dónde   | Variable      | Ejemplo                          |
|---------|---------------|----------------------------------|
| Railway | CORS_ORIGINS  | `https://tu-app.vercel.app`      |
| Vercel  | VITE_API_URL  | `https://tu-proyecto.railway.app`|

---

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Página principal (HTML) si hay `api/static`; si no, mensaje JSON |
| GET | `/health` | Estado del servicio (Railway/monitoreo) |
| GET | `/search` | Búsqueda Steam (+ merge con Instant Gaming) |
| GET | `/nuuvem` | Búsqueda Nuuvem |
| GET | `/fanatical` | Búsqueda Fanatical (CheapShark) |
| GET | `/greenmangaming` | Búsqueda GreenManGaming |
| GET | `/instantgaming` | Búsqueda Instant Gaming |
| GET | `/autocomplete` | Sugerencias (Steam) |
| GET | `/preview` | Vista previa de un juego por `appid` |

Parámetros comunes: `q` (texto), `cc` (código país, p. ej. `co`), `limit`.

---

## Notas

- **Scraping**: Nuuvem, GreenManGaming e Instant Gaming dependen del HTML actual de cada sitio; si cambian la estructura, puede ser necesario ajustar selectores en `api/nuuvem.py`, `api/greenmangaming.py` y `api/instantgaming.py`.
- **Steam**: usa la API pública de la tienda; no requiere API key.
- **CORS**: en producción conviene fijar `CORS_ORIGINS` en Railway a la URL exacta del frontend en Vercel en lugar de `*`.

## Contribución

1. Fork del proyecto.
2. Rama para tu cambio: `git checkout -b feature/nueva-funcionalidad`
3. Commit y push a la rama.
4. Abre un Pull Request.
