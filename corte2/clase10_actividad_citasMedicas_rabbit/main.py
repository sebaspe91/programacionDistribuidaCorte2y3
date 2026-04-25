from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import asyncio

from redis_client import r
from producer import enviar_evento
from database import init_db, guardar_cita, cancelar_cita, listar_citas, obtener_cita, listar_logs

# Inicializar BD al arrancar
init_db()

app = FastAPI(
    title="Sistema de Citas Médicas",
    description="Sistema distribuido basado en eventos: FastAPI + Redis + RabbitMQ + SQLite",
    version="6.0.0(ya no se cuantas van)",
)


# ── Modelos ────────────────────────────────────────────────────────────────

class CitaRequest(BaseModel):
    horario: str
    paciente: str = "Paciente Anónimo"


class CitasMultiplesRequest(BaseModel):
    horarios: list[str]
    paciente: str = "Paciente Anónimo"


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.post("/crear_cita", summary="Crear una cita médica")
async def crear_cita(datos: CitaRequest):
    """
    Crea una cita para el horario indicado.
    Usa Redis como lock distribuido para evitar duplicados.
    Publica un evento en RabbitMQ para procesamiento asíncrono.
    """
    horario = datos.horario
    paciente = datos.paciente

    # LOCK con Redis: NX=solo si no existe, EX=expira en 60s
    lock = r.set(f"cita:{horario}", "ocupado", nx=True, ex=60)

    if not lock:
        raise HTTPException(status_code=400, detail=f"El horario '{horario}' ya está ocupado.")

    # Guardar en base de datos
    ok = guardar_cita(horario, paciente)
    if not ok:
        r.delete(f"cita:{horario}")
        raise HTTPException(status_code=400, detail=f"El horario '{horario}' ya existe en la base de datos.")

    print(f"[API] Cita creada para {paciente} en {horario}")

    # Publicar evento a RabbitMQ
    enviar_evento({
        "tipo": "cita_creada",
        "horario": horario,
        "paciente": paciente,
    })

    # Simulación async (no bloqueante)
    await asyncio.sleep(0.1)

    return {
        "mensaje": "Cita creada correctamente",
        "horario": horario,
        "paciente": paciente,
    }


@app.post("/crear_citas_multiples", summary="Crear múltiples citas a la vez")
async def crear_citas_multiples(datos: CitasMultiplesRequest):
    """
    Intenta crear citas para varios horarios en paralelo.
    Devuelve el resultado por cada horario.
    """
    resultados = []

    async def procesar_horario(horario: str):
        lock = r.set(f"cita:{horario}", "ocupado", nx=True, ex=60)
        if not lock:
            resultados.append({"horario": horario, "estado": "ocupado"})
            return

        ok = guardar_cita(horario, datos.paciente)
        if not ok:
            r.delete(f"cita:{horario}")
            resultados.append({"horario": horario, "estado": "duplicado_en_bd"})
            return

        enviar_evento({
            "tipo": "cita_creada",
            "horario": horario,
            "paciente": datos.paciente,
        })
        resultados.append({"horario": horario, "estado": "creada"})

    # Ejecutar todos los horarios en paralelo con asyncio.gather
    await asyncio.gather(*[procesar_horario(h) for h in datos.horarios])

    return {"resultados": resultados}


@app.delete("/cancelar_cita", summary="Cancelar una cita médica")
async def cancelar_cita_endpoint(horario: str = Query(..., description="Horario a cancelar")):
    """
    Cancela una cita activa.
    Libera el lock en Redis y actualiza la BD.
    Publica evento de cancelación en RabbitMQ.
    """
    # Verificar que existe
    cita = obtener_cita(horario)
    if not cita:
        raise HTTPException(status_code=404, detail=f"No existe cita para el horario '{horario}'.")
    if cita["estado"] == "cancelada":
        raise HTTPException(status_code=400, detail=f"La cita '{horario}' ya fue cancelada.")

    # Actualizar BD
    ok = cancelar_cita(horario)
    if not ok:
        raise HTTPException(status_code=500, detail="Error al cancelar la cita.")

    # Liberar lock en Redis
    r.delete(f"cita:{horario}")

    print(f"[API] Cita cancelada: {horario}")

    # Publicar evento
    enviar_evento({
        "tipo": "cita_cancelada",
        "horario": horario,
        "paciente": cita["paciente"],
    })

    await asyncio.sleep(0.1)

    return {"mensaje": f"Cita '{horario}' cancelada correctamente."}


@app.get("/citas", summary="Listar todas las citas")
async def listar_todas():
    return {"citas": listar_citas()}


@app.get("/citas/activas", summary="Listar citas activas")
async def listar_activas():
    return {"citas": listar_citas(solo_activas=True)}


@app.get("/logs", summary="Ver log de eventos procesados")
async def ver_logs():
    return {"logs": listar_logs()}


@app.get("/", summary="Bienvenida")
async def root():
    return {
        "sistema": "Citas Médicas Distribuidas",
        "docs": "/docs",
        "endpoints": [
            "POST /crear_cita",
            "POST /crear_citas_multiples",
            "DELETE /cancelar_cita?horario=...",
            "GET /citas",
            "GET /citas/activas",
            "GET /logs",
        ]
    }