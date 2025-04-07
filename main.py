import nest_asyncio
nest_asyncio.apply()

import asyncio
from bot import main as bot_main

if __name__ == "__main__":
    # Получаем текущий запущенный цикл и запускаем в нём основную корутину бота
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot_main())
