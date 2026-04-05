#Final Flask Code
# Create a function for prediction
import os
import pickle
import pandas as pd
from flask import Flask, request, jsonify

# Models will be loaded lazily when needed
scaler_model = None
rf_model = None


def load_models():
    global scaler_model, rf_model
    if scaler_model is None or rf_model is None:
        base_path = os.path.dirname(os.path.abspath(__file__))
        scaler_path = os.path.join(base_path, 'scaling.pkl')
        rf_path = os.path.join(base_path, 'rf_model.pkl')

        scaler_model = pickle.load(open(scaler_path, 'rb'))
        rf_model = pickle.load(open(rf_path, 'rb'))






def predict_price(input_data, model, scaler):
    # Prepare the input data

    # Initialize an empty DataFrame
    df_input2 = pd.DataFrame([input_data])

    # Independent features
    X = df_input2

    # Scale the data using the same scaler used during training
    X = scaler.transform(X)

    # Make predictions using the trained Decision model
    y_prediction = model.predict(X)

    return y_prediction[0]


app = Flask(__name__)


@app.route('/',
           methods=['GET', 'POST'])
def predict():
    return """

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Price Prediction</title>
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding: 0;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        h1 {
            color: #007BFF;
            font-size: 36px;
            margin-bottom: 20px;
        }

        form {
            text-align: left;
        }

        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 15px;
            margin: 15px 0;
            border: none;
            border-bottom: 2px solid #007BFF;
            font-size: 18px;
            background-color: transparent;
            color: #333;
            transition: border-bottom 0.3s ease;
        }

        input[type="text"]:focus,
        input[type="number"]:focus,
        select:focus {
            border-bottom: 2px solid #0056b3;
            outline: none;
        }

        input[type="submit"] {
            background-color: #007BFF;
            color: #fff;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 20px;
            transition: background-color 0.3s ease;
        }

        input[type="submit"]:hover {
            background-color: #0056b3;
        }

        p#prediction {
            margin-top: 20px;
            font-size: 24px;
            color: #007BFF;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Flight Price Prediction</h1>
        <form action="/predict" method="POST">
            <b>Select a Boarding City</b><br><br>
            <select name="from">
                <option value="Aracaju">Aracaju</option>
                <option value="Brasilia">Brasilia</option>
                <option value="Campo_Grande">Campo Grande</option>
                <option value="Florianopolis">Florianopolis</option>
                <option value="Natal">Natal</option>
                <option value="Recife">Recife</option>
                <option value="Rio_de_Janeiro">Rio de Janeiro</option>
                <option value="Salvador">Salvador</option>
                <option value="Sao_Paulo">Sao Paulo</option>
            </select>

            <br><br><b>Select a Destination City</b><br><br>
            <select name="Destination">
                <option value="Aracaju">Aracaju</option>
                <option value="Brasilia">Brasilia</option>
                <option value="Campo_Grande">Campo Grande</option>
                <option value="Florianopolis">Florianopolis</option>
                <option value="Natal">Natal</option>
                <option value="Recife">Recife</option>
                <option value="Rio_de_Janeiro">Rio de Janeiro</option>
                <option value="Salvador">Salvador</option>
                <option value="Sao_Paulo">Sao Paulo</option>
            </select>

            <br><br><b>Select a Flight Type</b><br><br>
            <select name="flightType">
                <option value="premium">Premium</option>
                <option value="economic">Economic</option>
                <option value="firstClass">First Class</option>
            </select>

            <br><br><b>Select Agency</b><br><br>
            <select name="agency">
                <option value="FlyingDrops">FlyingDrops</option>
                <option value="Rainbow">Rainbow</option>
                <option value="CloudFy">CloudFy</option>
            </select>

            <br><br><label for="day">Day:</label>
            <input type="number" name="day" min="1" max="31" placeholder="Travel day" value="5">

            <label for="week_no">Week No:</label>
            <input type="number" name="week_no" min="1" max="53" placeholder="Travel Week No" value="7">

            <label for="week_day">Week Day:</label>
            <input type="number" name="week_day" min="1" max="7" placeholder="Travel Week Day" value="5">

            <input type="submit" value="Predict">
        </form>
        <p id="prediction"></p>
    </div>
</body>
</html>



    """


@app.route('/predict', methods=['POST'])
def index():
    if request.method == 'POST':
        load_models()  # Load models when needed
        
        # Get input data from the form
        boarding = str(request.form.get('from'))
        destination = str(request.form.get('Destination'))
        selected_flight_class = str(request.form.get('flightType'))
        selected_agency = str(request.form.get('agency'))
        week_no = int(request.form.get('week_no'))
        week_day = int(request.form.get('week_day'))
        day = int(request.form.get('day'))

        boarding = 'from_' + boarding
        boarding_city_list = ['from_Florianopolis (SC)',
                              'from_Sao_Paulo (SP)',
                              'from_Salvador (BH)',
                              'from_Brasilia (DF)',
                              'from_Rio_de_Janeiro (RJ)',
                              'from_Campo_Grande (MS)',
                              'from_Aracaju (SE)',
                              'from_Natal (RN)',
                              'from_Recife (PE)']

        destination = 'destination_' + destination
        destination_city_list = ['destination_Florianopolis (SC)',
                                 'destination_Sao_Paulo (SP)',
                                 'destination_Salvador (BH)',
                                 'destination_Brasilia (DF)',
                                 'destination_Rio_de_Janeiro (RJ)',
                                 'destination_Campo_Grande (MS)',
                                 'destination_Aracaju (SE)',
                                 'destination_Natal (RN)',
                                 'destination_Recife (PE)']

        selected_flight_class = 'flightType_' + selected_flight_class
        class_list = ['flightType_economic',
                      'flightType_firstClass',
                      'flightType_premium']

        selected_agency = 'agency_' + selected_agency
        agency_list = ['agency_Rainbow',
                       'agency_CloudFy',
                       'agency_FlyingDrops']

        travel_dict = dict()

        for city in boarding_city_list:
            if city[:-5] != boarding:
                travel_dict[city] = 0
            else:
                travel_dict[city] = 1
        for city in destination_city_list:
            if city[:-5] != destination:
                travel_dict[city] = 0
            else:
                travel_dict[city] = 1
        for flight_class in class_list:
            if flight_class != selected_flight_class:
                travel_dict[flight_class] = 0
            else:
                travel_dict[selected_flight_class] = 1
        for agency in agency_list:
            if agency != selected_agency:
                travel_dict[agency] = 0
            else:
                travel_dict[selected_agency] = 1
        travel_dict['week_no'] = week_no
        travel_dict['week_day'] = week_day
        travel_dict['day'] = day

        # Use loaded models from load_models()
        if scaler_model is None or rf_model is None:
            load_models()

        predicted_price = str(round(predict_price(travel_dict, rf_model, scaler_model), 2))

        return jsonify({'prediction': predicted_price})


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)
