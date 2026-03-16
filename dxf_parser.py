import ezdxf
import math

# --- CẤU HÌNH TÙY CHỌN (LỌC LOẠI ĐƯỜNG) ---
# Danh sách các loại đường muốn tính chiều dài. Để trống [] sẽ tính TẤT CẢ các đường.
# Ví dụ chỉ polyline:  ALLOWED_ENTITY_TYPES = ['POLYLINE']
# Ví dụ chỉ lwpolyline: ALLOWED_ENTITY_TYPES = ['LWPOLYLINE']
ALLOWED_ENTITY_TYPES = []

def extract_cutting_info(dxf_path):
    """
    Phân tích file DXF để trích xuất tổng chiều dài cắt và thông tin hình học.
    Giả định đường cắt nằm trên các layer cụ thể hoặc là các thực thể chuẩn (LINE, ARC, POLYLINE...).
    """
    file_paths = dxf_path if isinstance(dxf_path, list) else [dxf_path]
    
    total_straight_len = 0.0
    total_curved_len = 0.0
    total_entity_counts = {"LINE": 0, "ARC": 0, "CIRCLE": 0, "POLYLINE": 0, "LWPOLYLINE": 0, "SPLINE": 0, "TEXT": 0, "MTEXT": 0}
    files_processed = 0
    warnings_list = []
    all_texts = []

    for path in file_paths:
        try:
            doc = ezdxf.readfile(path)
            msp = doc.modelspace()
            
            straight_len = 0.0
            curved_len = 0.0
            entity_counts = {"LINE": 0, "ARC": 0, "CIRCLE": 0, "POLYLINE": 0, "LWPOLYLINE": 0, "SPLINE": 0, "TEXT": 0, "MTEXT": 0}
            
            # Duyệt qua các thực thể trong không gian mô hình
            for entity in msp:
                entity_type = entity.dxftype()
                
                # Bỏ qua các đường không nằm trong danh sách cho phép (nếu có cấu hình danh sách)
                if ALLOWED_ENTITY_TYPES and entity_type not in ALLOWED_ENTITY_TYPES:
                    continue
                
                if entity_type == 'LINE':
                    start = entity.dxf.start
                    end = entity.dxf.end
                    l = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                    straight_len += l
                    entity_counts["LINE"] += 1
                    
                elif entity_type == 'ARC':
                    radius = entity.dxf.radius
                    start_angle = entity.dxf.start_angle
                    end_angle = entity.dxf.end_angle
                    if end_angle < start_angle: end_angle += 360
                    angle_diff_rad = math.radians(end_angle - start_angle)
                    l = radius * angle_diff_rad
                    curved_len += l
                    entity_counts["ARC"] += 1

                elif entity_type == 'CIRCLE':
                    l = 2 * math.pi * entity.dxf.radius
                    curved_len += l
                    entity_counts["CIRCLE"] += 1
                    
                elif entity_type == 'LWPOLYLINE':
                    # Duyệt các đoạn để kiểm tra độ phình (đường cong)
                    points = entity.get_points(format='xyb') # x, y, bulge
                    for i in range(len(points) - 1):
                        p1, p2 = points[i], points[i+1]
                        bulge = p1[2] # bulge nằm ở điểm bắt đầu
                        dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                        
                        if bulge != 0:
                            # Tính chiều dài cung từ dây cung và độ phình
                            theta = 4 * math.atan(abs(bulge))
                            radius = dist / (2 * math.sin(theta/2))
                            l = radius * theta
                            curved_len += l
                        else:
                            straight_len += dist
                    
                    # Đóng vòng lặp nếu cần
                    if entity.is_closed:
                        p1, p2 = points[-1], points[0]
                        bulge = p1[2]
                        dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                        if bulge != 0:
                            theta = 4 * math.atan(abs(bulge))
                            radius = dist / (2 * math.sin(theta/2))
                            l = radius * theta
                            curved_len += l
                        else:
                            straight_len += dist

                    entity_counts["LWPOLYLINE"] += 1

                elif entity_type == 'POLYLINE':
                    # Đơn giản hóa: coi polyline cũ là các đoạn thẳng, hoặc kiểm tra đỉnh
                    # Giả định chủ yếu là thẳng cho polyline 2D cũ trừ khi có chỉ định khác
                    points = list(entity.points())
                    for i in range(len(points) - 1):
                        p1, p2 = points[i], points[i+1]
                        l = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                        straight_len += l
                    if entity.is_closed:
                        p1, p2 = points[-1], points[0]
                        l = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                        straight_len += l
                    entity_counts["POLYLINE"] += 1
                    
                elif entity_type == 'TEXT':
                    all_texts.append(entity.dxf.text)
                    entity_counts["TEXT"] += 1

                elif entity_type == 'MTEXT':
                    all_texts.append(entity.text)
                    entity_counts["MTEXT"] += 1
                    
                # TODO: CÀI ĐẶT SPLINE
            
            total_straight_len += straight_len
            total_curved_len += curved_len
            for k in entity_counts:
                total_entity_counts[k] += entity_counts[k]
                
            files_processed += 1

        except IOError:
            warnings_list.append(f"File not found or unreadable: {path}")
        except ezdxf.DXFStructureError:
            warnings_list.append(f"Invalid DXF file structure: {path}")
        except Exception as e:
            warnings_list.append(f"Error processing {path}: {str(e)}")

    if files_processed == 0:
        return {"status": "error", "message": "No DXF files were successfully processed.", "warnings": warnings_list}
        
    return {
        "status": "success",
        "total_len_mm": round(total_straight_len + total_curved_len, 2),
        "straight_len_mm": round(total_straight_len, 2),
        "curved_len_mm": round(total_curved_len, 2),
        "complexity_ratio": round(total_curved_len / (total_straight_len + total_curved_len + 1e-9), 2),
        "entity_counts": total_entity_counts,
        "texts": all_texts,
        "files_processed": files_processed,
        "warnings": warnings_list
    }

if __name__ == "__main__":
    # Test with a dummy file if run directly, or user can import
    pass
