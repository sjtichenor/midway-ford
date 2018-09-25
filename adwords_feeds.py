import sqlite3
import csv
from datetime import datetime
import locale
import json

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

def createAdwordsManagerSpecialsTable():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    c.execute('CREATE TABLE IF NOT EXISTS adwordsManagerSpecialsFeed (ID TEXT UNIQUE, ID2 TEXT, Item_title TEXT, Final_url TEXT, Image_url TEXT, Item_subtitle TEXT, Item_description TEXT, Item_category TEXT, Price TEXT, Sale_price TEXT, Contextual_keywords TEXT, Item_address TEXT, Tracking_template TEXT, Custom_parameter TEXT)')
    
    conn.commit()
    conn.close()

def updateAdwordsManagerSpecialsTable():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    c.execute('SELECT vin, stock, invType, year, make, model, vehTrim, intMSRP, intPrice, vdp_url, imageUrls, bodyStyle, intTotalDiscount from masterInventory WHERE managerSpecial = ?', ('True',))
    results = c.fetchall()
    
    for r in results :
        print(r)
        vin= r[0]
        stock = r[1]
        invType = r[2]
        year= r[3]
        make = r[4]
        model = r[5]
        vehTrim = r[6]
        msrp = r[7]
        price = r[8]
        vdpUrl = r[9]
        imageUrls = r[10]
        bodyStyle = r[11]
        discount = r[12]
        
        msrp = locale.currency(msrp, grouping=True).replace('$', '') + ' USD'
        price = locale.currency(price, grouping=True).replace('$', '') + ' USD'
        imageUrl = imageUrls.split(',')[0]
        discount = locale.currency(discount, grouping=True).replace('.00', '')
        
        
        item_title = str(year) + ' ' + make + ' ' + model + ' - ' + price
        item_subtitle = 'Discounted ' + discount + ' for a limited time.'
        item_description = 'Stock #' + stock
        contextual_keywords = invType + ' ' + bodyStyle + ' sale; ' + make + ' ' + model + ' sale;'
        item_address = '2777 Snelling Ave N, Roseville, MN 55113'
        
        
        to_db = (r[0], r[1], item_title, vdpUrl, imageUrl, item_subtitle, item_description, bodyStyle, msrp, price, contextual_keywords, item_address, '', '')
        query = 'INSERT OR REPLACE INTO adwordsManagerSpecialsFeed (ID, ID2, Item_title, Final_url, Image_url, Item_subtitle, Item_description, Item_category, Price, Sale_price, Contextual_keywords, Item_address, Tracking_template, Custom_parameter) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        c.execute(query, to_db)
    conn.commit()
    conn.close()
