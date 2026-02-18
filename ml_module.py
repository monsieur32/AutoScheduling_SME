
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.preprocessing import LabelEncoder

class FJSPML:
    def __init__(self, model_path='models'):
        self.model_path = model_path
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
            
        self.clf = RandomForestClassifier(n_estimators=100, random_state=42)
        self.reg = RandomForestRegressor(n_estimators=100, random_state=42)
        self.le_material = LabelEncoder()
        
        self.is_trained = False

    def load_data(self, csv_path):
        """Loads data from CSV for training."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Data file not found: {csv_path}")
        return pd.read_csv(csv_path)

    def preprocess(self, df, training=True):
        """Prepares features (X) and targets (y)."""
        # Features: Process Steps, Material Group, Size, Complexity
        # We need to encode 'Material Group'
        
        df_clean = df.copy()
        
        if training:
            self.le_material.fit(df_clean['material_group'])
            # Save the encoder for inference
            joblib.dump(self.le_material, os.path.join(self.model_path, 'le_material.joblib'))
        else:
            # Load encoder if not in training mode
            self.le_material = joblib.load(os.path.join(self.model_path, 'le_material.joblib'))
            
            # Handle unknown labels in inference (fallback to a common one like 'C')
            # For simplicity in this demo, we assume known labels or handle error
            # In prod, we'd use a more robust encoder
            pass

        df_clean['material_code'] = self.le_material.transform(df_clean['material_group'])
        
        features = ['process_steps', 'material_code', 'size_mm', 'dxf_complexity']
        X = df_clean[features]
        
        y_clf = None
        y_reg = None
        
        if 'better_expert' in df_clean.columns:
            y_clf = df_clean['better_expert']
        if 'roi_improvement' in df_clean.columns:
            y_reg = df_clean['roi_improvement']
            
        return X, y_clf, y_reg

    def train(self, csv_path='schedule_log.csv'):
        """Trains the Classification and Regression models."""
        print(f"Loading data from {csv_path}...")
        df = self.load_data(csv_path)
        
        X, y_clf, y_reg = self.preprocess(df, training=True)
        
        # Split data
        X_train, X_test, y_clf_train, y_clf_test, y_reg_train, y_reg_test = train_test_split(
            X, y_clf, y_reg, test_size=0.2, random_state=42
        )
        
        # Train Classifier (Should we use Expert?)
        print("Training Classifier...")
        self.clf.fit(X_train, y_clf_train)
        acc = accuracy_score(y_clf_test, self.clf.predict(X_test))
        print(f"-> Classifier Accuracy: {acc:.2f}")
        
        # Train Regressor (How much improvement?)
        print("Training Regressor...")
        self.reg.fit(X_train, y_reg_train)
        mse = mean_squared_error(y_reg_test, self.reg.predict(X_test))
        print(f"-> Regressor MSE: {mse:.4f}")
        
        # Save models
        joblib.dump(self.clf, os.path.join(self.model_path, 'clf_model.joblib'))
        joblib.dump(self.reg, os.path.join(self.model_path, 'reg_model.joblib'))
        self.is_trained = True
        print("Models saved successfully.")

    def load_models(self):
        """Loads trained models from disk."""
        try:
            self.clf = joblib.load(os.path.join(self.model_path, 'clf_model.joblib'))
            self.reg = joblib.load(os.path.join(self.model_path, 'reg_model.joblib'))
            self.le_material = joblib.load(os.path.join(self.model_path, 'le_material.joblib'))
            self.is_trained = True
            return True
        except FileNotFoundError:
            print("Models not found. Please train first.")
            return False

    def predict_adjust(self, job_dict):
        """
        Input: Dictionary with job details (material_group, process_steps, size_mm, dxf_complexity)
        Output: Dict with recommendation
        """
        if not self.is_trained:
            if not self.load_models():
                return {"error": "Model not trained"}

        # Convert input dict to DataFrame
        input_df = pd.DataFrame([job_dict])
        
        try:
            X, _, _ = self.preprocess(input_df, training=False)
            
            should_adjust = self.clf.predict(X)[0]
            predicted_roi = self.reg.predict(X)[0]
            
            return {
                "use_expert_rule": bool(should_adjust),
                "predicted_roi": round(predicted_roi, 3),
                "confidence": round(max(self.clf.predict_proba(X)[0]), 2)
            }
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Test Run
    ml_system = FJSPML()
    if os.path.exists('schedule_log.csv'):
        ml_system.train('schedule_log.csv')
        
        # Test Prediction
        test_job = {
            "process_steps": 14,
            "material_group": "I", # Hard material
            "size_mm": 2000,
            "dxf_complexity": 0.6
        }
        print("\nTest Prediction (Hard Job):")
        print(ml_system.predict_adjust(test_job))
        
        test_job_easy = {
            "process_steps": 5,
            "material_group": "A", # Easy material
            "size_mm": 500,
            "dxf_complexity": 0.1
        }
        print("\nTest Prediction (Easy Job):")
        print(ml_system.predict_adjust(test_job_easy))
    else:
        print("schedule_log.csv not found. Run demo_log.py first.")
