import json
from typing import Any, Dict, List

# Generate HTML table from Splunk data for the first list
def generate_first_splunk_html_table(data: List[Dict[str, Any]]) -> str:
    html: str = "<table border='1' style='width:100%; border-collapse: collapse; text-align: center; padding: 8px;'>"

    # Adding header row
    html += "<thead><tr style='background-color: #f2f2f2;'>"
    headers = ['Event API', 'Response Time Steady Period']
    for header in headers:
        html += f"<th style='padding: 8px;'>{header}</th>"
    html += "</tr></thead>"

    # Adding value rows
    html += "<tbody>"
    for entry in data:
        html += "<tr>"
        html += f"<td style='padding: 8px;'>{entry['event_api'].replace('_', ' ').replace('/', ' / ')}</td>"
        html += f"<td style='padding: 8px;'>{entry.get('00:00:00', 'N/A')}</td>"
        html += "</tr>"
    html += "</tbody>"

    html += "</table><br>"
    return html

# Generate HTML table from Splunk data for the second list
def generate_second_splunk_html_table(data: List[Dict[str, Any]]) -> str:
    html: str = "<table border='1' style='width:100%; border-collapse: collapse; text-align: center; padding: 8px;'>"

    # Adding header row
    html += "<thead><tr style='background-color: #f2f2f2;'>"
    headers = ['Event API', 'AVG_TPS', 'MAX_TPS']
    for header in headers:
        html += f"<th style='padding: 8px;'>{header}</th>"
    html += "</tr></thead>"

    # Adding value rows
    html += "<tbody>"
    for entry in data:
        html += "<tr>"
        html += f"<td style='padding: 8px;'>{entry['event_api'].replace('_', ' ').replace('/', ' / ')}</td>"
        html += f"<td style='padding: 8px;'>{entry.get('AVG_TPS', 'N/A')}</td>"
        html += f"<td style='padding: 8px;'>{entry.get('MAX_TPS', 'N/A')}</td>"
        html += "</tr>"
    html += "</tbody>"

    html += "</table><br>"
    return html
