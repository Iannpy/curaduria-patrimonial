"""
Script para crear curadores
Uso: python crear_curadores.py
"""
from src.database.models import UsuarioModel
import bcrypt

# Lista de curadores a crear
curadores = [
    {"username": "marilinb", "password": "32891379"},
    {"username": "rosandryo", "password": "22669635"},
    {"username": "juanad", "password": "22521563"},
    {"username": "edgardoa", "password": "7451403"},
    {"username": "mayerlisb", "password": "32580932"},
    {"username": "esmeirod", "password": "19596603"},
    {"username": "zulmai", "password": "32608112"},
    {"username": "miguelp", "password": "72043865"},
    {"username": "joaquina", "password": "7464618"},
    {"username": "beatrizo", "password": "22406401"},
    {"username": "judithr", "password": "32634991"},
    {"username": "javierj", "password": "8712801"},
    {"username": "emmanuelm", "password": "73125539"},
    {"username": "martap", "password": "32697821"},
    {"username": "diegor", "password": "1045675211"},
    {"username": "marbelb", "password": "22440563"},
    {"username": "astergiop", "password": "80255163"},
    {"username": "juanc", "password": "85373346"},
    {"username": "jairoa", "password": "72254821"},
    {"username": "jorgeb", "password": "7436401"},
]

print("=" * 60)
print("🎭 CREACIÓN DE CURADORES")
print("=" * 60)

creados = 0
ya_existen = 0
errores = 0

for curador in curadores:
    username = curador["username"]
    password = curador["password"]
    
    try:
        # Verificar si ya existe
        usuario_existente = UsuarioModel.obtener_por_username(username)
        
        if usuario_existente:
            print(f"⚠️  {username}: Ya existe")
            ya_existen += 1
        else:
            # Crear hash de contraseña
            hash_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Crear usuario
            user_id = UsuarioModel.crear_usuario(username, hash_pass, "curador")
            
            if user_id:
                print(f"✅ {username}: Creado exitosamente (ID: {user_id})")
                creados += 1
            else:
                print(f"❌ {username}: Error al crear")
                errores += 1
                
    except Exception as e:
        print(f"❌ {username}: Error - {str(e)}")
        errores += 1

print("\n" + "=" * 60)
print("📊 RESUMEN")
print("=" * 60)
print(f"✅ Creados exitosamente: {creados}")
print(f"⚠️  Ya existían: {ya_existen}")
print(f"❌ Errores: {errores}")
print(f"📋 Total procesados: {len(curadores)}")
print("=" * 60)