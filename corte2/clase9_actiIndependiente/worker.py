import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()
channel.queue_declare(queue='citas')

def callback(ch, method, properties, body):
    cita = json.loads(body.decode())
    print(f" Procesando cita: Paciente={cita['paciente']} | Médico={cita['medico']} | Hora={cita['hora']}")

channel.basic_consume(
    queue='citas',
    on_message_callback=callback,
    auto_ack=True
)

print("Worker escuchando citas...")
channel.start_consuming()