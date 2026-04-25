import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()
channel.queue_declare(queue='citas')

def callback(ch, method, properties, body):
    print("Mensaje recibido:", body.decode())

channel.basic_consume(
    queue='citas',
    on_message_callback=callback,
    auto_ack=True
)

print("Esperando mensajes...")
channel.start_consuming()