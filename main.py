import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random

# ==========================================
# 1. CẤU HÌNH & DỮ LIỆU GIẢ LẬP
# ==========================================

st.set_page_config(page_title="Hệ thống Điều độ Xưởng 8C", layout="wide")

MACHINES = [
    "MÁY CẮT CẦU 01", "MÁY CẮT CẦU 02",
    "WATERJET WJ-01", "WATERJET WJ-02", "WATERJET WJ-03",
    "MÁY CMS-01", "MÁY CMS-02",
    "MÁY LÍP 45"
]

if 'jobs' not in st.session_state:
    data = []
    base_time = datetime.now().replace(hour=7, minute=30, second=0, microsecond=0)

    for i in range(1, 20):
        machine = random.choice(MACHINES)
        duration = random.randint(30, 180)
        setup_time = random.choice([15, 30, 45])

        start_setup = base_time + timedelta(minutes=random.randint(0, 400))
        end_setup = start_setup + timedelta(minutes=setup_time)
        data.append({
            "Job ID": f"SETUP-{i}", "Machine": machine,
            "Start": start_setup, "Finish": end_setup,
            "Type": "Setup", "Status": "Hoàn thành" if i < 5 else "Chờ"
        })

        data.append({
            "Job ID": f"JOB-{100 + i}", "Machine": machine,
            "Start": end_setup, "Finish": end_setup + timedelta(minutes=duration),
            "Type": "Sản xuất", "Status": "Hoàn thành" if i < 5 else "Chờ",
            "Product": f"Đá Nhóm {random.choice(['A', 'B', 'C'])}"
        })

    st.session_state.jobs = pd.DataFrame(data)

if 'machine_status' not in st.session_state:
    st.session_state.machine_status = {m: "Đang chạy" for m in MACHINES}

# ==========================================
# 2. GIAO DIỆN CHÍNH
# ==========================================

st.sidebar.title(" XƯỞNG ABC")
role = st.sidebar.radio("Vai trò người dùng:", ["Ban Điều độ (Planner)", "Công nhân (Worker)"])

# ==========================================
# 3. PHÂN HỆ 1: BAN ĐIỀU ĐỘ & KẾ HOẠCH
# ==========================================
if role == "Ban Điều độ (Planner)":
    st.title("Bảng Sản Xuất Trung Tâm")

    # --- KPI Dashboard ---
    col1, col2, col3, col4 = st.columns(4)
    total_jobs = len(st.session_state.jobs[st.session_state.jobs['Type'] == 'Sản xuất'])
    completed = len(st.session_state.jobs[st.session_state.jobs['Status'] == 'Hoàn thành'])
    machine_down = sum(1 for status in st.session_state.machine_status.values() if status == "Đang bảo trì")

    col1.metric("Tổng đơn hàng hôm nay", f"{total_jobs} Jobs")
    col2.metric("Tiến độ hoàn thành", f"{completed}/{total_jobs}", f"{round(completed / total_jobs * 100)}%")
    col3.metric("Số máy đang hỏng", f"{machine_down}", delta_color="inverse" if machine_down > 0 else "normal")
    col4.metric("Dự kiến trễ hạn (Tardiness)", "3 Jobs", "-1 so với hôm qua")

    st.markdown("---")

    st.subheader(" Lịch trình Máy (Gantt Chart)")

    col_btn1, col_btn2 = st.columns([1, 5])
    if col_btn1.button("Chạy Tối ưu (GA-VNS)"):
        with st.spinner('Đang chạy thuật toán GA-VNS để giảm setup time...'):
            # (Ở đây sẽ gọi code Python thuật toán của bạn)
            st.toast("Đã tối ưu hóa xong! Giảm được 45 phút setup.")

    # Vẽ Gantt Chart
    df_view = st.session_state.jobs.copy()
    color_map = {"Sản xuất": "rgb(46, 134, 193)", "Setup": "rgb(231, 76, 60)"}

    fig = px.timeline(
        df_view, x_start="Start", x_end="Finish", y="Machine", color="Type",
        hover_data=["Job ID", "Status", "Product"],
        color_discrete_map=color_map,
        title="Lịch trình chi tiết từng máy CNC"
    )
    fig.update_yaxes(categoryorder="category ascending")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # --- Xử lý Đơn hàng gấp & Sự cố ---
    st.subheader(" Xử lý Động (Dynamic Scheduling)")
    with st.expander(" Chèn đơn hàng gấp (Urgent Job)", expanded=True):
        c1, c2, c3 = st.columns(3)
        new_job_id = c1.text_input("Mã đơn hàng", "URGENT-001")
        new_machine = c2.selectbox("Gán máy (Gợi ý)", MACHINES)
        duration = c3.number_input("Thời gian chạy (phút)", 30, 300, 60)

        if st.button("Chèn đơn & Tái lập lịch"):
            start_time = datetime.now()
            new_row = {
                "Job ID": new_job_id, "Machine": new_machine,
                "Start": start_time, "Finish": start_time + timedelta(minutes=duration),
                "Type": "Sản xuất", "Status": "Chờ", "Product": "Hàng Gấp"
            }
            st.session_state.jobs = pd.concat([st.session_state.jobs, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Đã chèn {new_job_id} vào lịch trình. Hệ thống đang cân bằng lại tải!")
            st.rerun()

# ==========================================
# 4. PHÂN HỆ 2: CÔNG NHÂN / PHÂN XƯỞNG
# ==========================================
elif role == "Công nhân (Worker)":
    st.title("Giao diện Vận hành Máy (Shop Floor)")

    selected_machine = st.selectbox("Chọn Máy bạn đang đứng:", MACHINES)

    current_status = st.session_state.machine_status[selected_machine]
    st.info(f"Trạng thái hiện tại: **{current_status}**")

    # 2. Báo cáo Sự cố
    if st.button("BÁO HỎNG MÁY / DỪNG MÁY"):
        st.session_state.machine_status[selected_machine] = "Đang bảo trì"
        st.error("Đã gửi cảnh báo về Ban Điều độ! Hãy chờ kỹ thuật xuống.")

    st.markdown("---")

    # 3. Danh sách công việc
    st.subheader(f"Danh sách công việc của {selected_machine}")

    # Lọc công việc của máy này
    my_jobs = st.session_state.jobs[
        (st.session_state.jobs['Machine'] == selected_machine) &
        (st.session_state.jobs['Status'] != 'Hoàn thành')
        ].sort_values(by="Start")

    if len(my_jobs) > 0:
        for index, row in my_jobs.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                c1.write(f"**{row['Job ID']}**")
                c1.caption(f"Loại: {row['Type']}")

                c2.write(f"{row['Start'].strftime('%H:%M')} - {row['Finish'].strftime('%H:%M')}")

                if row['Type'] == 'Setup':
                    c3.warning("Cần thay dao/gá phôi")
                else:
                    c3.write(f"{row.get('Product', '')}")

                if c4.button("Hoàn thành", key=f"done_{index}"):
                    st.session_state.jobs.at[index, 'Status'] = 'Hoàn thành'
                    st.toast(f"Đã xong job {row['Job ID']}! Chuyển sang job tiếp theo.")
                    st.rerun()
                st.divider()
    else:
        st.success("Bạn đã hoàn thành hết công việc trong ca!")