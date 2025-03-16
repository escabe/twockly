"""Example of sending realtime frames to Twinkly"""

import asyncio
import time
from seven_segment import digits

from ttls.client import Twinkly, TwinklyFrame

# Define some colors
RED = (0xFF, 0x00, 0x00)
GREEN = (0x00, 0x77, 0x00)
BLUE = (0x00, 0x00, 77)
CYAN = (0x00, 0x77 ,0x77)
BLACK = (0x00, 0x00, 0x00)

# Define the tile layout
tiles = [
    [(0,0),(1,0),(2,0)]
]
# Define x-offsets for each digit
offsets = [1,6,13,18]
colon_offset = offsets[1] + 5

def xyToIndex(x,y):
    # Determine which tile the requested global coordinate is on
    tile_info = tiles[y//8][x//8]
    # Start with the base offset to end up on the right tile
    index = tile_info[0] * 64
    # Convert global coordinate to local coordinate on the tile
    x = x % 8
    y = y % 8
    # Depending on the tile orientation compute the correct local index
    # and add it to the global index
    if tile_info[1] == 0:
        if y % 2 == 0: # For even rows, in which the index increases when going left
            index += (7-y) * 8 + (7-x)
        else:          # For odd rows, in which the index increases when going right
            index += (7-y) * 8 + x
    elif tile_info[1] == 1:
        pass # TODO
    elif tile_info[1] == 2:
        pass # TODO
    elif tile_info[1] == 3:
        pass # TODO
    
    return index

def generate_clock_frame(n: int,blink) -> TwinklyFrame:
    """Generate a clock frame"""
    
    # Start with an empty frame
    res = [BLACK] * n
    # Convert current time to four separate digits
    now = time.localtime()
    numbers = [now.tm_hour//10,now.tm_hour%10,now.tm_min//10,now.tm_min%10]
    # For each of the four digits
    for i in range(4):
        # Get the number
        num = numbers[i]
        # Work through the font grid
        for y in range(8):
            for x in range(4):
                # If pixel should be lit
                if digits[num][y][x] == 1:
                    # Update the correct pixel
                    res[xyToIndex(x+offsets[i],y)] = RED
    # Add the colon
    if blink :
        res[xyToIndex(colon_offset,3)] = RED
        res[xyToIndex(colon_offset,5)] = RED


    res[xyToIndex(23,1)] = GREEN
    res[xyToIndex(23,4)] = BLUE
    res[xyToIndex(23,7)] = CYAN


    
    return res


async def main() -> None:
    # Connect to device
    t = Twinkly(host="192.168.1.188")
    await t.interview()
    # Configure device
    await t.set_mode("rt")
    await t.set_brightness(15)
    # Blink colon
    blink = 0
    # For as long as the application is active
    while True:
        # Verify that device is still in realtime mode
        # (this can change if for example the Twinly App
        #  also tried to interact with the device)
        if (await t.get_mode())['mode'] != "rt":
            # If no longer in rt mode, switch back to it
            print("Restting to rt mode")
            await t.set_mode("rt")
        # Generate the frame and send it
        frame = generate_clock_frame(t.length,blink)
        await t.send_frame(frame)
        # Colon blinker
        blink = (blink+1) % 2
        # Wait before sending next frame
        time.sleep(2)

    await t.close()


if __name__ == "__main__":
    asyncio.run(main())
