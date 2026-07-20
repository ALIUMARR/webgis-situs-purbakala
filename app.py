"""
Peta Interaktif Zonasi Konservasi dan Aksesibilitas Wisata Edukasi Situs Purbakala
Dibangun dengan Streamlit + Folium.

Cara jalankan (lokal):
    pip install -r requirements.txt
    streamlit run app.py

Cara publikasi publik (gratis):
    1. Push seluruh isi folder ini (app.py, requirements.txt, data/) ke repo GitHub.
    2. Buka https://share.streamlit.io -> New app -> pilih repo -> pilih app.py.
    3. Streamlit Community Cloud akan memberi URL publik (contoh:
       https://nama-app.streamlit.app) yang bisa dibuka dari HP/Laptop
       tanpa instalasi QGIS.
"""

import json
import os

import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="WebGIS Zonasi Konservasi Situs Purbakala",
    page_icon="🏛️",
    layout="wide",
)

# app.py dan folder data/ berada tepat sejajar di dalam folder proyek yang sama
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# -----------------------------------------------------------------------
# 1. STYLING & SIMBOLISASI -- sesuai poin 2a-2e instruksi tugas
# -----------------------------------------------------------------------
LAYER_CONFIG = {
    "zonasi_inti": {
        "file": "zonasi_inti.geojson",
        "label": "🔴 Zonasi Inti Candi (Konservasi Ketat)",
        "type": "polygon",
        "style": {"color": "#B22222", "weight": 2, "fillColor": "#FF0000", "fillOpacity": 0.45},
        "default_on": True,
    },
    "zonasi_penyangga": {
        "file": "zonasi_penyangga.geojson",
        "label": "🟧 Zonasi Penyangga (Buffer Zone - Aktivitas Terbatas)",
        "type": "polygon",
        "style": {"color": "#E67E22", "weight": 2, "fillColor": "#FFA500", "fillOpacity": 0.35},
        "default_on": True,
    },
    "buffer_getaran_1000": {
        "file": "buffer_getaran_1000.geojson",
        "label": "🟡 Buffer Kerentanan Getaran 1000 m",
        "type": "polygon",
        "style": {"color": "#F1C40F", "weight": 1, "fillColor": "#F4D03F", "fillOpacity": 0.12},
        "default_on": True,
    },
    "buffer_getaran_500": {
        "file": "buffer_getaran_500.geojson",
        "label": "🟠 Buffer Kerentanan Getaran 500 m",
        "type": "polygon",
        "style": {"color": "#E74C3C", "weight": 1, "fillColor": "#F5B041", "fillOpacity": 0.22},
        "default_on": True,
    },
    "fasilitas_edukasi": {
        "file": "fasilitas_edukasi.geojson",
        "label": "🟢 Pusat Informasi & Fasilitas Edukasi",
        "type": "point",
        "color": "green",
        "icon": "info-sign",
        "default_on": True,
    },
    "pos_pemantauan": {
        "file": "pos_pemantauan.geojson",
        "label": "🔵 Pos Pemantauan / Penjaga Situs",
        "type": "point",
        "color": "blue",
        "icon": "eye-open",
        "default_on": True,
    },
    "situs_utama": {
        "file": "situs_utama.geojson",
        "label": "🏛️ Titik Candi (Situs Utama)",
        "type": "point",
        "color": "red",
        "icon": "star",
        "default_on": True,
    },
}

# Label atribut yang ditampilkan di pop-up per layer (urut sesuai instruksi tugas)
POPUP_FIELDS = {
    "situs_utama": [
        ("nama", "Nama Candi"),
        ("abad_pembuatan", "Abad Pembuatan"),
        ("kerajaan_dinasti_pendiri", "Kerajaan / Dinasti Pendiri"),
        ("status_konservasi", "Status Konservasi"),
        ("tingkat_risiko_kerusakan", "Tingkat Risiko Kerusakan"),
    ],
    "fasilitas_edukasi": [
        ("nama", "Nama Fasilitas"),
        ("kapasitas_pengunjung_harian", "Kapasitas Pengunjung Harian"),
        ("jenis_layanan_informasi", "Jenis Layanan Informasi"),
    ],
    "pos_pemantauan": [
        ("nama", "Nama Pos"),
        ("petugas_per_shift", "Petugas per Shift"),
        ("keterangan", "Keterangan"),
    ],
}
DEFAULT_POPUP_FIELDS = [("nama", "Nama"), ("kategori", "Kategori"), ("keterangan", "Keterangan")]


