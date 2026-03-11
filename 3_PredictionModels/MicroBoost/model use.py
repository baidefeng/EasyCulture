import pandas as pd
import os
import pickle

# Specify the model directory and data file path
model_dir = 'model'
data_path = 'try_use.csv'
result_path = 'result_use.csv'

# Load the data (assuming the first column is the index)
data = pd.read_csv(data_path, index_col=0)

# Initialize a DataFrame to store prediction results, using the data's index as the index for the results DataFrame
results = pd.DataFrame(index=data.index)

# Iterate through each model file in the model directory
for model_file in os.listdir(model_dir):
    if model_file.endswith('.pkl'):  # Ensure only .pkl files are processed
        # Full path to the model file
        full_model_path = os.path.join(model_dir, model_file)

        # Load the model
        with open(full_model_path, 'rb') as file:
            model = pickle.load(file)

        # Use the model to make predictions
        pred = model.predict(data)

        # Add the prediction results to the results DataFrame, column name is the model file name, but remove the ".pkl" suffix
        model_name = model_file[:-4]  # Remove the ".pkl" from the file name
        results[model_name] = pred

# Save the results DataFrame as a CSV file
results.to_csv(result_path)
