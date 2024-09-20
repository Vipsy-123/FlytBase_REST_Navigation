import asyncio
import paho.mqtt.client as mqtt
import ssl
import json
import requests
import logging
from logging.handlers import RotatingFileHandler
import time
import os
import aiohttp

"""
    Navigation Manager :

    This script manages the navigation of multiple drones asynchornously by coordinating their waypoint-based missions and communicating with waypoint server.

"""

# Add a new Device here
devices = ["66eaa6668c006de8ca631657",
           "66eaab808c006de8ca6317df",
           "66eaac6fb649065f39d7f147",
           "66eaad0e8c006de8ca63187d",
           "66eaad4ab649065f39d7f1a9"
           ]

# Define delays for processing each waypoint for each device
delays = [ 2,2,2,2,2,2,2,2,2,2 ]

log_filename = os.path.join('../logs', 'navigation_manager.log')


# Configure rolling file handler 
log_handler = RotatingFileHandler(
    log_filename, maxBytes=1*1024*1024  
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # This sets the date format
    handlers=[
        # log_handler,  
        logging.FileHandler(log_filename),  # Log to a file
        logging.StreamHandler()  # Also log to the console (terminal)
    ]
)

# # Ensure Uvicorn logs are captured
# uvicorn_logger = logging.getLogger("uvicorn")
# uvicorn_logger.setLevel(logging.DEBUG)  # Capture debug-level logs from Uvicorn
# uvicorn_logger.addHandler(logging.FileHandler(log_filename))  # Add file handler

