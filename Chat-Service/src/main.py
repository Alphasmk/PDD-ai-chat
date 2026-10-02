from fastapi import FastAPI, UploadFile, File, Form
from src.infrastructure.cloud_provider.cloud_adapter import GoogleCloudProvider

app = FastAPI()
cloud_provider = GoogleCloudProvider()

@app.post("/")
async def get_response(image: UploadFile = File(...)):
    response = await cloud_provider.generate_response(
        image=await image.read(),
        mime_type=image.content_type,
        )
    return response