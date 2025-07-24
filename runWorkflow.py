import asyncio
import fal_client

async def stream():
    stream = fal_client.stream_async(
        "workflows/dedkamaroz/image-to-video",
        arguments={},
    )
    async for event in stream:
        print(event)


if __name__ == "__main__":
    asyncio.run(stream())