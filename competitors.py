from lxml import html
import requests
import sqlite3
import math
import time
import locale
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sheets
import datetime
from pyvirtualdisplay import Display

locale.setlocale(locale.LC_ALL, 'en_US.utf8')  # 'en_US.utf8'


def fake_msrp_checker():
    # Connect to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    for competitor in competitorList:
        print('Checking for fake MSRPs in {} inventory\n\n'.format(competitor['tableName']))

        query = 'SELECT vin, msrp, low_msrp FROM {}'.format(competitor['tableName'])
        c.execute(query)

        results = c.fetchall()
        # print('RESULTS:', results)
        # print('LEN:', len(results))
        fakeCount = 0
        for result in results:
            vin = result[0]
            list_msrp = result[1]
            low_msrp = result[2]
            if list_msrp != low_msrp and list_msrp != None and low_msrp != None:
                print('\tLooks like a fake MSRP!!!')
                print('\tVIN:', vin)
                print('\tList MSRP:', list_msrp)
                print('\tReal MSRP:', low_msrp, '\n')
                fakeCount += 1

        print('\n\nFound {} vehicles with fake MSRPs listed.'.format(str(fakeCount)))
        print(10 * '\n')

    # Close connection to database
    conn.commit()
    conn.close()


def compare_discounts():
    # Establish connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # For each new model-year in our inventory, get unique MSRP
    c.execute('SELECT DISTINCT year FROM masterInventory WHERE invType = ?', ('New',))
    years = c.fetchall()
    for year in years:
        year = year[0]
        c.execute('SELECT DISTINCT model FROM masterInventory WHERE invType = ? AND year = ?', ('New', str(year)))
        models = c.fetchall()
        for model in models:
            model = model[0]
            print('*********************************' + str(year) + ' ' + model + '*********************************\n')
            c.execute('SELECT DISTINCT intMSRP FROM masterInventory WHERE invType = ? AND year = ? AND model = ?', ('New', str(year), model))
            msrps = c.fetchall()
            for msrp in msrps:
                msrp = msrp[0]
                # print('\tMSRP:', msrp, '\n')
                c.execute('SELECT MIN(intPrice), MAX(totalConditionalRebates) FROM masterInventory WHERE invType = ? AND year = ? AND model = ? AND intMSRP = ?',
                          ('New', str(year), model, msrp))
                results = c.fetchall()
                ourPrice = results[0][0]
                conditionalRebates = results[0][1]

                if ourPrice == 0:  # if it's a vehicle we haven't priced
                    ourPrice = msrp
                # continue  #continue??? not sure if this is right usage

                if conditionalRebates:
                    ourPrice = ourPrice - conditionalRebates

                print('\tMSRP:', locale.currency(msrp, grouping=True).replace('.00', ''))
                print('\tOur price:', locale.currency(ourPrice, grouping=True).replace('.00', ''), '\n')
                msrpMatches = False
                for competitor in competitorList:  # For each competitor, get price where MSRP and model-year are the same and compare to our price
                    # comPriceList = []
                    query = 'SELECT DISTINCT price FROM competitorInventory WHERE dealership = ? AND year = ? AND model = ? AND low_msrp = ? AND price > ?'
                    to_db = (competitor['dealership'], str(year), model, msrp, 0)
                    c.execute(query, to_db)
                    results = c.fetchall()
                    if results:  # != [] :
                        msrpMatches = True
                        print('\t\t' + competitor['dealership'] + '\n')
                        for i, result in enumerate(results):
                            comPrice = result[0]
                            # comPriceList.append(comPrice) # only used for mean
                            # print('\t\tPrice:', comPrice)
                            if comPrice < ourPrice:
                                comparator = 'LOWER'
                                difference = ourPrice - comPrice

                            elif comPrice > ourPrice:
                                comparator = 'HIGHER'
                                difference = comPrice - ourPrice
                            else:
                                comparator = 'SAME'
                                difference = ourPrice - comPrice
                            difference = locale.currency(difference, grouping=True).replace('.00', '')

                            query = 'SELECT vin, vdp_url FROM competitorInventory WHERE dealership = ? AND year = ? AND model = ? AND price = ?'
                            to_db = (competitor['dealership'], str(year), model, comPrice)
                            c.execute(query, to_db)
                            vehMatches = c.fetchall()
                            print('\t\t\t' + 'Found {} {} {} with an MSRP of {} priced at {} ({} {} than us):\n'
                                  .format(str(len(vehMatches)), str(year), model, locale.currency(msrp, grouping=True).replace('.00', ''),
                                          locale.currency(comPrice, grouping=True).replace('.00', ''), difference, comparator)
                                  )

                            for veh in vehMatches:
                                print('\t\t\tVIN:', veh[0])
                                print('\t\t\tVDP:', veh[1], '\n')
                        print('\n')
                print('\n')
                if not msrpMatches:  # == False :  if there were no matching MSRPs at any of the other dealerships
                    print('\t\tNo matches found.\n\n\n')

    conn.close()


