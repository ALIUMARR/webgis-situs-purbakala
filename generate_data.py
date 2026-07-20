"""
generate_data.py
Membuat data spasial DUMMY (contoh) untuk 5 layer zonasi konservasi situs purbakala,
lengkap dengan atribut pop-up sesuai instruksi tugas:

- Situs Utama (Candi): Nama Candi, Abad Pembuatan, Kerajaan/Dinasti Pendiri,
  Status Konservasi, Tingkat Risiko Kerusakan, Periode (untuk filter dinamis).
- Fasilitas Edukasi: Nama Fasilitas, Kapasitas Pengunjung harian,
  Jenis Layanan Informasi.

Catatan: Koordinat memakai lokasi fiktif "Situs Purbakala Giri Wangun" di area
Jawa Tengah sebagai contoh. Ganti dengan data hasil digitasi QGIS Anda sendiri
(export ke GeoJSON: klik kanan layer > Export > Save Features As > GeoJSON)
saat data asli sudah tersedia -- pastikan nama kolom atribut tetap sama
seperti di bawah agar pop-up & filter tetap berfungsi.
"""

import geopandas as gpd
from shapely.geometry import Point
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)

WGS84 = "EPSG:4326"
UTM = "EPSG:32749"  # UTM 49S, metrik, cocok untuk wilayah Jawa Tengah

pusat_lat, pusat_lon = -7.60800, 110.20400

# ---------------------------------------------------------------
# 1. ZONASI INTI CANDI (poligon)
# ---------------------------------------------------------------
pusat = gpd.GeoSeries([Point(pusat_lon, pusat_lat)], crs=WGS84).to_crs(UTM)
zonasi_inti_poly = pusat.buffer(60).to_crs(WGS84)

zonasi_inti = gpd.GeoDataFrame(
    {
        "nama": ["Zonasi Inti - Candi Giri Wangun"],
        "kategori": ["Zonasi Inti"],
        "periode": ["Hindu"],
        "keterangan": ["Area konservasi ketat. Dilarang aktivitas fisik selain penelitian & pemugaran."],
    },
    geometry=zonasi_inti_poly.geometry,
    crs=WGS84,
)
zonasi_inti.to_file(os.path.join(OUT_DIR, "zonasi_inti.geojson"), driver="GeoJSON")

# ---------------------------------------------------------------
# Titik pusat candi -- atribut lengkap sesuai instruksi tugas
# ---------------------------------------------------------------
titik_candi = gpd.GeoDataFrame(
    {
        "nama": ["Candi Giri Wangun"],
        "abad_pembuatan": ["Abad ke-9 Masehi"],
        "kerajaan_dinasti_pendiri": ["Wangsa Sailendra"],
        "status_konservasi": ["Terpugar Sebagian"],
        "tingkat_risiko_kerusakan": ["Sedang"],
        "periode": ["Hindu"],
        "kategori": ["Situs Utama"],
        "keterangan": ["Struktur utama candi peninggalan abad ke-9, relief bercorak Hindu-Buddha."],
    },
    geometry=[Point(pusat_lon, pusat_lat)],
    crs=WGS84,
)
titik_candi.to_file(os.path.join(OUT_DIR, "situs_utama.geojson"), driver="GeoJSON")

# ---------------------------------------------------------------
# 2. ZONASI PENYANGGA / BUFFER ZONE (ring 60m - 200m dari pusat)
# ---------------------------------------------------------------
buffer_luar = pusat.buffer(200)
penyangga_geom = buffer_luar.difference(pusat.buffer(60))

zonasi_penyangga = gpd.GeoDataFrame(
    {
        "nama": ["Zonasi Penyangga"],
        "kategori": ["Buffer Zone"],
        "periode": ["Hindu"],
        "keterangan": [
            "Aktivitas wisata terbatas & terjadwal. Kendaraan bermotor dilarang masuk. "
            "Terpantau adanya tekanan ekspansi permukiman warga di batas luar zona ini."
        ],
    },
    geometry=penyangga_geom.to_crs(WGS84).geometry,
    crs=WGS84,
)
zonasi_penyangga.to_file(os.path.join(OUT_DIR, "zonasi_penyangga.geojson"), driver="GeoJSON")

