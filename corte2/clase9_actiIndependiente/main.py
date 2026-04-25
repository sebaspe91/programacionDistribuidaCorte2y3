from fastapi import FastAPI, HTTPException
import pika
import redis
import json

app = FastAPI()

# Conexión a Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def enviar_a_cola(mensaje: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()
    channel.queue_declare(queue='citas')
    channel.basic_publish(
        exchange='',
        routing_key='citas',
        body=json.dumps(mensaje)
    )
    connection.close()

@app.post("/citas")
def crear_cita(paciente: str, medico: str, hora: str):
    # Redis: verificar que el médico no tenga cita en esa hora
    lock_key = f"cita:{medico}:{hora}"
    
    if r.get(lock_key):
        raise HTTPException(status_code=400, detail="El médico ya tiene cita en esa hora")
    
    # Reservar el turno en Redis por 1 hora
    r.setex(lock_key, 3600, "ocupado")
    
    # Enviar a la cola para que el worker lo procese
    cita = {"paciente": paciente, "medico": medico, "hora": hora}
    enviar_a_cola(cita)
    
    return {"mensaje": "Cita enviada a procesamiento", "cita": cita}