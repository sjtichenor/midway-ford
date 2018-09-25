from pprint import pprint
import locale
import requests
import hashlib
import sqlite3
from datetime import datetime
import ds_scrape
import db_master

locale.setlocale(locale.LC_ALL, 'en_US')


# Convert date_string in format of '2018/01/15' to seconds from epoch string
def date_to_timestamp(date_string):
    date_object = datetime.strptime(date_string, '%Y/%m/%d')
    date_string = int((date_object - datetime(1970, 1, 1)).days * (24 * 60 * 60))
    return date_string


def get_service_data():

    # Connect to db
    conn = sqlite3.connect('data/midway.db')
    c = conn.cursor()

    query = ("""
           SELECT Customer.id, Customer.first_name, Customer.last_name, Customer.city, Customer.state, Customer.zip, Customer.home_phone, Customer.mobile_phone, Customer.work_phone, Customer.email1, Customer.email2, Customer.email3, Customer.birthdate, Service.id, Service.gross, Service.service_date 
           FROM ((Customer 
           INNER JOIN Vehicle ON Vehicle.customer_id = Customer.id) 
           INNER JOIN Service ON Service.vehicle_id = Vehicle.id) 
           WHERE Service.service_date >= '2018/07/31' AND Customer.first_name != '' 
           ORDER BY Service.service_date DESC;
           """)

    c.execute(query)

    results = c.fetchall()

    conn.close()

    return results


def get_sales_data():

    # Connect to db
    conn = sqlite3.connect('data/midway.db')
    c = conn.cursor()

    query = ("""
           SELECT Customer.id, Customer.first_name, Customer.last_name, Customer.city, Customer.state, Customer.zip, Customer.home_phone, Customer.mobile_phone, Customer.work_phone, Customer.email1, Customer.email2, Customer.email3, Customer.birthdate, Sale.id, Sale.gross_profit, Sale.purchase_date 
           FROM ((Customer 
           INNER JOIN Vehicle ON Vehicle.customer_id = Customer.id) 
           INNER JOIN Sale ON Sale.vehicle_id = Vehicle.id) 
           WHERE Sale.purchase_date >= '2018/07/31' 
           ORDER BY Sale.purchase_date DESC;
           """)

    c.execute(query)

    results = c.fetchall()

    conn.close()

    return results


def upload_service_data(event_data):

    version = 'v3.0'
    FACEBOOK_API_TOKEN = 'EAACEWe6RzUwBALuyYhSTKBBjbjoSfR6tAhFMAcwV6QcrNIkrjTRf2bU1V6Xbmk8DZBB469fL3tJUrvetYwv6DKR94c9EwYycEY1OZCw537cEbvRps0mAWgd3ZAn9NzqdvLdPJ4WFmf0lL5roWpU2dcm5w7hhZAQTWhiJ1UNQaJTZCF7cDgHzu'
    BUSINESS_MANAGER_ID = '488585047978938'
    AD_ACCOUNT_ID = '49968439'
    base_url = 'https://graph.facebook.com'
    service_purchase_event_id = '1187134724751909'

    data = []

    for z, event in enumerate(event_data):

        # Reformat city
        city = event[3].replace(' ', '')

        # Reformat birthdate
        if event[12]:
            doby, dobm, dobd, = event[12].split('/')
        else:
            doby, dobm, dobd, = ['', '', '']

        # Reformat event_time
        event_time = date_to_timestamp(event[15])

        # Build phone list
        phone_list = [event[6], event[7], event[8]]
        phone_list = [x for x in phone_list if x is not '']
        print(phone_list)
    
        # Build email list
        email_list = [event[9], event[10], event[11]]
        email_list = [x for x in email_list if x is not '']
        print(email_list)
    
        match_keys = {
            'fn': event[1],
            'ln': event[2],
            'ct': city,
            'st': event[4],
            'zip': event[5],
            'phone': phone_list,
            'email': email_list,
            'doby': doby,
            'dobm': dobm,
            'dobd': dobd,
            }
        pprint(match_keys)

        # Hash the data
        for k in match_keys:
            if type(match_keys[k]) is str:
                match_keys[k] = hashlib.sha256(match_keys[k].encode('utf-8')).hexdigest()
            elif type(match_keys[k]) is list:
                for i in range(len(match_keys[k])):
                    match_keys[k][i] = hashlib.sha256(match_keys[k][i].encode('utf-8')).hexdigest()

        event_dict = {
                    'match_keys': match_keys,
                    'currency': 'USD',
                    'value': event[14],
                    'event_name': 'Purchase',
                    'event_time': event_time,
                    'custom_data': {
                        'event_source': 'dealersocket'
                    },
                }
        data.append(event_dict)
        # if z == 50:
        #     break

    with requests.Session() as s:

        for d in data:
            d = [d]

            payload = {
                'access_token': FACEBOOK_API_TOKEN,
                'session': s,
                'upload_tag': 'store_data',
                'data': str(d),
            }

            url = 'https://graph.facebook.com/{}/{}/events'.format(version, service_purchase_event_id)
            r = requests.post(url, params=payload)
            print('r:', r)
            a = r.json()
            print('a:', a)