competitorList = [
    {'dealership': 'Autonation Ford', 'domainName': 'http://autonationfordwhitebearlake.com', 'msrpXpath': '//li[contains(@class, "an-msrp")]//strong/text()',
     'priceXpath': '//li[contains(@class, "an-final-price") and not(contains(@class, "an-msrp"))]//strong/text()', 'condPriceXpath': '', 'boondock_dealer': False,
     'one_price_dealer': False},
    {'dealership': 'Freeway Ford', 'domainName': 'http://freewayford.net', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()',
     'priceXpath': '//span[contains(@class, "askingPrice")]/strong/text()', 'condPriceXpath': '//span[contains(@class, "stackedConditionalFinal")]/strong/text()',
     'boondock_dealer': False, 'one_price_dealer': False},
    {'dealership': 'Inver Grove Ford', 'domainName': 'http://invergroveford.com', 'msrpXpath': '//span[contains(@class, "retailValue")]/strong/text()',
     'priceXpath': '//span[contains(@class, "final-price")]/strong/text()', 'condPriceXpath': '//span[contains(@class, "stackedConditionalFinal")]/strong/text()',
     'boondock_dealer': False, 'one_price_dealer': False},
    {'dealership': 'New Brighton Ford', 'domainName': 'http://newbrightonford.com', 'msrpXpath': '//span[contains(@class, "retailValue")]/strong/text()',
     'priceXpath': '//span[contains(@class, "final-price")]/strong/text()', 'condPriceXpath': '//span[contains(@class, "stackedConditionalFinal")]/strong/text()',
     'boondock_dealer': False, 'one_price_dealer': False},
    {'dealership': 'Apple Ford', 'domainName': 'http://applefordshakopee.com', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()',
     'priceXpath': '//span[contains(@class, "askingPrice")]/strong/text()', 'condPriceXpath': '', 'boondock_dealer': False, 'one_price_dealer': True},
    {'dealership': 'North Country Ford', 'domainName': 'http://northcountryford.com', 'msrpXpath': '//span[contains(@class, "retailValue")]/strong/text()',
     'priceXpath': '//span[contains(@class, "final-price") and not(contains(@class, "retailValue"))]/strong/text()',
     'condPriceXpath': '//span[contains(@class, "stackedConditionalFinal")]/strong/text()', 'boondock_dealer': False, 'one_price_dealer': False},
    {'dealership': 'Superior Ford', 'domainName': 'http://superiorford.com', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()',
     'priceXpath': '//span[contains(@class, "final-price")]/strong/text()', 'condPriceXpath': '//span[contains(@class, "stackedConditionalFinal")]/strong/text()',
     'boondock_dealer': False, 'one_price_dealer': False},
    {'dealership': 'Metropolitan Ford', 'domainName': 'http://metropolitanford.com', 'msrpXpath': '//span[contains(@class, "internetPrice")]/strong/text()',
     'priceXpath': '//span[contains(@class, "final-price")]/strong/text()', 'condPriceXpath': '//span[contains(@class, "stackedConditionalFinal")]/strong/text()',
     'boondock_dealer': False, 'one_price_dealer': False},
    {'dealership': 'Rochester Ford', 'domainName': 'http://rochesterfordofmn.com', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()',
     'priceXpath': '//span[contains(@class, "salePrice")]/strong/text()', 'condPriceXpath': '', 'boondock_dealer': False, 'one_price_dealer': False},
    {'dealership': 'Hudson Ford', 'domainName': 'http://hudsonford.com', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()',
     'priceXpath': '//span[contains(@class, "internetPrice")]/strong/text()', 'condPriceXpath': '', 'boondock_dealer': False, 'one_price_dealer': False},
    {'dealership': 'Morries Minnetonka Ford', 'domainName': 'http://minnetonkaford.com', 'msrpXpath': '//li[contains(@class, "msrp")]/span[@itemprop="price"]/text()',
     'priceXpath': '//li[contains(@class, "retail-price")]/span[@itemprop="price"]/text()', 'condPriceXpath': '', 'boondock_dealer': False, 'one_price_dealer': False},
    # {'dealership': 'Vern Eide Ford', 'domainName': 'http://verneideford.com', 'msrpXpath': '//span[contains(@class, "retailValue")]/strong/text()', 'priceXpath': '//span[contains(@class, "internetPrice")]/strong/text()', 'condPriceXpath': '', 'boondock_dealer': True, 'one_price_dealer': False},
    # {'dealership': 'Luther Family Ford', 'domainName': 'http://lutherfamilyford.com', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()', 'priceXpath': '//span[contains(@class, "final-price")]/strong/text()', 'condPriceXpath': '', 'boondock_dealer': True, 'one_price_dealer': False},
    # {'dealership': 'Morries Buffalo Ford', 'domainName': 'http://morriesbuffaloford.com', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()', 'priceXpath': '//span[contains(@class, "internetPrice")]/strong/text()', 'condPriceXpath': '', 'boondock_dealer': True, 'one_price_dealer': False},
    # {'dealership': 'North Star Ford', 'domainName': 'http://www.northstarfordduluth.com', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()', 'priceXpath': '//span[contains(@class, "final-price")]/strong/text()', 'condPriceXpath': '//span[contains(@class, "stackedConditionalFinal")]/strong/text()', 'boondock_dealer': True, 'one_price_dealer': False},
    # {'dealership': 'Waconia Ford', 'domainName': 'http://waconiaford.net', 'msrpXpath': '//span[contains(@class, "msrp")]/strong/text()', 'priceXpath': '//span[contains(@class, "final-price")]/strong/text()', 'boondock_dealer': True, 'one_price_dealer': False},
]


