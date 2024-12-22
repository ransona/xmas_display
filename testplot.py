import matplotlib.pyplot as plt
import random
import time

# Create an empty scatter plot
fig, ax = plt.subplots()
scatter = ax.scatter([], [])

# Set the axis limits
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)

# Start the loop
while True:
    # Generate a random number
    random_number = random.random()

    # Wait for 1 second
    time.sleep(1)

    # Plot the random number on the scatter plot
    scatter.set_offsets([(random_number, random_number)])

    # Update the scatter plot
    plt.draw()
    plt.pause(0.001)
