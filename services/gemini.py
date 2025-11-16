import google.generativeai as genai
from core.config import settings

# Konfigurasi library Google dengan API key Anda dari .env
genai.configure(api_key=settings.GEMINI_API_KEY)

# Inisialisasi model yang ingin Anda gunakan
# Kita bisa setel safety_settings di sini jika perlu
model = genai.GenerativeModel('gemini-2.5-flash')

async def call_gemini_api(prompt: str) -> str:
    """
    Memanggil Gemini API secara asinkron menggunakan Google Python SDK.
    """
    try:
        # Gunakan .generate_content_async() untuk FastAPI (non-blocking)
        response = await model.generate_content_async(
            prompt,
            # (Opsional) Atur setelan keamanan di sini
            # safety_settings={
            #     'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            #     'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            #     'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            #     'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
            # }
        )
        
        # Ekstrak teks dari respons SDK
        return response.text
    
    except Exception as e:
        # Tangani error spesifik dari library (contoh: permission denied)
        print(f"[ERROR] Error dari Google SDK: {e}")
        # Beri tahu pengguna tentang error tersebut
        return f"Maaf, terjadi kesalahan saat memproses permintaan AI: {e}"