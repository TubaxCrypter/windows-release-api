from flask import Flask
import requests
from bs4 import BeautifulSoup
import re
import json
import os

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

@app.route("/")
def home():
    return "Up"

@app.route("/windows.json")
def parser():
    WIN_11_URL = 'https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information'
    WIN_10_URL = 'https://learn.microsoft.com/en-us/windows/release-health/release-information'
    win_11 = parse(WIN_11_URL, 'Windows 11')
    win_10 = parse(WIN_10_URL, 'Windows 10')
    return [win_11, win_10]

def parse(uri, windows_name, num_skipped_table = 0):
    result = {'windowsName': windows_name, 'releaseInformationURL': uri}
    request = requests.get(uri)
    versions = parse_versions(request.text, num_skipped_table)
    result['versions'] = versions
    return result

def parse_versions(text, num_skipped_table):
    versions = []
    soup = BeautifulSoup(text, 'html.parser')
    
    for table in soup.find_all('table'):
        # Find the nearest previous Version header
        version_txt = None
        build_txt = None
        
        # Search backwards through previous siblings and ancestors for the version info
        for prev in table.find_all_previous(['strong', 'summary', 'h2', 'h3', 'p', 'b']):
            content = prev.get_text(strip=True)
            # Match "Version XXX (OS build YYY)"
            res = re.search(r"Version (\S+).*\(OS build (\d+)\)", content)
            if res:
                version_txt = res.group(1)
                build_txt = res.group(2)
                break
        
        # If no version info found, skip this table (it's likely a summary or general info table)
        if not version_txt:
            continue
            
        version_dict = {"versionName": version_txt, "osBuild": build_txt}
        builds = []
        
        # Parse table rows, skipping the header row
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) < 4:
                continue
                
            build = {
                'servicingOption': cols[0].get_text(strip=True),
                'availabilityDate': cols[1].get_text(strip=True),
                'build': cols[2].get_text(strip=True),
                'kb': cols[3].get_text(strip=True)
            }
            builds.append(build)
            
        version_dict['builds'] = builds
        versions.append(version_dict)
        
    return versions

def save_json():
    print("Fetching Windows release information...")
    WIN_11_URL = 'https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information'
    WIN_10_URL = 'https://learn.microsoft.com/en-us/windows/release-health/release-information'
    
    win_11 = parse(WIN_11_URL, 'Windows 11')
    win_10 = parse(WIN_10_URL, 'Windows 10')
    
    data = [win_11, win_10]
    
    filename = "windows.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Success! Data saved to {os.path.abspath(filename)}")

if __name__ == '__main__':
    # Save the file immediately
    save_json()
    
    # Start Flask server for API access
    print("\nStarting Flask server for API access...")
    app.run(debug=True, port=5001)