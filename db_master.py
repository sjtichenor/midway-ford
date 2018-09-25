import sqlite3
import csv
import os
import glob
from datetime import datetime
from pprint import pprint


def remove_double_quotes(row):
    # Remove stupid quotes (no idea where they come from!)
    for key in row:
        if type(row[key]) is str:
            row[key] = row[key].replace('"', '')
    return row


def convert_to_lowercase(row):
    # Remove stupid quotes (no idea where they come from!)
    for key in row:
        if type(row[key]) is str:
            row[key] = row[key].lower()
    return row


def convert_email_to_list(email_string):
    if ';' in email_string:
        email_list = email_string.split(';')
    else:
        email_list = [email_string]
    for i, email in enumerate(email_list):
        # Skip shit emails
        if 'carcode' in email:
            continue
        email_list[i] = email.lower()
        if len(email_list) == 3:
            break
    while len(email_list) < 3:
        email_list.append('')
    return email_list


def string_to_number(num_string, data_type):
    num_string = num_string.replace(',', '').replace('$', '').replace('"', '').replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
    if data_type == 'int':
        return int(float(num_string))
    elif data_type == 'float':
        return float(num_string)
    elif data_type == 'str':
        return num_string


def clean_customer_row(row):
    row = remove_double_quotes(row)
    row = convert_to_lowercase(row)
    row['State'] = row['State'].strip()
    row['Email Address'] = convert_email_to_list(row['Email Address'])
    row['Home/Main Number'] = string_to_number(row['Home/Main Number'], 'str')
    row['Mobile Number'] = string_to_number(row['Mobile Number'], 'str')
    row['Work Number'] = string_to_number(row['Work Number'], 'str')
    if row['Insert Date']:
        try:
            row['Insert Date'] = datetime.strptime(row['Insert Date'], '%m/%d/%Y %H:%M:%S %p').strftime('%Y/%m/%d')
        except ValueError as e:
            print('Invalid insert date!')
            print('Error:', e)
            row['Insert Date'] = ''
    if row['Birthdate']:
        row['Birthdate'] = datetime.strptime(row['Birthdate'], '%m/%d/%Y %H:%M:%S %p').strftime('%Y/%m/%d')
    return row


def clean_vehicle_row(row):
    row = remove_double_quotes(row)
    row = convert_to_lowercase(row)
    if row['MSRP']:
        row['MSRP'] = string_to_number(row['MSRP'], 'int')
    if row['Year']:
        row['Year'] = string_to_number(row['Year'], 'int')
    # this is fucked. its insert date of customer. need fix.
    if row['Insert Date']:
        row['Insert Date'] = datetime.strptime(row['Insert Date'], '%m/%d/%Y %H:%M:%S %p').strftime('%Y/%m/%d')
    return row


def clean_sale_row(row):
    row = remove_double_quotes(row)
    row = convert_to_lowercase(row)
    row['Sale Price'] = string_to_number(row['Sale Price'], 'float')
    row['Gross Profit'] = string_to_number(row['Gross Profit'], 'float')
    if row['Gross Profit'] < 0:
        row['Gross Profit'] = 0
    row['Payment'] = string_to_number(row['Payment'], 'float')
    row['Warranty'] = string_to_number(row['Warranty'], 'float')
    if row['Finance Rate']:
        row['Finance Rate'] = string_to_number(row['Finance Rate'], 'float')
    if row['Purchase Date']:
        try:
            row['Purchase Date'] = datetime.strptime(row['Purchase Date'], '%m/%d/%Y %H:%M:%S %p').strftime('%Y/%m/%d')
        except ValueError as e:
            print('Invalid purchase date!')
            print('Error:', e)
            row['Purchase Date'] = ''
    if row['Lease Due Date']:
        row['Lease Due Date'] = datetime.strptime(row['Lease Due Date'], '%m/%d/%Y %H:%M:%S %p').strftime('%Y/%m/%d')
    if row['Finance Due Date']:
        try:
            row['Finance Due Date'] = datetime.strptime(row['Finance Due Date'], '%m/%d/%Y %H:%M:%S %p').strftime('%Y/%m/%d')
        except ValueError as e:
            print('ERROR:', e)
            row['Finance Due Date'] = ''
    else:
        row['Finance Due Date'] = ''
    return row


def clean_service_row(row):
    row = remove_double_quotes(row)
    row = convert_to_lowercase(row)
    row['DMS Deal/RO Number'] = int(row['DMS Deal/RO Number'])
    row['Service RO Total'] = string_to_number(row['Service RO Total'], 'float')
    row['Service Miles'] = string_to_number(row['Service Miles'], 'int')
    row['Service RO Close Date'] = datetime.strptime(row['Service RO Close Date'], '%b %d %Y %H:%M%p').strftime('%Y/%m/%d')
    return row


