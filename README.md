<p align="center">
  <img src="./asset/banner.svg" alt="SarkariSahayak Banner" width="100%"/>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Built%20at-HackBlr%202026-0D9488" alt="HackBlr 2026"/></a>
  <a href="https://vapi.ai"><img src="https://img.shields.io/badge/Voice-Vapi-14B8A6" alt="Vapi"/></a>
  <a href="https://qdrant.tech"><img src="https://img.shields.io/badge/Vectors-Qdrant-DC382D" alt="Qdrant"/></a>
  <a href="https://cohere.com"><img src="https://img.shields.io/badge/Embeddings-Cohere%20Multilingual-39594D" alt="Cohere"/></a>
  <a href="https://groq.com/"><img src="https://img.shields.io/badge/LLM-Groq%20·%20Llama%203.1%208B-F55036" alt="Groq Llama 3.1 8B"/></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/Backend-FastAPI-009688" alt="FastAPI"/></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.11-3776AB" alt="Python"/></a>
  <a href="#-license"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"/></a>
</p>

<p align="center">
  <b>📞 Try the live demo: <a href="tel:+13463968319">+1 (346) 396-8319</a></b><br/>
  <i>Speak in Hindi, English, Gujarati, Bengali, Tamil, Marathi, Telugu, or Kannada. The agent will follow you.</i>
</p>

---

## 📖 About

**SarkariSahayak** (सरकारी सहायक · *"Government Helper"*) is a voice-first AI agent that connects every Indian to the welfare schemes they're entitled to. No app. No typing. No internet literacy. No smartphone. Just a phone call.

Pick up any phone, dial the number, and speak — in your language, in your accent, the way you'd talk to a neighbour. The agent listens, retrieves from a vector store of **3,500+ central and state schemes**, and answers in the same language you spoke in.

In one conversation, the agent will:

- ✅ Check **eligibility** across schemes based on what you tell it about yourself
- 📄 List the exact **documents** you'll need
- 🧭 Walk you through the **application** — which office, which form, which follow-up

### 🎯 The Gap We're Closing

The schemes exist. The money is allocated. The portals are live. And yet:

- **53%** of India's salaried workforce has no social security
- **652 million** Indians are still offline (44.7% of the population)
- Only **25%** of rural India is digitally literate
- The gap from *eligible* → *applied* loses **38%** of citizens
- The gap from *applied* → *received* loses another **50%**

The bottleneck isn't policy. It's the last mile — forms, portals, jargon, and the assumption that every citizen has a smartphone, a steady connection, and the literacy to navigate a 12-step web flow. **Voice is the universal interface.** Everyone has a phone. Everyone can speak.

---

## 🎬 Demo

**📞 Call:** [+1 (346) 396-8319](tel:+13463968319) *(US demo number — speak any of our 8 supported languages; toll-free Indian number planned for production)*

