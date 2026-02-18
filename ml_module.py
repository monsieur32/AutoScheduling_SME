
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
        """Tải dữ liệu từ CSV để huấn luyện."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {csv_path}")
        return pd.read_csv(csv_path)

    def preprocess(self, df, training=True):
        """Chuẩn bị đặc trưng (X) và mục tiêu (y)."""
        # Đặc trưng: Bước gia công, Nhóm vật liệu, Kích thước, Độ phức tạp
        # Cần mã hóa hóa 'Nhóm vật liệu'
        
        df_clean = df.copy()
        
        if training:
            self.le_material.fit(df_clean['material_group'])
            # Lưu bộ mã hóa để suy luận sau này
            joblib.dump(self.le_material, os.path.join(self.model_path, 'le_material.joblib'))
        else:
            # Tải bộ mã hóa nếu không phải chế độ huấn luyện
            self.le_material = joblib.load(os.path.join(self.model_path, 'le_material.joblib'))
            
            # Xử lý nhãn lạ khi suy luận (fallback về nhãn phổ biến như 'C')
            # Để đơn giản trong demo này, giả định nhãn đã biết hoặc bỏ qua lỗi
            # Trong thực tế, cần bộ mã hóa mạnh mẽ hơn
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
        """Huấn luyện mô hình Phân loại và Hồi quy."""
        print(f"Đang tải dữ liệu từ {csv_path}...")
        df = self.load_data(csv_path)
        
        X, y_clf, y_reg = self.preprocess(df, training=True)
        
        # Chia tách dữ liệu
        X_train, X_test, y_clf_train, y_clf_test, y_reg_train, y_reg_test = train_test_split(
            X, y_clf, y_reg, test_size=0.2, random_state=42
        )
        
        # Huấn luyện Phân loại (Có nên dùng Chuyên gia?)
        print("Đang huấn luyện Bộ phân loại...")
        self.clf.fit(X_train, y_clf_train)
        acc = accuracy_score(y_clf_test, self.clf.predict(X_test))
        print(f"-> Độ chính xác Phân loại: {acc:.2f}")
        
        # Huấn luyện Hồi quy (Cải thiện bao nhiêu?)
        print("Đang huấn luyện Bộ hồi quy...")
        self.reg.fit(X_train, y_reg_train)
        mse = mean_squared_error(y_reg_test, self.reg.predict(X_test))
        print(f"-> Sai số Hồi quy (MSE): {mse:.4f}")
        
        # Lưu mô hình
        joblib.dump(self.clf, os.path.join(self.model_path, 'clf_model.joblib'))
        joblib.dump(self.reg, os.path.join(self.model_path, 'reg_model.joblib'))
        self.is_trained = True
        print("Lưu mô hình thành công.")

    def load_models(self):
        """Tải mô hình đã huấn luyện từ ổ cứng."""
        try:
            self.clf = joblib.load(os.path.join(self.model_path, 'clf_model.joblib'))
            self.reg = joblib.load(os.path.join(self.model_path, 'reg_model.joblib'))
            self.le_material = joblib.load(os.path.join(self.model_path, 'le_material.joblib'))
            self.is_trained = True
            return True
        except FileNotFoundError:
            print("Không tìm thấy mô hình. Vui lòng huấn luyện trước.")
            return False

    def predict_adjust(self, job_dict):
        """
        Đầu vào: Dict chi tiết job (material_group, process_steps, size_mm, dxf_complexity)
        Đầu ra: Dict khuyến nghị
        """
        if not self.is_trained:
            if not self.load_models():
                return {"error": "Mô hình chưa được huấn luyện"}

        # Chuyển đổi dict đầu vào thành DataFrame
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
    # Chạy thử nghiệm
    ml_system = FJSPML()
    if os.path.exists('schedule_log.csv'):
        ml_system.train('schedule_log.csv')
        
        # Dự đoán thử
        test_job = {
            "process_steps": 14,
            "material_group": "I", # Vật liệu cứng
            "size_mm": 2000,
            "dxf_complexity": 0.6
        }
        print("\nDự đoán thử (Job Khó):")
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
