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

## Django API

The Vue app loads marketplace listings from `/api/marketplace-listings/` and
Mthandizi businesses from `/api/businesses/` through Axios. During development,
Vite proxies `/api` requests to Django at `http://127.0.0.1:8000`.

The frontend uses lazy-loaded Vue Router pages:

- `/overview` for directory statistics and visual summaries
- `/marketplace` for marketplace listings
- `/businesses` for local business records

The root path redirects to `/overview`. Production hosting should serve
`index.html` as the fallback for these frontend routes.

Run Django from the repository root in one terminal:

```powershell
cd pg_scrap
..\.env\Scripts\python.exe manage.py runserver
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
