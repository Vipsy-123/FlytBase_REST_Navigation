import paho.mqtt.client as mqtt
import json
import asyncio
import ssl

# Define MQTT broker details
broker = "cloud.flytbase.com"
port = 8883
client = None

# Organisation and Device IDs
org_id = "66682685365372daee8facec" # adityap Organisation
device_id = "66e299a6b649065f39d6d5d8"

# MQTT topic (same as publisher)
topic =  "66682685365372daee8facec/66e299a6b649065f39d6d5d8/navigation/go_to_location/request"   #f"{org_id}/{device_id}/navigation/go_to_location/request"

# Payload data
payload = {
    "timestamp": 12345678.0,
    "job_id": f"Job-{device_id}",
    "data": {
        "latitude": 18.56703161024171,
        "longitude": 73.77140053195978,
        "height": 40.0,
        "speed": 10.0,
        "flight_id": f"{device_id}",
        "rth_height": 50.0
    }
}

# Convert the payload to JSON format
message = json.dumps(payload)

# Callback function to handle received messages
def on_message(client, userdata, message):
    # Decode the message payload
    payload = message.payload.decode("utf-8")
    print(f"Received message on topic {message.topic}: {payload}")
    
if __name__ == "__main__":
    # Initialize and connect the MQTT client
    client = mqtt.Client()
    try:
        client.username_pw_set(username="flytnow-services", password="flytnow-services123")
    except Exception as e :
        print(e)

    # Enable TLS for secure connection
    client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, 
            tls_version=ssl.PROTOCOL_TLS, ciphers=None)
    
    try:
        result = client.connect(broker, port, 60)
        print(f"Connected to broker: {result}")
    except Exception as e:
        print(f"Connection failed: {e}")

    # Publish the message and print detailed results
    result = client.publish(topic, message)
    print(f"Message publish result: {result}")
    
    topic = f"{org_id}/{device_id}/go_to_location_state"
    msg,helo = client.subscribe(topic)
    
    client.on_message = on_message

    client.loop_start()
    
        # Keep the script running to continuously receive messages
    try:
        while True:
            pass  # Keep the program running
    except KeyboardInterrupt:
        print("Exiting...")

    # Stop the loop and disconnect from the broker
    client.loop_stop()
    client.disconnect()
