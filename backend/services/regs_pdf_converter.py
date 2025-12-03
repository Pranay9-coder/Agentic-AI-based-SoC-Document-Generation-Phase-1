"""
Service for converting .regs XML files to PDF documentation
"""
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Flowable
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER


class RegsToPDFConverter:
    """Convert .regs XML to PDF with bit diagrams"""
    
    def __init__(self):
        self.ns = {
            'crr': 'agen/regs/latest',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def convert(self, regs_file_path: str, output_pdf_path: str) -> dict:
        """
        Convert .regs file to PDF
        
        Args:
            regs_file_path: Path to input .regs XML file
            output_pdf_path: Path for output PDF file
            
        Returns:
            dict: Conversion result with status and message
        """
        try:
            # Parse XML
            tree = ET.parse(regs_file_path)
            root = tree.getroot()
            
            # Extract register data
            registers = self._extract_register_data(root)
            
            if not registers:
                return {
                    'status': 'error',
                    'message': 'No registers found in .regs file'
                }
            
            # Generate PDF
            self._generate_pdf(registers, output_pdf_path)
            
            return {
                'status': 'success',
                'message': f'Successfully converted {len(registers)} register(s) to PDF',
                'register_count': len(registers),
                'output_file': output_pdf_path
            }
            
        except ET.ParseError as e:
            return {
                'status': 'error',
                'message': f'Invalid XML format: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Conversion failed: {str(e)}'
            }
    
    def _extract_register_data(self, root):
        """Extract register information from XML"""
        registers = []
        
        for register in root.findall('.//register_def', self.ns):
            reg_name = register.get('name', 'Unknown')
            reg_id = register.get('id', 'Unknown')
            reg_width = int(register.get('width', '32'))
            
            # Extract descriptions
            brief_desc = register.find('brief_description', self.ns)
            long_desc = register.find('long_description', self.ns)
            
            brief_text = brief_desc.text if brief_desc is not None else ''
            long_text_elem = long_desc.find('p', self.ns) if long_desc is not None else None
            long_text = long_text_elem.text if long_text_elem is not None else ''
            
            # Extract offset and reset value
            offset_elem = register.find('address', self.ns)
            reset_elem = register.find('reset_value', self.ns)
            
            offset = offset_elem.get('offset', '0x0') if offset_elem is not None else '0x0'
            reset_value = reset_elem.get('value', '0x0') if reset_elem is not None else '0x0'
            
            # Extract bit fields
            fields = []
            for field in register.findall('bit_field', self.ns):
                field_data = self._extract_field(field)
                fields.append(field_data)
            
            # Extract reserved fields
            for reserved in register.findall('reserved_bit_field', self.ns):
                reserved_data = self._extract_reserved_field(reserved)
                fields.append(reserved_data)
            
            # Sort fields by position (descending)
            fields.sort(key=lambda x: x['position'], reverse=True)
            
            # Validate bit ranges
            validation_errors = self._validate_bit_ranges(reg_name, fields, reg_width)
            
            registers.append({
                'name': reg_name,
                'id': reg_id,
                'width': reg_width,
                'offset': offset,
                'reset_value': reset_value,
                'brief_desc': brief_text,
                'long_desc': long_text,
                'fields': fields,
                'validation_errors': validation_errors
            })
        
        return registers
    
    def _extract_field(self, field):
        """Extract bit field information"""
        name = field.get('name', 'Unknown')
        field_id = field.get('id', 'Unknown')
        position = int(field.get('position', '0'))
        width = int(field.get('width', '1'))
        access = field.get('access', 'RW')
        modified_write = field.get('modified_write_values', '')
        
        brief_desc = field.find('brief_description', self.ns)
        long_desc = field.find('long_description', self.ns)
        
        brief_text = brief_desc.text if brief_desc is not None else ''
        long_text_elem = long_desc.find('p', self.ns) if long_desc is not None else None
        long_text = long_text_elem.text if long_text_elem is not None else ''
        
        # Extract bit field values
        values = []
        for value in field.findall('bit_field_value', self.ns):
            value_id = value.get('value_id', 'Unknown')
            value_val = value.get('value', '0b0')
            usage = value.get('usage', '')
            
            value_brief = value.find('brief_description', self.ns)
            value_desc = value_brief.text if value_brief is not None else ''
            
            values.append({
                'id': value_id,
                'value': value_val,
                'usage': usage,
                'desc': value_desc
            })
        
        return {
            'name': name,
            'id': field_id,
            'position': position,
            'width': width,
            'access': access,
            'modified_write': modified_write,
            'brief_desc': brief_text,
            'long_desc': long_text,
            'values': values,
            'reserved': False
        }
    
    def _extract_reserved_field(self, reserved):
        """Extract reserved field information"""
        position = int(reserved.get('position', '0'))
        width = int(reserved.get('width', '1'))
        access = reserved.get('access', 'ROZ')
        
        return {
            'name': 'Reserved',
            'id': 'RESERVED',
            'position': position,
            'width': width,
            'access': access,
            'modified_write': '',
            'brief_desc': 'Reserved',
            'long_desc': 'Reserved for future use',
            'values': [],
            'reserved': True
        }
    
    def _validate_bit_ranges(self, register_name, fields, register_width):
        """Validate bit ranges for overlaps and gaps"""
        errors = []
        bit_to_field = {}
        
        for field in fields:
            field_start = field['position']
            field_width = field['width']
            field_end = field_start + field_width - 1
            field_name = field['name']
            
            # Check if field exceeds register width
            if field_end >= register_width:
                errors.append(
                    f"Field '{field_name}' bits [{field_end}:{field_start}] "
                    f"exceed register width of {register_width}"
                )
            
            # Check for overlaps
            for bit in range(field_start, min(field_end + 1, register_width)):
                if bit in bit_to_field:
                    overlapping_field = bit_to_field[bit]
                    errors.append(
                        f"Bit {bit} overlaps between '{field_name}' and '{overlapping_field['name']}'"
                    )
                    break
                bit_to_field[bit] = field
        
        return errors
    
    def _generate_pdf(self, registers, output_path):
        """Generate PDF from register data"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        
        # Create styles
        styles = getSampleStyleSheet()
        
        normal_style = styles['Normal']
        normal_style.fontSize = 9
        normal_style.leading = 11
        
        big_normal_style = ParagraphStyle(
            'big_normal',
            parent=normal_style,
            fontSize=14,
            leading=16
        )
        
        center_style = ParagraphStyle(
            'CenterStyle',
            parent=normal_style,
            alignment=TA_CENTER
        )
        
        # Generate content for each register
        for register in registers:
            # Register header
            reg_header = Paragraph(f"{register['name']}", big_normal_style)
            elements.append(reg_header)
            elements.append(Spacer(1, 0.1*inch))
            
            # Offset table
            offset_value = register['offset']
            if offset_value.startswith('0x'):
                offset_hex = offset_value[2:].upper()
                offset_formatted = f"{offset_hex}h"
            else:
                offset_formatted = offset_value
            
            reg_info_data = [
                ['Register', 'Offset'],
                [register['id'], offset_formatted]
            ]
            
            available_width = doc.width
            reg_info_table = Table(reg_info_data, colWidths=[available_width/2, available_width/2])
            
            reg_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F0F0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('TOPPADDING', (0, 0), (-1, 0), 4),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(Paragraph("<b>Offset</b>", normal_style))
            elements.append(Spacer(1, 0.15*inch))
            elements.append(reg_info_table)
            elements.append(Spacer(1, 0.15*inch))
            
            # Description
            if register['brief_desc']:
                elements.append(Paragraph('<b>Function</b>', normal_style))
                elements.append(Paragraph(register['brief_desc'], normal_style))
                elements.append(Spacer(1, 0.15*inch))
            
            # Bit diagram
            elements.append(Paragraph("<b>Diagram</b>", normal_style))
            bit_diagram = self._create_bit_diagram(register, doc.width)
            elements.append(bit_diagram)
            elements.append(Spacer(1, 0.2*inch))
            
            # Field details table
            elements.append(Paragraph("<b>Fields</b>", normal_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Create field table
            table_data = [['Field', 'Function']]
            
            for field in register['fields']:
                if field['width'] == 1:
                    bit_range = f"{field['position']}"
                else:
                    bit_range = f"{field['position'] + field['width'] - 1}-{field['position']}"
                
                if field['reserved']:
                    field_cell = f"{bit_range}<br/>{'—' * 1}"
                else:
                    field_cell = f"{bit_range}<br/>{field['id']}"
                
                function_parts = []
                if field['long_desc'] and field['long_desc'] != field['brief_desc']:
                    long_clean = field['long_desc'].strip()
                    if '\n' in long_clean:
                        parts = long_clean.split('\n', 1)
                        long_clean = parts[0] + '.' + '<br/>' + parts[1].replace('\n', ' ')
                    function_parts.append(long_clean)
                
                if field['modified_write']:
                    function_parts.append(f"<br/>{field['modified_write']}")
                
                if field['values']:
                    for val in field['values']:
                        usage_str = f" ({val['usage']})" if val['usage'] else ""
                        function_parts.append(f"<br/>{val['value']}{usage_str}: {val['desc']}")
                
                function_cell = ''.join(function_parts) if function_parts else ""
                
                table_data.append([
                    Paragraph(field_cell, center_style),
                    Paragraph(function_cell, normal_style)
                ])
            
            col_widths = [1.5*inch, 5*inch]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F0F0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(table)
            elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
    
    def _create_bit_diagram(self, register, page_width):
        """Create simplified bit diagram (basic version)"""
        # This is a simplified version - you can enhance with the full diagram logic
        fields = register['fields']
        
        # Create simple table representation
        bit_headers = ['Bits']
        field_row = ['Fields']
        
        for field in fields:
            if field['width'] == 1:
                bit_headers.append(str(field['position']))
            else:
                bit_range = f"{field['position'] + field['width'] - 1}-{field['position']}"
                bit_headers.append(bit_range)
            field_row.append(field['id'])
        
        table_data = [bit_headers, field_row]
        
        col_widths = [0.8*inch] + [1.2*inch] * (len(bit_headers) - 1)
        diagram_table = Table(table_data, colWidths=col_widths)
        
        diagram_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return diagram_table