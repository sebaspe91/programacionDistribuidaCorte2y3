import pika
import asyncio
import json
import sys
import os

# Permite importar database desde el mismo directorio
sys.path.insert(0, os.path.dirname(__file__))
from database import guardar_log

# ID del worker (útil cuando se lanzan varios)
WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "worker-1"


# ── Handlers de eventos ────────────────────────────────────────────────────

async def notificar(mensaje: dict):
    """Simula el envío de una notificación (email/SMS)."""
    await asyncio.sleep(0.5)
    tipo = mensaje.get("tipo", "desconocido")
    horario = mensaje.get("horario", "?")
    paciente = mensaje.get("paciente", "?")

    if tipo == "cita_creada":
        texto = f"Notificación enviada a {paciente}: su cita para {horario} fue confirmada."
    elif tipo == "cita_cancelada":
        texto = f"Notificación enviada a {paciente}: su cita para {horario} fue CANCELADA."
    else:
        texto = f"Notificación genérica: {mensaje}"

    print(f"[{WORKER_ID}][NOTIFICACION] {texto}")
    guardar_log("notificacion", texto)


async def registrar_log(mensaje: dict):
    """Registra el evento en la base de datos."""
    await asyncio.sleep(0.3)
    detalle = json.dumps(mensaje, ensure_ascii=False)
    print(f"[{WORKER_ID}][LOG] Evento registrado: {detalle}")
    guardar_log(mensaje.get("tipo", "evento"), detalle)


async def auditar(mensaje: dict):
    """Simula auditoría del sistema."""
    await asyncio.sleep(0.2)
    print(f"[{WORKER_ID}][AUDITORIA] Auditando evento: {mensaje.get('tipo')} - {mensaje.get('horario')}")
    guardar_log("auditoria", f"Auditado: {mensaje.get('tipo')} horario={mensaje.get('horario')}")


# ── Procesamiento concurrente del evento ───────────────────────────────────

async def procesar_evento(mensaje: dict):
    """
    Ejecuta todas las tareas del evento en PARALELO usando asyncio.gather.
    """
    print(f"[{WORKER_ID}] Procesando evento: {mensaje}")
    await asyncio.gather(
        notificar(mensaje),
        registrar_log(mensaje),
        auditar(mensaje),
    )
    print(f"[{WORKER_ID}] Evento procesado completamente: {mensaje.get('tipo')} - {mensaje.get('horario')}")


# ── Callback de RabbitMQ ───────────────────────────────────────────────────

def callback(ch, method, properties, body):
    try:
        mensaje = json.loads(body.decode())
    except json.JSONDecodeError:
        mensaje = {"tipo": "desconocido", "raw": body.decode()}

    print(f"\n[{WORKER_ID}] Evento recibido: {mensaje}")

    # Ejecutar el procesamiento asíncrono desde el contexto síncrono de pika
    asyncio.run(procesar_evento(mensaje))

    # Confirmar procesamiento a RabbitMQ (manual ack)
    ch.basic_ack(delivery_tag=method.delivery_tag)


# ── Conexión y consumo ─────────────────────────────────────────────────────

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    # Cola durable (misma declaración que en producer)
    channel.queue_declare(queue='eventos', durable=True)

    # Procesar de a 1 mensaje a la vez (fair dispatch entre múltiples workers)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue='eventos',
        on_message_callback=callback,
        auto_ack=False,  # Confirmación manual
    )

    print(f"[{WORKER_ID}] Worker escuchando eventos en cola 'eventos'... (Ctrl+C para salir)")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"\n[{WORKER_ID}] Worker detenido.")
        channel.stop_consuming()

    connection.close()


if __name__ == "__main__":
    main()