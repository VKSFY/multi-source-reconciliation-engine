from __future__ import annotations

import io
import zipfile
import xml.etree.ElementTree as ET
from typing import Any


NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_letter(index: int) -> str:
    letter = ""
    while index >= 0:
        letter = chr(index % 26 + 65) + letter
        index = index // 26 - 1
    return letter


def write_simple_xlsx(path: str, rows: list[dict[str, Any]]) -> None:
    headers = list(rows[0].keys()) if rows else []
    sheet_rows = [headers] + [[row.get(h, "") for h in headers] for row in rows]

    def build_sheet_xml() -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            "<sheetData>",
        ]
        for r_idx, row in enumerate(sheet_rows, start=1):
            lines.append(f'<row r="{r_idx}">')
            for c_idx, value in enumerate(row):
                ref = f"{_col_letter(c_idx)}{r_idx}"
                text = str(value if value is not None else "")
                text = (
                    text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                lines.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
            lines.append("</row>")
        lines += ["</sheetData>", "</worksheet>"]
        return "".join(lines)

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    rels_root = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    rels_wb = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/></Relationships>'
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels_root)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", rels_wb)
        zf.writestr("xl/worksheets/sheet1.xml", build_sheet_xml())


def read_simple_xlsx(path: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(path, "r") as zf:
        sheet_xml = zf.read("xl/worksheets/sheet1.xml")
        shared = {}
        if "xl/sharedStrings.xml" in zf.namelist():
            shared_xml = ET.parse(io.BytesIO(zf.read("xl/sharedStrings.xml"))).getroot()
            shared = {
                idx: "".join(node.itertext()).strip()
                for idx, node in enumerate(shared_xml.findall("m:si", NS))
            }

    root = ET.parse(io.BytesIO(sheet_xml)).getroot()
    rows_data: list[list[str]] = []
    for row in root.findall(".//m:row", NS):
        vals: list[str] = []
        for cell in row.findall("m:c", NS):
            cell_type = cell.attrib.get("t", "")
            if cell_type == "inlineStr":
                t_node = cell.find("m:is/m:t", NS)
                vals.append("" if t_node is None or t_node.text is None else t_node.text)
                continue

            v_node = cell.find("m:v", NS)
            if v_node is None or v_node.text is None:
                vals.append("")
            elif cell_type == "s":
                vals.append(shared.get(int(v_node.text), ""))
            else:
                vals.append(v_node.text)
        rows_data.append(vals)

    if not rows_data:
        return []
    headers = [h.strip() for h in rows_data[0]]
    out: list[dict[str, str]] = []
    for row in rows_data[1:]:
        padded = row + [""] * (len(headers) - len(row))
        out.append({headers[i]: padded[i] for i in range(len(headers))})
    return out
