import openpyxl
import os
import shutil
from parse_masterdata import parse_master_data

MASTER_DATA_FILE = "data/MASTERDATA.csv"
TEMP_DATA_FILE = "data/temp_updating_master.xlsx"

def set_machine_status(machine_id, new_status):
    """
    Cập nhật cột 'status' của máy có machine_id trong sheet MACHINES
    new_status có thể là: 'On', 'Off', 'Maintenance'
    """
    if not os.path.exists(MASTER_DATA_FILE):
        print(f"File {MASTER_DATA_FILE} không tồn tại!")
        return False
        
    try:
        # Copy to temp .xlsx because openpyxl requires strict extension checking
        shutil.copy(MASTER_DATA_FILE, TEMP_DATA_FILE)
        wb = openpyxl.load_workbook(TEMP_DATA_FILE)
        
        if "MACHINES" not in wb.sheetnames:
            print("Không tìm thấy sheet MACHINES.")
            wb.close()
            os.remove(TEMP_DATA_FILE)
            return False
            
        sheet = wb["MACHINES"]
        
        # Tìm các cột
        headers = {cell.value: cell.column for cell in sheet[1] if cell.value}
        
        if "machine_id" not in headers:
            print("Không tìm thấy cột machine_id.")
            wb.close()
            os.remove(TEMP_DATA_FILE)
            return False
            
        # Thêm cột status nếu chưa có
        if "status" not in headers:
            new_col = sheet.max_column + 1
            sheet.cell(row=1, column=new_col).value = "status"
            headers["status"] = new_col
            
        col_id = headers["machine_id"]
        col_status = headers["status"]
        
        # Tìm và cập nhật trạng thái
        updated = False
        for row in range(2, sheet.max_row + 1):
            if sheet.cell(row=row, column=col_id).value == machine_id:
                sheet.cell(row=row, column=col_status).value = new_status
                updated = True
                break
                
        if updated:
            wb.save(TEMP_DATA_FILE)
            wb.close()
            # Xóa file cũ và copy đè file mới
            os.remove(MASTER_DATA_FILE)
            shutil.copy(TEMP_DATA_FILE, MASTER_DATA_FILE)
            os.remove(TEMP_DATA_FILE)
            
            print(f"Đã cập nhật máy {machine_id} -> {new_status}")
            # Cập nhật lại JSON database
            parse_master_data()
            return True
        else:
            print(f"Không tìm thấy máy {machine_id}")
            wb.close()
            os.remove(TEMP_DATA_FILE)
            return False
            
    except Exception as e:
        print(f"Lỗi khi cập nhật trạng thái: {e}")
        if os.path.exists(TEMP_DATA_FILE):
            try:
                os.remove(TEMP_DATA_FILE)
            except:
                pass
        return False
