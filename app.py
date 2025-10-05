# app.py
from fastapi import FastAPI, Response
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
import io, base64, requests

APP_TITLE = "VitalHealth Analyzer Pro – PDF Service"
DISTRIBUIDOR = "Jair Montilla – VitalHealth Colombia"
WHATSAPP = "316 709 9568"

app = FastAPI(title=APP_TITLE, version="1.0.0")

class Suplemento(BaseModel):
    nombre: str
    dosis: str
    duracion_dias: int
    notas: Optional[str] = None

class Plan30D(BaseModel):
    habitos: List[str] = []
    suplementos: List[Suplemento] = []

class Secciones(BaseModel):
    estado_general: str
    lo_bueno: str
    vigilar: str
    alterado: str
    como_se_siente: str
    proyeccion: str
    seguimiento: str
    plan_30d: Plan30D

class Branding(BaseModel):
    logo_base64: Optional[str] = None
    logo_url: Optional[str] = None
    whatsapp: str = WHATSAPP
    distribuidor: str = DISTRIBUIDOR

class Payload(BaseModel):
    paciente_nombre: str = Field(..., description="Tomado del contenido DEL EXAMEN (no del nombre de archivo)")
    paciente_edad: Optional[str] = None
    paciente_sexo: Optional[str] = None
    fecha_analisis: Optional[str] = None
    secciones: Secciones
    branding: Branding = Branding()

def _load_logo(branding: Branding):
    if branding.logo_base64:
        try:
            return ImageReader(io.BytesIO(base64.b64decode(branding.logo_base64)))
        except Exception:
            pass
    if branding.logo_url:
        try:
            img = requests.get(branding.logo_url, timeout=8).content
            return ImageReader(io.BytesIO(img))
        except Exception:
            pass
    return None

def draw_wrapped_text(c, text, x, y, max_width, leading=14, font="Helvetica"):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    c.setFont(font, 11)
    words = text.split()
    line = ""
    while words:
        test = line + ("" if line == "" else " ") + words[0]
        if stringWidth(test, font, 11) <= max_width:
            line = test
            words.pop(0)
        else:
            c.drawString(x, y, line)
            y -= leading
            line = ""
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y

@app.get("/")
def root():
    return {"ok": True, "service": APP_TITLE}

@app.post("/generate-pdf", response_class=Response)
def generate_pdf(payload: Payload):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    bg = HexColor("#F5F1E8")
    c.setFillColor(bg); c.rect(0, 0, W, H, fill=1, stroke=0)
    green = HexColor("#005532")
    gray  = HexColor("#555555")
    logo = _load_logo(payload.branding)
    if logo:
        c.drawImage(logo, W/2-90, H-120, width=180, height=60, mask='auto')
    c.setFillColor(green); c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W/2, H-140, "ANÁLISIS CUÁNTICO DE SALUD")
    c.setFillColor(gray); c.setFont("Helvetica", 11)
    c.drawCentredString(W/2, H-158, "Informe generado mediante tecnología cuántica de VitalHealth Analyzer Pro.")
    c.setFillColor(HexColor("#000000")); c.setFont("Helvetica", 11)
    fecha = payload.fecha_analisis or datetime.now().strftime("%d/%m/%Y")
    datos = f"Paciente: {payload.paciente_nombre}    Edad: {payload.paciente_edad or '-'}    Sexo: {payload.paciente_sexo or '-'}    Fecha: {fecha}"
    c.drawString(40, H-185, datos)
    y = H-210
    def title(t):
        nonlocal y
        c.setFillColor(green); c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, t); y -= 16
        c.setFillColor(HexColor("#000000")); c.setFont("Helvetica", 11)
    def para(txt):
        nonlocal y
        lines = txt.split("\n")
        for ln in lines:
            y = draw_wrapped_text(c, ln, 40, y, W-80)
        y -= 4

    title("Estado general"); para(payload.secciones.estado_general)
    title("Lo bueno"); para(payload.secciones.lo_bueno)
    title("Lo que hay que vigilar"); para(payload.secciones.vigilar)
    title("Lo que está alterado"); para(payload.secciones.alterado)
    title("Cómo se siente actualmente"); para(payload.secciones.como_se_siente)

    if y < 140:
        c.showPage(); c.setFillColor(bg); c.rect(0, 0, W, H, fill=1, stroke=0); y = H-60

    title("Plan de acción VitalHealth (30 días)")
    y = draw_wrapped_text(c, "Hábitos:", 40, y, W-80)
    for h in payload.secciones.plan_30d.habitos:
        y = draw_wrapped_text(c, f"• {h}", 55, y, W-95)
    y -= 6
    y = draw_wrapped_text(c, "Suplementación recomendada:", 40, y, W-80)
    for s in payload.secciones.plan_30d.suplementos:
        line = f"• {s.nombre}: {s.dosis} – {s.duracion_dias} días" + (f". {s.notas}" if s.notas else "")
        y = draw_wrapped_text(c, line, 55, y, W-95)

    title("Proyección de mejora"); para(payload.secciones.proyeccion)
    title("Seguimiento y contacto")
    seg = payload.secciones.seguimiento + f"  |  WhatsApp: {payload.branding.whatsapp}"
    y = draw_wrapped_text(c, seg, 40, y, W-80)

    c.setFillColor(HexColor("#666666")); c.setFont("Helvetica", 8)
    c.drawCentredString(W/2, 28, f"Informe generado mediante tecnología cuántica de VitalHealth Analyzer Pro • {payload.branding.distribuidor}")
    c.drawCentredString(W/2, 16, "Este documento es informativo y no sustituye valoración médica.")
    c.showPage(); c.save()
    pdf_bytes = buf.getvalue()
    filename = f"Informe_Cuantico_{payload.paciente_nombre.replace(' ','_')}_{fecha.replace('/','-')}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "application/pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
