# make_test_file.py
# Creates a messy sample Excel (sample_dirty.xlsx) to test the cleaner pipeline.

import pandas as pd

rows = [
    {"Name": "Zaid Khan", "Email": "zaidkhan(at)gmail.com", "Join Date": "01/02/25", "Salary": "₹50,000", "Department": "sales", "Phone": " +91 98765 43210"},
    {"Name": "Ahmed", "Email": "ahmed123@gamil.com", "Join Date": "2025-2-1", "Salary": "45,000", "Department": "Sales ", "Phone": "9876543210"},
    {"Name": "Sarah", "Email": "sarah.k@ example.com", "Join Date": "Feb 2 2025", "Salary": "48 000", "Department": "marketing", "Phone": "(+91)9812345678"},
    {"Name": "zaid khan", "Email": "zaidkhan@gmail.com", "Join Date": "1 Feb 25", "Salary": "50000", "Department": "sales", "Phone": "9988776655"},
    {"Name": "Imran", "Email": "imran@taskmindai.r", "Join Date": "02-02-25", "Salary": "₹60,000", "Department": "Tech", "Phone": "0091-99999-99999"},
    {"Name": "John Doe", "Email": "", "Join Date": "", "Salary": "", "Department": "Unknown", "Phone": "12345678"},
]

df = pd.DataFrame(rows)

out = "sample_dirty.xlsx"
df.to_excel(out, index=False)
print(f"Sample test file written to: {out}")
