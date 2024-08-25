# models/model_loader.py

from tensorflow.keras.models import load_model
import os

def load_classification_model():
    model_path = os.path.join(os.getcwd(), 'models', 'fine_tuned_vgg16.h5')
    model = load_model(model_path)
    return model