def fmc_login():  # Logs into fmcdealer and returns browser

    # Fire up ChomeDriver
    display = Display(visible=0, size=(800, 600))
    display.start()
    path_to_chromedriver = 'chromedriver'
    browser = webdriver.Chrome(executable_path=path_to_chromedriver)
    wait = WebDriverWait(browser, 10)

    # Log into FMC Dealer
    url = 'https://fmcdealer.com'
    browser.get(url)
    username = wait.until(EC.element_to_be_clickable((By.ID, 'DEALER-WSLXloginUserIdInput')))
    password = wait.until(EC.element_to_be_clickable((By.ID, 'DEALER-WSLXloginPasswordInput')))
    username.send_keys('t-spen29')
    password.send_keys('Tichenor10')
    browser.find_element_by_xpath('//div[@id="DEALER-WSLXloginWSLSubmitButton"]/input').click()
    time.sleep(5)

    return browser


def clean_model(model):
    if 'Connect' in model:
        return 'Transit Connect'
    if 'Transit' in model:
        return 'Transit'
    if 'F-250' in model:
        return 'F-250'
    if 'F-350' in model:
        return 'F-350'
    if 'F-450' in model:
        return 'F-450'
    if 'F-550' in model:
        return 'F-550'
    if 'F-650' in model:
        return 'F-650'
    if 'Focus' in model:
        return 'Focus'
    if 'C-Max' in model or 'C-MAX' in model:
        return 'C-Max'
    return model