def create_tables():
    conn = sqlite3.connect('data/midway.db')
    c = conn.cursor()

    c.executescript("""
    DROP TABLE IF EXISTS Customer;
    DROP TABLE IF EXISTS Employee;
    DROP TABLE IF EXISTS Vehicle;
    DROP TABLE IF EXISTS Sale;
    DROP TABLE IF EXISTS Service;
    
    CREATE TABLE Customer (
      id  TEXT NOT NULL PRIMARY KEY UNIQUE,
      company TEXT,
      first_name TEXT,
      last_name TEXT,
      address1 TEXT,
      address2 TEXT,
      city TEXT,
      state TEXT,
      zip TEXT,
      home_phone TEXT,
      mobile_phone TEXT,
      work_phone TEXT,
      email1 TEXT,
      email2 TEXT,
      email3 TEXT,
      individual_type TEXT, 
      insert_date TEXT NOT NULL,
      birthdate TEXT
    );
    
    CREATE TABLE Employee (
      id  INTEGER NOT NULL PRIMARY KEY UNIQUE,
      first_name TEXT,
      last_name TEXT,
      email TEXT,
      address TEXT,
      city TEXT,
      state TEXT,
      zip TEXT,
      home_phone TEXT,
      mobile_phone TEXT,
      work_phone TEXT,
      birthdate TEXT,
      employee_type TEXT
    );
    
    CREATE TABLE Vehicle (
      id  TEXT NOT NULL PRIMARY KEY UNIQUE,
      stock TEXT,
      year INTEGER,
      make TEXT,
      model TEXT,
      trim TEXT,
      drive TEXT,
      msrp INTEGER,
      insert_date TEXT,
      customer_id TEXT NOT NULL UNIQUE
    );
    
    CREATE TABLE Sale (
      id  TEXT NOT NULL PRIMARY KEY UNIQUE,
      gross_profit INTEGER NOT NULL,
      purchase_date TEXT NOT NULL,
      sale_type TEXT,
      purchase_type TEXT,
      sale_price INTEGER,
      payment REAL,
      warranty INTEGER,
      finance_rate REAL,
      lease_due_date TEXT,
      finance_due_date TEXT,
      lender TEXT,
      employee_id INTEGER,
      vehicle_id TEXT NOT NULL 
    );
    
    CREATE TABLE Service (
      id INTEGER NOT NULL PRIMARY KEY UNIQUE,
      gross REAL,
      service_type TEXT,
      mileage INTEGER,
      service_date TEXT,
      vehicle_id TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def update_customer_table():

    # Get latest csv files from DealerSocket
    list_of_files = glob.glob('/Users/spencertichenor/PycharmProjects/midway/data/ds_service/*.csv')
    latest_service_file = max(list_of_files, key=os.path.getctime)
    list_of_files = glob.glob('/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/*.csv')
    latest_sales_file = max(list_of_files, key=os.path.getctime)
    #latest_service_file = '/Users/spencertichenor/PycharmProjects/midway/data/ds_service/all-service.csv'
    #latest_sales_file = '/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/all-sales.csv'

    # Connect to db
    conn = sqlite3.connect('data/midway.db')
    c = conn.cursor()
    to_db = []

    with open(latest_sales_file, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:
            row = clean_customer_row(row)
            customer_data = (
                row['Entity Id'],
                row['Company'],
                row['First Name'],
                row['Last Name'],
                row['Address 1'],
                row['Address 2'],
                row['City'],
                row['State'],
                row['Postal Code'],
                row['Home/Main Number'],
                row['Mobile Number'],
                row['Work Number'],
                row['Email Address'][0],
                row['Email Address'][1],
                row['Email Address'][2],
                row['Individual Type'],
                row['Insert Date'],
                row['Birthdate'],
            )
            to_db.append(customer_data)
            print(customer_data)

    with open(latest_service_file, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:
            row = clean_customer_row(row)
            customer_data = [
                row['Entity Id'],
                row['Company'],
                row['First Name'],
                row['Last Name'],
                row['Address 1'],
                row['Address 2'],
                row['City'],
                row['State'],
                row['Postal Code'],
                row['Home/Main Number'],
                row['Mobile Number'],
                row['Work Number'],
                row['Email Address'][0],
                row['Email Address'][1],
                row['Email Address'][2],
                row['Individual Type'],
                row['Insert Date'],
                row['Birthdate']
            ]
            to_db.append(customer_data)
            print(customer_data)

    query = ('INSERT OR REPLACE INTO Customer '
             '(id, company, first_name, last_name, address1, address2, city, state, zip, '
             'home_phone, mobile_phone, work_phone, email1, email2, email3, '
             'individual_type, insert_date, birthdate)'
             'VALUES '
             '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    c.executemany(query, to_db)
    conn.commit()
    conn.close()


def update_vehicle_table():

    # Get latest csv files from DealerSocket
    list_of_files = glob.glob('/Users/spencertichenor/PycharmProjects/midway/data/ds_service/*.csv')
    latest_service_file = max(list_of_files, key=os.path.getctime)
    list_of_files = glob.glob('/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/*.csv')
    latest_sales_file = max(list_of_files, key=os.path.getctime)
    #latest_service_file = '/Users/spencertichenor/PycharmProjects/midway/data/ds_service/all-service.csv'
    #latest_sales_file = '/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/all-sales.csv'

    # Connect to db
    conn = sqlite3.connect('data/midway.db')
    c = conn.cursor()
    to_db = []

    with open(latest_service_file, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:

            if not row['VIN']:
                continue

            row = clean_vehicle_row(row)

            vehicle_data = (
                row['VIN'],
                row['Stock Num'],
                row['Year'],
                row['Make'],
                row['Model'],
                row['Trim'],
                row['Drive'],
                row['MSRP'],
                row['Insert Date'],
                row['Entity Id']
            )
            to_db.append(vehicle_data)
            print(vehicle_data)

    with open(latest_sales_file, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:

            if not row['VIN']:
                continue

            row = clean_vehicle_row(row)

            vehicle_data = (
                row['VIN'],
                row['Stock Num'],
                row['Year'],
                row['Make'],
                row['Model'],
                row['Trim'],
                row['Drive'],
                row['MSRP'],
                row['Insert Date'],
                row['Entity Id']
            )
            to_db.append(vehicle_data)
            print(vehicle_data)

    query = ('INSERT OR REPLACE INTO Vehicle '
             '(id, stock, year, make, model, trim, drive, msrp, insert_date, '
             'customer_id) '
             'VALUES '
             '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    c.executemany(query, to_db)
    conn.commit()
    conn.close()


def update_sale_table():

    # Get latest sales csv file from DealerSocket
    list_of_files = glob.glob('/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    #latest_file = '/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/all-sales.csv'

    # Connect to db
    conn = sqlite3.connect('data/midway.db')
    c = conn.cursor()
    to_db = []

    with open(latest_file, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:

            if not row['DMS No']:
                continue

            row = clean_sale_row(row)
            sale_data = (
                row['DMS No'],
                row['Purchase Date'],
                row['Gross Profit'],
                row['Sales Type'],
                row['Purchase Type'],
                row['Sale Price'],
                row['Payment'],
                row['Warranty'],
                row['Finance Rate'],
                row['Lease Due Date'],
                row['Finance Due Date'],
                row['Lender'],
                row['Sales Rep'],
                row['VIN'],
            )
            to_db.append(sale_data)
            print(sale_data)

    query = ('INSERT OR REPLACE INTO Sale '
             '(id, purchase_date, gross_profit, sale_type, purchase_type, sale_price, payment, warranty, finance_rate, '
             'lease_due_date, finance_due_date, lender, employee_id, vehicle_id)'
             'VALUES '
             '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    c.executemany(query, to_db)
    conn.commit()
    conn.close()


def update_service_table():

    print('Updating "Service" table..')

    # Get latest service csv file from DealerSocket
    list_of_files = glob.glob('/Users/spencertichenor/PycharmProjects/midway/data/ds_service/*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    #latest_file = '/Users/spencertichenor/PycharmProjects/midway/data/ds_service/all-service.csv'

    # Connect to db
    conn = sqlite3.connect('data/midway.db')
    c = conn.cursor()
    to_db = []

    with open(latest_file, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:

            if not row['DMS Deal/RO Number']:
                print('skipping', row['DMS Deal/RO Number'])
                continue

            row = clean_service_row(row)
            service_data = (
                row['DMS Deal/RO Number'],
                row['Service RO Total'],
                row['Sales Type'],
                row['Service Miles'],
                row['Service RO Close Date'],
                row['VIN'],
            )
            to_db.append(service_data)
            print(service_data)

    query = ('INSERT OR REPLACE INTO Service '
             '(id, gross, service_type, mileage, service_date, vehicle_id) '
             'VALUES '
             '(?, ?, ?, ?, ?, ?)')
    c.executemany(query, to_db)
    conn.commit()
    conn.close()

    print('Finished updating "Service" table.')


def main():

    # create_tables()
    update_customer_table()
    update_vehicle_table()
    update_sale_table()
    update_service_table()


if __name__ == '__main__':
    main()
