"""NOVA v2 Agent 13 — PDOK Downloader (postcode cache + PDOK 3D OGC API).

FASE 8 FIX 7: oude endpoints (brt.kadaster.nl / hardcoded
download.pdok.nl/kadaster/basisvoorziening-3d-paden) zijn vervangen door de
PDOK OGC API. CityJSON-download per kaartblad met JAARGANG-REGEL: eerst de
daadwerkelijk beschikbare jaargangen opvragen, dan de meest recente kiezen
(overridebaar via request-parameter `jaargang`).
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import ssl
import sys as _sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote, urljoin

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

_sys.path.insert(0, "/nova_shared")
_sys.path.insert(0, r"L:\!Nova V2\shared")
try:
    from proof import make_and_record as _make_and_record_proof
except ImportError:  # pragma: no cover
    def _make_and_record_proof(*_a, **_k):  # type: ignore[misc]
        return {}

logger = logging.getLogger("agent_13")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="NOVA v2 Agent 13 - PDOK Downloader", version="0.3.0")

CACHE_META: Dict[str, Dict[str, Any]] = {}

PDOK_3D_BASE = "https://api.pdok.nl/kadaster/3d-basisvoorziening/ogc/v1"
DEFAULT_OUTPUT_DIR = Path(r"L:\! 2 Nova v2 OUTPUT !\pdok_3d")
EPSG28992 = "http://www.opengis.net/def/crs/EPSG/0/28992"
CRS84 = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"


def _pdok_ssl_context() -> ssl.SSLContext:
    """PDOK's CA-keten faalt de Python 3.13+ VERIFY_X509_STRICT-controle
    ('Basic Constraints of CA cert not marked critical'); certificaat-verificatie
    zelf blijft gewoon aan."""
    ctx = ssl.create_default_context()
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


_SSL_CTX = _pdok_ssl_context()


def _client(**kw: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(verify=_SSL_CTX, **kw)


COLLECTION_ALIASES: Dict[str, str] = {
    "3d-tiles-gebouwen": "gebouwen",
    "3d-tiles-terreinen": "terreinen",
    "dtm": "digitaalterreinmodel",
    "dsm": "digitaaloppervlaktemodel_20cm",
}

TILES_COLLECTIONS = {"gebouwen", "terreinen"}
COVERAGE_COLLECTIONS = {"digitaalterreinmodel", "digitaaloppervlaktemodel_20cm", "digitaaloppervlaktemodel_8cm"}

# FASE 8 FIX 7: CityJSON-download per kaartblad (vervangt de oude brt.kadaster.nl-route)
CITYJSON_COLLECTIONS = {"basisbestand_gebouwen_terreinen", "basisbestand_gebouwen"}
CITYJSON_ALIASES: Dict[str, str] = {
    "volledig": "basisbestand_gebouwen_terreinen",   # oude "Volledig": gebouwen+terrein+wegen+water
    "gebouwen_terreinen": "basisbestand_gebouwen_terreinen",
    "gebouwen": "basisbestand_gebouwen",             # alleen gebouwen
}
MAX_FULL_VALIDATE_BYTES = 400 * 1024 * 1024

Bbox = Tuple[float, float, float, float]


class DownloadBody(BaseModel):
    postcode: str = Field(..., min_length=4, max_length=12)
    layers: List[str] = Field(default_factory=lambda: ["BAG"])


def _cache_key(pc: str, layers: List[str]) -> str:
    raw = json.dumps({"postcode": pc.upper(), "layers": sorted(layers)}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _parse_bbox(raw: Any) -> Bbox:
    if isinstance(raw, dict):
        vals = [raw.get("min_x"), raw.get("min_y"), raw.get("max_x"), raw.get("max_y")]
    elif isinstance(raw, (list, tuple)) and len(raw) == 4:
        vals = list(raw)
    else:
        raise ValueError("bbox must be [min_x, min_y, max_x, max_y] in EPSG:28992")
    try:
        min_x, min_y, max_x, max_y = (float(v) for v in vals)
    except (TypeError, ValueError) as exc:
        raise ValueError("bbox values must be numeric") from exc
    if min_x >= max_x or min_y >= max_y:
        raise ValueError("invalid bbox: min must be less than max")
    return min_x, min_y, max_x, max_y


def _resolve_output_dir(raw: Any) -> Path:
    out = Path(str(raw or DEFAULT_OUTPUT_DIR))
    out.mkdir(parents=True, exist_ok=True)
    return out


def rd_to_wgs84(x: float, y: float) -> Tuple[float, float]:
    """RD New (EPSG:28992) -> WGS84 lon/lat (RDNAPTRANS approximation)."""
    dx = (x - 155_000.0) * 1e-5
    dy = (y - 463_000.0) * 1e-5
    lat = 52.15517440 + (
        (3235.65389 * dy)
        + (-32.58297 * dx * dx)
        + (-0.24750 * dy * dy)
        + (-0.84978 * dx * dx * dy)
        + (-0.06550 * dy * dy * dy)
        + (-0.01709 * dx * dx * dy * dy)
        + (-0.00738 * dx)
        + (0.00530 * dx * dx * dx)
        + (-0.00039 * dx * dy * dy)
        + (0.00033 * dx * dx * dx * dx)
        + (-0.00012 * dx * dy * dy * dy)
    ) / 3600.0
    lon = 5.38720621 + (
        (5260.52916 * dx)
        + (105.94684 * dx * dy)
        + (2.45656 * dx * dy * dy)
        + (-0.81885 * dx * dx * dx)
        + (0.05594 * dx * dy * dy * dy)
        + (-0.05607 * dx * dx * dx * dy)
        + (0.01199 * dy)
        + (-0.00256 * dx * dx * dy)
        + (0.00128 * dx * dy * dy * dy)
        + (0.00022 * dy * dy)
        + (-0.00022 * dx * dx)
        + (0.00026 * dx * dx * dx * dx)
    ) / 3600.0
    return lon, lat


def bbox_rd_to_wgs84(bbox: Bbox) -> Tuple[float, float, float, float]:
    min_x, min_y, max_x, max_y = bbox
    sw = rd_to_wgs84(min_x, min_y)
    ne = rd_to_wgs84(max_x, max_y)
    return min(sw[0], ne[0]), min(sw[1], ne[1]), max(sw[0], ne[0]), max(sw[1], ne[1])


def _regions_intersect(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> bool:
    aw, as_, ae, an = a
    bw, bs, be, bn = b
    return not (ae < bw or be < aw or an < bs or bn < as_)


def _lonlat_to_tile(lon: float, lat: float, zoom: int) -> Tuple[int, int]:
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return max(0, min(n - 1, x)), max(0, min(n - 1, y))


async def _fetch_json(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
    r = await client.get(url, headers={"Accept": "application/json"}, timeout=120.0)
    r.raise_for_status()
    return r.json()


async def _download_file(client: httpx.AsyncClient, url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    async with client.stream("GET", url, timeout=600.0, follow_redirects=True) as resp:
        resp.raise_for_status()
        with dest.open("wb") as fh:
            async for chunk in resp.aiter_bytes(256 * 1024):
                fh.write(chunk)


async def list_collections() -> Dict[str, Any]:
    async with _client() as client:
        data = await _fetch_json(client, f"{PDOK_3D_BASE}/collections?f=json")
    cols = data.get("collections") or []
    return {
        "ok": True,
        "base": PDOK_3D_BASE,
        "count": len(cols),
        "collections": [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "collectionType": c.get("collectionType"),
            }
            for c in cols
        ],
    }


async def _get_collection_meta(client: httpx.AsyncClient, collection_id: str) -> Dict[str, Any]:
    cid = COLLECTION_ALIASES.get(collection_id, collection_id)
    return await _fetch_json(client, f"{PDOK_3D_BASE}/collections/{cid}?f=json")


def _tileset_content_uris(node: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    content = node.get("content") or {}
    uri = content.get("uri")
    if uri:
        out.append(str(uri))
    for child in node.get("children") or []:
        out.extend(_tileset_content_uris(child))
    return out


def _tileset_region(node: Dict[str, Any]) -> Optional[Tuple[float, float, float, float]]:
    bv = node.get("boundingVolume") or {}
    region = bv.get("region")
    if isinstance(region, list) and len(region) >= 4:
        west, south, east, north = (math.degrees(region[i]) for i in range(4))
        return west, south, east, north
    return None


def _collect_tile_assets(
    node: Dict[str, Any],
    base_prefix: str,
    wgs_bbox: Tuple[float, float, float, float],
    assets: List[str],
    subtrees: List[str],
    max_assets: int,
) -> None:
    if len(assets) >= max_assets:
        return
    region = _tileset_region(node)
    if region and not _regions_intersect(region, wgs_bbox):
        return
    content = node.get("content") or {}
    uri = str(content.get("uri") or "")
    if uri:
        if uri.endswith(".json"):
            subtrees.append(urljoin(base_prefix, uri))
        elif uri.endswith((".glb", ".b3dm", ".i3dm", ".pnts", ".cmpt", ".terrain")):
            assets.append(urljoin(base_prefix, uri))
    for child in node.get("children") or []:
        _collect_tile_assets(child, base_prefix, wgs_bbox, assets, subtrees, max_assets)
        if len(assets) >= max_assets:
            return


async def _download_3d_tiles(
    collection_id: str,
    bbox: Bbox,
    output_dir: Path,
    max_assets: int = 100,
) -> Dict[str, Any]:
    cid = COLLECTION_ALIASES.get(collection_id, collection_id)
    if cid not in TILES_COLLECTIONS:
        raise ValueError(f"not a 3D tiles collection: {collection_id}")

    wgs_bbox = bbox_rd_to_wgs84(bbox)
    tileset_root = f"{PDOK_3D_BASE}/collections/{cid}/3dtiles?f=json"
    out_root = output_dir / cid / f"{int(bbox[0])}_{int(bbox[1])}_{int(bbox[2])}_{int(bbox[3])}"
    out_root.mkdir(parents=True, exist_ok=True)

    async with _client() as client:
        meta = await _get_collection_meta(client, cid)
        root_doc = await _fetch_json(client, tileset_root)
        (out_root / "tileset.root.json").write_text(json.dumps(root_doc, indent=2), encoding="utf-8")

        assets: List[str] = []
        subtrees: List[str] = []
        base_prefix = f"{PDOK_3D_BASE}/collections/{cid}/3dtiles/"
        _collect_tile_assets(root_doc.get("root") or {}, base_prefix, wgs_bbox, assets, subtrees, max_assets)

        seen_sub: set[str] = set()
        while subtrees and len(assets) < max_assets:
            rel = subtrees.pop(0)
            if rel in seen_sub:
                continue
            seen_sub.add(rel)
            try:
                doc = await _fetch_json(client, rel if rel.startswith("http") else urljoin(base_prefix, rel))
            except Exception as exc:
                logger.warning("skip subtree %s: %s", rel, exc)
                continue
            rel_path = rel.split("/3dtiles/", 1)[-1]
            sub_prefix = urljoin(base_prefix, rel_path.rsplit("/", 1)[0] + "/") if "/" in rel_path else base_prefix
            local_meta = out_root / rel_path.replace("/", "_")
            local_meta.write_text(json.dumps(doc, indent=2), encoding="utf-8")
            _collect_tile_assets(doc.get("root") or {}, sub_prefix, wgs_bbox, assets, subtrees, max_assets)

        downloaded: List[str] = []
        for url in assets[:max_assets]:
            rel = url.split("/3dtiles/", 1)[-1]
            dest = out_root / rel.replace("/", "_")
            if dest.is_file():
                downloaded.append(str(dest))
                continue
            try:
                await _download_file(client, url, dest)
                downloaded.append(str(dest))
            except Exception as exc:
                logger.warning("download failed %s: %s", url, exc)

    return {
        "ok": True,
        "collection": cid,
        "alias": collection_id,
        "bbox_rd": list(bbox),
        "bbox_wgs84": list(wgs_bbox),
        "output_dir": str(out_root),
        "tileset_root": tileset_root,
        "title": meta.get("title"),
        "assets_found": len(assets),
        "assets_downloaded": len(downloaded),
        "files": downloaded,
        "note": "Partial bbox download; full 73GB dataset not via API.",
    }


async def download_3d_tiles_gebouwen(bbox: Bbox, output_dir: Path) -> Dict[str, Any]:
    return await _download_3d_tiles("3d-tiles-gebouwen", bbox, output_dir)


async def download_3d_tiles_terreinen(bbox: Bbox, output_dir: Path) -> Dict[str, Any]:
    return await _download_3d_tiles("3d-tiles-terreinen", bbox, output_dir)


async def _download_dtm_coverage(bbox: Bbox, output_dir: Path, max_tiles: int = 64) -> Dict[str, Any]:
    cid = COLLECTION_ALIASES["dtm"]
    wgs_bbox = bbox_rd_to_wgs84(bbox)
    out_root = output_dir / cid / f"{int(bbox[0])}_{int(bbox[1])}_{int(bbox[2])}_{int(bbox[3])}"
    out_root.mkdir(parents=True, exist_ok=True)
    tilejson_url = f"{PDOK_3D_BASE}/collections/{cid}/quantized-mesh?f=json"
    base_tiles = f"{PDOK_3D_BASE}/collections/{cid}/quantized-mesh/"

    async with _client() as client:
        meta = await _get_collection_meta(client, cid)
        tilejson = await _fetch_json(client, tilejson_url)
        (out_root / "tilejson.json").write_text(json.dumps(tilejson, indent=2), encoding="utf-8")
        version = str(tilejson.get("version") or "1.1.0")
        template = (tilejson.get("tiles") or ["{z}/{x}/{y}.terrain?v={version}"])[0]

        downloaded: List[str] = []
        min_lon, min_lat, max_lon, max_lat = wgs_bbox
        for zoom in range(10, 16):
            x0, y1 = _lonlat_to_tile(min_lon, min_lat, zoom)
            x1, y0 = _lonlat_to_tile(max_lon, max_lat, zoom)
            for x in range(min(x0, x1), max(x0, x1) + 1):
                for y in range(min(y0, y1), max(y0, y1) + 1):
                    if len(downloaded) >= max_tiles:
                        break
                    rel = template.format(z=zoom, x=x, y=y, version=version)
                    url = urljoin(base_tiles, rel)
                    dest = out_root / f"z{zoom}_x{x}_y{y}.terrain"
                    try:
                        await _download_file(client, url, dest)
                        downloaded.append(str(dest))
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code != 404:
                            logger.warning("terrain tile %s: %s", url, exc)
                    except Exception as exc:
                        logger.warning("terrain tile %s: %s", url, exc)
                if len(downloaded) >= max_tiles:
                    break
            if len(downloaded) >= max_tiles:
                break

    return {
        "ok": True,
        "collection": cid,
        "bbox_rd": list(bbox),
        "bbox_wgs84": list(wgs_bbox),
        "output_dir": str(out_root),
        "tilejson_url": tilejson_url,
        "title": meta.get("title"),
        "tiles_downloaded": len(downloaded),
        "files": downloaded,
        "note": "Quantized-mesh partial coverage; full DTM zip ~12GB not via tile API.",
    }


async def download_dtm(bbox: Bbox, output_dir: Path) -> Dict[str, Any]:
    return await _download_dtm_coverage(bbox, output_dir)


async def _download_dsm_coverage(bbox: Bbox, output_dir: Path, max_items: int = 20) -> Dict[str, Any]:
    cid = COLLECTION_ALIASES["dsm"]
    out_root = output_dir / cid / f"{int(bbox[0])}_{int(bbox[1])}_{int(bbox[2])}_{int(bbox[3])}"
    out_root.mkdir(parents=True, exist_ok=True)
    min_x, min_y, max_x, max_y = bbox
    bbox_param = f"{min_x},{min_y},{max_x},{max_y}"
    items_url = (
        f"{PDOK_3D_BASE}/collections/{cid}/items"
        f"?bbox={bbox_param}&bbox-crs={quote(EPSG28992, safe='')}&f=json&limit={max_items}"
    )

    async with _client() as client:
        meta = await _get_collection_meta(client, cid)
        fc = await _fetch_json(client, items_url)
        (out_root / "items_bbox.json").write_text(json.dumps(fc, indent=2), encoding="utf-8")

        downloaded: List[str] = []
        for feat in fc.get("features") or []:
            for link in feat.get("links") or []:
                if link.get("rel") != "enclosure":
                    continue
                href = str(link.get("href") or "")
                if not href:
                    continue
                name = href.rstrip("/").rsplit("/", 1)[-1]
                if not name.lower().endswith((".laz", ".las", ".zip")):
                    continue
                dest = out_root / name
                if dest.is_file():
                    downloaded.append(str(dest))
                    continue
                try:
                    await _download_file(client, href, dest)
                    downloaded.append(str(dest))
                except Exception as exc:
                    logger.warning("dsm download %s: %s", href, exc)

    return {
        "ok": True,
        "collection": cid,
        "bbox_rd": list(bbox),
        "output_dir": str(out_root),
        "items_url": items_url,
        "title": meta.get("title"),
        "features_matched": len(fc.get("features") or []),
        "files_downloaded": len(downloaded),
        "files": downloaded,
        "note": "Partial bbox LAZ tiles only; full DSM not via single API call.",
    }


async def download_dsm(bbox: Bbox, output_dir: Path) -> Dict[str, Any]:
    return await _download_dsm_coverage(bbox, output_dir)


def _validate_cityjson(path: Path) -> Dict[str, Any]:
    """Valideer een (uitgepakt) CityJSON-bestand. Volledige parse tot
    MAX_FULL_VALIDATE_BYTES; daarboven alleen een type-marker-scan (eerlijk gemeld)."""
    size = path.stat().st_size
    if size <= MAX_FULL_VALIDATE_BYTES:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return {"valid": False, "methode": "volledige_parse", "fout": str(exc)[:200]}
        checks = {
            "type_cityjson": doc.get("type") == "CityJSON",
            "heeft_version": bool(doc.get("version")),
            "heeft_cityobjects": isinstance(doc.get("CityObjects"), dict) and len(doc["CityObjects"]) > 0,
            "heeft_vertices": isinstance(doc.get("vertices"), list) and len(doc["vertices"]) > 0,
        }
        return {
            "valid": all(checks.values()),
            "methode": "volledige_parse",
            "checks": checks,
            "version": doc.get("version"),
            "cityobjects": len(doc.get("CityObjects") or {}),
            "vertices": len(doc.get("vertices") or []),
            "size_bytes": size,
        }
    head = path.open("rb").read(1024 * 1024).decode("utf-8", errors="replace")
    marker = '"type"' in head and '"CityJSON"' in head
    return {
        "valid": bool(marker),
        "methode": "marker_scan_eerste_1MB",
        "note": f"bestand {size/1e6:.0f}MB > limiet voor volledige parse; alleen type-marker gecontroleerd",
        "size_bytes": size,
    }


async def download_kaartblad(
    kaartblad: str,
    collection: str = "basisbestand_gebouwen_terreinen",
    jaargang: Optional[int] = None,
    output_dir: Optional[Path] = None,
    unzip: bool = True,
) -> Dict[str, Any]:
    """FASE 8 FIX 7: CityJSON-download per kaartblad via de PDOK OGC API.

    JAARGANG-REGEL: vraag eerst de daadwerkelijk beschikbare jaargangen voor dit
    kaartblad+collectie op en kies daaruit de meest recente — nooit een default of
    hardcoded jaartal. `jaargang` is overridebaar (reproduceerbare bakes) maar moet
    in de beschikbare lijst zitten. Beide worden gelogd in het job-resultaat.
    """
    blad = (kaartblad or "").strip().lower()
    if not blad:
        raise ValueError("kaartblad is verplicht (bv. '17cz2')")
    cid = CITYJSON_ALIASES.get((collection or "").strip().lower(), (collection or "").strip())
    if cid not in CITYJSON_COLLECTIONS:
        raise ValueError(
            f"onbekende CityJSON-collectie: {collection!r}; geldig: {sorted(CITYJSON_COLLECTIONS)} "
            f"of alias {sorted(CITYJSON_ALIASES)}"
        )
    out_base = output_dir or DEFAULT_OUTPUT_DIR
    items_url = f"{PDOK_3D_BASE}/collections/{cid}/items?bladnr={quote(blad)}&f=json&limit=100"

    async with _client() as client:
        fc = await _fetch_json(client, items_url)
        feats = [
            f for f in (fc.get("features") or [])
            if str((f.get("properties") or {}).get("bladnr", "")).lower() == blad
        ]
        per_jaar: Dict[int, Dict[str, Any]] = {}
        for f in feats:
            jr = (f.get("properties") or {}).get("jaargang_luchtfoto")
            if jr is not None:
                per_jaar[int(jr)] = f
        beschikbaar = sorted(per_jaar)
        if not beschikbaar:
            raise ValueError(
                f"geen jaargangen beschikbaar via de API voor kaartblad {blad!r} in {cid} "
                f"(items: {len(fc.get('features') or [])})"
            )
        if jaargang is not None:
            gekozen = int(jaargang)
            if gekozen not in per_jaar:
                raise ValueError(
                    f"jaargang {gekozen} niet beschikbaar voor kaartblad {blad!r}; "
                    f"beschikbaar: {beschikbaar}"
                )
            bron = "request_override"
        else:
            gekozen = max(beschikbaar)
            bron = "max_beschikbaar"
        logger.info(
            "JAARGANG-REGEL kaartblad=%s collectie=%s beschikbaar=%s gekozen=%s bron=%s",
            blad, cid, beschikbaar, gekozen, bron,
        )

        feat = per_jaar[gekozen]
        href = ""
        for link in feat.get("links") or []:
            if link.get("rel") == "enclosure" and str(link.get("href", "")).lower().endswith(".zip"):
                href = str(link["href"])
                break
        if not href:
            href = str((feat.get("properties") or {}).get("download_link") or "")
        if not href:
            raise ValueError(f"geen download-link in API-response voor {blad} jaargang {gekozen}")

        out_root = Path(out_base) / cid / f"{blad}_{gekozen}"
        out_root.mkdir(parents=True, exist_ok=True)
        zip_path = out_root / href.rsplit("/", 1)[-1]
        if not zip_path.is_file():
            await _download_file(client, href, zip_path)

    cityjson_files: List[Path] = []
    validatie: Dict[str, Any] = {}
    if unzip:
        extract_dir = out_root / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        cityjson_files = sorted(
            p for p in extract_dir.rglob("*.json") if p.is_file()
        )
        if cityjson_files:
            validatie = _validate_cityjson(cityjson_files[0])

    result: Dict[str, Any] = {
        "ok": True,
        "kaartblad": blad,
        "collection": cid,
        "items_url": items_url,
        # JAARGANG-REGEL: beide expliciet in het job-resultaat
        "beschikbare_jaargangen": beschikbaar,
        "gekozen_jaargang": gekozen,
        "jaargang_bron": bron,
        "download_url": href,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "cityjson_files": [str(p) for p in cityjson_files[:50]],
        "cityjson_validatie": validatie,
    }
    result["proof"] = _make_and_record_proof(
        "file",
        path=str(zip_path),
        agent="13_pdok_downloader",
        note=f"kaartblad {blad} {cid} jaargang={gekozen} ({bron}; beschikbaar {beschikbaar})",
        context="pdok_kaartblad_download",
    )
    return result


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "13_pdok_downloader", "version": "0.3.0"}


@app.post("/download")
def download(body: DownloadBody) -> Dict[str, Any]:
    layers = body.layers or ["BAG"]
    key = _cache_key(body.postcode, layers)
    rec = {
        "cache_key": key,
        "minio_bucket": "nova-pdok-cache",
        "object_prefix": f"pdok/{body.postcode.upper()}/{key}/",
        "layers": layers,
        "delta_detected": False,
        "fetched_at": time.time(),
        "note": "Stub response — replace with PDOK REST + MinIO put_object.",
    }
    CACHE_META[key] = rec
    return rec


@app.post("/invoke")
async def invoke(body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"error": "expected_object"}

    action = str(body.get("action", "")).lower()
    if not action and body.get("postcode"):
        return download(DownloadBody.model_validate(body))

    if action == "list_collections":
        return await list_collections()

    # FASE 8 FIX 7: CityJSON-download per kaartblad met jaargang-regel
    if action == "download_kaartblad":
        try:
            jaargang_raw = body.get("jaargang")
            return await download_kaartblad(
                kaartblad=str(body.get("kaartblad") or ""),
                collection=str(body.get("collection") or "basisbestand_gebouwen_terreinen"),
                jaargang=int(jaargang_raw) if jaargang_raw is not None else None,
                output_dir=Path(str(body["output_dir"])) if body.get("output_dir") else None,
                unzip=bool(body.get("unzip", True)),
            )
        except ValueError as exc:
            raise HTTPException(400, detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(502, detail=f"pdok_api_error: {exc}") from exc

    download_actions = {
        "download_3d_tiles_gebouwen": download_3d_tiles_gebouwen,
        "download_3d_tiles_terreinen": download_3d_tiles_terreinen,
        "download_dtm": download_dtm,
        "download_dsm": download_dsm,
    }
    if action in download_actions:
        try:
            bbox = _parse_bbox(body.get("bbox"))
        except ValueError as exc:
            raise HTTPException(400, detail=str(exc)) from exc
        output_dir = _resolve_output_dir(body.get("output_dir"))
        try:
            return await download_actions[action](bbox, output_dir)
        except ValueError as exc:
            raise HTTPException(400, detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(502, detail=f"pdok_api_error: {exc}") from exc

    return {
        "hint": "POST /download or invoke with action",
        "valid_actions": ["list_collections", "download_kaartblad", *download_actions.keys()],
        "keys": list(body.keys()),
    }
