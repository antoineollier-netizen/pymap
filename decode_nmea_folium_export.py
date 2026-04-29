#!/usr/bin/env python3
# ------------------------------------------------------------
# EXEMPLE USAGE : python decode_nmea_folium_export.py input.nmea 
# ------------------------------------------------------------
# ✅ Fichiers générés :
# - input.html
# - input.gpx
# - input.kml
import argparse
import os
import folium
import xml.etree.ElementTree as ET


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def nmea_to_decimal(coord, direction):
    if not coord:
        return None
    deg_len = 2 if direction in ("N", "S") else 3
    deg = float(coord[:deg_len])
    minutes = float(coord[deg_len:])
    dec = deg + minutes / 60.0
    if direction in ("S", "W"):
        dec *= -1
    return dec


def parse_time(timestr):
    if not timestr or len(timestr) < 6:
        return "N/A"
    return f"{timestr[0:2]}:{timestr[2:4]}:{timestr[4:6]}"


# ------------------------------------------------------------
# NMEA parsing
# ------------------------------------------------------------
def parse_nmea_line(line):
    """
    Supports:
      - GPRMC : lat, lon, speed, time
      - GPGGA : lat, lon, altitude, time
    Returns: dict or None
    """
    if line.startswith("$GPRMC"):
        p = line.split(",")
        if len(p) < 10 or p[2] != "A":
            return None

        return {
            "lat": nmea_to_decimal(p[3], p[4]),
            "lon": nmea_to_decimal(p[5], p[6]),
            "speed": float(p[7]) * 1.852 if p[7] else None,  # km/h
            "time": parse_time(p[1]),
            "alt": None,
        }

    elif line.startswith("$GPGGA"):
        p = line.split(",")
        if len(p) < 10:
            return None

        return {
            "lat": nmea_to_decimal(p[2], p[3]),
            "lon": nmea_to_decimal(p[4], p[5]),
            "speed": None,
            "time": parse_time(p[1]),
            "alt": float(p[9]) if p[9] else None,
        }

    return None


def load_nmea_file(path):
    points = []
    with open(path, "r") as f:
        for line in f:
            parsed = parse_nmea_line(line.strip())
            if parsed and parsed["lat"] and parsed["lon"]:
                points.append(parsed)
    return points


# ------------------------------------------------------------
# Color logic
# ------------------------------------------------------------
def speed_to_color(speed):
    if speed is None:
        return "gray"
    if speed > 10:
        return "green"
    elif 5 <= speed <= 10:
        return "orange"
    else:
        return "yellow"


# ------------------------------------------------------------
# Folium map
# ------------------------------------------------------------
def create_map(points, output_html):
    m = folium.Map(
        location=[points[0]["lat"], points[0]["lon"]],
        zoom_start=15
    )

    for i in range(1, len(points)):
        p0 = points[i - 1]
        p1 = points[i]

        color = speed_to_color(p1["speed"])

        popup_text = (
            f"Heure : {p1['time']}<br>"
            f"Altitude : {p1['alt']} m<br>"
            f"Vitesse : {p1['speed']:.1f} km/h"
            if p1["speed"] is not None
            else
            f"Heure : {p1['time']}<br>"
            f"Altitude : {p1['alt']} m<br>"
            f"Vitesse : inconnue"
        )

        folium.PolyLine(
            [(p0["lat"], p0["lon"]), (p1["lat"], p1["lon"])],
            color=color,
            weight=4,
            opacity=0.9
        ).add_to(m)

        folium.CircleMarker(
            [p1["lat"], p1["lon"]],
            radius=4,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=popup_text
        ).add_to(m)

    m.save(output_html)


# ------------------------------------------------------------
# GPX export
# ------------------------------------------------------------
def export_gpx(points, output_gpx):
    gpx = ET.Element("gpx", version="1.1", creator="NMEA Decoder")
    trk = ET.SubElement(gpx, "trk")
    trkseg = ET.SubElement(trk, "trkseg")

    for p in points:
        trkpt = ET.SubElement(
            trkseg, "trkpt",
            lat=str(p["lat"]),
            lon=str(p["lon"])
        )
        if p["alt"] is not None:
            ET.SubElement(trkpt, "ele").text = str(p["alt"])

    ET.ElementTree(gpx).write(output_gpx, encoding="utf-8", xml_declaration=True)


# ------------------------------------------------------------
# KML export
# ------------------------------------------------------------
def export_kml(points, output_kml):
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    placemark = ET.SubElement(doc, "Placemark")
    linestring = ET.SubElement(placemark, "LineString")
    coords = ET.SubElement(linestring, "coordinates")

    coords.text = " ".join(
        f"{p['lon']},{p['lat']},{p['alt'] or 0}"
        for p in points
    )

    ET.ElementTree(kml).write(output_kml, encoding="utf-8", xml_declaration=True)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Decode NMEA and generate map + GPX + KML"
    )
    parser.add_argument("nmea_file", help="Fichier NMEA (ex: mon_fichier.nmea)")
    args = parser.parse_args()

    base_name = os.path.splitext(os.path.basename(args.nmea_file))[0]

    points = load_nmea_file(args.nmea_file)
    if not points:
        raise RuntimeError("Aucun point GPS valide trouvé.")

    create_map(points, f"{base_name}.html")
    export_gpx(points, f"{base_name}.gpx")
    export_kml(points, f"{base_name}.kml")

    print("✅ Fichiers générés :")
    print(f" - {base_name}.html")
    print(f" - {base_name}.gpx")
    print(f" - {base_name}.kml")


if __name__ == "__main__":
    main()