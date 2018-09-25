import sqlite3
import math
import time
from pprint import pprint
from lxml import html
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pyvirtualdisplay import Display

from utilz import fire_up_chromedriver
#import pyautogui


# FMC Dealer Scrapes
def randomInterval():  # returns random float roughly between 1.5 and 2.75
    return 1.75 + 1 * random.random() - .25 * random.random()


def switchDefaultSearch(browser):  # Switch between MyLot/States
    # Switch default search back to Dealership Proximity
    print('Switching default search...')
    browser.get('https://www.vlplus.dealerconnection.com/Search?&searchType=quicksearch')
    time.sleep(3)
    browser.find_element_by_xpath('//a[@id="ActivateSettings"]').click()
    time.sleep(3)
    browser.find_element_by_xpath('//a[text()="Search Settings"]').click()
    time.sleep(3)

    # Check what default is currently set to
    tree = html.fromstring(browser.page_source)
    currentSetting = tree.xpath('//option[@selected]/text()')
    print('Setting Before:', currentSetting)
    if 'My Lot' in currentSetting:
        print('Switching default search from My Lot to Proximity')
        browser.find_element_by_xpath('//select[@id="searchSettingsDefaultSearchMode"]').click()
        time.sleep(2)
        browser.find_element_by_xpath('//option[@value="6"]').click()
        time.sleep(2)
    elif 'States' in currentSetting:
        print('Switching default search from States to My Lot')
        browser.find_element_by_xpath('//select[@id="searchSettingsDefaultSearchMode"]').click()
        time.sleep(2)
        browser.find_element_by_xpath('//option[@value="1"]').click()
        time.sleep(2)
    currentSetting = tree.xpath('//option[@selected]/text()')
    # print('Setting After:', currentSetting)   This doesn't work..


    browser.find_element_by_xpath('//a[@id="saveSearchSettings"]').click()
    time.sleep(2)
    browser.get('https://www.vlplus.dealerconnection.com/Search?&searchType=quicksearch')
    time.sleep(2)
    print('Finished switching default search...')
    return browser


def getVinList():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    vinList = []
    c.execute('SELECT vin FROM masterInventory where invType = ?', ('New',))
    vinTupleList = c.fetchall()
    for vinTuple in vinTupleList:
        vin = vinTuple[0]
        vinList.append(vin)
    numVehicles = len(vinList)

    conn.commit()
    conn.close()

    return vinList


def enter_fmc_login_info(browser):
    username = browser.find_element_by_id('DEALER-WSLXloginUserIdInput')
    password = browser.find_element_by_id('DEALER-WSLXloginPasswordInput')
    username.send_keys('t-spen29')
    password.send_keys('Tichenor70')
    browser.find_element_by_xpath('//div[@id="DEALER-WSLXloginWSLSubmitButton"]/input').click()
    time.sleep(5)

    while 'clicked in 2 seconds' in browser.page_source:
        time.sleep(5)

    return browser


def fmcdealer_login(browser, wait):  # Logs into fmcdealer and returns browser

    # # Fire up ChomeDriver
    # path_to_chromedriver = '/Users/spencertichenor/PycharmProjects/midway/chromedriver'
    #
    # browser = fire_up_chromedriver(executable_path=path_to_chromedriver, virtual_display=False, auto_download=True, download_directory=r'data/ds_sales')

    # wait = WebDriverWait(browser, 10)

    # Log into FMC Dealer
    url = 'https://fmcdealer.com'
    browser.get(url)
    wait.until(EC.element_to_be_clickable((By.ID, 'DEALER-WSLXloginUserIdInput')))
    browser = enter_fmc_login_info(browser)

    return browser


