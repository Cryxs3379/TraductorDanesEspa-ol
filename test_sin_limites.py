#!/usr/bin/env python3
"""
Test para verificar que ya no hay límites artificiales.
"""
import requests
import json

def test_sin_limites():
    """Test que debería funcionar sin límites."""
    
    texto = """Esto no se queda en el periodismo. Las editoriales y los lectores hoy por hoy agradecen los libros narrativos cortos, novelas fragmentadas y relatos breves: un objeto liviano que puedan leer de a sorbos en no más de una semana (yo misma escribo así). Porque ya es poca la concentración y el tiempo que nos queda, y porque nos hemos acostumbrado a la rapidez de ese clickbait y de las redes sociales. Así, muchos libros de no ficción, de autoayuda, autobiográficos o incluso narrativos están siguiendo esta línea para acelerar su lectura y no perder audiencia. Además, no solo se escriben livianos, sino que se leerán cada vez más livianos. Hoy existen apps donde puedes subir un libro en pdf y pedirle que te lo resuma en dos líneas. Queremos leer así porque no hay tiempo, porque a la décima línea nos distraemos, nos aburrimos, miramos TikTok, vamos a la cocina a hacernos un café y luego olvidamos retomarlo. ¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"""
    
    print(f"🔍 Testing texto de {len(texto)} caracteres")
    print("📤 Enviando sin max_new_tokens (modo auto)...")
    
    response = requests.post('http://localhost:8000/translate', json={
        "text": texto,
        "direction": "es-da"
    }, timeout=120)
    
    if response.status_code == 200:
        data = response.json()
        result = data["translations"][0]
        
        print(f"✅ Status: {response.status_code}")
        print(f"📏 Original:  {len(texto)} chars")
        print(f"📏 Traducido: {len(result)} chars")
        
        # Buscar palabras clave del final
        final_words = ["TLDR", "robot", "completo", "famoso"]
        found_final = any(word.lower() in result.lower() for word in final_words)
        
        print(f"🔍 Final presente: {'✅' if found_final else '❌'}")
        
        if found_final:
            print("🎉 ÉXITO: Traducción completa sin truncado")
        else:
            print("❌ Aún hay truncado")
            print(f"Final original: ...{texto[-100:]}")
            print(f"Final traducido: ...{result[-100:]}")
        
        return found_final
    else:
        print(f"❌ Error: {response.status_code}")
        return False

if __name__ == "__main__":
    try:
        # Verificar servidor
        health = requests.get('http://localhost:8000/health', timeout=5)
        if health.status_code != 200 or not health.json().get('model_loaded'):
            print("❌ Servidor no listo")
            exit(1)
            
        success = test_sin_limites()
        print(f"\n{'🎉 ÉXITO' if success else '❌ AÚN HAY PROBLEMA'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
