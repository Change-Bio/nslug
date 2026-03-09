import sys
from gpiozero import OutputDevice
from time import sleep

# Hardware Setup
STEP_PIN = 17
DIR_PIN = 27
STEPS_PER_REV = 6400  # 1/32 Microstepping

step = OutputDevice(STEP_PIN)
direction = OutputDevice(DIR_PIN)

def move_pump(turns, mode):
    # Swapped Direction Logic
    if mode.lower() == "forward":
        direction.off() # Now Low = Forward
        print(f"Pumping FORWARD for {turns} turns...")
    else:
        direction.on()  # Now High = Backward
        print(f"Pumping BACKWARD for {turns} turns...")

    total_steps = int(turns * STEPS_PER_REV)
    
    for i in range(total_steps):
        step.on()
        sleep(0.0002) #
        step.off()
        sleep(0.0002)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pump.py [turns] [forward/backward]")
        sys.exit()

    try:
        num_turns = float(sys.argv[1])
        dir_mode = sys.argv[2]
        move_pump(num_turns, dir_mode)
    except ValueError:
        print("Error: Turns must be a number.")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        print("Done.")
