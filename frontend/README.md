# frontend

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

## FastAPI backend

The Vue app loads marketplace listings from `/api/marketplace-listings/` and
Mthandizi businesses from `/api/businesses/` through Axios. The FastAPI backend
serves these endpoints and the scraper controls. During development, Vite proxies
`/api` requests to `http://127.0.0.1:8000`.
FastAPI reuses the Django `app_scrap` database tables, loading
`pg_scrap/.env` and its `DB_*` settings (or `DATABASE_URL`). If no database
settings are provided, it uses `pg_scrap/db.sqlite3`.

The `/home` endpoint is available for the FastAPI status page. The directory
endpoints retain their Django-compatible response shapes and trailing slashes.

The frontend uses lazy-loaded Vue Router pages:

- `/overview` for directory statistics and visual summaries
- `/marketplace` for marketplace listings
- `/businesses` for local business records
- `/settings` to run the Mthandizi business and featured-product scraper

The root path redirects to `/overview`. Production hosting should serve
`index.html` as the fallback for these frontend routes.

The Mthandizi scraper is started with `POST /api/scrape-mthandizi/`. The
frontend polls the returned run ID at `/api/scrape-mthandizi/<run-id>/` until
the run completes or fails. Existing business profiles are checked again so
new featured products can be discovered. Install the backend requirements and
start FastAPI from the repository root:

```powershell
.\.env\Scripts\python.exe -m pip install -r requirements.txt
.\.env\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Run the frontend from the repository root in another terminal:

```powershell
cd frontend
npm run dev
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```
