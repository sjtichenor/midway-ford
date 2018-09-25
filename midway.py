import csv
import string
import ftplib
import math
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
from lxml import html
import requests
import sys
import midwords
import facebook
import hd_images
import adwords_feeds
import sheets
import random
import sales_specials
import scrape
from pprint import pprint
from pyvirtualdisplay import Display
import locale

locale.setlocale(locale.LC_ALL, 'en_US.utf8')




# Misc stuff


def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
def start_chromedriver():

    display = Display(visible=0, size=(800, 800))
    display.start()

    path_to_chromedriver = 'chromedriver'
    browser = webdriver.Chrome(executable_path=path_to_chromedriver)

    return browser

# FMC Dealer Scrapes
def randomInterval(): #returns random float roughly between 1.5 and 2.75
    return 1.75+1*random.random()-.25*random.random()
def switchDefaultSearch(browser) : # Switch between MyLot/States
    #Switch default search back to Dealership Proximity
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
    elif 'States' in currentSetting :
        print('Switching default search from States to My Lot')
        browser.find_element_by_xpath('//select[@id="searchSettingsDefaultSearchMode"]').click()
        time.sleep(2)
        browser.find_element_by_xpath('//option[@value="1"]').click()
        time.sleep(2)
    currentSetting = tree.xpath('//option[@selected]/text()')
    #print('Setting After:', currentSetting)   This doesn't work..
    
    
    browser.find_element_by_xpath('//a[@id="saveSearchSettings"]').click()
    time.sleep(2)
    browser.get('https://www.vlplus.dealerconnection.com/Search?&searchType=quicksearch')
    time.sleep(2)
    print('Finished switching default search...')
    return browser
def getVinList() :
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    vinList = []
    c.execute('SELECT vin FROM masterInventory where invType = ?', ('New',))
    vinTupleList = c.fetchall()
    for vinTuple in vinTupleList :
        vin = vinTuple[0]
        vinList.append(vin)
    numVehicles = len(vinList)
    
    conn.commit()
    conn.close()
    
    return vinList
def fmcLogin(browser) :  #Logs into fmcdealer and returns browser
    
    # Fire up ChomeDriver
    # path_to_chromedriver = '/Users/spencertichenor/PycharmProjects/midway/chromedriver'
    # browser = webdriver.Chrome(executable_path = path_to_chromedriver)
    
    # Log into FMC Dealer
    url = 'https://fmcdealer.com'
    browser.get(url)
    username = browser.find_element_by_id('DEALER-WSLXloginUserIdInput')
    password = browser.find_element_by_id('DEALER-WSLXloginPasswordInput')
    username.send_keys('t-spen29')
    password.send_keys('Tichenor5')
    browser.find_element_by_xpath('//div[@id="DEALER-WSLXloginWSLSubmitButton"]/input').click()
    time.sleep(5)
    
    return browser
def navigateToVincent(browser, vin) :
    print('\nNavigating to Vincent page for VIN: ' + vin + '...\n\n')
    

    #print('\nSearching for rebate info for vehicle ' + str(k+1) + '/' + str(len(vinList)) + '...')
    #print('\n\tVIN: ' + vin + '\n')
    browser.get('https://www.vlplus.dealerconnection.com/Search?&searchType=quicksearch')
    time.sleep(3)
    try :
        vinField = browser.find_element_by_id('txtVIN')
        vinField.send_keys(vin)
        browser.find_element_by_xpath('//input[@value="Search"]').click()
        time.sleep(2)
    except :
        print('VIN FIELD ERROR:')
        print(sys.exc_info()[0])
        #errorList.append(vin)
        #pass    this was pass but i think it should be return
        return browser
    
    source = browser.page_source
    if 'Please broaden your search.' not in source : # Check if vehicle was not found in dealership proximity search
    
        # Click on Vincent button
        #source = browser.page_source

        try :
            vincentUrl = vincentUrl[0]
            browser.get(vincentUrl)
            time.sleep(4)
        except :
            print('Vincent Url Error:')
            print(sys.exc_info()[0])
            #errorList.append(vin)
            #pass
            return browser
    
        
        source = browser.page_source
        tree = html.fromstring(source)
        if 'Please click the "Close" button to continue with the Sales Process.' in source : # Check for recall warning
            browser.find_element_by_xpath('//input[@value="Close"]').click()
            time.sleep(2)
        
        if 'value="Certificate Inquiry"' not in source : # Check if vehicle already sold
        
            # Enter ZIP code and click next
            try :
                zipField = browser.find_element_by_xpath('//div/input[@name="customerZip"]')
                zipField.send_keys('55113')
                browser.find_element_by_id('primaryButtonId').click()
                time.sleep(2)
            except :
                print('ZIP FIELD ERROR:')
                print(sys.exc_info()[0])
                #errorList.append(vin)
                pass
    
            # Get rebate info
            
            #rebateInfo = scrapeRebateInfo(browser)
            
        else :
            #soldList.append(vin)
            print('\tIt looks like this vehicle has already been sold.\n\n')
    else : # Vehicle not found in Dealership Proximity search
        print('\tVehicle not found after searching Dealership Proximity.')
        
        #Switch default search to My Lot
        browser = switchDefaultSearch(browser)
        try :
            vinField = browser.find_element_by_id('txtVIN')
            vinField.send_keys(vin)
            browser.find_element_by_xpath('//input[@value="Search"]').click()
            time.sleep(2)
        except :
            #errorList.append(vin)
            print('VIN FIELD ERROR:')
            print(sys.exc_info()[0])
            #switchToProximity(browser)
            return browser
        
        
        
        # Click on Vincent button
        source = browser.page_source
        tree = html.fromstring(source)
        vincentUrl = tree.xpath('//a[@title="Smart Vincent"]/@href')
        try :
            vincentUrl = vincentUrl[0]
            browser.get(vincentUrl)
            time.sleep(4)
        except :
            #errorList.append(vin)
            print('Vincent Url Error:')
            print(sys.exc_info()[0])
            #switchToProximity(browser)
            #return browser
    
        
        source = browser.page_source
        tree = html.fromstring(source)
        if 'Please click the "Close" button to continue with the Sales Process.' in source : # Check for recall warning
            browser.find_element_by_xpath('//input[@value="Close"]').click()
            time.sleep(2)
        
        if 'value="Certificate Inquiry"' not in source : # Check if vehicle already sold
        
            # Enter ZIP code and click next
            try :
                zipField = browser.find_element_by_xpath('//div/input[@name="customerZip"]')
                zipField.send_keys('55113')
                browser.find_element_by_id('primaryButtonId').click()
                time.sleep(2)
            except :
                #errorList.append(vin)
                print('ZIP FIELD ERROR:')
                print(sys.exc_info()[0])
                #switchToProximity(browser)
                #return browser
    
            # Get rebate info
            #rebateInfo = scrapeRebateInfo(browser)
            
            
            
        else :
            #soldList.append(vin)
            print('\tIt looks like this vehicle has already been sold.\n\n')
        
        #Switch default search back to Dealership Proximity
        #switchToProximity(browser)
        #pass
    

    return browser
    
    
    
            
            
            
            
    # print('\nNumber of vehicles appear to have been sold: ' + str(len(soldList)))
    # print('Sold List:')
    # print(soldList)
    # print('\nNumber of vehicles that ran into errors: ' + str(len(errorList)))
    # print('Error List:')
    # print(errorList)
    #print('\n\nFinished getting rebate information.')
