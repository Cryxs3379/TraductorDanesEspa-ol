"""
Versión simplificada del servidor sin warmup problemático.
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union, Optional

# Configurar variables de entorno
os.environ["MODEL_DIR"] = "./models/nllb-600m"
os.environ["CT2_DIR"] = "./models/nllb-600m-ct2-int8"

app = FastAPI(
    title="Traductor Español → Danés (NLLB + CTranslate2)",
    description="Servicio de traducción 100% local, gratuito y privado.",
    version="1.0.0"
)

# Variables globales para el modelo
translator = None
tokenizer = None
model_loaded = False

class TranslateRequest(BaseModel):
    text: Union[str, list]
    max_new_tokens: int = 256
    glossary: Optional[dict] = None

class TranslateResponse(BaseModel):
    provider: str = "nllb-ct2-int8"
    source: str = "spa_Latn"
    target: str = "dan_Latn"
    translations: list[str]

@app.on_event("startup")
async def startup_event():
    """Carga el modelo al inicio."""
    global translator, tokenizer, model_loaded
    
    try:
        print("=" * 70)
        print("Iniciando servidor de traduccion ES->DA")
        print("=" * 70)
        
        # Importar aquí para evitar problemas de carga
        import ctranslate2 as ct
        from transformers import AutoTokenizer
        
        print("Cargando modelo CTranslate2...")
        translator = ct.Translator(
            os.environ["CT2_DIR"],
            device="cpu",
            compute_type="int8"
        )
        print("✓ CTranslate2 cargado")
        
        print("Cargando tokenizador...")
        tokenizer = AutoTokenizer.from_pretrained(os.environ["MODEL_DIR"])
        print("✓ Tokenizador cargado")
        
        model_loaded = True
        print("✓ Modelo listo para traducir")
        print("=" * 70)
        
    except Exception as e:
        print(f"✗ Error al cargar modelo: {e}")
        model_loaded = False

@app.get("/")
async def root():
    return {
        "service": "Traductor ES → DA",
        "provider": "nllb-ct2-int8",
        "status": "online" if model_loaded else "loading",
        "model_loaded": model_loaded
    }

@app.get("/health")
async def health():
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Modelo no cargado")
    return {"status": "healthy", "model_loaded": True}

@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Modelo no cargado")
    
    try:
        # Normalizar input
        texts = [request.text] if isinstance(request.text, str) else request.text
        
        if not texts:
            raise HTTPException(status_code=400, detail="Texto vacío")
        
        # Traducir
        translations = []
        for text in texts:
            if not text.strip():
                translations.append("")
                continue
                
            # Tokenizar
            encoded = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            # Convertir a tokens
            source_tokens = tokenizer.convert_ids_to_tokens(encoded["input_ids"][0].tolist())
            
            # Traducir con CTranslate2
            results = translator.translate_batch(
                [source_tokens],
                beam_size=4,
                max_decoding_length=request.max_new_tokens,
                return_scores=False
            )
            
            # Decodificar
            if results and results[0].hypotheses:
                tokens = results[0].hypotheses[0]
                token_ids = tokenizer.convert_tokens_to_ids(tokens)
                translation = tokenizer.decode(
                    token_ids,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True
                )
                translations.append(translation)
            else:
                translations.append(text)  # Fallback
        
        return TranslateResponse(translations=translations)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al traducir: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
