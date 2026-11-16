# Sarkari Sahayak: web chat UI

A text chat front end for Sarkari Sahayak, built with React 19, Vite, Tailwind CSS and Motion.
It shows example prompts, renders replies as markdown, and keeps the conversation history.

> **Status:** the UI runs, but no backend currently serves `/chat`, so every message gets the
> "trouble connecting" reply. See [Web Chat](../README.md#web-chat-in-progress) in the main README.

## Run it

```bash
npm install
npm run dev       # http://localhost:5173
```

Other scripts:

| Command | What it does |
| --- | --- |
| `npm run build` | Production build into `dist/` |
| `npm run preview` | Serves the production build locally |
| `npm run lint` | Lints with Oxlint |

## Backend

Each message is sent as `POST {VITE_API_URL}/chat` with `{ message, history }`, where `history` is
the earlier turns as `{ role: "user" | "assistant", content }`. The UI expects
`{ content, citation, cta }` back.

`VITE_API_URL` defaults to `http://localhost:8000`. To change it, create `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000
```

## Layout

- `src/App.jsx`: chat state and the `/chat` call
- `src/components/`: navbar, hero, example chips, chat input and messages, animated background
