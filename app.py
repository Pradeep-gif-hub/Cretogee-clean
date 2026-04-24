from flask import Flask, render_template, request
import pickle
import pandas as pd
import os
import random
import requests

# Flask app
app = Flask(__name__)

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -------- LOAD MODEL FROM HUGGINGFACE --------
MODEL_URL = "https://huggingface.co/pradeep240818/cretogee-model/resolve/main/model.pkl"
model_path = os.path.join(BASE_DIR, "model.pkl")

if not os.path.exists(model_path):
    print("Downloading model...")
    r = requests.get(MODEL_URL)
    with open(model_path, "wb") as f:
        f.write(r.content)

model = pickle.load(open(model_path, "rb"))

# -------- LOAD DATASET --------
csv_path = os.path.join(BASE_DIR, "dataset.csv")
crater_data = pd.read_csv(csv_path)

crater_data = crater_data.rename(columns={
    'Flags_data': 'f',
    'ID': 'g',
    'Lat': 'h',
    'Lon': 'i',
    'Diam_km': 'j',
    'Lat_new': 'k',
    'Lon_new': 'l'
})

crater_data = crater_data[['g', 'h', 'i', 'j']].dropna()

# -------- ROUTES --------

@app.route('/')
def home():
    return render_template('lun3.html')  

@app.route('/project')
def project():
    return render_template('lun.html')       

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # ✅ Use STATIC folder (IMPORTANT)
        crater_folder = os.path.join(BASE_DIR, "static", "images", "crater")
        random_image = random.choice(os.listdir(crater_folder))
        random_num = random.uniform(88, 98)

        # Get form data
        lat = float(request.form['latitude'])
        lon = float(request.form['longitude'])
        dia = float(request.form['diameter'])

        input_data = pd.DataFrame([[lat, lon, dia]], columns=['h', 'i', 'j'])

        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0][1] * 100

        result_text = 'Likely Crater' if prediction == 1 else 'Unlikely Crater'
        prob_text = f"{probability:.2f}%"
        model_accuracy = 91.78

        # Nearby crater logic
        ad, ae, af = 5, 5, 10
        nearby_craters = crater_data[
            (crater_data['h'] >= lat - ad) & (crater_data['h'] <= lat + ad) &
            (crater_data['i'] >= lon - ae) & (crater_data['i'] <= lon + ae) &
            (crater_data['j'] >= dia - af) & (crater_data['j'] <= dia + af)
        ]

        nearby_count = len(nearby_craters)

        largest_crater = None
        smallest_crater = None
        crater_samples = []

        if nearby_count > 0:
            largest = nearby_craters.loc[nearby_craters['j'].idxmax()]
            smallest = nearby_craters.loc[nearby_craters['j'].idxmin()]

            largest_crater = {
                'size': largest['j'],
                'lat': largest['h'],
                'lon': largest['i']
            }

            smallest_crater = {
                'size': smallest['j'],
                'lat': smallest['h'],
                'lon': smallest['i']
            }

            sample_craters = nearby_craters.sample(min(6, nearby_count))
            for _, row in sample_craters.iterrows():
                crater_samples.append({
                    'id': row['g'],
                    'lat': row['h'],
                    'lon': row['i'],
                    'size': row['j']
                })

        return render_template(
            'result.html',
            random_image=random_image,
            random_num=random_num,
            result=result_text,
            probability=prob_text,
            nearby_count=nearby_count,
            largest_crater=largest_crater,
            smallest_crater=smallest_crater,
            crater_samples=crater_samples,
            model_accuracy=model_accuracy
        )

    except Exception as e:
        return f"Error: {e}"

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)