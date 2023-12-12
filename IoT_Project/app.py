import RPi.GPIO as GPIO
import dash
import dash as doc
import dash as html
import dash_daq as daq
from dash.dependencies import Input, Output
import threading
from dash import Dash, dcc, html, Input, Output, callback, State

import time
from humidity_temperature import HumidityTemperature
from lightSensor import LightSensor
from card import Card
from dash.exceptions import PreventUpdate

import imaplib
import email
from email.header import decode_header
import time
import smtplib
import random
import string
from email.mime.text import MIMEText
import board
import Adafruit_DHT

import datetime
import serial

import sqlite3

import bluetooth as blue

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

username = "etotesto1234@outlook.com"
password = "TestingIot3"
emailSentMotor = 0
emailSentLight = 0

LED = 18

Motor1 = 21
Motor2 = 19
Motor3 = 13
fanOn = False
humidTemp = HumidityTemperature()

GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Motor1, GPIO.OUT)
GPIO.setup(Motor2, GPIO.OUT)
GPIO.setup(Motor3, GPIO.OUT)

sens = LightSensor()
lightVal = 0

card = Card()
currCard = '0'

devices = 0

app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.Img(id='pfp-image', src='/assets/pfp/basic.jpg'),
            ], id='image-div'),
            html.Div(children=[
                html.Div(children=[
                    html.Label('Name: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='name-input', className='info-inputs', value='Please scan your RFID tag'),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Email: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='email-input', className='info-inputs', value=''),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Preferred Temperature (°C): ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='temp-input', className='info-inputs', value=''),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Light Activation Threshold: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='threshold-input', className='info-inputs', value=''),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Button('Update Preferences', id='info-submit', n_clicks=0),
                ], className='info-all'),
            ], id='information'),
        ], id='information-div'),
        html.Div(children=[
            html.Div(children=[
                html.Div(children=[
                    html.Div(children=[
                        html.H1("Bluetooth"),
                    ], id='temp-blue-section'),
                    html.P("Devices Detected: ", id="bluetooth_text"),
                ], className='section-divs-mini'),
                html.Div(children=[
                    html.Div(children=[
                        html.H1("Fan"),
                    ], id='temp-fan-section'),
                    html.Img(id='fan-image', src='/assets/fan.png', className='fan-animation', style={'width': '145px', 'height': '145px'})
                ], className='section-divs-mini'),
            ], id='bluetooth-fan-section'),
            html.Div(children=[
                html.H1("Humidity"),
                html.Div(children=[
                    daq.Gauge(
                        id='hum_gauge',
                        showCurrentValue=True,
                        value=0,
                        max=100,
                        min=0,
                        size=145,
                        color='#A0E9FF'
                    ),
                ]),
            ], className='section-divs-small'),
        ], id='fan-hum'),
        html.Div(children=[
            html.H1("Temperature"),
            html.Div(children=[
                daq.Thermometer(
                    id='temp_termometer',
                    value=0,
                    min=-10,
                    max=40,
                    height=300,
                    color='#A0E9FF',
                    style={'color': 'white'}
                ),
            ]),
            html.Div(id='temp_gauge_label'),
        ], className='section-divs-tall'),
        html.Div(children=[
            html.H1("LED Control"),
            html.Div([
                html.Img(id='led-image', src='/assets/light_off.png', style={'width': '220px', 'height': '220px'}),
            ]),
            html.Div(children=[
                html.H4("Environment Light Intensity", style={'color': 'white'}),
                daq.GraduatedBar(
                    id='light_intensity',
                    showCurrentValue=True,
                    color={"gradient":True,"ranges":{"#b2edff":[0,4],"#80dffc":[4,7],"#1ccaff":[7,10]}},
                    value=10,
                    max=10
                ),
                html.P("", id="email_text"),
            ], id='light-intensity'),
        ], className='section-divs-tall'),
        html.Div(id='email_div'),
    ], id='dashboard'),
    dcc.Interval(
        id = "interval",
        interval = 5 * 1000,
        n_intervals = 0,
    ),
    dcc.Interval(
        id = "interval-fan",
        interval = 4 * 1000,
        n_intervals = 0,
    ),
    html.Div(id='motor_email'),
    dcc.Interval(
        id = "interval-motor-email",
        interval = 5 * 1000,
        n_intervals = 0,
    ),
    html.Div(id='light_div'),
    dcc.Interval(
        id = "interval-light",
        interval = 5 * 1000,
        n_intervals = 0,
    ),
    html.Div(id='light_email'),
    dcc.Interval(
        id = "interval-light-email",
        interval = 5 * 1000,
        n_intervals = 0,
    ),
    html.Div(id='card_getter'),
    dcc.Interval(
        id = "interval-card",
        interval = 5 * 1000,
        n_intervals = 0,
    ),
    html.Div(id='bluetooth'),
    dcc.Interval(
        id = "interval-bluetooth",
        interval = 10 * 1000,
        n_intervals = 0,
    ),
], className='content')


