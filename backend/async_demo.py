"""
Day 4 - why async? Run: python async_demo.py
Part 1 simulates slow I/O; part 2 downloads real pages.
"""
import asyncio
import time

import httpx


# ---------- Part 1: sync vs async with simulated waiting ----------
def make_tea_sync(name, seconds):
    time.sleep(seconds)            # blocks everything
    return f"{name} ready"


async def make_tea_async(name, seconds):
    await asyncio.sleep(seconds)   # gives control back while waiting
    return f"{name} ready"


def run_sync():
    start = time.perf_counter()
    results = [make_tea_sync("Tea", 1), make_tea_sync("Coffee", 1), make_tea_sync("Milk", 1)]
    print("SYNC :", results, f"{time.perf_counter() - start:.1f}s")


async def run_async():
    start = time.perf_counter()
    results = await asyncio.gather(
        make_tea_async("Tea", 1), make_tea_async("Coffee", 1), make_tea_async("Milk", 1)
    )
    print("ASYNC:", results, f"{time.perf_counter() - start:.1f}s")


# ---------- Part 2: real HTTP downloads ----------
URLS = [
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
]


def download_sync():
    start = time.perf_counter()
    with httpx.Client(timeout=15) as client:
        codes = [client.get(u).status_code for u in URLS]
    print("SYNC  downloads:", codes, f"{time.perf_counter() - start:.1f}s")


async def download_async():
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=15) as client:
        responses = await asyncio.gather(*(client.get(u) for u in URLS))
    print("ASYNC downloads:", [r.status_code for r in responses], f"{time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    run_sync()
    asyncio.run(run_async())
    download_sync()
    asyncio.run(download_async())
    # Point to make: async helps when WAITING (network, disk, DB).
    # It does NOT speed up heavy CPU work like big calculations.