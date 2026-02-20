from pathlib import Path
from src.config import DATA_DIR

# Ver qué archivos .db hay
archivos = list(Path(DATA_DIR).glob("*.db"))
print("BDs encontradas:")
for archivo in archivos:
    print(f"  - {archivo.name}")