def upload_sales_data(event_data):
    version = 'v3.0'
    FACEBOOK_API_TOKEN = 'EAACEWe6RzUwBALuyYhSTKBBjbjoSfR6tAhFMAcwV6QcrNIkrjTRf2bU1V6Xbmk8DZBB469fL3tJUrvetYwv6DKR94c9EwYycEY1OZCw537cEbvRps0mAWgd3ZAn9NzqdvLdPJ4WFmf0lL5roWpU2dcm5w7hhZAQTWhiJ1UNQaJTZCF7cDgHzu'
    BUSINESS_MANAGER_ID = '488585047978938'
    AD_ACCOUNT_ID = '49968439'
    base_url = 'https://graph.facebook.com'
    vehicle_purchase_event_id = '473150923086219'

    data = []

    for z, event in enumerate(event_data):

        # Reformat city
        city = event[3].replace(' ', '')

        # Reformat birthdate
        if event[12]:
            doby, dobm, dobd, = event[12].split('/')
        else:
            doby, dobm, dobd, = ['', '', '']

        # Reformat event_time
        event_time = date_to_timestamp(event[15])

        # Build phone list
        phone_list = [event[6], event[7], event[8]]
        phone_list = [x for x in phone_list if x is not '']

        # Build email list
        email_list = [event[9], event[10], event[11]]
        email_list = [x for x in email_list if x is not '']

        match_keys = {
            'fn': event[1],
            'ln': event[2],
            'ct': city,
            'st': event[4],
            'zip': event[5],
            'phone': phone_list,
            'email': email_list,
            'doby': doby,
            'dobm': dobm,
            'dobd': dobd,
        }
        pprint(match_keys)

        # Hash the data
        for k in match_keys:
            if type(match_keys[k]) is str:
                match_keys[k] = hashlib.sha256(match_keys[k].encode('utf-8')).hexdigest()
            elif type(match_keys[k]) is list:
                for i in range(len(match_keys[k])):
                    match_keys[k][i] = hashlib.sha256(match_keys[k][i].encode('utf-8')).hexdigest()

        event_dict = {
            'match_keys': match_keys,
            'currency': 'USD',
            'value': event[14],
            'event_name': 'Purchase',
            'event_time': event_time,
            'custom_data': {
                'event_source': 'dealersocket'
            },
        }
        data.append(event_dict)

    with requests.Session() as s:

        for d in data:
            d = [d]

            payload = {
                'access_token': FACEBOOK_API_TOKEN,
                'session': s,
                'upload_tag': 'store_data',
                'data': str(d),
            }

            url = 'https://graph.facebook.com/{}/{}/events'.format(version, vehicle_purchase_event_id)
            r = requests.post(url, params=payload)
            print('r:', r)
            a = r.json()
            print('a:', a)


def uploadSalesDataOld():

    version = 'v2.11'
    FACEBOOK_API_TOKEN = 'EAACEWe6RzUwBALuyYhSTKBBjbjoSfR6tAhFMAcwV6QcrNIkrjTRf2bU1V6Xbmk8DZBB469fL3tJUrvetYwv6DKR94c9EwYycEY1OZCw537cEbvRps0mAWgd3ZAn9NzqdvLdPJ4WFmf0lL5roWpU2dcm5w7hhZAQTWhiJ1UNQaJTZCF7cDgHzu'
    BUSINESS_MANAGER_ID = '488585047978938'

    AD_ACCOUNT_ID = '49968439'

    base_url = 'https://graph.facebook.com'

    vehicle_purchase_event_id = '473150923086219'
    service_purchase_event_id = '1187134724751909'

    match_keys = {
        'fn': 'Claudia',
        'ln': 'Skinner',
        'phone': ['16513984222'],
        'email': ['claudiajskinner@gmail.com'],
        }

    for k in match_keys:
        if type(match_keys[k]) is str:
            match_keys[k] = hashlib.sha256(match_keys[k].encode('utf-8')).hexdigest()
        elif type(match_keys[k]) is list:
            for i in range(len(match_keys[k])):
                match_keys[k][i] = hashlib.sha256(match_keys[k][i].encode('utf-8')).hexdigest()

    print(match_keys)

    with requests.Session() as s:
        data = [
            {
                'match_keys': match_keys,
                'currency': 'USD',
                'value': 1,
                'event_name': 'Purchase',
                'event_time': '1515852065',
                # 'custom_data': {
                #     'event_source': "in_store"
                # },
            },
        ]

        payload = {
            'access_token': FACEBOOK_API_TOKEN,
            'session': s,
            'upload_tag': 'store_data',
            'data': str(data),
        }


        url = 'https://graph.facebook.com/{}/{}/events'.format(version, vehicle_purchase_event_id)
        #url = 'https://graph.facebook.com/{}/{}/offline_conversion_data_sets'.format(version, BUSINESS_MANAGER_ID)
        r = requests.post(url, params=payload)
        print(r)
        a = r.json()
        pprint(a)


def main():

    #ds_scrape.main()
    db_master.main()

    service_data = get_service_data()
    upload_service_data(service_data)
    sales_data = get_sales_data()
    pprint(sales_data)
    print(len(sales_data))
    upload_sales_data(sales_data)


if __name__ == '__main__':
    main()
