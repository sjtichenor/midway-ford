import csv
import json
import os
import string
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


def removeWeirdChars(dirtyStr):  # Takes in a string, removes weird chars, returns new string
    validchars = string.ascii_letters + string.digits + ' ' + ':' + '-' + ',' + '&' + '$' + '/' + '.' + '_' + '!'
    cleanStr = ''.join(c for c in dirtyStr if c in validchars)
    return cleanStr


def loan_payment(amount, apr, term_length):

    # If 0% apr
    if not apr:
        return int(amount/term_length)

    i = apr/12.0
    d = ((1 + i)**term_length - 1) / (i * (1 + i)**term_length)
    return int(amount/d)


def csvToJson(csv_path, json_path):

    csv_file = open(csv_path, 'r')
    json_file = open(json_path, 'w')

    field_names = ('ID','ID2','Item title','Final URL', 'Image URL', 'Item subtitle', 'Item description', 'Item Category', 'Price', 'Sale price', 'Contextual keywords', 'Item address', 'Tracking template', 'Custom parameter')
    reader = csv.DictReader(csv_file, field_names)
    for i, row in enumerate(reader):
        if i != 0:
            json.dump(row, json_file)
            json_file.write('\n')
    print('Converted {} to json file located at: {}'.format(csv_path, json_path))


def fire_up_chromedriver(executable_path='chromedriver', virtual_display=True, auto_download=True, download_directory=r'data/ds_sales'):

    if virtual_display:
        display = Display(visible=0, size=(800, 800))
        display.start()

    browser = webdriver.Chrome(executable_path=executable_path)

    if auto_download:
        os.environ['webdriver.chrome.driver'] = executable_path
        chrome_options = Options()
        prefs = {
            'profile.default_content_setting_values.automatic_downloads': 1,
            'download.default_directory': download_directory,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'plugins.plugins_disabled': ['Chrome PDF Viewer'],
            # 'plugins.always_open_pdf_externally': True,
        }
        chrome_options.add_experimental_option('prefs', prefs)

    wait = WebDriverWait(browser, 10)

    return browser, wait





def int_word_converter(i):
    key = [
        [1, 'one'],
        [2, 'two'],
        [3, 'three'],
        [4, 'four'],
        [5, 'five'],
        [6, 'six'],
        [7, 'seven'],
        [8, 'eight'],
        [9, 'nine'],
        [10, 'ten']
    ]

    if isinstance(i, int):
        if i > 10:
            return i
        else:
            for k in key:
                if k[0] == i:
                    return k[1]
    else:
        for k in key:
            if k[1] == i:
                return k[0]
    # this last return i is just in case nothing matching
    return 'ERROR: NO QUANTITY FOUND'





