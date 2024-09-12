import asyncio
import paho.mqtt.client as mqtt
import ssl
import json
import requests
import logging
import time

# # Define MQTT broker details
# client = None

# Initialise HTTP Server url

speed = 5.0
rth_height = 50.0

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
    
    # "66e29a6bb649065f39d6d626": [  # Drone 3 waypoints
    #     {"latitude": 18.571623618098293, "longitude": 73.77107082745479, "height": 40},
    #     {"latitude": 18.574813746925578, "longitude": 73.77071147877139, "height": 40},
    #     {"latitude": 18.578906893098814, "longitude": 73.77058598484574, "height": 40},
    #     {"latitude": 18.590177008565323, "longitude": 73.76872543828205, "height": 40}
    # ]
    
}


# Add a new Device here
devices = [ "66e299a6b649065f39d6d5d8", # Sim Drone 1
            "66e29a0db649065f39d6d601", # Sim Drone 2 
            # "66e29a6bb649065f39d6d626" # Sim Drone 3 
        ] 


# Define delays for processing each waypoint for each device
delays = {
            "66e299a6b649065f39d6d5d8" : [2,2,2,2],# Sim Drone 1
            "66e29a0db649065f39d6d601": [2,2,2,2], # Sim Drone 2
            # "66e29a6bb649065f39d6d626" : [2,2,2,2]# Sim Drone 3 
        }

status = {
            "66e299a6b649065f39d6d5d8" : -1,
            "66e29a0db649065f39d6d601": -1,
            # "66e29a6bb649065f39d6d626" : - 1
}

# Configure Logger
logging.basicConfig(
    filename='../logs/navigation_manager.log',  # Log file name
    level=logging.DEBUG,  # Logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Correct format string
    datefmt='%Y-%m-%d %H:%M:%S'
)

