import ftplib
import sqlite3
import csv
from datetime import datetime
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from sheets import get_credentials
from pprint import pprint
import locale
import requests
import hashlib

#import facebook

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

# Some crap to make Google Sheets work
try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets-api-credentials.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'  # .readonly
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Midway Ford Competitor Pricing'


def createFacebookTable(table_name):
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    query = 'CREATE TABLE IF NOT EXISTS {} ( id INTEGER UNIQUE, title TEXT, description TEXT, product_type TEXT, link TEXT, image_link TEXT, condition TEXT, availability TEXT, price TEXT, sale_price TEXT, sale_price_effective_date TEXT, brand TEXT, color TEXT, size TEXT, google_product_category TEXT, item_group_id TEXT, additional_image_link TEXT, custom_label_0 TEXT)'.format(table_name)
    c.execute(query)
    conn.commit()
    conn.close()


def update_facebook_inventory_table():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    c.execute('SELECT vin, stock, invType, year, make, model, vehTrim, intMSRP, intPrice, vdp_url, imageUrls, imageUrlsHD, exteriorColor, rebateExpiration, description, bodyStyle, style, drive, engine, highlights, miles '
              'FROM masterInventory')
    results = c.fetchall()

    updatedVinList = []

    for r in results:
        vin = r[0]
        stock = r[1]
        inv_type = r[2]
        year = r[3]
        make = r[4]
        model = r[5]
        veh_trim = r[6]
        msrp = r[7]
        price = r[8]
        vdp_url = r[9]
        image_urls = r[10]
        image_urls_hd = r[11]
        color = r[12]
        finance_expiration = r[13]
        description = r[14]
        body_style = r[15]
        style = r[16]
        drive = r[17]
        engine = r[18]
        highlights = r[19]
        miles = r[20]

        if price == 0:
            price = msrp

        # Use small pic if that's all that's available. use hd if possible.
        if image_urls_hd:
            image_link = image_urls_hd
        elif image_urls:
            image_link = image_urls.split(',')[0]
        else:
            continue

        title = '{} {} {} {} - {}'\
            .format(str(year), make, model, veh_trim, locale.currency(price, grouping=True).replace('.00', ''))
        print('title:', title)

        msrp = str(msrp) + ' USD'
        price = str(price) + ' USD'
        availability = 'In Stock'
        google_product_category = 'Vehicles & Parts > Vehicles > Motor Vehicles > Cars, Trucks & Vans'

        # Set sale_price_effective_date
        d = datetime.today()
        sale_start = str(d.year) + '-' + str(d.month) + '-' + str(d.day) + 'T9:00-05:00'
        if not finance_expiration or finance_expiration == 'None':
            sale_price_effective_date = None
        else:
            finance_expiration = finance_expiration.replace('/', '-')
            sale_end = '{}T20:00-5:00'.format(finance_expiration)
            # rebateYear = finance_expiration.split('/')[0]
            # rebateMonth = finance_expiration.split('/')[1]
            # rebateDay = finance_expiration.split('/')[2]
            # saleEnd = rebateYear + '-' + rebateMonth + '-' + rebateDay + 'T20:00-5:00'
            sale_price_effective_date = sale_start + '/' + sale_end

        # Make description
        description = highlights.replace(',', ', ') + ' - Stock #' + stock
        description = description.replace('0, 0', '0,0')  # fix for 100,000-mile warranty
        if inv_type == 'Used':  # Add mileage if vehicle is used
            miles = locale.format('%d', miles, grouping=True)
            description = miles + ' miles - ' + description

        # print(imageUrl)
        # print(type(imageUrl))
        # Skip if missing required fields
        if not image_link or not description:
            pass

        query = 'INSERT OR REPLACE INTO facebookInventory (id, title, ios_url, android_url, windows_phone_url, description, product_type, link, image_link, condition, availability, price, sale_price, sale_price_effective_date, brand, color, google_product_category, custom_label_0, size, item_group_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        to_db = (vin, title, None, None, None, description, body_style, vdp_url, image_link, inv_type, availability, msrp, price, sale_price_effective_date, make, color, google_product_category, stock, style, title)
        c.execute(query, to_db)

    # Delete old vins from facebookInventory table
    count = 0
    c.execute('SELECT id FROM facebookInventory')
    fb_vin_list = c.fetchall()
    c.execute('SELECT vin FROM masterInventory')
    master_vin_list = c.fetchall()
    for fb_vin in fb_vin_list:
        if fb_vin not in master_vin_list:
            c.execute('DELETE FROM facebookInventory WHERE id = ?', fb_vin)
            count += 1
    print(str(count) + ' vehicle deleted from facebookInventory table.')
    conn.commit()
    conn.close()


