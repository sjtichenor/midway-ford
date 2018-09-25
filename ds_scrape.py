from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import datetime
import os
from utilz import fire_up_chromedriver




def export_veh_sales():

    # Delete mydata.csv if it's already in folder (bug from past run)
    try:
        #os.remove('/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/mydata.csv')
        os.remove('data/ds_sales/mydata.csv')
    except FileNotFoundError:
        pass

    # Fire up ChromeDriver
    # executable_path = '/Users/spencertichenor/PycharmProjects/midway/chromedriver'
    # os.environ['webdriver.chrome.driver'] = executable_path
    # chrome_options = Options()
    # prefs = {
    #     'profile.default_content_setting_values.automatic_downloads': 1,
    #     'download.default_directory': r'/Users/spencertichenor/PycharmProjects/midway/data/ds_sales',
    # }
    # chrome_options.add_experimental_option('prefs', prefs)
    # browser = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)


    browser = fire_up_chromedriver()
    wait = WebDriverWait(browser, 10)

    # Log into DealerSocket
    url = 'https://my.dealersocket.com/SSO/Login.aspx?ReturnURL=/CRM/Login.aspx&NoRedirect=1'
    browser.get(url)
    username = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="username"]')))
    password = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="password"]')))
    username.send_keys('mf4jtichen')
    password.send_keys('Shoshana17')
    wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"]'))).click()

    # Navigate to List Builder
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="index"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//frame[@name="main"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//frame[@name="leftnav"]')))
    wait.until(EC.element_to_be_clickable((By.ID, 'nav_marketing_tools'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'ListBldrLink'))).click()

    # Click Load button
    browser.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="ifModalPopup"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@name="ifLsData"]')))
    time.sleep(5)
    wait.until(EC.element_to_be_clickable((By.ID, 'LoadButton'))).click()

    # Select Vehicle Purchases option
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="viewFullTextIframe"]')))
    wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="174"]'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_iconLoad'))).click()

    # Click to turn Remove Duplicates off
    browser.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="ifModalPopup"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@name="ifLsData"]')))
    time.sleep(1)
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="frmMid"]')))
    time.sleep(1)
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//frame[@id="sFrame2"]')))
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//img[@class="iCheckbox_switch"]'))).click()

    # Run selected option
    browser.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="ifModalPopup"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@name="ifLsData"]')))
    wait.until(EC.element_to_be_clickable((By.ID, 'RunButton'))).click()
    time.sleep(3)

    # Select all results
    browser.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="ifModalPopup"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@name="ifLsData"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="Frame2"]')))
    wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@value="Select All"]'))).click()

    # Click to export
    browser.switch_to.parent_frame()
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_iconExport'))).click()

    # Select fields to export
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="viewFullTextIframe"]')))
    wait.until(EC.element_to_be_clickable((By.ID, 'chkboxSelectAll'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_HyperVehicleFields'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'chkboxSelectAll'))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="VehicleFields"]//label[text()="Insert Date"]'))).click()

    # Click to export (again)
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_btnCreate'))).click()

    time.sleep(5)

    # Rename file
    date_today = datetime.datetime.today()
    file_name = 'vehicle_sales_{}-{}-{}-{}-{}-{}.csv'.format(
        date_today.year, date_today.month, date_today.day, date_today.hour, date_today.minute, date_today.second
    )
    file_path = '/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/{}'.format(file_name)

    download_finished = False
    while not download_finished:
        try:
            #os.rename('/Users/spencertichenor/PycharmProjects/midway/data/ds_sales/mydata.csv', file_path)
            os.rename('data/ds_sales/mydata.csv', file_path)
            download_finished = True
        except FileNotFoundError:
            print('File still downloading...')
            time.sleep(5)


