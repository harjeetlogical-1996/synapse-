# Deploy Synapse to Render (free) — for testing

Goal: get a public URL like `https://synapse-xxxx.onrender.com` you can send to
your partner to test. Takes ~10 minutes. Free tier.

## What you need
- A GitHub account (free)
- A Render account (free) — sign up at https://render.com with GitHub
- Your two keys: `GEMINI_API_KEY` and `SERPER_API_KEY`

---

## Step 1 — Put the code on GitHub

From the `synapse` folder:

```bash
cd synapse
git init
git add .
git commit -m "Synapse Research Agent"
```

Then create a new **private** repo on github.com (call it `synapse`), and push:

```bash
git remote add origin https://github.com/<your-username>/synapse.git
git branch -M main
git push -u origin main
```

Note: `.env` is git-ignored, so your keys do NOT get uploaded. Good — we add them
safely in Render instead (Step 3).

---

## Step 2 — Create the service on Render

1. Go to https://dashboard.render.com → **New +** → **Web Service**
2. Connect your GitHub, pick the `synapse` repo
3. Render auto-detects `render.yaml`. If it asks manually, set:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `python server.py`
   - **Plan:** Free

---

## Step 3 — Add your keys (secrets)

In the service's **Environment** tab, add:

| Key | Value |
|-----|-------|
| `HOST` | `0.0.0.0` |
| `GEMINI_API_KEY` | your Gemini key |
| `SERPER_API_KEY` | your Serper key |

(`render.yaml` already sets `HOST`; still confirm the two keys are there.)

Click **Save** → Render redeploys.

---

## Step 4 — Open the URL

Render gives you a URL like `https://synapse-xxxx.onrender.com`.
Open it, run a company, and send the same link to your partner.

---

## Notes for the free tier
- The service **sleeps after ~15 min idle**. The first request after that takes
  ~30-50 seconds to wake up. Normal for free — just wait on the first load.
- Every research call uses your Gemini + Serper quota, so testing is cheap but
  not zero. Keep an eye on the Serper free tier (2,500 searches).
- To update the live site later: `git push` again — Render redeploys automatically.

---

## Quicker alternative (no deploy): ngrok
If you just want a fast one-off demo from your own laptop:
1. Install ngrok (https://ngrok.com), sign up (free)
2. Run the server locally: `python server.py`
3. In another terminal: `ngrok http 8000`
4. ngrok prints a public URL — send that to your partner.
Downside: your laptop must stay on with the server running.
