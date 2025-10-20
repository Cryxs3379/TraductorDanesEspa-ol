#!/usr/bin/env python3
"""
Test específico para el texto que reporta el usuario.
"""
import requests
import json
import sys

def test_texto_usuario():
    """Test con el texto específico del usuario."""
    print("🔍 TEST CON TEXTO ESPECÍFICO DEL USUARIO")
    print("=" * 60)
    
    texto_original = """Esto no se queda en el periodismo. Las editoriales y los lectores hoy por hoy agradecen los libros narrativos cortos, novelas fragmentadas y relatos breves: un objeto liviano que puedan leer de a sorbos en no más de una semana (yo misma escribo así). Porque ya es poca la concentración y el tiempo que nos queda, y porque nos hemos acostumbrado a la rapidez de ese clickbait y de las redes sociales. Así, muchos libros de no ficción, de autoayuda, autobiográficos o incluso narrativos están siguiendo esta línea para acelerar su lectura y no perder audiencia. Además, no solo se escriben livianos, sino que se leerán cada vez más livianos. Hoy existen apps donde puedes subir un libro en pdf y pedirle que te lo resuma en dos líneas. Queremos leer así porque no hay tiempo, porque a la décima línea nos distraemos, nos aburrimos, miramos TikTok, vamos a la cocina a hacernos un café y luego olvidamos retomarlo. ¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"""
    
    traduccion_esperada_completa = """Det er ikke journalistikken, der holder. Redaktioner og læsere i dag takker for korte fortællingsbøger, fragmenterede noveller og kortfortællinger: et let genstand, som man kan læse af sig selv på mindst en uge (jeg skriver sådan). Fordi vi allerede har lidt koncentration og tid tilbage, og fordi vi er vant til hurtigheden med denne clickbait og de sociale medier. Så mange boger uden fiktion, selvhjælp, autobiografi eller endda fortælling følger denne linje for at fremskynde sin læsning og undgå at miste publikum. Desuden bliver det ikke kun lettere skrevet, men vil blive mere lett. I dag findes apps hvor du kan downloade en pdf-bog og bede dig om at opsummere den online."""
    
    print(f"📏 Texto original: {len(texto_original)} caracteres")
    print(f"📏 Traducción esperada completa: {len(traduccion_esperada_completa)} caracteres")
    
    # Test 1: Modo Auto (sin max_new_tokens)
    print("\n🧪 TEST 1: Modo Auto")
    payload = {
        "text": texto_original,
        "direction": "es-da"
        # Sin max_new_tokens - debería usar cálculo adaptativo
    }
    
    try:
        print("📤 Enviando request al servidor...")
        response = requests.post('http://localhost:8000/translate', json=payload, timeout=120)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            traduccion_obtenida = data["translations"][0]
            
            print(f"\n📏 RESULTADOS:")
            print(f"   Original:    {len(texto_original)} chars")
            print(f"   Obtenida:    {len(traduccion_obtenida)} chars")
            print(f"   Esperada:    {len(traduccion_esperada_completa)} chars")
            print(f"   Ratio:       {len(traduccion_obtenida)/len(texto_original):.2%}")
            
            # Verificar si está truncada comparando con la esperada
            diferencia_pct = abs(len(traduccion_obtenida) - len(traduccion_esperada_completa)) / len(traduccion_esperada_completa)
            
            print(f"\n📝 TRADUCCIÓN OBTENIDA:")
            print("-" * 50)
            print(traduccion_obtenida)
            print("-" * 50)
            
            print(f"\n📝 TRADUCCIÓN ESPERADA:")
            print("-" * 50)
            print(traduccion_esperada_completa)
            print("-" * 50)
            
            # Verificar si se perdió el final
            texto_original_final = "¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"
            if texto_original_final in texto_original:
                if "TLDR" in traduccion_obtenida or "robot" in traduccion_obtenida.lower():
                    print("✅ FINAL PRESENTE: La parte final parece estar traducida")
                else:
                    print("❌ FINAL PERDIDO: La parte final se perdió en la traducción")
                    
                    # Buscar dónde se corta
                    palabras_finales = ["TLDR", "robot", "completo"]
                    for palabra in palabras_finales:
                        if palabra.lower() in texto_original.lower():
                            pos_original = texto_original.lower().find(palabra.lower())
                            print(f"   Palabra '{palabra}' en posición {pos_original} del original")
            
            # Análisis de truncado
            if len(traduccion_obtenida) < len(traduccion_esperada_completa) * 0.8:
                print(f"\n❌ PROBLEMA CONFIRMADO: Traducción truncada")
                print(f"   Diferencia: {len(traduccion_esperada_completa) - len(traduccion_obtenida)} caracteres")
                return False
            else:
                print(f"\n✅ Traducción parece completa (diferencia < 20%)")
                return True
                
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def test_health():
    """Verifica que el servidor esté funcionando."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"🏥 Servidor: {data.get('status', 'unknown')}")
            print(f"🤖 Modelo: {'✅ Cargado' if data.get('model_loaded') else '❌ No cargado'}")
            return data.get('model_loaded', False)
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TEST ESPECÍFICO")
    
    if not test_health():
        print("\n❌ El servidor no está listo.")
        print("   Ejecuta: python start_server.py")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    success = test_texto_usuario()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Traducción completa - no hay truncado")
    else:
        print("❌ CONFIRMADO: Hay truncado - necesitamos investigar más")
        print("\n💡 Revisa los logs del servidor para ver qué max_new_tokens se está usando")