def scrapeRebateInfo(page_source) : #input browser of vincent page, return tuple with unconditional rebate info
    
    
    # Get rebate info
    #source = browser.page_source
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
    
    if rowspans == [] : # No unconditional rebates
        print('No rebates found for this vehicle.\n')
        print('Updating rebate info...')
        while len(to_db) < 43 :
            to_db += (None,)
    else : # Yah, it has unconditional rebates
        # Clean up Condition info
        condition = conditions[0]
        condition = condition.replace('\n', '').replace('\t', '').replace('  ', '').replace(':C', ': C')
        condition = condition[1:]
        condition = removeWeirdChars(condition)
        if 'Cash Payment' in condition :
            print('\tUnconditional Rebates:\n')
            i=0
            for i in range(i, int(rowspans[0])) :
                num = nums[i].replace('\n', '').replace('\t', '').replace('  ', '')
                name = names[i*2+1].replace('\n', '').replace('\t', '').replace(' - ', '').replace('s  C', 's C').replace('  ', '').replace('"', '')
                amount = amounts[i].replace('\n', '').replace('\t', '').replace('  ', '')
                expiration = expirations[i].replace('\n', '').replace('\t', '').replace('  ', '')
                if 'SIRIUS' in name : #Fix for the stupid 6-month extra Sirius incentive
                    amount = '$0'
                if ' - ' not in amount and 'Amount Not Available' not in amount : # stupid fix for Oct 2016 rebate and anotehr fix for Dec 2016 rebate
                    print('\t\tProgram: #' + num)
                    print('\t\tName: ' + name)
                    print('\t\tAmount: ' + amount)
                    print('\t\tExpiration: ' + expiration + '\n')
                    to_db += (num,) + (name,) + (condition,) + (amount,) + (expiration,) + (condition,) #fix double header
            while len(to_db) < 43 :
                to_db += (None,)
                
    return to_db
    time.sleep(2)
def scrapeLeaseInfo(page_source) : 
    
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
    #rclRebateRow = tree.xpath('//tr[td[contains(., "RCL Customer Cash")]]/td/text()')
    rclFactorsRow = tree.xpath('//tr[td[contains(., "RCL Factors")]]/td/text()')
    rclTermLengths = tree.xpath('//tr[td[contains(., "RCL Factors")]]//th/text()')
    rclFactors = tree.xpath('//tr[td[contains(., "RCL Factors")]]//td/text()')
    rebateCells = tree.xpath('//tr[td[contains(., "LEASE")]]/following-sibling::*/td/text()')
    #print('rebateCells:', rebateCells)
    #print('length of rebateCells:', len(rebateCells))
    
    
    
    
    if rebateCells != [] :
        print('Lease Rebates:')
        
        rebateDict = {}
        for i, cell in enumerate(rebateCells) :
            if 'Cash' in cell and 'Fast Cash Certificate' not in cell:
                rebateName = cell.replace('\t', '').replace('\n', '').replace(' - ', '')
                if '$' in rebateCells[i+2] :
                    rebateAmount = int(rebateCells[i+2].replace('\t', '').replace('\n', '').replace(' ', '').replace('$', '').replace(',', ''))
                    rebateExpiration = rebateCells[i+3].replace('\t', '').replace('\n', '').replace(' ', '')
                elif '$' in rebateCells[i+3] :
                    rebateAmount = int(rebateCells[i+3].replace('\t', '').replace('\n', '').replace(' ', '').replace('$', '').replace(',', ''))
                    rebateExpiration = rebateCells[i+4].replace('\t', '').replace('\n', '').replace(' ', '')
            
            
                rebateDict[rebateName] = [rebateAmount, rebateExpiration]
                print('\tRebate Name:', rebateName)
                print('\tRebate Amount:', rebateAmount)
                print('\tRebate Expiration:', rebateExpiration)
                print('\n')
    
        print('rebateDict:', rebateDict)
    
        totalRebates = 0
        for rebateName in rebateDict :
            totalRebates += rebateDict[rebateName][0]
        
        
        
        
        vehDesc = vehDesc[0].replace('\xa0', ' ').replace('\t', '').replace('\n', '')
        rclResiduals =  {}
        for i, leaseTerm in enumerate(residualTable[0:4]) :
            rclResiduals[leaseTerm + ' Month'] = float(residualTable[i+5])/100
        
        #rclRebateName = rclRebateRow[5].replace('\t', '').replace('\n', '').replace(' - ', '')
        #rclRebateAmount = rclRebateRow[8].replace('\t', '').replace('\n', '').replace(' ', '').replace('$', '').replace(',', '')
        #rclRebateExpiration = rclRebateRow[9].replace('\t', '').replace('\n', '').replace(' ', '')
        
        rclTermLengths = rclTermLengths[:-1]
        for i, termLength in enumerate(rclTermLengths) :
            rclTermLengths[i] = int(termLength)
        
        rclFactorsExpiration = rclFactorsRow[8].replace('\t', '').replace('\n', '').replace(' ', '')
        
        
        factors = {}
        for e in rclFactors :
            if 'Tier' in e :
                tierIndex = rclFactors.index(e)
                tier = rclFactors[tierIndex]
                tierFactors = rclFactors[tierIndex+1:tierIndex+5]
                for i, factor in enumerate(tierFactors) :
                    tierFactors[i] = float(factor)
                factors[tier] = tierFactors
        
        print('VIN:', vin)
        print('Vehicle Description:', vehDesc)
        #print('RCL Rebate Name:', rclRebateName)
        print('Total Rebates:', totalRebates)
        #print('RCL Rebate Expiration:', rclRebateExpiration)
        print('RCL Lengths:', rclTermLengths)
        print('RCL Factors: ', factors) #used to be factors but too hard to deal with everything
        print('RCL Factors Expiration:', rclFactorsExpiration)
        print('RCL Residual:', rclResiduals)
        
        
        c.execute('SELECT stock, year, model, vehTrim FROM masterInventory WHERE vin = ?', (vin,))
        vehInfo = c.fetchall()
        vehInfo = vehInfo[0]
        print('vehInfo:', vehInfo)
        
        to_db = (vin,) + vehInfo + (str(rebateDict), totalRebates, str(rclTermLengths), str(factors), rclFactorsExpiration, str(rclResiduals))
        #to_db = (vin, str(rebateDict), totalRebates, str(rclTermLengths), str(factors), rclFactorsExpiration, str(rclResiduals))
    
    
    else :
        print('No lease info found.')
        to_db = (vin, None, None, None, None, None, None, None, None, None, None)
    
    # Close connection to database
    conn.commit()
    conn.close()
            
    return to_db
    time.sleep(2)