# ---------------------------------------------------------------
# 3. PUSAT INFORMASI & FASILITAS EDUKASI WISATA (titik hijau)
#    Atribut: Nama Fasilitas, Kapasitas Pengunjung harian, Jenis Layanan Informasi
# ---------------------------------------------------------------
fasilitas = gpd.GeoDataFrame(
    {
        "nama": [
            "Pusat Informasi Wisata",
            "Museum Situs Giri Wangun",
            "Gedung Edukasi & Interpretasi",
        ],
        "kategori": ["Fasilitas Edukasi"] * 3,
        "kapasitas_pengunjung_harian": [300, 150, 200],
        "jenis_layanan_informasi": [
            "Loket tiket, peta cetak, pemandu wisata",
            "Pameran artefak & panel edukasi sejarah",
            "Audiovisual, ruang diskusi kelompok pelajar",
        ],
        "periode": ["Hindu", "Hindu", "Hindu"],
        "keterangan": [
            "Loket, peta, dan pemandu wisata.",
            "Koleksi artefak hasil ekskavasi.",
            "Ruang audiovisual edukasi publik.",
        ],
    },
    geometry=[
        Point(pusat_lon + 0.0028, pusat_lat + 0.0012),
        Point(pusat_lon + 0.0031, pusat_lat - 0.0009),
        Point(pusat_lon + 0.0018, pusat_lat + 0.0025),
    ],
    crs=WGS84,
)
fasilitas.to_file(os.path.join(OUT_DIR, "fasilitas_edukasi.geojson"), driver="GeoJSON")

# ---------------------------------------------------------------
# 4. POS PEMANTAUAN / PENJAGA SITUS (titik biru)
# ---------------------------------------------------------------
pos_jaga = gpd.GeoDataFrame(
    {
        "nama": ["Pos Jaga Utara", "Pos Jaga Selatan", "Pos Jaga Timur", "Pos Jaga Barat"],
        "kategori": ["Pos Pemantauan"] * 4,
        "petugas_per_shift": [2, 2, 1, 1],
        "periode": ["Hindu"] * 4,
        "keterangan": ["Pengawasan 24 jam & pencatatan pengunjung."] * 4,
    },
    geometry=[
        Point(pusat_lon, pusat_lat + 0.0021),
        Point(pusat_lon, pusat_lat - 0.0021),
        Point(pusat_lon + 0.0021, pusat_lat),
        Point(pusat_lon - 0.0021, pusat_lat),
    ],
    crs=WGS84,
)
pos_jaga.to_file(os.path.join(OUT_DIR, "pos_pemantauan.geojson"), driver="GeoJSON")

# ---------------------------------------------------------------
# 5. BUFFER KERENTANAN GETARAN 500 m & 1000 m (poligon transparan gradasi)
# ---------------------------------------------------------------
buffer_500 = gpd.GeoDataFrame(
    {
        "nama": ["Buffer Kerentanan Getaran 500m"],
        "radius_m": [500],
        "periode": ["Hindu"],
        "keterangan": ["Risiko getaran tinggi dari aktivitas kendaraan/konstruksi."],
    },
    geometry=pusat.buffer(500).to_crs(WGS84).geometry,
    crs=WGS84,
)
buffer_500.to_file(os.path.join(OUT_DIR, "buffer_getaran_500.geojson"), driver="GeoJSON")

buffer_1000_ring = pusat.buffer(1000).difference(pusat.buffer(500))
buffer_1000 = gpd.GeoDataFrame(
    {
        "nama": ["Buffer Kerentanan Getaran 1000m"],
        "radius_m": [1000],
        "periode": ["Hindu"],
        "keterangan": ["Risiko getaran sedang, perlu pemantauan berkala."],
    },
    geometry=buffer_1000_ring.to_crs(WGS84).geometry,
    crs=WGS84,
)
buffer_1000.to_file(os.path.join(OUT_DIR, "buffer_getaran_1000.geojson"), driver="GeoJSON")

print("Selesai. File GeoJSON tersimpan di folder 'data/':")
for f in sorted(os.listdir(OUT_DIR)):
    print(" -", f)
