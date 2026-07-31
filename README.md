<div align="center">

# Sarkari Sahayak

**Government welfare schemes, one phone call away.**

A multilingual voice **and** chat assistant that helps any citizen in India find the government
welfare schemes they actually qualify for — by calling a phone number or opening a website and
speaking naturally in their own language. No smartphone, no internet, no reading required.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![Pipecat](https://img.shields.io/badge/Pipecat-voice%20AI-5A45FF?style=flat-square)
![LiveKit](https://img.shields.io/badge/LiveKit-realtime-1FD5F9?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-gpt--oss-F55036?style=flat-square)
![Qdrant](https://img.shields.io/badge/Qdrant-vector%20DB-DC244C?style=flat-square)
![Langchain](https://img.shields.io/badge/LangChain-ffffff?logo=langchain&logoColor=green)

<sub>Built for the Agent&#123;a&#125;thon hackathon · Open Innovation Track · by Team **The Debuggers**</sub>

</div>

---

## Table of Contents

- [Overview](#overview)
- [The Problem](#the-problem)
- [Key Features](#key-features)
- [Live Demo](#live-demo)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Data and Schema](#data-and-schema)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Limitations and Roadmap](#limitations-and-roadmap)
- [Team](#team)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

India runs thousands of welfare schemes, but the people who need them most often cannot find or
claim them — the information sits behind text-heavy, mostly-English government portals that demand
strong reading and digital literacy.

**Sarkari Sahayak** removes that barrier entirely. It is an AI assistant with **two front doors**:

- **Voice** — call a regular phone number and talk in your own language. Works on any phone, even a
  basic keypad phone, with no internet or app.
- **Chat** — a web interface for users who are comfortable typing.

Both channels share one AI brain and one knowledge base of **3,397 real government schemes**. Ask in
plain language and it tells you what you qualify for, the benefits, the documents you need, and how
to apply — grounded in real scheme data, never invented.

---

## The Problem

- Welfare information is scattered, mostly in English, and buried in complex web portals.
- Eligibility rules (age, income, occupation, category) are left for the citizen to decode alone.
- Confusion between National, State, and Regional schemes makes it worse.
- The intended beneficiaries are left behind — many pay middlemen to find their benefits, or give up.

---

## Key Features

- **Voice + chat** — reachable by a phone call or the website.
- **Works on any phone** — even a keypad phone; no smartphone, internet, or app needed.
- **Multilingual** — understands and replies in Hindi, English, and Indian languages.
- **Grounded answers** — hybrid RAG over real scheme data; it will not invent schemes or amounts.
- **Eligibility-aware** — finds best-fit schemes, checks eligibility, and lists required documents.
- **Broad coverage** — National, State, and Regional schemes (3,397 in the database).
- **Built on free / low-cost infrastructure** — designed to scale without heavy costs.

---

## Live Demo

| Channel | Link |
| --- | --- |
| Web chat | [sarkari-sahayak-seven.vercel.app](https://sarkari-sahayak-seven.vercel.app) |
| Chat API (backend) | `https://sarkari-sahayak-chat.onrender.com` |
| Voice helpline | Demo line available on request <sub>(currently a Twilio trial number)</sub> |

> The Render free instance sleeps when idle, so the first chat request after a while may take a few
> seconds to wake it up.

---

## Architecture

Two front doors, one shared Groq brain, and a hybrid retrieval layer over 3,397 schemes.

![Architecture and flow](docs/architecture.png)

- **Voice path:** phone caller → Twilio (SIP) → LiveKit Cloud → the Pipecat bot (`main.py`), which
  runs VAD and turn-taking, speech-to-text, the LLM, and text-to-speech.
- **Chat path:** React frontend (Vercel) → FastAPI (`chat_server.py`, Render) → the same LLM.
- **Shared brain + retrieval:** the LLM calls a `search_schemes` tool, which embeds the question via
  Cloudflare Workers AI and runs a hybrid search in Qdrant, returning the matching schemes.

---

## How It Works

**Voice (real-time loop):** LiveKit moves the audio; Pipecat orchestrates the conversation. Audio
enters the pipeline, a VAD plus turn-detector decide when the caller has finished, speech is
transcribed, the language is locked for the call, the LLM answers (calling the scheme search when
needed), and the reply is spoken back through Sarvam TTS and out via LiveKit.

**Chat (request/response):** the browser holds the conversation history and POSTs each new message
(plus recent history) to `/chat`. FastAPI runs one turn through the same LLM and search, and returns
the answer. The server is stateless — the browser owns the conversation, the backend owns the
thinking.

**Retrieval (RAG):** every question is matched two ways at once — a dense vector (meaning) and a
BM25 sparse vector (keywords) — and the results are fused with Reciprocal Rank Fusion (RRF). The LLM
answers only from the returned schemes.

---

## Data and Schema

3,397 raw schemes are cleaned into a strict 39-field record (zero nulls), then stored as one hybrid
point per scheme in Qdrant.

![Data ingestion and schema](docs/schema.png)

- **One scheme = one searchable point** (no chunking) — every result comes back whole.
- **Content fields feed the AI** (description, benefits, eligibility, documents, how to apply);
  **metadata fields feed the filters** (government level, state, category).
- **Hybrid vectors:** a 1024-dim BGE-M3 dense vector (cosine) plus a BM25 sparse vector (IDF),
  fused by RRF at query time.
- **Pipeline:** `build_json_file_for_schemes.py` (clean) → `create_collection.py` (define vectors +
  indexes) → `ingest.py` (embed + upsert, resumable).

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Telephony / transport | Twilio (phone → SIP), LiveKit Cloud (real-time audio, SIP bridge) |
| Voice orchestration | Pipecat (VAD, turn-taking, pipeline) |
| Speech | Sarvam AI — `saaras` (STT) and `bulbul` (TTS) |
| LLM | Groq — `gpt-oss` (20B for voice, 120B for chat) |
| Retrieval | Qdrant Cloud (hybrid dense + BM25, RRF) · Cloudflare Workers AI — BGE-M3 embeddings |
| Chat backend | FastAPI (Python) |
| Frontend | React + Vite |
| Hosting | Vercel (frontend) · Render (chat API) · LiveKit Cloud · Qdrant Cloud |
| Data source | myScheme (Government of India) |

---

## Getting Started

### Prerequisites

- Python 3.11+ and Node.js 18+
- API keys / accounts for: **Groq**, **Sarvam AI**, **Qdrant Cloud**, **Cloudflare** (Workers AI),
  **LiveKit Cloud**, and **Twilio**

### 1. Clone

```bash
# clone the upstream repo (or your fork of it)
git clone https://github.com/Jagrit7/Sarkari-Sahayak.git
cd Sarkari-Sahayak
```

### 2. Backend setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-chat.txt   # covers the data pipeline + chat API
```

### 3. Environment variables

```bash
cp .env.example .env
# then open .env and fill in your keys (see Configuration below)
```

### 4. Build and ingest the scheme data

```bash
python data/build_json_file_for_schemes.py   # raw data -> clean 39-field JSON
python data/create_collection.py             # create the Qdrant collection + indexes
python data/ingest.py                         # embed + upsert all 3,397 schemes (resumable)
```

### 5. Run the voice agent

The voice agent needs the real-time voice stack on top of the chat deps — Pipecat with its
LiveKit, Silero VAD, Groq, and Sarvam integrations. Install those, then run:

```bash
python main.py
```

The bot connects out to LiveKit and joins the support room; incoming phone calls (via Twilio → SIP)
are bridged into that room.

### 6. Run the chat backend

```bash
uvicorn chat_server:app --reload --port 8000
```

### 7. Run the frontend

```bash
cd frontend
npm install
# point the frontend at your local API:
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## Project Structure

```
Sarkari-Sahayak/
├── main.py                          # Voice agent entrypoint (Pipecat pipeline)
├── server.py                        # LiveKit agent / worker server
├── chat_server.py                   # Text chat API (FastAPI) — deployed to Render
├── requirements-chat.txt            # Dependencies for the data pipeline + chat API
├── .env.example                     # Template for the required keys
├── .gitignore
├── scheme-setu demo.mpeg            # Voice agent demo recording
├── src/
│   ├── core/
│   │   ├── pipeline.py              # Assembles the Pipecat pipeline
│   │   ├── router.py               # Language detection / lock
│   │   ├── prompts.py              # System prompts (English / Hindi agents)
│   │   ├── transport.py            # LiveKit transport setup
│   │   └── config.py               # Settings loaded from environment
│   └── services/
│       ├── stt.py                  # Speech-to-text
│       ├── tts.py                  # Text-to-speech (Sarvam bulbul)
│       └── llm.py                  # Groq gpt-oss
├── data/
│   ├── build_json_file_for_schemes.py   # Raw scheme data -> clean 39-field JSON
│   ├── create_collection.py             # Define Qdrant collection + payload indexes
│   ├── ingest.py                        # Embed (Cloudflare) + upsert into Qdrant
│   ├── query.py                         # Hybrid search (dense + BM25, RRF)
│   ├── scheme_tool.py                   # search_schemes tool exposed to the LLM
│   └── common.py                        # Shared Qdrant / embedding config
├── frontend/                        # React + Vite chat UI (deployed to Vercel)
└── docs/                            # Architecture and schema diagrams
```

---

## Configuration

Set these in your `.env` (see `.env.example`):

| Variable | Used for |
| --- | --- |
| `LIVEKIT_API_KEY` | LiveKit Cloud authentication |
| `LIVEKIT_API_SECRET` | LiveKit Cloud authentication |
| `LIVEKIT_URL` | LiveKit project URL (`wss://...livekit.cloud`) |
| `GROQ_API_KEY` | Groq LLM (and Whisper STT, if used) |
| `SARVAM_API_KEY` | Sarvam speech (STT / TTS) |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud authentication |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Workers AI (BGE-M3 embeddings) |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers AI authentication |

The chat API only needs `GROQ_API_KEY`, the two `QDRANT_*`, and the two `CLOUDFLARE_*` keys.

---

## Deployment

- **Frontend → Vercel:** set the project root to `frontend/` and add `VITE_API_URL` pointing to your
  chat API (no trailing slash).
- **Chat API → Render:** Web Service. Build: `pip install -r requirements-chat.txt`. Start:
  `uvicorn chat_server:app --host 0.0.0.0 --port $PORT`. Add the Groq, Qdrant, and Cloudflare keys.
- **Voice agent:** runs as a long-lived worker that dials out to LiveKit, so it needs an always-on
  host (for example a free-tier VM) — or run it from your machine during demos.
- **Vector DB / embeddings:** Qdrant Cloud and Cloudflare Workers AI both have free tiers.

> Tip: on the free Render tier, a small keep-alive ping to `/health` prevents the chat instance from
> sleeping between requests.

---

## Limitations and Roadmap

**Current limitations**

- The scheme data is a one-time snapshot. Incremental refresh is built in (via a per-record
  `content_hash`) but is not yet wired to run automatically.
- Retrieval filtering can occasionally over-narrow (a state filter may bury large national schemes).
- No memory across calls or sessions; the current telephony setup handles one caller at a time
  (demo scale).

**Roadmap**

- **Live government data** — request official government API access to move off the static snapshot
  entirely.
- Smarter retrieval that reliably surfaces flagship national schemes.
- Voice-driven, end-to-end application auto-fill.
- Proactive alerts when a newly launched scheme matches a user's profile.
- WhatsApp integration, Panchayat-office kiosks, and deeper rural-dialect support.

---

## Team

**The Debuggers** — built for the Agent&#123;a&#125;thon hackathon (Open Innovation Track).

- Jagrit Goel — Team Lead
- Parth Krishan Goswami
- Milind Suman
- Soahum Trivedi

---

## License

Released under the [MIT License](LICENSE).

---

## Acknowledgements

- Scheme data from [myScheme](https://www.myscheme.gov.in/) (Government of India).
- Built with [Pipecat](https://www.pipecat.ai/), [LiveKit](https://livekit.io/),
  [Sarvam AI](https://www.sarvam.ai/), [Groq](https://groq.com/), [Qdrant](https://qdrant.tech/),
  and [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/).