def navigateToVincent(browser, vin):
    print('\nNavigating to Vincent page for VIN: ' + vin + '...\n\n')

    # print('\nSearching for rebate info for vehicle ' + str(k+1) + '/' + str(len(vinList)) + '...')
    # print('\n\tVIN: ' + vin + '\n')
    browser.get('https://www.vlplus.dealerconnection.com/Search?&searchType=quicksearch')
    time.sleep(3)
    try:
        vinField = browser.find_element_by_id('txtVIN')
        vinField.send_keys(vin)
        browser.find_element_by_xpath('//input[@value="Search"]').click()
        time.sleep(2)
    except:
        print('VIN FIELD ERROR:')
        print(sys.exc_info()[0])
        # errorList.append(vin)
        # pass    this was pass but i think it should be return
        return browser

    source = browser.page_source
    if 'Please broaden your search.' not in source:  # Check if vehicle was not found in dealership proximity search

        # Click on Vincent button
        # source = browser.page_source

        try:
            vincentUrl = vincentUrl[0]
            browser.get(vincentUrl)
            time.sleep(4)
        except:
            print('Vincent Url Error:')
            print(sys.exc_info()[0])
            # errorList.append(vin)
            # pass
            return browser

        source = browser.page_source
        tree = html.fromstring(source)
        if 'Please click the "Close" button to continue with the Sales Process.' in source:  # Check for recall warning
            browser.find_element_by_xpath('//input[@value="Close"]').click()
            time.sleep(2)

        if 'value="Certificate Inquiry"' not in source:  # Check if vehicle already sold

            # Enter ZIP code and click next
            try:
                zipField = browser.find_element_by_xpath('//div/input[@name="customerZip"]')
                zipField.send_keys('55113')
                browser.find_element_by_id('primaryButtonId').click()
                time.sleep(2)
            except:
                print('ZIP FIELD ERROR:')
                print(sys.exc_info()[0])
                # errorList.append(vin)
                pass

                # Get rebate info

                # rebateInfo = scrapeRebateInfo(browser)

        else:
            # soldList.append(vin)
            print('\tIt looks like this vehicle has already been sold.\n\n')
    else:  # Vehicle not found in Dealership Proximity search
        print('\tVehicle not found after searching Dealership Proximity.')

        # Switch default search to My Lot
        browser = switchDefaultSearch(browser)
        try:
            vinField = browser.find_element_by_id('txtVIN')
            vinField.send_keys(vin)
            browser.find_element_by_xpath('//input[@value="Search"]').click()
            time.sleep(2)
        except:
            # errorList.append(vin)
            print('VIN FIELD ERROR:')
            print(sys.exc_info()[0])
            # switchToProximity(browser)
            return browser

        # Click on Vincent button
        source = browser.page_source
        tree = html.fromstring(source)
        vincentUrl = tree.xpath('//a[@title="Smart Vincent"]/@href')
        try:
            vincentUrl = vincentUrl[0]
            browser.get(vincentUrl)
            time.sleep(4)
        except:
            # errorList.append(vin)
            print('Vincent Url Error:')
            print(sys.exc_info()[0])
            # switchToProximity(browser)
            # return browser

        source = browser.page_source
        tree = html.fromstring(source)
        if 'Please click the "Close" button to continue with the Sales Process.' in source:  # Check for recall warning
            browser.find_element_by_xpath('//input[@value="Close"]').click()
            time.sleep(2)

        if 'value="Certificate Inquiry"' not in source:  # Check if vehicle already sold

            # Enter ZIP code and click next
            try:
                zipField = browser.find_element_by_xpath('//div/input[@name="customerZip"]')
                zipField.send_keys('55113')
                browser.find_element_by_id('primaryButtonId').click()
                time.sleep(2)
            except:
                # errorList.append(vin)
                print('ZIP FIELD ERROR:')
                print(sys.exc_info()[0])
                # switchToProximity(browser)
                # return browser

                # Get rebate info
                # rebateInfo = scrapeRebateInfo(browser)



        else:
            # soldList.append(vin)
            print('\tIt looks like this vehicle has already been sold.\n\n')

            # Switch default search back to Dealership Proximity
            # switchToProximity(browser)
            # pass

    return browser







    # print('\nNumber of vehicles appear to have been sold: ' + str(len(soldList)))
    # print('Sold List:')
    # print(soldList)
    # print('\nNumber of vehicles that ran into errors: ' + str(len(errorList)))
    # print('Error List:')
    # print(errorList)
    # print('\n\nFinished getting rebate information.')


