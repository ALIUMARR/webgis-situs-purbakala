"""
Peta Interaktif Zonasi Konservasi dan Aksesibilitas Wisata Edukasi Situs Purbakala
Dibangun dengan Streamlit + Folium.

Cara jalankan (lokal):
    pip install -r requirements.txt
    streamlit run app.py

Cara publikasi publik (gratis):
    1. Push folder ini ke sebuah repo GitHub.
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

# -----------------------------------------------------------------------
# Styling global: seluruh font memakai Times New Roman, dan judul/heading
# (st.title, st.header, st.subheader, markdown ###) berwarna hitam.
# -----------------------------------------------------------------------
st.markdown(
    """
    <style>
    html, body, [class^="css"], [class*=" css"],
    .stApp, .stMarkdown, .stMarkdown p, .stMarkdown li,
    .stText, .stCaption, .stMetric, .stTable, .stDataFrame,
    p, div, span, label, li, td, th, input, textarea, select {
        font-family: "Times New Roman", Times, serif !important;
    }
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "webgis_situs_purbakala", "data")

# -----------------------------------------------------------------------
# Konfigurasi styling tiap layer (warna & simbol) sesuai arahan tugas
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
        "color": "darkred",
        "icon": "star",
        "default_on": True,
    },
}


@st.cache_data
def load_geojson(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def popup_html(props):
    rows = "".join(
        f"<b>{k.replace('_', ' ').title()}</b>: {v}<br>"
        for k, v in props.items()
        if k != "geometry"
    )
    html = f"<div style='font-family: \"Times New Roman\", Times, serif;'>{rows}</div>"
    return folium.Popup(html, max_width=280)


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


def collect_periods():
    periods = set()
    for cfg in LAYER_CONFIG.values():
        gj = load_geojson(cfg["file"])
        for feat in gj["features"]:
            period = feat["properties"].get("periode")
            if period:
                periods.add(str(period))
    return sorted(periods)


def build_map(active_layers, basemap, search_query="", selected_period="Semua Periode"):
    m = folium.Map(
        location=[-7.60800, 110.20400],
        zoom_start=16,
        tiles=None,
        control_scale=True,
    )

    basemaps = {
        "OpenStreetMap": "OpenStreetMap",
        "Citra Satelit (Esri)": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
    }
    if basemap == "OpenStreetMap":
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    else:
        folium.TileLayer(
            tiles=basemaps["Citra Satelit (Esri)"],
            attr="Esri World Imagery",
            name="Citra Satelit (Esri)",
        ).add_to(m)

    for key, cfg in LAYER_CONFIG.items():
        if key not in active_layers:
            continue
        gj = load_geojson(cfg["file"])

        if cfg["type"] == "polygon":
            fg = folium.FeatureGroup(name=cfg["label"])
            for feat in gj["features"]:
                props = feat["properties"]
                if not feature_matches_filter(props, search_query, selected_period):
                    continue
                html_popup = "<div style='font-family: \"Times New Roman\", Times, serif; width: 200px;'>"
                for k, v in props.items():
                    html_popup += f"<b>{k.replace('_', ' ').title()}</b>: {v}<br>"
                html_popup += "</div>"
                folium.GeoJson(
                    feat,
                    style_function=lambda x, s=cfg["style"]: s,
                    highlight_function=lambda x: {"weight": 3, "fillOpacity": 0.6},
                    popup=folium.Popup(html_popup, max_width=280),
                ).add_to(fg)
            fg.add_to(m)
        else:  # point
            fg = folium.FeatureGroup(name=cfg["label"])
            for feat in gj["features"]:
                props = feat["properties"]
                if not feature_matches_filter(props, search_query, selected_period):
                    continue
                lon, lat = feat["geometry"]["coordinates"]
                folium.Marker(
                    location=[lat, lon],
                    popup=popup_html(props),
                    tooltip=props.get("nama", ""),
                    icon=folium.Icon(color=cfg["color"], icon=cfg["icon"]),
                ).add_to(fg)
            fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ------------------------------- UI -------------------------------------
st.title("🏛️ Peta Interaktif Zonasi Konservasi & Aksesibilitas Wisata Edukasi Situs Purbakala")
st.caption(
    "Data pada peta ini adalah **data contoh (dummy)** untuk keperluan tugas. "
    "Ganti file di folder `data/` dengan hasil ekspor GeoJSON dari analisis QGIS Anda."
)

with st.sidebar:
    st.header("⚙️ Pengaturan Peta")
    basemap = st.radio("Basemap", ["OpenStreetMap", "Citra Satelit (Esri)"])

    st.subheader("Filter Periode Historis")
    search_query = st.text_input("Cari tempat / kata kunci", "")
    available_periods = ["Semua Periode"] + collect_periods()
    selected_period = st.selectbox("Periode Historis", available_periods, index=0)

    st.subheader("Layer aktif")
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
        "- 🟢 Fasilitas Edukasi & Informasi\n"
        "- 🔵 Pos Pemantauan/Penjaga\n"
        "- Gradasi kuning→oranye transparan — buffer kerentanan getaran 500 m & 1000 m"
    )

