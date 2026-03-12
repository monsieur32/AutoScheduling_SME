import openpyxl
import os
import shutil
from parse_masterdata import parse_master_data

MASTER_DATA_FILE = "data/MASTERDATA.csv"
TEMP_DATA_FILE = "data/temp_updating_master.xlsx"

def set_machine_status(machine_id, new_status):
    """
    Cập nhật cột 'status' của máy có machine_id trong database SQLite
    new_status có thể là: 'On', 'Off', 'Maintenance'
    """
    from database.models import get_engine, Machine
    from sqlalchemy.orm import sessionmaker
    
    try:
        engine = get_engine('sqlite:///master_data_v2.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        machine = session.query(Machine).filter_by(id=machine_id).first()
        if machine:
            machine.status = new_status
            session.commit()
            print(f"Đã cập nhật máy {machine_id} -> {new_status} in DB")
            success = True
        else:
            print(f"Không tìm thấy máy {machine_id}")
            success = False
            
        session.close()
        return success
    except Exception as e:
        print(f"Lỗi khi cập nhật trạng thái: {e}")
        return False
