# JARVIS (v0)

The first working slice of JARVIS: you talk or type a "take," JARVIS pulls out
action items, decides what it can just handle vs. what needs you, and asks a
clarifying question when it's missing something.

This is the intake layer everything else plugs into later — the specialist
agents (content, meetings, outreach, etc.) will route through this same
JARVIS front door.

## Run it (no coding needed — just these steps)

1. **Install Node.js** if you don't have it: https://nodejs.org (pick the LTS version, click through the installer).

2. **Get a Claude API key**: go to https://console.anthropic.com, sign in, click
   "API Keys," create a new key, copy it.

3. **Open a terminal in this folder** (`jarvis/`) and run:
   ```
   npm install
   ```

4. **Add your API key**: copy `.env.example` to a new file named `.env` in this
   same folder, and paste your key in:
   ```
   ANTHROPIC_API_KEY=sk-ant-...your key...
   ```

5. **Start JARVIS**:
   ```
   npm start
   ```

6. Open your browser to **http://localhost:3131**

7. Type a take, or click 🎤 and talk (works in Chrome/Edge). Click **Send to
   JARVIS**.

## What it does right now

- Takes your raw, messy input (voice or text)
- Replies with a short acknowledgment in JARVIS's voice
- Extracts action items, each tagged:
  - **SMALL** — JARVIS/an agent should just handle it
  - **BIG** — needs your judgment, taste, or approval
- Asks you one clarifying question if it's missing something it needs

## What's next

This is intentionally the smallest useful version. Next layers, in order:
1. Persistent memory across takes (so JARVIS remembers context between sessions)
2. The meeting-sweep agent (auto-pull action items from recordings on a schedule)
3. Specialist agents fanning out from JARVIS (content, outreach, ops) — same
   front door, more hands behind it
