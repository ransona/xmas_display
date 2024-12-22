import tkinter as tk
from PIL import Image, ImageTk
from screeninfo import get_monitors
import threading

def display_image_on_screen2(image_path):
    # Load the image
    image = Image.open(image_path)

    # Set up the Tkinter window
    window = tk.Tk()
    window.attributes('-fullscreen', True)  # Set window to fullscreen
    window.attributes('-topmost', True)  # Keep on top
    window.bind("<Escape>", lambda e: (e.widget.withdraw(), e.widget.quit()))  # Press Esc to close

    # Find the secondary screen, assuming it's the second one listed
    if len(get_monitors()) > 1:
        monitor = get_monitors()[1]  # Get the second monitor
        # Position the window in the second screen
        window.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
    else:
        print("Second monitor not found. Displaying on primary monitor.")

    # Convert the image to a format Tkinter can use
    photo = ImageTk.PhotoImage(image)

    # Add the image to a label and pack it
    label = tk.Label(window, image=photo)
    label.image = photo  # keep a reference!
    label.pack()

    # Run the Tkinter loop
    window.mainloop()

def start_display_thread(image_path):
    display_thread = threading.Thread(target=display_image_on_screen2, args=(image_path,))
    display_thread.daemon = True  # Daemonize thread
    display_thread.start()

# Example usage:
# start_display_thread("path/to/your/image.jpg")
