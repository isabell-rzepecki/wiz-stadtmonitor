"""Vektorkacheln (MVT) in einer PMTiles-Datei für große Kartenebenen (Gebäude, Bodenrichtwertzonen).

PMTiles ist eine einzelne Datei; der Browser lädt nur die nötigen Kacheln über HTTP-Range-Abfragen. GitHub Pages
beantwortet sie (Status 206) und komprimiert Binärdateien nicht (geprüft am 26.10.2026). Die Kacheln sind mit gzip
komprimiert, ohne Zeitstempel, damit dieselben Daten dieselbe Datei ergeben.
"""
import gzip
import math

import mapbox_vector_tile
import numpy as np
import shapely
from pmtiles.tile import Compression, TileType, zxy_to_tileid
from pmtiles.writer import Writer
from pyproj import Transformer
from shapely import STRtree, box, clip_by_rect
from shapely.geometry import shape

R = 6378137.0
HALB = math.pi * R  # halber Erdumfang in Web-Mercator (EPSG:3857)
PUFFER = 64 / 4096  # Rand um jede Kachel (Anteil der Kachelbreite), damit Linien an Kachelgrenzen nicht abreißen


def projizieren(g, fn):
    """Geometrie mit einer pyproj-Transformation (always_xy) umrechnen."""
    return shapely.transform(g, lambda xy: np.column_stack(fn(xy[:, 0], xy[:, 1])))


def _kachel_grenzen(z, x, y):
    n = 2 ** z
    breite = 2 * HALB / n
    x0 = -HALB + x * breite
    y1 = HALB - y * breite
    return x0, y1 - breite, x0 + breite, y1


def _kacheln_fuer(bounds, z):
    n = 2 ** z
    breite = 2 * HALB / n
    x0, y0, x1, y1 = bounds
    return (range(max(0, int((x0 + HALB) // breite)), min(n - 1, int((x1 + HALB) // breite)) + 1),
            range(max(0, int((HALB - y1) // breite)), min(n - 1, int((HALB - y0) // breite)) + 1))


def schreiben(features, ziel, ebene, min_zoom, max_zoom, attribution="", vereinfachen=True):
    """GeoJSON-Features (EPSG:4326) als PMTiles; je Zoomstufe vereinfacht (etwa ein halbes Pixel). Gibt die Zahl der
    Kacheln zurück."""
    merc = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
    geoms = [projizieren(shape(f["geometry"]), merc) for f in features]
    props = [f.get("properties") or {} for f in features]
    baum = STRtree(geoms)
    gx0 = min(g.bounds[0] for g in geoms)
    gy0 = min(g.bounds[1] for g in geoms)
    gx1 = max(g.bounds[2] for g in geoms)
    gy1 = max(g.bounds[3] for g in geoms)
    kacheln = []
    for z in range(min_zoom, max_zoom + 1):
        xs, ys = _kacheln_fuer((gx0, gy0, gx1, gy1), z)
        breite = 2 * HALB / 2 ** z
        toleranz = breite / 4096 / 2 if vereinfachen and z < max_zoom else 0
        for x in xs:
            for y in ys:
                x0, y0, x1, y1 = _kachel_grenzen(z, x, y)
                p = breite * PUFFER
                treffer = baum.query(box(x0 - p, y0 - p, x1 + p, y1 + p))
                if not len(treffer):
                    continue
                objekte = []
                for i in sorted(int(t) for t in treffer):
                    g = clip_by_rect(geoms[i], x0 - p, y0 - p, x1 + p, y1 + p)
                    if toleranz:
                        g = g.simplify(toleranz, preserve_topology=True)
                    if g.is_empty:
                        continue
                    objekte.append({"geometry": g, "properties": props[i]})
                if not objekte:
                    continue
                # in Kachelkoordinaten (0–4096, y nach unten) umrechnen; die Bibliothek rundet nur noch
                for o in objekte:
                    o["geometry"] = shapely.transform(o["geometry"], lambda xy, x0=x0, y1=y1: np.column_stack(
                        ((xy[:, 0] - x0) / breite * 4096, (y1 - xy[:, 1]) / breite * 4096)))
                daten = mapbox_vector_tile.encode([{"name": ebene, "features": objekte}],
                                                  default_options={"y_coord_down": True, "extents": 4096})
                kacheln.append((zxy_to_tileid(z, x, y), gzip.compress(daten, mtime=0)))
    kacheln.sort()
    lon = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform
    w0, s0 = lon(gx0, gy0)
    w1, s1 = lon(gx1, gy1)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel, "wb") as f:
        wr = Writer(f)
        for tid, daten in kacheln:
            wr.write_tile(tid, daten)
        wr.finalize({"tile_type": TileType.MVT, "tile_compression": Compression.GZIP,
                     "min_lon_e7": int(w0 * 1e7), "min_lat_e7": int(s0 * 1e7), "max_lon_e7": int(w1 * 1e7), "max_lat_e7": int(s1 * 1e7),
                     "center_zoom": min_zoom, "center_lon_e7": int((w0 + w1) / 2 * 1e7), "center_lat_e7": int((s0 + s1) / 2 * 1e7)},
                    {"vector_layers": [{"id": ebene, "minzoom": min_zoom, "maxzoom": max_zoom,
                                        "fields": {k: "Number" if all(isinstance(p.get(k), (int, float)) for p in props if p.get(k) is not None) else "String"
                                                   for k in sorted({k for p in props for k in p})}}],
                     "attribution": attribution})
    return len(kacheln)