def update_facebook_inventory_file():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    c.execute('SELECT * FROM facebookInventory')

    with open('data/facebook-inventory-feed.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0] for i in c.description])  # write headers
        csv_writer.writerows(c)

    conn.commit()
    conn.close()


def upload_facebook_inventory_feed():
    print('\nUploading inventory to FTP server at spencertichenor.com for Facebook...')
    file_path = 'data/facebook-inventory-feed.csv'
    file_name = file_path.split('/')
    file_name = file_name[-1]
    print('Uploading ' + file_name + ' to FTP server...\n')
    file = open(file_path, 'rb')
    ftp = ftplib.FTP('spencertichenor.com')
    ftp.login('ftpbot@spencertichenor.com', 'M4lonePovolny')
    ftp.storbinary('STOR ' + file_name, file, 1024)
    file.close()
    ftp.quit()
    print('Successfully uploaded ' + file_name + ' to homenet folder on FTP server.\n')


def upload_file_to_ftp(file_path):
    print('\nUploading file to FTP server at spencertichenor.com...')
    print('File path:', file_path)

    #file_path = 'data/facebook-inventory-feed.csv'
    file_name = file_path.split('/')
    file_name = file_name[-1]
    print('Uploading ' + file_name + ' to FTP server...\n')
    file = open(file_path, 'rb')
    ftp = ftplib.FTP('spencertichenor.com')
    ftp.login('ftpbot@spencertichenor.com', 'M4lonePovolny')
    ftp.storbinary('STOR ' + file_name, file, 1024)
    file.close()
    ftp.quit()
    print('Successfully uploaded ' + file_name + ' to homenet folder on FTP server.\n')


def set_link(body_style):

    link = 'http://rosevillemidwayford.com/sales-specials'
    if 'Car' in body_style:
        link = 'https://www.rosevillemidwayford.com/Specials_D?model=Focus%2CMustang%2CTaurus%2CFiesta%2CFusion'
    elif 'Truck' in body_style:
        link = 'https://www.rosevillemidwayford.com/Specials_D?model=Super%20Duty%20F-350%20SRW%2CSuper%20Duty%20F-450%20DRW%2CF-150%2CSuper%20Duty%20F-250%20SRW'
    elif 'Van' in body_style:
        link = 'https://www.rosevillemidwayford.com/Specials_D?model=E-Series%20Cutaway%2CTransit%20Connect%20Van%2CTransit%20Van'
    elif 'SUV' in body_style:
        link = 'https://www.rosevillemidwayford.com/Specials_D?model=EcoSport%2CEdge%2CEscape%2CExpedition%20Max%2CExplorer%2CFlex'
    return link


def update_facebook_sales_specials_table():
    # Establish connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    query = 'DELETE FROM facebookSalesSpecials'
    c.execute(query)

    query = 'SELECT * FROM salesSpecials'
    c.execute(query)
    results = c.fetchall()

    to_db = []
    for r in results:
        print(r)
        id = r[0]
        special_type = r[1]
        year = r[2]
        make = r[3]
        model = r[4]
        veh_trim = r[5]
        drive = r[6]
        engine = r[7]
        cab_style = r[8]
        option_codes = r[9]
        msrp = r[10]
        sale_price = r[11]
        monthly_payment = r[12]
        term_length = r[13]
        apr = r[14]
        rebates = r[15]
        due_at_signing = r[16]
        down_payment = r[17]
        expiration = r[18]
        price_before_rebates = r[19]

        # Reformat expiration
        print('EXPIRATION:', expiration)
        expiration = expiration.split('/')
        expiration = '{}/{}/{}'.format(expiration[1], expiration[2], expiration[0])
        print('EXPIRATION after:', expiration)

        # Try to get vehicle with matching msrp
        if special_type == 'lease' or (special_type == 'finance' and monthly_payment):
            int_msrp = int(msrp.replace('$', '').replace(',', ''))
            query = 'SELECT imageUrls, imageUrlsHD, exteriorColor, stock, highlights, bodyStyle FROM masterInventory WHERE model = ? AND intMSRP = ? AND invType = ?'
            to_dbb = (model, int_msrp, 'New')  # to_dbb because db is taken
            c.execute(query, to_dbb)
            results = c.fetchall()
            if not results:
                # print('not results:', results)
                # Get lower priced vehicle if no matches
                query = 'SELECT imageUrls, imageUrlsHD, exteriorColor, stock, highlights, bodyStyle, max(intMSRP) FROM masterInventory WHERE model = ? AND intMSRP < ? AND invType = ?'
                to_dbb = (model, int_msrp, 'New')
                c.execute(query, to_dbb)
                results = c.fetchall()
        elif special_type == 'finance' and not monthly_payment:
            # Try to get vehicle with matching
            if engine and veh_trim and cab_style:  # NEED TO ADD FOR FACT CODES
                print('Specified engine and trim and cab_style.')
                engine = '%{}%'.format(engine)
                query = 'SELECT imageUrls, imageUrlsHD, exteriorColor, stock, highlights, bodyStyle, max(intTotalDiscount), max(intMSRP) FROM masterInventory WHERE invType = ? AND model = ? AND vehTrim = ? AND engine LIKE ? AND style LIKE ? AND imageUrlsHD != ?'
                to_dbb = ('New', model, veh_trim, engine, cab_style, '')  # to_dbb because db is taken
                c.execute(query, to_dbb)
                results = c.fetchall()
            elif engine and veh_trim:  # NEED TO ADD FOR FACT CODES
                print('Specified Engine and trim.')
                engine = '%{}%'.format(engine)
                query = 'SELECT imageUrls, imageUrlsHD, exteriorColor, stock, highlights, bodyStyle, max(intTotalDiscount)e, max(intMSRP) FROM masterInventory WHERE invType = ? AND model = ? AND vehTrim = ? AND engine LIKE ? AND imageUrlsHD != ?'
                to_dbb = ('New', model, veh_trim, engine, '')
                c.execute(query, to_dbb)
                results = c.fetchall()
            elif engine:
                print('Specified engine.')
                engine = '%{}%'.format(engine)
                query = 'SELECT imageUrls, imageUrlsHD, exteriorColor, stock, highlights, bodyStyle, max(intTotalDiscount), max(intMSRP) FROM masterInventory WHERE invType = ? AND model = ? AND engine LIKE ? AND imageUrlsHD != ?'
                to_dbb = ('New', model, engine, '')
                c.execute(query, to_dbb)
                results = c.fetchall()
            elif veh_trim:
                print('Specified trim.')
                query = 'SELECT imageUrls, imageUrlsHD, exteriorColor, stock, highlights, bodyStyle, max(intTotalDiscount), max(intMSRP) FROM masterInventory WHERE invType = ? AND model = ? AND vehTrim = ? AND imageUrlsHD != ?'
                to_dbb = ('New', model, veh_trim, '')
                c.execute(query, to_dbb)
                results = c.fetchall()
            else:
                query = 'SELECT imageUrls, imageUrlsHD, exteriorColor, stock, highlights, bodyStyle, max(intTotalDiscount), max(intMSRP) FROM masterInventory WHERE invType = ? AND model = ? AND imageUrlsHD != ?'
                to_dbb = ('New', model, '')
                c.execute(query, to_dbb)
                results = c.fetchall()
        results = results[0]
        image_urls = results[0]
        hd_image_url = results[1]
        color = results[2]
        stock = results[3]
        # highlights = results[4].replace(',', ', ')
        body_style = results[5]

        if not stock:
            continue

        # if not results[0][3]:  # for some reason this returns [(None, None, None, None, None, None)] when it's empty. maybe cuz of max msrp
        #     continue

        # print('results:', results)
        # if len(results) > 1:
        # print('results1', results)
        results = results[0]
        # print('results2', results)

        # Set image_link
        if hd_image_url:
            image_link = hd_image_url
        elif image_urls:
            image_link = image_urls.split(',')[0]
        else:
            continue

        # Set title and description and custom label
        title = ''
        if special_type == 'lease':
            title = '{} {} {} {} - Lease for {}/mo for {} months with {} down'.format(year, make, model, veh_trim, monthly_payment, term_length, due_at_signing)
        elif special_type == 'finance' and monthly_payment:
            print(monthly_payment)
            print(type(monthly_payment))
            if veh_trim and cab_style:
                title = '{} {} {} {} {} - Finance for {}/mo for {} months with {} down'.format(year, make, model, veh_trim, cab_style, monthly_payment, term_length, down_payment)
            elif veh_trim:
                title = '{} {} {} {} - Finance for {}/mo for {} months with {} down'.format(year, make, model, veh_trim, monthly_payment, term_length, down_payment)
            else:
                title = '{} {} {} - Finance for {}/mo for {} months with {} down'.format(year, make, model, monthly_payment, term_length, down_payment)
        elif special_type == 'finance' and not monthly_payment:
            if veh_trim and cab_style:
                title = '{} {} {} {} {} - {} APR with {} in rebates'.format(year, make, model, veh_trim, cab_style, apr, rebates)
            elif veh_trim:
                title = '{} {} {} {} - {} APR with {} in rebates'.format(year, make, model, veh_trim, apr, rebates)
            else:
                title = '{} {} {} - {} APR with {} in rebates'.format(year, make, model, apr, rebates)
        description = 'Visit our website to build your own deal with current rates and discounts from Midway Ford.'
        custom_label_0 = 'Offer expires {}'.format(expiration)

        # Set prices
        if monthly_payment:
            price = monthly_payment.replace('$', '') + '.00 USD'
        elif sale_price:
            price = '{}.00 USD'.format(sale_price)
        else:
            continue

        google_product_category = 'Vehicles & Parts > Vehicles > Motor Vehicles > Cars, Trucks & Vans'

        # link = set_link(body_style)
        link = 'https://rosevillemidwayford.com/sales-specials'

        to_db.append((stock, title, description, body_style, link, image_link, 'new', 'in stock', price, make, color, google_product_category, None, stock, None, custom_label_0))

    # print('to_db:', to_db)
    query = ('INSERT OR REPLACE INTO facebookSalesSpecials '
             '(id, title, description, product_type, link, image_link, condition, availability, price, brand, color, google_product_category, size, item_group_id, additional_image_link, custom_label_0) '
             'VALUES '
             '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    c.executemany(query, to_db)
    conn.commit()
    conn.close()


def update_facebook_sales_specials_file():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    c.execute('SELECT * FROM facebookSalesSpecials')

    with open('data/facebook-sales-specials-feed.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0] for i in c.description])  # write headers
        csv_writer.writerows(c)

    conn.commit()
    conn.close()


def table_to_csv(db_file_path, table_name, csv_file_path):
    conn = sqlite3.connect(db_file_path)
    c = conn.cursor()

    query = 'SELECT * FROM {}'.format(table_name)
    c.execute(query)

    with open(csv_file_path, 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0] for i in c.description])  # write headers
        csv_writer.writerows(c)

    conn.commit()
    conn.close()


def upload_facebook_sales_specials_feed():
    print('\nUploading sales specials to FTP server at spencertichenor.com for Facebook...')
    file_path = 'data/facebook-sales-specials-feed.csv'
    file_name = file_path.split('/')
    file_name = file_name[-1]
    print('Uploading ' + file_name + ' to FTP server...\n')
    file = open(file_path, 'rb')
    ftp = ftplib.FTP('spencertichenor.com')
    ftp.login('ftpbot@spencertichenor.com', 'M4lonePovolny')
    ftp.storbinary('STOR ' + file_name, file, 1024)
    file.close()
    ftp.quit()
    print('Successfully uploaded ' + file_name + ' to homenet folder on FTP server.\n')


def main():
    createFacebookTable('facebookSalesSpecials')

    update_facebook_inventory_table()
    table_to_csv('data/inventory.db', 'facebookInventory', 'data/facebook-inventory-feed.csv')
    upload_file_to_ftp('data/facebook-inventory-feed.csv')

    update_facebook_sales_specials_table()
    table_to_csv('data/inventory.db', 'facebookSalesSpecials', 'data/facebook-sales-specials-feed.csv')
    upload_file_to_ftp('data/facebook-sales-specials-feed.csv')


if __name__ == '__main__':
    main()