def scrapeRebateInfo(page_source):  # input browser of vincent page, return tuple with unconditional rebate info


    # Get rebate info
    # source = browser.page_source
    tree = html.fromstring(page_source)
    vin = tree.xpath('//dt[.="VIN:"]/following-sibling::dd/text()')
    vin = vin[0].replace('\xa0', ' ').replace('\t', '').replace('\n', '')
    rowspans = tree.xpath('//table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textC altRow"]/@rowspan | //table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textC "]/@rowspan')
    conditions = tree.xpath('//table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr[@class="programTableHeader"]/td[@style="{border-right:none;}"]/text()')
    nums = tree.xpath('//table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textL txtCol  "]/a/text() | //table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textL txtCol altRow "]/a/text()')
    names = tree.xpath('//table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textL txtCol  "]/text() | //table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textL txtCol altRow "]/text()')
    amounts = tree.xpath('//table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textR "]/text() | //table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textR altRow"]/text()')
    expirations = tree.xpath('//table[@summary="This table displays and lets you choose public program bundles."]/tbody/tr/td[@class="textC highlight noWrap"]/text()')

    to_db = (vin,)

    if rowspans == []:  # No unconditional rebates
        print('No rebates found for this vehicle.\n')
        print('Updating rebate info...')
        while len(to_db) < 43:
            to_db += (None,)
    else:  # Yah, it has unconditional rebates
        # Clean up Condition info
        condition = conditions[0]
        condition = condition.replace('\n', '').replace('\t', '').replace('  ', '').replace(':C', ': C')
        condition = condition[1:]
        condition = removeWeirdChars(condition)
        if 'Cash Payment' in condition:
            print('\tUnconditional Rebates:\n')
            i = 0
            for i in range(i, int(rowspans[0])):
                num = nums[i].replace('\n', '').replace('\t', '').replace('  ', '')
                name = names[i * 2 + 1].replace('\n', '').replace('\t', '').replace(' - ', '').replace('s  C', 's C').replace('  ', '').replace('"', '')
                amount = amounts[i].replace('\n', '').replace('\t', '').replace('  ', '')
                expiration = expirations[i].replace('\n', '').replace('\t', '').replace('  ', '')
                if 'SIRIUS' in name:  # Fix for the stupid 6-month extra Sirius incentive
                    amount = '$0'
                if ' - ' not in amount and 'Amount Not Available' not in amount:  # stupid fix for Oct 2016 rebate and anotehr fix for Dec 2016 rebate
                    print('\t\tProgram: #' + num)
                    print('\t\tName: ' + name)
                    print('\t\tAmount: ' + amount)
                    print('\t\tExpiration: ' + expiration + '\n')
                    to_db += (num,) + (name,) + (condition,) + (amount,) + (expiration,) + (condition,)  # fix double header
            while len(to_db) < 43:
                to_db += (None,)

    return to_db
    time.sleep(2)


