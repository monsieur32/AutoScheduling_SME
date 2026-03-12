import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from database.models import get_engine, Material, Machine, MachineCapability, MachineSpeed, ProcessDefinition

# Helper function to load and save data for a specific model
def render_table_editor(session, model_class, table_name, pk_col='id'):
    st.subheader(f"Quản lý bảng: {table_name}")
    
    # Lấy dữ liệu từ DB
    records = session.query(model_class).all()
    
    if not records:
        # Nếu bảng trống, tạo dataframe với các cột dựa trên model
        cols = [c.name for c in model_class.__table__.columns]
        df = pd.DataFrame(columns=cols)
    else:
        # Chuyển đổi records thành list of dicts
        data = []
        for r in records:
            r_dict = {c.name: getattr(r, c.name) for c in model_class.__table__.columns}
            data.append(r_dict)
        df = pd.DataFrame(data)

    # st.data_editor form, khóa cột ID (pk_col) lại để người dùng không chỉnh sửa được
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"editor_{table_name}",
        disabled=[pk_col] # Vô hiệu hoá sửa chữa cột key chính
    )

    if st.button(f"Lưu thay đổi {table_name}", type="primary"):
        try:
            # Lấy list ID hiện tại trên giao diện
            current_ids = []
            
            for _, row in edited_df.iterrows():
                row_dict = row.to_dict()
                
                # Nếu ID là số nguyên (Autoincrement) và bị NaN do thêm mới dòng
                if pd.isna(row_dict.get(pk_col)):
                    row_dict.pop(pk_col, None)
                    new_obj = model_class(**row_dict)
                    session.add(new_obj)
                    session.flush() # Để sinh ID tạm
                    current_ids.append(getattr(new_obj, pk_col))
                else:
                    # Cập nhật hoặc Thêm mới (nếu là ID chuỗi nhập tay)
                    obj_id = row_dict[pk_col]
                    current_ids.append(obj_id)
                    existing_obj = session.query(model_class).filter(getattr(model_class, pk_col) == obj_id).first()
                    
                    if existing_obj:
                        for k, v in row_dict.items():
                            setattr(existing_obj, k, v)
                    else:
                        new_obj = model_class(**row_dict)
                        session.add(new_obj)
            
            # Xoá các dòng không còn trên giao diện (Người dùng đã bấm delete row)
            if current_ids:
                session.query(model_class).filter(~getattr(model_class, pk_col).in_(current_ids)).delete(synchronize_session=False)
            else:
                session.query(model_class).delete() # Nếu xoá hết sạch dòng
                
            session.commit()
            st.success(f"Cập nhật {table_name} thành công!")
            st.rerun()
        except Exception as e:
            session.rollback()
            st.error(f"Lỗi khi lưu: {e}")

def render_master_data_management():
    st.markdown("## QUẢN LÝ Masterdata")
    
    engine = get_engine('sqlite:///master_data_v2.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Vật liệu (Materials)", 
        "Máy móc (Machines)", 
        "Khả năng Máy (Capabilities)", 
        "Tốc độ Máy (Speeds)", 
        "Quy trình (Processes)"
    ])

    with tab1:
        render_table_editor(session, Material, "Vật Liệu", pk_col="id") 
    with tab2:
        render_table_editor(session, Machine, "Máy Móc", pk_col="id")
    with tab3:
        render_table_editor(session, MachineCapability, "Khả Năng Cắt", pk_col="id")
    with tab4:
        render_table_editor(session, MachineSpeed, "Tốc Độ Cắt", pk_col="id")
    with tab5:
        render_table_editor(session, ProcessDefinition, "Quy Trình Sản Xuất", pk_col="id")

    session.close()
