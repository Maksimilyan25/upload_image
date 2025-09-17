import pika
import json
import os
from typing import Callable, Any


class RabbitMQClient:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL")
        self.connection = None
        self.channel = None

    def connect(self):
        """Подключиться к RabbitMQ."""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            # Объявляем очередь
            self.channel.queue_declare(queue='images', durable=True)
        except Exception as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            raise

    def disconnect(self):
        """Отключиться от RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def send_message(
        self,
        message: dict,
        queue_name: str = 'images'
    ):
        """Отправить сообщение в очередь."""
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()

            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # сделать сообщение постоянным
                )
            )
        except Exception as e:
            print(f"Ошибка отправки сообщения в RabbitMQ: {e}")
            raise

    def consume_messages(
        self,
        callback: Callable[[dict], Any],
        queue_name: str = 'images'
    ):
        """Потреблять сообщения из очереди."""
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()

            def _callback(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    callback(message)
                    # Подтверждаем получение сообщения
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"Ошибка обработки сообщения: {e}")
                    # Не подтверждаем сообщение, чтобы оно вернулось в очередь
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=True
                    )

            # Настраиваем потребление сообщений
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=_callback
            )

            print("Ожидание сообщений. Для выхода нажмите CTRL+C")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("Остановка потребления сообщений")
            self.channel.stop_consuming()
        except Exception as e:
            print(f"Ошибка потребления сообщений из RabbitMQ: {e}")
            raise