class NavigationManager:
    """Class to manage navigation for drones."""
    def __init__(self):
        # Create a Mqtt client instance
        self.client = mqtt.Client()

        try:
            # Client Configurations
            self.client.username_pw_set(username="flytnow-services", password="flytnow-services123")
            # Enable TLS for secure connection
            self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, 
                tls_version=ssl.PROTOCOL_TLS, ciphers=None)
            # Connect to MQTT Broker and keep spinning for Subscriptions
            result = self.client.connect(broker, port, 60)
            self.client.loop_start()
            print(f"Connected to broker: {result}")
        except Exception as e :
            print(e)    
            
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.message_payload = None
        
        # Define MQTT broker details
        self.broker = "cloud-stag.flytbase.com"
        self.port = 8883

        # URLs setup
        # self.org_id = "64f86348220a0c7ac080696d"  # robotics-stag Organization Id 
        self.org_id = "66682685365372daee8facec" # adityap Organisation
        self.base_url = 'http://127.0.0.1:5000'        
    
    def setup_devices(self,devices,waypoints, delays):
        """Set waypoints and delays in one go."""
        
        # Combine waypoints and delays into a single dictionary
        data = {
            "devices" : devices,
            "waypoints": waypoints,
            "delays": delays
        }

        # Post the combined data to the server
        url = f"{self.base_url}/waypoints"  # A single endpoint to handle both waypoints and delays
        response = requests.post(url, json=data)

        # Check the response status
        if response.status_code == 200:
            logging.info("Waypoints and delays set successfully.")
            logging.info(response.json())
        else:
            logging.error(f"Error {response.status_code}: {response.json()}")
                       
    # On connect callback
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        for id,device in enumerate(devices):
            self.client.subscribe(f"{self.org_id}/{device}/go_to_location_state")
            # print(f"Subscribed to topic {self.org_id}/{device}/go_to_location_state")
        print()

    # Define the on_message callback
    def on_message(self,client, userdata, message):
        payload = message.payload.decode("utf-8")  # Decode the message payload
        self.payload = json.loads(payload)  # Convert JSON string to dictionary
        # print(f"- Received message: {self.payload} on topic: {message.topic}")
        
        device_id = message.topic.split('/')[-2]
        # print(device_id)
        # Check for Mission completion status
        if self.payload['state'] == 2 :  # Mission complete , go to next wp
            print("Goto Waypoint completed")
            print()
            logging.info(f"Goto Waypoint completed - {message.topic}")
            status[device_id] = 2
        elif self.payload['state'] == 4:  # Mission Aborted goto same wp
            print("Goto Waypoint Failed")
            logging.warning(f"Goto Waypoint Failed - {message.topic}")
            status[device_id] = 4

    
    def get_waypoint(self,device_id, index):
        """Get the next waypoint for a specific drone with added delay."""
        
        url = f"{self.base_url}/devices/{device_id}/{index}"
        response = requests.get(url)
        if response.status_code == 200 or response.json() is not None:
            logging.info(response.json())
            print(f"Got WP {device_id} {response.json()}")
            print()
            return response.json()
        else:
            logging.error(f"Error {response.status_code}: {response.json()}")
        
    # Call goto location api    
    def goto_waypoint(self,device_id,waypoint):
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
        # print(message)
        try:
            result = self.client.publish(topic, message)
            logging.info(result)
            print("-----------------------------------------------------------------------------------------------")
        except Exception as e:
            print(e)
            logging.error(f"{e} - {result}")
                 
    # Async function to handle waiting for a message
    async def monitor_goto_mission(self, device_id, wp_no, waypoint):
        print(f"Monitoring GoTo for {device_id} at waypoint {wp_no}")
        
        # Wait for the status to change asynchronously
        while True:
            if status[device_id] == 2:
                print(f"GoTo waypoint {wp_no} completed for {device_id}")
                status[device_id] = -1
                break
            elif status[device_id] == 4:
                print(f"GoTo waypoint {wp_no} failed for {device_id}, retrying...")
                status[device_id] = -1
                self.goto_waypoint(device_id, waypoint)  # Retry waypoint
                break
            await asyncio.sleep(1.0)  # Asynchronous sleep to avoid blocking
            
        print("End Monitor Loop for", device_id)
        
        # Check if last waypoint
        if wp_no == len(waypoints[device_id]) - 1:
            self.initiate_RTDS(device_id)

    
    def initiate_RTDS(self,device_id):
        topic = f"{self.org_id}/{device_id}/navigation/rth/request"
        payload = {
            "timestamp": time.time(),
            "job_id": f"Job-{device_id}-RTDS",
            "data": {  }
        }
        message = json.dumps(payload)
        try:
            result = self.client.publish(topic, message)
            logging.info(f"Initiated RTDS for {device_id} - {result}")
            print(f"RTDS Initiated for {device_id}")
            print("--------------------------------------X-----------------------------------------")
        except Exception as e:
            print(e)
            logging.error(e)
    
    async def execute_mission(self, device_id):
        print(f"Executing mission for {device_id}")
        
        for wp_no in range(len(waypoints[device_id])):
            await asyncio.sleep(0.1)
            waypoint = self.get_waypoint(device_id, wp_no)
            
            if waypoint:
                print(f"Drone {device_id} going to waypoint {waypoint}")
                await asyncio.sleep(0.1)
                self.goto_waypoint(device_id, waypoint)
                
                # Monitor mission completion asynchronously
                await self.monitor_goto_mission(device_id, wp_no, waypoint)

        
async def main():
    # Create a list of tasks
    tasks = []
    
    # Iterate over device ids and add tasks to the list
    for device_id in devices:
        tasks.append(nm.execute_mission(device_id))
        
    # tasks.append(nm.execute_mission(devices[0])) # Test a single device
    
    # Use asyncio.gather to run tasks concurrently
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Set MQTT Broker details
    broker = "cloud.flytbase.com"
    port = 8883        
    
    nm = NavigationManager()
    nm.setup_devices(devices,waypoints,delays)
    
    asyncio.run(main())