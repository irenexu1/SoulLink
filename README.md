# SoulLink

SoulLink is a desktop overlay that gives your computer a “soul” — a living, evolving personality that reacts to how you spend your time.  
Work too much and it becomes burnt-out. Play games all night and it grows feral. Maintain balance, and it thrives.

Under the hood, SoulLink tracks real activity (apps, idle time, focus sessions, gaming time, etc.), generates an internal behavioral profile, and uses AI-generated visuals & animations to express the current emotional state of your computer.

---

## 🌱 Core Concept

| Input | Output |
|-------|--------|
| You work for 6 hours straight | Soul becomes stressed, posture slumps, background dulls |
| You binge games until 3AM | Soul turns chaotic / gremlin mode |
| You take breaks, sleep well, mix work + play | Soul becomes well-rounded and calm |
| You abandon the PC for 2 days | Soul becomes lonely, starts “wilting” |

The goal isn't to track productivity — it’s to create a **living reflection of digital habits**, where your computer becomes a character you care for.

---

## 🔮 Features

✅ Electron desktop overlay (Windows / macOS / Linux)  
✅ Tracks live activity: active window, app category, idle time, sleep cycles, gaming vs working balance  
✅ Soul personality system (mood → emotion → visual state)  
✅ Nanobanana-powered image + animation generation (soul expressions, idle animations, transitions)  
✅ Status bars: energy, chaos, focus, rest, social, balance  
✅ “Life drift” system — the soul moves toward extremes unless kept in check  
✅ Local + cloud profile sync (Postgres, Kafka event ingestion)  
✅ Real-time metrics exposed via Prometheus  
✅ Backend designed for scale (Kafka, Redis, async workers, batching, backpressure)

---

## 🏗️ High-Level Architecture

```
+-------------------+        +-------------------+
|  Electron Overlay | <----> |  Local Activity   |
|  (frontend UI)    |   IPC  |  Sampler (Node)   |
+-------------------+        +-------------------+
           |                           |
           | REST/WebSocket            |
           v                           |
+-------------------+        +-------------------+
|  Ingest Service   | -----> | Redis Burst Buffer|
|  (FastAPI)        |        +-------------------+
           |   batched drain
           v
+-------------------+        +-------------------+
| Kafka (Redpanda)  | -----> |  Worker Service   |
+-------------------+        | (Python, async)   |
                             |  → soul model     |
                             |  → Postgres store |
                             +-------------------+
```

---

## 🧠 Soul Model (behavior → personality → visual state)

```
Raw activity → Weighted signals → Personality curve → Animation + Expression
(app, duration)   (work %, play %, idle %, circadian)  (workaholic, gremlin, ghost, balanced)
```

Each behavior axis has a **decay curve** and **influence weight**:

| Axis | Source | Effect on Soul |
|------|--------|----------------|
| Work Load | VSCode, IDEs, terminals | burnout, stress, productivity glow |
| Play Load | Steam, games, Discord | chaos, fun, hyperstate |
| Rest / Sleep | idle > 45m, overnight offline | healing, calm, soft colors |
| Social | voice chat, calls, messaging | connection, empathy, bright mood |
| Neglect | no input for days | ghost / wilted state |

---

## 🧰 Tech Stack

| Layer | Tech |
|-------|------|
| Desktop Overlay | Electron + React + WebGL/Lottie |
| Local Event Collector | Node.js, OS-level hooks (Win32 / macOS APIs) |
| Ingest API | FastAPI (Python), pydantic, rate-limited batching |
| Burst Buffer | Redis (RPUSH + trimming) |
| Stream Processing | Kafka (Redpanda) + aiokafka consumers |
| Storage | PostgreSQL (time-weighted behavior profiles) |
| AI Visuals | Nanobanana (image + animation prompt pipeline) |
| Metrics | Prometheus `/metrics` endpoints on all services |
| Deployment | Docker Compose (dev), Kubernetes (prod) |

---

## 📂 Repository Layout (planned)

```
soulink/
├── desktop/             # Electron app
│   ├── overlay-ui/      # React + WebGL soul renderer
│   └── system-hooks/    # Native OS event collectors
├── ingest/              # FastAPI event receiver + Redis buffer
├── worker/              # Kafka consumer → Postgres writer → soul engine
├── models/              # Behavior mapping + soul personality curves
├── db/
│   └── schema.sql
├── services/
│   └── nanobanana_client.py
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## 🚀 Quickstart (Local Dev)

```bash
cp .env.example .env
docker compose up -d --build
```

Send sample event:

```bash
curl -X POST "http://localhost:8000/v1/events?user_id=u_1" \
  -H "content-type: application/json" \
  -d '[{"ts": 1730066400123,"app":"code","window":"index.ts","idle":false,"focus_secs":300}]'
```

Query soul profile:

```bash
docker exec -it $(docker ps -qf name=postgres) \
  psql -U postgres -d soulink \
  -c "select * from soul_profiles limit 5;"
```

---

## 🛠 Development Modes

| Mode | Purpose |
|------|---------|
| `docker compose up` | full stack running (ingest, worker, db, redis, kafka) |
| `npm run dev` in `/desktop` | live Electron overlay |
| `pytest` in `/worker` | soul evolution logic tests |

---

## 📌 Roadmap

- [ ] Nanobanana animated sprite packs
- [ ] Local model fallback (no cloud dependency)
- [ ] Social soul interactions (your soul reacts to friends’ souls)
- [ ] Soul “seasons” / long-term memory
- [ ] Web dashboard + history heatmaps
- [ ] Public API for external apps to affect soul state

---
