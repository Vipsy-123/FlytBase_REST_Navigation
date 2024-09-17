import asyncio
import paho.mqtt.client as mqtt
import ssl
import json
import requests
import logging
import time
import os
import aiohttp

# Add a new Device here
devices = ["66e299a6b649065f39d6d5d8",
           "66e29a0db649065f39d6d601",
           "66e29a6bb649065f39d6d626",
           "66e9c311b649065f39d7d603",
           "66e9c382b649065f39d7d64c"
           ]

# Define delays for processing each waypoint for each device
delays = [ 2,2,2,2,2,2,2,2,2,2 ]

log_filename = os.path.join(os.path.dirname(__file__), "../logs/navigation_manager.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # This sets the date format
    handlers=[
        logging.FileHandler(log_filename),  # Log to a file
        logging.StreamHandler()  # Also log to the console (terminal)
    ]
)

class NavigationManager:
    """Class to manage navigation for drones."""
    
    def __init__(self):
        """Initialize MQTT client, connect to broker, and configure callbacks."""
        self.client = mqtt.Client()
        self.broker = "cloud.flytbase.com" # Cloud MQTT Broker
        self.port = 8883  # Broker Port  
        
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
            while True: # apply polling Logic 
                try:
                    # Client Configurations
                    logging.info(f"Retrying (__init__): {result}")
                    time.sleep(5.0)
                    self.client.username_pw_set(username="flytnow-services", password="flytnow-services123")
                    self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, 
                        tls_version=ssl.PROTOCOL_TLS, ciphers=None)
                    result = self.client.connect(self.broker, self.port, 60)
                    self.client.loop_start()
                    logging.info(f"Connected to broker: {result}")
                    
                except Exception as e:
                    # print("Here")
                    logging.exception(f"Exception (__init__) : {e}")

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.message_payload = None
        self.waypoint_dict = {}
        self.lat_threshold = 0.0001
        self.long_threshold = 0.0001
        self.wp_registry = []
        
        self.status = {}
        self.curr_pos = {}
        self.goal_wp = {}

        for device_id in devices:
            # Initialize all self.statuses to -1
            self.status[device_id] = -1

            # Initialize current positions with latitude and longitude as -1, height as 30
            self.curr_pos[device_id] = {"latitude": -1, "longitude": -1, "height": 30}

            # Initialize goal waypoints similarly
            self.goal_wp[device_id] = {"latitude": -1, "longitude": -1, "height": 30}
            
        # URLs setup
        self.org_id = "66682685365372daee8facec"
        self.base_url = 'http://127.0.0.1:5000'


    def on_connect(self, client, userdata, flags, rc):
        """
        Callback function triggered upon successful MQTT connection.
        
        :param client: MQTT client instance
        :param userdata: User-defined data
        :param flags: Response flags sent by the broker
        :param rc: Connection result
        """
        logging.info(f"Connected with result code {rc}")
        try:
            for id, device in enumerate(devices):
                self.client.subscribe(f"{self.org_id}/{device}/global_position")
        except Exception as e:
            logging.error(f"Error (on_connect) : Subscription to global_position Failed - {e}")


    def on_disconnect(self, client, userdata, rc):
        """Callback for handling MQTT disconnection with infinite retry loop."""
        logging.warning(f"Warning (MQTT_Connection) : MQTT Disconnected with result code {rc}")
        
        if rc != 0:
            delay = 5 # delay between retries (in seconds)           
            while True:
                try:
                    logging.info("Attempting to reconnect...")
                    self.client.reconnect()  # Try to reconnect
                    logging.info("Success (MQTT_Connection) : Reconnected successfully")
                    break  # Exit loop once reconnected
                except Exception as e:
                    logging.exception(f"Exception (MQTT_Connection) : Reconnection failed: {e}")
                    time.sleep(delay)  # Wait before retrying
                    
                    
    def on_message(self, client, userdata, message):
        """ TODO : Implement monitoring Logic using global_position_api
        Callback function triggered when a message is received on a subscribed topic.
        
        :param client: MQTT client instance
        :param userdata: User-defined data
        :param message: The received message
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
        
        :param device_id: Device ID
        :return: Waypoint data
        """
        try:
            url = f"{self.base_url}/waypoints"
            logging.info(f"Sent- GET Waypoint request for {device_id}")
            curr_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    await response.json()
            
                
            now = time.time() - curr_time
            logging.info(f" Response received after {now} seconds")
            
            self.waypoint_dict = await response.json()
            if self.waypoint_dict is not None:
                # Log the contents of self.waypoint_dict to debug the structure
                logging.info(f"Waypoint dict contents: {self.waypoint_dict}")
                
                # if self.waypoint_dict['waypoint_no'] not in self.wp_registry:
                #     self.wp_registry.append(self.waypoint_dict['waypoint_no'])
                #     print(self.wp_registry)
                #     logging.info(f"Added waypoint {self.waypoint_dict['waypoint_no']} in wp_registry")
                # else:
                #     logging.error(f"Duplicate waypoint received: {self.waypoint_dict['waypoint_no']}")
                #     self.status['device_id'] = -1 # Restart status
                    # raise ValueError(f"Duplicate waypoint: {self.waypoint_dict['waypoint_no']} has already been processed")
                    # return
                # Ensure the 'waypoint' key exists before accessing it
                if 'waypoint' in self.waypoint_dict:
                    self.goal_wp[device_id] = self.waypoint_dict['waypoint']
                    logging.info(f"Received - GET Waypoint request for {device_id}")
                else:
                    logging.error(f"Key 'waypoint' not found in waypoint_dict for {device_id}")

        except Exception as e:
            logging.exception(f"Exception (get_waypoint): {e}")
            while True:
                try:
                    url = f"{self.base_url}/waypoints"
                    logging.info(f"Sent- GET Waypoint request for {device_id}")
                    curr_time = time.time()
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            await response.json()
                            
                    now = time.time() - curr_time
                    logging.info(f" Response received after {now} seconds")
                    
                    self.waypoint_dict = await response.json()
                    self.goal_wp[device_id] = self.waypoint_dict['waypoint']        
                    logging.info(f"Received - GET Waypoint request for {device_id}")
                except Exception as e:
                    logging.exception(f"Exception (get_waypoint): {e}")
                    
                    
    async def goto_waypoint(self, device_id):
        """
        Publish a command to send a device to a specific waypoint.
        
        :param device_id: Device ID
        :param waypoint: Waypoint data (latitude, longitude, height)
        """
    
        try:
            topic = f"{self.org_id}/{device_id}/navigation/go_to_location/request"
            print(f"waypoint {self.waypoint_dict}")
            wp_no = self.waypoint_dict['waypoint_no']
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
            logging.info(f"Success in (goto_waypoint) : Sending GoTo to WP {wp_no} for {device_id} , got result : {result}")
        except Exception as e:
            logging.exception(f"Exception (goto_waypoint) {e} ")
            while True:
                try:
                    if self.waypoint_dict is not None and device_id is not None:
                        topic = f"{self.org_id}/{device_id}/navigation/go_to_location/request"
                        payload = {
                            "timestamp": time.time(),
                            "job_id": f"Job-{device_id}",
                            "data": {
                                "latitude": self.waypoint_dict['waypoint']['latitude'],
                                "longitude": self.waypoint_dict['waypoint']['longitude'],
                                "height": self.waypoint_dict['waypoint']['height'],
                                "speed": 2.0,
                                "flight_id": f"{device_id}+{time.time()}",
                                "rth_height": 40.0
                            }
                        }

                        message = json.dumps(payload)
                        logging.info(f"Retrying (goto_waypoint) : For {device_id}")
                        result = self.client.publish(topic, message)
                        logging.info(result)
                        break
                except Exception as e:
                    logging.exception(f"Exception (goto_waypoint) : {e}")
                    

    async def monitor_goto_mission(self, device_id):
        """ # TODO : To implement if Drone hasnt moved since last 30 seconds meaning , Drone Docke is not active , handle that exception as well
        Monitor the progress of the 'GoTo' mission for a device asynchronously.
        
        :param device_id: Device ID
        :param wp_no: Waypoint number
        :param waypoint: Waypoint data
        """
        logging.info(f"Monitoring GoTo for {device_id} ")
        try:
            while True:
                logging.info(f"Curr Pose {device_id} - {self.curr_pos[device_id]}")
                logging.info(f"Goal Pose {device_id} - {self.goal_wp[device_id]}")
                logging.info(f"self.status {self.status[device_id]}")
                print()
                if (abs(self.goal_wp[device_id]['latitude'] - self.curr_pos[device_id]['latitude'])) <= self.lat_threshold and \
                    (abs(self.goal_wp[device_id]['longitude'] - self.curr_pos[device_id]['longitude'])) <= self.long_threshold :
                    # logging.info(f"Goto Waypoint completed - {message.topic}")
                    self.status[device_id] = 2
                
                if self.status[device_id] == 2:
                    print()
                    logging.info(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! SUCCESS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! : GoTo waypoint completed for {device_id}")
                    print()
                    self.status[device_id] = -1
                    # logging.info(f"Setting self.status false : {self.status[device_id]}")
                    # if self.waypoint_dict['waypoint_no'] in self.wp_registry:
                    #     self.wp_registry.remove(self.waypoint_dict['waypoint_no'])
                    #     logging.info(f"Waypoint {self.waypoint_dict['waypoint_no']} removed from registry after mission completion.")
                    # else:
                    #     logging.error(f"Waypoint {self.waypoint_dict['waypoint_no']} not found in registry when trying to remove it.")
                    break
                await asyncio.sleep(2.0)
        except KeyboardInterrupt as e:
            logging.warning(f"Warning (execute_mission) : {e} - Initiating RTDS for {device_id}")
            await self.initiate_RTDS(device_id)
        except Exception as e:
            logging.exception(f"Exception (monitor_goto_mission) : {e} for device {device_id}")
            try:
                while True:
                    logging.info(f"Curr Pose {device_id} - {self.curr_pos[device_id]}")
                    logging.info(f"Goal Pose {device_id} - {self.goal_wp[device_id]}")
                    logging.info(f"self.status {self.status[device_id]}")
                    print()
                    if (abs(self.goal_wp[device_id]['latitude'] - self.curr_pos[device_id]['latitude'])) <= self.lat_threshold and \
                        (abs(self.goal_wp[device_id]['longitude'] - self.curr_pos[device_id]['longitude'])) <= self.long_threshold :
                        # logging.info(f"Goto Waypoint completed - {message.topic}")
                        self.status[device_id] = 2
                    
                    if self.status[device_id] == 2:
                        print()
                        logging.info(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! SUCCESS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! : GoTo waypoint completed for {device_id}")
                        print()
                        self.status[device_id] = -1
                        # logging.info(f"Setting self.status false : {self.status[device_id]}")
                        # self.wp_registry.remove(self.waypoint_dict['waypoint_no'])
                        # logging.info(self.wp_registry)
                        break
                    await asyncio.sleep(2.0)
            except KeyboardInterrupt as e:
                logging.warning(f"Warning (execute_mission) : {e} - Initiating RTDS for {device_id}")
                await self.initiate_RTDS(device_id)
            except Exception as e:
                logging.exception(f"Exception (monitor_goto_mission) : {e} for device {device_id}")



    async def initiate_RTDS(self, device_id):
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
        Execute the navigation mission for a device asynchronously, handling waypoints and self.status monitoring.
        
        :param device_id: Device ID
        """
        logging.info(f"Executing mission for {device_id}")
        while True: # Keep Running Infinitely
            try:
                # await asyncio.sleep(0.1)
                await self.get_waypoint(device_id)  # Get the waypoint
                await self.goto_waypoint(device_id)
                logging.info(f"Going to a waypoint for {device_id}.")
                await self.monitor_goto_mission(device_id)
                logging.info(f"Success (execute_mission) for {device_id}")
            except KeyboardInterrupt as e:
                logging.warning(f"Warning (execute_mission) : {e} - Initiating RTDS for {device_id}")
                await self.initiate_RTDS(device_id)
                break
            except Exception as e:
                logging.exception(f"Exception (execute_mission) : {e}")
                # while True:  # Loop to keep polling in cases when Exception is not yet resolved
                try:
                    logging.info(f"Retrying (execute_mission) : ")
                    self.waypoint_dict = await self.get_waypoint(device_id)
                    await self.goto_waypoint(device_id)
                    logging.info(f"Going to a waypoint for {device_id}.")
                    await self.monitor_goto_mission(device_id)
                    logging.info(f"Success (execute_mission) for {device_id}")
                except KeyboardInterrupt as e:
                    logging.warning(f"Warning (execute_mission) : {e} - Initiating RTDS for {device_id}")
                    await self.initiate_RTDS(device_id)
                    break
                except Exception as e:
                    logging.exception(f"Exception (execute_mission) : {e}")
                await asyncio.sleep(5.0)


    async def execute_main(self):
        """
        Start missions for all devices asynchronously, coordinating their waypoint navigation.
        """
        try:
            self.session = aiohttp.ClientSession()  # Initialize aiohttp session
            tasks = [self.execute_mission(device_id) for device_id in devices]
            # tasks = self.execute_mission(devices[0]) # Test a single device
            await asyncio.gather(*tasks)
        except KeyboardInterrupt :
            logging.warning("Exception (execute_main) : Mission Interrupted going for RTDS")
            tasks = [self.initiate_RTDS(device_id) for device_id in devices]
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    nm = NavigationManager()
    # nm.setup_devices(devices, waypoints, delays)
    asyncio.run(nm.execute_main())
