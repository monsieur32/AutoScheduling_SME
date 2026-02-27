
import ezdxf
import math

def extract_cutting_info(dxf_paths):
    """
    Phân tích một hoặc nhiều file DXF để trích xuất tổng chiều dài cắt và thông tin hình học.
    Trả về tổng hợp của tất cả các file.
    """
    if isinstance(dxf_paths, str):
        dxf_paths = [dxf_paths]
        
    total_straight = 0.0
    total_curved = 0.0
    total_counts = {"LINE": 0, "ARC": 0, "CIRCLE": 0, "POLYLINE": 0, "LWPOLYLINE": 0, "SPLINE": 0}
    
    success_files = []
    error_messages = []

    for path in dxf_paths:
        try:
            doc = ezdxf.readfile(path)
            msp = doc.modelspace()
            
            straight_len = 0.0
            curved_len = 0.0
            entity_counts = {"LINE": 0, "ARC": 0, "CIRCLE": 0, "POLYLINE": 0, "LWPOLYLINE": 0, "SPLINE": 0}
        
            # Duyệt qua các thực thể trong không gian mô hình
            for entity in msp:
                entity_type = entity.dxftype()
                
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
                    
                # TODO: CÀI ĐẶT SPLINE
                
            # Cập nhật tổng
            total_straight += straight_len
            total_curved += curved_len
            for k in total_counts:
                total_counts[k] += entity_counts[k]
                
            success_files.append(path)

        except IOError:
            error_messages.append(f"{path}: File not found or unreadable.")
        except ezdxf.DXFStructureError:
            error_messages.append(f"{path}: Invalid DXF file structure.")
        except Exception as e:
            error_messages.append(f"{path}: {str(e)}")

    if not success_files:
        return {
            "status": "error", 
            "message": "Không thể đọc bất kỳ file nào: " + "; ".join(error_messages)
        }
        
    return {
        "status": "success",
        "files_processed": len(success_files),
        "total_len_mm": round(total_straight + total_curved, 2),
        "straight_len_mm": round(total_straight, 2),
        "curved_len_mm": round(total_curved, 2),
        "complexity_ratio": round(total_curved / (total_straight + total_curved + 1e-9), 2),
        "entity_counts": total_counts,
        "warnings": error_messages if error_messages else None
    }

if __name__ == "__main__":
    # Test with a dummy file if run directly, or user can import
    pass
