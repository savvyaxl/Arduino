
import uasyncio as asyncio # type: ignore
import SmartHomeManager

manager = SmartHomeManager()
try:
    asyncio.run(manager.run())
except KeyboardInterrupt:
    pass