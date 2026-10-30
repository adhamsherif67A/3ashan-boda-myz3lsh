"""Sensor rendering repair applied only to the generated simulation world."""
import xml.etree.ElementTree as ET

def repair_depth_cover(path):
    tree=ET.parse(path)
    model=tree.find(".//model[@name='mako']")
    if model is None:raise ValueError('Generated world has no Mako model')
    removed=[]
    # A translucent protective cover is not a valid near-range depth return.
    # Keep collisions, inertials, sensors and TF; omit only this render mesh.
    for link in model.findall('.//link'):
        for visual in list(link.findall('visual')):
            if 'camera_dome' in visual.get('name',''):
                removed.append(visual.get('name'));link.remove(visual)
    if not removed:raise ValueError('Expected camera dome render mesh was not found')
    tree.write(path,encoding='utf-8',xml_declaration=True)
    return removed
