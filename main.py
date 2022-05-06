import csv
import datetime
import json
import threading
import time
import traceback

import pandas as pd
import requests
import requests.exceptions

# Timeout for checking website. If website dont respont withing this time, its marked as close.
timeout = 15
# Headers for CSV
headers = ['URL', 'Status', 'Response Code', 'Comments', 'Time']
# Number of threads checking websites concurrently
thread_count = 10
semaphore = threading.Semaphore(thread_count)
# Lock for writing file
lock = threading.Lock()
# Print out errors if enabled for easier testing and debugging.
debug = True
# reads list of all closed keywords.
with open('CloseKeywords.txt') as kwfile:
    close_keywords = kwfile.read().splitlines()
with open('Websites.txt') as webfile:
    sites = webfile.read().splitlines()
with open('ResponseCodes.txt') as resfile:
    rescodes = resfile.read().splitlines()
# Enable or disable the testing.
test = False


def convert():
    try:
        print("Converting CSV to XLSX.")
        # Read the CSV file
        read_file = pd.read_csv(f"Report.csv", encoding='utf8', encoding_errors='ignore')
        # Write it into Excel file.
        read_file.to_excel(f"Report.xlsx", index=None, header=True)
        print(f"Report.xlsx")
    except:
        if debug:
            traceback.print_exc()

def check(url):
    # Semaphore for controlling number of parallel threads.
    with semaphore:
        comments = ""
        try:
            res = requests.get(url, timeout=timeout, headers={
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                              ' Chrome/101.0.4951.54 Safari/537.36',
            })
            if test:
                print(res.content)
            # If it's able to access the URL then its marked as working (Unless it has keyword from "closed.txt")
            work = True
            # Writes the redirect chain of url to comments, if it has any.
            if res != "" and res.history:
                comments = "->".join([f"{x.status_code} ({x.headers['Location']})" for x in res.history])
            # if it has any keyword from closed file, mark it as "closed". They are case insensitive (a == A)!
            for code in rescodes:
                if str(res.status_code).startswith(code):
                    work = False
                    break
            for kw in close_keywords:
                if kw.lower() in str(res.content).lower():
                    work = False
                    break
        except:
            # If the website don't exist or respond, it's marked as closed
            res = "No response"
            work = False
            if debug:
                traceback.print_exc()
        # JSON for row is created with all the details.
        row = {
            "URL": url,
            "Status": "Open" if work else "Closed",
            "Response Code": str(res),
            "Comments": f"Redirect {comments}" if comments != "" else "",
            'Time': str(datetime.datetime.now()).split('.')[0]
        }
        # The newly created JSON os written as row in CSV
        append(row)
        return row


def append(row):
    # Since the program is using threads, only 1 thread can write to file so it uses lock so only 1 thread is
    # accessing file at a time
    with lock:
        print(json.dumps(row, indent=4))
        with open(f'Report.csv', 'a', newline='', encoding='utf8', errors='ignore') as sfile:
            csv.DictWriter(sfile, fieldnames=headers).writerow(row)


def main():
    # Prints the header banner
    logo()
    threads = []
    # Create CSV file for report and write its headers (fieldnames)
    with open(f'Report.csv', 'w', newline='', encoding='utf8', errors='ignore') as sfile:
        csv.DictWriter(sfile, fieldnames=headers).writeheader()
    for line in sites:
        # Check if Entity URL is not empty so it wont waste time in processing nothing!
        if line != "":
            # Remove trailing spaces.
            # Add HTTP scheme if URL doesn't have one.
            url = line
            if not url.startswith("http"):
                url = f"http://{url}"
            # Spawn a thread to check the status of URL.
            thread = threading.Thread(target=check, args=(url,))
            # Add the thread to array of threads, so we will wait
            threads.append(thread)
            # Start processing the thread in "parallel"
            thread.start()
            time.sleep(0.01)
    # Wait for all threads to finish!!
    for thread in threads:
        thread.join()


def logo():
    print(r"""
      _  _  _____  _____  ___    ___  _              _             
     | || ||_   _||_   _|| _ \  / __|| |_   ___  __ | |__ ___  _ _ 
     | __ |  | |    | |  |  _/ | (__ | ' \ / -_)/ _|| / // -_)| '_|
     |_||_|  |_|    |_|  |_|    \___||_||_|\___|\__||_\_\\___||_|  
========================================================================
      Bulk HTTP code checker by https://github.com/evilgenius786
========================================================================
[+] Works without browser
[+] Detailed output CSV
[+] Logs redirect chain
[+] Multithreaded
[+] Proxy supported
[+] JSON/CSV/XLSX output
________________________________________________________________________
""")


if __name__ == '__main__':
    convert()
    # main()

    # print(json.dumps(check('http://big-sky-people.com'), indent=4))
