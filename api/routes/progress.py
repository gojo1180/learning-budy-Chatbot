from fastapi import APIRouter, Depends
from schemas.chat import ProgressResponse
from services.gemini import call_gemini_api
from services.supabase import call_supabase_api
from api.deps import get_current_user_email # Import Satpam
import json

router = APIRouter(prefix="/progress", tags=["Progres Siswa"])

# Hapus parameter request body, ganti dengan Dependency Injection
@router.post("/", response_model=ProgressResponse)
async def handle_progress(current_email: str = Depends(get_current_user_email)):
    """
    FITUR 3: Mengecek progres belajar pengguna.
    Mengambil data berdasarkan EMAIL DARI TOKEN LOGIN (Otomatis).
    """
    
    print(f"[DEBUG] User request progres untuk email: {current_email}")

    # Gunakan email dari token untuk cari data
    data_progres_list = await call_supabase_api(
        "Student Progress", 
        db_type="mock",      
        params={
            "email": f"eq.{current_email}", # Filter pakai email token
            "select": "*"                  
        }
    )
    
    if not data_progres_list:
        return ProgressResponse(bot_response=f"Halo! Saya melihat Anda login sebagai {current_email}, namun saya tidak menemukan data progres untuk email tersebut di database nilai. Pastikan email akun Anda sesuai dengan data sekolah.")
    
    data_progres_str = json.dumps(data_progres_list)
    
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
    
    jawaban_ai = await call_gemini_api(prompt)
    
    return ProgressResponse(bot_response=jawaban_ai)