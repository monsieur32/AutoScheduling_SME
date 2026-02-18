
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# Nhập Module Tùy chỉnh
from dxf_parser import extract_cutting_info
from ml_module import FJSPML
from hybrid_engine import HybridEngine

# ==========================================
# 0. CẤU HÌNH & THIẾT LẬP
# ==========================================
st.set_page_config(page_title="Hệ thống Lập lịch Sản xuất", layout="wide")

# Khởi tạo Session State
if 'jobs_queue' not in st.session_state:
    st.session_state.jobs_queue = [] # Danh sách công việc

if 'scheduled_jobs' not in st.session_state:
    st.session_state.scheduled_jobs = [] # Kết quả từ Hybrid Engine

if 'ml_system' not in st.session_state:
    st.session_state.ml_system = FJSPML()
    # Thử tải mô hình đã huấn luyện
    st.session_state.ml_system.load_models()

# ==========================================
# 1. THANH BÊN & ĐIỀU HƯỚNG
# ==========================================
st.sidebar.markdown("## ĐIỀU HƯỚNG")
tab_selection = st.sidebar.radio("Chọn chức năng:", [
    "1. Nhập liệu đơn hàng", 
    "2. Bảng điều độ sản xuất",
    "3. Giao diện Máy (Công nhân)"
], label_visibility="collapsed")

st.sidebar.markdown("---")
# with st.sidebar.expander("Thông tin hệ thống", expanded=True):
#     st.write("Phiên bản: 1.0.0")
#     st.write("Module tích hợp:")
#     st.write("- Phân tích DXF")
#     st.write("- Random Forest AI")
#     st.write("- Genetic Algorithm")

