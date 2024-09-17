import asyncio
import paho.mqtt.client as mqtt
import ssl
import json
import requests
import logging
import time
import os

# Initialize variables 
speed = 5.0
rth_height = 50.0
broker = "cloud.flytbase.com" # Cloud MQTT Broker
port = 8883  # Broker Port  

# Define waypoints for Device
waypoints = {
    "66e299a6b649065f39d6d5d8": [  # Drone 1 waypoints
        {"latitude": 18.567401186240225, "longitude": 73.77164156403151, "height": 30},
        {"latitude": 18.56789888415445, "longitude": 73.77173236517294, "height": 30},
        {"latitude": 18.567978836883235, "longitude": 73.7721740773291, "height": 30},
        {"latitude": 18.56754219638799, "longitude": 73.77218376137297, "height": 30}
    ],
    "66e29a0db649065f39d6d601": [  # Drone 2 waypoints
        {"latitude": 18.567188585855867, "longitude": 73.7724513709704, "height": 35},
        {"latitude": 18.567140020748337, "longitude": 73.77315097993511, "height": 35},
        {"latitude": 18.56595551156461, "longitude": 73.7728491523852, "height": 35},
        {"latitude": 18.566126212943733, "longitude": 73.77210984507171, "height": 35}
    ]
}

# Add a new Device here
devices = ["66e299a6b649065f39d6d5d8", "66e29a0db649065f39d6d601"]

# Define delays for processing each waypoint for each device
delays = {
    "66e299a6b649065f39d6d5d8": [2, 2, 2, 2],
    "66e29a0db649065f39d6d601": [2, 2, 2, 2]
}

status = {
    "66e299a6b649065f39d6d5d8": -1,
    "66e29a0db649065f39d6d601": -1,
}

log_file_path = os.path.join('/app/logs', 'navigation_manager.log')

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),  # Log to a file
        logging.StreamHandler()  # Also log to the console (terminal)
    ]
)