def calculateLeasePayment(vin, termLength, mileage, tier) : # outputs monthly payments. input example: ('1FAHP1231', 36, 15000, 'Tier 0-1')
    
    print('Calculating lease payments for VIN: ' + vin)
    leaseParameters = getLeaseParameters(vin)
    #print('leaseParameters:', leaseParameters)
    
    if leaseParameters[5] == None : # if there are no lease deals
        paymentOptions = (None, None, None, None, None, vin)
    else : 
        msrp = leaseParameters[0]
        dealerDiscount = leaseParameters[1]
        rebateAmount = leaseParameters[2]
        termLengths = leaseParameters[3]
        interestRates = leaseParameters[4]
        residuals = leaseParameters[5]
    
        termLengthIndex = termLengths.index(termLength)
        apr = interestRates[tier][termLengthIndex]
        apr += 1 # Juicing the apr by 1%
        residual = residuals[str(termLength) + ' Month']
    
    
    
        # Adjust residual for mileage
        residual += (15000 - mileage)/1500 * .01
        residual = round(residual, 2)
    
        taxRate = .07125  # plus any local taxes i guess
        aquisitionFee = 645  # need to figure out better way
        moneyFactor = apr/2400
    
        salesTax = round(msrp * taxRate, 2)  # dunno if this should be here
        salesTax = 0
        signAndDrive = 0 - aquisitionFee - salesTax
    
        downPayments = [signAndDrive, 0, 1000, 2000, 3000]
    
        print('MSRP:', msrp)
        print('Dealer Discount:', dealerDiscount)
        print('Rebate Amount:', rebateAmount)
        print('Term Length:', str(termLength) + ' Month')
        print('APR:', apr)
        print('Money Factor:', moneyFactor)
        print('Residual:', residual)
        print('\n\n')
    
    
        paymentOptions = ()
        for downPayment in downPayments :
    
            sellingPrice = msrp - dealerDiscount - rebateAmount
    
            #taxableAmount = sellingPrice - residualValue - downPayment + rentCharge   # not accurate
            #salesTax = msrp * taxRate
            #salesTax = 0
            
            grossCapCost = msrp - dealerDiscount + aquisitionFee + salesTax
            capCostReduction = rebateAmount + downPayment
            netCapCost = round(grossCapCost - capCostReduction, 2)
            residualValue = round(msrp * residual, 2)
            depreciation = round(netCapCost - residualValue, 2)
    
            basePayment = round(depreciation/termLength, 2)
            rentPayment = round((netCapCost + residualValue) * moneyFactor, 2)
            rentCharge = rentPayment*termLength
            totalPayment = round(basePayment + rentPayment, 2)
        
        
        
            print('Down Payment:', downPayment)
            print('\n')
            print('Gross Cap. Cost:', grossCapCost)
            print('Cap. Cost Reduction:', capCostReduction)
            print('Net Cap. Cost:', netCapCost)
            print('Residual Value:', residualValue)
            print('Depreciation:', depreciation)
            print('Base Payment:', basePayment)
            print('Rent Payment:', rentPayment)
            print('Total Monthly Payment:', totalPayment)
            print('\n\n\n')
        
            paymentOptions += (totalPayment,)
        paymentOptions += (vin,)
    #print('Payment Options:', paymentOptions)
    return paymentOptions
def scrapeFMC(): # Gets rebate and lease info from FMC Dealer
    vinList = getVinList()
    #vinList = ['3FA6P0VP1HR195216', '3FA6P0H77HR187150']

    #path_to_chromedriver = 'chromedriver'
    #browser = webdriver.Chrome(executable_path=path_to_chromedriver)
    browser = start_chromedriver()
    browser = fmcLogin(browser)
    
    errorList = []
    for i, vin in enumerate(vinList) :
        print('Vehicle ' + str(i+1) + '/' + str(len(vinList)) + ':\n')
        browser = navigateToVincent(browser, vin)
        try :
            to_db = scrapeRebateInfo(browser.page_source)
            updateRebateTable(to_db)
            to_db = scrapeLeaseInfo(browser.page_source)
            updateLeaseTable(to_db)
            #to_db = calculateLeasePayment(vin, 36, 10500, 'Tier 0-1')
            #updateLeaseTable(to_db)
        except Exception as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            message += '\nError on line {}'.format(sys.exc_info()[-1].tb_lineno)
            print(message)
            errorList.append(vin)
            continue
    print('Error List:', errorList)
    print('Number of Errors:', len(errorList))
    doubleErrorList = []
    for i, vin in enumerate(errorList) : # Re-run all VINs that had errors
        print('Vehicle ' + str(i+1) + '/' + str(len(errorList)) + ':\n')
        browser = navigateToVincent(browser, vin)
        try :
            to_db = scrapeRebateInfo(browser.page_source)
            updateRebateTable(to_db)
            to_db = scrapeLeaseInfo(browser.page_source)
            updateLeaseTable(to_db)
        except Exception as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            message += '\nError on line {}'.format(sys.exc_info()[-1].tb_lineno)
            print(message)
            doubleErrorList.append(vin)
            continue
    print('Double Error List:', errorList)
    print('Number of Double Errors:', len(errorList))
    
    
    print(20*'\n')

