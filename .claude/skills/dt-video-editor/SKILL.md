---
name: dt-video-editor
description: Transcribe and fully edit Dr. Denise Turley's vertical talking-head and walk-and-talk videos (AI twin series, LinkedIn shorts, tips videos) into her approved premium style, end to end, with no hand-offs back to her. Covers offline speech-to-text, word-timed captions, virtual camera angles, a 3D orbiting hook carousel, frosted-glass motion cards timed to her words, a full-screen "Screenshot this" prompt card takeover, sound effects, the "Always assume I used AI" end card, and self-QA. Use this whenever she uploads or mentions an MP4 or MOV and asks to edit it, add motion graphics, captions, carousels or camera angles, move or add a prompt card, match the edit to the transcript, transcribe a video, or redo or fix a previous edit, even if she doesn't say "skill" or name the steps.
---

# Dr. Turley video editor

You do the whole job yourself: setup, transcription, script cleanup, edit plan, rendering, QA, fixes, delivery. She wants a finished video back, not homework. Don't ask her to confirm captions, check timing, or pick options you can decide. Send the finished file and a short note on what you did.

Ask her something only when you can't get it anywhere else. The usual case is a prompt card she wants on screen whose text she hasn't given you. Even then, build the rest of the edit while you wait.

## Pipeline

All scripts live in `scripts/` next to this file. Use a scratch work folder per video.

1. **Setup** (about 5 s, safe to re-run): `bash scripts/setup.sh`. This installs OpenCV and Vosk and downloads the small English Vosk model from npm, because the model's usual host is blocked in sandboxes.
2. **Get the video.** Uploads land under `/root/.claude/uploads/...`. Copy the file to `WORK/src.mp4`. If she says the upload is too big, tell her once to export at 720p (QuickTime: File > Export As > 720p; HandBrake: "Fast 720p30"). Output is 720x1280 anyway.
3. **Transcribe:** `python3 scripts/transcribe.py WORK/src.mp4 WORK`. This prints a transcript split on pauses and writes `words.json` and `pauses.json`.
4. **Clean the script.** Rewrite the ASR text into the real script with punctuation. Fix "a i" to "AI", split or joined words ("web sites"), and misheard product names. Use context to fix names: what she's demonstrating, the prompt card, and earlier videos. Vosk-small usually gets names like "Claude Code" and "Codex" right, and it is much better than guessing from audio energy. Keep her words. Don't paraphrase, because captions must match what she says.
5. **Write `WORK/plan.json`.** See `references/plan_schema.md` for every field, and copy `examples/cybersecurity_plan.json` as the starting point. Anchor every time to a phrase from the script ("at": "this prompt") instead of seconds, so timing follows her speech automatically.
6. **Check layout fast:** `python3 scripts/render.py WORK/plan.json --stills 0.5 <one time per beat> <mid-takeover> <end>`. Tile the stills (`ffmpeg ... -vf scale=216:-1,tile=5x2`) and look at them. Fix overlaps, text that is too long, or a card that's too tall before the full render.
7. **Render:** `python3 scripts/render.py WORK/plan.json`. This takes about 5 minutes for 50 s of video, so run it in the background if it's long. It writes `final.mp4`, `qa_sheet.jpg` and `qa_report.txt`.
8. **QA yourself.** Read `qa_report.txt`. Any `FAIL` line is yours to fix: adjust the plan and re-render. Look at `qa_sheet.jpg` for anything the checks can't see: a card covering her face, a cut that looks odd, text that's hard to read.
9. **Deliver.** Rename the file to something meaningful (`<Topic>_edit_v1.mp4`) and send it with SendUserFile. Then write a short summary in her voice preferences: no em dashes, no hype, plain and direct. Cover what's on screen and when. Mention any judgment call worth knowing about, such as a product name you inferred from context.

## Editing decisions (what good looks like)

**Hook (frame 0 is also the thumbnail).** Use a white setup line plus a big yellow key phrase taken from her first sentence. Add 6 to 7 orbiting tiles named for the topic's real objects (Website, Login, Forms... or Inbox, Calendar, Orders...). It runs until her second sentence.

**Beats.** Make one beat per concrete thing she names. Each beat gets a short headline (2 to 5 words) and a card with live UI that acts out what she says: counters for numbers, checks for findings, toggles for settings, typing for URLs or messages, chips for named tools, files for code, a pending circle for "still needed" items. Time rows to the exact words ("at": "web access") so the UI moves as she speaks. Use 3 to 4 yellow highlights per video, only on takeaway phrases. Use invented names and no real logos; cards say "Example data" automatically.

**Numbered chips (01/02/03)** go on her steps. When there's a takeover, it is usually step 02 and its kicker says so.

**Prompt card takeover.** When she says "this prompt", "use this template" or similar, the card bursts through the screen right then. Start it with `"at"` on that phrase. It holds through every sentence that is still about the prompt and ends on the first sentence that moves on (`"until"`). It needs at least 6 s on screen so people can screenshot it. Captions keep running underneath. Use the exact prompt text she gave you. Highlight the part viewers must replace (e.g. `[yourdomain.com]`). Use `"style": "slide"` instead of "bust" for calmer videos.

**Camera.** Shots are automatic. The script cuts only in pauses, never mid-word (QA checks this), and alternates wide, medium punch-in and reframes left or right with a slow push-in and a settle at each cut. Set `subject_x` if she isn't centered in the source.

**End card.** "Always assume / I used AI." with her name and the AI disclosure. Keep it on for AI-twin videos. Set `"end_card": null` only if she says the video isn't AI-generated.

**Sound.** Her audio is never altered. Whooshes, the bust-through impact and the shutter click are synthesized and mixed low.

## Re-edits

When she asks for a change ("move the card", "different angle here", "fix that caption"), edit `plan.json` and re-render. Don't rebuild from scratch. Keep `WORK` around for the session. If she uploads a new cut of the same video, re-run transcribe and keep the plan, because phrase anchors usually still resolve.

## Related

- `dt-ai-twin-video` covers writing Higgsfield prompts and generating her AI-twin clips. This skill edits the result. Hand off between them as needed.
- After delivery, offer the LinkedIn post (`dt-linkedin`) with an opening line that matches the on-screen hook.
