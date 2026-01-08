#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://localhost:5001/api"

def test_reports_list():
    print("Testing /api/reports...")
    try:
        response = requests.get(f"{BASE_URL}/reports")
        if response.status_code == 200:
            reports = response.json()
            print(f"✓ Found {len(reports)} reports")
            for report in reports[:2]:  # Show first 2
                print(f"  - {report['code']} ({report.get('name', 'No name')})")
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Connection error: {e}")

def test_report_summary():
    print("\nTesting /api/reports/{{id}}/summary...")
    try:
        # First get reports
        response = requests.get(f"{BASE_URL}/reports")
        if response.status_code == 200:
            reports = response.json()
            if reports:
                report_id = reports[0]['id']
                print(f"Testing with report: {report_id}")
                
                summary_response = requests.get(f"{BASE_URL}/reports/{report_id}/summary")
                if summary_response.status_code == 200:
                    summary = summary_response.json()
                    print("✓ Summary fields:")
                    important_fields = ['stock_name', 'industry', 'pe_ttm', 'roe', 'gross_margin', 'net_margin', 'debt_ratio']
                    for field in important_fields:
                        value = summary.get(field)
                        print(f"  - {field}: {value}")
                else:
                    print(f"✗ Error: {summary_response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("BlackOil Platform API Test")
    print("=" * 40)
    test_reports_list()
    time.sleep(1)
    test_report_summary()
