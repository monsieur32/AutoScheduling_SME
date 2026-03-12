
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
if 'job_counter' not in st.session_state:
    st.session_state.job_counter = 0 # Đếm số lượng Job chính đã tạo

if 'jobs_queue' not in st.session_state:
    st.session_state.jobs_queue = [] # Danh sách công việc

if 'scheduled_jobs' not in st.session_state:
    st.session_state.scheduled_jobs = [] # Kết quả từ Hybrid Engine

if 'schedule_options' not in st.session_state:
    st.session_state.schedule_options = None # Các tùy chọn lịch trình trả về từ GA

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
    "3. Giao diện Máy (Công nhân)",
    "4. Quản Lý Master Data"
], label_visibility="collapsed")

st.sidebar.markdown("---")
# with st.sidebar.expander("Thông tin hệ thống", expanded=True):
#     st.write("Phiên bản: 1.0.0")
#     st.write("Module tích hợp:")
# #     st.write("- Phân tích DXF")
# #     st.write("- Random Forest AI")
# #     st.write("- Genetic Algorithm")

# ==========================================
# TAB 1: NHẬP LIỆU (PLANNER)
# ==========================================
if tab_selection == "1. Nhập liệu đơn hàng":
    st.markdown("### NHẬP ĐƠN HÀNG MỚI")
    
    from database.models import get_engine, ProcessDefinition
    from sqlalchemy.orm import sessionmaker
    
    try:
        engine = get_engine('sqlite:///master_data_v2.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Load unique process names preserving order by step_order roughly, or just get unique
        proc_defs = session.query(ProcessDefinition.process_name).distinct().all()
        process_map = {p[0]: [] for p in proc_defs}
        
        # Reconstruct mapping for the UI
        all_steps = session.query(ProcessDefinition).all()
        for step in all_steps:
            process_map[step.process_name].append(step.capability_required)
            
        session.close()
    except Exception as e:
        print(f"Error loading DB: {e}")
        process_map = {}
        
    # Fallback in case JSON is missing or map is empty
    if not process_map:
        process_map = {
            "Cắt thô (Standard)": 1,
            "Cắt + Đánh bóng (Polishing)": 2,
            "Cắt + Soi cạnh + Đánh bóng (Complex)": 3
        }
    
    process_options = list(process_map.keys())

    with st.container(border=True):
        st.markdown("#### Thiết lập chung cho Đơn hàng")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            project_name_input = st.text_input("Tên Công trình", placeholder="Ví dụ: VINHOME")
        with c2:
            project_code_input = st.text_input("Mã Công trình", placeholder="Ví dụ: VH")
        with c3:
            hexcode_input = st.text_input("Mã Hexcode (Mã phụ của Dự án)", placeholder="Ví dụ: VH0122")
        with c4:
            priority_input = st.selectbox("Mức độ ưu tiên", ["Bình thường", "Cao", "Gấp"], index=0)

        c5, c6 = st.columns(2)
        with c5:
            default_start_date = datetime.now()
            start_date_input = st.date_input("Ngày bắt đầu làm", value=default_start_date.date())
            start_time_input = st.time_input("Giờ bắt đầu làm", value=datetime.strptime("07:00", "%H:%M").time())
            start_datetime = datetime.combine(start_date_input, start_time_input)
        with c6:
            default_due = datetime.now() + timedelta(days=1)
            due_date_input = st.date_input("Hạn chót (Due Date)", value=default_due.date())
            due_time_input = st.time_input("Giờ giao", value=datetime.strptime("17:00", "%H:%M").time())
            due_datetime = datetime.combine(due_date_input, due_time_input)

        st.markdown("#### Tải lên Bản vẽ & Phân bổ Công việc")
        uploaded_files = st.file_uploader("Tải lên nhiều bản vẽ (.dxf)", type=['dxf'], accept_multiple_files=True)
        
        if uploaded_files:
            file_configs = []
            st.markdown("#### Cấu hình cho từng Bản vẽ")
            for idx, file in enumerate(uploaded_files):
                with st.expander(f"Bản vẽ {idx+1}: {file.name}", expanded=True):
                    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
                    with f_col1:
                        material = st.selectbox("Nhóm Vật Liệu", ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"], index=2, key=f"mat_{file.name}_{idx}")
                    with f_col2:
                        quantity = st.number_input("Số lượng (tấm)", min_value=1, value=1, key=f"qty_{file.name}_{idx}")
                    with f_col3:
                        process_type = st.selectbox("Quy trình Gia công", process_options, key=f"proc_{file.name}_{idx}")
                    
                    file_configs.append({
                        "file": file,
                        "material": material,
                        "quantity": quantity,
                        "process_type": process_type
                    })
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_analyze = st.button("Phân tích & Thêm tất cả vào hàng đợi", use_container_width=True, type="primary")

            if btn_analyze:
                st.markdown("#### Kết quả phân tích")
                os.makedirs("data", exist_ok=True)
                
                st.session_state.job_counter += 1
                master_job_idx = st.session_state.job_counter
                total_added = 0
                
                for idx_in_batch, config in enumerate(file_configs):
                    file = config["file"]
                    
                    # 1. Lưu file tạm
                    temp_path = os.path.join("data", file.name)
                    with open(temp_path, "wb") as f:
                        f.write(file.getbuffer())
                    
                    # 2. Phân tích DXF
                    with st.spinner(f"Đang xử lý {file.name}..."):
                        # Xử lý từng file riêng biệt
                        dxf_info = extract_cutting_info([temp_path])
                        
                    if dxf_info['status'] == 'success':
                        # Hiển thị kết quả riêng cho file này
                        st.success(f"**{file.name}**: Dài {dxf_info['total_len_mm']}mm, Phức tạp {dxf_info['complexity_ratio']}")
                        
                        # 3. Dự đoán AI và chuẩn bị Job Data
                        # Tạo Job ID duy nhất dù có trùng tên ban đầu (gom nhóm theo master_job_idx)
                        ts = int(time.time() * 1000) % 10000 
                        short_name = file.name[:6].replace(" ", "_")
                        
                        prefix = project_code_input.strip() if project_code_input.strip() else f"JOB-{master_job_idx:03d}"
                        job_id = f"{prefix}.{idx_in_batch+1}_{short_name}_{ts}"
                        
                        job_data = {
                            "id": job_id,
                            "project_name": project_name_input,
                            "project_code": project_code_input,
                            "hexcode": hexcode_input,
                            "material_group": config["material"],
                            "process_steps": len(process_map[config["process_type"]]),
                            "size_mm": dxf_info['total_len_mm'], 
                            "complexity": dxf_info['complexity_ratio'],
                            "quantity": config["quantity"],
                            "operations": process_map[config["process_type"]],
                            "start_time": start_datetime,
                            "due_date": due_datetime,
                            "priority": priority_input                            
                        }
                        
                        ai_pred = st.session_state.ml_system.predict_adjust({
                            "process_steps": job_data['process_steps'],
                            "material_group": job_data['material_group'],
                            "size_mm": job_data['size_mm'],
                            "dxf_complexity": job_data['complexity']
                        })
                        job_data['process'] = str(process_type)
                        job_data['process_machine'] = str(job_data['operations'])
                        # Thêm vào hàng đợi
                        st.session_state.jobs_queue.append(job_data)
                        total_added += 1
                        
                        if dxf_info.get("warnings"):
                            st.warning(f"Cảnh báo ({file.name}): " + "; ".join(dxf_info["warnings"]))
                            
                    else:
                        st.error(f"Lỗi khi đọc {file.name}: {dxf_info['message']}")
                
                if total_added > 0:
                    st.toast(f"Đã thêm thành công {total_added} bản vẽ vào hàng đợi.")
                    # Automatically update task.md internally

# ==========================================
# TAB 2: DASHBOARD
# ==========================================
elif tab_selection == "2. Bảng điều độ sản xuất":
    st.markdown("### TRUNG TÂM ĐIỀU ĐỘ SẢN XUẤT")
    
    # Phần 1: Hàng đợi
    with st.expander("DANH SÁCH HÀNG ĐỢI CÔNG VIỆC", expanded=True):
        if len(st.session_state.jobs_queue) > 0:
            df_queue = pd.DataFrame(st.session_state.jobs_queue)
            
            # Map process_machine id to visual names
            if 'operations' in df_queue.columns:
                def map_ops_to_machines(ops_list):
                    mapping = {"Cut_straight": "Máy Cắt Cầu", "Cut_contour": "Máy Cắt Nước", "Polish_edge": "Máy Đánh Bóng", "Drill_hole": "Máy Khoan"}
                    if not isinstance(ops_list, list):
                        try:
                            import ast
                            ops_list = ast.literal_eval(str(ops_list))
                        except Exception:
                            ops_list = [str(ops_list)]
                    if isinstance(ops_list, list):
                        return " -> ".join([mapping.get(cap, cap) for cap in ops_list])
                    return str(ops_list)
                    
                df_queue['process_machine'] = df_queue['operations'].apply(map_ops_to_machines)

            # Hiển thị dataframe sạch sẽ
            st.dataframe(
                df_queue[['id', 'project_name', 'project_code', 'hexcode', 'material_group', 'size_mm', 'complexity', 'process','process_machine']],
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
                    with st.spinner("Đang tính toán phương án tối ưu..."):
                        st.write("Đang tải dữ liệu máy...")
                        time.sleep(0.3)
                        st.write("Đang phân tích ràng buộc kỹ thuật...")
                        options = engine.solve(st.session_state.jobs_queue, use_ml=use_ml)
                        
                        st.session_state.schedule_options = options
                    st.success("Hoàn tất lập lịch. Vui lòng chọn phương án tối ưu bên dưới!")

            # Hiển thị các phương án để người dùng chọn
            if st.session_state.get('schedule_options') is not None:
                st.markdown("#### LỰA CHỌN PHƯƠNG ÁN LỊCH TRÌNH")
                options = st.session_state.schedule_options
                
                cols = st.columns(len(options))
                for idx, (col, opt) in enumerate(zip(cols, options)):
                    with col:
                        st.markdown(f"**{opt['name']}**")
                        metrics = opt['metrics']
                        st.metric("Tổng Thời Gian (Makespan)", f"{metrics['makespan']} phút")
                        st.metric("Thời gian Setup", f"{metrics['setup']} phút")
                        
                        # Nút bấm để chọn phương án này
                        if st.button(f"Chọn Phương án {idx+1}", key=f"btn_choose_opt_{idx}", type="primary"):
                            st.session_state.scheduled_jobs = opt['schedule']
                            st.session_state.schedule_options = None 
                            st.success(f"Đã chọn {opt['name']}!")
                            st.rerun() 
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
        
        # Real-time Lấy trạng thái máy từ DB mỗi khi render tab này
        machine_status_map = {}
        try:
            from database.models import Machine, get_engine
            from sqlalchemy.orm import sessionmaker
            engine_db = get_engine('sqlite:///master_data_v2.db')
            Session = sessionmaker(bind=engine_db)
            session_db = Session()
            all_machines_db = session_db.query(Machine).all()
            machine_status_map = {m.id: m.status for m in all_machines_db}
            session_db.close()
        except Exception as e:
            print(f"Error fetching machine status for gantt: {e}")
                
        # Gán trạng thái hiện tại vào data để tô màu
        df_schedule['machine_status'] = df_schedule['machine'].apply(lambda m: machine_status_map.get(m, "On"))

        # Biểu đồ sạch
        # Color theo trạng thái máy thay vì Loại thuật toán
        color_map = {
            "On": "#1B5E20",         # Xanh lá đậm (Bình thường)
            "Off": "#757575",        # Xám (Tắt máy)
            "Maintenance": "#B71C1C" # Đỏ (Bảo trì)
        }
        
        fig = px.timeline(
            df_schedule, 
            x_start="Start_Time", x_end="Finish_Time", 
            y="machine",    
            color="machine_status",
            color_discrete_map=color_map,
            hover_data=["job_id", "note", "machine_status"],
            title="",
            text="job_id"
        )
        fig.update_traces(
            textposition="inside",
            textfont_size=40    ,
            textfont_color="white",
            insidetextanchor='middle'
        )
        fig.update_layout(
            xaxis_title="Thời gian",
            yaxis_title="Máy",
            legend_title="Loại Lập lịch",
            height=400 + (len(df_schedule['machine'].unique())   * 20),
            margin=dict(l=0, r=0, t=30, b=0)

        )
        fig.update_yaxes(categoryorder="category ascending")
        st.plotly_chart(fig, use_container_width=True)
        
        # Xuất dữ liệu bảng
        with st.expander("Xem chi tiết dữ liệu"):
            if len(st.session_state.jobs_queue) > 0:
                df_queue_details = pd.DataFrame(st.session_state.jobs_queue)
                # Chỉ lấy các cột cần thiết để hiển thị 
                cols_to_keep = ['id', 'project_name', 'project_code', 'hexcode', 'material_group', 'size_mm', 'complexity', 'quantity']
                cols_to_merge = [c for c in cols_to_keep if c in df_queue_details.columns]
                
                if cols_to_merge:
                    df_queue_subset = df_queue_details[cols_to_merge]
                    # Đổi tên 'id' thành 'job_id' để dễ map, nếu df_schedule lưu dưới dạng mã có ".X" thì ta filter
                    # Lưu ý: job_id trong df_schedule chứa id của job
                    df_detailed = pd.merge(df_schedule, df_queue_subset, left_on='job_id', right_on='id', how='left')
                    # Xóa cột id thừa
                    if 'id' in df_detailed.columns:
                        df_detailed = df_detailed.drop(columns=['id'])
                else:
                    df_detailed = df_schedule
            else:
                df_detailed = df_schedule


            front_cols = ['job_id', 'project_name', 'project_code', 'hexcode', 'machine', 'Start_Time', 'Finish_Time', 'setup']
            front_cols_exist = [c for c in front_cols if c in df_detailed.columns]
            other_cols = [c for c in df_detailed.columns if c not in front_cols_exist]
            df_detailed = df_detailed[front_cols_exist + other_cols]

            # Bỏ các cột thừa không mong muốn
            cols_to_drop = ['op_idx', 'start', 'finish', 'note']
            curr_drop = [c for c in cols_to_drop if c in df_detailed.columns]
            if curr_drop:
                df_detailed = df_detailed.drop(columns=curr_drop)

            st.dataframe(df_detailed, use_container_width=True)
            csv = df_detailed.to_csv(index=False).encode('utf-8')
            st.download_button("Tải xuống CSV", csv, "schedule.csv", "text/csv")
            
    else:
        st.write("Chưa có dữ liệu lịch trình.")

# ==========================================
# TAB 3: CÔNG NHÂN
# ==========================================
elif tab_selection == "3. Giao diện Máy (Công nhân)":
    st.markdown("### GIAO DIỆN VẬN HÀNH MÁY (SƠ ĐỒ XƯỞNG)")
    
    if 'selected_worker_machine' not in st.session_state:
        st.session_state.selected_worker_machine = None

    from database.models import get_engine, Machine
    from sqlalchemy.orm import sessionmaker
    
    try:
        engine = get_engine('sqlite:///master_data_v2.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        machines_db = session.query(Machine).all()
        all_machines = {
            m.id: {
                'name': m.name,
                'status': m.status
            } for m in machines_db
        }
        
        session.close()
    except Exception as e:
        print(f"Lỗi load DB Machine: {e}")
        all_machines = {}

    if not all_machines:
        st.warning("Không tải được dữ liệu máy móc từ Master Data!")
        st.session_state.selected_worker_machine = None
    else:
        # Lấy danh sách toàn bộ máy từ Master Data
        machines = list(all_machines.keys())
        machines.sort()
        
        st.markdown("#### Sơ đồ các máy")
        
        # Grid layout (4 cột)
        cols_per_row = 4
        
        for i in range(0, len(machines), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(machines):
                    machine = machines[i+j]
                    machine_info = all_machines[machine]
                    machine_status = machine_info.get('status', 'On')
                    
                    machine_jobs = [jb for jb in st.session_state.scheduled_jobs if jb['machine'] == machine]
                    job_count = len(machine_jobs)
                    
                    if machine_status == 'Maintenance':
                        status_icon = "🔴"
                        status_text = "Bảo trì"
                    elif machine_status == 'Off':
                        status_icon = "⚪"
                        status_text = "Ngoại tuyến"
                    else:
                        if job_count > 100:
                            status_icon = "🔴"
                            status_text = "Quá tải"
                        elif job_count > 0:
                            status_icon = "🟡"
                            status_text = f"Đang chờ: {job_count} đơn"
                        else:
                            status_icon = "🟢"
                            status_text = "Rảnh"
                        
                    card_label = f"{status_icon} {machine}\n\n{status_text}"
                    
                    if col.button(card_label, key=f"btn_mach_{machine}", use_container_width=True):
                        st.session_state.selected_worker_machine = machine
                        st.rerun()

        st.markdown("---")
        
        selected_machine = st.session_state.selected_worker_machine
        
        if selected_machine and selected_machine in machines:
            machine_name = all_machines[selected_machine].get('name', selected_machine)
            st.markdown(f"### Chi tiết công việc: {selected_machine} ({machine_name})")
            
            # Khối điều khiển trạng thái cho Quản lý
            with st.expander("Cài đặt Trạng thái Máy", expanded=False):
                from utils_masterdata import set_machine_status
                curr_status = all_machines[selected_machine].get('status', 'On')
                status_opts = ["On", "Off", "Maintenance"]
                idx = status_opts.index(curr_status) if curr_status in status_opts else 0
                
                c_st1, c_st2 = st.columns([3, 1])
                
                with c_st1:
                    new_st = st.selectbox("Cập nhật trạng thái mới cho máy:", status_opts, index=idx, key=f"status_sel_{selected_machine}")
                    
                    if new_st == "Maintenance":
                        base_time = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
                        
                        m_col1, m_col2 = st.columns(2)
                        with m_col1:
                            repair_time = st.number_input("Thời gian dự kiến sửa (phút)", min_value=1, value=40)
                        with m_col2:
                            current_time = datetime.now().time()
                            breakdown_time = st.time_input("Thời điểm sự cố", value=current_time)
                            
                        # Tính số phút từ 07:00 để dùng cho logic scheduling
                        breakdown_dt = datetime.combine(datetime.today(), breakdown_time)
                        breakdown_minute = int((breakdown_dt - base_time).total_seconds() / 60)
                        if breakdown_minute < 0: breakdown_minute = 0

                with c_st2:
                    # Căn chỉnh nút bấm
                    st.markdown("<br>", unsafe_allow_html=True)
                    if new_st == "Maintenance":
                         st.markdown("<br>", unsafe_allow_html=True) # Cách dòng thêm để ngang hàng
                    
                    if st.button("Lưu Trạng Thái", type="primary", use_container_width=True):
                        if new_st != curr_status:
                            if new_st == "Maintenance" and repair_time > 30:
                                with st.spinner("Đang tái lập lịch (Rescheduling)..."):
                                    from utils_masterdata import set_machine_status
                                    success = set_machine_status(selected_machine, new_st)
                                    if success:
                                        scheduled_jobs = st.session_state.scheduled_jobs
                                        jobs_queue = st.session_state.jobs_queue
                                        
                                        job_status = {}
                                        for op in scheduled_jobs:
                                            j_id = op['job_id']
                                            if j_id not in job_status: job_status[j_id] = 'unaffected'
                                            
                                            # Gián đoạn thực sự trên máy hỏng
                                            if op['machine'] == selected_machine and op['start'] <= breakdown_minute < op['finish']:
                                                job_status[j_id] = 'affected'
                                                
                                        # Các job hoàn toàn chưa bắt đầu cũng chuyển vào affected
                                        for j_id in job_status.keys():
                                            ops_for_job = [o for o in scheduled_jobs if o['job_id'] == j_id]
                                            first_start = min([o['start'] for o in ops_for_job])
                                            if first_start > breakdown_minute:
                                                job_status[j_id] = 'affected'
                                                
                                        affected_job_ids = {j for j, st_ in job_status.items() if st_ == 'affected'}
                                        unaffected_job_ids = {j for j, st_ in job_status.items() if st_ == 'unaffected'}
                                        
                                        unaffected_schedule = [op for op in scheduled_jobs if op['job_id'] in unaffected_job_ids]
                                        
                                        mac_avail = {}
                                        mac_last = {}
                                        for m in all_machines.keys():
                                            if m == selected_machine:
                                                mac_avail[m] = breakdown_minute + repair_time
                                                mac_last[m] = None
                                            else:
                                                ops_on_m = [op for op in unaffected_schedule if op['machine'] == m]
                                                if ops_on_m:
                                                    mac_avail[m] = max([op['finish'] for op in ops_on_m] + [breakdown_minute])
                                                    mac_last[m] = max(ops_on_m, key=lambda x: x['finish'])['job_id']
                                                else:
                                                    mac_avail[m] = breakdown_minute
                                                    mac_last[m] = None
                                                    
                                        affected_jobs_queue = [q for q in jobs_queue if q['id'] in affected_job_ids]
                                        
                                        if affected_jobs_queue:
                                            engine_opts = HybridEngine().solve(
                                                affected_jobs_queue, 
                                                use_ml=st.session_state.ml_system.is_trained, 
                                                initial_machine_avail=mac_avail, 
                                                initial_machine_last_job=mac_last
                                            )
                                            # Tự động chọn phương án Cân Bằng (Option 0)
                                            best_opt = engine_opts[0]['schedule']
                                            st.session_state.scheduled_jobs = unaffected_schedule + best_opt
                                            st.success("Tái lập lịch thành công! Đã tạo chuỗi lịch trình mới thay thế.")
                                        else:
                                            st.success("Cập nhật thành công. Không có hoạt động nào bị ảnh hưởng!")
                                            
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error("Có lỗi xảy ra khi lưu trạng thái.")
                            else:
                                # Normal save
                                with st.spinner("Đang ghi đè file định dạng gốc..."):
                                    from utils_masterdata import set_machine_status
                                    success = set_machine_status(selected_machine, new_st)
                                    if success:
                                        st.success("Cập nhật thành công! Đang tải lại...")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Có lỗi xảy ra khi lưu trạng thái.")

            my_jobs = [j for j in st.session_state.scheduled_jobs if j['machine'] == selected_machine]
            my_jobs = sorted(my_jobs, key=lambda x: x['start'])
            
            if len(my_jobs) == 0:
                st.success(f"{selected_machine} hiện không có công việc nào!")
            else:
                for idx, job in enumerate(my_jobs):
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                        
                        # Job ID & Tình trạng rút gọn
                        if idx == 0:
                            c1.markdown(f"**{job['job_id']}**  \n*(Đang thực thi)*")
                        else:
                            c1.markdown(f"**{job['job_id']}**  \n*(Đang chờ)*")
                        
                        # Thời gian (mô phỏng từ mốc 07:00)
                        start_str = (datetime.now().replace(hour=7, minute=0) + timedelta(minutes=job['start'])).strftime('%H:%M')
                        end_str = (datetime.now().replace(hour=7, minute=0) + timedelta(minutes=job['finish'])).strftime('%H:%M')
                        duration = job['finish'] - job['start']
                        
                        c2.write(f" {start_str} - {end_str} ({duration} phút)")
                        if idx == 0:
                            c2.progress(0.4) 
                            
                        # Ghi chú / Trạng thái
                        if job['note'] == "Expert Intervention":
                            c3.warning("Chạy chế độ an toàn")
                        else:
                            c3.info("Chế độ tiêu chuẩn")
                        
                        # Hành động
                        if c4.button(" Hoàn Thành", key=f"btn_{job['job_id']}", type="primary" if idx == 0 else "secondary"):
                            # Xóa job khỏi danh sách phân công
                            st.session_state.scheduled_jobs = [j for j in st.session_state.scheduled_jobs if j['job_id'] != job['job_id']]
                            # Xóa job khỏi hàng đợi
                            st.session_state.jobs_queue = [q for q in st.session_state.jobs_queue if q['id'] != job['job_id']]
                                
                            st.toast(f" Máy {selected_machine} đã hoàn thành {job['job_id']}!")
                            st.rerun()
        elif selected_machine:
            st.success("Chọn máy khác phía trên!")
            
# ==========================================
# TAB 4: QUẢN LÝ MASTER DATA
# ==========================================    
elif tab_selection == "4. Quản Lý Master Data":
    from ui_master_data import render_master_data_management
    render_master_data_management()