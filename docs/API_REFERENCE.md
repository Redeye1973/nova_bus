# NOVA v2 — API Reference

> 36 agents, auto-generated

## NOVA v2 Code Jury (`agent_02_code_jury`)
Version: 0.1.0

> NOVA v2 Agent 02 — Code Jury (Python + GDScript POC).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review/python` | `review_python` |
| POST | `/review/gdscript` | `review_gdscript` |
| POST | `/review/batch` | `review_batch` |
| POST | `/review` | `review_unified` |

**Models:** `CodePayload`, `BatchItem`, `BatchPayload`, `UnifiedReview`

## NOVA v2 Audio Jury (`agent_03_audio_jury`)
Version: 1.0.0

> NOVA v2 Agent 03 — Audio Jury (WAV DSP + uniform /review).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review` | `review` |
| POST | `/review/audio` | `review_audio` |
| POST | `/review/batch` | `review_batch` |
| POST | `/invoke` | `invoke` |

**Models:** `JuryRequest`, `JuryVerdict`, `AudioReviewItem`, `BatchPayload`

## NOVA v2 3D Model Jury (`agent_04_3d_model_jury`)
Version: 1.0.0

> NOVA v2 Agent 04 — 3D Model Jury (metadata + uniform /review).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review` | `review` |
| POST | `/invoke` | `invoke` |

**Models:** `JuryRequest`, `JuryVerdict`

## NOVA v2 GIS Jury (`agent_05_gis_jury`)
Version: 1.0.0

> NOVA v2 Agent 05 — GIS Jury (GeoJSON-style artifact + uniform /review).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review` | `review` |
| POST | `/invoke` | `invoke` |

**Models:** `JuryRequest`, `JuryVerdict`

## NOVA v2 CAD Jury (`agent_06_cad_jury`)
Version: 1.0.0

> NOVA v2 Agent 06 — CAD Jury (parametric metadata + uniform /review).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review` | `review` |
| POST | `/invoke` | `invoke` |

**Models:** `JuryRequest`, `JuryVerdict`

## NOVA v2 Narrative Jury (`agent_07_narrative_jury`)
Version: 1.0.0

> NOVA v2 Agent 07 — Narrative Jury (text heuristics + uniform /review).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review` | `review` |
| POST | `/invoke` | `invoke` |

**Models:** `JuryRequest`, `JuryVerdict`

## NOVA v2 Character Art Jury (`agent_08_character_art_jury`)
Version: 1.0.0

> NOVA v2 Agent 08 — Character Art Jury (image heuristics + uniform /review).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review` | `review` |
| POST | `/invoke` | `invoke` |

**Models:** `JuryRequest`, `JuryVerdict`

## NOVA v2 2D Illustration Jury (`agent_09_illustration_jury`)
Version: 1.0.0

> NOVA v2 Agent 09 — 2D Illustration Jury (image heuristics + uniform /review).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review` | `review` |
| POST | `/invoke` | `invoke` |

**Models:** `JuryRequest`, `JuryVerdict`

## NOVA v2 Agent 10 Game Balance Jury (`agent_10_game_balance_jury`)
Version: 0.1.0

> Agent 10 — Game Balance Jury.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/review/stats` | `review_stats_ep` |
| POST | `/review/economy` | `review_economy_ep` |
| POST | `/review/difficulty_curve` | `review_diff_ep` |
| POST | `/review` | `review_all` |

## NOVA v2 Agent 11 - Monitor (`agent_11_monitor`)
Version: 0.2.0

> NOVA v2 Agent 11 — Monitor (health/status/metrics/alerts).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/status` | `status` |
| GET | `/alerts` | `alerts` |
| POST | `/feedback` | `post_feedback` |
| GET | `/feedback/recent` | `feedback_recent` |
| GET | `/pdok-weekly-delta` | `pdok_weekly_delta_stub` |
| POST | `/pipeline/start` | `pipeline_start` |
| POST | `/pipeline/stage` | `pipeline_stage` |
| POST | `/pipeline/finish` | `pipeline_finish` |
| GET | `/pipeline/active` | `pipeline_active` |
| GET | `/pipeline/{pipeline_id}` | `pipeline_detail` |
| GET | `/pipeline/history` | `pipeline_history_list` |
| GET | `/metrics` | `metrics` |
| POST | `/invoke` | `invoke` |

