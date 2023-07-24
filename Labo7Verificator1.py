import time
import hashlib
import paho.mqtt.client as mqtt
from encrypt_lib import adcencrypt, adcdecrypt

mqtt_ip = "localhost"

global encseed, verify, token, dec_val, enc_val, token_adres_ver, token_adres_ont, control_hash, ACK_list, system_hash
encseed = "rzebczwwhpnflsyr"
verify = False

token = ""
dec_val = 0
enc_val = 0
token_adres_ver = ""
token_adres_ont = ""
control_hash = ""

verification_hash = hashlib.sha256()

ACK_list = []
aantal_verificatoren = 2
system_hash = hashlib.sha256().hexdigest()

def on_connect(client, userdata, flags, rc):
        print("Verifictor is connected to broker\n")
        client.subscribe("/transact")

def on_message(client, userdata, msg):
        global encseed, verify, token, dec_val, enc_val, token_adres_ver, token_adres_ont, control_hash, system_hash
        if msg.topic == "/transact":
                token = msg.payload.decode('utf-8')
                token_split = token.split(",")
                if token_split[0] == "TX1":
                        token_adres_ver = token_split[0]
                        token_adres_ont = token_split[1]
                        enc_val = token_split[3]
                        dec_val = adcdecrypt(encseed, enc_val)
                        control_hash = token_split[4]
                        verify = True

                        print("Token recieved from sender")
                        print(f"Potmeter value: {dec_val}  Encrypted value: {enc_val}")
                        print(f"Control Hash: {control_hash}\n")
                if token_split[0] == "RX1":
                        system_hash = token_split[2]
        if msg.topic == "/verify":
                ACK_list.append(msg.payload.decode('utf-8'))
                print(ACK_list)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_ip, 1883)
client.loop_start()

while True:
        if verify:
                verification_hash.update(str.encode(f"{system_hash},{token_adres_ver},{token_adres_ont},{dec_val}"))

                print("Checking recieved control hash")
                print(f"Verification hash string: {system_hash},{token_adres_ver},{token_adres_ont},{dec_val}")
                print(f"Verification hash: {verification_hash.hexdigest()}\n")

                client.subscribe("/verify")
                time.sleep(1)

                if verification_hash.hexdigest() == control_hash:
                        client.publish("/verify", "ACK")
                else:
                        client.publish("/verify", "NEG")
                verify = False

        if len(ACK_list) == aantal_verificatoren+1:
                if ACK_list == ["ACK", "ACK", "ACK"]:
                        print("Sending new hash to reciever\n")
                        ACK_list = []

                        s = f"{dec_val},"
                        for i in range(aantal_verificatoren):
                                s += f"VY{i},"
                        s = s[:-1]
                        system_hash = hashlib.sha256(str.encode(s)).hexdigest()
                        client.publish("/systemhash", system_hash)
                else:
                        print("Error... Sending old hash to reciever\n")
                        ACK_list = []
                        client.publish("/systemhash", system_hash)

