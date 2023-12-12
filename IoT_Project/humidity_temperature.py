import time
import Freenove_DHT as DHT
import Adafruit_DHT

class HumidityTemperature :
   
    def getHumAndTemp():
        DHTPin = 17
        
        dht_sensor = Adafruit_DHT.DHT11
        humidity, temperature = Adafruit_DHT.read_retry(dht_sensor, DHTPin)
        
        data = dict()
        data['humidity'] = humidity
        data['temperature'] = temperature
        return data
