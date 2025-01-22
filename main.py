import time
import dht
from machine import Pin, reset
from umqtt.simple import MQTTClient
import network

# Koneksi ke WiFi
print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')  # SSID dan password jaringan WiFi
while not sta_if.isconnected():
    print(".", end="")
    time.sleep(0.1)
print(" Connected!")
print("Network configuration:", sta_if.ifconfig())

# Inisialisasi sensor DHT22 dan LED
dht_sensor = dht.DHT22(Pin(15))  # Sensor DHT22 PIN
led = Pin(2, Pin.OUT)  # LED PIN

# Konfigurasi MQTT
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "mosquitto.org"
MQTT_TOPIC_SUBSCRIBE = "/UNI514/rico/aktuasi_led"
MQTT_TOPIC_PUBLISH = "/UNI514/rico/data_sensor"

def mqtt_callback(topic, msg):
    print(f"Message received: {topic.decode()} -> {msg.decode()}")
    if msg.decode().lower() == "on":
        print("Turning LED ON")
        led.value(1)
    elif msg.decode().lower() == "off":
        print("Turning LED OFF")
        led.value(0)
    else:
        print(f"Unknown command: {msg.decode()}")

def reconnect(attempt=0):
    global client
    try:
        client.connect()
        client.subscribe(MQTT_TOPIC_SUBSCRIBE)
        print("Reconnected to MQTT broker.")
    except Exception as e:
        print(f"Failed to reconnect: {e}")
        time.sleep(2**attempt)
        reconnect(attempt+1)

try:
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, keepalive=60)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(MQTT_TOPIC_SUBSCRIBE)
    print("Connected to MQTT broker and subscribed to topic.")
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")
    raise

try:
    while True:
        if not sta_if.isconnected():
            print("Reconnecting to WiFi...")
            sta_if.connect('Wokwi-GUEST', '')
            while not sta_if.isconnected():
                print(".", end="")
                time.sleep(1)
            print("Reconnected!")

        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()
            print(f"Temperature: {temp}°C, Humidity: {hum}%")

            payload = f'{{"temperature": {temp}, "humidity": {hum}}}'
            client.publish(MQTT_TOPIC_PUBLISH, payload)
        except Exception as e:
            print(f"Failed to read DHT22: {e}")

        try:
            client.check_msg()
        except OSError as e:
            print("MQTT connection lost, reconnecting...")
            reconnect()

        time.sleep(5)

except KeyboardInterrupt:
    print("Disconnected from MQTT.")
    client.disconnect()