from pydantic import BaseModel
from typing import Optional, Literal, List

# --- Model untuk /ask ---
class AskRequest(BaseModel):
    question: str
    preset: Literal["to the point", "santai"] = "to the point"

class AskResponse(BaseModel):
    bot_response: str

# --- Model untuk /progress ---
class ProgressRequest(BaseModel):
    email: str # Kita kembalikan ke email sesuai struktur CSV

class ProgressResponse(BaseModel):
    bot_response: str

# --- Model BARU untuk Alur Rekomendasi ---

# Model untuk GET /interests
class InterestResponse(BaseModel):
    id: int
    name: str

# Model untuk GET /quiz (hanya soal & opsi, tanpa jawaban)
class QuizQuestion(BaseModel):
    question_id: int
    question_desc: str
    option_1: str
    option_2: str
    option_3: str
    option_4: str

# Model untuk POST /submit (jawaban dari user)
class QuizAnswer(BaseModel):
    question_id: int
    selected_answer: str # Teks dari jawaban yang dipilih

class SubmitRequest(BaseModel):
    kategori_minat: str
    level: Literal["beginner", "intermediate", "advanced"]
    answers: List[QuizAnswer]

# Model untuk response /submit (rekomendasi final)
class SubmitResponse(BaseModel):
    bot_response: str
    suggested_course_name: Optional[str] = None
    suggested_course_id: Optional[int] = None
    
# --- Hapus Model RecommendRequest & RecommendResponse yang lama ---
# class RecommendRequest(BaseModel): ... (HAPUS INI)
# class RecommendResponse(BaseModel): ... (HAPUS INI)