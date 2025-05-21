# Gingr to QuickBooks Online Converter

A simple tool to convert Gingr exports into a format suitable for QuickBooks Online import.

## Description

This application allows users to:
1. Upload Excel files exported from Gingr (a pet service management platform)
2. Process and transform the data to match QuickBooks Online import format
3. Download the processed file, ready for import into QuickBooks Online

## Features

- Handles both Invoices and Payments sheets
- Correctly formats dates for QBO compatibility
- Properly categorizes taxable and non-taxable items
- Sets appropriate deposit accounts based on payment methods
- Maintains data totals and integrity throughout the conversion
- Streamlit interface for easy use

## Requirements

- Python 3.8+
- Streamlit
- Pandas
- XlsxWriter

## Installation

```bash
# Clone the repository
git clone https://github.com/t0nebone/gingrtoqbo.git
cd gingrtoqbo

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the Streamlit app
streamlit run gingrtoqbo.py
```

Then open your web browser to http://localhost:8501

1. Click "Browse files" to upload your Gingr Excel export file
2. The app will process the file automatically
3. Click "Download Processed Excel" to save the QuickBooks-ready file

## Input File Format

The tool expects an Excel file with two sheets:
1. First sheet: Invoices with columns for Transaction ID, Location, Date, Owner, etc.
2. Second sheet: Payments with columns for Payment ID, Invoice ID, Owner, etc.

## Output Format

The tool produces an Excel file with two sheets:
1. "Invoices" sheet formatted for QBO import
2. "Payments" sheet formatted for QBO import

## License

This project is licensed under the MIT License - see the LICENSE file for details.