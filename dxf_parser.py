
import ezdxf
import math

def extract_cutting_info(dxf_path):
    """
    Phân tích file DXF để trích xuất tổng chiều dài cắt và thông tin hình học.
    Giả định đường cắt nằm trên các layer cụ thể hoặc là các thực thể chuẩn (LINE, ARC, POLYLINE...).
    """
    try:
        doc = ezdxf.readfile(dxf_path)
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
            
        return {
            "status": "success",
            "filename": dxf_path,
            "total_len_mm": round(straight_len + curved_len, 2),
            "straight_len_mm": round(straight_len, 2),
            "curved_len_mm": round(curved_len, 2),
            "complexity_ratio": round(curved_len / (straight_len + curved_len + 1e-9), 2),
            "entity_counts": entity_counts
        }

    except IOError:
        return {"status": "error", "message": "File not found or unreadable."}
    except ezdxf.DXFStructureError:
        return {"status": "error", "message": "Invalid DXF file structure."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Test with a dummy file if run directly, or user can import
    pass
