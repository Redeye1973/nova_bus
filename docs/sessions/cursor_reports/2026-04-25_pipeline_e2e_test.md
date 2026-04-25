

## 2026-04-25T10:58:17.181126


### [2026-04-25T10:58:17.171130+00:00] **PIPELINE_START** ÔÇö INIT

```
{
  "type": "ship_sprite",
  "faction": "helios",
  "hull_class": "scout",
  "hull_id": "02",
  "damage_state": "clean",
  "output_format": "png",
  "resolution": "64x64",
  "palette": "helios_chrome",
  "test_mode": true,
  "test_id": "c14a60a2-862d-415d-a865-fb43bfc63483"
}
```



## 2026-04-25T10:58:17.260853


### [2026-04-25T10:58:17.257930+00:00] **STAGE_1_PIPELINE_START** ÔÇö PASS

```
pipeline_id=29a99400-7ecb-48ad-aa48-1a012043972f
```



## 2026-04-25T10:58:17.297240


### [2026-04-25T10:58:17.295374+00:00] **STAGE_2_BUDGET_CHECK** ÔÇö PASS

```
{"ok":true,"pipeline_id":"29a99400-7ecb-48ad-aa48-1a012043972f","pipeline_type":"shmup_sprite","used_pct":0,"remaining":{"cost_usd":0.5,"api_calls":100},"budget":{"pipeline_type":"shmup_sprite","max_cost_usd":"0.5000","max_duration_seconds":"600","max_gpu_seconds":"30","max_api_calls":"100","notify_threshold_pct":"80"}}
```



## 2026-04-25T10:58:17.341130


### [2026-04-25T10:58:17.339286+00:00] **STAGE_2B_AUDIT** ÔÇö PASS

```
{"audit_id":"27addca9-892d-4e94-90d4-973f9f93eb2e","timestamp":"2026-04-25 10:58:17.331351"}
```



## 2026-04-25T10:58:17.352544


### [2026-04-25T10:58:17.351009+00:00] **STAGE_3_PROMPT_SELECT** ÔÇö PASS

```
{"count":2,"templates":[{"name":"build_v2_agent","versions":2,"latest_version":2,"approved":true,"tags":[],"runs":0,"success_rate":0.0},{"name":"jury_review","versions":1,"latest_version":1,"approved":true,"tags":[],"runs":0,"success_rate":0.0}]}
```



## 2026-04-25T10:58:17.463201


### [2026-04-25T10:58:17.460642+00:00] **STAGE_4_BLENDER_RENDER** ÔÇö SKIP

```
bridge unreachable from server (test limitation; not pipeline bug)
{
  "bridge_reachable": false,
  "error": "[Errno -2] Name or service not known"
}
```



## 2026-04-25T10:58:17.526963


### [2026-04-25T10:58:17.524731+00:00] **STAGE_5_ASEPRITE_POLISH** ÔÇö SKIP

```
{
  "bridge_reachable": false,
  "error": "[Errno -2] Name or service not known"
}
```



## 2026-04-25T10:58:17.538507


### [2026-04-25T10:58:17.536452+00:00] **STAGE_6_SPRITE_JURY** ÔÇö PASS

```
{
  "verdict": "accept",
  "reasoning": "all jury scores > 7"
}
```



## 2026-04-25T10:58:17.546567


### [2026-04-25T10:58:17.545322+00:00] **STAGE_6B_QUALITY_GATE** ÔÇö PASS

```
{"verdict":"pass","reason":"bypass","stage_type":"sprite_generation","profile":"experiment"}
```



## 2026-04-25T10:58:17.556194


### [2026-04-25T10:58:17.554899+00:00] **STAGE_7_ASSET_LINEAGE** ÔÇö PASS

```
{
  "asset_id": "daf8a2f4-bf5a-4ecb-a9ea-7b7e8a1f9002",
  "registered": true
}
```



## 2026-04-25T10:58:17.568662


### [2026-04-25T10:58:17.566201+00:00] **STAGE_7B_NOTIFY** ÔÇö PASS

```
{"sent":true,"channels":{}}
```



## 2026-04-25T10:58:17.600778


### [2026-04-25T10:58:17.598722+00:00] **STAGE_8_PIPELINE_FINISH** ÔÇö PASS

```
{"pipeline_id":"29a99400-7ecb-48ad-aa48-1a012043972f","status":"success","duration_s":0.41}
```



## 2026-04-25T10:58:17.604405


### [2026-04-25T10:58:17.602637+00:00] **PIPELINE_END** ÔÇö COMPLETE

```
pipeline_run_id=29a99400-7ecb-48ad-aa48-1a012043972f test_id=c14a60a2-862d-415d-a865-fb43bfc63483
```