def scrapeLeaseInfo(page_source):
    # Connect to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    to_db = ()

    # Get rebate info

    tree = html.fromstring(page_source)

    vin = tree.xpath('//dt[.="VIN:"]/following-sibling::dd/text()')
    vin = vin[0].replace('\xa0', ' ').replace('\t', '').replace('\n', '')

    vehDesc = tree.xpath('//dt[.="Description:"]/following-sibling::dd/text()')
    residualTable = tree.xpath('//table[@class="rateTable"]/tbody/tr/td/text() | //table[@class="rateTable"]/thead/tr/th/text()')
    # rclRebateRow = tree.xpath('//tr[td[contains(., "RCL Customer Cash")]]/td/text()')
    rclFactorsRow = tree.xpath('//tr[td[contains(., "RCL Factors")]]/td/text()')
    rclTermLengths = tree.xpath('//tr[td[contains(., "RCL Factors")]]//th/text()')
    rclFactors = tree.xpath('//tr[td[contains(., "RCL Factors")]]//td/text()')
    rebateCells = tree.xpath('//tr[td[contains(., "LEASE")]]/following-sibling::*/td/text()')
    # print('rebateCells:', rebateCells)
    # print('length of rebateCells:', len(rebateCells))




    if rebateCells != []:
        print('Lease Rebates:')

        rebateDict = {}
        for i, cell in enumerate(rebateCells):
            if 'Cash' in cell and 'Fast Cash Certificate' not in cell:
                rebateName = cell.replace('\t', '').replace('\n', '').replace(' - ', '')
                if '$' in rebateCells[i + 2]:
                    rebateAmount = int(rebateCells[i + 2].replace('\t', '').replace('\n', '').replace(' ', '').replace('$', '').replace(',', ''))
                    rebateExpiration = rebateCells[i + 3].replace('\t', '').replace('\n', '').replace(' ', '')
                elif '$' in rebateCells[i + 3]:
                    rebateAmount = int(rebateCells[i + 3].replace('\t', '').replace('\n', '').replace(' ', '').replace('$', '').replace(',', ''))
                    rebateExpiration = rebateCells[i + 4].replace('\t', '').replace('\n', '').replace(' ', '')

                rebateDict[rebateName] = [rebateAmount, rebateExpiration]
                print('\tRebate Name:', rebateName)
                print('\tRebate Amount:', rebateAmount)
                print('\tRebate Expiration:', rebateExpiration)
                print('\n')

        print('rebateDict:', rebateDict)

        totalRebates = 0
        for rebateName in rebateDict:
            totalRebates += rebateDict[rebateName][0]

        vehDesc = vehDesc[0].replace('\xa0', ' ').replace('\t', '').replace('\n', '')
        rclResiduals = {}
        for i, leaseTerm in enumerate(residualTable[0:4]):
            rclResiduals[leaseTerm + ' Month'] = float(residualTable[i + 5]) / 100

        # rclRebateName = rclRebateRow[5].replace('\t', '').replace('\n', '').replace(' - ', '')
        # rclRebateAmount = rclRebateRow[8].replace('\t', '').replace('\n', '').replace(' ', '').replace('$', '').replace(',', '')
        # rclRebateExpiration = rclRebateRow[9].replace('\t', '').replace('\n', '').replace(' ', '')

        rclTermLengths = rclTermLengths[:-1]
        for i, termLength in enumerate(rclTermLengths):
            rclTermLengths[i] = int(termLength)

        rclFactorsExpiration = rclFactorsRow[8].replace('\t', '').replace('\n', '').replace(' ', '')

        factors = {}
        for e in rclFactors:
            if 'Tier' in e:
                tierIndex = rclFactors.index(e)
                tier = rclFactors[tierIndex]
                tierFactors = rclFactors[tierIndex + 1:tierIndex + 5]
                for i, factor in enumerate(tierFactors):
                    tierFactors[i] = float(factor)
                factors[tier] = tierFactors

        print('VIN:', vin)
        print('Vehicle Description:', vehDesc)
        # print('RCL Rebate Name:', rclRebateName)
        print('Total Rebates:', totalRebates)
        # print('RCL Rebate Expiration:', rclRebateExpiration)
        print('RCL Lengths:', rclTermLengths)
        print('RCL Factors: ', factors)  # used to be factors but too hard to deal with everything
        print('RCL Factors Expiration:', rclFactorsExpiration)
        print('RCL Residual:', rclResiduals)

        c.execute('SELECT stock, year, model, vehTrim FROM masterInventory WHERE vin = ?', (vin,))
        vehInfo = c.fetchall()
        vehInfo = vehInfo[0]
        print('vehInfo:', vehInfo)

        to_db = (vin,) + vehInfo + (str(rebateDict), totalRebates, str(rclTermLengths), str(factors), rclFactorsExpiration, str(rclResiduals))
        # to_db = (vin, str(rebateDict), totalRebates, str(rclTermLengths), str(factors), rclFactorsExpiration, str(rclResiduals))


    else:
        print('No lease info found.')
        to_db = (vin, None, None, None, None, None, None, None, None, None, None)

    # Close connection to database
    conn.commit()
    conn.close()

    return to_db
    time.sleep(2)




