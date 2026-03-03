import ezdxf
import math


def calculate_total_cut_length(file_path):
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        # Chỉ lấy các thực thể có khả năng tạo thành đường cắt
        # Chúng ta bỏ qua DIMENSION, TEXT, MTEXT, v.v.
        cutting_entities = msp.query('LINE CIRCLE ARC LWPOLYLINE POLYLINE')

        total_length = 0.0

        print(f"--- ĐANG PHÂN TÍCH CHIỀU DÀI CẮT ---")

        for entity in cutting_entities:
            e_type = entity.dxftype()
            length = 0.0

            if e_type == 'LINE':
                # Khoảng cách giữa điểm đầu và điểm cuối
                length = math.dist(entity.dxf.start, entity.dxf.end)

            elif e_type == 'CIRCLE':
                # Chu vi hình tròn: 2 * pi * R
                length = 2 * math.pi * entity.dxf.radius

            elif e_type == 'ARC':
                # Chiều dài cung tròn: R * góc (radian)
                delta_angle = entity.dxf.end_angle - entity.dxf.start_angle
                if delta_angle < 0: delta_angle += 360
                length = entity.dxf.radius * math.radians(delta_angle)

            elif e_type in ['LWPOLYLINE', 'POLYLINE']:
                # Polyline có thể chứa cả đoạn thẳng và cung tròn
                # virtual_entities() giúp tách chúng ra để tính chính xác nhất
                for sub_entity in entity.virtual_entities():
                    if sub_entity.dxftype() == 'LINE':
                        length += math.dist(sub_entity.dxf.start, sub_entity.dxf.end)
                    elif sub_entity.dxftype() == 'ARC':
                        d_angle = sub_entity.dxf.end_angle - sub_entity.dxf.start_angle
                        if d_angle < 0: d_angle += 360
                        length += sub_entity.dxf.radius * math.radians(d_angle)

            total_length += length

        print(f"Tổng chiều dài máy cần cắt: {total_length:.2f} mm")
        return total_length

    except Exception as e:
        print(f"Lỗi: {e}")
        return 0.0


# Sử dụng
file_name = "designs/250911700.dxf"
calculate_total_cut_length(file_name)