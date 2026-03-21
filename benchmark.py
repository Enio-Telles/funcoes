import asyncio
import time
import httpx
from fastapi.testclient import TestClient
from server.python.routers.references import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def make_requests(n):
    start = time.time()
    for _ in range(n):
        client.get("/api/python/references/ncm/01012100")
    print(f"Sequential took: {time.time() - start:.3f}s")

async def make_async_requests(n):
    # httpx.ASGITransport for testing FastAPI app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        start = time.time()
        tasks = [ac.get("/api/python/references/ncm/01012100") for _ in range(n)]
        await asyncio.gather(*tasks)
        print(f"Concurrent took: {time.time() - start:.3f}s")

if __name__ == "__main__":
    make_requests(50)
    asyncio.run(make_async_requests(50))
