import board
import machine
import time

def safe_pin_test():
    print("--- Starting Pin Safety Test ---")
    
    # Filter only Pin objects from your board dictionary
    for name, pin_obj in board.pins.items():
        if not isinstance(pin_obj, machine.Pin):
            continue
            
        try:
            # Attempt to set the pin as an output
            print(f"Testing {name}...", end=" ")
            pin_obj.init(mode=machine.Pin.OUT)
            
            # Toggle it briefly
            pin_obj.value(1)
            time.sleep(0.1)
            pin_obj.value(0)
            
            print("OK")
            
        except Exception as e:
            # Catch and report any errors (e.g., ValueError for invalid pins)
            print(f"FAILED: {e}")

    print("--- Test Complete ---")

safe_pin_test()
