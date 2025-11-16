from fastapi import APIRouter
from schemas.chat import AskRequest, AskResponse
from services.gemini import call_gemini_api
from services.supabase import call_supabase_api

# Buat router khusus untuk endpoint 'ask'
router = APIRouter()

@router.post("/ask", response_model=AskResponse)
async def handle_ask(request: AskRequest):
    """
    FITUR 2: Menjawab pertanyaan teknis (Dengan RAG)
    """
    
    # --- RETRIEVAL ---
    search_query = request.question.replace(" ", "%") 
    
    konteks_tutorials = await call_supabase_api(
        "tutorials", 
        db_type= "dicoding",
        params={
            "tutorial_title": f"ilike.%{search_query}%",
            "select": "tutorial_title", 
            "limit": 3
        }
    )

    konteks_str = "Tidak ada konteks materi yang ditemukan."
    if konteks_tutorials:
        judul_tutorial = [t['tutorial_title'] for t in konteks_tutorials]
        konteks_str = "Konteks Materi:\n- " + "\n- ".join(judul_tutorial)
        
    print(f"[DEBUG RAG] Konteks ditemukan: {konteks_str}")

    # ---  AUGMENTATION  ---
    prompt_nada = ""
    if request.preset == "santai":
        prompt_nada = "Jawab pertanyaan berikut dengan nada yang santai, ramah, dan mudah dimengerti (dalam Bahasa Indonesia), seolah-olah menjelaskan ke seorang teman."
    else:
        prompt_nada = "Jawab pertanyaan teknis berikut secara akurat, ringkas, dan to the point (dalam Bahasa Indonesia)."

    prompt_final = f"""
    Anda adalah Asisten Pengajar yang ahli.
    Tugas Anda adalah menjawab pertanyaan siswa berdasarkan materi kursus yang tersedia.
    
    {konteks_str}
    
    Berdasarkan konteks di atas (JIKA relevan) dan pengetahuan umum Anda, 
    tolong jawab pertanyaan siswa berikut:
    
    Pertanyaan: "{request.question}"
    
    Instruksi Jawaban: {prompt_nada}
    """
    
    # --- ENERATION ---
    jawaban_ai = await call_gemini_api(prompt_final)
    
    return AskResponse(bot_response=jawaban_ai)