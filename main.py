import xml.etree.ElementTree as ET
import knxnet
import paho.mqtt.client as mqtt
import time

# KNX bus connection details
KNX_GATEWAY_IP = '192.168.190.13'
KNX_GATEWAY_PORT = 3671

# MQTT broker connection details
MQTT_BROKER_IP = '192.168.191.14'
MQTT_BROKER_PORT = 1883

# XML file exported from ETS software project
XML_FILE_PATH = 'exportGrupenadressen.csv.xml'

# Function to handle incoming KNX messages
def handle_knx_message(address, value):
    # Print the received KNX message
    print(f'Received KNX message - Address: {address}, Value: {value}')

    # Send the KNX message to MQTT broker
    mqtt_client.publish(f'knx/{address}', value)

# Load KNX addresses from XML file
def load_knx_addresses(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    namespaces = {'ga': 'http://knx.org/xml/ga-export/01'}
    addresses = []

    for group_range in root.findall('ga:GroupRange', namespaces):
        for group_address in group_range.findall('ga:GroupAddress', namespaces):
            address = group_address.attrib['Address']
            addresses.append(address)

    return addresses

# MQTT connection status
mqtt_connected = False

# MQTT on_connect event callback
def on_mqtt_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print('Connected to MQTT broker')
    else:
        print(f'Failed to connect to MQTT broker with error code: {rc}')

# MQTT on_disconnect event callback
def on_mqtt_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    print('Disconnected from MQTT broker')

# Connect to the MQTT broker
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_disconnect = on_mqtt_disconnect
mqtt_client.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT)

# KNX connection status
knx_connected = False

# Reconnect to KNX bus
def reconnect_knx():
    global knx_connected
    print('Reconnecting to KNX bus...')
    try:
        gateway.connect(KNX_GATEWAY_IP, KNX_GATEWAY_PORT)
        knx_connected = True
        print('Reconnected to KNX bus')
    except Exception as e:
        print(f'Failed to reconnect to KNX bus: {str(e)}')

# Connect to the KNX bus gateway
gateway = knxnet.KNXnetIPRouting()

# Loop to handle MQTT events and reconnect if necessary
while True:
    mqtt_client.loop_start()
    if mqtt_connected:
        # Load KNX addresses from XML file
        knx_addresses = load_knx_addresses(XML_FILE_PATH)

        # Connect to the KNX bus gateway
        try:
            gateway.connect(KNX_GATEWAY_IP, KNX_GATEWAY_PORT)
            knx_connected = True
            print('Connected to KNX bus')
        except Exception as e:
            print(f'Failed to connect to KNX bus: {str(e)}')
        
        if knx_connected:
            # Subscribe to KNX group addresses
            for address in knx_addresses:
                gateway.group_read(address, handle_knx_message)

            # Keep the program running to receive KNX messages
            while mqtt_connected and knx_connected:
                gateway.process_comms()
                time.sleep(0.1)
