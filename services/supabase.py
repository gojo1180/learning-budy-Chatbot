import httpx
from core.config import settings
from typing import Optional, List, Dict, Any, Literal


# Konfigurasi untuk DUA klien Supabase
CLIENT_CONFIGS = {
    "dicoding": {
        "base_url": settings.DICODING_SUPABASE_URL,
        "headers": {
            "apikey": settings.DICODING_SUPABASE_KEY,
            "Authorization": f"Bearer {settings.DICODING_SUPABASE_KEY}"
        }
    },
    "mock": {
        "base_url": settings.MOCK_SUPABASE_URL,
        "headers": {
            "apikey": settings.MOCK_SUPABASE_KEY,
            "Authorization": f"Bearer {settings.MOCK_SUPABASE_KEY}"
        }
    }
}

async def call_supabase_api(
    endpoint: str, 
    db_type: Literal["dicoding", "mock"] = "dicoding", 
    params: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    
    

    config = CLIENT_CONFIGS.get(db_type)
    if not config:
        print(f"Error: Konfigurasi db_type '{db_type}' tidak ditemukan.")
        return None
        

    async with httpx.AsyncClient() as client:
        try:
            url = f"{config['base_url']}/{endpoint}"
            
            response = await client.get(
                url,
                headers=config['headers'],
                params=params
            )
            response.raise_for_status() 
            return response.json()
        
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP saat memanggil Supabase ({db_type}): {e}")
            return None
        except Exception as e:
            print(f"Error tidak terduga saat memanggil Supabase: {e}")
            return None