# does this thing check for dealer trades?
def scrape_elite_plus_sites():
    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # Run through each other dealership from the competitorList variable
    for competitor in competitorList:
        print('Scraping ' + competitor['dealership'] + '\n\n')

        # Get original vin list so that we can delete vehicles that are no longer in their inventory later
        new_vin_list = []
        original_vin_list = []
        query = 'SELECT vin FROM competitorInventory WHERE dealership = ?'
        to_db = (competitor['dealership'],)
        c.execute(query, to_db)
        results = c.fetchall()
        for r in results:
            original_vin_list.append(r[0])
        print('Number of vehicles originally in inventory:', len(original_vin_list))

        # Go to page #1 of new inventory
        url = competitor['domainName'] + '/new-inventory/index.htm'
        page = requests.get(url)
        tree = html.fromstring(page.content)
        vehicle_count = int(tree.xpath('//div/span[@class="vehicle-count"]/text()')[0])
        page_count = math.ceil(vehicle_count / 35)
        print('Total New Vehicles:', vehicle_count)
        print('Number of Pages:', page_count)

        for page_index in range(0, page_count):
            print('Scraping page ' + str(page_index + 1) + '/' + str(page_count))
            url = competitor['domainName'] + '/new-inventory/index.htm?start=' + str(page_index * 35)
            page = requests.get(url)
            tree = html.fromstring(page.content)

            vin_list = tree.xpath('//div[@class="hproduct auto ford"]/@data-vin')
            vdp_list = tree.xpath('//a[contains(., "View Details")]/@href')
            year_list = tree.xpath('//div[@class="hproduct auto ford"]/@data-year')
            model_list = tree.xpath('//div[@class="hproduct auto ford"]/@data-model')
            # print(vdps)
            # print(len(vdps))

            if len(vin_list) != len(vdp_list):
                print('ERROR ERROR number of VDPs does not equal num of VINs!!')
                raise ValueError
            # else:
            for i, vdp_url in enumerate(vdp_list):
                vdp_url = competitor['domainName'] + vdp_url
                vin = vin_list[i]
                year = year_list[i]
                model = model_list[i]
                model = clean_model(model)

                d = datetime.date.today()
                last_modified = str(d.month) + '/' + str(d.day) + '/' + str(d.year)

                # Set date in stock if new to inventory
                if vin in original_vin_list:
                    to_db = (competitor['dealership'], year, model, vdp_url, last_modified, vin)
                    query = 'UPDATE competitorInventory SET dealership = ?, year = ?, model = ?, vdp_url = ?, last_modified = ? WHERE vin = ?'

                else:
                    to_db = (competitor['dealership'], vin, year, model, vdp_url, last_modified, vin)
                    query = 'INSERT OR REPLACE INTO competitorInventory (dealership, vin, year, model, vdp_url, last_modified, date_in_stock) VALUES (?, ?, ?, ?, ?, ?, ?)'

                c.execute(query, to_db)
                new_vin_list.append(vin)
            conn.commit()

        # Delete vehicles that are no longer in inventory
        delete_count = 0
        if original_vin_list:
            for vin in original_vin_list:
                if vin not in new_vin_list:
                    query = 'DELETE FROM competitorInventory WHERE vin = ? AND dealership = ?'
                    to_db = (vin, competitor['dealership'])
                    print(to_db)
                    c.execute(query, to_db)
                    delete_count += 1
            conn.commit()
            print('Deleted {} vehicles from {} inventory table.'.format(str(delete_count), competitor['dealership']))

        query = 'SELECT vin, vdp_url FROM competitorInventory WHERE dealership = ?'
        to_db = (competitor['dealership'],)
        c.execute(query, to_db)
        result = c.fetchall()

        for i, t in enumerate(result):

            print('Scraping VDP for vehicle #' + str(i + 1) + '/' + str(len(result)) + '\n')

            vin = t[0]
            vdp_url = t[1]

            print('VIN:', vin)
            print('vdp_url:', vdp_url)

            try:
                page = requests.get(vdp_url)
            except ConnectionError as e:
                print('Exception caught for ConnectionError!')
                print(e)

            tree = html.fromstring(page.content)

            msrp = tree.xpath(competitor['msrpXpath'])
            if msrp:
                msrp = msrp[0].replace('$', '').replace(',', '')
            else:
                msrp = None

            price = tree.xpath(competitor['priceXpath'])
            if price and 'Please Call' not in price:
                price = price[0].replace('$', '').replace(',', '')
            else:
                price = None

            if competitor['condPriceXpath']:
                conditional_price = tree.xpath(competitor['condPriceXpath'])
                if conditional_price:
                    conditional_price = conditional_price[0].replace('$', '').replace(',', '')
                    price = conditional_price
                else:
                    conditional_price = price
            else:
                conditional_price = price

            print('MSRP:', msrp)
            print('Price:', price)
            print('Conditional Price:', conditional_price, '\n')

            # Update database
            query = 'UPDATE competitorInventory SET list_msrp = ?, price = ?, conditional_price = ? WHERE vin = ?'
            c.execute(query, (msrp, price, conditional_price, vin))
        conn.commit()

    # Close connection to database
    conn.close()


