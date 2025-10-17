"""
Pydantic schemas para validación de request/response del API.
"""
from typing import Union, Optional
from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """
    Modelo de request para traducción.
    
    Attributes:
        text: Texto o lista de textos a traducir
        max_new_tokens: Número máximo de tokens a generar (default: 256)
        glossary: Diccionario opcional de términos ES -> DA para preservar/reemplazar
    """
    text: Union[str, list[str]] = Field(
        ...,
        description="Texto o lista de textos en español a traducir"
    )
    max_new_tokens: int = Field(
        default=256,
        ge=1,
        le=512,
        description="Número máximo de tokens a generar por traducción"
    )
    glossary: Optional[dict[str, str]] = Field(
        default=None,
        description="Glosario opcional: términos español -> danés"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": ["Hola mundo", "¿Cómo estás?"],
                "max_new_tokens": 256,
                "glossary": {
                    "Acme": "Acme",
                    "Python": "Python"
                }
            }
        }


class TranslateResponse(BaseModel):
    """
    Modelo de response para traducción.
    
    Attributes:
        provider: Identificador del proveedor de traducción
        source: Código de idioma origen (FLORES-200)
        target: Código de idioma destino (FLORES-200)
        translations: Lista de textos traducidos
    """
    provider: str = Field(
        default="nllb-ct2-int8",
        description="Proveedor/motor de traducción"
    )
    source: str = Field(
        default="spa_Latn",
        description="Código de idioma origen (FLORES-200)"
    )
    target: str = Field(
        default="dan_Latn",
        description="Código de idioma destino (FLORES-200)"
    )
    translations: list[str] = Field(
        ...,
        description="Lista de traducciones generadas"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "nllb-ct2-int8",
                "source": "spa_Latn",
                "target": "dan_Latn",
                "translations": ["Hej verden", "Hvordan har du det?"]
            }
        }