def updateVLPlusInventoryTable():
    print('Scraping Vehicle Locator..')

    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()


    # Delete old data
    query = 'DELETE FROM VLPlusInventory'
    c.execute(query)


    # all the xpath that we're gonna need
    vin_list_xpath = '//tr[contains(@class, "vehiclerow")]/@vin'
    msrp_list_xpath = '//td[contains(@class, "price")]/a[@class="pdfWindowSticker"]/span/text()'
    invoice_list_xpath = '//tr[contains(@class, "vehiclerow")]/td[11]/a/span/text()'
    pep_list_xpath = '//tr[contains(@class, "vehiclerow")]/td[7]/span[3]/text()'
    order_type_list_xpath = '//a[@onclick="showOrderTypeInfo();"]/span/text()'
    engine_list_xpath = '//tr[contains(@class, "vehiclerow")]/td[8]/span[1]/text()'
    status_list_xpath = '//tr[contains(@class, "vehiclerow")]/td[1]/@class'

    # Log into FMC Dealer
    #path_to_chromedriver = 'chromedriver'
    #browser = webdriver.Chrome(executable_path=path_to_chromedriver)
    browser = start_chromedriver()
    browser = fmcLogin(browser)
    wait = WebDriverWait(browser, 10)

    browser.get('https://www.vlplus.dealerconnection.com/InvMgt/')
    time.sleep(randomInterval() * 2)
    source = browser.page_source
    tree = html.fromstring(source)
    vehicle_count = tree.xpath('//th[@class="resultcount"]/text()')
    print(vehicle_count)
    vehicle_count = vehicle_count[1].split(' ')
    vehicle_count_index = vehicle_count.index('vehicles') - 1
    vehicle_count = vehicle_count[vehicle_count_index]
    vehicle_count = int(vehicle_count)
    page_count = math.ceil(vehicle_count/25)
    print('Total pages:', page_count)

    for j in range(0, page_count-1):
        tree = html.fromstring(browser.page_source)
        vin_list = tree.xpath(vin_list_xpath)
        ugly_msrp_list = tree.xpath(msrp_list_xpath)
        ugly_invoice_list = tree.xpath(invoice_list_xpath)
        ugly_pep_list = tree.xpath(pep_list_xpath)
        ugly_order_type_list = tree.xpath(order_type_list_xpath)
        ugly_engine_list = tree.xpath(engine_list_xpath)
        ugly_status_list = tree.xpath(status_list_xpath)

        # Clean up PEP Codes
        msrp_list = []
        invoice_list = []
        pep_list = []
        order_type_list = []
        engine_list = []
        status_list = []
        for k in range(0, len(vin_list)):

            msrp_list.append(ugly_msrp_list[k].replace('$', '').replace(',', ''))
            if msrp_list[k] != 'n/a':
                msrp_list[k] = int(msrp_list[k])
            else:
                msrp_list[k] = ''
            invoice_list.append(ugly_invoice_list[k].replace('$', '').replace(',', ''))
            if invoice_list[k] != 'n/a':
                invoice_list[k] = int(invoice_list[k])
            else:
                invoice_list[k] = ''


        for pep_code in ugly_pep_list:
            pep_list.append(pep_code)


        for order_type in ugly_order_type_list:
            order_type_list.append(order_type)

        for engine in ugly_engine_list:
            engine = engine.split('<br>')[0].replace('  ', '').replace('\n', '')
            if 'L ' in engine and 'SPD' not in engine and 'SPEED' not in engine:
                engine_list.append(engine)

        for status in ugly_status_list:
            if 'transit' in status:
                status_list.append('In Transit')
            elif 'plant' in status:
                status_list.append('In Plant')
            else:
                status_list.append('In Stock')

        if len(msrp_list) != len(invoice_list):
            print('len msrp != invoice')
            raise ValueError
        if len(pep_list) != len(msrp_list):
            print('len pep != msrp')
            print(msrp_list)
            print(ugly_pep_list)
            raise ValueError



        print('msrp_list len: ', len(msrp_list))
        print('msrp_list: ', msrp_list)
        print('invoice_list: ', invoice_list)
        print('pep_list: ', pep_list)
        print('order_type_list: ', order_type_list)
        print('engine_list: ', engine_list)
        print('status_list: ', status_list)


        to_db = []
        for k, vin in enumerate(vin_list):
            print('VIN: ', vin)
            print('msrp: ', msrp_list[k])
            print('invoice: ', invoice_list[k])
            print('pep: ', pep_list[k])
            print('order_type: ', order_type_list[k])
            print('engine: ', engine_list[k], '\n')
            if msrp_list[k] < invoice_list[k]:
                raise ValueError
            to_db.append((vin, msrp_list[k], invoice_list[k], pep_list[k], order_type_list[k], engine_list[k], status_list[k]))
        query = 'INSERT OR REPLACE INTO VLPlusInventory (vin, msrp, invoice, pepCode, orderType, engine, status) VALUES (?, ?, ?, ?, ?, ?, ?)'
        c.executemany(query, to_db)
        conn.commit()


        time.sleep(randomInterval())
        next_page_xpath = '//a[@page="{}"]'.format(str(j+2))
        next_page_link = wait.until(EC.element_to_be_clickable((By.XPATH, next_page_xpath)))
        next_page_link.click()

        #browser.find_element_by_xpath(next_page_xpath).click()
        time.sleep(randomInterval()*2)


    conn.close()
def updateMasterInventoryStockStatus():
    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # Get all vin in master inv
    query = 'SELECT vin FROM masterInventory'
    c.execute(query)
    master_results = c.fetchall()
    master_vin_list = []
    for r in master_results:
        master_vin_list.append(r[0])

    # Get all retail veh in vlplus inv
    query = 'SELECT vin, status FROM VLPlusInventory WHERE orderType = ? OR orderType = ?'
    to_db = ('1', '2')
    c.execute(query, to_db)
    vlplus_results = c.fetchall()

    for r in vlplus_results:
        vin = r[0]
        vlpus_status = r[1]
        print('\n', vin, ':\n\n')
        if vin in master_vin_list:
            query = 'SELECT status, dateInStock FROM masterInventory WHERE vin = ?'
            to_db = (vin,)
            c.execute(query, to_db)
            result = c.fetchall()
            master_status = result[0][0]
            date_in_stock = result[0][1]
            print(master_status)
            if date_in_stock and master_status == 'In Stock':
                print('Stock status already set')
                continue
            elif date_in_stock and master_status != 'In Stock':
                print('Updating stock status')
                query = 'UPDATE masterInventory SET status = ? WHERE vin = ?'
                to_db = ('In Stock', vin)
                c.execute(query, to_db)

        else:
            print('Adding veh to master')
            query = 'INSERT OR REPLACE INTO masterInventory (vin, status, invType) VALUES (?, ?, ?)'
            to_db = (vin, vlpus_status, 'New')
            c.execute(query, to_db)






    conn.commit()
    conn.close()


