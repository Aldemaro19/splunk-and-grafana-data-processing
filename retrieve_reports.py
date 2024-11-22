import requests
import json
import time
import splunklib.client as splunk_client
import splunklib.results as splunk_results
import traceback
import logging
from splunk_to_html import generate_first_splunk_html_table, generate_second_splunk_html_table
from util import save_html_to_file, load_json
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

# Function to fetch reports from Grafana and save as JSON
def fetch_grafana_reports() -> None:
    try:
        logging.info("Fetching Grafana Reports...")
        GRAFANA_API_URL: str = "http://k8s-jmeter8-grafana-75057ff730-1342617267.ca-central-1.elb.amazonaws.com/api/datasources/proxy/1/query"
        GRAFANA_API_KEY: str = "glsa_T79zbU6RNK2ieTaDPqI359J57CiPHRIK_6967b9fe"
        
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {GRAFANA_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        queries: List[str] = [
            '''SELECT count("num_requests") as Count, 
                count("num_requests")/((1727818200795 - 1727814600795)/1000) as "Throughput" 
                FROM "locust_test" 
                WHERE ("test_case" =~ /^Telus\.Optik\.Mix\.PT\.2024-10-01\.19:36\.250K-Main$/) 
                AND time >= 1727814631889ms AND time <= 1727818231889ms 
                GROUP BY "name" ORDER BY time DESC''',

            '''SELECT last("p90") as "90%", last("p95") as "95%", last("p99") as "99%" 
                FROM "locust_test_percentiles" 
                WHERE ("test_case" =~ /^Telus\.Optik\.Mix\.PT\.2024-10-01\.19:36\.250K-Main$/) 
                AND time >= 1727814723420ms AND time <= 1727818323420ms 
                GROUP BY "name" ORDER BY time DESC'''
        ]
        
        all_results: List[Any] = []
        
        for query in queries:
            payload: Dict[str, str] = {
                "db": "telegraf",
                "q": query
            }
            
            response = requests.post(GRAFANA_API_URL, headers=headers, data=payload, timeout=120)
            
            if response.status_code == 200:
                all_results.append(response.json())
            else:
                raise Exception(f"Failed to fetch Grafana data: {response.status_code}")
        
        # Save results to a JSON file
        with open('grafana_reports.json', 'w') as json_file:
            json.dump(all_results, json_file, indent=4)

        logging.info("✅ Grafana reports fetched and saved to grafana_reports.json")
    
    except Exception as e:
        logging.error(f"❌ Error fetching Grafana reports: {e}")
        logging.debug(traceback.format_exc())

# Function to fetch data from Splunk and save to JSON
def fetch_splunk_data() -> None:
    try:
        logging.info("Fetching Splunk Data...")
        service: Optional[splunk_client.Service] = connect_splunk()

        if not service:
            logging.error("Failed to connect to Splunk.")
            return

        queries: List[str] = [
            '''search index=avs_gcp_http_lb 
            | rename data.httpRequest.requestUrl AS requestUrl, data.httpRequest.requestMethod AS requestMethod, attributes.logging.googleapis.com/timestamp AS timestamp, data.httpRequest.latency AS latency
            | rex field=requestUrl "(?<page>PAGE/\\d+)"
            | rex field=requestUrl "(?<menu>MENU/menu)"
            | rex field=requestUrl "\\d+/\\w+/\\w+/\\w+/\\w+/(?<sss>\\w+/\\w+[/A-Z]+)"  
            | eval event_api=requestMethod." ".sss 
            | search event_api="*" 
            | bucket _time span=1d  
            | convert timeformat="%H:%M:%S" ctime(_time) AS timeF 
            | chart eval(round(perc95(latency),4)) over event_api by timeF limit=0 
            | fillnull value=0.0''',

            '''search index=avs_gcp_http_lb 
            | rename data.httpRequest.requestUrl AS requestUrl, data.httpRequest.requestMethod AS requestMethod, attributes.logging.googleapis.com/timestamp AS timestamp
            | rex field=requestUrl "(?<page>PAGE/\\d+)"
            | rex field=requestUrl "(?<menu>MENU/menu)"
            | rex field=requestUrl "\\d+/\\w+/\\w+/\\w+/\\w+/(?<sss>\\w+/\\w+[/A-Z]+)"  
            | eval event_api=requestMethod." ".sss 
            | search event_api="*" 
            | eval tzSplit=split(timestamp,".") 
            | eval LOG_TIME=mvindex(tzSplit,0,0) 
            | bucket span=1d LOG_TIME 
            | stats count by LOG_TIME, event_api 
            | stats avg(count) AS AVG_TPS max(count) AS MAX_TPS by event_api 
            | eval "AVG_TPS"=round(AVG_TPS,2)'''
        ]

        all_results: List[Any] = []

        for query in queries:
            logging.info(f"Running query: {query[:60]}...")  # Log the first part of the query for clarity
            job: splunk_client.Job = service.jobs.create(
                query=query,
                earliest_time="-1h",  # Set the earliest time to 1 hour ago
                latest_time="now",    # Set the latest time to now
                output_mode="json"    # Return results in JSON format
            )

            # Wait for the search to complete
            while not job.is_done():
                logging.info(f"Waiting for job {job['sid']} to complete...")
                time.sleep(10)  # Poll every 10 seconds

            logging.info(f"Job {job['sid']} completed, fetching results...")

            # Get the results
            results: splunk_client.ResultsReader = splunk_results.ResultsReader(job.results())
            parsed_results: List[Dict[str, Any]] = []

            # Read the results
            for item in results:
                if isinstance(item, dict):
                    parsed_results.append(item)

            # Append the parsed results
            all_results.append(parsed_results)

        # Save all results to a JSON file
        with open('splunk_reports.json', 'w') as json_file:
            json.dump(all_results, json_file, indent=4)

        logging.info("✅ Splunk data fetched and saved to splunk_reports.json")

    except Exception as e:
        logging.error(f"❌ Error fetching Splunk data: {e}")
        logging.debug(traceback.format_exc())

# Function to connect to Splunk
def connect_splunk() -> Optional[splunk_client.Service]:
    try:
        HOST: str = 'localhost'
        PORT: int = 9011
        TOKEN: str = "eyJraWQiOiJzcGx1bmsuc2VjcmV0IiwiYWxnIjoiSFM1MTIiLCJ2ZXIiOiJ2MiIsInR0eXAiOiJzdGF0aWMifQ.eyJpc3MiOiJmZW5nLndhbmcyQHRlbHVzLmNvbSBmcm9tIGF2czY4LXByZXByLW1vbml0b3Jpbmctc2gtb3BzLTAwMyIsInN1YiI6Im9sbGllLmZpZ3Vlcm9hQHRlbHVzLmNvbSIsImF1ZCI6IkxvYWQgVGVzdCBSZXBvcnRzIiwiaWRwIjoiU3BsdW5rIiwianRpIjoiMjU3OTUzZjllOTIwNmM2NjA5ZDIwY2E2MWJmOTNhY2FlNWQ4OTgwNWI3NTA1OWE5ODI5ODZiZTY0M2Y4NjcwYSIsImlhdCI6MTcyODMzOTgyNywiZXhwIjoxNzkwODM4MDAwLCJuYnIiOjE3MjgzMzk4Mjd9.ZD8Ew7BJ4yTy-kvrgjD2Vc1ZtH-K0-9HNK66838px0XrjAKQD7QNhm3WzTbyERNSRYF7ZQxnpCErOCzha3FvGA"  # Token
        
        service: splunk_client.Service = splunk_client.connect(
            host=HOST,
            port=PORT,
            splunkToken=TOKEN,
            autologin=True
        )
        logging.info("✅ Connected to Splunk")
        return service
    except Exception as e:
        logging.error(f"❌ Error connecting to Splunk: {e}")
        logging.debug(traceback.format_exc())
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("✨ Starting Report Fetching Process ✨")
    
    # Fetch Grafana Reports
    #fetch_grafana_reports()

    # Fetch Splunk Data
    fetch_splunk_data()

    locust_test_and_locust_test_percentiles: Any = load_json('grafana_reports.json')
    splunk_data: list = load_json('splunk_reports.json')
    
    # Generate HTML content from Splunk data
    splunk_html_content: str = ""
    splunk_html_content += generate_first_splunk_html_table(splunk_data[0])
    splunk_html_content += generate_second_splunk_html_table(splunk_data[1])

    save_html_to_file('grafana_report_preview.html', splunk_html_content)

    logging.info("🎉 Report Fetching Process Completed!")