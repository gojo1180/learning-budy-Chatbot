import asyncio
from fastapi import APIRouter, HTTPException, Query
from schemas.chat import (
    InterestResponse, QuizQuestion, 
    SubmitRequest, SubmitResponse
)
from services.gemini import call_gemini_api
from services.supabase import call_supabase_api
from typing import List, Literal
import random


router = APIRouter(prefix="/recommend", tags=["Rekomendasi"])

CATEGORY_MAP = {
    "AI Engineer": "Machine Learning",
    "Android Developer": "Android",
    "Back-End Developer JavaScript": "Web",
    "Back-End Developer Python": "machine learning",
    "Data Scientist": "Data", 
    "DevOps Engineer": "Cloud Computing", 
    "Front-End Web Developer": "Web",
    "Gen AI Engineer": "Machine Learning",
    "Google Cloud Professional": "Cloud Computing",
    "iOS Developer": "iOS", 
    "MLOps Engineer": "Machine Learning",
    "Multi-Platform App Developer": "Mobile",
    "React Developer": "Web" 
}

@router.get("/interests", response_model=List[InterestResponse])
async def get_interests():

    target_list = [
        "AI Engineer",
        "Android Developer",
        "Back-End Developer JavaScript",
        "Data Scientist",
        "DevOps Engineer",
        "Front-End Web Developer",
        "Gen AI Engineer",
        "Google Cloud Professional",
        "iOS Developer",
        "MLOps Engineer",
        "Multi-Platform App Developer",
        "React Developer"
    ]

    filter_query = "in.(" + ",".join([f'"{name}"' for name in target_list]) + ")"
    data = await call_supabase_api(
        "learning_paths",
        db_type="dicoding",
        params={
            "select": "learning_path_id,learning_path_name",
            "learning_path_name": filter_query  
        }
    )

    if not data:
        raise HTTPException(status_code=404, detail="Daftar alur belajar tidak ditemukan.")
    
    interests = [
        InterestResponse(id=item['learning_path_id'], name=item['learning_path_name']) 
        for item in data
    ]
    return interests


@router.get("/quiz", response_model=List[QuizQuestion])
async def get_quiz(
    kategori_minat: str = Query(..., example="Android Developer"), 
):
    """
    FITUR 1 (Step 2): Mengambil 5 soal kuis ACAK per level (Beginner, Intermediate, Advanced).
    """
    tech_category_mock = CATEGORY_MAP.get(kategori_minat, kategori_minat)
    print(f"[DEBUG] Menerjemahkan minat: '{kategori_minat}' -> '{tech_category_mock}'")
    
    select_query = "id,question_desc,option_1,option_2,option_3,option_4"
    
    try:
        data_beginner, data_intermediate, data_advanced = await asyncio.gather(
            call_supabase_api(
                "Tech Questions", db_type="mock",
                params={
                    "tech_category": f"eq.{tech_category_mock}",
                    "difficulty": "eq.beginner",
                    "select": select_query,
                    "limit": 20 
                }
            ),
            call_supabase_api(
                "Tech Questions", db_type="mock",
                params={
                    "tech_category": f"eq.{tech_category_mock}",
                    "difficulty": "eq.intermediate",
                    "select": select_query,
                    "limit": 20
                }
            ),
            call_supabase_api(
                "Tech Questions", db_type="mock",
                params={
                    "tech_category": f"eq.{tech_category_mock}",
                    "difficulty": "eq.advanced",
                    "select": select_query,
                    "limit": 20
                }
            )
        )
    except Exception as e:
        print(f"Error fetching quiz data: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil data kuis dari Supabase.")

    def pick_random_questions(data_pool, count=5):
        if not data_pool: 
            return []
        if len(data_pool) <= count: 
            return data_pool
        return random.sample(data_pool, count)
    final_beginner = pick_random_questions(data_beginner, 5)
    final_intermediate = pick_random_questions(data_intermediate, 5)
    final_advanced = pick_random_questions(data_advanced, 5)

    data_combined = final_beginner + final_intermediate + final_advanced
    
    if not data_combined:
        raise HTTPException(status_code=404, detail=f"Kuis untuk {kategori_minat} (kategori: {tech_category_mock}) tidak ditemukan.")
    
    questions = [
        QuizQuestion(
            question_id=item['id'],
            question_desc=item['question_desc'],
            option_1=item['option_1'],
            option_2=item['option_2'],
            option_3=item['option_3'],
            option_4=item['option_4']
        ) for item in data_combined
    ]
    
    return questions


