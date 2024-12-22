import serial
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
light_flash_min_freq = 20 # Hz
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
client = OpenAI()

# Initialize the webcam
cap = cv2.VideoCapture(0)
# Initialise the ardunio comms
try:
    arduino = serial.Serial(port='COM3', baudrate=9600, timeout=.1)
except:
    print("Arduino not connected")



def write_command(servo_positions, output_states):
    command = f"S{servo_positions[0]},{servo_positions[1]},{servo_positions[2]},{servo_positions[3]};D{output_states[0]},{output_states[1]},{output_states[2]},{output_states[3]}\n"
    arduino.write(bytes(command, 'utf-8'))
    time.sleep(0.01)


def flash_lights():
    print("Starting light flash...")
    light_flash_start_time = time.time()
    keep_flashing = True 
    while keep_flashing:
        time.sleep(1/light_flash_freq)
        write_command([45, 0, 150, 0], [1, 1, 0, 1])
        time.sleep(1/light_flash_freq)
        write_command([45, 0, 150, 0], [1, 0, 0, 0])
        if time.time() - light_flash_start_time > light_run_time:
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
        write_command([0, 90, 150, 0], [1, 1, 0, 0]) 
        time.sleep(1)
        write_command([0, 90, 50, 0], [0, 0, 0, 0]) 
        time.sleep(1)
    write_command([0, 90, 150, 0], [0, 0, 0, 0]) 
        
def fire_catapult():
    # do count down
    play_mp3("catapult.aac")
    time.sleep(3)
    countdown(10)
    # ensure unlocked
    write_command([160, 90, 150, 0], [0, 0, 0, 0])
    # # knock it back
    write_command([0, 90, 150, 0], [0, 0, 0, 0]) 
    time.sleep(2)
    write_command([45, 0, 150, 0], [0, 0, 0, 0]) 
    time.sleep(2)
    # lock it
    write_command([45, 0, 150, 0], [0, 0, 0, 0]) 
    time.sleep(2)
    # load
    for iLoad in range(45,160,3):
        write_command([iLoad, 0, 150, 0], [0, 0, 0, 0]) 
        time.sleep(0.05)
    time.sleep(1)
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

def make_pokemon():
    play_mp3("pokemon1.aac")
    time.sleep(3)
    play_mp3("pokemon2.aac")
    time.sleep(5)
    countdown(10)
    color = capture_and_send_image('Describe the colour of one thing that someone is holding in this image, it should be the most obvious thing being held. Describe the color in one word. The response should only contain one word with no punctuation')
    play_mp3("pokemon3.aac")
    time.sleep(7)
    countdown(10)
    inspiration = capture_and_send_image('Describe one thing that someone is holding in this image, it should be the most obvious thing being held. Describe the object in less than 10 words. only describe the object, not who is holding it or other details.')
    play_mp3("letsdothis.aac")
    time.sleep(4)
    print("Making pokemon...")
    prompt = f"Generate a picture that looks like a real pokemon card with a magical and colourful pokemon in the middle with the following characteristics: {color} color, and inspired by: {inspiration}"
    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
    )
    print("Done generating")
    image_url = response.data[0].url
    print(image_url)
    response = download_with_progress(image_url)
    #response = requests.get(image_url)
    # Check if the request was successful
    image_stream = BytesIO(response)

    # Display the image
    image = mpimg.imread(image_stream, format='JPG')
    # Display the image
    plot_image_on_screen(2,image)

def plot_image_on_screen(screen_number=1, image_path=None):
    # # Create a figure for the image
    plt.close('all')
    fig, ax = plt.subplots()
    ax.imshow(image_path)
    ax.axis('off')  # Hide axes  
    plt.ion()
    plt.show(block=False) 
    # # Load and display an image
    # ax.imshow(image_path)
    plt.waitforbuttonpress()
    # # Maximize the window
    # plt.get_current_fig_manager().window.state('zoomed')

    # # Get screen information using tkinter
    # root = tk.Tk()
    # screen_count = root.winfo_screenwidth()
    # screen_width = root.winfo_screenwidth()
    # screen_height = root.winfo_screenheight()
    # root.destroy()

    # # Determine which screen to use
    # if screen_count >= 2 and screen_number == 2:
    #     # Position on the second screen
    #     x_coord = screen_width
    # else:
    #     # Position on the first screen
    #     x_coord = 0

    # # Position the figure window
    # fig.canvas.manager.window.wm_geometry(f"+{x_coord}+0")

    # # Show the image in a non-blocking way
    # plt.ion()
    # plt.show(block=False)
    # plt.draw()
    # return fig, ax