class NavigationManager:
    """Class to manage navigation for drones."""
    
    def __init__(self):
        """
        Initialize MQTT client, connect to broker, and configure callbacks.

        Sets up MQTT client with connection to the broker, handles reconnection
        logic, and initializes various data structures for managing devices and
        waypoints.

        Returns:
            None
        """
        self.client = mqtt.Client()
        self.broker = "cloud.flytbase.com" # Cloud MQTT Broker
        self.port = 8883  # Broker Port  
        # URLs setup
        self.org_id = "66eaa32ee4a2482d2f0d94f8"
        self.base_url = 'http://waypoint_server_container:5000' # For Docker Container Network
        # self.base_url = 'http://localhost:5000' # For LocalHost Network
        
        try:
            # Client Configurations
            self.client.username_pw_set(username="flytnow-services", password="flytnow-services123")
            self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, 
                tls_version=ssl.PROTOCOL_TLS, ciphers=None)
            result = self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            logging.info(f"Success (__init__) : Connected to broker: {result}")
        except Exception as e:
            logging.exception(f"Exception (__init__) : {e}")
            time.sleep(1.0)
            while True: # apply polling Logic 
                try:
                    # Client Configurations
                    logging.info(f"Retrying (__init__) : Connection Failed")
                    time.sleep(5.0)
                    self.client.username_pw_set(username="flytnow-services", password="flytnow-services123")
                    self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, 
                        tls_version=ssl.PROTOCOL_TLS, ciphers=None)
                    result = self.client.connect(self.broker, self.port, 60)
                    self.client.loop_start()
                    logging.info(f"Connected to broker: {result}")
                    
                except Exception as e:
                    logging.exception(f"Exception (__init__) : {e}")

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        self.lat_threshold = 0.001
        self.long_threshold = 0.001 
        
        # URLs setup
        self.org_id = "66eaa32ee4a2482d2f0d94f8"
        self.base_url = 'http://waypoint_server_container:5000' # For Docker Container Network
        # self.base_url = 'http://localhost:5000'
        
        self.waypoint_dict = {}
        self.wp_registry = {}
        self.status = {}
        self.curr_pos = {}
        self.goal_wp = {}

        # Dictionary Initialization
        for device_id in devices:
            # Initialize status dict that maintains current mission status for each device
            self.status[device_id] = 0

            # Initialize current positions with latitude and longitude as -1, height as 40
            self.curr_pos[device_id] = {"latitude": -1, "longitude": -1, "height": 40}

            # Initialize goal waypoints similarly
            self.goal_wp[device_id] = {"latitude": -1, "longitude": -1, "height": 40}
            
            # Initialize waypoint Registry that maintiains goal_wp no. for each device
            self.wp_registry[device_id] = 0
        

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback function triggered upon successful MQTT connection.

        Subscribes to the global position topic for each device.

        Args:
            client (mqtt.Client): MQTT client instance.
            userdata: User-defined data.
            flags: Response flags sent by the broker.
            rc (int): Connection result code.

        Returns:
            None
        """
        logging.info(f"Connected with result code {rc}")
        try:
            for id, device in enumerate(devices):
                self.client.subscribe(f"{self.org_id}/{device}/global_position")
        except Exception as e:
            logging.error(f"Error (on_connect) : Subscription to global_position Failed - {e}")


    async def on_disconnect(self, client, userdata, rc):
        """
        Callback for handling MQTT disconnection with infinite retry loop.

        Attempts to reconnect to the broker if disconnection occurs.

        Args:
            client (mqtt.Client): MQTT client instance.
            userdata: User-defined data.
            rc (int): Disconnection result code.

        Returns:
            None
        """
        logging.warning(f"Warning (MQTT_Connection) : MQTT Disconnected with result code {rc}")
        
        if rc != 0:    
            while True:
                try:
                    logging.info("Attempting to reconnect...")
                    self.client.reconnect()  # Try to reconnect
                    logging.info("Success (MQTT_Connection) : Reconnected successfully")
                    break  # Exit loop once reconnected
                except Exception as e:
                    logging.exception(f"Exception (MQTT_Connection) : Reconnection failed: {e}")
                await asyncio.sleep(5.0)  # Wait before retrying
                    
                    
    def on_message(self, client, userdata, message):
        """
        Callback function triggered when a message is received on a subscribed topic.

        Updates the current position of the device from the received message.

        Args:
            client (mqtt.Client): MQTT client instance.
            userdata: User-defined data.
            message (mqtt.MQTTMessage): The received message.

        Returns:
            None
        """
        payload = message.payload.decode("utf-8")
        self.payload = json.loads(payload)
        device_id = message.topic.split('/')[-2]
        print()
        self.curr_pos[device_id]['latitude'] = self.payload['position']['latitude']
        self.curr_pos[device_id]['longitude'] = self.payload['position']['longitude']


    async def get_waypoint(self, device_id):
        """
        Retrieve the next waypoint for a specific device.

        Sends a GET request to retrieve waypoint data and updates the waypoint
        registry and goal waypoint.

        Args:
            device_id (str): Device ID.

        Returns:
            waypoint_dict: A dictionary containing:
                - `waypoint`: The waypoint data (latitude, longitude, height) or `None` if not found.
                - `waypoint_no`: The number of the waypoint.
                - `error`: Error message if an exception occurs.
        """
        try:
            url = f"{self.base_url}/waypoints/{device_id}"
            logging.info(f"Sent- GET Waypoint request for {device_id}")
            curr_time = time.time()
            
            # Use the aiohttp session to make the request
            async with self.session.get(url) as response:
                self.waypoint_dict = await response.json()
            
            now = time.time() - curr_time
            logging.info(f"Response received after {now} seconds")            
            logging.info(f"Waypoint dict contents: {self.waypoint_dict}")
            if self.waypoint_dict is not None:
                # Ensure the 'waypoint_dict contents exists before accessing it
                if self.waypoint_dict['waypoint'] is not None and self.waypoint_dict['waypoint_no'] is not None:
                    wp_no = self.waypoint_dict['waypoint_no']
                    logging.info(f"Wp Registry {self.wp_registry}")
                    
                    # Check for Duplicate Waypoints
                    if wp_no not in self.wp_registry.values():
                        logging.info(f"Add waypoint to registry {wp_no}")
                        self.wp_registry[device_id] = wp_no
                        logging.info(f"Wp Registry {self.wp_registry}")
                        self.goal_wp[device_id] = self.waypoint_dict['waypoint']
                        logging.info(f"Received - GET Waypoint request for {device_id}")
                        
                        # Update status - if   : wp is successfully obtained and is valid, then increment status to go forward with goto_wp();
                        #                 else : try get_wp in Next iteration
                        self.status[device_id] = (self.status[device_id] + 1) % 3 # status = 1
                        logging.info(f"Status = {self.status[device_id]} for device {device_id}")
                    else:
                        logging.info(f"Duplicate waypoint obtained for device {device_id}... Requesting again ...")
        except Exception as e:
            logging.exception(f"Exception (get_waypoint): {e}")
            await asyncio.sleep(5.0)
                    
                    
    async def goto_waypoint(self, device_id):
        """
        Publish a command to send a device to a specific waypoint.

        Sends a GoTo command via MQTT to move the device to the specified waypoint.

        Args:
            device_id (str): Device ID.

        Returns:
            None
        """
    
        try:
            topic = f"{self.org_id}/{device_id}/navigation/go_to_location/request"
            print(f"waypoint {self.waypoint_dict}")
            self.wp_no = self.waypoint_dict['waypoint_no']
            logging.info(f"Sending GoTo for {device_id} with {self.waypoint_dict}")
            payload = {
                "timestamp": time.time(),
                "job_id": f"Job-{device_id}",
                "data": {
                    "latitude": self.waypoint_dict['waypoint']['latitude'],
                    "longitude": self.waypoint_dict['waypoint']['longitude'],
                    "height": self.waypoint_dict['waypoint']['height'],
                    "speed": 10.0,
                    "flight_id": f"{device_id}+{time.time()}",
                    "rth_height": 40.0
                }
            }
            message = json.dumps(payload)
            result = self.client.publish(topic, message)
            logging.info(f"Success in (goto_waypoint) : Sending GoTo to WP {self.wp_no} for {device_id} , got result : {result}")
            #TODO : check request_response
            # Update status if goto_wp is Successful and go forward with monitor_goto
            self.status[device_id] = (self.status[device_id] + 1) % 3 # status = 2
            logging.info(f"Status = {self.status[device_id]} for device {device_id}")
        except Exception as e:
            logging.exception(f"Exception (goto_waypoint) {e} ")
            await asyncio.sleep(5.0)
                    

    async def monitor_goto_mission(self, device_id):
        """
        Monitor the progress of the 'GoTo' mission for a device asynchronously.

        Checks if the device has reached the goal waypoint within specified thresholds.

        Args:
            device_id (str): Device ID.

        Returns:
            None
        """
        logging.info(f"Monitoring GoTo for {device_id} ")
        try:
            while True:
                logging.info(f"Curr Pose {device_id} - {self.curr_pos[device_id]}")
                logging.info(f"Goal Pose {device_id} - {self.goal_wp[device_id]}")
                logging.info(f"Status ({device_id}) : {self.status[device_id]}")
                print()
                if (abs(self.goal_wp[device_id]['latitude'] - self.curr_pos[device_id]['latitude'])) <= self.lat_threshold and \
                    (abs(self.goal_wp[device_id]['longitude'] - self.curr_pos[device_id]['longitude'])) <= self.long_threshold :
                    print()
                    logging.info(f"!!!!!!!!!!!!!!!!!!!!!!! Success (monitor_goto_mission) !!!!!!!!!!!!!!!!! : GoTo waypoint completed for {device_id}")
                    print()
                    self.wp_registry[device_id] = 0
                    self.status[device_id] = (self.status[device_id] + 1) % 3 # status = 0
                    logging.info(f"Status = {self.status[device_id]} for device {device_id}")
                    break
                await asyncio.sleep(1.0)
        except Exception as e:
            logging.exception(f"Exception (monitor_goto_mission) : {e} for device {device_id}")
            await asyncio.sleep(1.0)

    
    async def initiate_RTDS(self, device_id):
        """
        Send the Return-To-Home (RTH) command to a device.

        Publishes an RTH command via MQTT to return the device to the home position.

        Args:
            device_id (str): Device ID.

        Returns:
            None
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
            logging.info(f"Success (initiate-RTDS) : For {device_id} , got result : {result}")
        except Exception as e:
            logging.exception(f"Exception (initiate_RTDS) : {e}")
            while True:
                try:
                    logging.info(f"Retrying (initiate_RTDS) :  For {device_id} - {result}")
                    result = self.client.publish(topic, message)
                    break
                except Exception as e:
                    logging.exception(f"Exception (initiate_RTDS) : {e}")

    async def execute_mission(self, device_id):
        """
        Execute the navigation mission for each device asynchronously in an infinte loop.

        Handles waypoints retrieval, navigation commands, and status monitoring for the device.

        Args:
            device_id (str): Device ID.

        Returns:
            None
        """
        logging.info(f"Executing mission for {device_id}")
        while True: # Keep Running flows Infinitely
            try:
                if self.status[device_id] == 0:
                    await self.get_waypoint(device_id)  # Get the waypoint
                if self.status[device_id] == 1:
                    await self.goto_waypoint(device_id) # Goto the waypoint
                    logging.info(f"Going to a waypoint for {device_id}.")
                if self.status[device_id] == 2:
                    await self.monitor_goto_mission(device_id) # Monitor Goto 
                    logging.info(f"Success (execute_mission) for {device_id}")
            except Exception as e:
                logging.exception(f"Exception (execute_mission) : {e}")
                await asyncio.sleep(5.0)


    async def execute_main(self):
        """
        Start missions for all devices asynchronously.

        Returns:
            None
        """
        try:
            self.session = aiohttp.ClientSession()  # Initialize aiohttp session
            tasks = [self.execute_mission(device_id) for device_id in devices]
            # tasks = self.execute_mission(devices[0]) # Test a single device
            logging.info("Success (execute_main) : Missions Started")
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logging.exception(f"Exception (execute_mission): Failed to start missions {e}")
            
            # Retry Loop 
            while True: 
                try:
                    self.session = aiohttp.ClientSession()  # Initialize aiohttp session
                    tasks = [self.execute_mission(device_id) for device_id in devices]
                    # tasks = self.execute_mission(devices[0]) # Test a single device
                    logging.info("Retry Success (execute_main) : Missions Started")
                    await asyncio.gather(*tasks)
                except Exception as e:
                    logging.exception(f"Exception (execute_mission): Failed to start missions {e}")
                await asyncio.sleep(5.0)
                        

    async def close(self):
        """Close the aiohttp session."""
        await self.session.close()

if __name__ == "__main__":
    nm = NavigationManager()
    try:
        asyncio.run(nm.execute_main())
    except KeyboardInterrupt as e:
        logging.warning(f"Exception (execute_main): {e} -- Mission Interrupted, going for RTDS")
    
        async def handle_interrupt():
            tasks = [nm.initiate_RTDS(device_id) for device_id in devices]
            await asyncio.gather(*tasks)
            
        asyncio.run(handle_interrupt())
    finally:
        asyncio.run(nm.close())  # Ensure the session is closed when done