**Models:** `InvokeBody`, `FeedbackBody`, `PipelineStart`, `PipelineStage`, `PipelineFinish`

## NOVA v2 Agent 12 - Bake Orchestrator (`agent_12_bake_orchestrator`)
Version: 0.2.0

> NOVA v2 Agent 12 — Bake Orchestrator + H09 Asset Lineage.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/bake/jobs` | `create_job` |
| GET | `/bake/jobs/{job_id}` | `get_job` |
| POST | `/bake/jobs/{job_id}/advance` | `advance_job` |
| POST | `/assets/register` | `register_asset` |
| GET | `/assets/{asset_id}` | `get_asset` |
| GET | `/assets/{asset_id}/lineage` | `asset_lineage` |
| GET | `/assets` | `list_assets` |
| POST | `/invoke` | `invoke` |

**Models:** `CreateJob`, `AssetRegister`

## NOVA v2 Agent 13 - PDOK Downloader (`agent_13_pdok_downloader`)
Version: 0.1.0

> NOVA v2 Agent 13 — PDOK Downloader (cache keys + stub fetch; real PDOK client later).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/download` | `download` |
| POST | `/invoke` | `invoke` |

**Models:** `DownloadBody`

## NOVA v2 Agent 14 - Blender Baker (`agent_14_blender_baker`)
Version: 0.1.0-stub

> NOVA v2 Agent 14 — Blender Baker (stub; bridge headless later).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/bake` | `bake` |
| POST | `/invoke` | `invoke` |

**Models:** `BakeBody`

## NOVA v2 Agent 15 - QGIS Processor (`agent_15_qgis_processor`)
Version: 0.1.0-pending

> NOVA v2 Agent 15 — QGIS Processor (pending full bridge).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/process` | `process` |
| POST | `/invoke` | `invoke` |

**Models:** `ProcessBody`

## NOVA v2 Agent 16 - Cost Guard (`agent_16_cost_guard`)
Version: 0.1.0

> NOVA v2 Agent 16 — Cost Guard (in-memory daily cap; Postgres DDL in scripts/).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/budget` | `budget` |
| POST | `/cost/record` | `cost_record` |
| POST | `/cost/check` | `cost_check` |
| GET | `/cost/log` | `cost_log` |
| GET | `/cost/daily/{date}` | `cost_daily` |
| GET | `/cost/summary` | `cost_summary` |
| GET | `/cost/by_agent` | `cost_by_agent` |
| POST | `/invoke` | `invoke` |

**Models:** `CostRecord`, `CostCheck`

## NOVA v2 Agent 17 - Error Handler (`agent_17_error_handler`)
Version: 0.1.0

> NOVA v2 Agent 17 — Error Handler + H11 Auto-Learning.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/error/report` | `error_report` |
| POST | `/error/resolve` | `error_resolve` |
| GET | `/repair/history` | `repair_history` |
| GET | `/errors/trends` | `error_trends` |
| GET | `/errors/learned` | `learned_patterns_list` |
| GET | `/errors/escalations` | `escalation_history` |
| POST | `/invoke` | `invoke` |

**Models:** `ErrorReport`, `ErrorResolve`, `InvokeBody`

## NOVA v2 Agent 18 - Prompt Director (`agent_18_prompt_director`)
Version: 0.2.0

