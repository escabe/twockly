from squares import TwinklySquares
import asyncio
import time

async def main() -> None:
    # Connect to device
    t = TwinklySquares(host="192.168.1.172",layout=
        [
            [[1,0],[2,1],[3,3]],
            [[0,0],[5,1],[4,1]],
        ],
        clock_x_offset=3,
        clock_y_offset=1,
        blink_speed=1000,
        mode="rt")
    await t.interview()
    await t.set_brightness(5)
    #await t.recalibrate()
    #await t.calibrate_set_order([[1,2,3],[0,5,4]])
    #await t.calibrate_rotate(1)
    #await t.calibrate_rotate(2)
    #await t.calibrate_rotate(2)
    #await t.calibrate_rotate(2)
    #await t.calibrate_rotate(4)
    #await t.calibrate_rotate(5)

    while True:
        await t.render_full_frame()
        t.wait()
    await t.close()


if __name__ == "__main__":
    asyncio.run(main())
