
import ezdxf
import math

def extract_cutting_info(dxf_path):
    """
    Parses a DXF file to extract total cutting length and other geometry info.
    Assumes cutting paths are on specific layers or are standard entities (LINE, ARC, POLYLINE, LWPOLYLINE, SPLINE, CIRCLE).
    """
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        straight_len = 0.0
        curved_len = 0.0
        entity_counts = {"LINE": 0, "ARC": 0, "CIRCLE": 0, "POLYLINE": 0, "LWPOLYLINE": 0, "SPLINE": 0}
        
        # Iterate through entities in model space
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
                # Iterate segments to check for bulges (curves)
                points = entity.get_points(format='xyb') # x, y, bulge
                for i in range(len(points) - 1):
                    p1, p2 = points[i], points[i+1]
                    bulge = p1[2] # bulge is at start point
                    dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                    
                    if bulge != 0:
                        # Calculate arc length from chord length and bulge
                        # sagitta = bulge * (dist / 2) ... simplified:
                        # Arc length formula from bulge: L = 4 * atan(|b|) * (chord_len / sin(4 * atan(|b|)) / 2 * radius...) 
                        # Easier: theta = 4 * atan(abs(bulge))
                        # radius = dist / (2 * sin(theta/2))
                        # arc_len = radius * theta
                        theta = 4 * math.atan(abs(bulge))
                        radius = dist / (2 * math.sin(theta/2))
                        l = radius * theta
                        curved_len += l
                    else:
                        straight_len += dist
                
                # Close the loop if needed
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
                # Simplified: treat legacy polylines as composed of linear segments for now, or check vertices
                # Assuming mostly straight for legacy 2D polys in this specific domain context unless specified
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
                
            # TODO: IMPL SPLINE
            
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
