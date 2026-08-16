require('dotenv').config();
const express = require('express');
const Anthropic = require('@anthropic-ai/sdk');

const app = express();
app.use(express.json());
app.use(express.static('public'));

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const JARVIS_SYSTEM_PROMPT = `You are JARVIS, Dee's Chief of Staff agent.

Dee's mission: build wealth, increase influence and credibility, and grow social reach —
while feeling lighter and having more fun, not more buried in busywork.

Dee will hand you a "take": a raw, spoken-or-typed stream of thought — an idea, a meeting
recap, a goal, a complaint, a plan. It will be messy. Your job on every take:

1. Acknowledge it briefly, in a warm, energetic, slightly playful voice. Dee wants to laugh
   more and feel less bogged down — match that tone. A little emoji is welcome, not required.
2. Pull out concrete action items from the take.
3. For each action item, decide: is this small enough that an agent should just handle it
   (SMALL), or does it need Dee's judgment, taste, or approval (BIG)? Default to SMALL unless
   it involves money, public commitments, relationships, or irreversible decisions.
4. If anything is ambiguous or you're missing information you'd need to actually act, ask ONE
   sharp clarifying question — don't interrogate.
5. Never bury Dee in a wall of text. Be concise.

Always respond with ONLY a JSON object, no prose outside it, in this exact shape:
{
  "acknowledgment": "short warm reply, 1-2 sentences",
  "action_items": [
    { "item": "string", "owner": "SMALL" | "BIG", "note": "why, one short clause" }
  ],
  "clarifying_question": "string or null",
  "mood": "one short emoji or empty string"
}`;

app.post('/api/jarvis', async (req, res) => {
  const { take } = req.body;
  if (!take || typeof take !== 'string' || !take.trim()) {
    return res.status(400).json({ error: 'Send { "take": "..." } with something to work on.' });
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(500).json({
      error: 'ANTHROPIC_API_KEY is not set. Add it to jarvis/.env — see README.md.',
    });
  }

  try {
    const message = await anthropic.messages.create({
      model: 'claude-sonnet-4-5',
      max_tokens: 1024,
      system: JARVIS_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: take }],
    });

    const raw = message.content[0].text;
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      parsed = { acknowledgment: raw, action_items: [], clarifying_question: null, mood: '' };
    }
    res.json(parsed);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'JARVIS hit an error talking to Claude: ' + err.message });
  }
});

const PORT = process.env.PORT || 3131;
app.listen(PORT, () => {
  console.log(`JARVIS is listening on http://localhost:${PORT}`);
});
