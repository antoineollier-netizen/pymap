import folium

def parse_nmea_line(line):
    if line.startswith('$GPRMC'):
        parts = line.split(',')
        if len(parts) < 7 or parts[2] != 'A':
            return None
        lat_raw, lat_dir = parts[3], parts[4]
        lon_raw, lon_dir = parts[5], parts[6]
    elif line.startswith('$GPGGA'):
        parts = line.split(',')
        if len(parts) < 6: return None
        lat_raw, lat_dir = parts[2], parts[3]
        lon_raw, lon_dir = parts[4], parts[5]
    else: return None

    def convert(coord, direction):
        if not coord: return None
        deg = float(coord[:2 if direction in ['N','S'] else 3])
        minutes = float(coord[2 if direction in ['N','S'] else 3:])
        dec = deg + minutes/60
        if direction in ['S','W']: dec *= -1
        return dec

    return convert(lat_raw, lat_dir), convert(lon_raw, lon_dir)

def load_nmea_file(path):
    pts = []
    with open(path) as f:
        for line in f:
            p = parse_nmea_line(line.strip())
            if p: pts.append(p)
    return pts

def create_map(points, save_path='map.html'):
    start = points[0]
    m = folium.Map(location=start, zoom_start=15)
    folium.PolyLine(points, color='blue', weight=3).add_to(m)
    for lat, lon in points:
        folium.CircleMarker([lat, lon], radius=4, color='red', fill=True).add_to(m)
    m.save(save_path)

if __name__ == '__main__':
    pts = load_nmea_file('input.nmea')
    create_map(pts, 'parcours_nmea.html')
