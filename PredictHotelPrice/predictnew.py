import numpy as np
import pandas as pd
import warnings
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import joblib

# Load data
hotel = pd.read_csv('hotels.csv')

# Handling date format inconsistencies
hotel['date'] = pd.to_datetime(hotel['date'], errors='coerce')

# Encode categorical columns
label_encoder_name = LabelEncoder()
hotel['name'] = label_encoder_name.fit_transform(hotel['name'])

label_encoder_place = LabelEncoder()
hotel['place'] = label_encoder_place.fit_transform(hotel['place'])

# Selecting features and target variable
X = hotel[['travelCode', 'userCode', 'days', 'price', 'total']]
y_name = hotel['name']
y_place = hotel['place']
y_price = hotel['price']

# Splitting the dataset into training and testing sets
X_train, X_test, y_name_train, y_name_test = train_test_split(X, y_name, test_size=0.2, random_state=42)
_, _, y_place_train, y_place_test = train_test_split(X, y_place, test_size=0.2, random_state=42)
_, _, y_price_train, y_price_test = train_test_split(X, y_price, test_size=0.2, random_state=42)

# Train the model for hotel name prediction
model_name = RandomForestClassifier()
model_name.fit(X_train, y_name_train)

# Train the model for hotel place prediction
model_place = RandomForestClassifier()
model_place.fit(X_train, y_place_train)

# Train the model for hotel price prediction
model_price = RandomForestRegressor()
model_price.fit(X_train, y_price_train)

# Save models and encoders
joblib.dump(model_name, 'model_name.joblib')
joblib.dump(model_place, 'model_place.joblib')
joblib.dump(model_price, 'model_price.joblib')
joblib.dump(label_encoder_name, 'label_encoder_name.joblib')
joblib.dump(label_encoder_place, 'label_encoder_place.joblib')

# Evaluating the models
y_name_pred = model_name.predict(X_test)
y_place_pred = model_place.predict(X_test)
y_price_pred = model_price.predict(X_test)

name_report = classification_report(y_name_test, y_name_pred)
place_report = classification_report(y_place_test, y_place_pred)
price_mse = mean_squared_error(y_price_test, y_price_pred)

print("Hotel Name Prediction Report:\n", name_report)
print("Hotel Place Prediction Report:\n", place_report)
print("Hotel Price Prediction Report:\n", price_mse)

# Example: Making a prediction
sample_data = pd.DataFrame({
    'travelCode': [100],
    'userCode': [2],
    'days': [4],
    'price': [165.99],
    'total': [663.96]
})

predicted_name = model_name.predict(sample_data)
predicted_place = model_place.predict(sample_data)
predicted_price = model_price.predict(sample_data)

print("Predicted Hotel Name:", label_encoder_name.inverse_transform(predicted_name))
print("Predicted Hotel Place:", label_encoder_place.inverse_transform(predicted_place))
print("Predicted Hotel Price:", predicted_price)

# Save the evaluation reports to files for later inspection
with open('name_report.txt', 'w') as f:
    f.write(name_report)
with open('place_report.txt', 'w') as f:
    f.write(place_report)
with open('price_mse.txt', 'w') as f:
    f.write(str(price_mse))
