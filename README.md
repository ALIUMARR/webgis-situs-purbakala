# Peta Interaktif Zonasi Konservasi & Aksesibilitas Wisata Edukasi Situs Purbakala

WebGIS ringan berbasis **Streamlit + Folium** untuk mempublikasikan hasil analisis
spasial delineasi kawasan cagar budaya dari QGIS, tanpa perlu instalasi QGIS di
sisi pengguna akhir.

## Isi Folder

```
webgis_situs_purbakala/
├── app.py                  # Aplikasi Streamlit (WebGIS interaktif)
├── generate_data.py         # Script pembuat data dummy (opsional, sudah dijalankan)
├── requirements.txt
├── README.md
└── data/
    ├── situs_utama.geojson          # Titik candi (Situs Utama)
    ├── zonasi_inti.geojson          # Polygon zonasi inti (merah)
    ├── zonasi_penyangga.geojson     # Polygon buffer zone (oranye/kuning)
    ├── fasilitas_edukasi.geojson    # Titik fasilitas edukasi (hijau)
    ├── pos_pemantauan.geojson       # Titik pos jaga (biru)
    ├── buffer_getaran_500.geojson   # Polygon buffer kerentanan 500 m
    └── buffer_getaran_1000.geojson  # Polygon buffer kerentanan 1000 m
```

> **PENTING:** Data pada folder `data/` saat ini adalah **data contoh (dummy)**
> di sekitar koordinat fiktif "Situs Purbakala Giri Wangun". Ganti dengan data
> asli hasil digitasi/analisis Anda di QGIS (lihat langkah di bawah).

## 1. Menjalankan Secara Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

Buka browser ke `http://localhost:8501`.

## 2. Mengganti Data Dummy dengan Data QGIS Asli

Untuk setiap layer di QGIS:

1. Klik kanan layer di panel Layers → **Export → Save Features As...**
2. Format: **GeoJSON**, CRS: **EPSG:4326 (WGS 84)** (wajib, agar tampil benar di web).
3. Simpan dengan nama file yang sama seperti tabel di atas, ke dalam folder `data/`.
4. Pastikan tabel atribut memiliki minimal kolom `nama` dan `keterangan` agar
   muncul rapi di popup peta.
5. Jalankan ulang `streamlit run app.py`.

Jika struktur/nama kolom atribut Anda berbeda, sesuaikan bagian
`LAYER_CONFIG` dan fungsi `popup_html()` di `app.py`.

## 3. Publikasi ke URL Publik (Gratis, tanpa server sendiri)

**Streamlit Community Cloud:**

1. Buat repository baru di GitHub, unggah seluruh isi folder ini
   (`app.py`, `requirements.txt`, folder `data/`, dst).
2. Buka https://share.streamlit.io → **New app**.
3. Pilih repo, branch, dan file utama `app.py`.
4. Klik **Deploy**. Dalam beberapa menit, Streamlit akan memberi URL publik,
   contoh: `https://situs-purbakala-webgis.streamlit.app`.
5. URL ini bisa dibuka langsung dari HP atau laptop mana pun tanpa instalasi
   QGIS — cukup browser dan koneksi internet.

## 4. Kesesuaian dengan Kriteria Tugas

| Elemen Tugas | Implementasi di `app.py` |
|---|---|
| Situs Utama / Zonasi Inti (merah) | Layer `zonasi_inti` (`fillColor: #FF0000`) |
| Zonasi Penyangga (oranye/kuning) | Layer `zonasi_penyangga` (`fillColor: #FFA500`) |
| Pusat Informasi & Fasilitas Edukasi (hijau) | Layer `fasilitas_edukasi`, marker `color="green"` |
| Pos Pemantauan/Penjaga (biru) | Layer `pos_pemantauan`, marker `color="blue"` |
| Buffer Kerentanan Getaran 500 m & 1 km (transparan gradasi) | Layer `buffer_getaran_500` & `buffer_getaran_1000`, `fillOpacity` 0.22 & 0.12 |
| Akses via browser tanpa QGIS | Deploy ke Streamlit Community Cloud → URL publik |
| Layer control interaktif | Sidebar checkbox per layer + `folium.LayerControl` |
| Popup atribut & tooltip | `folium.GeoJsonPopup` / `folium.Popup` per fitur |
| Basemap alternatif | Pilihan OpenStreetMap / Citra Satelit Esri |

## 5. Pengembangan Lanjutan (Opsional)

- Tambahkan analisis kepadatan pengunjung dengan **PyDeck HeatmapLayer**.
- Tambahkan fitur pengukuran jarak/luas dengan plugin `folium.plugins.MeasureControl`.
- Tambahkan filter waktu kunjungan bila ada data time-series pengunjung.
- Tambahkan unduh laporan PDF ringkasan zonasi langsung dari Streamlit
  (`st.download_button`).
