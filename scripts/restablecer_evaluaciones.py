
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para poder importar src
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database.connection import get_db_connection
from src.database.models import LogModel

def restablecer_evaluaciones():
    """
    Elimina todas las evaluaciones de la base de datos y registra la acción.
    """
    print("⚠️  ADVERTENCIA: Esta acción eliminará TODAS las evaluaciones registradas.")
    confirmacion = input("¿Está seguro de que desea continuar? (s/n): ").lower()
    
    if confirmacion != 's':
        print("Operación cancelada.")
        return

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Contar antes de borrar
            cursor.execute("SELECT COUNT(*) FROM evaluaciones")
            total = cursor.fetchone()[0]
            
            # Borrar evaluaciones
            cursor.execute("DELETE FROM evaluaciones")
            
            # También borrar logs relacionados si se desea, o al menos registrar el reset
            LogModel.registrar_log(
                usuario="SISTEMA",
                accion="RESET_EVALUACIONES",
                detalle=f"Se eliminaron {total} evaluaciones manualmente mediante script"
            )
            
            print(f"✅ Éxito: Se han eliminado {total} evaluaciones.")
            
    except Exception as e:
        print(f"❌ Error al restablecer evaluaciones: {e}")

if __name__ == "__main__":
    restablecer_evaluaciones()
