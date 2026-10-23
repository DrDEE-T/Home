# plan.json reference

`render.py` reads this file. `words.json` and `pauses.json` must sit in the same folder (or set `"workdir"`).

## Time values

Anywhere a time is accepted you can give:
- a number: seconds. Inside a card row, it's seconds after the card enters.
- a string: a phrase from `script`. It resolves to the moment the first word starts (case and punctuation ignored, fuzzy fallback). Inside a card row the phrase still means that spoken moment; it's converted to card time for you.

Prefer phrases. They survive re-cuts and you never have to read timestamps.

## Top level

| field | required | notes |
|---|---|---|
| `source` | yes | path to the video |
| `script` | recommended | cleaned transcript. Captions use these exact words, aligned to ASR timing. Without it, raw ASR words are captioned. |
| `output` | no | default `WORK/final.mp4` |
| `captions` | no | default `true` |
| `subject_x` | no | speaker's x position in source pixels if not centered |
| `shots` | no | omit for automatic shots. Or a list of `{"at", "zoom", "x", "top"}` (zoom 1.0 to 1.4, x = crop center in px, top = 0 to 0.15). |
| `min_shot` | no | minimum seconds between automatic cuts (default 2.4) |
| `hook` | no | see below |
| `beats` | no | list, see below |
| `takeover` | no | see below |
| `end_card` | no | `{"name", "line1", "line2", "disclosure", "length"}`. `null` turns it off. |

## hook

```json
{"setup": "AI is helping attackers find", "key": ["your website's", "weak spots"],
 "tiles": ["Website", "Login", "Forms", "Plugins", "Cookies", "Admin", "Keys"],
 "until": "And the pressure", "y": 486}
```
`key` lines render big and yellow. Keep each under about 16 characters. `until` defaults to the first beat.

Tile icons are drawn for: website, login/lock/security, forms/docs/drive/notes, plugins/apps/orders, cookies, admin/people/team/social/clients, keys, inbox/email/mail, calendar/schedule, chart/reports/analytics/data. Any other name gets a browser-window icon.

## beats

```json
{"at": "Use Claude Code", "until": "optional phrase", "headline": "Claude Code or Codex",
 "chip": "01", "highlight": "pro review", "card": { ... }}
```
- A beat ends at the pause before the next beat (or the takeover) unless you give `until`.
- `highlight` is the words from the headline that get the yellow marker. You can also give a list of word indexes.
- Headlines shrink to fit 560 px. Keep them to 2 to 5 words anyway.

### card

```json
{"title": "Vulnerability check", "subtitle": "optional gray line",
 "rows": [ ... ], "pill": {"text": "Found before attackers", "color": "ink", "at": 4.6},
 "example_data": true}
```
Colors: `yellow`, `rose`, `ink`, `gray`, `green`, `red`, or `[r,g,b]`.

Card height budget is about 265 px (QA fails anything taller, since it runs into the captions). The title uses 54 px, a subtitle 22, and a pill 40. Rows: counter 76, bars 82, typing 48, toggle 42, chips 40, check 38, field 38, file 36, type_text 28, text about 22 per line, pending 38+ (it wraps). Example: title + counter + pill fits; title + subtitle + counter + bars + pill does not.

| row `type` | fields | what it does |
|---|---|---|
| `counter` | `from`, `to`, `prefix`, `suffix`, `dur`, `color`, `at` | big number ticks up with a progress bar |
| `check` | `text`, `color`, `at` | row fades in, then a checkmark draws |
| `pending` | `text`, `color`, `at` | row with an empty ring ("still needed") |
| `toggle` | `text`, `at` | switch flips on at `at` |
| `typing` | `prefix`, `text`, `dur`, `at` | input field types text with a cursor |
| `type_text` | `text`, `dur`, `at` | plain line types out (message body) |
| `chips` | `items`, `ats` (one time each), `color` | dark pills pop in one by one, good for named tools |
| `file` | `text`, `at` | code file row, "Reading…" then a check |
| `field` | `label`, `value` | "To: [Web manager]" style row |
| `bars` | `values`, `color`, `at` | small bar chart grows |
| `text` | `text`, `bold`, `size`, `at` | static wrapped text |

## takeover

```json
{"at": "and this prompt", "until": "If you have the code", "style": "bust",
 "label": "SCREENSHOT THIS", "kicker": "02 / THE PROMPT", "title": "Paste into Claude Code or Codex",
 "highlight": "[yourdomain.com]",
 "body": [{"p": "paragraph"}, {"n": "1.", "text": "numbered item"}],
 "footer": "small gray line", "hint": "Pause and grab it", "body_size": 22}
```
- The start snaps to the pause before `at`, and the end snaps to the pause before `until`, so it never cuts a word. Set `"snap": false` to use `at` + `lead` instead.
- `style`: `bust` (screen shatters, card punches in, shake and impact sound) or `slide` (card rises from the bottom).
- Body text shrinks automatically, down to 15 px, to stay inside the safe zone. If it needs to go below 18 px, trim the prompt text or drop the title.
- Without `until`, give `duration` in seconds (default 9).
