import pika
import json


def enviar_evento(mensaje: dict):
    """
    Publica un evento (dict) en la cola 'eventos' de RabbitMQ.
    El mensaje se serializa como JSON.
    """
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    # Declarar cola durable para que sobreviva reinicios
    channel.queue_declare(queue='eventos', durable=True)

    channel.basic_publish(
        exchange='',
        routing_key='eventos',
        body=json.dumps(mensaje),
        properties=pika.BasicProperties(
            delivery_mode=2,  # mensaje persistente
        )
    )

    print(f"[PRODUCER] Evento enviado: {mensaje}")
    connection.close()