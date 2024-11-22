from atlassian import Confluence
import json

# Define your Atlassian Confluence credentials and domain
confluence = Confluence(
    url="https://telusvideoservices.atlassian.net/wiki",
    username="julio.cruz@telus.com",
    password="ATATT3xFfGF0yUKnKqmYR4Sk0U2M4q6as1fDwEjkpyDd7cgO1HOzqoO3NSEiTWv4kjPZDhDfpUB8w9MB"
)

# The title of the new page you want to create or update
page_title = "PT Load Test - TPS Mix Scenario - 250K - 2024 Oct 0 - Run"

# The space key where the page will be created
space_key = "PTS"

# The parent page ID (replace with the correct ID if needed)
parent_page_id = 2731212839

# Load Splunk report data from JSON file
with open('splunk_reports.json', 'r') as f:
    splunk_data = json.load(f)

# Extract data from the report (assuming the data is in the format provided)
performance_data = splunk_data[0]
tps_data = splunk_data[1]

# Create a table for performance data
performance_table = "<h2>Performance Data (Latency)</h2><table><tr><th>Event API</th><th>Latency (00:00:00)</th></tr>"
for entry in performance_data:
    performance_table += f"<tr><td>{entry['event_api']}</td><td>{entry['00:00:00']}</td></tr>"
performance_table += "</table>"

# Create a table for TPS data
tps_table = "<h2>TPS Data (AVG and MAX)</h2><table><tr><th>Event API</th><th>AVG TPS</th><th>MAX TPS</th></tr>"
for entry in tps_data:
    tps_table += f"<tr><td>{entry['event_api']}</td><td>{entry['AVG_TPS']}</td><td>{entry['MAX_TPS']}</td></tr>"
tps_table += "</table>"

# Template structure for the page content (using HTML format)
page_content = f"""
<h1>Performance Test Report</h1>
<p><strong>Test Scenario:</strong> TPS Mix Scenario - 250K</p>
<p><strong>Date:</strong> 2024 Oct 0</p>

{performance_table}

{tps_table}
"""

# Check if the page exists already by title, to update it or create a new one
existing_page = confluence.get_page_by_title(space_key, page_title)

if existing_page:
    # If the page exists, update the content
    page_id = existing_page["id"]
    confluence.update_page(
        page_id=page_id,
        title=page_title,
        body=page_content
    )
    print(f"Page '{page_title}' updated successfully.")
else:
    # If the page doesn't exist, create it
    confluence.create_page(
        space=space_key,
        title=page_title,
        body=page_content,
        parent_id=parent_page_id
    )
    print(f"Page '{page_title}' created successfully.")
