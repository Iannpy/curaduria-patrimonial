
import os
import sys

# Asegurar que el directorio raíz está en el path
sys.path.append(os.getcwd())

from src.database.models import EvaluacionModel
from src.config import config

print(f"Usando DB: {config.db_path}")

try:
    df = EvaluacionModel.obtener_todas_dataframe()
    print(f"Evaluaciones encontradas: {len(df)}")
    if not df.empty:
        print(df.head())
    else:
        print("El DataFrame está VACÍO")
        
        # Diagnóstico manual
        from src.database.connection import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM evaluaciones")
            print(f"Filas en 'evaluaciones': {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            print(f"Filas en 'usuarios': {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM grupos")
            print(f"Filas en 'grupos': {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM dimensiones")
            print(f"Filas en 'dimensiones': {cursor.fetchone()[0]}")
            
            # Probar el JOIN paso a paso
            cursor.execute("SELECT COUNT(*) FROM evaluaciones e JOIN usuarios u ON e.usuario_id = u.id")
            print(f"Join E+U: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM evaluaciones e JOIN grupos g ON e.codigo_grupo = g.codigo")
            print(f"Join E+G: {cursor.fetchone()[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM evaluaciones e JOIN dimensiones d ON e.dimension_id = d.id")
            print(f"Join E+D: {cursor.fetchone()[0]}")

            # Verificar si hay espacios o problemas en los códigos
            cursor.execute("SELECT codigo_grupo FROM evaluaciones LIMIT 5")
            e_codes = [f"'{row[0]}'" for row in cursor.fetchall()]
            print(f"Codigos en EVAL: {e_codes}")
            
            cursor.execute("SELECT codigo FROM grupos LIMIT 5")
            g_codes = [f"'{row[0]}'" for row in cursor.fetchall()]
            print(f"Codigos en GRUPOS: {g_codes}")

            # Verificar si hay algun error capturado en el log
            print("\nÚltimos logs relevantes:")
            import subprocess
            subprocess.run(["powershell", "-Command", "Get-Content logs/app.log -Tail 10"], capture_output=False)

except Exception as e:
    print(f"ERROR: {e}")
