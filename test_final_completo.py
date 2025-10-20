#!/usr/bin/env python3
"""
Test final completo para verificar que la traducción funciona sin truncado.
"""
import requests
import json
import sys

def test_completo():
    """Test completo del texto del usuario."""
    
    texto_problema = """Esto no se queda en el periodismo. Las editoriales y los lectores hoy por hoy agradecen los libros narrativos cortos, novelas fragmentadas y relatos breves: un objeto liviano que puedan leer de a sorbos en no más de una semana (yo misma escribo así). Porque ya es poca la concentración y el tiempo que nos queda, y porque nos hemos acostumbrado a la rapidez de ese clickbait y de las redes sociales. Así, muchos libros de no ficción, de autoayuda, autobiográficos o incluso narrativos están siguiendo esta línea para acelerar su lectura y no perder audiencia. Además, no solo se escriben livianos, sino que se leerán cada vez más livianos. Hoy existen apps donde puedes subir un libro en pdf y pedirle que te lo resuma en dos líneas. Queremos leer así porque no hay tiempo, porque a la décima línea nos distraemos, nos aburrimos, miramos TikTok, vamos a la cocina a hacernos un café y luego olvidamos retomarlo. ¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"""
    
    print("🔍 TEST FINAL - VERIFICACIÓN COMPLETA")
    print("=" * 60)
    print(f"📏 Longitud del texto: {len(texto_problema)} caracteres")
    
    # Verificar que contenga las palabras clave del final
    final_keywords = ["robot", "famoso", "TLDR"]
    has_final = all(keyword in texto_problema for keyword in final_keywords)
    print(f"🔑 Contiene palabras finales: {'✅' if has_final else '❌'} {final_keywords}")
    
    print("\n📤 Enviando request al servidor...")
    
    try:
        response = requests.post('http://localhost:8000/translate', 
            json={"text": texto_problema, "direction": "es-da"}, 
            timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            resultado = data["translations"][0]
            
            print(f"✅ HTTP Status: {response.status_code}")
            print(f"📏 Original:  {len(texto_problema)} chars")
            print(f"📏 Resultado: {len(resultado)} chars")
            print(f"📊 Ratio:     {len(resultado)/len(texto_problema):.1%}")
            
            # Verificar palabras clave en la traducción
            danish_keywords = ["robot", "famoso", "tldr", "komplet", "læse"]
            found_keywords = []
            for keyword in danish_keywords:
                if keyword.lower() in resultado.lower():
                    found_keywords.append(keyword)
            
            print(f"🔍 Palabras clave encontradas: {found_keywords}")
            
            # Verificar si parece completa
            ratio_ok = len(resultado) > len(texto_problema) * 0.6  # Al menos 60%
            has_final_content = len(found_keywords) > 0
            
            print(f"\n📋 CRITERIOS:")
            print(f"   └ Ratio aceptable (>60%): {'✅' if ratio_ok else '❌'} ({len(resultado)/len(texto_problema):.1%})")
            print(f"   └ Contenido final presente: {'✅' if has_final_content else '❌'} ({found_keywords})")
            
            success = ratio_ok and has_final_content
            
            print(f"\n📝 TRADUCCIÓN OBTENIDA:")
            print("-" * 80)
            print(resultado)
            print("-" * 80)
            
            # Mostrar final para comparación
            print(f"\n📝 FINAL ORIGINAL:")
            print("-" * 80) 
            print(texto_problema[-150:])
            print("-" * 80)
            
            return success
            
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - el servidor tardó demasiado")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 Error de conexión - verifica que el servidor esté corriendo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def verificar_servidor():
    """Verificar que el servidor esté funcionando."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            modelo_ok = data.get('model_loaded', False)
            print(f"🏥 Servidor: {'✅ OK' if response.status_code == 200 else '❌ Error'}")
            print(f"🤖 Modelo: {'✅ Cargado' if modelo_ok else '❌ No cargado'}")
            return modelo_ok
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TEST FINAL COMPLETO")
    print("=" * 60)
    
    # Verificar servidor
    if not verificar_servidor():
        print("\n❌ El servidor no está listo.")
        print("💡 Solución: Ejecuta 'python start_server.py' en otra terminal")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Ejecutar test
    resultado = test_completo()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    if resultado:
        print("🎉 ¡ÉXITO! La traducción está completa y sin truncado")
        print("✅ El problema del truncado ha sido resuelto")
    else:
        print("❌ AÚN HAY PROBLEMA - La traducción sigue truncada")
        print("💡 Revisa los logs del servidor para más detalles")
        print("   Busca: 'max_new_tokens', 'FINAL', 'continuación'")
    
    sys.exit(0 if resultado else 1)
