<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Kế Hoạch Triển Khai Toàn Diện ML Hybrid FJSP Cho Xưởng Đá (2026)

## 1. Lý Do Hình Thành Bài Toán

GA-VNS đã tối ưu 80% FJSP (lập lịch linh hoạt), nhưng **case đặc biệt** (thiết kế phức tạp, vật liệu cứng như Granite L/Quartz I, quy trình 12-16) cần **kinh nghiệm quản lý** chọn máy phù hợp hơn (CT CU thay WJ, CMS1 thay CMS2), cải thiện ROI 5-15%. ML học diff này → tự động hóa 90%, giảm makespan 10%, scale xưởng Tây Ninh.[^1][^2]

## 2. Mục Tiêu

### Ngắn hạn (1 tháng): MVP

- Hybrid GA-ML predict adjust cho special cases, test 20 jobs → ROI +8%.
- UI Streamlit dashboard Gantt + predict.


### Trung hạn (3 tháng): Production

- Real log 100+ jobs, accuracy 85%, tự động 70% lịch (quản lý confirm).
- Tích hợp ERP kho vật liệu, mobile scan QR.


### Dài hạn (12 tháng): Autonomous Manager

- RL agent thay 90% quản lý (self-optimize policy).
- Scale 5 xưởng, ROI +25%, publish paper/case study VN manufacturing.

**KPIs**: Makespan giảm 15%, throughput +20%, expert time -80%.

## 3. Outline Triển Khai Chi Tiết (5 Tuần MVP)

### Tuần 1: Foundation \& Data (Ngày 1-5)

1. **Setup (1h)**:

```
mkdir fjps_ml && cd fjps_ml
python -m venv venv && source venv/bin/activate
pip install pandas numpy scikit-learn xgboost deap plotly streamlit openpyxl joblib mlflow docker
git init && git add .
```

2. **Parse Masterdata (2h)**: `parse_data.py` → master.json (machines 10+, materials 100+, processes 16, jobs 170+).[^2]
3. **Demo Log Lịch (2h)**: `demo_log.py` → schedule_log.csv (20 jobs):
    - **Case 1 Expert > GA (12 jobs)**: quy>12/nhom I/L → expert_ms = ga*0.9, roi+12%.
    - **Case 2 ML/GA > Expert (8 jobs)**: quy<10/nhom A/F → expert_ms = ga*1.05, roi-5%.
Sample:
| job_id | quy_trinh | nhom | ga_ms | exp_ms | better_exp | ghi_chu |
|--------|-----------|------|-------|--------|------------|---------|
| job1  | 16       | L    | 1120 | 1008  | 1         | CT CU cứng tốt hơn |
| job2  | 5        | A    | 720  | 756   | 0         | GA WJ optimal |

### Tuần 2: ML Core (Ngày 6-10)

4. **ML Module (4h)**: `fjps_ml.py` – RandomForest selective train (better_exp=1):

```python
class FJSPML:
    def train(self): ...  # Features: quy_trinh, nhom_code, size → roi_improvement
    def predict_adjust(job): return {'adjust': imp>5%, 'roi_pct': imp}
```

Test: Expert case → adjust=True (+12%), ML case → False.
5. **GA-VNS Baseline (2 ngày)**: DEAP GA + VNS (từ GitHub), fitness=makespan.
6. **Hybrid Engine**: GA → ML predict → adjust ops → re-GA.

### Tuần 3: UI \& Test (Ngày 11-15)

7. **Streamlit App**: `app.py` – Input jobs JSON → Hybrid schedule → Gantt Plotly.
8. **A/B Test**: 20 demo jobs → so sánh hybrid vs GA thuần (ROI +9%).

### Tuần 4: Deploy \& Real Data (Ngày 16-20)

9. **SQLite Log Real**: API lưu expert_adjust.
10. **Docker**: Dockerfile + compose (Streamlit + DB).
11. **MLflow**: Track models/versions.

### Tuần 5: Scale \& Monitor (Ngày 21-25)

12. **Retraining Pipeline**: Cron weekly trên new log.
13. **Mobile QR Scan**: Flutter notify worker.

## 4. Hoạch Định Lâu Dài (6-12 Tháng)

| Phase | Timeline | Features | KPIs |
| :-- | :-- | :-- | :-- |
| MVP | Tháng 1 | Hybrid predict | ROI +8%, 70 jobs |
| Prod | Tháng 3 | Real log, ERP | Accuracy 85%, 500 jobs |
| Agentic | Tháng 6 | RL (PPO Gym FJSP) | Autonomous 70% |
| Enterprise | Tháng 12 | Multi-xưởng, API | ROI +25%, 5 xưởng |

**Rủi ro \& Mitigate**: Data ít → synthetic + active learning; drift → monitor weekly.
**Chi phí**: ~0đ (open-source), thời gian 1 dev part-time.

Chạy Phase 1 ngay: Copy code → test demo log/ML! Repo Git sẵn nếu cần.[^1]

<div align="center">⁂</div>

[^1]: MASTERDATA.xlsx

[^2]: MASTERDATA.xlsx

