# Agent 03 — Audio Jury

WAV DSP jury (`librosa`-style metrics via numpy): technical + spectral members, uniform `POST /review`, optional pipeline judge via `NOVA_JUDGE_URL`. n8n workflow: webhook → `/review` → `nova-judge` `/evaluate` → respond.
