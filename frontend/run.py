"""Punto de entrada del frontend.  Uso:  python run.py   ->  http://localhost:5001

El API corre en otro puerto (5000). Son DOS aplicaciones Flask independientes:
el front no toca la base de datos, solo le habla al API por HTTP.
"""
from dotenv import load_dotenv

load_dotenv()  # lee el archivo .env (si existe) ANTES de importar la config

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(port=5001, debug=True)
