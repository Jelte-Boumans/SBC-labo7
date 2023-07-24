
from smbus import SMBus
from encrypt_lib import adcencrypt, adcdecrypt
import RPi.GPIO as GPIO
import time
import hashlib
import paho.mqtt.client as mqtt

GPIO.setmode(GPIO.BCM)
transactie = 16
GPIO.setup(transactie, GPIO.IN)

bus = SMBus(1)

mqtt_ip = "localhost"

encseed = "rzebczwwhpnflsyr"
slave_address = 0x08

token = ""
control_hash = hashlib.sha256()
global system_hash, confirm_reject
system_hash = hashlib.sha256().hexdigest()
confirm_reject = None

aantal_verificatoren = 2

def on_connect(client, userdata, flags, rc):
        print("Sender is connected to broker\n")
        client.subscribe("/transact")

def on_message(client, userdata, msg):
        global system_hash, confirm_reject
        if msg.topic == "/transact":
                token = msg.payload.decode('utf-8')
                token_split = token.split(",")
                if token_split[0] == "RX1":
                        confirm_reject = token_split[1]
                        system_hash = token_split[2]
                        if confirm_reject == "CONFIRM":
                                print(f"Recieved {confirm_reject}, new systemhash: {system_hash}")
                        else:
                                print(f"Recieved {confirm_reject}, old systemhash: {system_hash}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_ip, 1883)
client.loop_start()

while True:
        if GPIO.input(transactie):
                block = bus.read_i2c_block_data(slave_address, 0)
                enc_val = ''.join(chr(i) for i in block)
                dec_val = adcdecrypt(encseed, enc_val)
                control_hash.update(str.encode(f"{system_hash},TX1,RX1,{dec_val}"))
                token = f"TX1,RX1,SEND,{enc_val},{control_hash.hexdigest()},{aantal_verificatoren}"

                print(f"Potmeter value: {dec_val}  Encrypted value: {enc_val}")
                print(f"Control Hash: {control_hash.hexdigest()}")
                print(f"System Hash: {system_hash}")
                print(f"Token: {token}\n")

                client.publish("/transact", token)

                time.sleep(1)
        if confirm_reject in ['CONFIRM', 'REJECT']:
                print("Sending feedback to Arduino\n")
                if confirm_reject == "CONFIRM":
                        bus.write_byte(slave_address, ord('c'))
                elif confirm_reject == "REJECT":
                        bus.write_byte(slave_address, ord('r'))
                confirm_reject = None

GPIO.cleanup()

