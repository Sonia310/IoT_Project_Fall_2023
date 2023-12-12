from paho.mqtt import client as mqtt_client
import random

class Card:
    broker = '10.0.0.187'
    port = 1883
    topic = "GetCard"
    client_id = f'subscribe-{random.randint(0, 100)}'
    cardValue = 0

    def __init__(self):
        print(f'Card Sensor Initialized')

    def connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc):
            if rc != 0:
                print("Failed to connect")

        client = mqtt_client.Client(self.client_id)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client

    def subscribe(self, client: mqtt_client):
        def on_message(client, userdata, msg):
            self.cardValue = msg.payload.decode()

        client.subscribe(self.topic)
        client.on_message = on_message

    def run(self):
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_forever()
