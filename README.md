# Takara Backend

Takara adalah *backend* API berbasis *async-first* yang dibangun dengan **FastAPI** untuk mengorkestrasi sistem Agen AI Ganda (Siswa & Profesor). Sistem ini dirancang dengan standar *Software Reliability Engineering* (SRE) untuk memastikan latensi rendah, konkurensi tinggi, dan ketahanan data tingkat *Enterprise* (*Zero Data Loss*).

## Fitur Utama

### Sistem Multi-Agen (Dual AI)
* **Student Agent:** Menggunakan model `openai/gpt-oss-20b` via **Groq** untuk respons super cepat. Menggunakan antarmuka *Server-Sent Events* (SSE) untuk mengalirkan (*stream*) teks secara *real-time* ke klien.
* **Professor Agent:** Menggunakan model `openai/gpt-oss-120b`. Memanfaatkan format `json_object` dan `temperature=0.0` murni untuk memberikan evaluasi logis dari sesi obrolan tanpa risiko halusinasi format.

### Ketahanan Tingkat Enterprise (SRE Best Practices)
* **Zero Data Loss Architecture:** Semua transaksi *database* menggunakan sistem antrean.
* **Smart Retry & Exponential Backoff:** Mekanisme pemulihan otomatis saat *database* (Supabase) mengalami *timeout* atau gangguan jaringan.
* **Encrypted SQLite Fallback:** Jika database utama gagal, payload fallback dienkripsi dengan Fernet sebelum ditulis ke SQLite. Fallback dinonaktifkan secara fail-closed bila kunci enkripsi tidak dikonfigurasi.
* **Logical UNION Aggregation:** Saat *database* utama *down*, layanan agregator tetap mampu menyajikan riwayat obrolan secara utuh kepada pengguna dengan menggabungkan data lokal dan *cloud*.
* **Graceful Disconnects:** Proses generasi AI (penggunaan token LPU) akan dihentikan secara otomatis jika klien/pengguna terputus dari koneksi.

### Pemrosesan Suara Asinkronus
* **Speech-to-Text (STT):** Integrasi **Groq Whisper** untuk transkripsi audio nyaris instan.
* **Text-to-Speech (TTS):** Integrasi **Microsoft Edge TTS** menghasilkan *output* `audio/mpeg` *raw stream*, mengeliminasi *overhead* pemrosesan JSON di sisi klien.

## Tech Stack

* **Framework:** FastAPI, Uvicorn, Pydantic
* **AI & LLM:** Groq API (GPT-OSS 20B & 120B, Whisper)
* **Voice:** Microsoft Edge TTS
* **Database:** Supabase (PostgreSQL), SQLite (via `aiosqlite`)
* **Testing:** Pytest, Pytest-Asyncio

## Prasyarat & Instalasi

1. **Clone repository ini:**
   ```bash
   git clone https://github.com/username/takara-backend.git
   cd takara-backend
   ```

2. **Buat Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Di Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Konfigurasi Environment Variables:**
   Salin file `.env.example` menjadi `.env` dan isi kunci API Anda.
   ```bash
   cp .env.example .env
   ```
   Wajib isi `GROQ_API_KEY`, `DATABASE_URL`, `JWT_SECRET`, dan `OTP_PEPPER`.
   Gunakan secret manager pada production; jangan menyalin nilai dari contoh atau Git history.
   Isi `FALLBACK_ENCRYPTION_KEY` jika encrypted SQLite fallback digunakan.

## Menjalankan Server

Gunakan Uvicorn untuk menjalankan aplikasi dalam mode *development*:

```bash
uvicorn main:app --reload
```

Aplikasi akan berjalan di `http://localhost:8000`.
Swagger, ReDoc, dan OpenAPI schema dinonaktifkan. Aktifkan hanya pada environment development yang terisolasi bila benar-benar diperlukan.

## Menjalankan Pengujian (Chaos Engineering)

Proyek ini dilengkapi dengan skenario *Chaos Testing* untuk memvalidasi ketahanan sistem (SRE Fallback) saat *database* Supabase mati total.

Pastikan file `pytest.ini` sudah tersedia di *root directory*, lalu jalankan:

```bash
pytest tests/ -v -s
```

Jika berhasil, Anda akan melihat log asinkronus yang menunjukkan proses percobaan ulang (*retry*) dan penyelamatan data asinkronus (*fallback*) ke SQLite.

## Deploy ke Render

1. Push direktori `takara-backend` sebagai repository tersendiri (mis. `takara-be`).
2. Di Render: **New → Blueprint Instance**, pilih repo tersebut. Render membaca `render.yaml` (build: `pip install -r requirements.txt`, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check `/api/v1/health`).
3. Isi variabel bertanda `sync: false` saat instance dibuat: `GROQ_API_KEY`, `DATABASE_URL`, `JWT_SECRET`, `OTP_PEPPER`, `FALLBACK_ENCRYPTION_KEY`, dan `CORS_ORIGINS` (isi dengan domain Vercel frontend setelah deploy pertama).
4. Variabel opsional (`REDIS_URL`, `SMTP_*`, `RESEND_API_KEY`, `BREVO_API_KEY`, `TRUSTED_PROXY_IPS`) ditambahkan lewat dashboard bila dipakai. Tanpa `REDIS_URL`, rate-limit dan turn-guard memakai fallback in-memory — valid untuk satu instance.
5. Verifikasi: `curl https://<service>.onrender.com/api/v1/health` mengembalikan `{"status":"healthy",...}`.

Alternatif monorepo: jika seluruh folder `takara/` berada dalam satu repo, jangan pakai Blueprint — buat **Web Service** manual dengan *Root Directory* `takara-backend` serta build/start command yang sama seperti di atas.

## Struktur Direktori Utama

```text
├── app/
│   ├── agents/          # Logika spesifik AI (Student & Professor)
│   ├── api/v1/          # Endpoints & Routers (Session, Voice, Health)
│   ├── core/            # Konfigurasi Pydantic & Sistem
│   ├── integrations/    # Klien eksternal (Groq, Edge TTS, Supabase)
│   ├── schemas/         # Validasi Input/Output Pydantic
│   └── services/        # Logika Bisnis & Transaksi Database (SRE Layer)
├── tests/               # Unit testing & Chaos testing
├── main.py              # Entry point FastAPI & Lifespan events
├── pytest.ini           # Konfigurasi Pytest
└── requirements.txt     # Daftar dependensi library
```
