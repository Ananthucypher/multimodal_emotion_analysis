# Audio Emotion Models

This directory should contain the pre-trained audio emotion recognition models.

## Required Files

1. **emotion_model_4class.keras** - Keras/TensorFlow model for audio emotion classification
2. **label_encoder_4class.pkl** - Pickle file containing the label encoder

## Model Details

- **Classes**: 4 emotions (neutral, happy, sad, angry)
- **Input**: Audio features (MFCC, Chroma, Spectral Contrast, ZCR)
- **Feature Shape**: 174 timesteps × 60 features

## If Models Are Missing

The backend will fall back to demonstration values when models are not present.
To train your own model, use datasets like:
- RAVDESS (Ryerson Audio-Visual Database)
- CREMA-D
- TESS (Toronto Emotional Speech Set)

## Obtaining Pre-trained Models

Contact the project maintainer or train using the provided training scripts.