class NavigationManager:
    """Class to manage navigation for drones."""
    def __init__(self):
        """Initialize MQTT client, connect to broker, and configure callbacks."""
        self.client = mqtt.Client()

        try:
            # Client Configurations
            self.client.username_pw_set(username="flytnow-services", password="flytnow-services123")
            self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, 
                tls_version=ssl.PROTOCOL_TLS, ciphers=None)
            result = self.client.connect(broker, port, 60)
            self.client.loop_start()
            print(f"Connected to broker: {result}")
        except Exception as e:
            print(e)
            while True:# TODO : apply polling Logic 
                pass

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.message_payload = None

        # URLs setup
        self.org_id = "66682685365372daee8facec"
        self.base_url = 'http://waypoint_server:5000'


    def setup_devices(self, devices, waypoints, delays):
        """
        Set waypoints and delays for multiple devices.
        
        :param devices: List of device IDs
        :param waypoints: Dictionary of waypoints for each device
        :param delays: Dictionary of delays for each device at waypoints
        """
        data = {
            "devices": devices,
            "waypoints": waypoints,
            "delays": delays
        }

        url = f"{self.base_url}/waypoints"
        response = requests.post(url, json=data)

        if response.status_code == 200:
            logging.info("Waypoints and delays set successfully.")
            logging.info(response.json())
        else:
            logging.error(f"Error {response.status_code}: {response.json()}")

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback function triggered upon successful MQTT connection.
        
        :param client: MQTT client instance
        :param userdata: User-defined data
        :param flags: Response flags sent by the broker
        :param rc: Connection result
        """
        print(f"Connected with result code {rc}")
        for id, device in enumerate(devices):
            self.client.subscribe(f"{self.org_id}/{device}/go_to_location_state")
        print()

    def on_message(self, client, userdata, message):
        """
        Callback function triggered when a message is received on a subscribed topic.
        
        :param client: MQTT client instance
        :param userdata: User-defined data
        :param message: The received message
        """
        payload = message.payload.decode("utf-8")
        self.payload = json.loads(payload)
        device_id = message.topic.split('/')[-2]

        if self.payload['state'] == 2:
            print("Goto Waypoint completed")
            logging.info(f"Goto Waypoint completed - {message.topic}")
            status[device_id] = 2
        elif self.payload['state'] == 4:
            print("Goto Waypoint Failed")
            logging.warning(f"Goto Waypoint Failed - {message.topic}")
            status[device_id] = 4

    def get_waypoint(self, device_id, index):
        """
        Retrieve the next waypoint for a specific device.
        
        :param device_id: Device ID
        :param index: Waypoint index
        :return: Waypoint data
        """
        url = f"{self.base_url}/devices/{device_id}/{index}"
        response = requests.get(url)

        if response.status_code == 200 or response.json() is not None:
            logging.info(response.json())
            print(f"Got WP {device_id} {response.json()}")
            return response.json()
        else:
            logging.error(f"Error {response.status_code}: {response.json()}")

    def goto_waypoint(self, device_id, waypoint):
        """
        Publish a command to send a device to a specific waypoint.
        
        :param device_id: Device ID
        :param waypoint: Waypoint data (latitude, longitude, height)
        """
        topic = f"{self.org_id}/{device_id}/navigation/go_to_location/request"
        payload = {
            "timestamp": time.time(),
            "job_id": f"Job-{device_id}",
            "data": {
                "latitude": waypoint['waypoint']['latitude'],
                "longitude": waypoint['waypoint']['longitude'],
                "height": waypoint['waypoint']['height'],
                "speed": 2.0,
                "flight_id": f"{device_id}+{time.time()}",
                "rth_height": 40.0
            }
        }

        message = json.dumps(payload)
        print(f"Sending GoTo {device_id}")

        try:
            result = self.client.publish(topic, message)
            logging.info(result)
        except Exception as e:
            print(e)
            logging.error(f"{e} - {result}")

    async def monitor_goto_mission(self, device_id, wp_no, waypoint):
        """
        Monitor the progress of the 'GoTo' mission for a device asynchronously.
        
        :param device_id: Device ID
        :param wp_no: Waypoint number
        :param waypoint: Waypoint data
        """
        print(f"Monitoring GoTo for {device_id} at waypoint {wp_no}")

        while True:
            if status[device_id] == 2:
                print(f"GoTo waypoint {wp_no} completed for {device_id}")
                status[device_id] = -1
                break
            elif status[device_id] == 4:
                print(f"GoTo waypoint {wp_no} failed for {device_id}, retrying...")
                status[device_id] = -1
                self.goto_waypoint(device_id, waypoint)
                break
            await asyncio.sleep(1.0)

        if wp_no == len(waypoints[device_id]) - 1:
            self.initiate_RTDS(device_id)

    def initiate_RTDS(self, device_id):
        """
        Send the Return-To-Home (RTH) command to a device.
        
        :param device_id: Device ID
        """
        topic = f"{self.org_id}/{device_id}/navigation/rth/request"
        payload = {
            "timestamp": time.time(),
            "job_id": f"Job-{device_id}-RTDS",
            "data": {}
        }
        message = json.dumps(payload)

        try:
            result = self.client.publish(topic, message)
            logging.info(f"Initiated RTDS for {device_id} - {result}")
            print(f"RTDS Initiated for {device_id}")
        except Exception as e:
            print(e)
            logging.error(e)

    async def execute_mission(self, device_id):
        """
        Execute the navigation mission for a device asynchronously, handling waypoints and status monitoring.
        
        :param device_id: Device ID
        """
        print(f"Executing mission for {device_id}")

        for wp_no, delay in enumerate(delays[device_id]):
            waypoint = self.get_waypoint(device_id, wp_no)

            print(f"Going to waypoint {wp_no} for {device_id} after delay {delay}")
            await asyncio.sleep(delay)
            self.goto_waypoint(device_id, waypoint)
            await self.monitor_goto_mission(device_id, wp_no, waypoint)

    async def execute(self):
        """
        Start missions for all devices asynchronously, coordinating their waypoint navigation.
        """
        tasks = [self.execute_mission(device_id) for device_id in devices]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    nm = NavigationManager()
    nm.setup_devices(devices, waypoints, delays)
    asyncio.run(nm.execute())
