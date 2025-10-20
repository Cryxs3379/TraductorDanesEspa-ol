import requests
import json

# Texto del problema del usuario
texto_problema = """Esto no se queda en el periodismo. Las editoriales y los lectores hoy por hoy agradecen los libros narrativos cortos, novelas fragmentadas y relatos breves: un objeto liviano que puedan leer de a sorbos en no más de una semana (yo misma escribo así). Porque ya es poca la concentración y el tiempo que nos queda, y porque nos hemos acostumbrado a la rapidez de ese clickbait y de las redes sociales. Así, muchos libros de no ficción, de autoayuda, autobiográficos o incluso narrativos están siguiendo esta línea para acelerar su lectura y no perder audiencia. Además, no solo se escriben livianos, sino que se leerán cada vez más livianos. Hoy existen apps donde puedes subir un libro en pdf y pedirle que te lo resuma en dos líneas. Queremos leer así porque no hay tiempo, porque a la décima línea nos distraemos, nos aburrimos, miramos TikTok, vamos a la cocina a hacernos un café y luego olvidamos retomarlo. ¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"""

print("TEST DIRECTO - VERIFICACION TRUNCADO")
print("=" * 60)
print(f"Longitud original: {len(texto_problema)} caracteres")

# Verificar health
try:
    health_response = requests.get('http://localhost:8000/health', timeout=5)
    if health_response.status_code == 200:
        health_data = health_response.json()
        print(f"Servidor OK - Modelo cargado: {health_data.get('model_loaded', False)}")
    else:
        print(f"Error health: {health_response.status_code}")
        exit(1)
except Exception as e:
    print(f"Error conectando: {e}")
    exit(1)

# Hacer la traducción
try:
    print("\nEnviando request de traduccion...")
    response = requests.post('http://localhost:8000/translate', 
        json={
            "text": texto_problema, 
            "direction": "es-da"
        }, 
        timeout=120)
    
    if response.status_code == 200:
        data = response.json()
        resultado = data["translations"][0]
        
        print(f"\nRESULTADOS:")
        print(f"Status: {response.status_code}")
        print(f"Original:  {len(texto_problema)} chars")
        print(f"Traducido: {len(resultado)} chars")
        print(f"Ratio:     {len(resultado)/len(texto_problema):.1%}")
        
        # Verificar si contiene el final
        final_original = "¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"
        print(f"\nFinal original:")
        print(final_original)
        
        # Buscar keywords en danish
        keywords_check = ["robot", "tldr", "komplet", "læse", "famoso"]
        encontradas = [kw for kw in keywords_check if kw.lower() in resultado.lower()]
        print(f"\nKeywords encontradas: {encontradas}")
        
        # Mostrar final de la traducción
        print(f"\nFinal traducido (ultimos 200 chars):")
        print(resultado[-200:])
        
        # Determinar éxito
        ratio_ok = len(resultado) > len(texto_problema) * 0.7  # 70%
        tiene_final = len(encontradas) > 0
        
        print(f"\nEVALUACION:")
        print(f"Ratio >70%: {'SI' if ratio_ok else 'NO'} ({len(resultado)/len(texto_problema):.1%})")
        print(f"Tiene keywords finales: {'SI' if tiene_final else 'NO'}")
        
        if ratio_ok and tiene_final:
            print("\nEXITO: Traduccion parece completa!")
        else:
            print("\nPROBLEMA: Aun hay truncado")
            
    else:
        print(f"Error HTTP {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
