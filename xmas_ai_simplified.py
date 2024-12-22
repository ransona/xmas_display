import serial
import serial.tools.list_ports
import time
import base64
import requests
import cv2
from pathlib import Path
from openai import OpenAI
import vlc
from PIL import Image
from io import BytesIO
import io
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from motion_detection import detect_motion
import random
import threading
from datetime import datetime
import numpy as np
import tkinter as tk
import sys


# loops grabbing cam image every 2 secs and checking for diff
# if diff found runs in verbose mode or with delay before starting next run
# if in delay mode can wait for a period of non-movement (i.e. nobody in room)
# calcs if different functions will run and randomises music etc
# random items:
seed_value = int(time.time())
random.seed(seed_value)
# canon
enable_cannon = True
cannon_probability = 0.2
# cook
enable_cock = True
cock_probability = 1
# pokemon card
enable_pokemon = True
pokemon_probability = 0
# light flash frequency
light_flash_freq = 5 # Hz
light_flash_min_freq = 5 # Hz
light_flash_max_freq = 80 # Hz
# grinch hourly cockoo
# no poem / catalan poem / english poem / apocaliptic
enable_poem = True
poem_boundaries = [0, 0.25, 0.5, 0.75, 1]
# santa random checkin
enable_santa = True
santa_probability = 1
# music
enable_music = True
music_probability = 1
# parameters
min_inter_party_interval = 0 # seconds
light_run_time = 600 # seconds
max_light_run_time = 30 # seconds
min_light_run_time = 10 # seconds
# OpenAI API Key

# client = OpenAI()

# Initialize the webcam
# cap = cv2.VideoCapture(0)
# Initialise the ardunio comms
# try:
#     arduino = serial.Serial(port='COM3', baudrate=9600, timeout=.1)
# except:
#     print("Arduino not connected")
# Scan available ports
ports = serial.tools.list_ports.comports()
arduino = None

for port in ports:
    try:
        # Try connecting to the serial port
        arduino = serial.Serial(port.device, baudrate=9600, timeout=0.1)
        print(f"Connected to Arduino on port: {port.device}")
        break  # Exit the loop once Arduino is found
    except Exception as e:
        print(f"Failed to connect on port {port.device}: {e}")
        sys.exit()

def write_command(servo_positions, output_states):
    command = f"S{servo_positions[0]},{servo_positions[1]},{servo_positions[2]},{servo_positions[3]};D{output_states[0]},{output_states[1]},{output_states[2]},{output_states[3]}\n"
    arduino.write(bytes(command, 'utf-8'))
    time.sleep(0.01)


def flash_lights_skate(on_time):
    print("Starting light flash + skating...")
    light_flash_start_time = time.time()
    light_flash_end_time = light_flash_start_time + on_time
    keep_flashing = True 
    while keep_flashing:
        time.sleep(1/light_flash_freq)
        write_command([45, 0, 150, 0], [1, 1, 0, 1])
        time.sleep(1/light_flash_freq)
        write_command([45, 0, 150, 0], [1, 0, 0, 0])
        if time.time() > light_flash_end_time:
            print("Light flash complete")
            shared_data["stop_music"] = True
            write_command([45, 0, 150, 0], [0, 0, 0, 0])
            keep_flashing = False

def flash_lights_for_time(on_time):
    print("Starting light flash...")
    light_flash_start_time = time.time()
    light_flash_end_time = light_flash_start_time + on_time
    keep_flashing = True 
    while keep_flashing:
        time.sleep(1/light_flash_freq)
        write_command([45, 0, 150, 0], [0, 1, 0, 1])
        time.sleep(1/light_flash_freq)
        write_command([45, 0, 150, 0], [0, 0, 0, 0])
        if time.time() > light_flash_end_time:
            print("Light flash complete")
            shared_data["stop_music"] = True
            write_command([45, 0, 150, 0], [0, 0, 0, 0])
            keep_flashing = False

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def capture_and_send_image(gpt_prompt):
    print("Starting background image analysis...")
    ret, frame = cap.read()
    #plt.imshow(frame)
    #plt.show()
    if ret:
        image_path = 'frame.jpg'
        cv2.imwrite(image_path, frame)
        base64_image = encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": gpt_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        picture_analysis_data = response.json()
        print(picture_analysis_data['choices'][0]['message']['content'])
        shared_data["picture_analysis_data"] = picture_analysis_data['choices'][0]['message']['content']
        print("Background image analysis complete")
        return(picture_analysis_data['choices'][0]['message']['content'])

def make_voice(text_to_read,speech_file_path,voice):
    # generating speech mp3
    print("Generating speech mp3...")
    response = client.audio.speech.create(
    model="tts-1",
    voice=voice,
    input=text_to_read,
    response_format="aac"
    )
    response.stream_to_file(speech_file_path)

