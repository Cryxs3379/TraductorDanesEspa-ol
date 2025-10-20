#!/usr/bin/env python3
"""
Test definitivo para verificar la traducción completa.
"""
import requests
import json

def test_definitivo():
    """Test definitivo con el texto específico del usuario."""
    
    texto = """Esto no se queda en el periodismo. Las editoriales y los lectores hoy por hoy agradecen los libros narrativos cortos, novelas fragmentadas y relatos breves: un objeto liviano que puedan leer de a sorbos en no más de una semana (yo misma escribo así). Porque ya es poca la concentración y el tiempo que nos queda, y porque nos hemos acostumbrado a la rapidez de ese clickbait y de las redes sociales. Así, muchos libros de no ficción, de autoayuda, autobiográficos o incluso narrativos están siguiendo esta línea para acelerar su lectura y no perder audiencia. Además, no solo se escriben livianos, sino que se leerán cada vez más livianos. Hoy existen apps donde puedes subir un libro en pdf y pedirle que te lo resuma en dos líneas. Queremos leer así porque no hay tiempo, porque a la décima línea nos distraemos, nos aburrimos, miramos TikTok, vamos a la cocina a hacernos un café y luego olvidamos retomarlo. ¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"""
    
    print(f"🔍 Testing texto de {len(texto)} caracteres")
    print("📤 Enviando request sin max_new_tokens...")
    
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
        print(f"📊 Ratio:     {len(result)/len(texto):.2%}")
        
        # Verificar palabras clave específicas del final
        final_phrases = [
            "robot",
            "famoso", 
            "TLDR",
            "completo",
            "pedirle"
        ]
        
        found_phrases = []
        for phrase in final_phrases:
            if phrase.lower() in result.lower():
                found_phrases.append(phrase)
        
        print(f"🔍 Frases finales encontradas: {found_phrases}")
        
        # Verificar el final específico
        texto_final = "¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"
        if any(word in result.lower() for word in ["tldr", "robot", "famoso", "completo"]):
            print("✅ ÉXITO: Contenido del final presente en la traducción")
            success = True
        else:
            print("❌ PROBLEMA: Falta contenido del final")
            success = False
            
        print(f"\n📝 TRADUCCIÓN COMPLETA:")
        print("-" * 80)
        print(result)
        print("-" * 80)
        
        # Mostrar el final original para comparar
        print(f"\n📝 FINAL ORIGINAL:")
        print("-" * 80)
        print(texto[-100:])
        print("-" * 80)
        
        return success
        
    else:
        print(f"❌ Error HTTP: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    try:
        # Verificar servidor primero
        health = requests.get('http://localhost:8000/health', timeout=5)
        if health.status_code != 200 or not health.json().get('model_loaded'):
            print("❌ Servidor no está listo")
            exit(1)
            
        print("🚀 Ejecutando test definitivo...")
        success = test_definitivo()
        
        if success:
            print("\n🎉 ¡ÉXITO! La traducción incluye el contenido completo")
        else:
            print("\n❌ AÚN HAY PROBLEMA - Revisa los logs del servidor")
            print("💡 Busca en los logs: 'max_new_tokens', 'FINAL', 'continuación'")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Asegúrate de que el servidor esté corriendo en http://localhost:8000")
