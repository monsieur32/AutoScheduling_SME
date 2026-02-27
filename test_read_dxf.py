import ezdxf
import math


def calculate_lengths(file_path):
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        total_linear = 0.0
        total_curve = 0.0

        for entity in msp:
            e_type = entity.dxftype()

            # 1. Xử lý đường thẳng đơn (LINE)
            if e_type == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                dist = math.dist(start, end)
                total_linear += dist

            # 2. Xử lý hình tròn (CIRCLE) -> Tính chu vi
            elif e_type == 'CIRCLE':
                total_curve += 2 * math.pi * entity.dxf.radius

            # 3. Xử lý cung tròn (ARC) -> Tính độ dài cung
            elif e_type == 'ARC':
                # Độ dài cung = R * (góc_kết_thúc - góc_bắt_đầu) tính bằng radian
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle

                # Xử lý trường hợp góc đi qua điểm 0 độ
                if end_angle < start_angle:
                    end_angle += 360

                angle_diff = math.radians(end_angle - start_angle)
                total_curve += radius * angle_diff

            # 4. Xử lý Đa tuyến (LWPOLYLINE) - Quan trọng nhất trong file của bạn
            elif e_type == 'LWPOLYLINE':
                # virtual_entities() tự động tách Polyline thành các LINE và ARC nhỏ
                for sub_entity in entity.virtual_entities():
                    if sub_entity.dxftype() == 'LINE':
                        total_linear += math.dist(sub_entity.dxf.start, sub_entity.dxf.end)
                    elif sub_entity.dxftype() == 'ARC':
                        # Tính độ dài cung cho phần cong của Polyline
                        radius = sub_entity.dxf.radius
                        start_angle = sub_entity.dxf.start_angle
                        end_angle = sub_entity.dxf.end_angle
                        if end_angle < start_angle:
                            end_angle += 360
                        total_curve += radius * math.radians(end_angle - start_angle)

        return total_linear, total_curve

    except Exception as e:
        print(f"Lỗi: {e}")
        return 0, 0


# Thực thi
file_name = "designs/250911700.dxf"  # Thay bằng file của bạn
linear, curve = calculate_lengths(file_name)

print(f"{'=' * 30}")
print(f"TỔNG CHIỀU DÀI ĐƯỜNG THẲNG: {linear:.2f} mm")
print(f"TỔNG CHIỀU DÀI ĐƯỜNG CONG:  {curve:.2f} mm")
print(f"TỔNG CỘNG:                 {linear + curve:.2f} mm")
print(f"{'=' * 30}")