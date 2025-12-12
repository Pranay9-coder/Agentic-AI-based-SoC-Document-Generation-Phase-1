"""
XML Generator for .regs files
File: backend/utils/xml_generator.py
"""
import re
from datetime import datetime
from typing import Dict, Any


class XMLGenerator:
    """Generate NXP .regs XML from register data"""
    
    def generate(self, register_data: Dict[str, Any], device_name: str) -> str:
        """Generate NXP .regs XML from register data"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        xml = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml += '<!-- Copyright 2025 NXP\n    NXP Confidential. For internal use only. -->\n'
        xml += '<!DOCTYPE UniversalDevice PUBLIC "-//W3C//ENTITIES HTML MathML Set//EN//XML" "http://www.w3.org/2003/entities/2007/htmlmathml-f.ent">\n'
        xml += '<crr:UniversalDevice xsi:schemaLocation="agen/regs/latest http://apif.nxp.com/schemas/regs/latest/regs.xsd" '
        xml += 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:crr="agen/regs/latest">\n'
        
        xml += f'  <creation_info author="$Author$" date="{current_time}" revision="$Revision$" source="$Source$"/>\n'
        
        device_id = re.sub(r'[^A-Z0-9_]', '_', device_name.upper())
        xml += '  <GeneralPeriphery>\n'
        xml += '    <GeneralParameters>\n'
        xml += '      <instance_header>\n'
        xml += '        <metadata>\n'
        xml += f'          <brief_description>{self._escape_xml(device_name)}</brief_description>\n'
        xml += '          <long_description/>\n'
        xml += '          <category type="IP"/>\n'
        xml += f'          <nickname pattern="{device_id}@[index]">\n'
        xml += '            <index type="int" use_for_single_inst="optional"/>\n'
        xml += '          </nickname>\n'
        xml += '        </metadata>\n'
        xml += '        <template_parameters>\n'
        xml += f'          <include_template_parameters file="../params/{device_id.lower()}.paramdef"/>\n'
        xml += '        </template_parameters>\n'
        xml += '      </instance_header>\n'
        xml += '      <general_parameter_defs/>\n'
        xml += '    </GeneralParameters>\n'
        
        xml += '    <register_defs>\n'
        xml += '      <address_block byte_order="littleEndian" lau="8">\n'
        xml += '        <base_address/>\n'
        xml += '        <bit_order order="lsb0"/>\n'
        
        for reg in register_data.get('registers', []):
            xml += self._generate_register_xml(reg)
        
        xml += '      </address_block>\n'
        xml += '    </register_defs>\n'
        xml += '  </GeneralPeriphery>\n'
        xml += '</crr:UniversalDevice>'
        
        return xml
    
    def _generate_register_xml(self, reg: Dict[str, Any]) -> str:
        """Generate XML for a single register"""
        xml = f'        <register_def name="{self._escape_xml(reg.get("name", "UNKNOWN"))}" '
        xml += f'id="{reg.get("id", reg.get("name", "UNKNOWN"))}" '
        xml += f'width="{reg.get("width", 32)}">\n'
        
        xml += f'          <brief_description>{self._escape_xml(reg.get("brief_desc", ""))}</brief_description>\n'
        xml += f'          <long_description><p>{self._escape_xml(reg.get("long_desc", ""))}</p></long_description>\n'
        xml += f'          <address offset="{reg.get("offset", "0x0")}"/>\n'
        xml += f'          <reset_value value="{reg.get("reset_value", "0x0")}"/>\n'
        
        for field in reg.get('fields', []):
            xml += self._generate_field_xml(field)
        
        xml += '        </register_def>\n'
        return xml
    
    def _generate_field_xml(self, field: Dict[str, Any]) -> str:
        """Generate XML for a bit field"""
        if field.get("reserved", False):
            return f'          <reserved_bit_field position="{field.get("position", 0)}" width="{field.get("width", 1)}" access="{field.get("access", "ROZ")}"/>\n'
        
        xml = f'          <bit_field name="{self._escape_xml(field.get("name", "UNKNOWN"))}" '
        xml += f'id="{field.get("id", field.get("name", "UNKNOWN"))}" '
        xml += f'position="{field.get("position", 0)}" '
        xml += f'width="{field.get("width", 1)}" '
        xml += f'access="{field.get("access", "RW")}"'
        
        if field.get("modified_write"):
            xml += f' modified_write_values="{field.get("modified_write")}"'
        
        xml += '>\n'
        xml += f'            <brief_description>{self._escape_xml(field.get("brief_desc", ""))}</brief_description>\n'
        xml += f'            <long_description><p>{self._escape_xml(field.get("long_desc", ""))}</p></long_description>\n'
        
        for value in field.get('values', []):
            xml += f'            <bit_field_value value_id="{value.get("id", "UNKNOWN")}" value="{value.get("value", "0b0")}"'
            if value.get("usage"):
                xml += f' usage="{value.get("usage")}"'
            xml += '>\n'
            xml += f'              <brief_description>{self._escape_xml(value.get("desc", ""))}</brief_description>\n'
            xml += '            </bit_field_value>\n'
        
        xml += '          </bit_field>\n'
        return xml
    
    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters"""
        if not text:
            return ""
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text