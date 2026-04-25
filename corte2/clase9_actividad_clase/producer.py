import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()
channel.queue_declare(queue='citas')

channel.basic_publish(
    exchange='',
    routing_key='citas',
    body='Nueva cita creada'
)

print("Mensaje enviado a la cola")
connection.close()