def scrape_cdk():

    # Connect to db
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    to_db = []

    # Get VDP Urls for new inventory

    url = 'https://www.rosevillemidwayford.com/VehicleSearchResults'
    page = requests.get(url)
    tree = html.fromstring(page.content)

    total_vehicles = tree.xpath('//*[@id="card-view/card/aafa1aff-abec-44e9-8226-a702bb0a5dd6"]/div[1]/div[1]/div[1]/h3/text()')
    total_vehicles = int(total_vehicles[0].replace(' Vehicles Found', ''))
    num_of_pages = int(math.ceil(total_vehicles / 24))
    print('Total New Vehicles: ' + str(total_vehicles))
    print('Number of Pages: ' + str(num_of_pages))

    for page_number in range(0, num_of_pages):
        url = 'https://www.rosevillemidwayford.com/VehicleSearchResults?limit=24&offset={}'.format(page_number * 24)
        print('Getting data from URL: ' + url + '\n')
        page = requests.get(url)
        tree = html.fromstring(page.content)
        vdp_url_list = tree.xpath('//a[@title="View Details"]/@href')
        vin_list = tree.xpath('//span[@itemprop="vehicleIdentificationNumber"]/text()')

        if len(vdp_url_list) != len(vin_list):
            print('ERROR: len(vdp_url_list) != len(vin_list)')
            raise IndexError

        for k in range(0, len(vin_list)):
            to_db.append((vdp_url_list[k], vin_list[k]))

    pprint(to_db)

    # Update database
    query = ('UPDATE masterInventory '
             'SET vdp_url = ? '
             'WHERE vin = ?')
    c.executemany(query, to_db)

    # Get lease/finance payments from VDPs
    to_db = []
    c.execute('SELECT vdp_url, stock FROM masterInventory WHERE vdp_url IS NOT NULL')
    results = c.fetchall()

    for i, r in enumerate(results):

        print('Vehicle #{}/{}\n'.format(str(i + 1), len(results)))
        vdp_url = r[0]
        stock = r[1]
        print('VDP URL:', vdp_url)
        print('Stock:', stock)
        print('\n')

        # temporary. delete once this car gets figured out.. maybe wrong vin.
        if stock == '187240F':
            continue

        # try:
        #     page = requests.get(vdp_url)
        # except requests.exceptions.MissingSchema as error:
        #     print('Invalid URL ERROR:', error)

        page = requests.get(vdp_url)
        tree = html.fromstring(page.content)
        finance_payment = tree.xpath('//span[@if="subject.mathBoxData.finance.paymentInfo.displayValue"]/text()')
        lease_payment = tree.xpath('//span[@if="subject.mathBoxData.lease.paymentInfo.displayValue"]/text()')

        if finance_payment:
            finance_payment = int(finance_payment[0].replace('/mo', '').replace('$', ''))
            finance_description = tree.xpath('//div[contains(@class, "finance-price")]//div[@itemprop="description"]/p/text()')
            finance_description = finance_description[0]
            print('finance_description:', finance_description)
            finance_expiration_start_index = finance_description.find('expires on ') + len('expires on ')
            finance_expiration_end_index = finance_description.find('.', finance_expiration_start_index)
            finance_expiration = finance_description[finance_expiration_start_index: finance_expiration_end_index]
            finance_expiration = finance_expiration.split('/')
            finance_expiration = '{}/{}/{}'.format(finance_expiration[2], finance_expiration[0], finance_expiration[1])
            #down_payment_index = finance_description.find('down payment') - 11
            down_payment_start_index = finance_description.find('months with ') + len('months with ')
            down_payment_end_index = finance_description.find(' down payment')
            finance_down_payment = finance_description[down_payment_start_index: down_payment_end_index]
            finance_down_payment = finance_down_payment.replace(' ', '').replace('$', '').replace(',', '')
            print(finance_down_payment)
            finance_down_payment = int(finance_down_payment)
            finance_term_length_index = finance_description.find('months with') - 3
            finance_term_length = int(finance_description[finance_term_length_index: finance_term_length_index+2])
            finance_apr_start_index = finance_description.find(' per month at ') + len(' per month at ')
            finance_apr_end_index = finance_description.find(' APR')
            finance_apr = finance_description[finance_apr_start_index: finance_apr_end_index]
            finance_apr = float(finance_apr.replace('%', ''))
        else:
            finance_payment = None
            finance_expiration = None
            finance_down_payment = None
            finance_term_length = None
            finance_apr = None

        if lease_payment:
            lease_payment = int(lease_payment[0].replace('/mo', '').replace('$', ''))
            lease_description = tree.xpath('//div[contains(@class, "lease-price")]//div[@itemprop="description"]/p/text()')
            lease_description = lease_description[0]
            print('lease_description:', lease_description)
            lease_expiration_start_index = lease_description.find('expires on ') + len('expires on ')
            lease_expiration_end_index = lease_description.find('.', lease_expiration_start_index)
            lease_expiration = lease_description[lease_expiration_start_index: lease_expiration_end_index]
            lease_expiration = lease_expiration.split('/')
            lease_expiration = '{}/{}/{}'.format(lease_expiration[2], lease_expiration[0], lease_expiration[1])
            das_start_index = lease_description.find('due at signing') - 8
            das_end_index = das_start_index + 8
            lease_das = lease_description[das_start_index: das_end_index]
            lease_das = lease_das.replace(' ', '').replace('$', '').replace(',', '')
            print('lease_das:', lease_das)
            lease_das = int(lease_das)
        else:
            lease_payment = None
            lease_expiration = None
            lease_das = None

        # print('VDP URL:', vdp_url)
        print('Finance Payment:', finance_payment)
        print('Finance Expiration:', finance_expiration)
        print('Finance Down Payment:', finance_down_payment)
        print('Finance Term Length:', finance_term_length)
        print('Finance APR:', finance_apr)
        print('\n')
        print('Lease Payment:', lease_payment)
        print('Lease Expiration:', lease_expiration)
        print('Lease DAS:', lease_das)
        print('\n')

        # Get rebate information
        total_conditional_rebates = 0
        total_unconditional_rebates = 0

        unconditional_rebates = tree.xpath('//div[contains(@class, "cash-price")]//li[@if="incentives"]/span[@itemprop="price"]/@value')
        conditional_rebates = tree.xpath('//div[contains(@class, "cash-price")]//ul[@class="conditional-offers"]//span[@itemprop="price"]/text()')

        for u in unconditional_rebates:
            total_unconditional_rebates += int(u)

        # Combine all conditional rebates (skipping for now because so many that don't stack)
        # for rebate in conditional_rebates:
        #     rebate = int(rebate.replace('- $', '').replace(',', ''))
        #     total_conditional_rebates += rebate

        # Take biggest conditional rebate and use it as total conditional rebates
        if conditional_rebates:
            for j, rebate in enumerate(conditional_rebates):
                conditional_rebates[j] = int(rebate.replace('- $', '').replace(',', ''))
            total_conditional_rebates = max(conditional_rebates)

        print('Total Unconditional Rebates:', total_unconditional_rebates)
        print('Total Conditional Rebates:', total_conditional_rebates)
        print('\n\n')

        to_db.append((
            finance_payment,
            finance_down_payment,
            finance_expiration,
            finance_term_length,
            finance_apr,
            lease_payment,
            lease_das,
            lease_expiration,
            total_unconditional_rebates,
            total_conditional_rebates,
            vdp_url
        ))

    # Add payments to database
    query = ('UPDATE masterInventory '
             'SET finance_payment = ?, finance_down_payment = ?, finance_expiration = ?, finance_term_length = ?, finance_apr = ?, leasePayment = ?, lease_due_at_signing = ?, leaseRebateExpiration = ?, intTotalRebates = ?, totalConditionalRebates = ? '
             'WHERE vdp_url = ?')

    c.executemany(query, to_db)

    # Close connection to database
    conn.commit()
    conn.close()


def main():
    scrape_cdk()




if __name__ == '__main__':

    main()
