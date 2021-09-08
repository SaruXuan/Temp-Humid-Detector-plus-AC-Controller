from flask import Flask, render_template, jsonify, abort
from flask_socketio import SocketIO, emit
import adafruit_dht
import board
import time
import json
from datetime import datetime
import sqlite3
import lirc
import subprocess

# create flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# create socketio
socketio = SocketIO(app, cor_allowed_origins='*')

# connect to dht22
sensor = adafruit_dht.DHT22(board.D4, use_pulseio=False)

# Initailize Lirc config parser
client = lirc.Client()

def record_data_to_db(temp, humid):
    try:
        sql = sqlite3.connect('lab_app.db')
        cursor = sql.cursor()
        cursor.execute("INSERT INTO lab (temperature, humidity, datetime) VALUES (?, ?, ?);", (temp, humid, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-7]))
        sql.commit()
        sql.close()
    except RuntimeError:
        print('failed to record data to db!')

def read_data_from_db():
    try:
        sql = sqlite3.connect('lab_app.db')
        cursor = sql.cursor()
        cursor.execute("SELECT * FROM lab;")
        log = cursor.fetchall()
        columns = [cloumn[0] for cloumn in cursor.description]
        res = []
        for row in log:
            res.append(dict(zip(columns, row)))
        sql.commit()
        sql.close()
        return res
    except RuntimeError:
        print('failed to read data from db!')

@app.route('/')
def lab_th():
    temp = None
    humid = None
    trys = 5
    while temp == None or humid == None:
        try:
            temp = sensor.temperature
            humid = sensor.humidity
            sensor.exit()
        except RuntimeError:
            trys -= 1
            print('failed to read data from DHT22!')
            if trys == 0:
                print(f'reach {trys} trys, end server!')
                return abort(500, 'Failed to connect to the sensor')
    trys = 5
    return render_template('lab_th.html',temp=temp, humid=humid)

@app.route('/lab_log')
def lab_log():
    log = read_data_from_db()
    return render_template('lab_log.html', data=log)

@app.route('/lab_ac')
def lab_ac():
    return render_template('lab_ac.html')

@socketio.on('connect')
def connect():
    print('SocketIO connection established!')

@socketio.on('refresh')
def refresh():
    temp = None
    humid = None
    while temp == None or humid == None:
        try:
            print('Requesting temperature and humidity from DHT22')
            temp = sensor.temperature
            humid = sensor.humidity
            print('Request complete successfully')
            emit('status', {'temperature': temp, 'humidity': humid}, broadcast=True)
            record_data_to_db(temp, humid)
            sensor.exit()
            socketio.sleep(0)
        except RuntimeError:
            print('failed to read data from DHT22 while refreshing!')

def send_once(msg):
    subprocess.call(['sudo', 'irsend', 'SEND_ONCE', 'hitachi-re10t1', 'KEY_MACRO26', '--count', '4'])

@socketio.on('open')
def open(msg):
    to_set_temp = int(msg['temperature'])
    try:
        if to_set_temp == 26:
            client.send_once('hitachi-re10t1', 'KEY_MACRO26', repeat_count=5)
    except RuntimeError:
        print('falied to send open signal to irsend')

@socketio.on('close')
def close():
    try:
        client.send_once('hitachi-re10t1', 'KEY_CLOSE', repeat_count=5)
    except RuntimeError:
        print('falied to send close signal to irsend')


if __name__ == '__main__':
        print('server start!!')
        socketio.run(app, host='127.0.0.1', port=8080, debug=True)
            
    