# Data stuff

def get_incoming_homenet_file():  # Logs into Homenet FTP server and downloads inventory file
    print('Getting CSV file from Homenet feed...')
    #autouplinkFilePath = 'spencertichenor.com/home/sjtichenor/public_ftp/incoming/RosevilleMidwayFord' + YEAR + MO + DAY
    ftp = ftplib.FTP('spencertichenor.com')
    ftp.login(user='ftpbot@spencertichenor.com', passwd='M4lonePovolny')
    homenetFileName = 'homenet_feed.csv'
    localFilePath = 'data/local_homenet_file.csv'
    localFile = open(localFilePath, 'wb')
    ftp.retrbinary('RETR ' + homenetFileName, localFile.write, 1024)
    print('CSV file from Homenet feed saved at:  data/local_homenet_file.csv')
    ftp.quit()
    localFile.close()
def update_incoming_homenet_table(): # Gets data from local_homenet_file.csv then updates homenetInventory and masterInventory tables
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    print('Updating homenetInventory table with data sent from Homenet FTP feed...')
    with open('data/local_homenet_file.csv', 'r') as homenetFile:
        # csv.DictReader uses first line in file for column headings by default
        dr = csv.DictReader(homenetFile) # comma is default delimiter
        to_db = []
        homenetVinList = []
        
        
        ## Clean out weird characters
        
        valid_chars = string.ascii_letters + string.digits + ' ' + ':' + '-' + ',' + '&' + '$' + '/' + '.' + '_' + '!'
        for i in dr:
            for key in i.keys():
                s = i[key]
                clean = ''.join(c for c in s if c in valid_chars)
                i[key] = clean
                #print(key + ': ' + i[key])
            #print('\n' + 50*'*' + '\n')
            
            to_db.append((
                i['VIN'],
                i['Stock'],
                i['Type'],
                i['Year'],
                i['Make'],
                i['Model'],
                i['Trim'],
                i['Body'],
                i['MSRP'],
                i['SellingPrice'],
                i['InternetPrice'],
                i['Invoice'],
                i['BookValue'],
                i['Certified'],
                i['ModelNumber'],
                i['Doors'],
                i['ExteriorColor'],
                i['InteriorColor'],
                i['EngineCylinders'],
                i['EngineDisplacement'],
                i['Transmission'],
                i['Miles'],
                i['DateInStock'],
                i['Description'],
                i['Options'],
                i['Categorized Options'],
                i['ImageList'],
                i['Style Description'],
                i['Drive type'],
                i['Wheelbase Code'],
                i['Engine Description'],
                i['Market Class'],
                i['Factory_Codes']
            ))
            
            homenetVinList.append(i['VIN']) #used later to delete vehicles that aren't in stock anymore, index of 0 because it is a tuple

    query = ("""
        INSERT OR REPLACE INTO homenetInventory (vin, stock, invType, year, make, model, vehTrim, cabStyle, intMSRP, intPrice, intInternetPrice, intInvoice, intGeneralLedger, cpo, modelNumber, doors, exteriorColor, interiorColor, engineCylinders, engineDisplacement, transmission, miles, dateInStock, description, options, optionsCategorized, imageUrls, style, drive, wheelbase, engine, marketClass, factCodes) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
    c.executemany(query, to_db)
    #c.executemany("INSERT OR REPLACE INTO masterInventory (vin, stock, invType, year, make, model, vehTrim, cabStyle, intMSRP, intPrice, intInternetPrice, intInvoice, intGeneralLedger, cpo, modelNumber, doors, exteriorColor, interiorColor, engineCylinders, engineDisplacement, transmission, miles, dateInStock, description, options, optionsCategorized, imageUrls, style, drive, wheelbase, engine, marketClass, factCodes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", to_db)
    # that was redundent i think ^^


    # Delete vehicles that aren't in stock anymore from Homenet table
    
    currentVinList = []
    c.execute('SELECT vin FROM homenetInventory')
    tupleVinList = c.fetchall()
    for tupleVin in tupleVinList: # Convert tuples to strings in order to compare later
        vin = tupleVin[0]
        currentVinList.append(vin)
    for vin in currentVinList:
        if vin not in homenetVinList:
            c.execute('DELETE FROM homenetInventory WHERE vin = ?', (vin,))
            print('Deleted VIN ' + vin + ' from Homenet Inventory Table.')
    conn.commit()
    print('Finished updating homenetInventory table.\n')
    
    # Update masterInventory table
    print('Updating masterInventory table with data from homenetInventory table...')
    query = 'INSERT OR REPLACE INTO masterInventory (vin, stock, invType, year, make, model, vehTrim, cabStyle, intMSRP, intPrice, intInternetPrice, intInvoice, intGeneralLedger, cpo, modelNumber, doors, exteriorColor, interiorColor, engineCylinders, engineDisplacement, transmission, miles, dateInStock, description, options, optionsCategorized, imageUrls, style, drive, wheelbase, engine, marketClass, factCodes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    c.executemany(query, to_db)
    c.execute('SELECT vin from masterInventory')
    masterVinTupleList = c.fetchall()
    for vinTuple in masterVinTupleList:
        vin = vinTuple[0]
        if vin not in homenetVinList:
            c.execute('DELETE FROM masterInventory WHERE vin = ?', (vin,))
            print('Deleted VIN ' + vin + ' from Master Inventory Table.')
    conn.commit()
    conn.close()
def updateMasterTable() :
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM homenetInventory')
    vehTupleList = c.fetchall()
    to_db = vehTupleList
    print(to_db)
    print(len(to_db))
    for i in to_db:
        print(i)
        print(len(i))
    c.executemany("INSERT OR REPLACE INTO masterInventory (vin, stock, invType, year, make, model, vehTrim, bodyStyle, intMSRP, intPrice, intInternetPrice, intInvoice, intGeneralLedger, cpo, modelNumber, doors, exteriorColor, interiorColor, engineCylinders, engineDisplacement, transmission, miles, dateinStock, description, options, optionsCategorized, imageUrls) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", to_db)
    conn.commit()
    
    
    
    
    # Delete vehicles that are no longer in stock from masterInventory
    
    homenetVinList = []
    c.execute('SELECT vin from homenetInventory')
    homenetVinTupleList = c.fetchall()
    for homenetVinTuple in homenetVinTupleList :
        homenetVin = homenetVinTuple[0]
        homenetVinList.append(homenetVin)
    c.execute('SELECT vin from masterInventory')
    masterVinTupleList = c.fetchall()
    for vinTuple in masterVinTupleList :
        vin = vinTuple[0]
        if vin not in homenetVinList :
            c.execute('DELETE FROM masterInventory WHERE vin = ?', (vin,))
            print('Deleted VIN ' + vin + ' from Master Inventory Table.')
    
    conn.commit()
    conn.close()


def removeOldVins(table): #DOES NOT WORK removes VINs that are no longer in masterInventory from supplied table
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    masterVinList = []
    c.execute('SELECT vin FROM masterInventory')
    masterVinTupleList = c.fetchall()
    for masterVinTuple in masterVinTupleList :
        vin = masterVinTuple[0]
        masterVinList.append(vin)
    c.execute('SELECT vin FROM ?', (table,))
    rebateVinTupleList = c.fetchall()
    for rebateVinTuple in rebateVinTupleList :
        vin = rebateVinTuple[0]
        if vin not in masterVinList :
            c.execute('DELETE FROM rebateInfo WHERE vin = ?', (vin,))
            print('\t' + vin + ' deleted from rebateInfo table.')
            
    conn.commit()
    conn.close()


def compute_highlights(): # Gets masterInventory 'options' field for each veh then finds highlights then adds them to highlights column separated by commas
    
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    c.execute('SELECT vin, options, year, invType, description, cpo, engine, drive, stock, make, model, marketClass FROM masterInventory')
    optionsTupleList = c.fetchall()
    for optionsTuple in optionsTupleList:
        highlightList = []
        highlightStr = ''
        vin = optionsTuple[0]
        options = optionsTuple[1].lower()
        year = optionsTuple[2]
        invType = optionsTuple[3]
        description = optionsTuple[4].lower()
        cpo = optionsTuple[5]
        engine = optionsTuple[6]
        drive = optionsTuple[7]
        stock = optionsTuple[8]
        make = optionsTuple[9]
        model = optionsTuple[10]
        marketClass = optionsTuple[11]
        
        
        # Get coolest options
        if cpo == 'True':
            highlightList.append('Certified Pre-Owned')
            highlightList.append('100,000-Mile Warranty')
        #if year == 2017 and invType == 'New' :
            #highlightList.append('Apple CarPlay')
            #highlightList.append('Android Auto')
        
        
        # Highlight Idicators - List of dictionaries where the key is the highlight name and the value is a list of indicator phrases
        indicatorList = [
            {'One-Owner': ['one owner', 'one-owner']},
            {'Low Miles': ['low mile']},
            {'Remote Start': ['remote start', 'remote engine start', 'remote auto start']},
            {'Technology Package': ['technology package', 'technology pkg']},
            {'Cold Weather Package': ['cold weather package']},
            {'Appearance Package': ['appearance package']},
            {'Moonroof': ['vista roof', 'moonroof', 'glass roof', 'panoramic roof']},
            {'Rear Camera': ['rear view camera', 'back-up camera', 'rear-view camera']},
            {'Rear Camera w/ Hitch Assist': ['rear view camera w/dynamic hitch assist']},
            {'Heated Seats': ['heated leather', 'heated front seats', 'heated bucket']},
            {'Heated/Cooled Seats': ['heated & cooled', 'heated and cooled', 'heated/cooled']},
            {'Heated Steering Wheel': ['heated steering wheel']},
            {'Heated Mirrors': ['heated mirrors']},
            {'Tow Package': ['tow package', 'Towing', 'Trailer Hitch']},
            {'Trailer Brake Controller': ['trailer brake controller']},
            {'Premium Audio System': ['premium audio system', 'premium 9 speaker']},
            {'Leather Interior': ['leather seats', 'leather-trimmed', 'leather trimmed']},
            {'Bluetooth': ['bluetooth']},
            {'USB Connectivity': ['usb']},
            {'Apple CarPlay': ['apple carplay']},
            {'Android Auto': ['android auto']},
            {'Snow Plow Package': ['snow plow package']},
            {'Lane-Keeping System': ['lane-keeping system']},
            {'Rain-Sensing Wipers': ['rain-sensing wipers']},
            {'Park Assist System': ['park assist system']},
            {'Sirius': ['sirius', 'satellite radio']},
            {'Power Liftgate': ['pwr liftgate', 'power liftgate']},
            {'Remote Tailgate': ['remote tailgate']},
            {'Push Button Start': ['push button start']},
            {'Navigation': ['navigation']},
            {'Bedliner': ['bedliner']},
            {'Extended Range Fuel Tank': ['extended range']},
            {'2nd Row Bucket Seats': ['2nd row bucket seats']},
            {'3rd Row Seat': ['3rd row seat', '3rd seat']},
            {'Touchscreen': ['touchscreen', 'touch-screen', 'myford touch', 'sync 3']},
            {'Keyless Entry': ['keyless', 'keypad entry']},
            {'Cruise Control': ['cruise control']},
            {'Auto Start-Stop Technology': ['auto start-stop technology']},
            {'LED Box Lighting': ['led box lighting']},
        ]
        
        for i in indicatorList:
            highlight = list(i.keys())[0]
            phraseList = list(i.values())[0]
            for phrase in phraseList:
                if phrase in options or phrase in description:
                    highlightList.append(highlight)
                    break
        highlightList.append(engine)
        highlightList.append(drive)
        
        
        
        # Remove redundant highlights
        redundantList = [
            ['Heated Seats', 'Heated/Cooled Seats'],
            ['Rear Camera', 'Rear Camera w/ Hitch Assist'],
            ['USB Connectivity', 'Bluetooth'],
            ['Bluetooth', 'Apple CarPlay'],
            ['Tow Package', 'Trailer Brake Controller']
        ]
        for i in redundantList:
            if i[0] in highlightList and i[1] in highlightList:
                highlightList.remove(i[0])
        
        for highlight in highlightList:
            highlightStr += highlight + ','
        if len(highlightStr) > 0: # Get rid of unnecessary comma on end of string
            highlightStr = highlightStr[:-1]
        
        # Set Body Style (not really a highlight) - Had to switch to ghetto version below because vans were getting marked as cars because iterating throguh dict is not ordered
        # indicatorDict = {
        #     'Car': ['Car'],
        #     'Truck': ['Truck'],
        #     'Van': ['Van', 'van'],
        #     'SUV': ['Sport Utility Vehicles']
        # }
        # bodyStyles = indicatorDict.keys()
        # for bodyStyle in bodyStyles :
        #     for indicator in indicatorDict[bodyStyle] :
        #         if indicator in marketClass :
        #             style = bodyStyle
        
        if 'Car' in marketClass:  # has to come first so cargo van gets listed as Van
            style = 'Car'
        if 'Truck' in marketClass:
            style = 'Truck'
        if 'Van' in marketClass or 'van' in marketClass :
            style = 'Van'
        if 'Sport Utility Vehicles' in marketClass :
            style = 'SUV'
            

        # Clean up Model
        model = model.replace(' Commercial Cutaway', '').replace(' Sport Fleet', '').replace(' Cutaway', '')
        
        # Clean up Engine
        engine = engine.replace(' L', 'L')
        
        print('Vehicle: ' + stock + ' ' + make + ' ' + model)
        print('Highlights:', highlightList)
        print('BodyStyle:', style)
        print('\n')

        # Set Status to In Stock
        status = 'In Stock'
        
        # Update database
        c.execute('UPDATE masterInventory SET highlights = ?, bodyStyle = ?, model = ?, engine = ?, status = ? WHERE vin = ?', (highlightStr, style, model, engine, status, vin,))
        
    conn.commit()
    conn.close()


def calculate_pricing():

    print('Calculating max discount for each vehicle...\n')

    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # Set dealer discount and total discount
    query = ('SELECT vin, intMSRP, intInternetPrice, intTotalRebates, totalConditionalRebates '
             'FROM masterInventory '
             'WHERE invType = "New" AND intMSRP != 0')
    c.execute(query)
    results = c.fetchall()
    for r in results:
        print('r:', r)
        vin = r[0]
        msrp = r[1]
        price_before_rebates = r[2]
        unconditional_rebates = r[3]
        conditional_rebates = r[4]

        dealer_discount = msrp - price_before_rebates

        if unconditional_rebates:
            best_discount = dealer_discount + unconditional_rebates + conditional_rebates
        else:
            best_discount = dealer_discount

        # Print results
        print('\t\tVIN:', vin)
        print('\t\tMSRP:', msrp)
        print('\t\tPrice before rebates:', price_before_rebates)
        print('\t\tDealer Discount:', dealer_discount)
        print('\t\tUnconditional Rebates:', unconditional_rebates)
        print('\t\tConditional Rebates:', conditional_rebates)
        print('\t\tBest Discount:', best_discount, '\n\n')

        # Update database
        query = 'UPDATE masterInventory SET intTotalDiscount = ? WHERE vin = ?'
        to_db = (best_discount, vin)
        c.execute(query, to_db)
        conn.commit()

    conn.close()
    print('Finished calculating max discount for each vehicle.\n')


def create_outgoing_homenet_table():

    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    query = ("""
        CREATE TABLE IF NOT EXISTS outgoingHomenet 
        (VIN TEXT UNIQUE, comment1 TEXT, misc_price1 INTEGER, comment2 TEXT, misc_price2 INTEGER, comment3 TEXT, misc_price3 INTEGER, comment5 TEXT) 
    """)
    c.execute(query)

    conn.commit()
    conn.close()


def update_outgoing_homenet_table():

    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    c.execute('DELETE FROM outgoingHomenet')

    to_db = []

    c.execute('SELECT vin, highlights, intTotalRebates, totalConditionalRebates FROM masterInventory')
    results = c.fetchall()
    for r in results:

        vin = r[0]
        highlights = r[1]
        unconditional_rebates = r[2]
        conditional_rebates = r[3]

        if not unconditional_rebates:
            unconditional_rebates = 0
        if not conditional_rebates:
            conditional_rebates = 0

        to_db.append((vin, highlights, 0, None, unconditional_rebates, None, conditional_rebates, ''))

        print('\n\nVIN:', vin)
        print('Highlights:', highlights)
        print('Unconditional Rebates:', unconditional_rebates)
        print('Conditional Rebates:', conditional_rebates)

    query = ("""
        INSERT OR REPLACE INTO outgoingHomenet (vin, comment1, misc_price1, comment2, misc_price2, comment3, misc_price3, comment5) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)
    c.executemany(query, to_db)

    conn.commit()
    conn.close()


