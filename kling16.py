import fal_client
import asyncio
from logging import log


start = fal_client.upload_file("D:\\File Transfer\\Inventory\\Profiles\\NSW\\Manh Cuong PHAN - 878\\KYC\\take4\\LP\\png\\tpz\\6.png")
print(start)
tail = fal_client.upload_file("D:\\File Transfer\\Inventory\\Profiles\\NSW\\Manh Cuong PHAN - 878\\KYC\\take4\\LP\\png\\tpz\\1.png")
print(tail)

async def subscribe():
    handler = await fal_client.submit_async(
        "fal-ai/kling-video/v1.6/pro/image-to-video",
        arguments={
            "prompt": "Smoth, even and gradual subject movement. Consistent lighting and colour. Slight camera shake as the camera is hand held. IMG_20201107_203740.JPG",
            "image_url": start,
            "duration": "5",
            "aspect_ratio": "9:16",
            "tail_image_url": tail,
            "negative_prompt": "talking, speaking, jerky subject movement, twitchy subject motion, changing luma or chroma, blur, distort",
            "cfg_scale": 0.8
        },
    )

    async for event in handler.iter_events(with_logs=True):
        print(event)

    result = await handler.get()

    print(result)


if __name__ == "__main__":
    asyncio.run(subscribe())