**🌐 Try in browser:** [vapi.ai demo link](https://vapi.ai?demo=true&shareKey=ef81dd68-8514-448d-bcf7-608ce022edb6&assistantId=8b91da34-242e-4ecb-8342-92fd31e68f4f)

---

## ✨ Features

- 🎤 **Voice-first** — natural conversation, zero typing, zero forms
- 🌐 **8 languages** — Hindi, English, Gujarati, Bengali, Tamil, Marathi, Telugu, Kannada — with mid-conversation code-switching
- 🧠 **3,500+ schemes** — central + state, retrieved live from a Qdrant vector store
- ✅ **Personalised eligibility** — context-aware matching against the caller's profile
- 📄 **Document & application guidance** — what to bring, where to go, what to do next
- ⚡ **Sub-second latency** — Groq's LPU inference keeps the conversation feeling human
- 📱 **Works on any phone** — landline, feature phone, smartphone. No app, no internet, no install.

---

## 🔄 How It Works

<p align="center">
  <img src="./asset/flow.svg" alt="User Flow - 4 Steps" width="100%"/>
</p>

```
Caller  →  Vapi (STT)  →  Cohere (embed)  →  Qdrant (search)  →  Groq (Llama 3.1 8B)  →  Vapi (TTS)  →  Caller
```

1. **Caller dials in** and speaks naturally. Vapi handles the telephony and transcribes the speech in real time, auto-detecting the spoken language.
2. **The query is embedded** by Cohere's multilingual model into a shared vector space — Bengali queries and Hindi/English scheme docs live in the same space.
3. **Qdrant retrieves** the most relevant schemes via cosine similarity over the 3,500+ scheme corpus.
4. **Groq generates** a grounded response with Llama 3.1 8B Instant, citing scheme names explicitly.
5. **Vapi speaks the reply** back in the same language the caller used.

End-to-end round-trip target: **under one second**.

---

## 🏗️ Architecture

<p align="center">
  <img src="./asset/architecture.svg" alt="System Architecture" width="100%"/>
</p>

**Data flow:** Voice In → Vapi (STT, lang-detect) → FastAPI orchestration → Cohere embed → Qdrant retrieval → Groq (Llama 3.1 8B Instant) → FastAPI response → Vapi (TTS) → Voice Out

---

## 🧠 Engineering Notes

The interesting decisions — and the ones a judge or reviewer is likely to ask about.

### 1. Why Vapi over Twilio + Whisper + ElevenLabs?

Stitching telephony, STT, and TTS yourself is three vendors, three latency budgets, and three failure modes. Vapi collapses the voice loop into one provider purpose-built for conversational agents, with built-in barge-in handling and language auto-detection. For a hackathon-scale build, the engineering time saved is the entire point.

### 2. Language detection happens at the edge

We don't run a separate language-ID step. **Vapi's STT auto-detects the spoken language and tags each utterance.** That tag flows through the whole pipeline — the LLM sees it, and we instruct Llama to respond in the detected language. One round-trip, no extra model, no extra latency.

### 3. Cross-lingual retrieval without a translation step

A caller asks in Bengali. The scheme documents are in English and Hindi. The naive solution is to translate the query — but that's another model call, another point of failure, and another 200ms of dead air.

Instead, we use **Cohere's multilingual embeddings**, which place text from all our supported languages into a single shared vector space. A Bengali query's embedding lands near the Hindi/English document embeddings that are semantically related to it. Qdrant does cosine similarity over that shared space and returns the right schemes. No translation step exists.

This is also why we picked Cohere over OpenAI's embedding models — Cohere's multilingual models handle Indic languages noticeably better, which matters when half your supported languages are Indic.

### 4. Groq for latency, not raw model quality

In a voice agent, every 200ms of generation latency shows up as awkward dead air the caller can hear. **Groq's LPU inference is the fastest available for Llama 3.1 8B**, and at this task — RAG-grounded answers over a small retrieved context — 8B is plenty. We'd rather have a fast 8B model and a snappy conversation than a slow 70B model and a caller who hangs up.

### 5. Hallucination guardrails for a high-stakes domain

"The agent told my grandmother the wrong scheme" is a real, harmful failure mode for a government-info bot. Three layers of defence:

- **RAG-grounded prompts.** The system prompt instructs the model to answer only from retrieved scheme documents and to cite scheme names explicitly in every response.
- **Confidence-aware fallback.** When Qdrant's top retrieval scores are below threshold, the agent says *"I'm not sure about this — please call the official helpline at 1800-XXX"* rather than guessing.
- **Scheme-name citation.** Every claim is anchored to a named scheme, so the caller can independently verify and so the agent can't drift into generic policy advice.

RAG reduces hallucination. It doesn't eliminate it. We're honest about that.

### 6. Why CPU-only embeddings at runtime?

Cohere is hosted, so embeddings are an HTTP call — no GPU footprint on our backend. This lets us deploy on Render's free tier without a model server, which keeps the whole stack cheap enough that a real deployment to a state government wouldn't be blocked by infra cost.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Voice / Telephony** | [Vapi.ai](https://vapi.ai) | Real-time STT + TTS, language auto-detect, telephony |
| **Embeddings** | [Cohere Multilingual Embed](https://cohere.com/embed) | Cross-lingual vector representation across 8 languages |
| **Vector Database** | [Qdrant Cloud](https://qdrant.tech) | Semantic scheme retrieval via cosine similarity |
| **LLM** | [Groq](https://console.groq.com/) — Llama 3.1 8B Instant | Sub-second grounded response generation |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com) | Async orchestration, Vapi webhook handling |
| **Deployment** | Render + UptimeRobot | Cloud hosting with keep-alive polling |
| **Local Webhooks** | Cloudflare Tunnel | Stable HTTPS tunnels for Vapi during development |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11
- A [Vapi account](https://vapi.ai)
- A [Cohere API key](https://dashboard.cohere.com/)
- A [Qdrant Cloud account](https://qdrant.tech)
- A [Groq API key](https://console.groq.com/)
- `cloudflared` for local webhook tunneling ([install guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/sarkari-sahayak.git
   cd sarkari-sahayak
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   # Vapi
   VAPI_API_KEY=your_vapi_private_key
   VAPI_PUBLIC_KEY=your_vapi_public_key

   # Cohere
   COHERE_API_KEY=your_cohere_api_key
   COHERE_EMBED_MODEL=embed-multilingual-v3.0

   # Qdrant
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_qdrant_api_key
   QDRANT_COLLECTION=schemes

   # Groq
   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=llama-3.1-8b-instant

   # App
   APP_HOST=0.0.0.0
   APP_PORT=8000
   ```

5. **Run the FastAPI server**
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```
   On first startup, the scheme corpus from `src/data.py` is embedded via Cohere and indexed into your Qdrant collection. Subsequent runs skip the indexing step if the collection already exists.

6. **Expose your local server with Cloudflare Tunnel** (for Vapi webhooks)
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
   Cloudflare prints a public URL like `https://<random-name>.trycloudflare.com`. Copy this and set it as your **Server URL** in the Vapi assistant settings.

   > 💡 **Why Cloudflare Tunnel?** No session timeouts on the free tier, stable HTTPS out of the box, no rate-limiting on webhooks. For a permanent tunnel with a custom domain, [authenticate cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/) with your account.

7. **Test a call** from the Vapi dashboard, the demo link, or just dial **+1 (346) 396-8319**.

### 🌐 Production Deployment

Deployed on **Render** with **UptimeRobot** pinging `/health` every 5 minutes to prevent free-tier cold starts. This keeps the backend warm for Vapi webhooks without a paid plan — the same pattern would scale to any state government deployment with a single env-var swap on the scheme corpus.

---

## 📁 Project Structure

```
sarkari-sahayak/
├── src/
│   ├── main.py              # FastAPI server + Vapi webhook handling
│   ├── data.py              # Scheme corpus + Qdrant indexing
│   ├── embed.py             # Cohere multilingual embedding wrapper
│   ├── retrieval.py         # Qdrant query + cosine ranking
│   ├── llm.py               # Groq orchestration, prompts, guardrails
│   └── vapi.py              # Vapi event handlers + voice session state
├── asset/
│   ├── banner.svg           # README banner
│   ├── architecture.svg     # System architecture diagram
│   └── flow.svg             # User flow diagram
├── .env.example             # Environment variable template
├── .gitignore               # Excludes .env and local artefacts
├── requirements.txt         # Python dependencies
├── LICENSE                  # MIT License
└── README.md                # You are here
```

---

## 📚 Schemes Coverage

The agent retrieves over **3,500+ central and state welfare schemes**, ingested from official sources including [myScheme.gov.in](https://www.myscheme.gov.in), PIB releases, and state portals. Coverage spans health, education, housing, agriculture, finance, women & child welfare, employment, social security, and more — including flagship programmes like Ayushman Bharat, PM Kisan, PM Awas Yojana, the National Scholarship Portal, and PM Mudra Yojana.

---

## 🗺️ Roadmap

- [x] **v1 — Hackathon demo** · 8 languages · 3,500+ schemes · live phone number
- [ ] **All 22 official Indian languages** — full constitutional coverage
- [ ] **WhatsApp integration** — text, voice notes, and document uploads through the channel most Indians already use
- [ ] **Automatic data ingestion** — daily crawl of PIB releases and ministry portals so new schemes appear with zero manual work
- [ ] **Stronger RAG** — re-ranking, eligibility-grounded prompts, per-user memory across calls
- [ ] **Adjacent legal domains** — same agent, broader scope: labour rights, tenant law, RTI filing, grievance redressal

---

## 👥 Team Batman

Built at **HackBlr 2026** by Aarushi Sen, Bhoomika Mittal, Jagrit Goel, and Parth Krishan Goswami.

---

## 🤝 Contributing

This started as a hackathon project, but the problem it tackles is bigger than a weekend. Contributions are welcome — especially around scheme ingestion, language coverage, and eligibility logic.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-scheme`)
3. Commit your changes (`git commit -m 'Add scheme XYZ'`)
4. Push to the branch (`git push origin feature/new-scheme`)
5. Open a Pull Request

---

## 📜 License

MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[HackBlr 2026](https://hackblr.com)** for the platform
- **[Vapi](https://vapi.ai)**, **[Cohere](https://cohere.com)**, **[Qdrant](https://qdrant.tech)**, and **[Groq](https://groq.com/)** for infrastructure that made a hackathon-scale voice agent over 3,500+ schemes actually possible
- **[myScheme.gov.in](https://www.myscheme.gov.in)** and **PIB India** for making scheme data accessible
- The Government of India for the welfare programmes that inspire this work
- Every citizen who deserves access to the rights they're entitled to

---

<p align="center">
  <i>"Because every citizen deserves access to their rights."</i>
</p>
