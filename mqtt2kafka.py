from kafka import KafkaProducer
import paho.mqtt.client as mqtt
from json import dumps

mqtt_topic = "test"
kafka_topic = "invoice_kaf"

def sendmessage2kafka(messages):
    print("Sending message to Kafka: " + messages)
    #producer = KafkaProducer(bootstrap_servers=kafka_broker)
    producer.send(kafka_topic, messages)
    #producer.flush()


def mqtt2kafka():
    print("MQTT to KAFKA")
    client = mqtt.Client(client_id=None)

    on_connect = lambda client, userdata, flags, rc: client.subscribe(mqtt_topic)
    client.on_connect = on_connect
    
    on_message = lambda client, userdata, msg: sendmessage2kafka(msg.payload.decode())
    client.on_message = on_message

    on_disconnect = lambda client, userdata, rc: print("Disconnected from MQTT broker", client, userdata, flags, rc)
    client.on_disconnect = on_disconnect

    client.connect("192.168.136.253", 1883, 60)
    client.loop_forever()

if __name__ == '__main__':
    producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda x: dumps(x).encode('utf-8'))
    mqtt2kafka()