def update_outgoing_homenet_file():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    c.execute('SELECT vin, comment1, misc_price1, comment2, misc_price2, comment3, misc_price3, comment5 FROM outgoingHomenet')
    with open('data/homenet-incentive-feed.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0] for i in c.description])  # write headers
        csv_writer.writerows(c)

    conn.commit()
    conn.close()


def upload_outgoing_homenet_file():
    print('\nUploading inventory to FTP server for Homenet...')
    file_path = 'data/homenet-incentive-feed.csv'
    file_name = file_path.split('/')
    file_name = file_name[-1]
    print('Uploading ' + file_name + ' to FTP server...\n')
    file = open(file_path, 'rb')
    ftp = ftplib.FTP('iol.homenetinc.com')
    ftp.login('hndatafeed', 'gx8m6')
    ftp.storbinary('STOR ' + file_name, file, 1024)
    file.close()
    ftp.quit()
    print('Successfully uploaded ' + file_name + ' to homenet folder on FTP server.\n')


def send_feeds_from_homenet():
    print('Navigating to Homenet.com and send out feeds to cars.com, cargurus, etc..')
    
    # Fire up ChromeDriver
    browser = start_chromedriver()
    wait = WebDriverWait(browser, 10)

    # Log into Homenet
    #url = 'https://www.homenetiol.com/marketplace/overview'
    url = 'https://www.homenetiol.com/login?RedirectUrl=%2fmarketplace%2foverview'
    browser.get(url)
    username = browser.find_element_by_xpath('//input[@class="username text-value"]')
    password = browser.find_element_by_xpath('//input[@class="password text-value"]')
    username.send_keys('spencer@rosevillemidwayford.com')
    password.send_keys('G3nericwords')
    wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="login-action button"]'))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="run-all-button button"]'))).click()
    time.sleep(10)

    print('Finished sending out feeds.')


