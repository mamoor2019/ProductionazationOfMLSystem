import streamlit as st
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

# Load the trained models and encoders
model_name = joblib.load('model_name.joblib')
model_place = joblib.load('model_place.joblib')
model_price = joblib.load('model_price.joblib')
label_encoder_name = joblib.load('label_encoder_name.joblib')
label_encoder_place = joblib.load('label_encoder_place.joblib')

# Define the prediction function
def predict_hotel(travelCode, userCode, days, price, total):
    sample_data = pd.DataFrame({
        'travelCode': [travelCode],
        'userCode': [userCode],
        'days': [days],
        'price': [price],
        'total': [total]
    })
    
    predicted_name = model_name.predict(sample_data)
    predicted_place = model_place.predict(sample_data)
    predicted_price = model_price.predict(sample_data)

    return {
        'name': label_encoder_name.inverse_transform(predicted_name)[0],
        'place': label_encoder_place.inverse_transform(predicted_place)[0],
        'price': predicted_price[0]
    }

# Streamlit app
st.title("Hotel Prediction App")

# Input fields
travelCode = st.number_input("Travel Code", min_value=0)
userCode = st.number_input("User Code", min_value=0)
days = st.number_input("Days", min_value=1)
price = st.number_input("Price", min_value=0.0)
total = st.number_input("Total", min_value=0.0)

if st.button("Predict"):
    result = predict_hotel(travelCode, userCode, days, price, total)
    st.write(f"Predicted Hotel Name: {result['name']}")
    st.write(f"Predicted Hotel Place: {result['place']}")
    st.write(f"Predicted Hotel Price: {result['price']}")