> NOVA v2 Agent 18 — Prompt Director (versioned templates + prompt registry).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/templates/{name}` | `get_template` |
| POST | `/templates` | `upsert_template` |
| GET | `/templates` | `list_templates` |
| GET | `/prompts/search` | `search_prompts` |
| POST | `/prompts/feedback` | `prompt_feedback` |
| GET | `/prompts/leaderboard` | `prompt_leaderboard` |
| GET | `/prompts/recent` | `prompt_recent` |
| POST | `/invoke` | `invoke` |

**Models:** `TemplateUpsert`, `PromptFeedback`

## NOVA v2 Agent 19 - Distribution (`agent_19_distribution`)
Version: 0.1.0

> NOVA v2 Agent 19 — Distribution (MinIO-oriented stub).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/publish` | `publish` |
| POST | `/invoke` | `invoke` |

**Models:** `PublishBody`

## NOVA v2 Agent 20 - Design Fase (`agent_20_design_fase`)
Version: 0.1.0

> NOVA v2 Agent 20 — Design Fase (palette, silhouette, consistency POC).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/palette/create` | `create_palette` |
| POST | `/palette/validate` | `validate_palette` |
| POST | `/silhouette/check` | `check_silhouette` |
| POST | `/consistency/check` | `check_consistency` |

**Models:** `PaletteRequest`, `PaletteValidationRequest`, `SilhouetteRequest`, `ConsistencyRequest`

## NOVA v2 Agent 21 - FreeCAD Parametric (`agent_21_freecad_parametric`)
Version: 0.2.0

> NOVA v2 Agent 21 — FreeCAD Parametric.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/model/build-base` | `build_base` |
| POST | `/variants/generate` | `variants_generate` |
| POST | `/components/assemble` | `components_assemble` |
| POST | `/invoke` | `invoke` |

**Models:** `BuildBaseRequest`, `VariantGenRequest`, `ComponentRef`, `AssembleRequest`, `InvokeBody`

## NOVA v2 Agent 22 - Blender Game Renderer (`agent_22_blender_renderer`)
Version: 0.2.0

> NOVA v2 Agent 22 — Blender Game Renderer.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/availability` | `availability` |
| POST | `/render` | `render` |
| POST | `/script` | `script` |
| POST | `/invoke` | `invoke` |

**Models:** `RenderRequest`, `ScriptRequest`

## NOVA v2 Agent 23 - Aseprite Processor (`agent_23_aseprite_processor`)
Version: 0.2.0

> NOVA v2 Agent 23 — Aseprite Processor.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/availability` | `availability` |
| POST | `/process` | `process` |
| POST | `/invoke` | `invoke` |

**Models:** `SpritesheetRequest`, `ProcessRequest`

## NOVA v2 Agent 24 - Aseprite Animation Jury (`agent_24_aseprite_anim_jury`)
Version: 0.1.0

> NOVA v2 Agent 24 — Aseprite Animation Jury (PIL frame coherence; optional Ollama verdict).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/animate/review` | `animate_review` |
| POST | `/invoke` | `invoke` |

**Models:** `AnimateReviewBody`

## NOVA v2 Agent 25 - PyQt Assembly (`agent_25_pyqt_assembly`)
Version: 0.2.0

> NOVA v2 Agent 25 — PyQt Assembly.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/availability` | `availability` |
| POST | `/assemble` | `assemble` |
| POST | `/invoke` | `invoke` |

**Models:** `AssembleRequest`

## NOVA v2 Agent 26 - Godot Import (`agent_26_godot_import`)
Version: 0.2.0

> NOVA v2 Agent 26 — Godot Import.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/availability` | `availability` |
| POST | `/validate` | `validate` |
| POST | `/import` | `import_assets` |
| POST | `/script` | `run_script` |
| POST | `/invoke` | `invoke` |

**Models:** `ValidateRequest`, `ImportRequest`, `ScriptRequest`

## NOVA v2 Agent 27 - Storyboard Visual (`agent_27_storyboard`)
Version: 0.1.0

> NOVA v2 Agent 27 — Storyboard Visual Agent (Cost Guard precheck; FLUX optional).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/storyboard/generate` | `storyboard_generate` |
| POST | `/invoke` | `invoke` |

**Models:** `StoryboardBody`

