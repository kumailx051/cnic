import uvicorn
from fastapi import FastAPI, UploadFile, File
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import requests
import os

app = FastAPI()

MODEL_URL = "https://cnicmodel.blob.core.windows.net/cnicmodel/cnic_model.h5"
MODEL_PATH = "cnic_model.h5"

# Download the model if not already present
if not os.path.exists(MODEL_PATH):
    print("Downloading model from Azure Blob Storage...")
    r = requests.get(MODEL_URL)
    with open(MODEL_PATH, "wb") as f:
        f.write(r.content)
    print("Model downloaded successfully.")

# Load the model
model = load_model(MODEL_PATH)

@app.get("/")
def home():
    return {"message": "FastAPI is running with CNIC model!"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Preprocess image
    img = image.load_img(file_path, target_size=(224, 224))  # adjust size based on your model
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0  # normalize

    # Predict
    prediction = model.predict(img_array)
    os.remove(file_path)

    return {"prediction": prediction.tolist()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
