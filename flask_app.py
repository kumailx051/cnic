from fastapi import FastAPI, File, UploadFile, HTTPException
from tensorflow.keras.models import load_model
import numpy as np
from io import BytesIO
from PIL import Image

app = FastAPI(title="CNIC Classifier API")

# Load model once on startup (place your model.h5 in the same folder)
MODEL_PATH = "model.h5"
model = load_model(MODEL_PATH)

def preprocess_pil(img: Image.Image):
    """Resize, normalize, and expand dims to prepare image for model."""
    img = img.resize((224, 224))
    arr = np.array(img).astype("float32") / 255.0
    if arr.ndim == 2:  # grayscale → RGB
        arr = np.stack([arr, arr, arr], axis=-1)
    arr = np.expand_dims(arr, axis=0)  # shape -> (1,224,224,3)
    return arr

@app.get("/")
async def root():
    """Health check route to verify server is running."""
    return {"status": "running", "message": "CNIC classifier API is live"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Accepts an image file and returns classification result."""
    if file.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Upload an image file.")

    contents = await file.read()
    try:
        img = Image.open(BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image.")

    x = preprocess_pil(img)
    pred = float(model.predict(x)[0][0])   # model outputs a single score
    label = "not_cnic" if pred > 0.5 else "cnic"

    return {"score": pred, "label": label}
