from fastapi import FastAPI, HTTPException
import redis
import time

app = FastAPI()

# Conexión a Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)


# ==============================
# CREAR CITA (con lock distribuido)
# ==============================
@app.post("/crear_cita/{hora}")
def crear_cita(hora: str):

    clave = f"cita_{hora}"

    # Intentar crear lock con expiración
    lock = r.set(clave, "ocupado", nx=True, ex=30)

    if lock:
        return {
            "mensaje": f"Cita creada para {hora}",
            "ttl": r.ttl(clave)
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"La cita de las {hora} ya está reservada"
        )


# ==============================
# VER CITA
# ==============================
@app.get("/ver_cita/{hora}")
def ver_cita(hora: str):

    clave = f"cita_{hora}"
    estado = r.get(clave) # buscamos la cita con la clave o key

    if estado:
        return {
            "hora": hora,
            "estado": estado,
            "ttl": r.ttl(clave)
        }
    else:
        return {
            "hora": hora,
            "estado": "Disponible"
        }


# ==============================
# CANCELAR CITA
# ==============================
@app.delete("/cancelar_cita/{hora}")
def cancelar_cita(hora: str):

    clave = f"cita_{hora}"
    eliminado = r.delete(clave)

    if eliminado:
        return {"mensaje": f"Cita de las {hora} cancelada"}
    else:
        raise HTTPException(
            status_code=404,
            detail="La cita no existe"
        )


# ==============================
# LISTAR TODAS LAS CITAS
# ==============================
@app.get("/todas_citas")
def todas_citas():

    claves = r.keys("cita_*")
    resultado = []

    for clave in claves:
        resultado.append({
            "cita": clave,
            "estado": r.get(clave),
            "ttl": r.ttl(clave)
        })

    return resultado
