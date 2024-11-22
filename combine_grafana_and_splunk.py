from typing import Any, Dict, List

# Combine Grafana and Splunk data into a unified structure
def combine_data(grafana_data: List[Dict[str, Any]], splunk_data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    combined_data: List[Dict[str, Any]] = []

    # Assuming splunk_data[0] and splunk_data[1] are lists of dicts
    splunk_dict_1 = {entry['event_api']: entry for entry in splunk_data[0]}
    splunk_dict_2 = {entry['event_api']: entry for entry in splunk_data[1]}

    for result in grafana_data:
        for statement in result.get('results', []):
            for series in statement.get('series', []):
                event_api: str = series['tags']['name']
                columns: List[str] = series['columns']
                values: List[List[Any]] = series['values']

                for value in values:
                    combined_entry = {
                        'event_api': event_api,
                        'grafana_columns': columns,
                        'grafana_values': value,
                    }
                    # Check if Splunk data exists for this event
                    splunk_entry_1 = splunk_dict_1.get(event_api)
                    splunk_entry_2 = splunk_dict_2.get(event_api)

                    if splunk_entry_1:
                        combined_entry.update({
                            'AVG_TPS_1': splunk_entry_1.get('AVG_TPS', 'N/A'),
                            'MAX_TPS_1': splunk_entry_1.get('MAX_TPS', 'N/A')
                        })

                    if splunk_entry_2:
                        combined_entry.update({
                            'AVG_TPS_2': splunk_entry_2.get('AVG_TPS', 'N/A'),
                            'MAX_TPS_2': splunk_entry_2.get('MAX_TPS', 'N/A')
                        })

                    combined_data.append(combined_entry)

    return combined_data

# Generate HTML table from combined data
def generate_combined_html_table(data: List[Dict[str, Any]]) -> str:
    html: str = "<table border='1' style='width:100%; border-collapse: collapse; text-align: center; padding: 8px;'>"

    # Adding header row
    html += "<thead><tr style='background-color: #f2f2f2;'>"
    headers = [
        'Event API', 'Grafana Columns', 'Grafana Values', 'AVG_TPS (Set 1)', 'MAX_TPS (Set 1)', 'AVG_TPS (Set 2)', 'MAX_TPS (Set 2)'
    ]
    for header in headers:
        html += f"<th style='padding: 8px;'>{header}</th>"
    html += "</tr></thead>"

    # Adding value rows
    html += "<tbody>"
    for entry in data:
        html += "<tr>"
        html += f"<td style='padding: 8px;'>{entry['event_api'].replace('_', ' ').replace('/', ' / ')}</td>"
        html += f"<td style='padding: 8px;'>{', '.join(entry['grafana_columns'])}</td>"
        html += f"<td style='padding: 8px;'>{', '.join([str(v) for v in entry['grafana_values']])}</td>"
        html += f"<td style='padding: 8px;'>{entry.get('AVG_TPS_1', 'N/A')}</td>"
        html += f"<td style='padding: 8px;'>{entry.get('MAX_TPS_1', 'N/A')}</td>"
        html += f"<td style='padding: 8px;'>{entry.get('AVG_TPS_2', 'N/A')}</td>"
        html += f"<td style='padding: 8px;'>{entry.get('MAX_TPS_2', 'N/A')}</td>"
        html += "</tr>"
    html += "</tbody>"

    html += "</table><br>"
    return html