def add_midway_inventory():
    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # Get original vin list so that we can delete vehicles that are no longer in their inventory later
    new_vin_list = []
    query = 'SELECT vin FROM competitorInventory WHERE dealership = ?'
    to_db = ('Midway Ford',)
    c.execute(query, to_db)
    original_vin_list = c.fetchall()
    for i, vin in enumerate(original_vin_list):
        original_vin_list[i] = vin[0]
    print('Number of vehicles originally in inventory:', len(original_vin_list))

    query = ("""
        SELECT vin, year, model, intMSRP, intPrice, intInvoice, dfireUrl, intMSRP, totalConditionalRebates 
        FROM masterInventory 
        WHERE invType = ?
        """)
    to_db = ('New',)
    c.execute(query, to_db)
    results = c.fetchall()
    to_db = []
    for r in results:
        l = list(r)
        if l[8]:
            l[4] = l[4] - l[8]
        t = ('Midway Ford',) + tuple(l[:-1])
        print('t: ', t)
        to_db.append(t)
        new_vin_list.append(r[0])
        print(len(t))
    query = ("""
        INSERT OR REPLACE INTO competitorInventory 
        (dealership, vin, year, model, list_msrp, price, invoice, vdp_url, top_msrp) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
    c.executemany(query, to_db)
    conn.commit()

    # Delete vehicles that are no longer in inventory
    if original_vin_list:
        to_db = []
        for vin in original_vin_list:
            if vin not in new_vin_list:
                to_db.append((vin, 'Midway Ford'))
        if to_db:
            c.executemany('DELETE FROM competitorInventory WHERE vin = ? AND dealership = ?', to_db)
            conn.commit()

    conn.close()


# need to make it so there's a sheet for each model year. then same format but each msrp instead of each model. then put averages at top or something

def update_price_comparison_table():

    print('Updating priceComparison table.')

    # Establish connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # Clear table
    c.executescript("""
        DROP TABLE IF EXISTS priceComparisons;

        CREATE TABLE priceComparisons (
          dealership  TEXT NOT NULL,
          year INTEGER NOT NULL,
          model TEXT NOT NULL,
          matchCount INTEGER,
          avgDifference INTEGER,
          vdpUrls TEXT
        );
        """)
    conn.commit()

    # For each new model-year in our inventory, get unique MSRP
    c.execute('SELECT DISTINCT year FROM competitorInventory WHERE dealership = ?', ('Midway Ford',))
    years = c.fetchall()
    for year in years:
        year = year[0]
        c.execute('SELECT DISTINCT model FROM competitorInventory WHERE dealership = ? AND year = ?', ('Midway Ford', year))
        models = c.fetchall()
        for model in models:
            match_dict = {}  # form of {'Freeway Ford': [4, 300], 'Apple Ford': [15, -100]}
            model = model[0]
            print('*********************************' + str(year) + ' ' + model + '*********************************\n')
            query = ("""
                SELECT DISTINCT list_msrp, low_msrp, invoice 
                FROM competitorInventory 
                WHERE dealership = ? AND year = ? AND model = ? AND price < list_msrp
                """)
            to_db = ('Midway Ford', year, model)
            c.execute(query, to_db)
            prices = c.fetchall()
            for p in prices:
                list_msrp = p[0]
                low_msrp = p[1]
                invoice = p[2]
                print('\tList MSRP:', list_msrp, '\n')
                print('\tLow MSRP:', low_msrp, '\n')
                print('\tInvoice:', invoice, '\n')
                query = (
                    ("""
                    SELECT MIN(price)
                    FROM competitorInventory 
                    WHERE dealership = ? AND year = ? AND model = ? AND (list_msrp = ? AND list_msrp IS NOT NULL OR low_msrp = ? AND low_msrp IS NOT NULL OR invoice = ? AND invoice IS NOT NULL) AND price < list_msrp 
                    ORDER BY price
                    """)
                )
                to_db = ('Midway Ford', year, model, list_msrp, low_msrp, invoice)
                c.execute(query, to_db)
                results = c.fetchall()
                our_price = results[0][0]

                query = (
                    ("""
                    SELECT DISTINCT price, dealership 
                    FROM competitorInventory 
                    WHERE year = ? AND model = ? AND price IS NOT NULL AND dealership != ? AND (list_msrp = ? OR low_msrp = ? OR invoice = ?) 
                    ORDER BY price
                    """)
                )
                to_db = (year, model, 'Midway Ford', list_msrp, low_msrp, invoice)

                # Skip dealerships that aren't that close to us (comment this part out if you want all dealerships)
                boondock_dealers = ['Hudson Ford', 'Luther Family Ford', 'Waconia Ford', 'Morries Buffalo Ford', 'Vern Eide Ford', 'North Star Ford', 'Rochester Ford']
                for d in boondock_dealers:
                    query += 'AND dealership != ?'
                    to_db += (d,)

                c.execute(query, to_db)
                results = c.fetchall()
                print('distinct price dealership - results:', results)
                if results:
                    prev_dealer = ''
                    for i, result in enumerate(results):
                        com_price = result[0]
                        dealership = result[1]

                        if dealership != prev_dealer:
                            prev_dealer = dealership
                        difference = com_price - our_price
                        query = (
                            ("""
                            SELECT vin, vdp_url, list_msrp 
                            FROM competitorInventory 
                            WHERE dealership = ? AND year = ? AND model = ? AND price = ?
                            """)
                        )
                        to_db = (dealership, str(year), model, com_price)
                        c.execute(query, to_db)
                        veh_matches = c.fetchall()
                        for veh in veh_matches:
                            if veh[2]:
                                msrp = locale.currency(veh[2], grouping=True)
                            else:
                                msrp = ''
                            vdp_link = '{} ~ {} ~ {} ~ {}'.format(
                                msrp, locale.currency(com_price, grouping=True), locale.currency(difference, grouping=True)[:-3], veh[1])
                        if dealership in match_dict.keys():
                            total_diff = match_dict[dealership][0] * match_dict[dealership][1] + difference
                            match_dict[dealership][0] += 1
                            match_dict[dealership][1] = total_diff / match_dict[dealership][0]
                            match_dict[dealership][2].append(vdp_link)
                        else:  # this is the first match for this dealer
                            match_dict[dealership] = [1, difference, [vdp_link]]
            for dealership in match_dict:
                match_count = match_dict[dealership][0]
                difference = match_dict[dealership][1]
                difference = int(difference)  # int(float(difference.replace('$', '').replace(',', '')))
                vdp_urls = match_dict[dealership][2]
                vdp_urls = str(vdp_urls).replace('[', '').replace(']', '').replace("'", "")  # .replace(', ', '')
                if difference > 0:
                    comparator = 'HIGHER'
                elif difference < 0:
                    comparator = 'LOWER'
                else:
                    comparator = 'SAME'

                print('\t' + dealership + ' - Found ' + str(match_count) + ' matches priced ' + locale.currency(difference, grouping=True).replace('.00', '').replace('-',
                                                                                                                                                                      '') + ' ' + comparator + ' that us.')
                query = 'INSERT OR REPLACE INTO priceComparisons (dealership, year, model, matchCount, avgDifference, vdpUrls) VALUES (?, ?, ?, ?, ?, ?)'
                to_db = (dealership, year, model, match_count, difference, vdp_urls)
                c.execute(query, to_db)
                conn.commit()
    conn.close()

    print('Finished updating priceComparisons table.')


def compareAverages(year, model):
    # Establish connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # For each new model-year in our inventory, get unique MSRP
    c.execute('SELECT DISTINCT intMSRP FROM masterInventory WHERE invType = ? AND year = ? AND model = ?', ('New', year, model))
    results = c.fetchall()
    for r in results:
        msrp = r[0]
        c.execute('SELECT DISTINCT model FROM masterInventory WHERE invType = ? AND year = ?', ('New', str(year)))
        models = c.fetchall()
        for model in models:
            model = model[0]
            print('*********************************' + str(year) + ' ' + model + '*********************************\n')
            c.execute('SELECT DISTINCT intMSRP FROM masterInventory WHERE invType = ? AND year = ? AND model = ?',
                      ('New', str(year), model))
            msrps = c.fetchall()
            for msrp in msrps:
                msrp = msrp[0]
                # print('\tMSRP:', msrp, '\n')
                query = 'SELECT min(intPrice) FROM masterInventory WHERE invType = ? AND year = ? AND model = ? AND intMSRP = ?'
                to_db = ('New', str(year), model, msrp)
                c.execute(query, to_db)
                ourPrice = c.fetchall()
                ourPrice = ourPrice[0][0]
                if ourPrice == 0:  # if it's a vehicle we haven't priced
                    ourPrice = msrp
                print('\tMSRP:', msrp)
                print('\tOur price:', ourPrice, '\n')
                msrpMatches = False
                for competitor in competitorList:  # For each competitor, get price where MSRP and model-year are the same and compare to our price
                    # comPriceList = []
                    query = 'SELECT price FROM competitorInventory WHERE dealership = ? AND year = ? AND model = ? AND list_msrp = ?'
                    to_db = (competitor['dealership'], str(year), model, msrp)

    # Close connection to database
    conn.close()


def randomInterval():
    # returns random float roughly between 1.5 and 2.75
    return 1.75 + 1 * random.random() - .25 * random.random()


def scrape_vl_plus():
    print('Scraping Vehicle Locator..')

    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # Make list of vins originally in db
    original_vin_list = []
    query = 'SELECT vin FROM competitorInventory'
    c.execute(query)
    results = c.fetchall()
    for r in results:
        original_vin_list.append(r[0])

    # all the xpath that we're gonna need
    model_name_list_xpath = '//div[@id="fordVehicles"]/label/text()'
    model_input_list_xpath = '//div[@id="fordVehicles"]/input'
    search_button_xpath = '//a[contains(@class, "newSearchButton")]'
    vin_list_xpath = '//a[@name="vinDetails"]/@vin'
    msrp_list_xpath = '//td[contains(@class, "msrp")]/a[@class="htmlWindowSticker"]/text()'
    invoice_list_xpath = '//a[@class="invoiceLink"]/text()'
    pep_list_xpath = '//td[@class="vehicleBody"]/text()'
    order_type_list_xpath = '//a[@onclick="showOrderTypeInfo()"]/text()'
    engine_list_xpath = '//tr[contains(@class, "vehiclerow")]/td[8]/text()'

    # Log into FMC Dealer
    browser = fmc_login()
    wait = WebDriverWait(browser, 10)

    browser.get('https://www.vlplus.dealerconnection.com/Search')
    source = browser.page_source
    tree = html.fromstring(source)
    model_name_list = tree.xpath(model_name_list_xpath)
    model_input_list = tree.xpath(model_input_list_xpath)
    time.sleep(randomInterval())
    for i, model_input in enumerate(model_input_list):
        model_name = model_name_list[i]
        print('Getting data for ' + model_name + '...')
        browser.get('https://www.vlplus.dealerconnection.com/Search')
        time.sleep(randomInterval())
        if 'FORD GT' in model_name:  # or 'F-150' in model_name or 'EXPLORER' in model_name or 'EXPEDITION' in model_name or 'EDGE' in model_name or 'ECONOLINE' in model_name or 'ESCAPE' in model_name:
            continue
        model_input = browser.find_elements_by_xpath(model_input_list_xpath)[i]
        model_input.click()
        time.sleep(randomInterval())

        browser.find_element_by_xpath(search_button_xpath).click()
        time.sleep(randomInterval())

        # Skip if no vehicles match query
        source = browser.page_source
        if 'Please broaden your search' in source:
            print('SKIPPING')
            browser.find_element_by_xpath('//a[@id="refineSearch"]').click()
            continue

        tree = html.fromstring(source)
        vehicle_count = tree.xpath('//th[@class="resultcount"]/@data-resultcount')
        vehicle_count = int(vehicle_count[0])
        page_count = int(math.ceil(vehicle_count / 25))
        print('Total pages:', page_count)

        for j in range(0, page_count):
            tree = html.fromstring(browser.page_source)
            vin_list = tree.xpath(vin_list_xpath)
            ugly_msrp_list = tree.xpath(msrp_list_xpath)
            ugly_invoice_list = tree.xpath(invoice_list_xpath)
            ugly_pep_list = tree.xpath(pep_list_xpath)
            ugly_order_type_list = tree.xpath(order_type_list_xpath)
            ugly_engine_list = tree.xpath(engine_list_xpath)

            msrp_list = []
            invoice_list = []
            pep_list = []
            order_type_list = []
            engine_list = []
            for k in range(0, len(vin_list)):

                # Clean up and add msrp
                msrp_list.append(ugly_msrp_list[k].replace('$', '').replace(',', ''))
                if msrp_list[k] != 'n/a':
                    msrp_list[k] = int(msrp_list[k])
                else:
                    msrp_list[k] = ''

                # Clean up and add invoice price
                invoice_list.append(ugly_invoice_list[k].replace('$', '').replace(',', ''))
                if invoice_list[k] != 'n/a':
                    invoice_list[k] = int(invoice_list[k])
                else:
                    invoice_list[k] = ''

            # Clean up pep code text
            for pep_code in ugly_pep_list:
                if 'PEP Code' in pep_code:
                    pep_code = pep_code.split('PEP Code: ')[1]
                    pep_list.append(pep_code)

            print(len(ugly_order_type_list))
            for order_type in ugly_order_type_list:
                order_type_list.append(order_type)

            # Clean up engine text
            for engine in ugly_engine_list:
                engine = engine.split('<br>')[0].replace('  ', '').replace('\n', '')
                if 'L ' in engine or 'ELECTRIC' in engine:
                    if 'SPD' not in engine and 'SPEED' not in engine:
                        engine_list.append(engine)

            # Raise error if amounts don't add up
            if len(msrp_list) != len(invoice_list):
                raise ValueError
            if len(pep_list) != len(msrp_list):
                raise ValueError

            print('msrp_list len: ', len(msrp_list))
            print('msrp_list: ', msrp_list)
            print('invoice_list: ', invoice_list)
            print('pep_list: ', pep_list)
            print('order_type_list: ', order_type_list)
            print('engine_list: ', engine_list)
            print('engine_list: ', len(engine_list))

            to_db = []
            for k, vin in enumerate(vin_list):
                print('VIN: ', vin)
                print('msrp: ', msrp_list[k])
                print('invoice: ', invoice_list[k])
                print('pep: ', pep_list[k])
                print('order_type: ', order_type_list[k])
                print('engine: ', engine_list[k], '\n')
                if msrp_list[k] < invoice_list[k]:
                    print('MSRP somehow less than invoice')
                    raise ValueError
                to_db.append((msrp_list[k], invoice_list[k], pep_list[k], order_type_list[k], engine_list[k], vin))
                query = ("""
                    UPDATE competitorInventory 
                    SET low_msrp = ?, invoice = ?, pep_code = ?, order_type = ?, engine = ? 
                    WHERE vin = ?
                    """)
            c.executemany(query, to_db)
            conn.commit()

            # Skip to next model if on last page
            if j + 1 == page_count:
                'Finished getting data for ' + model_name
                time.sleep(3)
                continue

            time.sleep(randomInterval())
            next_page_xpath = '//a[@page="{}"]'.format(str(j + 2))
            next_page_link = wait.until(EC.element_to_be_clickable((By.XPATH, next_page_xpath)))
            next_page_link.click()

            # browser.find_element_by_xpath(next_page_xpath).click()
            time.sleep(randomInterval() * 2)

    conn.close()
    print('Finished scraping VehicleLocator.')


def scrape_carsdotcom():

    url_dict = {
        'Midway Ford': 'midway_ford-17449/',
        'Autonation Ford': 'autonation_ford_white_bear_lake-17439/',
        'Superior Ford': 'superior_ford-17574/',
        'Freeway Ford': 'freeway_ford-17543/',
        'Metropolitan Ford': 'metropolitan_ford-80894/',
        'Apple Ford - Apple Valley': 'apple_ford_lincoln_apple_valley-17455/',
        'Apple Ford - Shakopee': 'apple_ford_shakopee-157973/',
        'Hudson Ford': 'hudson_ford-158055/',
        'Hastings Ford': 'hastings_automotive-157919/',
        'North Country Ford': 'luther_north_country_ford_lincoln-17587/',
        'Minnetonka Ford': '87892/morries-minnetonka-ford-lincoln/',
        'Waconia Ford': 'waconia_ford-17523/',
        'New Brighton Ford': '',

    }

    base_url = 'https://www.cars.com/shopping/new/'

    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()




    conn.commit()
    conn.close()


def scrape_carsoup():
    url_dict = {
        'Midway Ford': 'Roseville-Midway-Ford/2322/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'Autonation Ford': 'AutoNation-Ford-White-Bear-Lake/107/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=100&sorting=price+asc&ss=active',
        'Superior Ford': 'Superior-Brookdale-Ford/1545/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'Freeway Ford': 'Freeway-Ford/40/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'Metropolitan Ford': 'Metropolitan-Ford/66/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'Apple Ford - Apple Valley': 'Apple-Ford-Lincoln-Apple-Valley/7/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=100&sorting=distance+asc&ss=active',
        'Apple Ford - Shakopee': 'Apple-Ford-Shakopee/743/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'Hudson Ford': 'Hudson-Ford/7447/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'Hastings Ford': 'Hastings-Ford/866/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'North Country Ford': 'North-Country-Ford-Lincoln/133/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'Minnetonka Ford': 'Morries-Minnetonka-Ford/13/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=100&sorting=price+asc&ss=active',
        'Waconia Ford': 'Waconia-Ford/2345/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=30&sorting=price+asc&ss=active',
        'New Brighton Ford': 'New-Brighton-Ford/1326/inventory/New/Saint-Paul-MN-55113?currentPage=1&r=50&resultsPerPage=100&sorting=price+asc&ss=active',

    }

    base_url = 'https://www.carsoup.com/find-dealers/'

    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()


    conn.commit()
    conn.close()



def main():
    #scrape_elite_plus_sites()
    #add_midway_inventory()
    scrape_vl_plus()
    #update_price_comparison_table()


if __name__ == '__main__':
    main()

"""
TO DO:

    add bool for each competeir for uses topline msrp
    for those dealers, if no top line found in clplus, ignore
    need
    add bool to compet inv table for twin cities or no so i can filter if wanted
    
    maybe remove veh from stats if price == msrp

"""
