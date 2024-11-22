import json
from typing import Any, Dict, List

# Extracting series information and converting it into an HTML table
def extract_series_to_html(series: Dict[str, Any]) -> str:
    title: str = series['tags']['name']
    columns: List[str] = series['columns']
    values: List[List[Any]] = series['values']

    # Creating an HTML table
    html: str = f"<h3>{title.replace('_', ' ').replace('/', ' / ')}</h3>"
    html += "<table border='1' style='width:100%; border-collapse: collapse; text-align: center; padding: 8px;'>"

    # Adding header row
    html += "<thead><tr style='background-color: #f2f2f2;'>"
    for column in columns:
        html += f"<th style='padding: 8px;'>{column}</th>"
    html += "</tr></thead>"

    # Adding value rows
    html += "<tbody>"
    for value in values:
        html += "<tr>"
        for v in value:
            formatted_value: str = f"{v:.2f}" if isinstance(v, float) else str(v)
            html += f"<td style='padding: 8px;'>{formatted_value}</td>"
        html += "</tr>"
    html += "</tbody>"

    html += "</table><br>"
    return html


# Generate HTML content from JSON data
def generate_html_from_json_grafana(data: List[Dict[str, Any]]) -> str:
    html_content: str = ""
    for result in data:
        for statement in result.get('results', []):
            for series in statement.get('series', []):
                html_content += extract_series_to_html(series)
    return html_content