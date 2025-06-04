#!/usr/bin/env python
# coding: utf-8
# Gingr to QBO w/ streamlit
# Todo: Have user select document from finder/explorer window

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import pandas.tseries.offsets as offsets

st.title("Excel Converter: Gingr to QBO Format")

# Upload Excel file
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    # Read the uploaded file as a DataFrame
    df1 = pd.read_excel(uploaded_file, sheet_name=0)  # Modify as needed based on your sheet names - this is set up for indexes
    df2 = pd.read_excel(uploaded_file, sheet_name=1)

    # Get totals from Invoices and store them, then remove totals row

    # Clean the column headers by stripping any leading or trailing whitespace
    df1.columns = df1.columns.str.strip()

    # Find the row in df1 that contains 'Totals' in the 'Owner' column
    totals_row_df1 = df1[df1['Owner'].str.contains('Totals', case=False, na=False)]

    # If a totals row exists, extract its values into variables
    if not totals_row_df1.empty:
        totals_row = totals_row_df1.iloc[0]  # Get the first matching row

        # Assigning variables for each relevant column in the totals row
        exempt_charges = totals_row['Exempt Charges']
        taxable_charges = totals_row['Taxable Charges']
        tax_charged = totals_row['Tax Charged']
        total_charged = totals_row['Total Charged']

    # Remove the row containing 'Totals' from df1
    df1 = df1[~df1['Owner'].str.contains('Totals', case=False, na=False)]

    # Get totals from Payments and store total as variable
    # Clean the column headers by stripping any leading or trailing whitespace
    df2.columns = df2.columns.str.strip()
    # Calculate the sum of the 'Amount' column
    payment_totals = df2['Amount'].sum()

    # Get year from Invoice Opened Date

    # Extract the year from the 'Invoice Opened Date' column
    # Convert the column to datetime if it's not already
    try:
        df2['Invoice Opened Date'] = pd.to_datetime(df2['Invoice Opened Date']).dt.date
    except Exception as e:
        st.error(f"Error converting Invoice Opened Date: {e}")
        df2['Invoice Opened Date'] = pd.to_datetime(df2['Invoice Opened Date'])
    
    # Get the year from the first row of the 'Invoice Opened Date' column
    year = df2['Invoice Opened Date'].iloc[0].year

    # Invoices

    # Rename column headers and additional columns
    df1.columns = ['RefNumber', 'Location', 'TxnDate', 'Customer', 'LineAmount', 'Taxable Charges', 'TaxAmt', 'Total Charged']
    df1['LineTaxable'] = None
    df1['SalesTerm'] = None
    df1['LineItem'] = None

    # Clean up date and set format
    # Extract the MM/DD part using regex and create a complete date with a year placeholder
    try:
        # Extract date part and convert to datetime
        date_part = df1['TxnDate'].str.extract(r'(\d{1,2}/\d{1,2})')[0] + f'/{year}'
        df1['TxnDate'] = pd.to_datetime(date_part, format='%m/%d/%Y').dt.date
        
        # Convert the datetime object to the desired format M/DD/YYYY
        # Using %#m on Windows or %-m on Unix for month without leading zeros
        import platform
        if platform.system() == 'Windows':
            df1['TxnDate'] = df1['TxnDate'].apply(lambda x: x.strftime('%#m/%d/%Y'))
        else:
            df1['TxnDate'] = df1['TxnDate'].apply(lambda x: x.strftime('%-m/%d/%Y'))
    except Exception as e:
        st.error(f"Error formatting TxnDate: {e}")
        # Fallback to standard format if error occurs
        df1['TxnDate'] = pd.to_datetime(date_part, format='%m/%d/%Y').dt.strftime('%m/%d/%Y')

    # Remove all lines with 0 in the 'Total Charged'
    # Remove rows where 'Total Charged' is 0
    df1 = df1[df1['Total Charged'] != 0]

    # Set SalesTerm to Due on Receipt for all columns.
    # Insert "Due on Receipt" in the 'SalesTerm' column for all rows
    df1['SalesTerm'] = "Due on Receipt"

    # Ensure 'RefNumber' is treated as a string
    df1['RefNumber'] = df1['RefNumber'].astype(int).astype(str)

    # Any line with both Exempt Charge and Taxable Charge, create two lines for both of them with same invoice/RefNumber. 
    # - Make one line for LineAmount and update Col H total for that line
    # - The other line has the taxable charge and tax amount

    # Find rows with both 'LineAmount' (Exempt Charge) and 'Taxable Charges' present
    condition = (df1['LineAmount'] != 0) & (df1['Taxable Charges'] != 0)
    rows_to_split = df1[condition]

    # List to hold the new rows
    new_rows = []

    # Iterate through the rows that need to be split
    for index, row in rows_to_split.iterrows():
        # Create the first row for the exempt charge
        exempt_row = row.copy()
        exempt_row['Taxable Charges'] = 0
        exempt_row['TaxAmt'] = 0
        exempt_row['Total Charged'] = exempt_row['LineAmount']

        # Create the second row for the taxable charge, putting the taxable amount in 'LineAmount'
        taxable_row = row.copy()
        taxable_row['LineAmount'] = taxable_row['Taxable Charges']  # Move taxable charge to 'LineAmount'
        taxable_row['Taxable Charges'] = 0  # Set 'Taxable Charges' to 0
        taxable_row['Total Charged'] = taxable_row['LineAmount'] + taxable_row['TaxAmt']

        # Append the new rows to the list
        new_rows.append(exempt_row)
        new_rows.append(taxable_row)

    # Create a DataFrame from the new rows
    new_rows_df = pd.DataFrame(new_rows)

    # Remove the original rows with taxable charges and append the split rows.  Sort by RefNumber so that split rows are consecutive.
    # Remove the original rows that were split from df1
    df1 = df1.drop(rows_to_split.index)

    # Append the new rows to the original df1
    df1 = pd.concat([df1, new_rows_df], ignore_index=True)

    # Sort the DataFrame by 'RefNumber' to ensure the split rows are consecutive
    df1 = df1.sort_values(by='RefNumber').reset_index(drop=True)

    # Move value of any thing In TaxableCharges to LineAmount column
    # For any row with a value in the 'Taxable Charges' column, move that value to 'LineAmount' and set 'Taxable Charges' to 0
    df1.loc[df1['Taxable Charges'] > 0, 'LineAmount'] += df1['Taxable Charges']
    df1.loc[df1['Taxable Charges'] > 0, 'Taxable Charges'] = 0

    # Fill in LineTaxable -  NON for lines with TaxAmt == 0, TAX for those with TaxAmt  > 0
    # Loop through each row in the DataFrame and update the 'LineTaxable' column
    for index, row in df1.iterrows():
        if row['TaxAmt'] > 0:
            df1.at[index, 'LineTaxable'] = 'TAX'
        else:
            df1.at[index, 'LineTaxable'] = 'NON'

    # Fill in LineItem column: 'Sales' if NON-taxable or 'Sales of Product' if TAXable
    # Loop through each row in the DataFrame and update the 'LineItem' column based on 'LineTaxable'
    for index, row in df1.iterrows():
        if row['LineTaxable'] == 'NON':
            df1.at[index, 'LineItem'] = 'Sales'
        elif row['LineTaxable'] == 'TAX':
            df1.at[index, 'LineItem'] = 'Sales of Product'

    # Verify totals from original excel files match updated totals

    # # Perform checks
    # line_amount_check = df1['LineAmount'].sum() == (exempt_charges + taxable_charges)
    # tax_amt_check = df1['TaxAmt'].sum() == tax_charged
    # total_charged_check = df1['Total Charged'].sum() == total_charged

    # # Print the results of the checks
    # print("Line Amount Check:", line_amount_check)
    # print("Tax Amount Check:", tax_amt_check)
    # print("Total Charged Check:", total_charged)

    # # Additional print statements to see actual values if checks fail
    # if not line_amount_check:
    #     print("Actual Line Amount Sum:", df1['LineAmount'].sum(), "Expected:", exempt_charges + taxable_charges)
    # if not tax_amt_check:
    #     print("Actual Tax Amount Sum:", df1['TaxAmt'].sum(), "Expected:", tax_charged)
    # if not total_charged_check:
    #     print("Actual Total Charged Sum:", df1['Total Charged'].sum(), "Expected:", total_charged)

    # Remove the 'Location' column
    df1 = df1.drop(columns='Location')

    # Payments

    # Rename column headers and additional columns
    df2.columns = ['RefNumber', 'InvoiceApplyTo', 'Customer', 'Invoice Opened Date', 'TxnDate', 'PaymentMethod', 'LineAmount']
    df2['DepositToAccount'] = None

    # Remove ':' and name from RefNumber
    # Strip the names and keep only the reference number
    df2['RefNumber'] = df2['RefNumber'].str.split(':').str[0].str.strip()

    # Convert 'RefNumber' and 'InvoiceApplyTo' columns to strings
    df2['RefNumber'] = df2['RefNumber'].astype(str)
    df2['InvoiceApplyTo'] = df2['InvoiceApplyTo'].astype(str)

    # Convert Invoice Opened Date and TxnDate to M/DD/YYYY format
    try:
        # Convert the columns to datetime format first, keeping only the date part
        df2['Invoice Opened Date'] = pd.to_datetime(df2['Invoice Opened Date']).dt.date
        df2['TxnDate'] = pd.to_datetime(df2['TxnDate']).dt.date
        
        # Format the columns to 'M/DD/YYYY' - handle platform differences
        import platform
        if platform.system() == 'Windows':
            df2['Invoice Opened Date'] = df2['Invoice Opened Date'].apply(lambda x: x.strftime('%#m/%d/%Y'))
            df2['TxnDate'] = df2['TxnDate'].apply(lambda x: x.strftime('%#m/%d/%Y'))
        else:
            df2['Invoice Opened Date'] = df2['Invoice Opened Date'].apply(lambda x: x.strftime('%-m/%d/%Y'))
            df2['TxnDate'] = df2['TxnDate'].apply(lambda x: x.strftime('%-m/%d/%Y'))
    except Exception as e:
        st.error(f"Error formatting payment dates: {e}")
        # Fallback to standard format
        df2['Invoice Opened Date'] = pd.to_datetime(df2['Invoice Opened Date']).dt.strftime('%m/%d/%Y')
        df2['TxnDate'] = pd.to_datetime(df2['TxnDate']).dt.strftime('%m/%d/%Y')

    # Assign Undeposited funds or Petty Cash to DepositToAccount column
    # Update the 'DepositToAccount' column based on the conditions in 'PaymentMethod'
    df2['DepositToAccount'] = df2['PaymentMethod'].apply(
        lambda x: 'Petty Cash' if x == 'Cash' else 
                  'Undeposited funds' if x in ['Credit Card', 'Check'] else 
                  'Other'
    )

    # Save the updated Sheets to new excel file
    # Convert 'TxnDate' in df1 and relevant date columns in df2 to datetime format
    try:
        # Ensure dates are datetime objects for quarter/year extraction, but keep only date part
        df1['TxnDate'] = pd.to_datetime(df1['TxnDate']).dt.date
        df2['TxnDate'] = pd.to_datetime(df2['TxnDate']).dt.date
    except Exception as e:
        st.error(f"Error converting dates for file naming: {e}")
        # Fallback
        df1['TxnDate'] = pd.to_datetime(df1['TxnDate'])
        df2['TxnDate'] = pd.to_datetime(df2['TxnDate'])

    # Get the quarter and year from the first row of df1
    first_date = df1['TxnDate'].iloc[0]
    # Handle both date objects and strings
    if isinstance(first_date, str):
        try:
            first_date = pd.to_datetime(first_date).date()
        except:
            # If conversion fails, try to parse string directly
            pass
    
    # Extract month and year safely
    if hasattr(first_date, 'month'):
        quarter = (first_date.month - 1) // 3 + 1
        year = first_date.year
    else:
        # Default to current quarter/year if extraction fails
        current_date = datetime.now()
        quarter = (current_date.month - 1) // 3 + 1
        year = current_date.year

    # Define the filename using the quarter and year
    file_path = f'Q{quarter}-{year}-Invoices and Payments for Import.xlsx'

    # # Write both DataFrames to the same Excel file
    # with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
    #     # Write df1 to the first worksheet named 'Invoices'
    #     df1.to_excel(writer, sheet_name='Invoices', index=False)
    #     # Write df2 to the second worksheet named 'Payments'
    #     df2.to_excel(writer, sheet_name='Payments', index=False)
        
    #     # Access the workbook and worksheets
    #     workbook = writer.book
    #     worksheet_invoices = writer.sheets['Invoices']
    #     worksheet_payments = writer.sheets['Payments']

    #     # Define the currency format
    #     currency_format = workbook.add_format({'num_format': '$#,##0.00'})

    #     # Apply the currency format to specific columns in 'Invoices'
    #     worksheet_invoices.set_column('D:D', None, currency_format)  # LineAmount
    #     worksheet_invoices.set_column('E:E', None, currency_format)  # Taxable Charges
    #     worksheet_invoices.set_column('F:F', None, currency_format)  # TaxAmt
    #     worksheet_invoices.set_column('G:G', None, currency_format)  # Total Charged

    #     # Apply the currency format to the 'LineAmount' column in 'Payments'
    #     worksheet_payments.set_column('G:G', None, currency_format)  # LineAmount

    # Create a buffer to save the processed Excel file
    output = io.BytesIO()
    
    # Remove the Taxable Charges column from invoices
    df1 = df1.drop(columns='Taxable Charges')
    
    # Ensure date columns are properly formatted before Excel export
    # This helps Excel recognize them as dates
    try:
        # Force TxnDate in df1 to be date strings in M/D/YYYY format
        if 'TxnDate' in df1.columns:
            df1['TxnDate'] = pd.to_datetime(df1['TxnDate']).dt.strftime('%m/%d/%Y')
            
        # Force date columns in df2 to be date strings in M/D/YYYY format
        if 'Invoice Opened Date' in df2.columns:
            df2['Invoice Opened Date'] = pd.to_datetime(df2['Invoice Opened Date']).dt.strftime('%m/%d/%Y')
        if 'TxnDate' in df2.columns:
            df2['TxnDate'] = pd.to_datetime(df2['TxnDate']).dt.strftime('%m/%d/%Y')
    except Exception as e:
        st.warning(f"Final date formatting warning: {e}")
        # Continue with existing format if conversion fails
    
    # Sort payments by RefNumber from smallest to largest
    df2 = df2.sort_values(by='RefNumber')
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df1.to_excel(writer, sheet_name='Invoices', index=False)
        df2.to_excel(writer, sheet_name='Payments', index=False)

        try:
            # Access the workbook and apply formatting if needed
            workbook = writer.book
            worksheet_invoices = writer.sheets['Invoices']
            worksheet_payments = writer.sheets['Payments']

            # Define the currency format
            currency_format = workbook.add_format({'num_format': '$#,##0.00'})

            # Apply currency formatting (update column ranges as needed)
            worksheet_invoices.set_column('D:D', None, currency_format)
            worksheet_invoices.set_column('E:E', None, currency_format)
            worksheet_invoices.set_column('F:F', None, currency_format)
            worksheet_invoices.set_column('G:G', None, currency_format)
            worksheet_payments.set_column('G:G', None, currency_format)
            
            # Create a robust date format that explicitly shows only the date
            # Using m/d/yyyy ensures consistent display across systems
            date_format = workbook.add_format({
                'num_format': 'm/d/yyyy',
                'align': 'center'
            })
            
            # Apply date formatting to date columns
            worksheet_invoices.set_column('C:C', 12, date_format)  # TxnDate
            worksheet_payments.set_column('D:D', 12, date_format)  # Invoice Opened Date
            worksheet_payments.set_column('E:E', 12, date_format)  # TxnDate
        
        except Exception as e:
            st.warning(f"Error applying Excel formatting: {e}")
            st.info("The file will still be generated, but some formatting may not be applied correctly.")

    # Save the Excel file and create a download button
    st.download_button(
        label="Download Processed Excel",
        data=output.getvalue(),
        file_name="Processed_File.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Please upload an Excel file to begin.")