def play_mp3(file_path, audio_output='directx'):
    # # Create a VLC instance with the specified audio output
    # vlc_instance = vlc.Instance('--aout={}'.format(audio_output))
    # player = vlc_instance.media_player_new()
    # media = vlc_instance.media_new(file_path)
    # player.set_media(media)
    # player.audio_set_volume(100)
    # player.play()
    # return player, vlc_instance
    # Create a VLC instance
    vlc_instance = vlc.Instance()
    player = vlc_instance.media_player_new()

    # Load media
    media = vlc_instance.media_new(file_path)

    if not media:
        print("Media loading failed")
    else:
        player.set_media(media)
        player.audio_set_volume(100)
        # Play the media
        player.play()
        return player, vlc_instance

def is_playing(player):
    return player.is_playing()

def fade_out(player, duration=5, min_volume_fraction=0):
    # Get the current volume
    current_volume = player.audio_get_volume()
    target_volume = int(min_volume_fraction * current_volume)
    # Calculate the amount of volume to decrease each step
    volume_step = current_volume / (duration * 10)  # Assuming 10 steps per second

    while current_volume > target_volume:
        current_volume -= volume_step
        player.audio_set_volume(max(int(current_volume), target_volume))
        time.sleep(0.1)  # Wait for 0.1 seconds between each step

def cockoo(hour):
    for iCockoo in range(0,hour):
        # pop out grinch
        play_mp3("cockoo.m4a")
        time.sleep(0.5)
        write_command([0, 90, 150, 0], [0, 1, 0, 0]) 
        time.sleep(1)
        write_command([0, 90, 50, 0], [0, 1, 0, 0]) 
        time.sleep(1)
    write_command([0, 90, 150, 0], [0, 0, 0, 0]) 
        
def fire_catapult():
    # do count down
    # ensure unlocked
    write_command([160, 90, 150, 0], [0, 0, 0, 0])
    # # knock it back
    write_command([0, 90, 150, 0], [0, 0, 0, 0]) 
    play_mp3("Catapult.aac")
    write_command([45, 0, 150, 0], [0, 0, 0, 0]) 
    time.sleep(2)
    # lock it
    write_command([45, 0, 150, 0], [0, 0, 0, 0]) 
    time.sleep(2)
    # load
    for iLoad in range(45,160,3):
        write_command([iLoad, 0, 150, 0], [0, 0, 0, 0]) 
        time.sleep(0.05)

    countdown(10)
    time.sleep(2)

    # launch
    write_command([160, 90, 150, 0], [0, 0, 0, 0]) 
    time.sleep(3)
    # ensure unlocked
    write_command([160, 90, 150, 0], [0, 0, 0, 0])
    # # knock it back
    write_command([0, 90, 150, 0], [0, 0, 0, 0]) 
    time.sleep(2)
    write_command([45, 0, 150, 0], [0, 0, 0, 0]) 
    time.sleep(2)

def countdown(number):
    for iCountdown in range(number,0,-1):
        play_mp3(f"{iCountdown}.aac")
        time.sleep(1)

def download_with_progress(url):
    response = requests.get(url, stream=True)

    # Check if the server provided the content length
    total_length = response.headers.get('content-length')

    if total_length is None:  # No content length header
        print("Cannot determine progress - no content length available.")
        return response.content
    else:
        total_length = int(total_length)
        downloaded = 0
        
        # Create a variable to store the downloaded data
        data = bytes()

        for chunk in response.iter_content(chunk_size=4096):
            downloaded += len(chunk)
            data += chunk
            done = int(50 * downloaded / total_length)
            percent_complete = (downloaded / total_length) * 100
            print(f"\r[{'=' * done}{' ' * (50-done)}] {percent_complete:.2f}%", end="")
            # plot_image_on_screen(2,create_pie_chart_image((downloaded / total_length) * 100))
        return data


# variable to store the last hour when the cockoo was run
last_run_hour = None
# Initialise the last party time
last_party_time = time.time()
shared_data = {"picture_analysis_data": "test"}
shared_data["stop_music"] = False

#cockoo(3)
#write_command([45, 0, 150, 0], [0, 0, 0, 0])
# play_mp3("cockoo.m4a")
# make_pokemon()
#fire_catapult()

# speech file generator
# make_voice("Let's doooooooooooo this","letsdothis.aac","echo")
# player_santa,santa_vlc_instance = play_mp3("letsdothis.aac")

# main loop
next_skate_time = time.time()+random.randint(200,900)
next_catapult_time = time.time()+random.randint(200,900)

# test functionality
flash_lights_skate(5)
flash_lights_for_time(5)
fire_catapult()
cockoo(10)

while True:

    # default state
    # lights flashing or on
    # after a random delay turn on skaters for 20 secs
    # randomly turn on catapult sometimes
    # on the hour run cockoo
    light_flash_freq = random.randint(light_flash_min_freq,light_flash_max_freq)
    flash_lights_for_time(5)
    if time.time() > next_skate_time:
        flash_lights_skate(10)
        next_skate_time = time.time()+random.randint(200,900)
    
    if time.time() > next_catapult_time:
        fire_catapult()
        next_catapult_time = time.time()+random.randint(200,900)

    # Get the current time
    current_time = datetime.now()
    current_hour = current_time.hour
    # Check if the cockoo has been run this hour
    if last_run_hour != current_hour:
        print("Running cockoo")
        if current_hour > 12:
            cockoo(current_hour-12)
        else:
            cockoo(current_hour)
        last_run_hour = current_hour
