import fal_client
from logging import log

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

url = fal_client.upload_file("D:\\File Transfer\\Doc Scans\\Templates\\Selfie Pool\\Videos\\RunwayML Act-One vs Kling\\fluxface\\fluxface.png")
print(url)

result = fal_client.subscribe(
    "fal-ai/kling-video/v1/pro/image-to-video",
    arguments={
        "prompt": "IMG_1741.JPG man wearing a black shirt faces the camera smiling widely at the end, half body shot, interior, casual setting, amateur video.",
        "image_url": url,
        "duration": 10,
        "aspect_ratio": '9:16'
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)