@router.post("/submit", response_model=SubmitResponse)
async def handle_submission(request: SubmitRequest):
    """
    FITUR 1 (Step 3): Menerima jawaban kuis, menghitung skor,
    dan mengirim detail kesalahan ke AI untuk analisis personal.
    """
    
    question_ids = [answer.question_id for answer in request.answers]
    if not question_ids:
        raise HTTPException(status_code=400, detail="Tidak ada jawaban yang diterima.")

    correct_answers_data = await call_supabase_api(
        "Tech Questions", db_type="mock",
        params={
            "id": f"in.({','.join(map(str, question_ids))})",
            "select": "id,question_desc,correct_answer" 
        }
    )
    
    if not correct_answers_data:
        raise HTTPException(status_code=404, detail="Soal kuis tidak ditemukan di database.")
        
    qa_map = {
        item['id']: {
            'correct': item['correct_answer'], 
            'question': item['question_desc']
        } 
        for item in correct_answers_data
    }
    
    skor = 0
    total_soal = len(request.answers)
    list_analisis = [] 

    for answer in request.answers:
        if answer.question_id in qa_map:
            data_soal = qa_map[answer.question_id]
            jawaban_user = answer.selected_answer
            jawaban_benar = data_soal['correct']
            
            if jawaban_user == jawaban_benar:
                skor += 1
            else:
                detail = (
                    f"- Soal: {data_soal['question']}\n"
                    f"  Jawaban Kamu: {jawaban_user} (Salah)\n"
                    f"  Seharusnya: {jawaban_benar}"
                )
                list_analisis.append(detail)

    analisis_str = "\n".join(list_analisis) if list_analisis else "User menjawab semua soal dengan BENAR."

    level_rekomendasi_str = "Dasar"
    level_rekomendasi_id = 1 
    if total_soal > 0:
        persentase = skor / total_soal
        if persentase >= 0.6: 
            level_rekomendasi_str = "Menengah"
            level_rekomendasi_id = 3

    lp_data = await call_supabase_api(
        "learning_paths", db_type="dicoding",
        params={"learning_path_name": f"eq.{request.kategori_minat}", "select": "learning_path_id", "limit": 1}
    )
    if not lp_data:
         lp_id = 1 
    else:
         lp_id = lp_data[0]['learning_path_id']

    kursus_cocok = await call_supabase_api(
        "courses", db_type="dicoding",
        params={
            "learning_path_id": f"eq.{lp_id}",
            "course_level_str": f"eq.{level_rekomendasi_id}",
            "select": "course_id,course_name",
            "limit": 1
        }
    )
    
    nama_kursus = kursus_cocok[0].get('course_name') if kursus_cocok else "Kursus Umum"
    id_kursus = kursus_cocok[0].get('course_id') if kursus_cocok else None

    prompt = f"""
    Kamu adalah Learning Buddy, mentor coding yang suportif.
    
    Konteks:
    User baru saja mengerjakan kuis '{request.kategori_minat}'.
    - Skor: {skor} dari {total_soal}
    - Level Rekomendasi: {level_rekomendasi_str}
    - Kursus yang disarankan: {nama_kursus}
    
    Berikut adalah detail jawaban user (fokus pada kesalahannya):
    =========================================
    {analisis_str}
    =========================================
    
    Tugas:
    1. Berikan semangat berdasarkan skornya.
    2. JIKA ada jawaban salah, pilih 1 atau 2 kesalahan yang paling fatal/mendasar, lalu jelaskan secara singkat kenapa jawaban user salah dan apa konsep yang benar (gunakan bahasa santai). Jangan bahas semua kesalahan agar tidak kepanjangan.
    3. Arahkan user untuk mengambil kursus '{nama_kursus}' untuk memperbaiki pemahaman tersebut.
    4. Jaga respon tetap ringkas (maksimal 3 paragraf).
    5. Sebutkan 6 skill teknis spesifik (keyword) yang harus dikuasai user untuk memperbaiki kesalahannya, urutkan dari basic ke advanced.
    """
    
    jawaban_ai = await call_gemini_api(prompt)
    
    return SubmitResponse(
        bot_response=jawaban_ai,
        suggested_course_name=nama_kursus,
        suggested_course_id=id_kursus
    )