# ==========================================
# TAB 1: NHẬP LIỆU (PLANNER)
# ==========================================
if tab_selection == "1. Nhập liệu đơn hàng":
    st.markdown("### NHẬP ĐƠN HÀNG MỚI")
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 1.5], gap="large")
        
        with col1:
            st.markdown("#### Thông tin đầu vào")
            uploaded_file = st.file_uploader("Tải lên bản vẽ (.dxf)", type=['dxf'])
            
            c1, c2 = st.columns(2)
            with c1:
                material = st.selectbox("Nhóm Vật Liệu", ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"], index=2)
            with c2:
                quantity = st.number_input("Số lượng (tấm)", min_value=1, value=1)
            
            process_type = st.selectbox("Quy trình Gia công", [
                "Cắt thô (Standard)", 
                "Cắt + Đánh bóng (Polishing)", 
                "Cắt + Soi cạnh + Đánh bóng (Complex)"
            ])
            
            process_map = {
                "Cắt thô (Standard)": 5,
                "Cắt + Đánh bóng (Polishing)": 8,
                "Cắt + Soi cạnh + Đánh bóng (Complex)": 14
            }
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_analyze = st.button("Phân tích & Thêm vào hàng đợi", use_container_width=True)

        with col2:
            st.markdown("#### Kết quả phân tích (DXF & AI)")
            
            if uploaded_file is not None and btn_analyze:
                # 1. Lưu file tạm
                temp_path = os.path.join("data", uploaded_file.name)
                os.makedirs("data", exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 2. Phân tích DXF
                with st.spinner("Đang xử lý dữ liệu..."):
                    dxf_info = extract_cutting_info(temp_path)
                    
                if dxf_info['status'] == 'success':
                    # Hiển thị chỉ số gọn gàng
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Tổng chiều dài (mm)", f"{dxf_info['total_len_mm']}")
                    m2.metric("Chiều dài cong (mm)", f"{dxf_info['curved_len_mm']}")
                    m3.metric("Tỷ lệ phức tạp", f"{dxf_info['complexity_ratio']}")
                    
                    st.divider()
                    
                    # 3. Dự đoán AI
                    job_data = {
                        "id": f"JOB-{len(st.session_state.jobs_queue)+1:03d}",
                        "material_group": material,
                        "process_steps": process_map[process_type],
                        "size_mm": dxf_info['total_len_mm'], 
                        "complexity": dxf_info['complexity_ratio'],
                        "quantity": quantity,
                        "operations": list(range(process_map[process_type]))
                    }
                    
                    ai_pred = st.session_state.ml_system.predict_adjust({
                        "process_steps": job_data['process_steps'],
                        "material_group": job_data['material_group'],
                        "size_mm": job_data['size_mm'],
                        "dxf_complexity": job_data['complexity']
                    })
                    
                    # 4. Hiển thị đánh giá AI (Sạch, không icon)
                    st.markdown("**Đánh giá từ AI:**")
                    if ai_pred.get('use_expert_rule'):
                        st.warning(
                            f"Phát hiện rủi ro cao (Đá cứng/Quy trình dài).\n"
                            f"Đề xuất: Kích hoạt chế độ chuyên gia (Ưu tiên cao, giảm tốc độ máy).\n"
                            f"Lợi ích dự kiến (ROI): +{ai_pred.get('predicted_roi', 0):.1%}"
                        )
                        job_data['ml_note'] = "Expert Intervention"
                    else:
                        st.info(
                            "Đơn hàng tiêu chuẩn. Đề xuất sử dụng thuật toán tối ưu tự động (GA)."
                        )
                        job_data['ml_note'] = "Standard GA"
                    
                    # Thêm vào hàng đợi
                    st.session_state.jobs_queue.append(job_data)
                    st.toast(f"Đã thêm {job_data['id']} vào hàng đợi.")
                    
                else:
                    st.error(f"Lỗi: {dxf_info['message']}")

# ==========================================
# TAB 2: DASHBOARD
# ==========================================
elif tab_selection == "2. Bảng điều độ sản xuất":
    st.markdown("### TRUNG TÂM ĐIỀU ĐỘ SẢN XUẤT")
    
    # Phần 1: Hàng đợi
    with st.expander("DANH SÁCH HÀNG ĐỢI CÔNG VIỆC", expanded=True):
        if len(st.session_state.jobs_queue) > 0:
            df_queue = pd.DataFrame(st.session_state.jobs_queue)
            
            # Hiển thị dataframe sạch sẽ
            st.dataframe(
                df_queue[['id', 'material_group', 'size_mm', 'complexity', 'ml_note']],
                use_container_width=True,
                hide_index=True
            )
            
            c_opt1, c_opt2 = st.columns([1, 4])
            with c_opt1:
                if st.session_state.ml_system.is_trained:
                    use_ml = st.checkbox("Kích hoạt AI hỗ trợ", value=True)
                else:
                    use_ml = False
                    st.caption("AI chưa sẵn sàng")
            
            with c_opt2:
                if st.button("CHẠY LẬP LỊCH (HYBRID ENGINE)", type="primary"):
                    engine = HybridEngine()
                    with st.status("Đang tính toán phương án tối ưu...", expanded=True) as status:
                        st.write("Đang tải dữ liệu máy...")
                        time.sleep(0.3)
                        st.write("Đang phân tích ràng buộc kỹ thuật...")
                        schedule = engine.solve(st.session_state.jobs_queue, use_ml=use_ml)
                        st.session_state.scheduled_jobs = schedule
                        status.update(label="Hoàn tất lập lịch", state="complete", expanded=False)
        else:
            st.info("Chưa có đơn hàng nào trong hàng đợi.")

    st.markdown("---")
    
    # Phần 2: Biểu đồ Gantt
    st.markdown("#### BIỂU ĐỒ KẾ HOẠCH SẢN XUẤT (GANTT)")
    if len(st.session_state.scheduled_jobs) > 0:
        df_schedule = pd.DataFrame(st.session_state.scheduled_jobs)
        
        # Chuẩn bị cho Plotly
        base_time = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
        df_schedule['Start_Time'] = df_schedule['start'].apply(lambda x: base_time + timedelta(minutes=x))
        df_schedule['Finish_Time'] = df_schedule['finish'].apply(lambda x: base_time + timedelta(minutes=x))
        
        # Biểu đồ sạch
        color_map = {
            "Standard GA": "#2980B9",  # Professional Blue
            "Expert Intervention": "#C0392B" # Professional Red
        }
        
        fig = px.timeline(
            df_schedule, 
            x_start="Start_Time", x_end="Finish_Time", 
            y="machine", 
            color="note",
            color_discrete_map=color_map,
            hover_data=["job_id", "note"],
            title=""
        )
        fig.update_layout(
            xaxis_title="Thời gian",
            yaxis_title="Máy",
            legend_title="Loại Lập lịch",
            height=400,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        fig.update_yaxes(categoryorder="category ascending")
        st.plotly_chart(fig, use_container_width=True)
        
        # Xuất dữ liệu bảng
        with st.expander("Xem chi tiết dữ liệu"):
            st.dataframe(df_schedule, use_container_width=True)
            csv = df_schedule.to_csv(index=False).encode('utf-8')
            st.download_button("Tải xuống CSV", csv, "schedule.csv", "text/csv")
            
    else:
        st.write("Chưa có dữ liệu lịch trình.")

# ==========================================
# TAB 3: CÔNG NHÂN
# ==========================================
elif tab_selection == "3. Giao diện Máy (Công nhân)":
    st.markdown("### GIAO DIỆN VẬN HÀNH MÁY")
    
    if len(st.session_state.scheduled_jobs) == 0:
        st.info("Hiện tại chưa có lịch phân công.")
    else:
        machines = list(set([j['machine'] for j in st.session_state.scheduled_jobs]))
        selected_machine = st.selectbox("Chọn máy vận hành:", machines)
        
        st.markdown(f"#### Danh sách công việc: {selected_machine}")
        
        my_jobs = [j for j in st.session_state.scheduled_jobs if j['machine'] == selected_machine]
        my_jobs = sorted(my_jobs, key=lambda x: x['start'])
        
        # Sử dụng layout dạng bảng đơn giản
        for job in my_jobs:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                
                # Job ID
                c1.markdown(f"**{job['job_id']}**")
                
                # Thời gian
                start_str = (datetime.now().replace(hour=7, minute=0) + timedelta(minutes=job['start'])).strftime('%H:%M')
                end_str = (datetime.now().replace(hour=7, minute=0) + timedelta(minutes=job['finish'])).strftime('%H:%M')
                c2.write(f"{start_str} - {end_str}")
                
                # Ghi chú
                if job['note'] == "Expert Intervention":
                    c3.write("Lưu ý: Chạy chế độ an toàn")
                else:
                    c3.write("Chế độ tiêu chuẩn")
                
                # Hành động
                if c4.button("Xong", key=f"btn_{job['job_id']}"):
                    st.toast(f"Đã hoàn thành {job['job_id']}")