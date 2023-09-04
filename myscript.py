#!/usr/bin/env python
import asyncio
import time

# import debugpy
# debugpy.log_to("dpylogs")
# debugpy.listen(("localhost", 1235))
# debugpy.wait_for_client()


def main():
    foo = 1
    bar = 2
    print(foo + bar)
    import time

    while True:
        time.sleep(3)
        foo += 1
        print(foo + bar)
        asyncio.run(amain(foo, bar))

async def amain(foo, bar):
    bar += 10
    print(foo + bar)
    time.sleep(3)

main()
