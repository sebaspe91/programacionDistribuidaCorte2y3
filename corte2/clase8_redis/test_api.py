
from fastapi import FastAPI, HTTPException
import redis

app = FastAPI()

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.post("/crear_cita")
def crear_cita():
    lock = r.set("cita_10am", "ocupado", nx=True, ex=10)

    if not lock:
        raise HTTPException(
            status_code=400,
            detail="Cita ya reservada"
        )
    
    return {"mensaje" : "Cita creada"}



# CODIGO CORREGIDO POR IA
# from fastapi import FastAPI, HTTPException
# import redis

# app = FastAPI()

# # Conexión a Redis
# r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# @app.post("/crear_cita/{hora}")
# def crear_cita(hora: str):
#     lock_key = f"cita_{hora}"
#     # nx=True: solo crea si no existe
#     # ex=300: expira automáticamente después de 5 minutos
#     reservada = r.set(lock_key, "ocupado", nx=True, ex=10)
    
#     if not reservada:
#         raise HTTPException(
#             status_code=400,
#             detail=f"La cita para las {hora} ya está reservada"
#         )
    
#     return {"mensaje": f"Cita reservada para las {hora}"}

# @app.get("/verificar_cita/{hora}")
# def verificar_cita(hora: str):
#     existe = r.exists(f"cita_{hora}")
#     if existe:
#         return {"disponible": False, "mensaje": "Ya está reservada"}
#     return {"disponible": True, "mensaje": "Está disponible"}

# @app.get("/")
# def root():
#     return {"mensaje": "API de citas con Redis funcionando"}