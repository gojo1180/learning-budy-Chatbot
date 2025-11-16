from fastapi import APIRouter
from schemas.chat import ProgressRequest, ProgressResponse
from services.gemini import call_gemini_api
from services.supabase import call_supabase_api
import json

# Buat router khusus untuk endpoint 'progress'
router = APIRouter(prefix="/progress", tags=["Progres Siswa"])

# Catatan: path di sini adalah "/", karena prefix "/progress"
# sudah ditambahkan di api/router.py
@router.post("/", response_model=ProgressResponse)
async def handle_progress(request: ProgressRequest):
    """
    FITUR 3: Mengecek progres belajar pengguna.
    Mengambil data dari Mock Server berdasarkan email.
    """
    
    # 1. Panggil Supabase (Mock Server) untuk mendapatkan data progres
    #    berdasarkan file 'Student Progress.csv' Anda.
    data_progres_list = await call_supabase_api(
        "Student Progress",  # <-- Nama tabel dari CSV Anda (dikonfirmasi oleh screenshot Anda)
        db_type="mock",      # <-- PENTING: Kita panggil MOCK API Anda
        params={
            "email": f"eq.{request.email}",
            "select": "*"                  
        }
    )
    
    if not data_progres_list:
        # Jika Supabase mengembalikan list kosong []
        return ProgressResponse(bot_response=f"Maaf, saya tidak dapat menemukan data progres untuk email {request.email}. Pastikan emailnya ada di database mock Anda.")

    # 2. Ubah data list (JSON) menjadi string agar bisa dimasukkan ke prompt
    data_progres_str = json.dumps(data_progres_list)
    
    # 3. Buat prompt untuk Gemini
    prompt = f"""
    Anda adalah seorang mentor yang ramah dan suportif.
    Ini adalah data progres seorang siswa dalam format JSON (dia mungkin mengambil beberapa kursus):
    {data_progres_str}
    
    Tugas Anda (dalam Bahasa Indonesia):
    1. Analisis data tersebut. 'name' adalah nama siswa.
    2. 'completed_tutorials' adalah jumlah selesai, 'active_tutorials' adalah jumlah total modul.
    3. Hitung persentase progres untuk setiap kursus: (completed_tutorials / active_tutorials) * 100.
    4. Berikan ringkasan progres yang ramah dan memotivasi. Jika ada lebih dari satu kursus, sebutkan semuanya.
    5. Jika 'is_graduated' = 1, berikan selamat. Jika 'exam_score' ada (dan tidak null), sebutkan nilainya.
    6. Jawabannya harus dalam bentuk paragraf yang natural.
    
    Contoh Jawaban (jika 1 kursus, 50%):
    "Semangat terus, Rafi! Progresmu di 'Belajar Fundamental Aplikasi Android' sudah 51.4% (55 dari 107 modul). Sudah setengah jalan, lanjutkan!"
    
    Contoh Jawaban (jika 1 kursus, lulus):
    "Kerja bagus, Sari! Di kelas 'Belajar Fundamental Aplikasi Android', kamu sudah menyelesaikan 100% materi (214 dari 214 modul) dan lulus dengan nilai ujian 100! Luar biasa!"
    """
    
    # 4. Panggil Gemini untuk merangkum data
    jawaban_ai = await call_gemini_api(prompt)
    
    return ProgressResponse(bot_response=jawaban_ai)