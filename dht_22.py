import Adafruit_DHT
import board
import time

while(True):
    try:
        humid, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
        print(f'temperature:{temp}C, humidity:{humid}%')
        time.sleep(2)
    except Exception as e:
        print(f'[Error]: {e}')