@st.cache_data
def load_geojson(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_popup_html(layer_key, props):
    fields = POPUP_FIELDS.get(layer_key, DEFAULT_POPUP_FIELDS)
    rows = "".join(
        f"<b>{label}</b>: {props.get(key, '-')}<br>"
        for key, label in fields
        if key in props
    )
    if not rows:
        rows = "<i>Tidak ada atribut tambahan.</i>"
    return f"<div style='font-family: Arial; font-size: 13px; width: 220px;'>{rows}</div>"


def normalize_text(value):
    return str(value).lower().strip() if value is not None else ""


def feature_matches_filter(props, search_query: str, selected_period: str) -> bool:
    if selected_period and selected_period != "Semua Periode":
        if normalize_text(props.get("periode", "")) != normalize_text(selected_period):
            return False
    if search_query:
        haystack = " ".join(
            normalize_text(props.get(key, ""))
            for key in ("nama", "kategori", "keterangan", "periode")
        )
        return normalize_text(search_query) in haystack
    return True


@st.cache_data
def collect_periods():
    periods = set()
    for cfg in LAYER_CONFIG.values():
        gj = load_geojson(cfg["file"])
        for feat in gj["features"]:
            period = feat["properties"].get("periode")
            if period:
                periods.add(str(period))
    return sorted(periods)


# -----------------------------------------------------------------------
# 2. INTERAKTIVITAS -- pop-up atribut, layer control, filter dinamis
# -----------------------------------------------------------------------
def build_map(active_layers, basemap, search_query="", selected_period="Semua Periode"):
    m = folium.Map(
        location=[-7.60800, 110.20400],
        zoom_start=16,
        tiles=None,
        control_scale=True,  # menampilkan skala di pojok peta
    )

    if basemap == "OpenStreetMap":
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    else:
        folium.TileLayer(
            tiles=(
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ),
            attr="Esri World Imagery",
            name="Citra Satelit (Esri)",
        ).add_to(m)

    any_feature_shown = False

    for key, cfg in LAYER_CONFIG.items():
        if key not in active_layers:
            continue
        gj = load_geojson(cfg["file"])
        fg = folium.FeatureGroup(name=cfg["label"])

        if cfg["type"] == "polygon":
            for feat in gj["features"]:
                props = feat["properties"]
                if not feature_matches_filter(props, search_query, selected_period):
                    continue
                any_feature_shown = True
                folium.GeoJson(
                    feat,
                    style_function=lambda x, s=cfg["style"]: s,
                    highlight_function=lambda x: {"weight": 3, "fillOpacity": 0.6},
                    popup=folium.Popup(build_popup_html(key, props), max_width=280),
                    tooltip=props.get("nama", ""),
                ).add_to(fg)
        else:  # point
            for feat in gj["features"]:
                props = feat["properties"]
                if not feature_matches_filter(props, search_query, selected_period):
                    continue
                any_feature_shown = True
                lon, lat = feat["geometry"]["coordinates"]
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(build_popup_html(key, props), max_width=280),
                    tooltip=props.get("nama", ""),
                    icon=folium.Icon(color=cfg["color"], icon=cfg["icon"]),
                ).add_to(fg)

        fg.add_to(m)

    # Layer Control di pojok kanan atas peta (checkbox show/hide tiap layer)
    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    return m, any_feature_shown


# ------------------------------- UI -------------------------------------
st.title("🏛️ Peta Interaktif Zonasi Konservasi & Aksesibilitas Wisata Edukasi Situs Purbakala")
st.caption(
    "Data pada peta ini adalah **data contoh (dummy)** untuk keperluan tugas. "
    "Ganti file di folder `data/` dengan hasil ekspor GeoJSON dari analisis QGIS Anda "
    "(pertahankan nama kolom atribut agar pop-up & filter tetap berfungsi)."
)

