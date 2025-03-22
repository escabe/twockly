from squares import TwinklySquares
import asyncio

async def main() -> None:
    # Connect to device
    t = TwinklySquares(host="192.168.1.172",rows=2,cols=3)
    await t.interview()

    await t.recalibrate()

    await t.calibrate_set_order([[1,2,3],[0,5,4]])

    await t.calibrate_rotate(1)

    await t.calibrate_rotate(2)
    await t.calibrate_rotate(2)
    await t.calibrate_rotate(2)

    await t.calibrate_rotate(4)
    await t.calibrate_rotate(5)

    await t.close()


if __name__ == "__main__":
    asyncio.run(main())
