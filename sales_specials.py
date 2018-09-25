import sqlite3
import os
import csv
import datetime
import time
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from sheets import get_credentials
import httplib2
import smtplib
import os.path as op
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utilz import fire_up_chromedriver
import locale
locale.setlocale(locale.LC_ALL, 'en_US.utf8') #.utf8


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


def getUrlStatusCode(url):
    print('Testing Url:', url)
    http = httplib2.Http()
    response = http.request(uri=url, method='GET')
    print('Status Code:', response[0]['status'])
    return response[0]['status']


def createSalesSpecialsTable():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS salesSpecials (ID TEXT UNIQUE, special_type TEXT, year TEXT, make TEXT, model TEXT, veh_trim TEXT, drive TEXT, engine TEXT, cab_style TEXT, options TEXT, msrp TEXT, sale_price TEXT, monthly_payment TEXT, term_length TEXT, apr TEXT, rebates TEXT, due_at_signing TEXT, down_payment TEXT, expiration TEXT)')

    conn.commit()
    conn.close()


def updateSalesSpecialsTable():
    # Establish connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    query = 'DELETE FROM salesSpecials'
    c.execute(query)
    # query = 'SELECT id FROM facebookSalesSpecials'
    # original_specials = c.fetchall()
    # print(original_specials)

    # Get credentials to edit spreadsheet
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

    spreadsheet_id = '1SnW4R4vOTHu9nxMfByZLYuHUSVqXy9EwEyOWbxbkqHA'
    range_name = 'Lease!A1:P'
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result['values']

    special_id = 0

    if len(values) > 1:  # skip if no rows

        # Get lease specials from google sheet
        to_db = []
        for i, v in enumerate(values[1:]):
            creator = v[0]
            year = v[1]
            make = v[2]
            model = v[3]
            veh_trim = v[4]
            drive = v[5]
            engine = v[6]
            cab_style = v[7]
            options = v[8]
            msrp = v[9]
            sale_price = v[10]
            monthly_payment = v[11]
            term_length = v[12]
            due_at_signing = v[13]
            down_payment = v[14]
            expiration = v[15]

            special_id += 1

            # Add finance special to to_db
            to_db.append((special_id, 'lease', year, make, model, veh_trim, options, drive, engine, cab_style, msrp, sale_price, monthly_payment, term_length, due_at_signing, down_payment, expiration))


        query = ('INSERT OR REPLACE INTO salesSpecials '
                 '(ID, special_type, year, make, model, veh_trim, options, drive, engine, cab_style, msrp, sale_price, monthly_payment, term_length, due_at_signing, down_payment, expiration) '
                 'VALUES '
                 '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        c.executemany(query, to_db)
        conn.commit()

    # Get finance specials from google sheet
    to_db = []
    range_name = 'Finance!A1:M'
    results = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = results['values']
    if len(values) > 1:  # skip if no rows
        for j, v in enumerate(values[1:]):
            print('special:', v)
            creator = v[0]
            year = v[1]
            make = v[2]
            model = v[3]
            veh_trim = v[4]
            drive = v[5]
            engine = v[6]
            cab_style = v[7]
            options = v[8]
            apr = v[9]
            term_length = v[10]
            rebates = v[11]
            expiration = v[12]

            # Generate ID
            # special_id = i + j + 1
            special_id += 1

            to_db.append((special_id, 'finance', year, make, model, veh_trim, options, drive, engine, cab_style, apr, term_length, rebates, expiration))



        query = ('INSERT OR REPLACE INTO salesSpecials '
                 '(ID, special_type, year, make, model, veh_trim, options, drive, engine, cab_style, apr, term_length, rebates, expiration) '
                 'VALUES '
                 '( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        c.executemany(query, to_db)
        conn.commit()


    # Get lowest rates from inventory db
    c.execute('SELECT DISTINCT year FROM masterInventory')
    year_results = c.fetchall()
    for y in year_results:
        year = y[0]
        # print(year)
        query = 'SELECT DISTINCT model FROM masterInventory WHERE year = ? AND leasePayment != ?'
        to_db = (year, '')
        c.execute(query, to_db)
        model_results = c.fetchall()
        for m in model_results:
            model = m[0]

            # Get min lease payment
            query = 'SELECT min(leasePayment) FROM masterInventory WHERE year = ? AND model = ?'
            to_db = (year, model)
            c.execute(query, to_db)
            finance_payment_results = c.fetchall()
            min_lease_payment = finance_payment_results[0][0]

            if min_lease_payment:

                query = ('SELECT vin, stock, vehTrim, drive, cabStyle, intMSRP, intPrice, lease_due_at_signing, leaseRebateExpiration, intInternetPrice '
                         'FROM masterInventory '
                         'WHERE year = ? AND model = ? AND leasePayment = ?')
                to_db = (year, model, min_lease_payment)
                c.execute(query, to_db)
                lease_results = c.fetchall()
                v = lease_results[0]  # Just get first vehicle even if there are many
                print(v)
                vin = v[0]
                stock = v[1]
                veh_trim = v[2]
                drive = v[3]
                cab_style = v[4]
                msrp = v[5]
                price = v[6]
                lease_due_at_signing = v[7]
                lease_expiration = v[8]
                price_before_rebates = v[9]
                lease_term_length = 36

                special_id += 1

                # Reformat numbers
                msrp = locale.currency(msrp, grouping=True).replace('.00', '')
                price = locale.currency(price, grouping=True).replace('.00', '')
                min_lease_payment = locale.currency(min_lease_payment, grouping=True).replace('.00', '')
                lease_due_at_signing = locale.currency(lease_due_at_signing, grouping=True).replace('.00', '')

                to_db = (special_id, 'lease', year, make, model, veh_trim, drive, cab_style, msrp, price, min_lease_payment, lease_due_at_signing, lease_term_length, lease_expiration, price_before_rebates)
                query = ('INSERT OR REPLACE INTO salesSpecials '
                         '(ID, special_type, year, make, model, veh_trim, drive, cab_style, msrp, sale_price, monthly_payment, due_at_signing, term_length, expiration, price_before_rebates) '
                         'VALUES '
                         '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
                c.execute(query, to_db)
                print(to_db)
            else:
                print('Skipping min lease payment special because no lease payment data found.')

            # Get min finance payment
            query = ('SELECT min(finance_payment) '
                     'FROM masterInventory '
                     'WHERE year = ? AND model = ?')
            to_db_temp = (year, model)
            c.execute(query, to_db_temp)
            finance_payment_results = c.fetchall()
            min_finance_payment = finance_payment_results[0][0]

            # Skip if there are no monthly payments for this model year
            if min_finance_payment:
                query = ('SELECT vin, stock, vehTrim, drive, cabStyle, intMSRP, intPrice, finance_down_payment, finance_expiration, finance_apr, finance_term_length, intInternetPrice '
                         'FROM masterInventory '
                         'WHERE year = ? AND model = ? AND finance_payment = ?')
                to_db_temp = (year, model, min_finance_payment)
                print('to_db:', to_db_temp)
                c.execute(query, to_db_temp)
                finance_results = c.fetchall()
                v = finance_results[0]  # Just get first vehicle even if there are many
                vin = v[0]
                stock = v[1]
                veh_trim = v[2]
                drive = v[3]
                cab_style = v[4]
                msrp = v[5]
                price = v[6]
                finance_down_payment = v[7]
                finance_expiration = v[8]
                finance_apr = v[9]
                finance_term_length = v[10]
                price_before_rebates = v[11]

                # Reformat numbers
                msrp = locale.currency(msrp, grouping=True).replace('.00', '')
                price = locale.currency(price, grouping=True).replace('.00', '')
                min_finance_payment = locale.currency(min_finance_payment, grouping=True).replace('.00', '')
                finance_down_payment = locale.currency(finance_down_payment, grouping=True).replace('.00', '')
                finance_apr = str(finance_apr) + '%'

                special_id += 1

                to_db = (special_id, 'finance', year, make, model, veh_trim, drive, cab_style, msrp, price, min_finance_payment, finance_down_payment, finance_apr, finance_term_length, finance_expiration, price_before_rebates)
                query = ('INSERT OR REPLACE INTO salesSpecials '
                         '(ID, special_type, year, make, model, veh_trim, drive, cab_style, msrp, sale_price, monthly_payment, down_payment, apr, term_length, expiration, price_before_rebates) '
                         'VALUES '
                         '( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
                c.execute(query, to_db)
                print(to_db)
            else:
                print('Skipping min lease payment special because no lease payment data found.')

    # Close connection to db
    conn.commit()
    conn.close()


def generate_html():

    # Establish connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    body_html = '<div class="rm-sales-content-container"><div class="row"><div class="col-lg-12" style="margin-bottom: 20px;"><div id="rm-sales-specials-container">'

    # Buttons to filter All/Finance/Lease
    body_html += "<div class='clearfix' id='rm-offer-type-container'><button type='button' class='btn btn-primary btn-lg btn-block'>ALL</button><button type='button' class='btn btn-outline-primary btn-lg btn-block'>FINANCE</button><button type='button' class='btn btn-outline-primary btn-lg btn-block'>LEASE</button></div>"

    # Generate HTML for model selector
    body_html += '<div class="clearfix" id="rm-special-offer-model-list">'

    model_list = [
        'Fiesta',
        'Focus',
        'Fusion',
        'Taurus',
        'Mustang',
        'EcoSport',
        'Escape',
        'Edge',
        'Flex',
        'Explorer',
        'Expedition',
        'F-150',
        'Transit'
    ]

    for model in model_list:

        query = 'SELECT COUNT(*) FROM salesSpecials WHERE model = ?'
        to_db = (model,)
        c.execute(query, to_db)
        offer_count = c.fetchall()
        offer_count = offer_count[0][0]

        if offer_count:  # skip model if no specials offered

            # Get image url
            image_url = 'https://www.spencertichenor.com/images/sales-specials-page/2018-ford-{}-side-view.png'.format(model)
            image_url = image_url.lower().replace(' hybrid', '').replace('&nbsp;', '-').replace('t connect', 't-connect')
            print('after url:', image_url)

            # Check to make sure image url is good
            status_code = getUrlStatusCode(image_url)
            if status_code == '404' and '2019' in image_url:
                print('No image found for vehicle at url:', image_url)

                # Try previous year
                image_url = image_url.replace('2019', '2018')
                status_code = getUrlStatusCode(image_url)
                if status_code == '404':
                    print('No image found for vehicle at url for previous model year:', image_url)
                    continue

            elif status_code == '404' and '2018' in image_url:
                print('No image found for vehicle at url:', image_url)

                # Try previous year
                image_url = image_url.replace('2018', '2017')
                status_code = getUrlStatusCode(image_url)
                if status_code == '404':
                    print('No image found for vehicle at url for previous model year:', image_url)
                    continue

            body_html += '<div class="rm-model-selector-container clearfix"><div class="rm-model-name">{}</div><div class="rm-model-selector-image"><img src="{}" alt="Ford {} Side View"/></div><div class="rm-offer-count"><div>{} Offer(s)</div></div></div>'.format(model.upper(), image_url, model.title(), offer_count)
    body_html += '</div>'  # Close offer-model-list


    # Buttons to filter All/Finance/Lease
    #body_html += "<div class='clearfix' id='rm-offer-type-container'><button type='button' class='btn btn-primary btn-lg btn-block'>ALL</button><button type='button' class='btn btn-outline-primary btn-lg btn-block'>FINANCE</button><button type='button' class='btn btn-outline-primary btn-lg btn-block'>LEASE</button></div>"

    # Generate html for body

    body_html += '<div class="clearfix" id="rm-offer-container">'

    # Initialize variables
    previous_year = ''
    previous_model = ''
    model_count = 1
    image_number = 1


    for model in model_list:

        query = 'SELECT * FROM salesSpecials WHERE model = ? ORDER BY year, special_type, monthly_payment ASC'
        to_db = (model,)
        c.execute(query, to_db)
        results = c.fetchall()

        for i, r in enumerate(results):

            special_id = r[0]
            special_type = r[1]
            year = r[2]
            make = r[3]
            #model = r[4]
            veh_trim = r[5]
            drive = r[6]
            engine = r[7]
            cab_style = r[8]
            options = r[9]
            msrp = r[10]
            sale_price = r[11]
            monthly_payment = r[12]
            term_length = r[13]
            apr = r[14]
            rebates = r[15]
            due_at_signing = r[16]
            down_payment = r[17]
            expiration = r[18]

            # Skip special if no vehicles of this model year in stock
            query = 'SELECT COUNT(*) FROM masterInventory WHERE invType = "New" AND year = ? AND model LIKE ?'
            to_db = (year, model)
            c.execute(query, to_db)
            count_results = c.fetchall()
            print('count_results:', count_results)
            if count_results[0] == 0:
                continue

            # Reformat expiration
            if expiration:
                expiration = expiration.split('/')
                if len(expiration) == 3:
                    expiration = '{}/{}/{}'.format(expiration[1], expiration[2], expiration[0])
                elif len(expiration) == 2:
                    expiration = '{}/{}'.format(expiration[0], expiration[1])

            # Figure out what image to use
            if year == previous_year and model == previous_model:
                model_count += 1
                image_number += 1
            else:
                model_count = 1
                image_number = 1
                previous_year = year
                previous_model = model

            # Generate disclaimer text
            disclaimer = 'Must take new retail delivery from dealer stock by {}. Subject to credit approval.'.format(expiration)

            offer_html = '<div class="rm-sales-special-item rm-{}-special rm-{}-special"><div class="rm-special-style-info">'\
                .format(model.lower(), special_type)
            vehicle_pre = year + ' ' + make
            vehicle_model = model
            vehicle_post = ''
            if veh_trim == 'S' or veh_trim == 'Base':
                veh_trim = ''
            if veh_trim:
                vehicle_post += veh_trim
            if cab_style:
                vehicle_post += (' ' + cab_style)
            if drive and drive != 'FWD' and drive != 'RWD':
                if len(vehicle_post) > 0:
                    if len(vehicle_post + ' ' + drive) <= 35:  # +1 for the space
                        if len(vehicle_post) > 0:
                            vehicle_post += ' ' + drive
                else:
                    vehicle_post = drive
            if engine:
                if len(vehicle_post) > 0:
                    if len(vehicle_post + ', ' + engine + ' Engine') <= 35:
                        vehicle_post += ', ' + engine + ' Engine'
                else:
                    vehicle_post = engine + ' Engine'
            if vehicle_post == '':
                vehicle_post = '&nbsp;'

            offer_html += '<div class="vehicle-info"><div class="rm-vehicle-pre">{}</div><div class="rm-vehicle-model">{}</div><div class="rm-vehicle-post">{}</div></div>'.format(vehicle_pre, vehicle_model, vehicle_post)

            offer_html += '<div class="rm-special-text"><div class="rm-special-item">'
            if special_type == 'lease':
                disclaimer = 'Based on MSRP of {} and selling price of {}. Must take retail delivery by {}. '\
                    .format(msrp, sale_price, expiration)
                disclaimer += 'Monthly payment assumes {}-month lease, 10,500 miles/year, {} due at signing. Tax, title, and license not included. Some restrictions apply. Contact us for details.'\
                    .format(term_length, due_at_signing)
                offer_html += '<div class="rm-special-text-main"><span class="rm-special-top"><span class="rm-special-dollar">$</span>{}</span><span class="rm-lg-view"> per month</span><span class="rm-sm-view">/MO</span></div>'.format(monthly_payment.replace('$', ''))
                offer_html += '<div class="rm-special-text-sub">Lease for {} months</div>'.format(term_length)
                offer_html += '<div class="rm-special-text-post">{} due at signing</div>'.format(due_at_signing)
                offer_html += '<div class="rm-text-disclaimer"><span data-toggle="tooltip" data-title="{}" data-placement="auto bottom" data-trigger="hover"> Disclaimer </span></div>'.format(disclaimer)

                offer_description = '<strong>{} {} {}</strong><br>Lease for {}/mo for {} months with {} due at signing.'\
                    .format(year, make, model, monthly_payment, term_length, due_at_signing)

            elif special_type == 'finance':
                if monthly_payment:
                    offer_html += '<div class="rm-special-text-main"><span class="rm-special-top"><span class="rm-special-dollar">$</span>{}</span><span class="rm-lg-view"> per month</span><span class="rm-sm-view">/MO</span></div>'.format(monthly_payment.replace('$', ''))
                    offer_html += '<div class="rm-special-text-sub">Finance for {} months</div>'.format(term_length)
                    offer_html += '<div class="rm-special-text-post">{} down payment</div>'.format(down_payment)
                    offer_html += '<div class="rm-text-disclaimer"><span data-toggle="tooltip" data-title="{}" data-placement="auto bottom" data-trigger="hover"> Disclaimer </span></div>'.format(disclaimer)
                    offer_description = '<strong>{} {} {}</strong><br>Finance for {}/mo for {} months with {} down.' \
                        .format(year, make, model, monthly_payment, term_length, down_payment)
                elif apr:
                    offer_html += '<div class="rm-special-text-main"><span class="rm-special-top">{}<span class="rm-special-percentage">%</span></span><span> APR</span></div>'.format(apr.replace('%', '').replace('0.0', '0'))



                    # temporary
                    if model == 'F-150' and term_length == '72':
                        term_length = '{} months'.format(term_length)
                    else:
                        term_length = '24-{} months'.format(term_length)

                    offer_html += '<div class="rm-special-text-sub">For {}</div>'.format(term_length)
                    if rebates != '$0':
                        offer_html += '<div class="rm-special-text-post">PLUS {} Cash Back</div>'.format(rebates)
                    else:
                        offer_html += '<div class="rm-special-text-post">&nbsp;</div>'
                    offer_html += '<div class="rm-text-disclaimer"><span data-toggle="tooltip" data-title="{}" data-placement="auto bottom" data-trigger="hover"> Disclaimer </span></div>'.format(disclaimer)

                    offer_description = '<strong>{} {} {}</strong><br>Finance at {} APR for {}.' \
                        .format(year, make, model, apr, term_length, rebates)


            # Append trim if it exists
            if veh_trim:
                trim_str = ' {}</strong>'.format(veh_trim)
                offer_description = offer_description.replace('</strong>', trim_str)

            # Claim Offer and View Inventory Buttons
            offer_html += '<div class="rm-special-callouts"><table style="width: 100%;" border="0" cellspacing="0" cellpadding="0"><tbody><tr>'
            offer_html += '<td><a class="rm-input-button rm-input-gray smaller rm-view-inventory" href="https://www.rosevillemidwayford.com/VehicleSearchResults?search=new&make={}&model={}&sort=featuredPrice%7Casc">View Inventory</a></td>'\
                .format(make, model)

            offer_html += '<td><a class="popup-btn rm-input-button rm-input-gray smaller rm-claim-offer" href="#" data-inventory-type="new" data-year="{}" data-make="{}" data-model="{}" data-trim="{}" data-drive="{}" data-engine="{}" data-cab-style="{}" data-msrp="{}" data-sale-price="{}" data-purchase-type="{}" data-monthly-payment="{}" data-apr="{}" data-term-length="{}" data-down-payment="{}" data-due-at-signing="{}" data-rebate-amount="{}" data-expiration="{}" data-offer-description="{}"> Claim Offer </a></td>' \
                .format(year, make, model, veh_trim, drive, engine, cab_style, msrp, sale_price, special_type.title(), monthly_payment, apr, term_length, down_payment, due_at_signing, rebates, expiration, offer_description)
            offer_html += '</tr></tbody></table></div>'

            print('downpayment', down_payment)
            print('das', due_at_signing)

            offer_html += '</div></div></div>' #close special-text and special-item and special-style-info

            image_url = 'https://spencertichenor.com/images/sales-specials-page/{}-{}-{}-corner-view-{}.png'.format(year, make.lower(), model.lower(), image_number)
            image_url = image_url.replace(' hybrid', '').replace('&nbsp;', '-').replace('t connect', 't-connect')
            # Check to make sure image url is good
            status_code = getUrlStatusCode(image_url)
            if status_code == '404':
                print('No image found for vehicle at url:', image_url)
                if image_number > 1:
                    image_number = 1
                    image_url = 'https://www.spencertichenor.com/images/sales-specials-page/{}-{}-{}-corner-view-{}.png'.format(year, make.lower(), model.lower(), image_number)
                    status_code = getUrlStatusCode(image_url)
                    if status_code == '404':
                        print('No image found for vehicle at url:', image_url)
                        image_url = 'https://www.spencertichenor.com/images/sales-specials-page/{}-{}-{}-corner-view-{}.png'.format(int(year)-1, make.lower(), model.lower(), image_number)
                        status_code = getUrlStatusCode(image_url)
                        if status_code == '404':
                            print('No image found for vehicle at url:', image_url)
                            continue
                else:
                    if 'transit' in image_url:
                        print('testing transit')
                        image_url = image_url.replace('transit', 'transit-connect')
                        status_code = getUrlStatusCode(image_url)
                        if status_code == '404':
                            print('No image found for vehicle at url:', image_url)
                            image_url = image_url.replace('transit-connect', 'transit')  # switch url back

                    elif '2019' in image_url:
                        image_url = image_url.replace('2019', '2018')
                        status_code = getUrlStatusCode(image_url)
                        if status_code == '404':
                            print('No images found for this type of vehicle in previous year')

                            # Try swapping transit for transit-connect
                            if 'transit' in image_url:
                                print('testing transit w prev year')
                                image_url = image_url.replace('transit', 'transit-connect')
                                status_code = getUrlStatusCode(image_url)
                                if status_code == '404':
                                    print('No image found for vehicle at url:', image_url)
                                    continue
                            continue

                    elif '2018' in image_url:
                        image_url = image_url.replace('2018', '2017')
                        status_code = getUrlStatusCode(image_url)
                        if status_code == '404':
                            print('No images found for this type of vehicle in previous year')

                            # Try swapping transit for transit-connect
                            if 'transit' in image_url:
                                print('testing transit w prev year')
                                image_url = image_url.replace('transit', 'transit-connect')
                                status_code = getUrlStatusCode(image_url)
                                if status_code == '404':
                                    print('No image found for vehicle at url:', image_url)
                                    continue
                            continue
                    else:
                        print('No images found for this type of vehicle.')
                        continue
            offer_html += '<div class="rm-model-image"><img src="{}" alt="{} {} {}"/></div>'.format(image_url, year, make, model)
            offer_html += '</div>'  # close div sales-special-item model-special
            body_html += offer_html

    body_html += '</div>'  # Close offer-container


    # Modal form

    body_html += "<div class='modal fade' id='myModal' role='dialog'><div class='modal-dialog'><div class='modal-content'><div class='modal-header' style='padding:35px 0px;'><button type='button' class='close' data-dismiss='modal'>×</button><h4><span class='fa fa-tag'></span> Claim Offer</h4></div><div class='modal-body' style='padding:40px 50px;'><div class='rm-modal-offer-description'></div><form id='sales-specials-form' role='form' action='https://www.spencertichenor.com/scripts/sales-specials-form.php' method='post'><input type='hidden' name='inventory_type' value=''/><input type='hidden' name='year' value=''/><input type='hidden' name='make' value=''/><input type='hidden' name='model' value=''/><input type='hidden' name='trim' value=''/><input type='hidden' name='drive' value=''/><input type='hidden' name='engine' value=''/><input type='hidden' name='cab_style' value=''/><input type='hidden' name='msrp' value=''/><input type='hidden' name='sale-price' value=''/><input type='hidden' name='purchase_type' value=''/><input type='hidden' name='monthly_payment' value=''/><input type='hidden' name='apr' value=''/><input type='hidden' name='term_length' value=''/><input type='hidden' name='down_payment' value=''/><input type='hidden' name='due_at_signing' value=''/><input type='hidden' name='rebate_amount' value=''/><input type='hidden' name='expiration' value=''/><input type='hidden' name='offer_description' value=''/><div class='form-group'><label for='first_name'><span class='fa fa-user'></span> First Name</label><input type='text' class='form-control' id='first_name' name='first_name' placeholder='Henry'></div><div class='form-group'><label for='last_name'><span class='fa fa-user'></span> Last Name</label><input type='text' class='form-control' id='last_name' name='last_name' placeholder='Ford'></div><div class='form-group'><label for='email'><span class='fa fa-envelope'></span> Email</label><input type='text' class='form-control' id='email' name='email' placeholder='henry@ford.com'></div><div class='form-group'><label for='phone'><span class='fa fa-phone'></span> Phone</label><input type='text' class='form-control' id='phone' name='phone' placeholder='(XXX) XXX-XXXX'></div><div class='form-group'><label for='comment'><span class='fa fa-comment'></span> Comment</label><input type='text' class='form-control' id='comment' name='comment' placeholder='Leave a comment..'></div><div class='rm-submit-btn-container'><button type='submit' class='btn btn-block'><span class='fa fa-check-circle'></span> Submit</button></div></form></div><div class='modal-footer'><p>One of our representatives will contact you with more information and to answer and questions.</p></div></div></div></div>"

    body_html += '</div></div></div></div>'  # Close rest of tags

    print(body_html)

    # Close connection to database
    conn.close()

    return body_html


def save_html_as_txt(html):

    time_stamp = datetime.datetime.now()
    time_stamp = datetime.datetime.strftime(time_stamp, '%Y-%m-%d_%H:%M:%S')

    file_name = 'sales_specials_' + time_stamp

    text_file = open(file_name, 'w')
    text_file.write(html)
    text_file.close()

    new_file_path = 'data/sales_specials_html/' + file_name
    os.rename(file_name, new_file_path)

    return new_file_path


def send_mail(send_from, send_to, subject, message, files=[],
              server="localhost", port=587, username='', password='',
              use_tls=True):
    """Compose and send email with provided info and attachments.

    Args:
        send_from (str): from name
        send_to (str): to name
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{}"'.format(os.path.basename(path)))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()




def update_cdk_html():

    browser = fire_up_chromedriver(executable_path='/Users/spencertichenor/PycharmProjects/midway/chromedriver', virtual_display=False, auto_download=True, download_directory=r'data')
    wait = WebDriverWait(browser, 10)

    url = 'https://portal.cobalt.com/'

    browser.get(url)
    username = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="proxyUsername"]')))
    password = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="proxyPassword"]')))
    username.send_keys('spencer@rosevillemidwayford.com')
    password.send_keys('Pat0xley')
    wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="loginSubmit"]'))).click()

    wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="siteeditor"]/a'))).click()

    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="siteEditorIframe"]')))


    time.sleep(10)




def main():
    createSalesSpecialsTable()
    updateSalesSpecialsTable()
    html = generate_html()
    file_path = save_html_as_txt(html)
    send_mail('midway.ford.bot@gmail.com', 'spencertichenor@gmail.com', 'Sales Specials HTML', 'woolooloo', files=[file_path], server='smtp.gmail.com', port=587, username='midway.ford.bot@gmail.com', password='MidwayFord2777', use_tls=True)


if __name__ == '__main__':
    main()

    #update_cdk_html()