## NOVA v2 Agent 28 - Story Text Integration (`agent_28_story_integration`)
Version: 0.1.0

> NOVA v2 Agent 28 — Story Text Integration (in-memory canon + YAML profiles + docx ingest).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/canon/search` | `canon_search` |
| GET | `/character/{name}` | `character_get` |
| POST | `/ingest` | `ingest_text` |
| POST | `/ingest_docx` | `ingest_docx` |

**Models:** `CanonSearchBody`, `IngestTextBody`

## NOVA v2 Agent 29 - ElevenLabs Audio (`agent_29_elevenlabs`)
Version: 0.1.0

> NOVA v2 Agent 29 — ElevenLabs Audio (Cost Guard precheck; dry-run without API key).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/voices` | `voices_list` |
| POST | `/voices/register` | `voices_register` |
| POST | `/tts` | `tts_synthesize` |
| POST | `/invoke` | `invoke` |

**Models:** `VoiceRegister`, `TtsBody`

## NOVA v2 Agent 30 - Audio Asset Jury (`agent_30_audio_asset_jury`)
Version: 0.1.0

> NOVA v2 Agent 30 — Audio Asset Jury (librosa technical QA; optional Audio Jury ref).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/audio/analyze` | `audio_analyze` |
| POST | `/invoke` | `invoke` |

## NOVA v2 Agent 31 - QGIS Analysis (`agent_31_qgis_analysis`)
Version: 0.2.0

> NOVA v2 Agent 31 — QGIS Analysis.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/availability` | `availability` |
| POST | `/analyze` | `analyze` |
| POST | `/invoke` | `invoke` |

**Models:** `AnalyzeRequest`

## NOVA v2 Agent 32 - GRASS GIS (`agent_32_grass_gis`)
Version: 0.2.0

> NOVA v2 Agent 32 — GRASS GIS.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/availability` | `availability` |
| POST | `/analyze` | `analyze` |
| POST | `/invoke` | `invoke` |

**Models:** `GrassRequest`

## NOVA v2 Agent 33 - Blender Arch Walkthrough (`agent_33_blender_arch_walkthrough`)
Version: 0.2.0

> NOVA v2 Agent 33 — Blender Architecture Walkthrough.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/availability` | `availability` |
| POST | `/walkthrough` | `walkthrough` |
| POST | `/invoke` | `invoke` |

**Models:** `WalkthroughRequest`

## NOVA v2 Agent 34 - Unreal Import Prep (`agent_34_unreal_import`)
Version: 0.1.0

> NOVA v2 Agent 34 — Unreal import prep (FBX/USD validation, path rewrite mapping; no UE runtime).

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/unreal/prep` | `unreal_prep` |
| POST | `/invoke` | `invoke` |

**Models:** `PrepBody`

## NOVA v2 Agent 35 - Raster 2D Processor (`agent_35_raster_2d`)
Version: 0.2.0

> NOVA v2 Agent 35 — Raster 2D Processor.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| GET | `/availability` | `availability` |
| POST | `/process` | `process` |
| POST | `/invoke` | `invoke` |

**Models:** `ProcessRequest`

## NOVA v2 Agent 44 - Secrets Vault (`agent_44_secrets_vault`)
Version: 0.1.0

> NOVA v2 Agent 44 — Secrets Vault.

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/secrets/get` | `secret_get` |
| POST | `/secrets/set` | `secret_set` |
| POST | `/secrets/delete` | `secret_delete` |
| GET | `/secrets/list` | `secret_list` |
| POST | `/secrets/bulk_set` | `secret_bulk_set` |
| GET | `/secrets/audit` | `secret_audit` |
| POST | `/invoke` | `invoke` |

**Models:** `SecretGet`, `SecretSet`, `SecretBulk`, `InvokeBody`

## NOVA Judge (`judge`)
Version: 1.0.0

| Method | Path | Function |
|--------|------|----------|
| GET | `/health` | `health` |
| POST | `/evaluate` | `evaluate` |

**Models:** `EvaluateRequest`
