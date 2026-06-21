# 🎨 Visionary AI

A multimodal AI agent that generates **text answers**, **images**, and **videos** from natural language prompts.  
The architecture is split into two parts: a lightweight **local proxy server** (FastAPI) and a **GPU model server** running on Google Colab.

---

## ✨ What's Different from the Original

| Feature | Original | Visionary AI |
|---|---|---|
| Theme | Purple/dark | Teal/dark with gradient accents |
| Style selector | ❌ | ✅ Cinematic, Anime, Photorealistic, Watercolor, Pixel Art |
| Video frame control | Fixed 8 | ✅ Slider (4–16 frames) |
| Rate limiting | ❌ | ✅ Per-IP, configurable |
| Request logging | ❌ | ✅ Server-side with timestamps |
| Feedback buttons | ❌ | ✅ 👍 / 👎 per result |
| Image lightbox | ❌ | ✅ Click to expand |
| Model health detail | Basic | ✅ Per-model status returned |
| `.env` config | 1 variable | ✅ 3 configurable variables |
| Error handling | Basic | ✅ Rate-limit 429, generic 500 handler |
| History trimming | Client-side | ✅ Server-side with `MAX_HISTORY` |

---

## 📁 Project Structure

```
visionary-ai/
├── backend/
│   └── main.py              # FastAPI proxy server
├── frontend/
│   └── index.html           # UI (served by backend)
├── visionary_agent.ipynb    # Colab GPU model server
├── requirements.txt
├── .env.example             # Copy to .env
├── .gitignore
└── README.md
```

---

## 🚀 Deployment Guide

### Step 1 — Run the Colab Notebook (GPU Model Server)

1. Open [Google Colab](https://colab.research.google.com/) and upload `visionary_agent.ipynb`.
2. Set runtime to **GPU**: Runtime → Change runtime type → **T4 GPU**.
3. Get a free [Hugging Face token](https://huggingface.co/settings/tokens) and replace `YOUR_HF_TOKEN_HERE` in Cell 2.
4. Get a free [ngrok auth token](https://dashboard.ngrok.com/get-started/your-authtoken) and replace `YOUR_NGROK_AUTH_TOKEN_HERE` in Cell 6.
5. Run all cells top-to-bottom (**Runtime → Run all**).
6. Wait for all three models to load (~5–10 min on first run).
7. After Cell 6 runs, you will see output like:
   ```
   ===========================================================
     🚀 Visionary AI Model Server is LIVE
     Public URL : https://abc123.ngrok-free.app
   ===========================================================
   COLAB_API_URL=https://abc123.ngrok-free.app
   ```
8. **Copy** the `COLAB_API_URL=...` line — you need it in Step 2.

> ⚠️ Keep the Colab tab open. If it disconnects, re-run from Cell 6.

---

### Step 2 — Set Up the Local Backend

#### 2a. Clone / copy the project

```bash
git clone https://github.com/YOUR_USERNAME/visionary-ai.git
cd visionary-ai
```

#### 2b. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

#### 2c. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2d. Configure environment

```bash
cp .env.example .env
```

Open `.env` and paste the ngrok URL from Step 1:

```env
COLAB_API_URL=https://abc123.ngrok-free.app
MAX_HISTORY=10
RATE_LIMIT_PER_MINUTE=20
```

#### 2e. Start the server

```bash
uvicorn backend.main:app --reload --port 8000
```

Open your browser at **http://localhost:8000** — you should see the Visionary AI UI.

---

### Step 3 — Verify Everything Works

1. The status pill in the top-right should show **🟢 Models Online**.
2. Try a Q&A prompt: `What is a neural network?`
3. Try an image prompt: `Generate an image of a sunset over the ocean`
4. Try a video prompt: `Create a video of falling autumn leaves`

---

## 🌐 Deploy the Backend Live (Optional)

### Option A — Railway (free tier, easiest)

1. Push to GitHub.
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub.
3. Add environment variable `COLAB_API_URL` in the Railway dashboard.
4. Railway auto-detects FastAPI and deploys. You get a public `.up.railway.app` URL.

### Option B — Render (free tier)

1. Push to GitHub.
2. Go to [render.com](https://render.com) → New Web Service → connect your repo.
3. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add `COLAB_API_URL` in Environment Variables.

### Option C — Fly.io

```bash
fly launch
fly secrets set COLAB_API_URL=https://abc123.ngrok-free.app
fly deploy
```

### Option D — Docker (self-host)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t visionary-ai .
docker run -p 8000:8000 --env-file .env visionary-ai
```

---

## 🔧 Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `COLAB_API_URL` | _(required)_ | ngrok URL from Colab notebook |
| `MAX_HISTORY` | `10` | Max conversation messages in memory |
| `RATE_LIMIT_PER_MINUTE` | `20` | Max requests per IP per minute |

---

## 🎨 Style Hints

Select a style before sending to enhance image/video prompts:

| Style | Effect |
|---|---|
| Cinematic | Film lighting, shallow depth of field, 35mm look |
| Anime | Vibrant colors, Studio Ghibli inspired |
| Photorealistic | 8K, DSLR quality, natural lighting |
| Watercolor | Soft edges, pastel tones, artistic feel |
| Pixel Art | 16-bit retro game aesthetic |

---

## ⚠️ Limitations

- **Colab disconnect**: The free Colab GPU disconnects after ~12 hours of inactivity. Re-run Cell 6 to reconnect.
- **ngrok URL changes**: Every time the Colab restarts, you get a new ngrok URL. Update `.env` accordingly.
- **Image/video generation**: Takes 1–3 minutes on a T4 GPU — this is normal.
- **Rate limit**: Default 20 req/min per IP. Adjustable via `.env`.

---

## 📄 License

MIT — feel free to use and modify.
