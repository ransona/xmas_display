import vlc

def play_mp3(file_path, audio_output='directx'):
    # Create a VLC instance with the specified audio output
    vlc_instance = vlc.Instance('--aout={}'.format(audio_output))
    player = vlc_instance.media_player_new()
    media = vlc_instance.media_new(file_path)
    player.set_media(media)
    player.play()
    return player

# File paths
santa_mp3 = 'C:\\Users\\ranso\\Documents\\mp3s\\santa.mp3'
jingle_bells_mp3 = 'C:\\Users\\ranso\\Documents\\mp3s\\jingle_bells.mp3'

# Play the MP3 files
player1 = play_mp3(santa_mp3)
player2 = play_mp3(jingle_bells_mp3)

# Keep the script running until the music plays
import time
time.sleep(60)  # Adjust the duration as needed

# Stop the players
player1.stop()
player2.stop()
