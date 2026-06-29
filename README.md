# Product Requirements Document (PRD)
**OS Sim: Preemptive Video Encoder**

---

## 1. Ikhtisar Produk (Product Overview)
* **Nama Produk:** OS Sim: Preemptive Video Encoder
* **Deskripsi:** Aplikasi web berbasis simulasi yang memvisualisasikan cara kerja algoritma penjadwalan CPU *Shortest Job First (SJF) Preemptive* dengan mekanisme *Aging*.
* **Tujuan Utama:** Menerjemahkan konsep Sistem Operasi yang abstrak (seperti *Context Switch*, *Starvation*, dan antrean *Process Control Block*) ke dalam skenario dunia nyata (*video encoding*), sehingga lebih mudah dievaluasi oleh dosen dan dipahami oleh mahasiswa.

## 2. Target Pengguna
1. **Dosen / Evaluator**
   * **Kebutuhan:** Akurasi logis algoritma, transparansi proses, dan pembuktian konsep OS.
   * **Kriteria Sukses:** Log terminal mencetak peristiwa *Context Switch* dan *Aging* secara akurat tanpa indikasi *bug* pada antrean.
2. **Rekan Mahasiswa**
   * **Kebutuhan:** Antarmuka yang tidak membosankan dan visualisasi sistem yang mudah dipahami secara visual.
   * **Kriteria Sukses:** Antarmuka *dark mode* modern dengan pembaruan *real-time* tanpa perlu melakukan *refresh* halaman secara manual.

## 3. Kebutuhan Fungsional (Functional Requirements)
Aplikasi harus memenuhi fungsi inti berikut:
* **Modul Input Job:** Pengguna dapat memasukkan nama file video dan *Burst Time* (estimasi waktu *render*). Sistem otomatis mencatat *Arrival Time* (waktu kedatangan) berdasarkan *clock* sistem.
* **Mesin Penjadwalan (Scheduler Engine):**
  * **Preemption:** Sistem mengevaluasi antrean setiap detik. Jika ada video baru dengan sisa waktu lebih kecil dari video yang sedang berjalan, proses saat ini di-*pause* (*Context Switch*).
  * **Aging Mechanism:** Sistem menaikkan prioritas (mengurangi nilai virtual sisa waktu) dari video yang terus menunggu untuk mencegah *Starvation*.
  * **Formula:** `Prioritas = Waktu_Sisa - (Waktu_Tunggu * Faktor_Aging)`
* **Live Dashboard (Visualisasi):**
  * Menampilkan *Global Clock* (waktu simulasi).
  * Tabel *Ready Queue* yang diperbarui setiap detik.
* **Terminal Log Event:** Mencetak rekam jejak sistem (kapan sebuah proses masuk, di-*preempt*, di-*resume*, dan selesai).

## 4. Kebutuhan Non-Fungsional (Non-Functional Requirements)
* **Arsitektur Asinkron:** Logika *clock tick* OS harus berjalan di *background thread* agar tidak membuat *server* web *freeze*.
* **Pembaruan Klien Real-time:** Antarmuka mengambil *state* sistem (polling JSON) setiap 1 detik menggunakan JavaScript *Fetch API*.
* **Tech Stack:**
  * **Backend:** Python 3.x, Flask.
  * **Frontend:** HTML5, CSS3 (Custom Dark Mode), Vanilla JavaScript ES6.

## 5. Alur Pengguna (Demonstration User Flow)
1. **Inisialisasi:** Server Flask memulai *thread* jam OS pada hitungan 00:00.
2. **Input Job Besar:** Pengguna memasukkan "Video_A" (Burst Time 30s). Video_A berjalan.
3. **Memicu Preemption:** Pada detik ke-5, pengguna memasukkan "Video_B" (Burst Time 10s). Terminal mencetak *Context Switch*. Video_B mengambil alih CPU, Video_A masuk antrean menunggu.
4. **Memicu Starvation & Aging:** Pengguna terus memasukkan video berdurasi pendek. Video_A tertahan lama, prioritas virtualnya meningkat akibat *Aging*.
5. **Resolusi:** *Aging* memaksa Video_A kembali berjalan meskipun ada video yang durasi aslinya lebih pendek, mencegah *Starvation* permanen.

## 6. Struktur Data Inti (Process Control Block)
Atribut yang disimpan dalam RAM untuk setiap *Job*:
* `PID`: ID unik (Misal: VID-1)
* `Arrival Time`: Waktu *submit*
* `Burst Time`: Waktu asli eksekusi
* `Remaining Time`: Sisa waktu eksekusi aktual
* `Waiting Time`: Total waktu di *Ready Queue*
* `Turnaround Time`: `Waktu_Selesai - Arrival_Time`
* `Aging Factor`: Nilai pengurang virtual berbasis lama menunggu