def create_pie_chart_image(percentage):
    # Create a pie chart
    fig, ax = plt.subplots()
    ax.pie([percentage, 100 - percentage], labels=[f'{percentage}%', ''], startangle=90, counterclock=False, colors=['blue', 'lightgray'])
    ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    # Save the pie chart as an image in memory
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Load this image into an array for imshow
    img = plt.imread(buf)

    # Close the buffer and figure
    buf.close()
    plt.close(fig)

    return img

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
while True:
    write_command([45, 0, 150, 0], [0, 1, 0, 0])
    fire_catapult()
    cockoo(5)
    light_start_time = time.time()       
    thread_lights = threading.Thread(target=flash_lights)
    thread_lights.start()

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

    # loop to check for movement
    write_command([45, 0, 50, 0], [0, 0, 0, 0])
    while True:
        motion_detected = detect_motion(cap, 20000) # Example threshold
        if motion_detected:
            print("Motion detected!")
            if time.time()-last_party_time > min_inter_party_interval:
                print("Party started!")
                last_party_time = time.time()
                # work out what to do
                if random.random() < cock_probability:
                    enable_cock = True
                else:
                    enable_cock = False
                if random.random() < cannon_probability:
                    enable_cannon = True
                else:
                    enable_cannon = False
                if random.random() < pokemon_probability:
                    enable_pokemon = True
                else:
                    enable_pokemon = False
                if random.random() < santa_probability:
                    enable_santa = True
                else:
                    enable_santa = False
                if random.random() < music_probability:
                    enable_music = True
                else:
                    enable_music = False

                light_run_time = random.randint(min_light_run_time, max_light_run_time)
                # loop to run party
                # turn on skaters
                write_command([45, 0, 150, 0], [1, 0, 0, 0])
                light_start_time = time.time()       
                thread_lights = threading.Thread(target=flash_lights)
                thread_lights.start()
                jingle = round(random.uniform(1, 5))
                if enable_music:
                    player_music,music_vlc_instance = play_mp3("jingle_bells"+str(jingle)+".mp3")
                else:
                    player_music,music_vlc_instance = play_mp3("dummy.mp3")
                # Create and start the webcam capture thread

                # Wait for the threads to conclude
                print('Awaiting light thread completion')
                thread_lights.join()
                print('Light thread returned')
                print('Requested music stop')
                fade_out(player_music,5)
                player_music.stop()
                # player_santa.stop()

                if enable_santa:
                    santa_msg = " Describe the image in rhyming  english as if you are one of the three magic kings little helpers, suitable vocab for 6 year old, identifying any people, asking if any are called Pau or Marc or bernard,or catherine or adam or ana, especially children, and speculate if they have been good children. Link any actions you see to how good they might be. max 100 words. allways give it a try even if you are not sure. if there is an old man or woman say they looks a bit naughty but that you are sure he has been a good boy. if there is an old woman speculate if she has eaten enough potatoes like a good girl. if there is an old man speculate that he needs to start taking artifician intelligence seriously or he might miss his chnace to get presents."
                    capture_and_send_image(santa_msg)
                    # once it comes back read it out like santa
                    make_voice(shared_data["picture_analysis_data"],"Santa.aac","onyx")
                    player_santa,santa_vlc_instance = play_mp3("Santa.aac")
                    # wait for santa msg to end
                    fade_out(player_music,2,0.2)
                    while True:
                        state = player_santa.get_state() 
                        if state == vlc.State.Ended or state == vlc.State.Error:
                            break
                    print('Santa speech complete')
                    time.sleep(1)

                if enable_cannon:
                    fire_catapult()

                if enable_pokemon:
                    make_pokemon()

                if enable_cock:
                    cockoo(3)


                    
                
                

cap.release()
cv2.destroyAllWindows()
        



# Example command
#[catapult_load,release,flower1,grinch],[skating,leds,?,?]




 
#[spring [180=loaded,0=knockback],lock[90=unlocked,0=locked] ,...,...]
   


# yellow gd
# blue RED LED
# red WHITE LED