col1, col2 = st.columns([3, 1])

with col1:
    m = build_map(active_layers, basemap, search_query=search_query, selected_period=selected_period)
    st_folium(m, width=None, height=650, returned_objects=[])

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
    st.info(
        "Klik salah satu simbol/poligon pada peta untuk melihat detail atribut "
        "(nama, kategori, dan keterangan)."
    )

st.markdown("---")
st.subheader("📌 Ringkasan Eksekutif")
st.markdown(
    "Data peta ini menunjukkan zonasi konservasi, wilayah buffer getaran, fasilitas edukasi, dan pos pemantauan untuk mendukung pengelolaan situs purbakala secara berkelanjutan. "
    "Analisis menekankan perlunya pembatasan aktivitas pada zona inti, pengaturan wisata edukasi di zona penyangga, dan pemantauan getaran di radius 500 m dan 1000 m."
)

st.subheader("📊 Data Pendukung Analisis")
st.table(
    [
        {"Data": "Zonasi Inti", "Sumber": "Analisis QGIS - delimitasi konservasi", "Keterangan": "Area tingkat perlindungan tertinggi"},
        {"Data": "Zonasi Penyangga", "Sumber": "Analisis QGIS - buffer zone", "Keterangan": "Zona pembatas aktivitas sekitar situs"},
        {"Data": "Buffer Getaran 500 m", "Sumber": "Analisis dampak getaran", "Keterangan": "Area rentan terhadap getaran dari kegiatan sekitar"},
        {"Data": "Buffer Getaran 1000 m", "Sumber": "Analisis dampak getaran", "Keterangan": "Zona pemantauan tambahan untuk mitigasi"},
        {"Data": "Fasilitas Edukasi", "Sumber": "Inventarisasi lapangan", "Keterangan": "Pusat informasi dan edukasi pengunjung"},
        {"Data": "Pos Pemantauan", "Sumber": "Inventarisasi lapangan", "Keterangan": "Titik pengawasan dan penjagaan situs"},
    ]
)

st.subheader("🎨 Simbolisasi Warna")
st.table(
    [
        {"Simbol": "🔴", "Makna": "Zonasi Inti - konservasi ketat"},
        {"Simbol": "🟧", "Makna": "Zonasi Penyangga - aktivitas terbatas"},
        {"Simbol": "🟡", "Makna": "Buffer Getaran 1000 m - kewaspadaan moderat"},
        {"Simbol": "🟠", "Makna": "Buffer Getaran 500 m - kewaspadaan tinggi"},
        {"Simbol": "🟢", "Makna": "Fasilitas Edukasi - titik informasi"},
        {"Simbol": "🔵", "Makna": "Pos Pemantauan - titik penjagaan"},
        {"Simbol": "🏛️", "Makna": "Situs Utama - titik candi"},
    ]
)

st.subheader("✨ Fitur Interaktif")
st.markdown(
    "- Pilih layer yang ingin ditampilkan di sidebar untuk fokus pada tema tertentu.\n"
    "- Ganti basemap antara OpenStreetMap dan Citra Satelit untuk perbandingan visual.\n"
    "- Klik poligon atau marker untuk melihat informasi atribut setiap fitur.\n"
)

st.subheader("📚 Data Referensi")
st.markdown(
    "- Data spasial dihasilkan dari analisis QGIS dan diekspor ke format GeoJSON.\n"
    "- Peta ini menggunakan Folium untuk visualisasi dan Streamlit untuk antarmuka web.\n"
    "- Referensi metodologi: tata ruang konservasi cagar budaya, pedoman mitigasi getaran, dan prinsip wisata edukasi berkelanjutan."
)

st.caption(
    "Sumber: Analisis spasial delineasi kawasan cagar budaya (diekspor dari QGIS ke GeoJSON). "
    "Dipublikasikan sebagai WebGIS ringan menggunakan Streamlit + Folium."
)


def _is_streamlit_runtime_active() -> bool:
    try:
        import streamlit.runtime as runtime
        return runtime.exists()
    except Exception:
        return False


if __name__ == "__main__" and not _is_streamlit_runtime_active():
    import subprocess
    import sys

    subprocess.Popen([sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__)])
    sys.exit(0)
