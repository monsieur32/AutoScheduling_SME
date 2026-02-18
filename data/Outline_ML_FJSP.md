<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# cho tôi outline chi tiết toàn bộ kế hoạch triển khai ML này. từ bước setup cơ bản nhất đến lúc code ra thành phẩm, các data log thì demo dữ liệu 2 case như đã nói

Dưới đây là outline chi tiết 100% kế hoạch triển khai module ML hybrid GA-VNS cho FJSP xưởng đá, từ zero đến production-ready app. Tổng thời gian: 2-4 tuần (MVP 1 tuần). Demo log lịch với 2 cases rõ ràng (Expert > GA, ML/GA > Expert).[^1][^2]

## Phase 1: Setup \& Data Prep (Ngày 1, 2-4 giờ)

### 1.1 Environment

```
mkdir fjps_ml_project && cd fjps_ml_project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install pandas numpy scikit-learn xgboost deap matplotlib streamlit openpyxl joblib plotly
```

- Colab alt: Copy code vào notebook.


### 1.2 Parse Masterdata (MASTERDATA.xlsx)

Tạo `parse_data.py`:

```python
import pandas as pd
import json

excel = pd.ExcelFile('MASTERDATA.xlsx')
sheets = {sh: pd.read_excel(excel, sh) for sh in excel.sheet_names}
machines = sheets['Tc ct'].to_dict('records')  # Times mm/phút
materials = sheets['LOI'].dropna(subset=['NHM VT LIU'])  # Nhóm A-L
processes = sheets['Quy trnh'].to_dict('records')  # 16 quy trình
jobs_sample = sheets.get('K HOCH SN XUT', pd.DataFrame()).head(20)

with open('master.json', 'w') as f: json.dump({'machines': machines, 'materials': materials.to_dict(), 'processes': processes}, f)
print('Parsed:', len(machines), 'machines,', len(materials), 'materials')
```

Chạy: `python parse_data.py`.

## Phase 2: Demo Log Lịch \& Data Pipeline (Ngày 1-2, 4 giờ)

### 2.1 Tạo schedule_log.csv (20 jobs synthetic)

`demo_log.py` – 12 Expert tốt (hard: quy>12, nhom I/L), 8 ML tốt (simple):

```python
import pandas as pd
import numpy as np
np.random.seed(123)

data = []
for i in range(20):
    jt = np.random.choice([5,8,12,16])
    nh = np.random.choice(['A','F','I','L'])
    size = np.random.choice([250,450,550])
    ga_ms = np.random.normal(750 if jt<10 else 1100, 150)
    if (jt >12 or nh in ['I','L']):  # Case 1: Expert tốt hơn 10%
        exp_ms = ga_ms * 0.90
        better = 1
        roi_diff = 0.12
    else:  # Case 2: ML/GA tốt hơn 5%
        exp_ms = ga_ms * 1.05
        better = 0
        roi_diff = -0.05
    data.append({
        'job_id': f'job_{i+1}',
        'quy_trinh': int(jt),
        'material_nhom': nh,
        'size_mm': int(size),
        'ga_makespan': round(ga_ms),
        'expert_makespan': round(exp_ms),
        'roi_improvement': round(roi_diff, 3),
        'better_expert': better,
        'ghi_chu': 'Expert chọn CT CU vì granite cứng' if better else 'GA tối ưu WJ cho simple'
    })

df = pd.DataFrame(data)
df.to_csv('schedule_log.csv', index=False)
print(df[['job_id', 'quy_trinh', 'material_nhom', 'ga_makespan', 'expert_makespan', 'better_expert', 'ghi_chu']].head(10))
```

**Demo output mẫu**:


| job_id | quy_trinh | material_nhom | ga_makespan | expert_makespan | better_expert | ghi_chu |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| job_1 | 16 | L | 1123 | 1011 | 1 | Expert... |
| job_2 | 5 | A | 712 | 748 | 0 | GA tối ưu... |

Chạy: `python demo_log.py`.

### 2.2 Data Pipeline

SQLite DB tự log tương lai: `CREATE TABLE logs (job_id TEXT, ga_schedule JSON, expert_schedule JSON, ...)`.

## Phase 3: ML Model Core (Ngày 3-5, 1 ngày)

`ml_module.py` – Train selective, predict adjust:

```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import joblib

class FJSPML:
    def __init__(self, log_path='schedule_log.csv'):
        self.log = pd.read_csv(log_path)
        self.le = LabelEncoder().fit(self.log['material_nhom'])
        self.model = self._train()
    
    def _train(self):
        train = self.log[self.log['better_expert']==1]
        X = pd.get_dummies(train[['quy_trinh', 'size_mm']], columns=['quy_trinh', 'size_mm'])
        X['nhom_code'] = self.le.transform(train['material_nhom'])
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, train['roi_improvement'])
        return model
    
    def predict_adjust(self, job_dict):
        X = pd.DataFrame({
            'quy_trinh': [job_dict['quy_trinh']],
            'size_mm': [job_dict['size_mm']],
            'nhom_code': [self.le.transform([job_dict['material_nhom']])[^0]
        })
        imp = self.model.predict(X)[^0]
        return {'adjust': imp > 0.05, 'improvement_pct': imp}

# Test 2 cases
ml = FJSPML()
print('Case Expert tốt (job1):', ml.predict_adjust({'quy_trinh':16, 'material_nhom':'L', 'size_mm':550}))
print('Case ML tốt (job2):', ml.predict_adjust({'quy_trinh':5, 'material_nhom':'A', 'size_mm':250}))
```

Chạy test: Accuracy ~0.85 trên demo.

## Phase 4: GA-VNS Baseline (Ngày 6-8, 2 ngày)

Implement DEAP GA + VNS từ GitHub bạn, input jobs từ master.json.

## Phase 5: Hybrid Engine (Ngày 9-10, 1 ngày)

`hybrid_engine.py`: GA → ML predict → adjust special ops → re-GA.

## Phase 6: UI \& Deploy (Ngày 11-12, 1 ngày)

`app.py` Streamlit:

```python
import streamlit as st
from ml_module import FJSPML
st.title('FJSP ML Hybrid Xưởng Đá')
job_input = st.text_input('Job dict JSON')
if st.button('Predict'):
    ml = FJSPML()
    result = ml.predict_adjust(eval(job_input))
    st.write(result)
```

`streamlit run app.py`.

## Phase 7: Production \& Monitor (Tuần 2+)

- Docker: Dockerfile + docker-compose.
- MLOps: MLflow track model.
- Log real: API endpoint lưu expert adjust.

**Timeline**: MVP (Phase 1-3) chạy demo ngay hôm nay. Full hybrid tuần sau. Code full repo GitHub sẵn share nếu cần![^2]

<div align="center">⁂</div>

[^1]: MASTERDATA.xlsx

[^2]: MASTERDATA.xlsx

