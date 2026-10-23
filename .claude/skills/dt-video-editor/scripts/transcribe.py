"""Transcribe a video offline and find its pauses.

usage: python3 transcribe.py VIDEO WORKDIR

Writes into WORKDIR:
  audio16k.wav     mono 16 kHz audio
  words.json       [[word, start, end], ...] from Vosk
  pauses.json      [[start, end], ...] silent gaps >= 0.28 s (from a 10 ms RMS envelope)
  transcript.txt   raw ASR text, one line per speech run, with timestamps

Read transcript.txt, then write the cleaned script (punctuation, "a i" -> "AI",
product names) into plan.json "script". render.py aligns that script back onto
words.json, so captions get real word timing even after you fix the wording.
"""
import sys, os, json, wave, subprocess
import numpy as np

video, work = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)
CACHE = os.environ.get('DT_VIDEO_CACHE', os.path.expanduser('~/.cache/dt-video'))
sys.path.insert(0, CACHE + '/shim')
from vosk import Model, KaldiRecognizer, SetLogLevel

wav = os.path.join(work, 'audio16k.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-ac', '1', '-ar', '16000', wav], check=True)

SetLogLevel(-1)
model = Model(os.path.join(CACHE, 'vosk-model-small-en-us-0.15'))
w = wave.open(wav)
rec = KaldiRecognizer(model, 16000); rec.SetWords(True)
words = []
while True:
    d = w.readframes(4000)
    if not d: break
    if rec.AcceptWaveform(d): words += json.loads(rec.Result()).get('result', [])
words += json.loads(rec.FinalResult()).get('result', [])
words = [[x['word'], round(x['start'], 3), round(x['end'], 3)] for x in words]
json.dump(words, open(os.path.join(work, 'words.json'), 'w'))

# pauses from RMS envelope
w = wave.open(wav); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
n = 160; r = np.sqrt(np.mean(x[:len(x) // n * n].reshape(-1, n) ** 2, 1)); db = 20 * np.log10(r + 1e-9)
voiced = db > -35
segs, st = [], None
for i, v in enumerate(voiced):
    if v and st is None: st = i
    if not v and st is not None: segs.append([st / 100, i / 100]); st = None
if st is not None: segs.append([st / 100, len(voiced) / 100])
merged = []
for a, b in segs:
    if merged and a - merged[-1][1] < 0.28: merged[-1][1] = b
    else: merged.append([a, b])
merged = [s for s in merged if s[1] - s[0] > 0.08]
pauses = [[round(merged[i][1], 2), round(merged[i + 1][0], 2)] for i in range(len(merged) - 1)]
json.dump(pauses, open(os.path.join(work, 'pauses.json'), 'w'))

# human-readable transcript split on pauses
lines, cur, cur_st = [], [], None
for wd, s, e in words:
    # split where a pause midpoint falls between the previous word's middle and this word's middle
    if cur and any(prev_mid < (p[0] + p[1]) / 2 < (s + e) / 2 for p in pauses):
        lines.append(f'{cur_st:6.2f}-{prev_e:6.2f}  ' + ' '.join(cur)); cur = []
    if not cur: cur_st = s
    cur.append(wd); prev_e = e; prev_mid = (s + e) / 2
if cur: lines.append(f'{cur_st:6.2f}-{prev_e:6.2f}  ' + ' '.join(cur))
open(os.path.join(work, 'transcript.txt'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
print(f'\n{len(words)} words, {len(pauses)} pauses. Speech ends at {words[-1][2] if words else 0:.2f}s')