with st.sidebar:
    st.header("⚙️ Pengaturan Peta")
    basemap = st.radio("Basemap", ["OpenStreetMap", "Citra Satelit (Esri)"])

    st.subheader("🔎 Filter Dinamis")
    search_query = st.text_input("Cari nama / kategori / keterangan", "")
    available_periods = ["Semua Periode"] + collect_periods()
    selected_period = st.selectbox(
        "Filter Periodisasi Situs (Hindu / Buddha / Megalitikum)",
        available_periods,
        index=0,
    )

    st.subheader("🗂️ Layer Control")
    active_layers = []
    for key, cfg in LAYER_CONFIG.items():
        checked = st.checkbox(cfg["label"], value=cfg["default_on"], key=f"chk_{key}")
        if checked:
            active_layers.append(key)

    st.divider()
    st.markdown(
        "**Legenda Simbolisasi**\n"
        "- 🔴 Zonasi Inti Candi — konservasi ketat\n"
        "- 🟧 Zonasi Penyangga — aktivitas terbatas\n"
        "- 🟡🟠 Buffer Kerentanan Getaran 500 m & 1000 m — gradasi transparansi\n"
        "- 🟢 Pusat Informasi & Fasilitas Edukasi\n"
        "- 🔵 Pos Pemantauan / Penjaga Situs"
    )

col1, col2 = st.columns([3, 1])

with col1:
    m, ada_hasil = build_map(active_layers, basemap, search_query, selected_period)
    st_folium(m, width=None, height=650, returned_objects=[])
    if not ada_hasil and active_layers:
        st.warning("Tidak ada fitur yang cocok dengan filter/pencarian saat ini.")

with col2:
    st.subheader("📊 Ringkasan Zonasi")
    st.metric("Jumlah Layer Aktif", len(active_layers))
    st.markdown(
        """
        **Rekomendasi Mitigasi**
        - Zonasi inti: larangan kendaraan bermotor & pembatasan jumlah pengunjung per jam.
        - Zonasi penyangga: wisata edukasi terpandu, tanpa fasilitas permanen baru.
        - Radius 500 m: larangan konstruksi/alat berat tanpa kajian getaran.
        - Radius 1000 m: pemantauan berkala getaran & retakan struktur.
        """
    )
    st.info("Klik simbol atau poligon pada peta untuk melihat pop-up atribut detail.")

# -----------------------------------------------------------------------
# 3. KONTEKS & RINGKASAN EKSEKUTIF
# -----------------------------------------------------------------------
st.markdown("---")
st.subheader("📌 Ringkasan Eksekutif")
st.markdown(
    "Analisis spasial menunjukkan bahwa **zonasi inti Candi Giri Wangun tergolong stabil** "
    "karena berada dalam pengawasan langsung pos jaga dan pembatasan akses kendaraan. "
    "Namun, temuan utama analisis delineasi kawasan cagar budaya mengindikasikan adanya "
    "**ancaman ekspansi permukiman di sekitar batas luar zonasi penyangga (buffer zone)**, "
    "yang berpotensi mempersempit ruang penyangga fungsional candi dan meningkatkan beban "
    "getaran serta lalu lintas kendaraan warga pada radius 500 m–1000 m dari struktur candi. "
    "Jika tidak dikendalikan melalui regulasi tata ruang, tren ini dapat mempercepat "
    "degradasi struktur candi dan mengurangi efektivitas zona penyangga sebagai penyangga "
    "risiko fisik maupun sosial. Rekomendasi prioritas: penegakan IMB/tata ruang di kawasan "
    "penyangga, moratorium alih fungsi lahan pertanian menjadi permukiman baru dalam radius "
    "1 km, serta pelibatan masyarakat sekitar dalam program wisata edukasi agar tekanan "
    "ekspansi permukiman dapat dialihkan menjadi nilai ekonomi dari pelestarian situs."
)

