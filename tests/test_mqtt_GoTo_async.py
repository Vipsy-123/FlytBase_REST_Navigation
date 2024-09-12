import asyncio
import paho.mqtt.client as mqtt
import ssl
import json

# Define the message handler
class MQTTClient:
    def __init__(self, broker, port):
        # Create a Mqtt client instance
        client = mqtt.Client()

        try:
            # Client Configurations
            client.username_pw_set(username="flytnow-services", password="flytnow-services123")
            # Enable TLS for secure connection
            client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, 
                tls_version=ssl.PROTOCOL_TLS, ciphers=None)
            # Connect To Broker
            result = client.connect(broker, port, 60)
            print(f"Connected to broker: {result}")
        except Exception as e :
            print(e)    
            
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        self.event = asyncio.Event()  # To await messages
        self.message_payload = None

        client.connect(broker, port, 60)
        client.loop_start()
        
        # Define MQTT broker details
        self.broker = "cloud-stag.flytbase.com"
        self.port = 8883

        # Organisation and Device IDs
        self.org_id = "64f86348220a0c7ac080696d"
        self.device_id = "66a76584155b1de810e6acf3"
        self.reached = False

    # On connect callback
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe(f"{self.org_id}/{self.device_id}/go_to_location_state")

    # Define the message handler
    def on_message(self,client, userdata, message):
        payload = message.payload.decode("utf-8")  # Decode the message payload
        self.payload = json.loads(payload)  # Convert JSON string to dictionary
        print(f"Received message: {self.payload} on topic: {message.topic}")
        
        # Check for a specific state or message
        if self.payload['state'] == 2:  # Condition to exit
            print("Mission completed, exiting...")
            self.reached = True
            # self.event.set()  # Set the event to allow graceful exit
            client.loop_stop()
            print("SET")

    # Function to wait for the message
    async def wait_for_message(self):
        while True:
            if self.reached == True :
                break
        print("Message Transfer successful")
        return self.payload

        
# Asynchronous task to wait for the message
async def main():
    mqtt_client = MQTTClient("cloud-stag.flytbase.com", 8883)
    print("Waiting for message...")
    msg = asyncio.create_task(mqtt_client.wait_for_message())
    
    print(f"Received END: {msg}")

# Start the asyncio event loop
asyncio.run(main())
