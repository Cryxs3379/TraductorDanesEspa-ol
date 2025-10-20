#!/usr/bin/env python3
"""
Test rápido para verificar el fix con el texto específico del usuario.
"""
import requests
import json

def test_rapido():
    """Test rápido con el texto del usuario."""
    
    # Texto específico del usuario
    texto = """Esto no se queda en el periodismo. Las editoriales y los lectores hoy por hoy agradecen los libros narrativos cortos, novelas fragmentadas y relatos breves: un objeto liviano que puedan leer de a sorbos en no más de una semana (yo misma escribo así). Porque ya es poca la concentración y el tiempo que nos queda, y porque nos hemos acostumbrado a la rapidez de ese clickbait y de las redes sociales. Así, muchos libros de no ficción, de autoayuda, autobiográficos o incluso narrativos están siguiendo esta línea para acelerar su lectura y no perder audiencia. Además, no solo se escriben livianos, sino que se leerán cada vez más livianos. Hoy existen apps donde puedes subir un libro en pdf y pedirle que te lo resuma en dos líneas. Queremos leer así porque no hay tiempo, porque a la décima línea nos distraemos, nos aburrimos, miramos TikTok, vamos a la cocina a hacernos un café y luego olvidamos retomarlo. ¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"""
    
    print(f"🔍 Testing texto de {len(texto)} caracteres")
    print("📤 Enviando a /translate...")
    
    response = requests.post('http://localhost:8000/translate', json={
        "text": texto,
        "direction": "es-da"
    }, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        result = data["translations"][0]
        
        print(f"✅ Status: {response.status_code}")
        print(f"📏 Original:  {len(texto)} chars")
        print(f"📏 Traducido: {len(result)} chars")
        print(f"📊 Ratio:     {len(result)/len(texto):.2%}")
        
        # Verificar si tiene el final
        if "TLDR" in texto:
            if any(word in result.lower() for word in ["tldr", "robot", "completo"]):
                print("✅ ÉXITO: El final está presente")
            else:
                print("❌ PROBLEMA: El final se perdió")
                print(f"Original final: '...{texto[-50:]}'")
                print(f"Traducido final: '...{result[-50:]}'")
        
        print(f"\n📝 Traducción completa:")
        print("-" * 60)
        print(result)
        print("-" * 60)
        
        return len(result) > len(texto) * 0.7  # Al menos 70% de la longitud
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    try:
        # Verificar servidor
        health = requests.get('http://localhost:8000/health', timeout=5)
        if health.status_code != 200 or not health.json().get('model_loaded'):
            print("❌ Servidor no listo. Ejecuta: python start_server.py")
            exit(1)
            
        success = test_rapido()
        if success:
            print("\n🎉 TEST PASÓ - Traducción completa")
        else:
            print("\n❌ TEST FALLÓ - Posible truncado")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Asegúrate de que el servidor esté corriendo en http://localhost:8000")