@app.callback(
    [Output('image-div', 'children'),
     Output('information', 'children')],
    [Input('interval-card', 'n_intervals'),
     Input('info-submit', 'n_clicks')],
    [State('name-input', 'value'),
     State('email-input', 'value'),
     State('temp-input', 'value'),
     State('threshold-input', 'value')],
    allow_duplicate=True
)
def update_content(n, n_clicks, name, email, temperature, threshold):
    global currCard
    global isNewCard
    global updated_image
    global updated_content
    
    tempCard = str(card.cardValue)
    placeholder = currCard
    currCard = tempCard.lstrip()
    
    if (currCard == "0"):
        raise PreventUpdate

    if n_clicks is not None and n_clicks > 0:
        updated_image, updated_content = update_preferences(name, email, temperature, threshold)
    elif (placeholder == currCard):
        isNewCard = False
    else:
        isNewCard = True

    if currCard != '0' and isNewCard:
        updated_image, updated_content = show_user(currCard)
    else:
        raise PreventUpdate
            
    return updated_image, updated_content

def create_user():
    rfid = currCard
    newTemp = 22
    newLight = 4
    newN = "NewUser"
    newE = "Please set your email"
    newPro = "/assets/pfp/default.jpg"

    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user (RFID, TempThreshold, LightThreshold, Name, Email, ProfilePicture)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (rfid, newTemp, newLight, newN, newE, newPro))
    conn.commit()
    cursor.close()
    conn.close()
    
    updated_image = [html.Img(id='pfp-image', src=newPro),]
    
    updated_content = [html.Div(children=[
                    html.Label('Name: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='name-input', className='info-inputs', value=newN),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Email: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='email-input', className='info-inputs', value=newE),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Preferred Temperature (°C): ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='temp-input', className='info-inputs', value=newTemp),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Light Activation Threshold: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='threshold-input', className='info-inputs', value=newLight),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Button('Update Preferences', id='info-submit', n_clicks=0),
                ], className='info-all'),
            ]
    
    return updated_image, updated_content

def update_preferences(name, email, temperature, threshold):
    rfid = currCard
    newTemp = temperature
    newLight = threshold
    newN = name
    newE = email
    
    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE RFID=?', (rfid,))
    row = cursor.fetchone()
    cursor.execute('''
        UPDATE user
        SET TempThreshold=?, LightThreshold=?, Name=?, Email=?
        WHERE RFID=?
    ''', (newTemp, newLight, newN, newE, rfid))
    conn.commit()
    cursor.close()
    conn.close()
    
    pfp = row[6]
    
    updated_image = [html.Img(id='pfp-image', src=pfp),]
    
    updated_content = [html.Div(children=[
                    html.Label('Name: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='name-input', className='info-inputs', value=newN),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Email: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='email-input', className='info-inputs', value=newE),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Preferred Temperature (°C): ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='temp-input', className='info-inputs', value=newTemp),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Label('Light Activation Threshold: ', className='info-labels'),
                    html.Div(children=[
                        dcc.Input(id='threshold-input', className='info-inputs', value=newLight),
                    ]),
                ], className='info-all'),
                html.Div(children=[
                    html.Button('Update Preferences', id='info-submit', n_clicks=0),
                ], className='info-all'),
            ]
            
    return updated_image, updated_content

def show_user(rfid):
    conn = sqlite3.connect('iot_project.sqlite')

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE RFID=?', (rfid,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        temp_column = row[2]
        light_column = row[3]
        name_column = row[4]
        email_column = row[5]
        pfp_column = row[6]
        
        updated_image = [html.Img(id='pfp-image', src=pfp_column),]
        
        updated_content = [html.Div(children=[
                        html.Label('Name: ', className='info-labels'),
                        html.Div(children=[
                            dcc.Input(id='name-input', className='info-inputs', value=name_column),
                        ]),
                    ], className='info-all'),
                    html.Div(children=[
                            html.Label('Email: ', className='info-labels'),
                            html.Div(children=[
                                dcc.Input(id='email-input', className='info-inputs', value=email_column),
                            ]),
                        ], className='info-all'),
                    html.Div(children=[
                        html.Label('Preferred Temperature (°C): ', className='info-labels'),
                        html.Div(children=[
                            dcc.Input(id='temp-input', className='info-inputs', value=temp_column),
                        ]),
                    ], className='info-all'),
                    html.Div(children=[
                        html.Label('Light Activation Threshold: ', className='info-labels'),
                        html.Div(children=[
                            dcc.Input(id='threshold-input', className='info-inputs', value=light_column),
                        ]),
                    ], className='info-all'),
                    html.Div(children=[
                        html.Button('Update Preferences', id='info-submit', n_clicks=0),
                    ], className='info-all'),
                ]
        if (email_column != "Please set your email"):
            send_email_rfid(email_column, name_column)
    else:
        updated_image, updated_content = create_user()
    
    return updated_image, updated_content


@app.callback(
    Output('led-image', 'src'),
    Output('light_intensity', 'value'),
    Output('email_text', 'children'),
    Input('interval-light', 'n_intervals')
)
def toggle_led(n):
    lightValFirst = (int(sens.lightValue))/100
    global lightVal
    global light_intensity
    global email_text
    global emailSentLight
    global currCard
    
    if (currCard == "0"):
        raise PreventUpdate
        
    if (lightValFirst > 10):
        lightValFirst = 10
                
    lightVal = 10-lightValFirst
        
    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE RFID=?', (currCard,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    
    lightLevel = row[3]
    
    if (int(lightVal) < lightLevel and emailSentLight == 2):
        GPIO.output(LED, GPIO.HIGH)
        light_intensity = lightVal
        led_image = '/assets/light_on.png'
        email_text = "The light has been turned on, and a notification email has been sent."
    elif (int(lightVal) < lightLevel):
        GPIO.output(LED, GPIO.HIGH)
        light_intensity = lightVal
        led_image = '/assets/light_on.png'
        email_text = "The light has been turned on, and a notification email has been sent."
        emailSentLight = 1
    else:
        GPIO.output(LED, GPIO.LOW)
        light_intensity = lightVal
        led_image = '/assets/light_off.png'
        email_text = ""
        emailSentLight = 0
    
    return led_image, light_intensity, email_text
    

@app.callback(
    Output('light_email', 'children'),
    Input('interval-light-email', 'n_intervals')
)
def send_light_email(n):
    global emailSentLight
    global currCard
    
    if (currCard == "0"):
        raise PreventUpdate
        
    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE RFID=?', (currCard,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    
    if row:
        email = row[5]
        if (email != "Please set your email"):
            if (emailSentLight == 1):
                emailSentLight = 2
                send_email_light(email)

'''
@app.callback(
    Output('bluetooth_text', 'children'),
    Input('interval-bluetooth', 'n_intervals')
)
def send_light_email(n):
    global devices
    global currCard
    
    if (currCard == "0"):
        raise PreventUpdate
    
    devices = detect_bluetooth_devices()
    devices_value = "Devices Detected: " + str(devices)
    
    return devices_value
'''

@app.callback(
    Output('fan-image', 'className'),
    Input('interval-fan', 'n_intervals')
)
def toggle_fan_animation(n):
    global fanOn
    global emailSentMotor
    global currCard
    
    if (currCard == "0"):
        raise PreventUpdate
    
    if (emailSentMotor == 3):
        GPIO.output(Motor1, GPIO.HIGH)
        GPIO.output(Motor2, GPIO.HIGH)
        GPIO.output(Motor3, GPIO.LOW)
        return 'fan-image-on'
    else:
        GPIO.output(Motor1, GPIO.LOW)
        GPIO.output(Motor2, GPIO.LOW)
        GPIO.output(Motor3, GPIO.LOW)
        return 'fan-image-off'
        
@app.callback(
    Output('motor_email', 'children'),
    Input('interval-motor-email', 'n_intervals')
)
def send_motor_email(n):
    global emailSentMotor
    global currCard
    
    if (currCard == "0"):
        raise PreventUpdate
    
    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE RFID=?', (currCard,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    
    email = row[5]
    
    email_identifier = generate_identifier()
    
    if (email != "Please set your email"):
        if (emailSentMotor == 1):
            emailSentMotor = 2
            send_email(email)


@app.callback(
    Output('temp_termometer', 'value'),
    Output('hum_gauge', 'value'),
    Output('temp_gauge_label', 'children'),
    Input('interval', 'n_intervals'),
)
def checkHumAndTemp(n):
    global temp_termometer
    global hum_gauge
    global temp_gauge_label
    global emailSentMotor
    global currCard
    
    if (currCard == "0"):
        raise PreventUpdate
        
    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE RFID=?', (currCard,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    
    temp = row[2]
    
    humidity = HumidityTemperature.getHumAndTemp()['humidity']
    temperature = HumidityTemperature.getHumAndTemp()['temperature'] 

    temp_termometer = temperature
    hum_gauge = humidity
    temp_gauge_label = f'{temperature:.2f}°C'

    if (temperature < temp):
        emailSentMotor = 0

    if (temperature > temp and emailSentMotor == 0):
        emailSentMotor = 1

    return temp_termometer, hum_gauge, temp_gauge_label

def connectDb():
    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS user")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            RFID TEXT NOT NULL,
            TempThreshold REAL NOT NULL DEFAULT 18,
            LightThreshold REAL NOT NULL DEFAULT 40,
            Name TEXT NOT NULL DEFAULT 'NewUser',
            Email TEXT NOT NULL DEFAULT 'etotesto1234@outlook.com',
            ProfilePicture BLOB NOT NULL DEFAULT '/assets/pfp/default.jpg'
        )
    ''')
    data = [
        ('02 111 194 27', 23, 5, 'Nicholas Adiohos', 'etotesto1234@outlook.com', '/assets/pfp/claude.jpg'),
        ('210 245 60 26', 22, 3, 'Sonia Vetra', 'etotesto1234@outlook.com', '/assets/pfp/jingliu.jpg'),
        ('229 50 143 172', 24, 4, 'Jacob Lau', 'etotesto1234@outlook.com', '/assets/pfp/kenma.jpg')
    ]
    cursor.executemany('''
        INSERT INTO user (RFID, TempThreshold, LightThreshold, Name, Email, ProfilePicture)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    cursor.close()
    conn.close()

# Call the function to initialize the database
connectDb()


def check_rfid_exists(rfid):
    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user WHERE RFID=?", (rfid,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    return count > 0


@app.callback(
    Output('email_div', 'children'),
    Input('interval-fan', 'n_intervals')
)
def check_email(n):
    global emailSentMotor
    global currCard
    
    if (currCard == "0"):
        raise PreventUpdate
    
    try:
        imap_server = "outlook.office365.com"
        imap = imaplib.IMAP4_SSL(imap_server)
        imap.login(username, password)

        imap.select("INBOX")

        status, messages = imap.search(None, "UNSEEN")

        if status == "OK" and messages:
            message_ids = messages[0].split()
            for msg_id in message_ids:
                status, msg_data = imap.fetch(msg_id, "(RFC822)")
                if status == "OK" and emailSentMotor == 2:
                    email_message = email.message_from_bytes(msg_data[0][1])
                    process_email(email_message)

        imap.logout()

    except Exception as e:
        print("An error occurred:", str(e))

def generate_identifier(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def send_email(email):
    imap_server = "outlook.office365.com"
    with smtplib.SMTP(imap_server, 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        subject = f'turn on fan?'
        body = f'The current temperature is over 24. Would you like to turn on the fan?'
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = email
        smtp.sendmail(username, email, msg.as_string())
        print("Email sent")


def send_email_light(email):
    imap_server = "outlook.office365.com"

    current_time = datetime.datetime.now()
    hh = current_time.hour
    mm = current_time.minute

    with smtplib.SMTP(imap_server, 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        subject = f'Light turned on'
        body = f'The Light is ON at {hh:02}:{mm:02} time.'
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = email
        smtp.sendmail(username, email, msg.as_string())

def send_email_rfid(email, name):
    imap_server = "outlook.office365.com"
    
    conn = sqlite3.connect('iot_project.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE RFID=?', (currCard,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    
    name = row[4]

    current_time = datetime.datetime.now()
    hh = current_time.hour
    mm = current_time.minute

    with smtplib.SMTP(imap_server, 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        subject = f'RFID tag was read'
        body = f'{name} entered at this time: {hh:02}:{mm:02}.'
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = email
        smtp.sendmail(username, email, msg.as_string())


def process_email(email_message):
    global emailSentMotor
    
    print("Processing...")
    subject = email_message["Subject"]

    if email_message.is_multipart():
        body = ""
        for part in email_message.walk():
            content_type = part.get_content_type()
            if "text/plain" in content_type:
                body += part.get_payload(decode=True).decode()
    else:
        body = email_message.get_payload()

    if f"Re: turn on fan?" in subject:
        if "yes" in body.lower():
            print("Recieved Yes!")
            emailSentMotor = 3
            
'''
def detect_bluetooth_devices():
    nearby_devices = blue.discover_devices(duration=8, lookup_names=True)
    return nearby_devices
'''

if __name__ == '__main__':
    threading.Thread(target = sens.run).start()
    threading.Thread(target = card.run).start()
    
    app.run_server(debug=True)