def vacuum_db():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    c.execute("VACUUM")
    conn.close()


def figureManagerSpecials():
    
    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    url = 'http://www.rosevillemidwayford.com/new-car-sales-roseville-mn'
    page = requests.get(url)
    tree = html.fromstring(page.content)
    stockResults = tree.xpath('//span[contains(@class, "spec-value-stocknumber")]/text()')
    specialStockList = []
    for specialStock in stockResults :
        specialStock = specialStock.replace('#', '')
        specialStockList.append(specialStock)
    
    print(specialStockList)
    
    c.execute('SELECT stock FROM masterInventory')
    results = c.fetchall()
    for r in results:
        stock = r[0]
        if stock in specialStockList :
            print('looks like stock #' + stock + ' is a special!')
            query = 'UPDATE masterInventory SET managerSpecial = ? WHERE stock = ?'
            to_db = ('True', stock)
            c.execute(query, to_db)
        else :
            print('looks like stock #' + stock + ' is NOT a special!')
            query = 'UPDATE masterInventory SET managerSpecial = ? WHERE stock = ?'
            to_db = ('False', stock)
            c.execute(query, to_db)
    
    conn.commit()
    conn.close()


def figureLeaseSpecials():
    # Open connection to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    lease_specials = []

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
            query = 'SELECT min(leasePayment) FROM masterInventory WHERE year = ? AND model = ?'
            to_db = (year, model)
            c.execute(query, to_db)
            payment_results = c.fetchall()
            min_payment = payment_results[0][0]

            query = 'SELECT vin, stock, vehTrim, intMSRP, intPrice, leaseRebateExpiration FROM masterInventory WHERE year = ? AND model = ? AND leasePayment = ?'

            to_db = (year, model, minPayment)
            c.execute(query, to_db)
            veh_results = c.fetchall()
            v = veh_results[0]  # Just get first vehicle even if there are many
            print(v)
            vin = v[0]
            stock = v[1]
            vehTrim = v[2]
            msrp = v[3]
            price = v[4]
            term = 36
            residual = v[5]
            downPayment = v[6]
            totalLeaseRebates = v[7]
            dueAtSigning = v[8]
            expiration = v[9]

            # Get data from masterInventory table for rest of required info
            c.execute('SELECT bodyStyle, imageUrls, imageUrlsHD, vdp_url, drive FROM masterInventory WHERE vin = ?', (vin,))  # add option codes to this later
            master_results = c.fetchall()
            if not master_results:
                continue
            bodyStyle = master_results[0][0]  # just getting that matched the else query, could maybe hone this to get one with pic later??
            imageUrls = master_results[0][1]
            imageUrlsHD = master_results[0][2]
            vdp = master_results[0][3]
            drive = master_results[0][4]
            # option_codes = masterResults[0][4]

            # Set image to HD version if available
            if imageUrlsHD:
                imageUrl = imageUrlsHD
            elif imageUrls:
                imageUrl = imageUrls.split(',')[0]
            else:
                continue

            minPayment = locale.currency(minPayment, grouping=True).replace('.00', '')
            #downPayment = locale.currency(downPayment, grouping=True).replace('.00', '')
            #dueAtSigning = locale.currency(dueAtSigning, grouping=True).replace('.00', '')
            msrp = locale.currency(msrp, grouping=True).replace('.00', '')
            price = locale.currency(price, grouping=True).replace('.00', '')

            # offer = '<p>' + minPayment + '/month with ' + downPayment + ' down payment.<br><br>Just ' + dueAtSigning + ' due at signing.<br><br>Based on MSRP of ' + msrp + '.</p>'
            # title = minPayment + '/month with {} down.'.format(downPayment)
            # description = 'Lease term of {} months. Based on MSRP of {} and selling price of {}. Requires {} due at signing.'.format(term, msrp, price, dueAtSigning)
            # disclaimer = 'Must take new retail delivery from dealer stock by {}. Requires {} due at signing. Based on MSRP of {} and selling price of {}. See Subject to credit approval. Assumes 10,500 miles/year and Tier 0-1 credit. Tax, title, and license not included. Some restrictions apply. See sales representative for details.'.format(expiration, minPayment, msrp, price)



            lease_specials.append({
                'vin': vin,
                'stock': stock,
                'year': year,
                'model': model,
                'vehTrim': vehTrim,
                # 'title': title,
                # 'description': description,
                'expiration': expiration,
                'monthlyPayment': minPayment,
                'dueAtSigning': dueAtSigning,
                'vdp': vdp,
                'imageUrl': imageUrl,
                'bodyStyle': bodyStyle,
                'msrp': msrp,
                'price': price,
                # 'disclaimer': disclaimer,
                'drive': drive,
                # 'option_codes': option_codes
            })

    print('\nFresh Specials:')
    for s in lease_specials:
        print('\n')
        # print('\n\n', s, '\n')
        for k in s.keys():
            print(k + ': ' + str(s[k]))
        print('\n\n')

    # Close connection to database
    conn.close()

    return lease_specials


def wait_for_next_run(minutes_to_wait):
    print('Finished running program. Waiting 30 minutes to rerun.')
    minutes_to_wait = int(minutes_to_wait)
    for i in range(minutes_to_wait, 1, -1):
        time.sleep(60)
        print('Waiting {} minutes until next run.'.format(i))


def main():

        while True:
            get_incoming_homenet_file()
            update_incoming_homenet_table()

            scrape.scrape_cdk()
            calculate_pricing()
            compute_highlights()

            create_outgoing_homenet_table()
            update_outgoing_homenet_table()
            update_outgoing_homenet_file()
            upload_outgoing_homenet_file()
            send_feeds_from_homenet()

            sales_specials.main()
            midwords.main()
            hd_images.main()
            facebook.main()
            #adwords_feeds.main()
            sheets.main()


            # maybe add something to check if any dealer discounts are negative then re run (and if model isnt raptor)

            vacuum_db()

            wait_for_next_run(30)


if __name__ == '__main__':

    main()





