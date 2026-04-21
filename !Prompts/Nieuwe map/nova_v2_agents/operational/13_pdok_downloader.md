# 13. PDOK Downloader Agent

## Doel
Haalt geografische data van PDOK voor specifieke postcode-gebieden. Gestandaardiseerd en gecached.

## Datasets per bake

- BAG (Basisregistratie Adressen en Gebouwen)
- BGT (Basisregistratie Grootschalige Topografie)  
- AHN4 (Actueel Hoogtebestand Nederland)
- NWB (Nationaal Wegenbestand)
- 3D Basisvoorziening (wanneer beschikbaar voor gebied)
- PDOK Luchtfoto tiles (voor textures)

## Functionaliteit

**1. Bounding Box Calculator**
- Input: postcode → haal bbox uit PDOK
- Expand met margin voor rand-features

**2. Parallel Downloader**
- Download meerdere datasets concurrent
- Respect PDOK rate limits
- Resume bij onderbreking

**3. Cache Manager**
- Check lokale cache eerst
- Skip download als data < 30 dagen oud
- Force refresh optie

**4. Integrity Verifier**
- Checksum validation
- Parse test (opens succesvol)
- Feature count plausibility

## Cursor Prompt

```
Bouw een NOVA v2 PDOK Downloader:

1. Python service `pdok_downloader/downloader.py`:
   - FastAPI POST /download
   - Input: {postcode, datasets: [], force_refresh: bool}
   - Output: {job_id, cached_paths: {}}
   - Parallel downloads via asyncio

2. Python module `pdok_downloader/endpoints.py`:
   - PDOK API endpoints per dataset
   - BAG: https://api.pdok.nl/lv/bag/wfs/v2_0
   - BGT: https://api.pdok.nl/lv/bgt/download/v1_0
   - AHN: https://api.pdok.nl/rws/ahn/wms
   - NWB: https://api.pdok.nl/rws/nwbwegen/wfs
   - Helper functions voor bbox queries

3. Python module `pdok_downloader/postcode_to_bbox.py`:
   - Use PDOK Locatieserver om postcode naar coördinaten
   - Calculate bbox inclusief margin
   - Return in RD-New (EPSG:28992)

4. Python module `pdok_downloader/cache.py`:
   - Cache location: /mnt/nova/cache/pdok/
   - Naming: {dataset}_{postcode}_{version}.{ext}
   - Check age, size, integrity
   - LRU cleanup bij disk pressure

5. Python module `pdok_downloader/verifier.py`:
   - Parse downloaded files
   - Feature count checks
   - Geometry validity sampling
   - Output: {valid, issues}

6. Retry logic:
   - Exponential backoff
   - Different endpoint fallbacks
   - Alert monitor agent bij persistent failures

7. N8n workflow
8. CLI: `pdok-download --postcode 7901 --datasets bag,bgt,ahn`

Gebruik Python 3.11, FastAPI, httpx async, geopandas.
Respect PDOK fair use policy (max concurrent connections).
```

## Test Scenario's

1. Postcode 7901 alle datasets → successful download
2. Cache hit scenario → skip download, use cached
3. Network failure mid-download → resume from last chunk
4. Invalid postcode → clean error message

## Success Metrics

- Download success rate: > 95%
- Cache hit rate na 1e download: > 80%
- Data integrity verification: 100%