st.subheader("📊 Tabel Data Pendukung Analisis")
st.table(
    [
        {"Layer": "Zonasi Inti", "Sumber Data": "Analisis QGIS - delineasi konservasi", "Jumlah Fitur": 1, "Keterangan": "Area tingkat perlindungan tertinggi"},
        {"Layer": "Zonasi Penyangga", "Sumber Data": "Analisis QGIS - buffer zone", "Jumlah Fitur": 1, "Keterangan": "Zona pembatas aktivitas, rawan tekanan ekspansi permukiman"},
        {"Layer": "Buffer Getaran 500 m", "Sumber Data": "Analisis dampak getaran", "Jumlah Fitur": 1, "Keterangan": "Area rentan getaran tinggi"},
        {"Layer": "Buffer Getaran 1000 m", "Sumber Data": "Analisis dampak getaran", "Jumlah Fitur": 1, "Keterangan": "Zona pemantauan getaran sedang"},
        {"Layer": "Fasilitas Edukasi", "Sumber Data": "Inventarisasi lapangan", "Jumlah Fitur": 3, "Keterangan": "Pusat informasi, museum, gedung edukasi"},
        {"Layer": "Pos Pemantauan", "Sumber Data": "Inventarisasi lapangan", "Jumlah Fitur": 4, "Keterangan": "Titik pengawasan & penjagaan situs"},
    ]
)

st.subheader("🎨 Simbolisasi Warna")
st.table(
    [
        {"Simbol": "🔴", "Layer": "Zonasi Inti Candi", "Makna": "Konservasi ketat"},
        {"Simbol": "🟧", "Layer": "Zonasi Penyangga", "Makna": "Aktivitas terbatas"},
        {"Simbol": "🟠", "Layer": "Buffer Getaran 500 m", "Makna": "Kewaspadaan tinggi"},
        {"Simbol": "🟡", "Layer": "Buffer Getaran 1000 m", "Makna": "Kewaspadaan sedang"},
        {"Simbol": "🟢", "Layer": "Fasilitas Edukasi", "Makna": "Titik informasi/edukasi"},
        {"Simbol": "🔵", "Layer": "Pos Pemantauan", "Makna": "Titik penjagaan"},
    ]
)

st.subheader("✨ Fitur Interaktif")
st.markdown(
    "- **Pop-up atribut**: klik candi untuk melihat Abad Pembuatan, Kerajaan/Dinasti Pendiri, "
    "Status Konservasi, dan Tingkat Risiko Kerusakan; klik fasilitas untuk melihat Kapasitas "
    "Pengunjung Harian dan Jenis Layanan Informasi.\n"
    "- **Layer Control**: checkbox di sidebar & pojok kanan atas peta untuk menampilkan/"
    "menyembunyikan tiap layer (mis. matikan *Buffer Kerentanan Getaran* untuk fokus ke fasilitas wisata).\n"
    "- **Filter Periodisasi**: dropdown untuk menyaring situs berdasarkan periode (Hindu/Buddha/Megalitikum).\n"
    "- **Pencarian**: kotak teks untuk mencari fitur berdasarkan nama/kategori/keterangan.\n"
    "- **Ganti Basemap**: OpenStreetMap ↔ Citra Satelit Esri.\n"
    "- **Skala peta**: otomatis tampil di pojok kiri bawah (`control_scale`)."
)

st.subheader("📚 Data Referensi")
st.markdown(
    "- Data spasial dihasilkan dari analisis QGIS (delineasi kawasan cagar budaya & pemetaan "
    "konflik pemanfaatan lahan), diekspor ke format GeoJSON (EPSG:4326).\n"
    "- Visualisasi peta: Folium (Leaflet.js) dan antarmuka web: Streamlit.\n"
    "- Rujukan kebijakan: UU No. 11 Tahun 2010 tentang Cagar Budaya (zonasi inti & penyangga), "
    "pedoman mitigasi getaran struktur bangunan cagar budaya, dan prinsip wisata edukasi "
    "berkelanjutan (sustainable heritage tourism)."
)

st.caption(
    "Sumber: Analisis spasial delineasi kawasan cagar budaya (diekspor dari QGIS ke GeoJSON). "
    "Dipublikasikan sebagai WebGIS ringan menggunakan Streamlit + Folium."
)
