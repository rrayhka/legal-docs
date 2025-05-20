### 🗂️ Struktur dan Alur Folder Proses Ekstraksi

1. **PDF**

   - File asli dengan format `{kode_unik}.pdf`.
   - Disimpan di: `pdf_input/`

2. **Analysis**

   - Hasil awal konversi dari PDF ke teks (`txt`) untuk dianalisis.
   - Format nama: `analysis {kode_unik}.txt`
   - Disimpan di: `analysis/`

3. **Raw**

   - Hasil ekstraksi teks dari tahap `analysis/`, diproses lebih lanjut.
   - Format nama: `row {kode_unik}.txt`
   - Disimpan di: `raw/`

4. **Current Final Output**

   - Hasil akhir dari proses ekstraksi yang dilakukan secara otomatis, masih terdapat kesalahan.
   - Format nama: `final {kode_unik}.txt`
   - Disimpan di: `current_final_output/`

5. **Expected Final Output**

   - Berisi hasil ekstraksi akhir yang **benar** sesuai harapan (ground truth).
   - Disimpan `expected_final_output/`

---

### 🔁 Alur Singkat Proses

```
PDF ➜ Analysis ➜ Raw ➜ Current Final Output ➜ (bandingkan) ➜ Expected Final Output
```