def updateAdwordsManagerSpecialsFile():
    
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM adwordsManagerSpecialsFeed')
    
    with open('data/adwords-manager-specials-feed.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0].replace('_', ' ') for i in c.description]) # write headers
        csv_writer.writerows(c)
        
    conn.commit()
    conn.close()
def createAdwordsLeaseTable():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    c.execute('CREATE TABLE IF NOT EXISTS adwordsLeaseFeed (ID TEXT UNIQUE, ID2 TEXT, Item_title TEXT, Final_url TEXT, Image_url TEXT, Item_subtitle TEXT, Item_description TEXT, Item_category TEXT, Price TEXT, Sale_price TEXT, Contextual_keywords TEXT, Item_address TEXT, Tracking_template TEXT, Custom_parameter TEXT)')
    
    conn.commit()
    conn.close()
def updateAdwordsLeaseTable():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    
    
    freshList = []
    
    specials = lease.figureSpecials()
    for special in specials:
        
        item_title = 'Ford ' + special['model'] + ' Lease'
        item_subtitle = 'Lease for ' + special['monthlyPayment'] + '/mo with $0 Down'
        item_description = str(special['year']) + ' Ford ' + special['model'] + ' ' + special['vehTrim']
        final_url = 'http://rosevillemidwayford.com/lease-specials'
        price = ''
        sale_price = special['monthlyPayment']
        contextual_keywords = 'ford dealers; ' + 'new ' + special['bodyStyle'] + ' sale; new ' + special['bodyStyle'] + ' lease; ' + str(special['year']) + ' ford ' + special['model'] + ' sale'
        item_address = '2777 Snelling Ave N, Roseville, MN 55113'
        to_db = (special['vin'], special['stock'], item_title, final_url, special['imageUrl'], item_subtitle, item_description, special['bodyStyle'], price, sale_price, contextual_keywords, item_address, '', '')
        query = 'INSERT OR REPLACE INTO adwordsLeaseFeed (ID, ID2, Item_title, Final_url, Image_url, Item_subtitle, Item_description, Item_category, Price, Sale_price, Contextual_keywords, Item_address, Tracking_template, Custom_parameter) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        c.execute(query, to_db)
        
        freshList.append(special['vin'])
        
        
    
    count = 0
    c.execute('SELECT ID FROM adwordsLeaseFeed')
    currentVinList = c.fetchall()
    print(currentVinList)
    for currentVin in currentVinList :
        currentVin = currentVin[0]
        if currentVin not in freshList :
            c.execute('DELETE FROM adwordsLeaseFeed WHERE ID = ?', (currentVin,))
            count += 1
    print(str(count) + ' vehicle deleted from adwordsLeaseFeed table.')
    conn.commit()
    conn.close()
def updateAdwordsLeaseFile():
    
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM adwordsLeaseFeed')
    
    
    
    with open('data/adwords-lease-feed.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0].replace('_', ' ') for i in c.description]) # write headers
        csv_writer.writerows(c)
        
    conn.commit()
    conn.close()
def updateAdwordsNewInventoryTable():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    
    query = 'SELECT vin, stock, invType, year, make, model, vehTrim, intMSRP, intPrice, vdp_url, imageUrls, imageUrlsHD, exteriorColor, rebateExpiration, description, bodyStyle, style, drive, engine, highlights, miles FROM masterInventory WHERE invType = ?'
    to_db = ('New',)
    c.execute(query, to_db)
    results = c.fetchall()
    
    updatedVinList = []
    
    for r in results :
        vin = r[0]
        stock = r[1]
        invType = r[2]
        year = r[3]
        make = r[4]
        model = r[5]
        vehTrim = r[6]
        msrp = r[7]
        price = r[8]
        vdpUrl = r[9]
        imageUrls = r[10]
        imageUrlsHD = r[11]
        color = r[12]
        rebateExpiration = r[13]
        description = r[14]
        bodyStyle = r[15]
        style = r[16]
        drive = r[17]
        engine = r[18]
        highlights = r[19]
        miles = r[20]
        
        if price == 0 :
            price = msrp
        
        # Use small pic because adwords has max image size of 1MB
        if imageUrls != '' :
            image_link = imageUrls.split(',')[0]
        else :
            continue
        title = str(year) + ' ' + make + ' ' + model + ' ' + vehTrim + ' - ' + locale.currency(price, grouping=True).replace('.00', '')
        print(title)
        
        msrp = locale.currency(msrp, grouping=True).replace('$', '') + ' USD'
        price = locale.currency(price, grouping=True).replace('$', '') + ' USD'
        availability = 'In Stock'
        #google_product_category = 'Vehicles & Parts > Vehicles > Motor Vehicles > Cars, Trucks & Vans'
        
        
        # Set sale_price_effective_date
        d = datetime.today()
        saleStart = str(d.year) + '-' + str(d.month) + '-' + str(d.day) + 'T9:00-05:00'
        if rebateExpiration == None or rebateExpiration == 'None' :
            sale_price_effective_date = None
        else :
            
            rebateMonth = rebateExpiration.split('/')[0]
            rebateDay = rebateExpiration.split('/')[1]
            rebateYear = str(d.year)
            saleEnd = rebateYear + '-' + rebateMonth + '-' + rebateDay + 'T20:00-5:00'
            sale_price_effective_date = saleStart + '/' + saleEnd
        
        # Make description
        description = highlights.replace(',', ', ') + ' - Stock #' + stock 
        description = description.replace('0, 0', '0,0') # fix for 100,000-mile warranty
        if invType == 'Used' : # Add mileage if vehicle is used
            miles = midsql.priceIntToStr(miles)
            miles = miles.replace('$', '')
            description = miles + ' miles - ' + description
        
        # print(imageUrl)
        # print(type(imageUrl))
        # Skip if missing required fields
        if image_link == None or description == None :
            pass
            
        
        # Set address
        address = '2777 Snelling Ave N, Roseville, MN 55113'
        
        query = 'INSERT OR REPLACE INTO adwordsNewInventoryFeed (ID, ID2, Item_title, Final_URL, Image_URL, Item_subtitle, Item_category, Price, Sale_price, Contextual_keywords, Item_address, Tracking_template, Custom_parameter) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        to_db = (vin, stock, title, vdpUrl, image_link, description, model, msrp, price, bodyStyle, address, '', '')
        c.execute(query, to_db)
    
    
    # Delete old vins from adwordsNewInventoryFeed table
    count = 0
    c.execute('SELECT ID FROM adwordsNewInventoryFeed')
    adwordsVins = c.fetchall()
    c.execute('SELECT vin FROM masterInventory')
    mVins = c.fetchall()
    for adwordsVin in adwordsVins:
        if adwordsVin not in mVins:
            c.execute('DELETE FROM adwordsNewInventoryFeed WHERE ID = ?', adwordsVin)
            count += 1
    print(str(count) + ' vehicle deleted from adwordsNewInventoryFeed table.')
    conn.commit()
    conn.close()
def updateAdwordsNewInventoryFile():
    
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM adwordsNewInventoryFeed')
    
    
    
    with open('data/adwords-new-inventory-feed.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0].replace('_', ' ') for i in c.description]) # write headers
        csv_writer.writerows(c)
        
    conn.commit()
    conn.close()



# Model feeds

def createAdwordsNewModelsTable():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS adwordsNewModelsFeed (Model_9text0 TEXT UNIQUE, Price_9price0 TEXT, Discount_9price0 TEXT, Expiration_9date0 TEXT, Quantity_9number0 INTEGER, Target_campaign TEXT, Target_adgroup TEXT)')

    conn.commit()
    conn.close()


def updateAdwordsNewModelsTable():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # Delete old data
    c.execute('DELETE FROM adwordsNewModelsFeed')

    query = 'SELECT DISTINCT model FROM masterInventory WHERE invType = ?'
    to_db = ('New',)
    c.execute(query, to_db)
    results = c.fetchall()

    final_to_db = []
    for r in results:
        query = 'SELECT min(intPrice), max(intTotalDiscount), count(vin), min(rebateExpiration) FROM masterInventory WHERE invType = ? AND model = ?'
        to_db = ('New', r[0])
        c.execute(query, to_db)
        model_results = c.fetchall()
        print(model_results[0][3])
        exp_month = model_results[0][3].split('/')[0]
        exp_day = model_results[0][3].split('/')[1]
        exp_year = '2018'
        exp_time = '20:00:00'
        expiration = '{}/{}/{} {}'.format(exp_year, exp_month, exp_day, exp_time)
        print(expiration)
        final_to_db.append((r[0], model_results[0][0], model_results[0][1], model_results[0][2], expiration, 'New SEM - Make/Model', 'New 2017 {}'.format(r[0])))

    print('final_to_db', final_to_db)

    query = 'INSERT OR REPLACE INTO adwordsNewModelsFeed (Model_9text0, Price_9price0, Discount_9price0, Quantity_9number0, Expiration_9date0, Target_campaign, Target_adgroup) VALUES (?, ?, ?, ?, ?, ?, ?)'
    c.executemany(query, final_to_db)

    conn.commit()
    conn.close()

    # update sql table
    db_path = 'inventory.db'
    table_name = 'adwordsNewModelsFeed'
    csv_path = 'data/adwords-new-models-feed.csv'
    sql_table_to_csv(db_path, table_name, csv_path)


def updateAdwordsNewModelsFile():
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    c.execute('SELECT * FROM adwordsNewModelsFeed')

    with open('data/adwords-new-models-feed.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0].replace('_', ' ').replace('9', '(').replace('0', ')') for i in c.description])  # write headers
        csv_writer.writerows(c)

    conn.commit()
    conn.close()


def sql_table_to_csv(db_path, table_name, csv_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    query = 'SELECT * FROM {}'.format(table_name)
    c.execute(query)

    with open(csv_path, 'w') as csv_file:
        csv_writer = csv.writer(csv_file, dialect='excel')
        csv_writer.writerow([i[0].replace('_', ' ').replace('9', '(').replace('0', ')') for i in c.description])  # write headers
        csv_writer.writerows(c)

    conn.commit()
    conn.close()

def convertJson():

    with open('data/adwords-manager-specials-feed.csv', 'r') as csv_file:
        #field_names = ('ID', 'ID2', 'Item title', 'Final url', 'Image url', 'Item subtitle', 'Item description', 'Item category', 'Price', 'Sale price', 'Contextual keywords', 'Item address', 'Tracking template', 'Custom parameter')
        reader = csv.DictReader(csv_file)
        with open('/Users/spencertichenor/Drive/Marketing/Adwords/Google Web Designer/feeds/adwords-manager-specials-feed.json', 'w') as json_file:
            for row in reader:
                json.dump(row, json_file)
                #json_file.write('\n')



def main():
    
    createAdwordsManagerSpecialsTable()
    updateAdwordsManagerSpecialsTable()
    updateAdwordsManagerSpecialsFile()
    
    createAdwordsLeaseTable()
    updateAdwordsLeaseTable()
    updateAdwordsLeaseFile()
    
    updateAdwordsNewInventoryTable()
    updateAdwordsNewInventoryFile()

if __name__ == '__main__':
    main()


    # createAdwordsNewModelsTable()
    # updateAdwordsNewModelsTable()


    #updateAdwordsNewModelsFile()