"""
Pydantic schemas para validación de request/response del API.
"""
from typing import Union, Optional, Literal
from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """
    Modelo de request para traducción.
    
    Attributes:
        text: Texto o lista de textos a traducir
        max_new_tokens: Número máximo de tokens a generar (default: 192)
        glossary: Diccionario opcional de términos ES -> DA para preservar/reemplazar
        case_insensitive: Aplicar glosario sin considerar mayúsculas/minúsculas
        formal: Aplicar estilo formal danés (saludos, cierres, tratamiento de usted)
    """
    text: Union[str, list[str]] = Field(
        ...,
        description="Texto o lista de textos en español a traducir"
    )
    max_new_tokens: Optional[int] = Field(
        default=None,
        ge=32,
        le=10000,  # Sin límites prácticos
        description="Número máximo de tokens a generar (None = auto-calculado por el servidor)"
    )
    strict_max: bool = Field(
        default=False,
        description="Si True, NO elevar max_new_tokens en el servidor; usar valor exacto del cliente"
    )
    glossary: Optional[dict[str, str]] = Field(
        default=None,
        description="Glosario opcional: términos español -> danés"
    )
    case_insensitive: bool = Field(
        default=False,
        description="Aplicar glosario sin distinguir mayúsculas/minúsculas"
    )
    formal: bool = Field(
        default=False,
        description="Aplicar estilo formal danés (De/Dem en lugar de du/dig)"
    )
    direction: Literal["es-da", "da-es"] = Field(
        default="es-da",
        description="Dirección de traducción: es-da (Español→Danés) o da-es (Danés→Español)"
    )
    preserve_newlines: bool = Field(
        default=True,
        description="Preservar saltos de línea y estructura del texto original. Si False, permite normalización tradicional"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "text": "Hola, ¿cómo estás?",
                    "direction": "es-da",
                    "formal": False
                },
                {
                    "text": "Hej, hvordan har du det?",
                    "direction": "da-es",
                    "formal": False
                }
            ]
        }


class TranslateResponse(BaseModel):
    """
    Modelo de response para traducción.
    
    Attributes:
        provider: Identificador del proveedor de traducción
        direction: Dirección de traducción usada
        source: Código de idioma origen (FLORES-200)
        target: Código de idioma destino (FLORES-200)
        translations: Lista de textos traducidos
    """
    provider: str = Field(
        default="nllb-ct2-int8",
        description="Proveedor/motor de traducción"
    )
    direction: str = Field(
        ...,
        description="Dirección de traducción: es-da o da-es"
    )
    source: str = Field(
        ...,
        description="Código de idioma origen (FLORES-200)"
    )
    target: str = Field(
        ...,
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


class TranslateHTMLRequest(BaseModel):
    """
    Modelo de request para traducción de HTML.
    
    Attributes:
        html: Contenido HTML a traducir (correos electrónicos)
        max_new_tokens: Número máximo de tokens a generar (default: 192)
        glossary: Diccionario opcional de términos ES -> DA
        case_insensitive: Aplicar glosario sin considerar mayúsculas/minúsculas
        formal: Aplicar estilo formal danés
    """
    html: str = Field(
        ...,
        description="Contenido HTML del correo electrónico a traducir"
    )
    max_new_tokens: Optional[int] = Field(
        default=None,
        ge=32,
        le=10000,  # Sin límites prácticos
        description="Número máximo de tokens a generar por bloque (None = auto-calculado)"
    )
    strict_max: bool = Field(
        default=False,
        description="Si True, NO elevar max_new_tokens en el servidor; usar valor exacto del cliente"
    )
    glossary: Optional[dict[str, str]] = Field(
        default=None,
        description="Glosario opcional: términos español -> danés"
    )
    case_insensitive: bool = Field(
        default=False,
        description="Aplicar glosario sin distinguir mayúsculas/minúsculas"
    )
    formal: bool = Field(
        default=False,
        description="Aplicar estilo formal danés"
    )
    direction: Literal["es-da", "da-es"] = Field(
        default="es-da",
        description="Dirección de traducción: es-da (Español→Danés) o da-es (Danés→Español)"
    )
    preserve_newlines: bool = Field(
        default=True,
        description="Preservar saltos de línea y estructura HTML (<br>, <p>, etc.). Si False, permite normalización tradicional"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "html": "<p>Estimado cliente,</p><p>Gracias por contactar con <strong>Acme</strong>.</p>",
                    "direction": "es-da",
                    "formal": True
                },
                {
                    "html": "<p>Kære kunde,</p><p>Tak for at kontakte <strong>Acme</strong>.</p>",
                    "direction": "da-es",
                    "formal": False
                }
            ]
        }


class TranslateHTMLResponse(BaseModel):
    """
    Modelo de response para traducción de HTML.
    
    Attributes:
        provider: Identificador del proveedor de traducción
        direction: Dirección de traducción usada
        source: Código de idioma origen (FLORES-200)
        target: Código de idioma destino (FLORES-200)
        html: HTML traducido
    """
    provider: str = Field(
        default="nllb-ct2-int8",
        description="Proveedor/motor de traducción"
    )
    direction: str = Field(
        ...,
        description="Dirección de traducción: es-da o da-es"
    )
    source: str = Field(
        ...,
        description="Código de idioma origen (FLORES-200)"
    )
    target: str = Field(
        ...,
        description="Código de idioma destino (FLORES-200)"
    )
    html: str = Field(
        ...,
        description="HTML traducido con estructura preservada"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "nllb-ct2-int8",
                "source": "spa_Latn",
                "target": "dan_Latn",
                "html": "<p>Kære kunde,</p><p>Tak for at kontakte <strong>Acme</strong>.</p>"
            }
        }
