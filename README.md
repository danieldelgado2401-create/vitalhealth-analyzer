# VitalHealth Analyzer Pro – PDF Service
Servicio FastAPI que genera el Informe Cuántico de Salud (Base Caliber).

Deploy (Render):
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`

Endpoint: POST /generate-pdf (devuelve PDF)
