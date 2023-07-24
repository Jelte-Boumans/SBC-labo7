import time
import hashlib
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from encrypt_lib import adcencrypt, adcdecrypt

GPIO.setmode(GPIO.BCM)
servo = 17
confirm = 20
reject = 21
GPIO.setup(servo, GPIO.OUT)
pwm_servo = GPIO.PWM(servo, 50)
GPIO.setup(confirm, GPIO.IN)
GPIO.setup(reject, GPIO.IN)

mqtt_ip = "localhost"

global encseed, verify, token, dec_val, enc_val, token_adres_ver, token_adres_ont, control_hash, system_hash
encseed = "rzebczwwhpnflsyr"
token = ""
dec_val = 0
enc_val = 0
token_adres_ver = ""
token_adres_ont = ""
control_hash = ""
confirm_reject = None

verification_hash = hashlib.sha256()
syshash_list = []
old_system_hash = hashlib.sha256().hexdigest()
system_hash = hashlib.sha256().hexdigest()
aantal_verificatoren = 2
ACK_list = []
verify = False

duty_cycle = 5.0

pwm_servo.start(duty_cycle)

def on_connect(client, userdata, flags, rc):
        print("Reciever is connected to broker\n")
        client.subscribe("/transact")
        client.subscribe("/systemhash")

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
        if msg.topic == "/systemhash":
                syshash_list.append(msg.payload.decode('utf-8'))
                print(syshash_list)
        if msg.topic == "/verify":
                ACK_list.append(msg.payload.decode('utf-8'))
                print(ACK_list)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_ip, 1883)
client.loop_start()

while True:
        # Verification
        if verify:
                verification_hash.update(str.encode(f"{system_hash},{token_adres_ver},{token_adres_ont},{dec_val}"))

                print("Checking recieved control hash")
                print(f"Verification hash: {verification_hash.hexdigest()}\n")

                client.subscribe("/verify")
                time.sleep(3)

                if verification_hash.hexdigest() == control_hash:
                        client.publish("/verify", "ACK")
                else:
                        client.publish("/verify", "NEG")
                verify = False

        if len(ACK_list) == aantal_verificatoren+1:
                if ACK_list == ["ACK", "ACK", "ACK"]:
                        print("Sending new hash to reciever\n")
                        ACK_list = []

                        old_system_hash = system_hash
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

        # Reciever
        if len(syshash_list) == aantal_verificatoren+1:
                if len(set(syshash_list)) == 1:
                        print("No verificator error, turning the servo\n")
                        duty_cycle = ((round(dec_val / (1023*10), 2)*100)/2)+5
                        print(f"Potmeter value: {dec_val}  Encrypted value: {enc_val}")
                        print(f"DutyCycle: {duty_cycle}%")
                        pwm_servo.ChangeDutyCycle(duty_cycle)
                        time.sleep(1)

                        print("Now press confirm to confirm or reject to reject the incoming data.")
                        while confirm_reject == None:
                                if GPIO.input(confirm):
                                        confirm_reject = True
                                elif GPIO.input(reject):
                                        confirm_reject = False
                        if confirm_reject:
                                print("Confirmed\n")
                                client.publish("/transact", f"RX1,CONFIRM,{system_hash}")
                        else:
                                print("Rejected\n")
                                client.publish("/transact", f"RX1,REJECT,{old_system_hash}")

                        confirm_reject = None
                else:
                        print("Error, system hashes recieved from verificators are not the same")
                        client.publish("/transact", f"RX1,REJECT,{syshash_list[0]}")
                syshash_list = []

GPIO.cleanup()
