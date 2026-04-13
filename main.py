
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
        
        proc_defs = session.query(ProcessDefinition.process_name).distinct().all()
        process_map = {p[0]: [] for p in proc_defs}
        
        all_steps = session.query(ProcessDefinition).all()
        for step in all_steps:
            process_map[step.process_name].append(step.capability_required)

        # LOAD PROJECTS
        from database.models import Project
        all_projects = session.query(Project).all()
        project_options = [{"id": p.id, "name": p.project_name, "code": p.project_code, "hexcode": p.hexcode} for p in all_projects]
            
        session.close()
    except Exception as e:
        print(f"Error loading DB: {e}")
        process_map = {}
        project_options = []
        
    if not process_map:
        process_map = {
            "Cắt thô (Standard)": 1,
            "Cắt + Đánh bóng (Polishing)": 2,
            "Cắt + Soi cạnh + Đánh bóng (Complex)": 3
        }
    
    process_options = list(process_map.keys())

    with st.container(border=True):
        st.markdown("#### Thiết lập chung cho Đơn hàng")
        
        if 'project_options' not in locals() or not project_options:
            project_options_display = ["Chưa có dự án nào"]
        else:
            project_options_display = [f"[{p['code']}] {p['name']} (Hex: {p['hexcode'] or 'N/A'})" for p in project_options]

        c1, c2 = st.columns([3, 1])
        with c1:
            selected_project_str = st.selectbox("Chọn Dự án / Công trình hiện có:", project_options_display)
            
            selected_project_data = None
            if selected_project_str != "Chưa có dự án nào" and project_options:
                idx = project_options_display.index(selected_project_str)
                selected_project_data = project_options[idx]
        with c2:
            priority_input = st.selectbox("Mức độ ưu tiên", ["Bình thường", "Cao", "Gấp"], index=0)

        with st.expander("Tạo mới Dự án nhanh tại đây", expanded=False):
            with st.form("new_project_form"):
                new_c1, new_c2, new_c3 = st.columns(3)
                with new_c1:
                    new_p_name = st.text_input("Tên Công trình *")
                with new_c2:
                    new_p_code = st.text_input("Mã Công trình *")
                with new_c3:
                    new_p_hex = st.text_input("Hexcode")
                    
                submitted = st.form_submit_button("Lưu & Thêm Dự án mới", type="primary")
                if submitted:
                    if not new_p_name or not new_p_code:
                        st.error("Tên và Mã công trình là bắt buộc!")
                    else:
                        try:
                            from database.models import get_engine, Project
                            from sqlalchemy.orm import sessionmaker
                            eng = get_engine('sqlite:///master_data_v2.db')
                            Sess = sessionmaker(bind=eng)
                            sess = Sess()
                            
                            exist_p = sess.query(Project).filter_by(project_code=new_p_code).first()
                            if exist_p:
                                st.error(f"Mã công trình '{new_p_code}' đã tồn tại! Vui lòng chọn mã khác.")
                            else:
                                new_proj = Project(project_name=new_p_name, project_code=new_p_code, hexcode=new_p_hex)
                                sess.add(new_proj)
                                sess.commit()
                                st.success(f"Đã tạo dự án '{new_p_name}' thành công")
                            sess.close()
                        except Exception as e:
                            st.error(f"Lỗi thêm Dự án: {e}")

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

        st.markdown("#### Tải lên Bản vẽ & Phân tích")
        uploaded_files = st.file_uploader("Tải lên nhiều bản vẽ (.dxf)", type=['dxf'], accept_multiple_files=True)
        
        if uploaded_files:
            if 'analyzed_files' not in st.session_state:
                st.session_state.analyzed_files = {}

            if st.button("Phân tích bản vẽ", type="primary"):
                os.makedirs("data", exist_ok=True)
                with st.spinner("Đang phân tích ..."):
                    for file in uploaded_files:
                        temp_path = os.path.join("data", file.name)
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                        # Phân tích DXF
                        dxf_info = extract_cutting_info([temp_path])
                        st.session_state.analyzed_files[file.name] = dxf_info
                st.success("Done")

            if any(f.name in st.session_state.analyzed_files for f in uploaded_files):
                file_configs = []
                st.markdown("#### Cấu hình cho từng Bản vẽ")
                for idx, file in enumerate(uploaded_files):
                    dxf_info = st.session_state.analyzed_files.get(file.name)
                    if not dxf_info:
                        continue 
                        
                    with st.expander(f"Bản vẽ {idx+1}: {file.name}", expanded=True):
                        if dxf_info['status'] == 'success':
                            # Hiển thị thông tin
                            st.success(f"Dài thẳng: {dxf_info.get('straight_len_mm', 0)}mm | Cong/Tròn: {dxf_info.get('curved_len_mm', 0)}mm | Tổng: {dxf_info.get('total_len_mm', 0)}mm")
                            texts = dxf_info.get("texts", [])
                            if texts:
                                st.info(f"Ghi chú trong bản vẽ: {', '.join(texts[:10])}" + ("..." if len(texts)>10 else ""))
                            if dxf_info.get("warnings"):
                                st.warning(f"Cảnh báo: " + "; ".join(dxf_info["warnings"]))
                                
                            # Lọc quy trình
                            has_curve = dxf_info.get('curved_len_mm', 0) > 0
                            
                            valid_processes = []
                            for p_name, caps in process_map.items():
                                is_straight_only = ('Cut_straight' in caps) and ('Cut_contour' not in caps)
                                if has_curve and is_straight_only:
                                    continue 
                                valid_processes.append(p_name)
                                
                            if not valid_processes:
                                st.error("Không có quy trình nào phù hợp với bản vẽ chứa đường cong này!")
                                valid_processes = process_options 
                                
                            f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
                            with f_col1:
                                material = st.selectbox("Nhóm Vật Liệu", ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"], index=2, key=f"mat_{file.name}_{idx}")
                            with f_col2:
                                quantity = st.number_input("Số lượng (tấm)", min_value=1, value=1, key=f"qty_{file.name}_{idx}")
                            with f_col3:
                                process_type = st.selectbox("Quy trình Gia công phù hợp", valid_processes, key=f"proc_{file.name}_{idx}")
                            
                            process_lower = process_type.lower()
                            detail_len_mm = dxf_info['total_len_mm']
                            if any(k in process_lower for k in ["vát", "rãnh", "biên dạng", "chỉ", "hoa văn", "tất cả"]):
                                detail_len_mm = st.number_input(
                                    "Chiều dài chi tiết cần gia công (mm) - Dành cho Vát/Rãnh/Biên dạng",
                                    min_value=0.0,
                                    value=float(dxf_info['total_len_mm']),
                                    step=50.0,
                                    key=f"detail_{file.name}_{idx}",
                                    help="Hệ thống sẽ dùng chiều dài này để tính toán thời gian thay vì dùng toàn bộ chiều dài phôi."
                                )
                                
                            file_configs.append({
                                "file": file,
                                "material": material,
                                "quantity": quantity,
                                "process_type": process_type,
                                "dxf_info": dxf_info,
                                "detail_len_mm": detail_len_mm
                            })
                        else:
                            st.error(f"Lỗi khi đọc bản vẽ: {dxf_info['message']}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                btn_add = st.button("Thêm tất cả vào hàng đợi", use_container_width=True, type="primary")

                if btn_add and file_configs:
                    if not selected_project_data:
                        st.error("Vui lòng Tạo mới hoặc Chọn một Dự án trước khi thêm vào hàng đợi!")
                        st.stop()
                        
                    st.session_state.job_counter += 1
                    master_job_idx = st.session_state.job_counter
                    total_added = 0
                    
                    for idx_in_batch, config in enumerate(file_configs):
                        file = config["file"]
                        dxf_info = config["dxf_info"]
                        
                        ts = int(time.time() * 1000) % 10000 
                        short_name = file.name[:6].replace(" ", "_")
                        
                        project_code_val = selected_project_data['code']
                        project_name_val = selected_project_data['name']
                        hexcode_val = selected_project_data['hexcode']
                        
                        prefix = project_code_val.strip() if project_code_val.strip() else f"JOB-{master_job_idx:03d}"
                        job_id = f"{prefix}.{idx_in_batch+1}_{short_name}_{ts}"
                        
                        job_data = {
                            "id": job_id,
                            "project_name": project_name_val,
                            "project_code": project_code_val,
                            "hexcode": hexcode_val,
                            "material_group": config["material"],
                            "process_steps": len(process_map[config["process_type"]]),
                            "size_mm": dxf_info['total_len_mm'], 
                            "detail_len_mm": config.get("detail_len_mm", dxf_info['total_len_mm']),
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
                        job_data['process'] = str(config["process_type"])
                        job_data['process_machine'] = str(job_data['operations'])
                        st.session_state.jobs_queue.append(job_data)
                        total_added += 1
                        
                    if total_added > 0:
                        st.toast(f"Đã thêm thành công {total_added} bản vẽ vào hàng đợi.")
                        st.session_state.analyzed_files = {}
                        time.sleep(1)
                        st.rerun()

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
                try:
                    from database.models import get_engine, MachineCapability
                    from sqlalchemy.orm import sessionmaker
                    engine_map = get_engine('sqlite:///master_data_v2.db')
                    Session_map = sessionmaker(bind=engine_map)
                    session_map = Session_map()
                    
                    caps_db = session_map.query(MachineCapability).all()
                    dynamic_mapping = {}
                    for cap in caps_db:
                        if cap.capability_name not in dynamic_mapping:
                            dynamic_mapping[cap.capability_name] = []
                        if cap.machine_id not in dynamic_mapping[cap.capability_name]:
                            dynamic_mapping[cap.capability_name].append(cap.machine_id)
                            
                    mapping = {k: " / ".join(v) for k, v in dynamic_mapping.items()}
                    session_map.close()
                except Exception as e:
                    print(f"Lỗi lấy dữ liệu máy: {e}")
                    mapping = {"Cut_straight": "Máy Cắt Cầu", "Cut_contour": "Máy Cắt Nước", "Polish_edge": "Máy Đánh Bóng", "Drill_hole": "Máy Khoan"}

                def map_ops_to_machines(ops_list):
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

            # Hiển thị dataframe và cho phép chỉnh sửa/xóa dữ liệu
            edited_df_queue = st.data_editor(
                df_queue[['id', 'project_name', 'project_code', 'hexcode', 'material_group', 'size_mm', 'detail_len_mm', 'complexity', 'process','process_machine']],
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="queue_editor"
            )
            
            queue_changed = False
            if len(edited_df_queue) != len(df_queue):
                queue_changed = True
            else:
                if not edited_df_queue.equals(df_queue[['id', 'project_name', 'project_code', 'hexcode', 'material_group', 'size_mm', 'detail_len_mm', 'complexity', 'process','process_machine']]):
                    queue_changed = True

            if queue_changed:
                new_queue = []
                for _, row in edited_df_queue.iterrows():
                    old_job = next((j for j in st.session_state.jobs_queue if j['id'] == row['id']), None)
                    if old_job:
                        old_job.update({
                            'project_name': row.get('project_name', old_job.get('project_name')),
                            'project_code': row.get('project_code', old_job.get('project_code')),
                            'hexcode': row.get('hexcode', old_job.get('hexcode')),
                            'material_group': row.get('material_group', old_job.get('material_group')),
                            'size_mm': row.get('size_mm', old_job.get('size_mm')),
                            'detail_len_mm': row.get('detail_len_mm', old_job.get('detail_len_mm')),
                            'complexity': row.get('complexity', old_job.get('complexity')),
                            'process': row.get('process', old_job.get('process')),
                            'process_machine': row.get('process_machine', old_job.get('process_machine'))
                        })
                        new_queue.append(old_job)
                st.session_state.jobs_queue = new_queue
                st.rerun()
            
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
                        # Thay vì in đậm toàn bộ dòng chữ dài, có thể cắt phần mô tả xuống làm chú thích
                        opt_name = opt['name']
                        if "(" in opt_name and ")" in opt_name:
                            main_name = opt_name.split("(")[0].strip()
                            desc = opt_name.split("(")[1].replace(")", "").strip()
                            st.markdown(f"**{main_name}**")
                            st.caption(f"*{desc}*")
                        else:
                            st.markdown(f"**{opt['name']}**")
                            
                        metrics = opt['metrics']
                        st.metric("Tổng Thời Gian (Makespan)", f"{metrics['makespan']} phút")
                        st.metric("Thời gian Setup", f"{metrics['setup']} phút")
                        
                        # Nút bấm để chọn phương án này
                        if st.button(f"Chọn Phương án {idx+1}", key=f"btn_choose_opt_{idx}", type="primary"):
                            selected_schedule = opt['schedule']
                            for j_op in selected_schedule:
                                if 'status' not in j_op:
                                    j_op['status'] = 'pending'
                            st.session_state.scheduled_jobs = selected_schedule
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

        def get_display_color(row):
            j_status = row.get('status', 'pending')
            m_status = machine_status_map.get(row['machine'], "On")
            if j_status == 'completed': return "Hoàn thành"
            elif j_status == 'in_progress': return "Đang chạy"
            else:
                if m_status == 'Maintenance': return "Chờ - Bảo trì"
                if m_status == 'Off': return "Chờ - Tắt máy"
                return "Chờ - Bình thường"

        df_schedule['display_color'] = df_schedule.apply(get_display_color, axis=1)

        def format_text(row):
            j_status = row.get('status', 'pending')
            if j_status == 'completed': return f"[Xong] {row['job_id']}"
            elif j_status == 'in_progress': return f"[Đang chạy] {row['job_id']}"
            return row['job_id']
            
        df_schedule['display_text'] = df_schedule.apply(format_text, axis=1)

        color_map = {
            "Hoàn thành": "rgba(176, 190, 197, 0.4)", # Light Gray Mờ
            "Đang chạy": "#1976D2",                   # Blue chuyên nghiệp
            "Chờ - Bình thường": "#1B5E20",           # Green
            "Chờ - Tắt máy": "#757575",               # Gray
            "Chờ - Bảo trì": "#B71C1C"                # Red
        }
        
        fig = px.timeline(
            df_schedule, 
            x_start="Start_Time", x_end="Finish_Time", 
            y="machine",    
            color="display_color",
            color_discrete_map=color_map,
            hover_data=["job_id", "note", "machine_status", "status"],
            title="",
            text="display_text"
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
            legend_title="Trạng thái Máy",
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

            edited_df_detailed = st.data_editor(
                df_detailed, 
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="schedule_detailed_editor"
            )
            
            detailed_changed = False
            if len(edited_df_detailed) != len(df_detailed):
                detailed_changed = True
            elif not edited_df_detailed.equals(df_detailed):
                detailed_changed = True
                
            if detailed_changed:
                new_scheduled = []
                for idx, row in edited_df_detailed.iterrows():
                    # idx in edited_df_detailed corresponds to the index in df_detailed, 
                    # which corresponds identically to st.session_state.scheduled_jobs because of how pd.merge(how='left') behaves.
                    if isinstance(idx, int) and idx < len(st.session_state.scheduled_jobs):
                        old_sched = st.session_state.scheduled_jobs[idx]
                        
                        try:
                            # Update start/finish minutes if Start_Time / Finish_Time was changed
                            base_time = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)
                            if 'Start_Time' in row and pd.notnull(row['Start_Time']):
                                s_time = pd.to_datetime(row['Start_Time'])
                                old_sched['start'] = int((s_time - base_time).total_seconds() / 60)
                            if 'Finish_Time' in row and pd.notnull(row['Finish_Time']):
                                f_time = pd.to_datetime(row['Finish_Time'])
                                old_sched['finish'] = int((f_time - base_time).total_seconds() / 60)
                            if 'setup' in row:
                                old_sched['setup'] = row['setup']
                            if 'machine' in row:
                                old_sched['machine'] = row['machine']
                        except Exception:
                            pass
                        
                        new_scheduled.append(old_sched)
                
                st.session_state.scheduled_jobs = new_scheduled
                st.rerun()

            csv = edited_df_detailed.to_csv(index=False).encode('utf-8')
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
                                            for j_op in best_opt:
                                                if 'status' not in j_op:
                                                    j_op['status'] = 'pending'
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
                in_progress_jobs = [j for j in my_jobs if j.get('status') == 'in_progress']
                pending_jobs = [j for j in my_jobs if j.get('status', 'pending') == 'pending']
                completed_jobs = [j for j in my_jobs if j.get('status') == 'completed']

                def render_job_card(job, card_type="pending"):
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                        
                        lbl = "Đang chờ"
                        if card_type == "in_progress": lbl = "Đang thực thi"
                        elif card_type == "completed": lbl = "Đã hoàn thành"
                        c1.markdown(f"**{job['job_id']}**  \n*({lbl})*")
                        
                        start_str = (datetime.now().replace(hour=7, minute=0) + timedelta(minutes=job['start'])).strftime('%H:%M')
                        end_str = (datetime.now().replace(hour=7, minute=0) + timedelta(minutes=job['finish'])).strftime('%H:%M')
                        duration = job['finish'] - job['start']
                        
                        c2.write(f" {start_str} - {end_str} ({duration} phút)")
                        if card_type == "in_progress":
                            c2.progress(0.4) 
                            
                        if job['note'] == "Expert Intervention":
                            c3.warning("Chạy an toàn")
                        else:
                            c3.info("Tiêu chuẩn")
                        
                        if card_type == "pending":
                            if c4.button(" Bắt Đầu", key=f"btn_start_{job['job_id']}", type="primary"):
                                for sj in st.session_state.scheduled_jobs:
                                    if sj['job_id'] == job['job_id']:
                                        sj['status'] = 'in_progress'
                                st.rerun()
                        elif card_type == "in_progress":
                            if c4.button(" Hoàn Thành", key=f"btn_done_{job['job_id']}", type="primary"):
                                for sj in st.session_state.scheduled_jobs:
                                    if sj['job_id'] == job['job_id']:
                                        sj['status'] = 'completed'
                                st.toast(f"Máy {selected_machine} đã hoàn thành {job['job_id']}!")
                                st.rerun()
                        elif card_type == "completed":
                            if c4.button(" Hoàn Tác", key=f"btn_undo_{job['job_id']}", type="secondary"):
                                for sj in st.session_state.scheduled_jobs:
                                    if sj['job_id'] == job['job_id']:
                                        sj['status'] = 'pending'
                                st.rerun()

                st.markdown("##### [ĐANG THỰC THI]")
                if not in_progress_jobs:
                    st.write("Không có công việc nào đang chạy.")
                for job in in_progress_jobs:
                    render_job_card(job, "in_progress")

                st.markdown("##### [HÀNG ĐỢI]")
                if not pending_jobs:
                    st.write("Không có công việc trong hàng đợi.")
                for job in pending_jobs:
                    render_job_card(job, "pending")

                st.markdown("##### [LỊCH SỬ - ĐÃ HOÀN THÀNH]")
                if not completed_jobs:
                    st.write("Chưa có công việc nào hoàn thành.")
                for job in completed_jobs:
                    render_job_card(job, "completed")
        elif selected_machine:
            st.success("Chọn máy khác phía trên!")
            
# ==========================================
# TAB 4: QUẢN LÝ MASTER DATA
# ==========================================    
elif tab_selection == "4. Quản Lý Master Data":
    from ui_master_data import render_master_data_management
    render_master_data_management()