def export_veh_services():

    # Delete mydata.csv if it's already in folder (bug from past run)
    try:
        os.remove('/Users/spencertichenor/PycharmProjects/midway/data/ds_service/mydata.csv')
    except FileNotFoundError:
        pass

    # Fire up ChromeDriver
    chromedriver = '/Users/spencertichenor/PycharmProjects/midway/chromedriver'
    os.environ['webdriver.chrome.driver'] = chromedriver
    chrome_options = Options()
    prefs = {
        'profile.default_content_setting_values.automatic_downloads': 1,
        'download.default_directory': r'/Users/spencertichenor/PycharmProjects/midway/data/ds_service',
    }
    chrome_options.add_experimental_option('prefs', prefs)
    browser = webdriver.Chrome(executable_path=chromedriver, chrome_options=chrome_options)
    wait = WebDriverWait(browser, 10)

    # Log into DealerSocket
    url = 'https://my.dealersocket.com/SSO/Login.aspx?ReturnURL=/CRM/Login.aspx&NoRedirect=1'
    browser.get(url)
    username = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="username"]')))
    password = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="password"]')))
    username.send_keys('mf4jtichen')
    password.send_keys('Shoshana17')
    wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"]'))).click()

    # Navigate to List Builder
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="index"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//frame[@name="main"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//frame[@name="leftnav"]')))
    wait.until(EC.element_to_be_clickable((By.ID, 'nav_marketing_tools'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'ListBldrLink'))).click()

    # Click Load button
    browser.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="ifModalPopup"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@name="ifLsData"]')))
    wait.until(EC.element_to_be_clickable((By.ID, 'LoadButton'))).click()

    # Select Vehicle Purchases option
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="viewFullTextIframe"]')))
    wait.until(EC.element_to_be_clickable((By.XPATH, '//option[@value="175"]'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_iconLoad'))).click()

    # Click to turn Remove Duplicates off
    browser.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="ifModalPopup"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@name="ifLsData"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="frmMid"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//frame[@id="sFrame2"]')))
    wait.until(EC.element_to_be_clickable((By.XPATH, '//img[@class="iCheckbox_switch"]'))).click()

    # Run selected option
    browser.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="ifModalPopup"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@name="ifLsData"]')))
    wait.until(EC.element_to_be_clickable((By.ID, 'RunButton'))).click()
    time.sleep(3)

    # Select all results
    browser.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="ifModalPopup"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@name="ifLsData"]')))
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="Frame2"]')))
    wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@value="Select All"]'))).click()

    # Click to export
    browser.switch_to.parent_frame()
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_iconExport'))).click()

    # Select fields to export
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//iframe[@id="viewFullTextIframe"]')))
    wait.until(EC.element_to_be_clickable((By.ID, 'chkboxSelectAll'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_HyperVehicleFields'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'chkboxSelectAll'))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="VehicleFields"]//label[text()="Insert Date"]'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_HyperEventFields'))).click()
    wait.until(EC.element_to_be_clickable((By.ID, 'chkboxSelectAll'))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="EventFields"]//label[text()="Insert Date"]'))).click()

    # Click to export (again)
    wait.until(EC.element_to_be_clickable((By.ID, 'ctl00_body_btnCreate'))).click()

    # Wait for download..
    time.sleep(10)

    # Rename file
    date_today = datetime.datetime.today()
    file_name = 'vehicle_services_{}-{}-{}-{}-{}-{}.csv'.format(
        date_today.year, date_today.month, date_today.day, date_today.hour, date_today.minute, date_today.second
    )
    file_path = '/Users/spencertichenor/PycharmProjects/midway/data/ds_service/{}'.format(file_name)
    download_finished = False
    while not download_finished:
        try:
            os.rename('/Users/spencertichenor/PycharmProjects/midway/data/ds_service/mydata.csv', file_path)
            download_finished = True
        except FileNotFoundError:
            print('File still downloading...')
            time.sleep(5)


def main():

    export_veh_sales()
    export_veh_services()


if __name__ == '__main__':
    main()
