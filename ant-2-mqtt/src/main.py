"""
Example of using mulitple devices: a PowerMeter and FitnessEquipment.

Also demos Workout feature of FitnessEquipment, where the device has a thread and sends info to the master.

Refer to subparsers/influx for another example of creating multiple devices at runtime
"""
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.power_meter import PowerMeter, PowerData
from openant.devices.bike_speed_cadence import BikeSpeed, BikeCadence, BikeSpeedData, BikeCadenceData
from openant.devices.heart_rate import HeartRate, HeartRateData
from openant.easy.channel import Channel
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
import json
import logging
logging.basicConfig(level=logging.INFO)

with open("/data/options.json") as f:
    config = json.load(f)


def human_name(name):
    return name.replace("_", " ").capitalize()

def autodiscover_device(device, mqtt_client):
    device_id = device.device_id
    device_name = device.name
    device.topics = {}
    
    if isinstance(device, PowerMeter):
        device.topics.update(publish_autodiscovery(mqtt_client, device_id, device_name, 
                                                   data_field="instantaneous_power",
                                                   units="W", 
                                                   device_class="power",
                                                   value_template="{{ value | int }}"))
        device.topics.update(publish_autodiscovery(mqtt_client, device_id, device_name, 
                                                   data_field="cadence",
                                                   units="rpm",
                                                   value_template="{{ value | int }}"))
    elif isinstance(device, BikeSpeed):
        device.topics.update(publish_autodiscovery(mqtt_client, device_id, device_name, 
                                                   data_field="speed", 
                                                   units="km/h", 
                                                   device_class="speed",
                                                   data_mapping_fn=calculate_speed))
    elif isinstance(device, BikeCadence):
        device.topics.update(publish_autodiscovery(mqtt_client, device_id, device_name, 
                                                   data_field="cadence",
                                                   units="rpm",
                                                   data_mapping_fn=calculate_cadence,
                                                   value_template="{{ value | int }}"))
    elif isinstance(device, HeartRate):
        device.topics.update(publish_autodiscovery(mqtt_client, device_id, device_name, 
                                                   data_field="heart_rate",
                                                   units="bpm", 
                                                   value_template="{{ value | int }}"))

    
def publish_autodiscovery(mqtt_client, device_id, device_name, data_field, units,
                          device_model="unknown", device_manufacturer="unknown",
                          device_class=None, data_mapping_fn=None, 
                          value_template="{{ value | float | round(1) }}"):
    discovery_topic = f"homeassistant/sensor/ant_{device_name}/{device_id}/config"
    logging.info(f"Publishing autodiscovery topic for {device_name} {data_field} to {discovery_topic}") 
    if data_mapping_fn is None:
        #If no custom mapping function, just look up the data field
        data_mapping_fn = lambda data: getattr(data, data_field)

    state_topic = f"ant/{device_name}/{device_id}/{data_field}"
    device_topic_dict = {data_field: {"topic": state_topic,
                                "data_mapping_fn": data_mapping_fn}}
    config_payload = {
        "name": f"{human_name(data_field)}",
        "unique_id": f"ant_{device_name}_{device_id}_{data_field}",
        "state_topic": state_topic,
        "unit_of_measurement": f"{units}",
        "value_template": value_template,
        "state_class": "measurement",
        "device": {
            "name": f"ANT+ {human_name(device_name)}",
            "identifiers": [
                f"ant_{device_name}_{device_id}"
             ],
        "model": device_model,
        "manufacturer": device_manufacturer,
             
             
             },
    }
    if device_class:
        config_payload["device_class"] = device_class
    mqtt_client.publish(discovery_topic, json.dumps(config_payload), retain=False)
    return device_topic_dict


def calculate_speed(self, wheel_circumference_m=config["wheel_circumference_m"]):
    delta_rev_count = (
        self.cumulative_speed_revolution[1] - self.cumulative_speed_revolution[0]
    )
    delta_event_time = self.bike_speed_event_time[1] - self.bike_speed_event_time[0]
    if delta_event_time > 0:
        return (wheel_circumference_m * delta_rev_count) / delta_event_time * 3.6
    else:
        return 0

def calculate_cadence(self):
        delta_rev_count = (
            self.cumulative_cadence_revolution[1]
            - self.cumulative_cadence_revolution[0]
        )
        delta_event_time = (
            self.bike_cadence_event_time[1] - self.bike_cadence_event_time[0]
        )
        if delta_event_time > 0:
            return (60 * delta_rev_count) / delta_event_time
        else:
            return 0



def main(mqtt_client):
    
    node = Node()
    node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
    devices = []

    #Add devices here that we should watch for
    devices.append(PowerMeter(node))
    devices.append(BikeCadence(node))
    devices.append(BikeSpeed(node))
    devices.append(HeartRate(node))

    def on_found(device):
        logging.info("Found ANT+ device")
        logging.info(" --> About to send autodiscovery")
        autodiscover_device(device, mqtt_client)
        
    for d in devices:
        
        d.on_found = lambda d=d: on_found(d)
        
        def on_device_data(page: int, page_name: str, data, d=d):
            #logging.info("on_device_data: device=", d, "data: ", type(data))
            if not(hasattr(d, 'topics')):
                #logging.info(f"Device {d} has not been discovered yet we have data. Skipping.")
                return
            for datafield in d.topics:
                logging.info(f"-> Device {type(d)} should have datafield: {datafield}")
                try:
                    value = d.topics[datafield]["data_mapping_fn"](data)
                    mqtt_client.publish(d.topics[datafield]["topic"], value)
                except:
                    pass


        d.on_device_data = on_device_data
        RX_MODE = Channel.Type.UNIDIRECTIONAL_RECEIVE_ONLY
        d.open_channel(extended=False, channel_type=RX_MODE)
        d.channel.set_search_timeout(60)
    
    try:
        logging.info(f"Starting {devices}, press Ctrl-C to finish")
        mqtt_client.publish('ant2mqtt/starting_ant_node', 1)
        node.start()
        logging.info("Started")
    except KeyboardInterrupt:
        logging.info("Closing ANT+ device...")
    finally:
        logging.info("Closing ANT+ device...")
        for d in devices:
            logging.info(f"Closing device {d}")
            d.close_channel()
        node.stop()




if __name__ == "__main__":
    logging.info("Starting")
    #read config from /data/options.json

    logging.info("Done reading options from config")

    # Define the MQTT broker details
    broker = config["mqtt_broker"] # Replace with your broker's address
    port = config["mqtt_port"]  # Default MQTT port
    client_id = "ant2mqtt"
    

    logging.info(f"About to connect to MQTT broker @ {broker}:{port} with client_id {client_id} as user {config['mqtt_user']}")
    try:
        client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

        #client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)

#        client.tls_insecure_set(True)
#)  # <--- even without arguments

        def on_mqtt_connect(*args):
            logging.info("Connected to MQTT")
            client.publish('ant2mqtt/connected', 1)


        client.on_connect = on_mqtt_connect
        client.username_pw_set(username=config["mqtt_user"], password=config["mqtt_password"])
        
        client.connect(broker, port, 60)
        # Start the loop in a separate thread to handle communication
        client.loop_start()    
        logging.info("Connected to MQTT broker. About to start main loop") 
        main(client)
    except Exception as e:
        raise e
    finally:
        client.loop_stop()
        client.disconnect()

