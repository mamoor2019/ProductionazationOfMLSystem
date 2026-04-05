# Example of a Flask endpoint for model inference
from flask import Flask, request, jsonify
import pickle  # For model serialization
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder

# Initialize the SentenceTransformer model
model = SentenceTransformer('flax-sentence-embeddings/all_datasets_v4_MiniLM-L6')

# Load the trained classification model and scaler model
scaler_model = pickle.load(open("scaler.pkl", 'rb'))
pca_model = pickle.load(open("pca_model.pkl", 'rb'))
logistic_model = pickle.load(open("logistic_model_tuned.pkl", 'rb'))

# Create a function for prediction
def predict_price(input_data, lr_model, pca, scaler):
    # Prepare the input data
    text_columns = ['name']

    # Initialize an empty DataFrame
    df = pd.DataFrame([input_data])
    
    #filtering records based on relavent categories in the target variable
    #df=df[(df['gender']=='male') | (df['gender']=='female') ]
    
    
    # Encode userCode and company to numeric values
    label_encoder = LabelEncoder()

    df['company_encoded'] = label_encoder.fit_transform(df['company'])
    #df['gender_encoded'] = label_encoder.fit_transform(df['gender'])
    
    # Encode text-based columns and create embeddings
    for column in text_columns:
        df[column + '_embedding'] = df[column].apply(lambda text: model.encode(text))

    # Apply PCA separately to each text embedding column
    n_components = 23  # Adjust the number of components as needed
    text_embeddings_pca = np.empty((len(df), n_components * len(text_columns)))

    for i, column in enumerate(text_columns):
        embeddings = df[column + '_embedding'].values.tolist()
        embeddings_pca = pca.transform(embeddings)
        text_embeddings_pca[:, i * n_components:(i + 1) * n_components] = embeddings_pca

    # Combine text embeddings with other numerical features if available
    numerical_features = ['code','company_encoded','age']
    

    X_numerical = df[numerical_features].values

    # Combine PCA-transformed text embeddings and numerical features
    X = np.hstack((text_embeddings_pca, X_numerical))

    # Scale the data using the same scaler used during training
    X = scaler.transform(X)

    # Make predictions using the trained Linear Regression model
    y_pred = lr_model.predict(X)

    return y_pred[0]



app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def predict():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gender Prediction</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            padding: 20px;
            max-width: 500px;
            width: 100%;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], input[type="number"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        button {
            background-color: #007bff;
            color: #fff;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        .result {
            margin-top: 20px;
            padding: 10px;
            background-color: #dff0d8;
            border: 1px solid #d0e9c6;
            color: #3c763d;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Gender Prediction</h2>
        <form id="prediction-form">
            <div class="form-group">
                <label for="Usercode">User Code</label>
                <input type="text" id="Usercode" name="Usercode" required>
            </div>
            <div class="form-group">
                <label for="company_name">Company Name</label>
                <input type="text" id="company_name" name="company_name" required>
            </div>
            <div class="form-group">
                <label for="Username">User Name</label>
                <input type="text" id="Username" name="Username" required>
            </div>
            <div class="form-group">
                <label for="Traveller_Age">Age</label>
                <input type="number" id="Traveller_Age" name="Traveller_Age" required>
            </div>
            <button type="submit">Predict</button>
        </form>
        <div class="result" id="result" style="display:none;"></div>
    </div>
    <script>
        document.getElementById('prediction-form').addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            fetch('/predict', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                resultDiv.textContent = 'Predicted Gender: ' + data.prediction;
            })
            .catch(error => console.error('Error:', error));
        });
    </script>
</body>
</html>"""



    


@app.route('/predict', methods=['POST'])
def index():
    if request.method == 'POST':
        # Get input data from the form
        usercode = request.form.get('Usercode')
        company = request.form.get('company_name')
        name = request.form.get('Username')
        age = request.form.get('Traveller_Age')


        # Create a dictionary to store the input data
        data = {
            'code': usercode,
            'company': company,
            'name': name,
            'age': age,
           
        }

        # Perform prediction using the custom_input dictionary
        prediction = predict_price(data, logistic_model, pca_model, scaler_model)
        
        if prediction ==0:
            gender='female'
        else:
            gender='male'
        
        prediction = str(gender)
       

        return jsonify({'prediction':  prediction})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)





