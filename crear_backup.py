import os
import shutil
from datetime import datetime

def realizar_backup():
    db_original = 'db.sqlite3'
    carpeta_backups = 'backups_seguridad'
    
    if not os.path.exists(carpeta_backups):
        os.makedirs(carpeta_backups)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    nombre_backup = f"backup_academia_{timestamp}.sqlite3"
    ruta_destino = os.path.join(carpeta_backups, nombre_backup)

    if os.path.exists(db_original):
        shutil.copy2(db_original, ruta_destino)
        print("\n" + "="*40)
        print(f"✅ RESPALDO CREADO: {nombre_backup}")
        print(f"�� UBICACIÓN: {carpeta_backups}/")
        print("="*40 + "\n")
    else:
        print(f"❌ Error: No se encontró '{db_original}'.")

if __name__ == '__main__':
    realizar_backup()
