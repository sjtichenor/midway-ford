from googleads import adwords
from googleads import errors
import sqlite3
import locale
import suds
from utilz import loan_payment
from utilz import int_word_converter
from pprint import pprint
import datetime
import calendar
locale.setlocale(locale.LC_ALL, 'en_US.utf8')

client = adwords.AdWordsClient.LoadFromStorage('googleads.yaml')


# -------------------Adwords Functions-------------------#

def handleError(e):  # except suds.WebFault, e
    for error in e.fault.detail.ApiExceptionFault.errors:
        if error['ApiError.Type'] == 'PolicyViolationError':
            operation_index = re.findall(r'operations\[(.*)\]\.', error['fieldPath'])
            if operation_index:
                index = int(operation_index[0])
                operation = operations[index]
                print('Ad with headline \'%s\' violated %s policy \'%s\'.' %
                      (operation['operand']['ad']['headline'],
                       'exemptable' if error['isExemptable'] else 'non-exemptable',
                       error['externalPolicyName']))
                if error['isExemptable'].lower() == 'true':
                    # Add exemption request to the operation.
                    print('Adding exemption request for policy name \'%s\' on text '
                          '\'%s\'.' %
                          (error['key']['policyName'], error['key']['violatingText']))
                    if 'exemptionRequests' not in operation:
                        operation['exemptionRequests'] = []
                        operation['exemptionRequests'].append({'key': error['key']})
                else:
                    # Set non-exemptable operation to None to mark for deletion
                    print('Removing the operation from the request.')
                    operations[index] = None
        else:
            # Non-policy error returned, re-throw exception.
            raise e


def addAds(client, operations):
    ad_group_ad_service = client.GetService('AdGroupAdService', version='v201806')
    try:
        result = ad_group_ad_service.mutate(operations)
    except suds.WebFault as e:
        handleError(e)

    print('Added ' + str(len(operations)) + ' ad(s):\n')
    for i, ad in enumerate(result['value']):
        print('\t\t\t\t\t\tAd #' + str(i + 1) + ':')
        # print ('Added : ', ad['ad'])

        ad_id = str(ad['ad']['id'])
        ad_type = str(ad['ad']['type'])
        h1 = str(ad['ad']['headlinePart1'])
        h2 = str(ad['ad']['headlinePart2'])
        description = str(ad['ad']['description'])
        p1 = str(ad['ad']['path1'])
        p2 = str(ad['ad']['path2'])
        urls = str(ad['ad']['finalUrls'][0])

        print('\t\t\t\t\t\t\tAd ID: ' + ad_id)
        print('\t\t\t\t\t\t\tAd Type: ' + ad_type)
        print('\t\t\t\t\t\t\tHeadline Part 1: ' + h1)
        print('\t\t\t\t\t\t\tHeadline Part 2: ' + h2)
        print('\t\t\t\t\t\t\tDescription: ' + description)
        print('\t\t\t\t\t\t\tPath 1: ' + p1)
        print('\t\t\t\t\t\t\tPath 2: ' + p2)
        print('\t\t\t\t\t\t\tFinal Url: ' + str(urls))
        print('\n')


def addAdGroup(client, campaignID, adGroupName):  # Adds ad group and returns ID for ad group
    print('Adding ad group named \'' + adGroupName + ' to campaign ID# ' + campaignID)

    # Initialize appropriate service.
    ad_group_service = client.GetService('AdGroupService', version='v201806')

    # Construct operations and add ad groups.
    operations = [{
        'operator': 'ADD',
        'operand': {
            'campaignId': campaignID,
            'name': adGroupName,
            'status': 'ENABLED',
            'biddingStrategyConfiguration': {
                'bids': [
                    {
                        'xsi_type': 'CpcBid',
                        'bid': {
                            'microAmount': '2000000'
                        },
                    }
                ]
            },
            'settings': [
                {
                    # Targeting restriction settings. Depending on the
                    # criterionTypeGroup value, most TargetingSettingDetail only
                    # affect Display campaigns. However, the
                    # USER_INTEREST_AND_LIST value works for RLSA campaigns -
                    # Search campaigns targeting using a remarketing list.
                    'xsi_type': 'TargetingSetting',
                    'details': [
                        # Restricting to serve ads that match your ad group
                        # placements. This is equivalent to choosing
                        # "Target and bid" in the UI.
                        {
                            'xsi_type': 'TargetingSettingDetail',
                            'criterionTypeGroup': 'PLACEMENT',
                            'targetAll': 'false',
                        },
                        # Using your ad group verticals only for bidding. This is
                        # equivalent to choosing "Bid only" in the UI.
                        {
                            'xsi_type': 'TargetingSettingDetail',
                            'criterionTypeGroup': 'VERTICAL',
                            'targetAll': 'true',
                        },
                    ]
                }
            ]
        }
    }]

    try:
        ad_groups = ad_group_service.mutate(operations)
    except suds.WebFault as e:
        handleError(e)

    # Display results.
    for ad_group in ad_groups['value']:
        print('Ad group with name \'%s\' and id \'%s\' was added.' % (ad_group['name'], ad_group['id']))
    return str(ad_group['id'])


def addKeywords(client, operations):
    print('Adding keywords...')
    ad_group_criterion_service = client.GetService('AdGroupCriterionService', version='v201806')

    try:
        ad_group_criteria = ad_group_criterion_service.mutate(operations)['value']
    except suds.WebFault as e:
        handleError(e)

    # Display results.
    print('Added ' + str(len(operations)) + ' keyword(s):\n')
    for criterion in ad_group_criteria:
        ad_group_id = str(criterion['adGroupId'])
        keyword_id = str(criterion['criterion']['id'])
        text = str(criterion['criterion']['text'])
        match_type = str(criterion['criterion']['matchType'])

        print('\t\t\t\t\t\t\t\tAd Group ID: ' + ad_group_id)
        print('\t\t\t\t\t\t\t\tKeyword ID: ' + keyword_id)
        print('\t\t\t\t\t\t\t\tText: ' + text)
        print('\t\t\t\t\t\t\t\tMatch Type: ' + match_type + '\n')


def get_ad_groups(client, campaignID):  # Returns dictionary where each element is another dictionary with AdGroup Name as key and AdGroup ID as value.
    print('Getting Ad Groups where campaignID=\'' + campaignID + '\' ...')
    PAGE_SIZE = 500
    ad_group_service = client.GetService('AdGroupService', version='v201806')
    adGroups = {}

    # Construct selector and get all ad groups.
    offset = 0
    selector = {
        'fields': ['Id', 'Name', 'Status'],
        'predicates': [
            {
                'field': 'CampaignId',
                'operator': 'EQUALS',
                'values': campaignID
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }
    more_pages = True
    while more_pages:
        page = ad_group_service.get(selector)

        # Display results.
        if 'entries' in page:
            print('Campaign contains ' + str(len(page['entries'])) + ' ad groups:\n')
            i = 1
            for ad_group in page['entries']:
                adGroupName = str(ad_group['name'])
                ad_group_id = str(ad_group['id'])
                adGroupStatus = str(ad_group['status'])
                adGroups[adGroupName] = ad_group_id
                print('\t\t\tAd Group #' + str(i))
                print('\t\t\t\tName: ' + adGroupName)
                print('\t\t\t\tID: ' + ad_group_id)
                print('\t\t\t\tStatus: ' + adGroupStatus + '\n')
                i += 1
        else:
            print('No ad groups were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
    return adGroups


def get_expanded_text_ads(client, ad_group_id):  # Returns dictionary of all the enabled expanded text ads in given ad group
    ##Example return dictionary :
    ## {'171373128155': {'headlinePart1': 'Used Ford Mustang Inventory', 'headlinePart2': 'Midway Ford in Roseville, MN.', 'adType': 'EXPANDED_TEXT_AD', 'description': 'Used Ford Mustang - Currently on sale for just $22,998.', 'id': '171373128155'}}
    print('Getting expanded text ads where ad_group_id=\'' + ad_group_id + '\' ...')
    PAGE_SIZE = 500
    # Initialize appropriate service.
    ad_group_ad_service = client.GetService('AdGroupAdService', version='v201806')

    # Construct selector and get all ads for a given ad group.
    offset = 0
    selector = {
        'fields': ['Id', 'AdGroupId', 'Status', 'HeadlinePart1', 'HeadlinePart2', 'Description'],
        'predicates': [
            {
                'field': 'AdGroupId',
                'operator': 'EQUALS',
                'values': [ad_group_id]
            },
            {
                'field': 'AdType',
                'operator': 'EQUALS',
                'values': ['EXPANDED_TEXT_AD']
            },
            {
                'field': 'Status',
                'operator': 'EQUALS',
                'values': ['ENABLED']
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }
    more_pages = True
    while more_pages:
        page = ad_group_ad_service.get(selector)

        # Display results.
        allAds = {}
        if 'entries' in page:
            print('Ad group contains ' + str(len(page['entries'])) + ' expanded text ad(s):\n')
            i = 1
            for ad in page['entries']:
                adAd = ad['ad']
                adID = str(ad['ad']['id'])
                headlinePart1 = str(ad['ad']['headlinePart1'])
                headlinePart2 = str(ad['ad']['headlinePart2'])
                description = str(ad['ad']['description'])
                # path1 = str(ad['ad']['path1'])
                # path2 = str(ad['ad']['path2'])
                adType = str(ad['ad']['type'])
                adDict = {
                    adID: {
                        'headlinePart1': headlinePart1,
                        'headlinePart2': headlinePart2,
                        'description': description,
                        'id': adID,
                        'adType': adType
                    }
                }  # , 'path1': path1, 'path2': path2
                allAds.update(adDict)
                print('\t\t\t\t\tExpanded Text Ad #' + str(i) + ':')
                print('\t\t\t\t\t\tHeadline Part 1: ' + headlinePart1)
                print('\t\t\t\t\t\tHeadline Part 2: ' + headlinePart2)
                print('\t\t\t\t\t\tDescription: ' + description)
                print('\t\t\t\t\t\tAd ID: ' + adID)
                print('\t\t\t\t\t\tAd Type: ' + adType + '\n')
                i += 1
        else:
            print('No ads were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])

    return allAds


def get_ads(client, ad_group_id):
    ## Takes ad_group_id, gets all ads, returns diciontary: {{adID: {'adAd': adAd}}} keys are the adIDs and the values are the adwords dictionary for the ad
    ## Returns empty dictionary if there are no ads in given ad group
    # adGroupName = get_ad_group_name(client, ad_group_id)
    print('Getting Ads where ad_group_id=\'' + ad_group_id + '\' ...')  # 'and adGroupName=\'' + adGroupName + '\' ...')

    all_ads = {}

    PAGE_SIZE = 500
    # Initialize appropriate service.
    ad_group_ad_service = client.GetService('AdGroupAdService', version='v201806')

    # Construct selector and get all ads for a given ad group.
    offset = 0
    selector = {
        'fields': ['Id', 'AdGroupId', 'Status', 'HeadlinePart1', 'HeadlinePart2', 'Description'],
        'predicates': [
            {
                'field': 'AdGroupId',
                'operator': 'EQUALS',
                'values': [ad_group_id]
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }
    more_pages = True
    while more_pages:
        page = ad_group_ad_service.get(selector)

        # Display results.
        if 'entries' in page:
            for ad in page['entries']:
                # ad_ad = ad['ad']
                # ad_id = ad['ad']['id']
                # ad_dict = {ad_id: {'adAd': ad_ad}}
                ad_dict = {ad['ad']['id']: {'adAd': ad['ad']}}
                all_ads.update(ad_dict)
                print(ad)
        else:
            print('No ads were found.\n')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])

    return all_ads


def get_ad_ids(client, ad_group_id):  # Returns list of adIDs for each expanded text ad in supplied ad group
    print('Getting ID\'s for ads where ad_group_id=\'' + ad_group_id + '\' ...')  # 'and adGroupName=\'' + adGroupName + '\' ...')
    adIDs = []

    PAGE_SIZE = 500
    # Initialize appropriate service.
    ad_group_ad_service = client.GetService('AdGroupAdService', version='v201806')

    # Construct selector and get all ads for a given ad group.
    offset = 0
    selector = {
        'fields': ['Id', 'AdGroupId', 'Status'],
        'predicates': [
            {
                'field': 'AdGroupId',
                'operator': 'EQUALS',
                'values': [ad_group_id]
            },
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }
    more_pages = True
    while more_pages:
        page = ad_group_ad_service.get(selector)

        # Display results.
        if 'entries' in page:
            print('Ad group contains ' + str(len(page['entries'])) + ' ad(s):\n')
            i = 1
            for ad in page['entries']:
                if ad['ad']['type'] == 'EXPANDED_TEXT_AD':
                    adID = str(ad['ad']['id'])
                    adIDs.append(adID)
            print('ID List: ' + str(adIDs) + '\n')
        else:
            print('Ad group contains no ads.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
    return adIDs


def get_ad_group(client, ad_group_id):  # Returns ad group ID (for ad group is active), given client and ad group name
    # print('Getting ad_group_id where adGroupName=\'' + ad_group_id + '\' ...')
    print('Getting ad_group_id where ad_group_id=\'' + ad_group_id + '\' and status is \'ENABLED\'...')
    PAGE_SIZE = 500
    ad_group_service = client.GetService('AdGroupService', version='v201806')

    # Construct selector and get all ad groups.
    offset = 0
    selector = {
        'fields': ['Id', 'Name', 'Status'],
        'predicates': [
            {
                'field': 'Id',
                'operator': 'EQUALS',
                'values': [ad_group_id]
            },
            {
                'field': 'Status',
                'operator': 'EQUALS',
                'values': ['ENABLED']
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }
    more_pages = True
    while more_pages:
        page = ad_group_service.get(selector)

        # Display results.
        if 'entries' in page:
            for ad_group in page['entries']:
                print('Ad group with id \'%s\' and status \'%s\' was found.' % (ad_group['id'], ad_group['status']))
                print('ad_group: ', ad_group)
                print('ad_group[0]: ', ad_group[0])

        else:
            print('No ad groups were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
    return ad_group


def get_ad_group_id(client, campaign_id, ad_group_name):  # Returns ad group ID (for ad group is active), given client and ad group name
    print('Getting ad_group_id where campaign_id = \'' + campaign_id + '\' and ad_group_name=\'' + ad_group_name + '\' and ad group status is \'ENABLED\' ...')
    PAGE_SIZE = 500
    ad_group_service = client.GetService('AdGroupService', version='v201806')

    # Construct selector and get all ad groups.
    offset = 0
    selector = {
        'fields': ['Id', 'Name', 'Status'],
        'predicates': [
            {
                'field': 'CampaignId',
                'operator': 'EQUALS',
                'values': [campaign_id]
            },
            {
                'field': 'Name',
                'operator': 'EQUALS',
                'values': [ad_group_name]
            },
            {
                'field': 'Status',
                'operator': 'EQUALS',
                'values': ['ENABLED']
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }
    more_pages = True
    while more_pages:
        page = ad_group_service.get(selector)

        # Display results.
        if 'entries' in page:
            for ad_group in page['entries']:
                print('Ad group with name \'%s\' and id \'%s\' and status \'%s\' was found.' % (ad_group['name'], ad_group['id'], ad_group['status']))
                ad_group_id = str(ad_group['id'])
        else:
            print('No ad groups were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
    return ad_group_id


def get_ad_group_name(client, ad_group_id):  # Returns ad group name, given client and ad group ID
    print('Getting adGroupName where ad_group_id=\'' + ad_group_id + '\' ...')
    PAGE_SIZE = 500
    ad_group_service = client.GetService('AdGroupService', version='v201806')

    # Construct selector and get all ad groups.
    offset = 0
    selector = {
        'fields': ['Id', 'Name', 'Status'],
        'predicates': [
            {
                'field': 'Id',
                'operator': 'EQUALS',
                'values': [ad_group_id]
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }
    more_pages = True
    while more_pages:
        page = ad_group_service.get(selector)

        # Display results.
        if 'entries' in page:
            for ad_group in page['entries']:
                print('Ad group with name \'%s\' and status \'%s\' was found.\n' % (ad_group['name'], ad_group['status']))
                adGroupName = str(ad_group['name'])
        else:
            print('No ad groups were found.')
            adGroupName = None
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
    return adGroupName


def get_campaign_names(client):  # Returns names of all active campaigns
    campaignNames = []
    # Initialize appropriate service.
    campaign_service = client.GetService('CampaignService', version='v201806')

    # Construct selector and get all campaigns.
    offset = 0
    selector = {
        'fields': ['Id', 'Name', 'Status'],
        'predicates': [
            {
                'field': 'Status',
                'operator': 'EQUALS',
                'values': ['ENABLED']
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }

    more_pages = True
    while more_pages:
        page = campaign_service.get(selector)

        # Display results.

        if 'entries' in page:
            print('Client account has ' + str(len(page['entries'])) + ' campaigns.\n')
            for campaign in page['entries']:
                campaign_id = campaign['id']
                name = campaign['name']
                status = campaign['status']
                campaignNames.append(name)
        else:
            print('No campaigns were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
        time.sleep(1)
    return campaignNames


def get_campaign_name(client, campaign_id):  # Returns name of campaign for given campaign id
    # Initialize appropriate service.
    campaign_service = client.GetService('CampaignService', version='v201806')

    # Construct selector and get all campaigns.
    offset = 0
    selector = {
        'fields': ['Id', 'Name', 'Status'],
        'predicates': [
            {
                'field': 'Id',
                'operator': 'EQUALS',
                'values': [campaign_id]
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        }
    }

    more_pages = True
    while more_pages:
        page = campaign_service.get(selector)

        # Display results.

        if 'entries' in page:
            print('Client account has ' + str(len(page['entries'])) + 'campaigns.\n')
            for campaign in page['entries']:
                name = campaign['name']
                campaignNames.append(name)
        else:
            print('No campaigns were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])
        time.sleep(1)
    return campaignName


def get_keywords(client, ad_group_id, print_results=False):  # Returns list of keyword objects for given ad group data can be accessed like: keyword['criterion']['id'] OR keyword['criterion']['text']

    if print_results:
        print('Getting keywords where ad_group_id=\'' + ad_group_id + '\' ...')
    fresh_keyword_list = []
    keywordList = []

    # Initialize appropriate service.
    ad_group_criterion_service = client.GetService('AdGroupCriterionService', version='v201806')

    # Construct selector and get all ad group criteria.
    PAGE_SIZE = 500
    offset = 0
    selector = {
        'fields': ['Id', 'CriteriaType', 'KeywordMatchType', 'KeywordText'],
        'predicates': [
            {
                'field': 'AdGroupId',
                'operator': 'EQUALS',
                'values': [ad_group_id]
            },
            {
                'field': 'CriteriaType',
                'operator': 'EQUALS',
                'values': ['KEYWORD']
            },
            {
                'field': 'Status',
                'operator': 'EQUALS',
                'values': ['ENABLED']
            }
        ],
        'paging': {
            'startIndex': str(offset),
            'numberResults': str(PAGE_SIZE)
        },
        'ordering': [{'field': 'KeywordText', 'sortOrder': 'ASCENDING'}]
    }
    more_pages = True
    while more_pages:
        page = ad_group_criterion_service.get(selector)

        # Display results.
        if 'entries' in page:
            print('Ad Group contains ' + str(len(page['entries'])) + ' keyword(s):\n')
            i = 1
            for keyword in page['entries']:
                keyword_id = str(keyword['criterion']['id'])
                keyword_type = str(keyword['criterion']['type'])
                text = str(keyword['criterion']['text'])
                match_type = str(keyword['criterion']['matchType'])
                ad_group_criterion_type = str(keyword['AdGroupCriterion.Type'])
                fresh_keyword_list.append(text)
                keywordList.append(keyword)

                # Print results
                if print_results:
                    print('\t\t\t\t\t\t\tKeyword #' + str(i) + ':')
                    print('\t\t\t\t\t\t\t\tID: ' + keyword_id)
                    print('\t\t\t\t\t\t\t\tCriterion Type: ' + ad_group_criterion_type)
                    print('\t\t\t\t\t\t\t\tType: ' + keyword_type)
                    print('\t\t\t\t\t\t\t\tMatch Type: ' + match_type)
                    print('\t\t\t\t\t\t\t\tText: ' + text + '\n')
                    i += 1
        else:
            print('No keywords were found.')
        offset += PAGE_SIZE
        selector['paging']['startIndex'] = str(offset)
        more_pages = offset < int(page['totalNumEntries'])

    # return fresh_keyword_list
    return keywordList


def remove_ad_group(client, ad_group_id):  # Removes Ad Group for given ad_group_id
    print('Removing ad group with id=\'' + ad_group_id + '\' ...')
    # Initialize appropriate service.
    ad_group_service = client.GetService('AdGroupService', version='v201806')

    # Construct operations and delete ad group.
    operations = [{
        'operator': 'SET',
        'operand': {
            'id': ad_group_id,
            'status': 'REMOVED'
        }
    }]
    try:
        result = ad_group_service.mutate(operations)
    except suds.WebFault as e:
        handleError(e)

    # Display results.
    for ad_group in result['value']:
        print('Ad group with name \'%s\' and id \'%s\' was deleted.'
              % (ad_group['name'], ad_group['id']))


def remove_ad(client, ad_group_id, ad_id):
    print('Removing ad where ad_group_id=\'' + ad_group_id + ' and ad_id=\'' + ad_id + '\'.')

    # Initialize appropriate service.
    ad_group_ad_service = client.GetService('AdGroupAdService', version='v201806')

    # Construct operations and delete ad.
    operations = [{
        'operator': 'REMOVE',
        'operand': {
            'xsi_type': 'AdGroupAd',
            'adGroupId': ad_group_id,
            'ad': {
                'id': ad_id
            }
        }
    }]
    try:
        result = ad_group_ad_service.mutate(operations)
    except suds.WebFault as e:
        handleError(e)

    # Display results.
    for ad in result['value']:
        print('Ad with id \'%s\' and type \'%s\' was deleted.'
              % (ad['ad']['id'], ad['ad']['Ad.Type']))


def remove_keyword(client, ad_group_id, criterion_id):

    # Initialize appropriate service.
    ad_group_criterion_service = client.GetService('AdGroupCriterionService', version='v201806')

    # Construct operations and delete ad group criteria.
    operations = [
        {
            'operator': 'REMOVE',
            'operand': {
                'xsi_type': 'BiddableAdGroupCriterion',
                'adGroupId': ad_group_id,
                'criterion': {
                    'id': criterion_id
                }
            }
        }
    ]

    result = ad_group_criterion_service.mutate(operations)

    # Display results.
    for criterion in result['value']:
        print(('Ad group criterion with ad group id \'%s\', criterion id \'%s\', criterion text \'%s\', and type \'%s\' was deleted.'
               % (criterion['adGroupId'], criterion['criterion']['id'], criterion['criterion']['text'], criterion['criterion']['Criterion.Type'])))


# -------------------Functions that call Adwords Functions-------------------#



def search_ads(client, ad_group_id, search_term_dict):  # returns True if all search terms found or False if one not found
    # searchTerms = {'stock': ['search_term1', 'search_term2'], 'lease': ['search_term1', 'search_term2']}
    print('searchTermDict:', search_term_dict)
    print('Checking Ad Group ID ' + ad_group_id + ' to see if it needs updates.')
    text_ads = get_expanded_text_ads(client, ad_group_id)
    print('textAds:', text_ads)

    search_results = []

    for indicator in search_term_dict.keys():
        indicator_found = False
        print('\n\nChecking indicator:', indicator)
        for ad_id in text_ads:
            print('\n\tAd ID: ', ad_id)
            print('\tAd Headline 1:', text_ads[ad_id]['headlinePart1'])
            print('\tAd Headline 2:', text_ads[ad_id]['headlinePart2'])
            print('\tAd Description:', text_ads[ad_id]['description'], '\n')

            # Return false if search term dict is empty because that means there are no ads for this ad type

            if indicator in text_ads[ad_id]['description'] or indicator in text_ads[ad_id]['headlinePart1'] or indicator in text_ads[ad_id]['headlinePart2']:
                indicator_found = True

                # This would indicate that should be no ads of this type right now if there are no search terms
                print('search_term_dict[indicator]:', search_term_dict[indicator])
                if search_term_dict[indicator]:
                    print('\t\tSearching ' + indicator + ' ad for strings ' + str(search_term_dict[indicator]) + ' in ad_id ' + ad_id)
                    for search_term in search_term_dict[indicator]:
                        if search_term not in text_ads[ad_id]['headlinePart1'] and search_term not in text_ads[ad_id]['headlinePart2'] and search_term not in text_ads[ad_id]['description']:
                            print('\t\tSearch term [\'' + search_term + '\'] NOT contained in headlines/description.')
                            search_results.append([indicator, ad_id, False])
                            break
                        else:
                            print('\t\tSearch term [\'' + search_term + '\'] contained in headlines/description.')
                            search_results.append([indicator, ad_id, True])
                else:
                    print('\t\tNo data available for ad type [\'' + indicator + '\'].')
                    search_results.append([indicator, ad_id, False])
            else:  # remove later i hope
                print('\n\t\tThis is not the ' + indicator + ' ad')
        if not indicator_found and search_term_dict[indicator]:  # if no ads of this type were found but there should be ads for this type
            print('No ads were found containing any of the indicator words:', indicator)
            search_results.append([indicator, None, False])

    return search_results


def update_make_model_keywords(ad_group_id, inv_type, year, make, model):
    print('Updating keywords where ad_group_id=\'' + ad_group_id + '\' ...')

    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # if 'Transit' in model and 'New' in inv_type:
    #     print('Skipping because vehicle is some kind of Transit.')
    #     return

    # use this later..
    city_keywords = [
        'roseville',
        'st. paul',
        'saint paul',
        'minneapolis',
        'shoreview',
        'arden hills',
        'white bear lake',
        'new brighton',
        'oakdale',
        'woodbury',
    ]

    general_keywords = [
        'near me',
        'for sale',
        'sale',
        'inventory',
        'deals',
        'discounts',
        'price',
        'specials',
        'finance',
        'finance specials',
        'apr specials'
    ]

    new_inv_keywords = [
        'lease',
        'lease return'
        'lease return specials',
        'rebates',
        'incentives',
    ]

    used_inv_keywords = [
        'low miles',
        'one owner'
    ]

    if inv_type == 'New' and year:
        fresh_keyword_list = [
            year + ' ' + make + ' ' + model + ' roseville',
            year + ' ' + make + ' ' + model + ' saint paul',
            year + ' ' + make + ' ' + model + ' minneapolis',
            year + ' ' + make + ' ' + model + ' near me',
            year + ' ' + make + ' ' + model + ' for sale',
            year + ' ' + make + ' ' + model + ' sale',
            year + ' ' + make + ' ' + model + ' inventory',
            year + ' ' + make + ' ' + model + ' deals',
            year + ' ' + make + ' ' + model + ' rebates',
            year + ' ' + make + ' ' + model + ' incentives',
            year + ' ' + make + ' ' + model + ' discounts',
            year + ' ' + make + ' ' + model + ' price',
            year + ' ' + make + ' ' + model + ' specials',
            year + ' ' + make + ' ' + model + ' lease',
            year + ' ' + make + ' ' + model + ' lease return specials',
        ]
    elif inv_type == 'Used' and year:  # if it's used
        fresh_keyword_list = [
            inv_type + ' ' + make + ' ' + model,
            inv_type + ' ' + make + ' ' + model + ' roseville',
            inv_type + ' ' + make + ' ' + model + ' saint paul',
            inv_type + ' ' + make + ' ' + model + ' minneapolis',
            inv_type + ' ' + make + ' ' + model + ' near me',
            inv_type + ' ' + make + ' ' + model + ' for sale',
            inv_type + ' ' + make + ' ' + model + ' inventory',
            inv_type + ' ' + make + ' ' + model + ' deals',
            inv_type + ' ' + make + ' ' + model + ' low miles',
            inv_type + ' ' + make + ' ' + model + ' one owner',
            inv_type + ' ' + make + ' ' + model + ' cheap',
            inv_type + ' ' + make + ' ' + model + ' price',
            inv_type + ' ' + make + ' ' + model + ' specials',
            year + ' ' + make + ' ' + model + ' roseville',
            year + ' ' + make + ' ' + model + ' saint paul',
            year + ' ' + make + ' ' + model + ' minneapolis',
            year + ' ' + make + ' ' + model + ' for sale',
            year + ' ' + make + ' ' + model + ' inventory',
            year + ' ' + make + ' ' + model + ' deals',
            year + ' ' + make + ' ' + model + ' low miles',
            year + ' ' + make + ' ' + model + ' one owner',
            year + ' ' + make + ' ' + model + ' cheap',
            year + ' ' + make + ' ' + model + ' price',
            year + ' ' + make + ' ' + model + ' specials',
        ]
    else:
        raise ValueError('Vehicle is neither New or Used or else is Used and has no Year.')

    # Add keyword that includes trim (if it exists)
    query = 'SELECT DISTINCT vehTrim FROM masterInventory WHERE invType = ? AND year = ? AND model = ?'
    to_db = (inv_type, year, model,)
    c.execute(query, to_db)
    results = c.fetchall()
    if results:
        for r in results:
            veh_trim = r[0]
            trim_keyword = fresh_keyword_list[0] + ' ' + veh_trim + ' near me'
            fresh_keyword_list.append(trim_keyword)

    # Add keyword that include drive
    query = 'SELECT DISTINCT drive FROM masterInventory WHERE invType = ? AND year = ? AND model = ?'
    to_db = (inv_type, year, model,)
    c.execute(query, to_db)
    results = c.fetchall()
    if results:
        for r in results:
            drive = r[0]
            drive_keyword = fresh_keyword_list[0] + ' ' + drive + ' near me'
            fresh_keyword_list.append(drive_keyword)

    # Add keywords that include engine
    query = 'SELECT DISTINCT engine FROM masterInventory WHERE invType = ? AND year = ? AND model = ?'
    to_db = (inv_type, year, model,)
    c.execute(query, to_db)
    results = c.fetchall()
    if results:
        for r in results:
            engine = r[0]
            engine_keyword = fresh_keyword_list[0] + ' ' + engine + ' near me'
            fresh_keyword_list.append(engine_keyword)

    # Add keywords that include engine
    query = 'SELECT DISTINCT exteriorColor FROM masterInventory WHERE invType = ? AND year = ? AND model = ?'
    to_db = (inv_type, year, model,)
    c.execute(query, to_db)
    results = c.fetchall()
    if results:
        for r in results:
            color = r[0]
            color_keyword = fresh_keyword_list[0] + ' ' + color + ' near me'
            fresh_keyword_list.append(color_keyword)

    # Get keywords currently in ad group (old keywords)
    #print('Old Keywords:')
    old_keywords = get_keywords(client, ad_group_id)
    old_keyword_list = []
    for k, old_keyword in enumerate(old_keywords):
        #print(old_keyword)
        old_keyword_list.append(old_keyword['criterion']['text'])

    # Build list of keyword operands
    keyword_operand_list = []
    for keywordText in fresh_keyword_list:
        word_list = keywordText.split(' ')

        # Skip for validity
        if len(keywordText) > 80 or len(word_list) > 10:
            print('Keyword \'{}\' is invalid.'.format(keywordText))
            continue

        # Skip if already in ad group
        if keywordText in old_keyword_list:
            print('Keyword \'' + keywordText + '\' already contained in ad group.')
            continue

        # Add keyword
        else:
            print('Keyword \'' + keywordText + '\' not contained in ad group \'' + ad_group_id + '\' yet.')
            print('Building operations to add keyword \'' + keywordText + '\' to ad group \'' + ad_group_id + '\'.')
            keyword_operand = {
                'xsi_type': 'BiddableAdGroupCriterion',
                'adGroupId': ad_group_id,
                'criterion': {
                    'xsi_type': 'Keyword',
                    'matchType': 'BROAD',
                    'text': keywordText
                },
                'userStatus': 'ENABLED'
            }
            keyword_operand_list.append(keyword_operand)

    # Add other Ford model names as negative keywords and make the operands
    if inv_type == 'New':

        # Build list of other model names
        query = 'SELECT DISTINCT model FROM masterInventory WHERE model != ? AND invType = ?'
        to_db = (model, 'New')
        c.execute(query, to_db)
        other_models = c.fetchall()
        print('other_model_names', other_models)
        for i, o in enumerate(other_models):
            other_models[i] = o[0]

        # Build list of operands
        for other_model in other_models:
            fresh_keyword_list.append(other_model)
            if other_model in old_keyword_list:
                print('Keyword \'' + other_model + '\' already contained in ad group.')
                continue
            else:
                print('Keyword \'' + other_model + '\' not contained in ad group \'' + ad_group_id + '\' yet.')
                print('Building operations to add keyword \'' + other_model + '\' to ad group \'' + ad_group_id + '\'.')
                keyword_operand = {
                    'xsi_type': 'NegativeAdGroupCriterion',
                    'adGroupId': ad_group_id,
                    'criterion': {
                        'xsi_type': 'Keyword',
                        'matchType': 'PHRASE',
                        'text': other_model
                    }
                }
                keyword_operand_list.append(keyword_operand)



    # Add other years as negative keywords
    year_today = datetime.date.today().year

    max_year = year_today + 2
    min_year = int(year) - 20

    neg_year_list = [str(y) for y in range(min_year, max_year)]
    neg_year_list.remove(year)
    fresh_keyword_list += neg_year_list
    print('year:', year)
    print('neg_year_list:', neg_year_list)

    # Build list of operands
    for neg_year in neg_year_list:
        # fresh_keyword_list.append(neg_year)
        if neg_year in old_keyword_list:
            print('Keyword \'' + neg_year + '\' already contained in ad group.')
            continue
        else:
            print('Keyword \'' + neg_year + '\' not contained in ad group \'' + ad_group_id + '\' yet.')
            print('Building operations to add keyword \'' + neg_year + '\' to ad group \'' + ad_group_id + '\'.')
            keyword_operand = {
                'xsi_type': 'NegativeAdGroupCriterion',
                'adGroupId': ad_group_id,
                'criterion': {
                    'xsi_type': 'Keyword',
                    'matchType': 'PHRASE',
                    'text': neg_year
                }
            }
            keyword_operand_list.append(keyword_operand)

    operations = []
    for keyword_operand in keyword_operand_list:
        keyword_operation = {
            'operator': 'ADD',
            'operand': keyword_operand
        }
        operations.append(keyword_operation)

    if operations:
        addKeywords(client, operations)

    # Remove obsolete keywords
    del_count = 0
    for i, old_keyword in enumerate(old_keywords):
        if old_keyword['criterion']['text'] not in fresh_keyword_list:
            criterion_id = old_keyword['criterion']['id']
            # print('Removing keyword:', old_keyword)
            remove_keyword(client, ad_group_id, criterion_id)

    # Print summary
    print('{} keywords added (or at least I tried to add them).'.format(len(keyword_operand_list)))
    print('{} keywords removed.'.format(del_count))

    # Close connection to database
    conn.close()


def update_make_model_ads(ad_group_id, ad_group_name, inv_type, year, make, model, min_price, max_discount, rebate_expiration, quantity, special_results, ad_type='all'):
    print('Updating ads for ' + ad_group_name + ' ad group ...')

    # Initialize variables
    operations = []

    # Clean up model
    #model = model.replace(' Hybrid', '').replace(' Energi', '').replace(' Connect', '')
    model = simplify_model_name(model)


    # Figure out a format for model name so url works
    url_formatted_model = model.replace(' ', '%20')


    quantity = int_word_converter(quantity)

    # Build ad for each sales special
    for special in special_results:

        apr = special[0]
        monthly_payment = special[1]
        term_length = special[2]
        down_payment = special[3]
        due_at_signing = special[4]
        expiration = special[5]

        final_url = 'https://www.rosevillemidwayford.com/sales-specials'

        if apr and not monthly_payment:  # APR ad
            headline_part_1 = '{} {} {} Finance Offer'.format(year, make, model)
            headline_part_2 = '{} APR for 24-{} months'.format(apr, term_length)
            path1 = 'finance-offers'
        elif due_at_signing:  # Lease ad
            headline_part_1 = '{} {} {} Lease Special'.format(year, make, model)
            headline_part_2 = '{}/month with {} down'.format(monthly_payment, due_at_signing)
            path1 = 'lease-specials'
        elif monthly_payment and down_payment:  # Finance payment ad
            headline_part_1 = '{} {} {} Financing'.format(year, make, model)
            headline_part_2 = '{}/month with {} down'.format(monthly_payment, down_payment)
            path1 = 'finance-offers'
        description = 'Build your own deal using current rates and offers from Midway Ford on our site.'
        path2 = '{}-{}'.format(make.lower(), model.lower().replace(' ', '-'))

        operation = {
            'operator': 'ADD',
            'operand': {
                'xsi_type': 'AdGroupAd',
                'adGroupId': ad_group_id,
                'ad': {
                    'xsi_type': 'ExpandedTextAd',
                    'headlinePart1': headline_part_1,
                    'headlinePart2': headline_part_2,
                    'path1': path1,
                    'path2': path2,
                    'description': description,
                    'finalUrls': [final_url],
                },
                # Optional fields.
                'status': 'ENABLED'
            }
        }
        if 'all' in ad_type:
            operations.append(operation)
        elif 'APR' in ad_type and 'APR' in headline_part_2:
            operations.append(operation)
        elif 'Lease' in ad_type and 'Lease' in headline_part_1:
            operations.append(operation)
        elif 'Financing' in ad_type and 'Financing' in headline_part_1:
            operations.append(operation)

    # Set final url for rest of ads
    final_url = 'https://www.rosevillemidwayford.com/VehicleSearchResults?search=new&make=Ford&model={}&sort=featuredPrice%7Casc'.format(url_formatted_model)

    if 'F-' in model and 'F-150' not in model:
        final_url = 'https://www.rosevillemidwayford.com/VehicleSearchResults?sort=featuredPrice%7Casc&searchQuery=%22super%20duty%22'


    # Make stock ads
    if inv_type == 'New' and year:
        if rebate_expiration and rebate_expiration != 'None':  # if it has a discount and the discount has an expiration
            headline_part_1 = '{} {} {} {} Sale'.format(inv_type, year, make, model)
            headline_part_2 = 'Midway Ford in Roseville, MN.'
            description = 'Currently {} in stock starting at {} with up to {} discount until {}.'.format(quantity, min_price, max_discount, rebate_expiration)
            path1 = '{}-inventory'.format(inv_type.lower())

        elif max_discount:  # if it has a discount but no expiration
            headline_part_1 = '{} {} {} {} Sale'.format(inv_type, year, make, model)
            headline_part_2 = 'Midway Ford in Roseville, MN.'
            description = 'Currently {} in stock starting at {} with up to {} in discounts.'.format(quantity, min_price, max_discount)
            path1 = '{}-inventory'.format(inv_type.lower())

        else:  # if it has no discount and no expiration
            headline_part_1 = '{} {} {} {} Sale'.format(inv_type, year, make, model)
            headline_part_2 = 'Midway Ford in Roseville, MN.'
            description = 'Currently {} in stock starting at {} at Midway Ford in Roseville, MN.'.format(quantity, min_price)
            path1 = '{}-inventory'.format(inv_type.lower())

    elif inv_type == 'New' and not year:  # for the New Make/Model ads   == None
        headline_part_1 = '{} {} {} Sale'.format(inv_type, make, model)
        headline_part_2 = 'Midway Ford in Roseville, MN.'
        description = 'Currently {} in stock starting at {} at Midway Ford in Roseville, MN.'.format(quantity, min_price)
        path1 = '{}_Inventory'.format(inv_type.lower())

    # If used vehicle
    else:
        final_url = 'https://www.rosevillemidwayford.com/VehicleSearchResults?search=preowned&sort=featuredPrice%7Casc&model={}'.format(url_formatted_model)

        # need to add script to check final url for error code

        headline_part_1 = '{} {} {} {} Sale'.format(inv_type, year, make, model)
        headline_part_2 = 'Midway Ford in Roseville, MN.'
        description = '{} {} {} {} - Currently {} in stock starting at {}.'.format(inv_type, year, make, model, quantity, min_price)
        path1 = '{}-inventory'.format(inv_type.lower())

    path2 = '{}-{}'.format(make.lower(), model.lower().replace(' ', '-'))
    # headline_part_3 = 'Your Twin Cities Ford Dealer.'
    # description_2 = 'Family-owned and operated since 1954.'

    if ' one in stock' in description:
        description = description.replace('starting', 'priced')

    operation = {
        'operator': 'ADD',
        'operand': {
            'xsi_type': 'AdGroupAd',
            'adGroupId': ad_group_id,
            'ad': {
                'xsi_type': 'ExpandedTextAd',
                'headlinePart1': headline_part_1,
                'headlinePart2': headline_part_2,
                'path1': path1,
                'path2': path2,
                'description': description,
                'finalUrls': [final_url],
            },
            # Optional fields.
            'status': 'ENABLED'
        }
    }

    if 'all' in ad_type or 'stock' in ad_type:
        operations.append(operation)

    operations, invalid_operations = check_ad_validity(operations, inv_type, make, model)
    if operations:
        addAds(client, operations)
    else:
        print('ALERT: Not adding ads because no operations were valid.')

    return invalid_operations


def check_ad_validity(operations, inv_type, make, model):
    print('Checking ad operations for validity...')
    valid_operations = []
    invalid_operations = []
    for operation in operations:

        if len(operation['operand']['ad']['headlinePart1']) > 30:
            print('Invalid headline_1')
            print(operation['operand']['ad']['headlinePart1'])
            operation['operand']['ad']['headlinePart1'] = operation['operand']['ad']['headlinePart1'].replace('New ', '').replace('Used ', '')
            print('New headline_1:', operation['operand']['ad']['headlinePart1'])
            if len(operation['operand']['ad']['headlinePart1']) > 30:
                operation['operand']['ad']['headlinePart1'] = operation['operand']['ad']['headlinePart1'].replace(' Special', ' Offer')
                print('New headline_1:', operation['operand']['ad']['headlinePart1'])
                if len(operation['operand']['ad']['headlinePart1']) > 30:
                    operation['operand']['ad']['headlinePart1'] = operation['operand']['ad']['headlinePart1'].replace(' Offer', '')
                    print('New headline_1:', operation['operand']['ad']['headlinePart1'])
                    if len(operation['operand']['ad']['headlinePart1']) > 30:
                        print('Still broken')
                        invalid_operations.append(operation)
                        break
        else:
            print('Valid Headline #1')
            print('Headline #1:', operation['operand']['ad']['headlinePart1'])

        if len(operation['operand']['ad']['headlinePart2']) > 30:
            print('Invalid headline_2')
            operation['operand']['ad']['headlinePart2'] = operation['operand']['ad']['headlinePart2'].replace('New ', '').replace('Used ', '')
            print('New headline_2:', operation['operand']['ad']['headlinePart2'])
            if len(operation['operand']['ad']['headlinePart2']) > 30:
                print('Still broken')
                invalid_operations.append(operation)
                break
        else:
            print('Valid Headline #2')
            print('Headline #2:', operation['operand']['ad']['headlinePart2'])

        if len(operation['operand']['ad']['description']) > 90:
            print('Invalid description')
            print(operation['operand']['ad']['description'])
            operation['operand']['ad']['description'] = operation['operand']['ad']['description'].replace(inv_type + ' ' + make + ' ' + model + ' - ', '')
            print('New description:', operation['operand']['ad']['description'])
            if len(operation['operand']['ad']['description']) > 90:
                operation['operand']['ad']['description'] = operation['operand']['ad']['description'].replace('.', '')
                print('New description:', operation['operand']['ad']['description'])
                if len(operation['operand']['ad']['description']) > 90:
                    print('Still broken')
                    invalid_operations.append(operation)
                    break
        else:
            print('Valid description')
            print('Description:', operation['operand']['ad']['description'])

        if len(operation['operand']['ad']['path1']) > 15:
            print('Invalid path1')
            print('Path 1:', operation['operand']['ad']['path1'])
            invalid_operations.append(operation)
            break
        else:
            print('Valid path1')
            print('Path 1:', operation['operand']['ad']['path2'])

        if len(operation['operand']['ad']['path2']) > 15:
            print('Invalid path2')
            operation['operand']['ad']['path2'] = operation['operand']['ad']['path2'].replace(make.lower() + '-', '')
            print('New path2:', operation['operand']['ad']['path2'])
            if len(operation['operand']['ad']['path2']) > 15:
                print('Still broken')
                invalid_operations.append(operation)
                break
        else:
            print('Valid path1')
            print('Path 2:', operation['operand']['ad']['path2'])

        valid_operations.append(operation)
    print('Finished checking ad operations for validity.')
    return valid_operations, invalid_operations


def create_price_table_row(header, description, final_url, price_in_micros, currency_code, price_unit, final_mobile_url=None):
    """Helper function to generate a single row of a price table.
    Args:
      header: A str containing the header text of this row.
      description: A str description of this row in the price table.
      final_url: A str containing the final URL after all cross domain redirects.
      price_in_micros: An int indicating the price of the given currency in
        micros.
      currency_code: A str indicating the currency code being used.
      price_unit: A str enum indicating the price unit for this row.
      final_mobile_url: A str containing the final mobile URL after all cross
        domain redirects.
    Returns:
      A dictionary containing the contents of the generated price table row.
    """
    table_row = {
        'header': header,
        'description': description,
        'finalUrls': {'urls': [final_url]},
        'price': {
            'money': {
                'microAmount': price_in_micros,
            },
            'currencyCode': currency_code
        },
        'priceUnit': price_unit,
        'xsi_type': 'PriceTableRow'
    }

    if final_mobile_url:
        table_row['finalMobileUrls'] = {
            'urls': [final_mobile_url]
        }

    return table_row


def build_price_extension_operand(ad_group_id, table_rows, expiration):
    operand = {
        'adGroupId': ad_group_id,
        'extensionType': 'PRICE',
        'extensionSetting': {
            'extensions': [{
                'priceExtensionType': 'PRODUCT_CATEGORIES',
                'trackingUrlTemplate': None,  # 'http://tracker.example.com/?u={lpurl}',
                'language': 'en',
                # 'campaignTargeting': {
                #     'TargetingCampaignId': campaign_id
                # },
                'adGroupTargeting': {
                    'TargetingAdGroupId': ad_group_id
                },
                'startTime': '20171210 000000',
                'endTime': expiration,
                'tableRows': table_rows,
                # Price qualifier is optional.
                'priceQualifier': None,
                'xsi_type': 'PriceFeedItem'
            }]
        }
    }

    return operand


def build_price_extension_operations(ad_group_id, inv_type, make, model):
    # Static variables
    MICROS_PER_DOLLAR = 1000000

    # Set default expiration
    current_year = datetime.date.today().year
    current_month = datetime.date.today().month
    current_month = current_month
    last_day_of_month = calendar.monthrange(current_year, current_month)[1]
    if len(str(current_month)) == 1:
        current_month = '0' + str(current_month)
    expiration = '{}{}{} 000000'.format(current_year, current_month, last_day_of_month)

    # Connect to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    operations = []
    finance_operations = []

    #for special_type in special_type_list:
    # for model_list in model_list_list:

    # Initialize table_rows
    finance_table_rows = []
    lease_table_rows = []

    # Get Sales Special info from db
    query = ('SELECT DISTINCT finance_payment '
             'FROM masterInventory '
             'WHERE invType = ? AND make = ? AND model = ? '
             'ORDER BY finance_payment ASC')
    to_db = (inv_type, make, model)
    c.execute(query, to_db)
    results = c.fetchall()
    pprint(results)


    for r in results:
        # Get parameters from db results
        finance_payment = r[0]

        if finance_payment:
            query = ('SELECT vdp_url, year '
                     'FROM masterInventory '
                     'WHERE invType = ? AND make = ? AND model = ? AND finance_payment = ?')

            to_db = (inv_type, make, model, finance_payment)
            c.execute(query, to_db)
            sub_results = c.fetchall()
            print(sub_results)
            vdp_url = sub_results[0][0]
            year = sub_results[0][1]
        else:
            continue

        # Set parameters for create_price_table_row
        final_url = vdp_url
        currency_code = 'USD'
        price_unit = 'PER_MONTH'

        # Add finance row
        if finance_payment:
            header = '{} {} - {}/mo'.format(year, model, finance_payment)
            description = 'Finance for 60 months'
            price_in_micros = finance_payment * MICROS_PER_DOLLAR
            table_row = create_price_table_row(header, description, final_url, price_in_micros, currency_code, price_unit, final_mobile_url=None)
            finance_table_rows.append(table_row)
        if len(finance_table_rows) >= 8:
            break

        # # Add lease row
        # if lease_payment:
        #     header = '{} {} - {}/mo'.format(year, model, lease_payment)
        #     description = '36-Month Lease'
        #     price_in_micros = lease_payment * MICROS_PER_DOLLAR
        #     table_row = create_price_table_row(header, description, final_url, price_in_micros, currency_code, price_unit, final_mobile_url=None)
        #     lease_table_rows.append(table_row)
        # if len(lease_table_rows) >= 8:
        #     break

    for t in finance_table_rows:
        print(t)
    print('finance_table_rows length:', len(finance_table_rows))

    if len(finance_table_rows) >= 3:
        operand = build_price_extension_operand(ad_group_id, finance_table_rows, expiration)
        finance_operations.append({'operator': 'SET', 'operand': operand})

    # if len(lease_table_rows) >= 3:
    #     operand = build_price_extension_operand(ad_group_id, lease_table_rows, expiration)
    #     operations.append({'operator': 'SET', 'operand': operand})

    for o in finance_operations:
        print(o)

    return finance_operations



def update_sales_price_extensions():
    # Static variables
    MICROS_PER_DOLLAR = 1000000
    special_type_list = ['lease', 'finance']
    model_list = ['Focus', 'Fusion', 'Escape', 'Explorer', 'Edge', 'F-150']

    # Connect to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    operations = []


    for special_type in special_type_list:
        # for model_list in model_list_list:

        # Initialize table_rows
        table_rows = []

        for model in model_list:
            # Get Sales Special info from db
            query = ('SELECT min(monthly_payment), min(apr), term_length '
                     'FROM salesSpecials '
                     'WHERE special_type = ? AND model = ?')
            to_db = (special_type, model)
            c.execute(query, to_db)
            results = c.fetchall()

            # Get parameters from db results
            monthly_payment = results[0][0]
            apr = results[0][1]
            term_length = results[0][2]

            # Get proper year and expiration
            if not apr:
                apr = None
            if not monthly_payment:
                monthly_payment = None
            query = ('SELECT year, expiration '
                     'FROM salesSpecials '
                     'WHERE special_type = ? AND model = ? AND monthly_payment IS ? AND apr IS ?')
            to_db = (special_type, model, monthly_payment, apr)
            c.execute(query, to_db)
            results = c.fetchall()
            year = results[0][0]
            expiration = results[0][1].replace('/', '') + ' 000000'

            # Get lowest price for this model (used to calculate monthly payment)
            query = ('SELECT min(intPrice) '
                     'FROM masterInventory '
                     'WHERE invType = ? AND year = ? AND model = ?')
            to_db = ('New', year, model)
            c.execute(query, to_db)
            results = c.fetchall()
            lowest_price = results[0][0]

            # Set parameters for create_price_table_row
            header = '{} Ford {}'.format(year, model)
            final_url = 'https://rosevillemidwayford.com/sales-specials'
            currency_code = 'USD'
            price_unit = 'PER_MONTH'
            if apr:
                # Skip model if no models of this type in stock
                if not lowest_price:
                    continue
                ad_group_id = '47180029660'
                #monthly_payment = loan_payment(float(lowest_price), float(apr.replace('%', '')), float(term_length))

                price_in_micros = monthly_payment * MICROS_PER_DOLLAR
                description = '{} APR for 24-{} mo'.format(apr, term_length)
            else:
                ad_group_id = '44603992037'
                monthly_payment = int(monthly_payment.replace('$', '').replace(',', ''))
                price_in_micros = monthly_payment * MICROS_PER_DOLLAR
                description = '{}-Month Lease'.format(term_length)

            # Build table row and add to table_rows
            table_row = create_price_table_row(header, description, final_url, price_in_micros, currency_code, price_unit, final_mobile_url=None)
            table_rows.append(table_row)
        for t in table_rows:
            print(t)
        print('len', len(table_rows))

        if len(table_rows) >= 3:
            operand = build_price_extension_operand(ad_group_id, table_rows, expiration)
            operations.append({'operator': 'SET', 'operand': operand})

    for o in operations:
        print('operation', o)
    add_price_extension(client, operations)


def update_specials_price_extension(ad_group_id, inv_type, make, model):
    # Static variables
    MICROS_PER_DOLLAR = 1000000

    # Set default expiration
    current_year = datetime.date.today().year
    current_month = datetime.date.today().month
    current_month = current_month
    last_day_of_month = calendar.monthrange(current_year, current_month)[1]
    if len(str(current_month)) == 1:
        current_month = '0' + str(current_month)
    expiration = '{}{}{} 000000'.format(current_year, current_month, last_day_of_month)

    # Connect to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    operations = []
    finance_operations = []

    # for special_type in special_type_list:
    # for model_list in model_list_list:

    # Initialize table_rows
    finance_table_rows = []
    lease_table_rows = []

    # Get Sales Special info from db
    query = ('SELECT DISTINCT finance_payment '
             'FROM masterInventory '
             'WHERE invType = ? AND make = ? AND model = ? '
             'ORDER BY finance_payment ASC')
    to_db = (inv_type, make, model)
    c.execute(query, to_db)
    results = c.fetchall()
    pprint(results)

    for r in results:
        # Get parameters from db results
        finance_payment = r[0]

        if finance_payment:
            query = ('SELECT vdp_url, year '
                     'FROM masterInventory '
                     'WHERE invType = ? AND make = ? AND model = ? AND finance_payment = ?')

            to_db = (inv_type, make, model, finance_payment)
            c.execute(query, to_db)
            sub_results = c.fetchall()
            print(sub_results)
            vdp_url = sub_results[0][0]
            year = sub_results[0][1]
        else:
            continue

        # Set parameters for create_price_table_row
        final_url = vdp_url
        currency_code = 'USD'
        price_unit = 'PER_MONTH'

        # Add finance row
        if finance_payment:
            header = '{} {} - {}/mo'.format(year, model, finance_payment)
            description = 'Finance for 60 months'
            price_in_micros = finance_payment * MICROS_PER_DOLLAR
            table_row = create_price_table_row(header, description, final_url, price_in_micros, currency_code, price_unit, final_mobile_url=None)
            finance_table_rows.append(table_row)
        if len(finance_table_rows) >= 8:
            break

            # # Add lease row
            # if lease_payment:
            #     header = '{} {} - {}/mo'.format(year, model, lease_payment)
            #     description = '36-Month Lease'
            #     price_in_micros = lease_payment * MICROS_PER_DOLLAR
            #     table_row = create_price_table_row(header, description, final_url, price_in_micros, currency_code, price_unit, final_mobile_url=None)
            #     lease_table_rows.append(table_row)
            # if len(lease_table_rows) >= 8:
            #     break

    for t in finance_table_rows:
        print(t)
    print('finance_table_rows length:', len(finance_table_rows))

    if len(finance_table_rows) >= 3:
        operand = build_price_extension_operand(ad_group_id, finance_table_rows, expiration)
        finance_operations.append({'operator': 'SET', 'operand': operand})

    # if len(lease_table_rows) >= 3:
    #     operand = build_price_extension_operand(ad_group_id, lease_table_rows, expiration)
    #     operations.append({'operator': 'SET', 'operand': operand})

    for o in finance_operations:
        print(o)

    return finance_operations


def add_price_extension(client, operations):
    ad_group_extension_setting_service = client.GetService(
        'AdGroupExtensionSettingService', 'v201806')

    # Add the price extension.
    response = ad_group_extension_setting_service.mutate(operations)

    # Print the results.
    if 'value' in response:
        print('Extension setting with type "%s" was added to your account.'
              % response['value'][0]['extensionType'])
    else:
        raise errors.GoogleAdsError('No extension settings were added.')


def get_price_extensions(client, ad_group_id):
    ad_group_extension_setting_service = client.GetService(
        'AdGroupExtensionSettingService', 'v201806')

    selector = {
        'fields': ['AdGroupId', 'ExtensionType', 'Extensions'],
        'predicates': [
            {
                'operator': 'EQUALS',
                'field': 'AdGroupId',
                'values': [ad_group_id]
            },
            {
                'operator': 'EQUALS',
                'field': 'ExtensionType',
                'values': ['PRICE']
            }
        ]
    }

    page = ad_group_extension_setting_service.get(selector)

    ad_group_extension_setting = page['entries'][0]
    extensions = ad_group_extension_setting['extensionSetting']['extensions']

    for extension_feed_item in extensions:
        pprint(extension_feed_item)


        #print('tableRows', extension_feed_item['tableRows'])

        for row in extension_feed_item['tableRows']:
            print(row['header'])
            print(row['price']['money']['microAmount'])

            if row['header'] == '2017 Ford Focus':
                row['header'] = 'Nonsense'

                # if 'Happy hours' == extension_feed_item['sitelinkText']:
                #     schedules = extension_feed_item['scheduling']['feedItemSchedules']
                #     for feed_item_schedule in schedules:
                #         if feed_item_schedule['dayOfWeek'] == 'FRIDAY':
                #             feed_item_schedule['startHour'] = 17
                #             feed_item_schedule['startMinute'] = 'ZERO'
                #             feed_item_schedule['endHour'] = 22
                #             feed_item_schedule['endMinute'] = 'ZERO'

    operations = [{
        'operator': 'SET',
        'operand': ad_group_extension_setting
    }]

    response = ad_group_extension_setting_service.mutate(operations)

    return response


def update_sales_campaigns():

    # Connect to database
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()

    # Initial variables
    inv_types = ['New', 'Used']
    campaign_ids = {
        'Used SEM - General': '630207548',
        'Used SEM - Make/Model': '732771041',
        # 'Used SEM - VIN Specific': '650887673',
        'New SEM - Make/Model': '619985667',
        # 'New SEM = VIN Specific': '409989124'
    }
    added_ad_groups = []
    deleted_ad_groups = []
    updated_ad_groups = []
    invalid_operations = []

    for inv_type in inv_types:
        campaign_name = inv_type + ' SEM - Make/Model'
        campaign_id = campaign_ids[campaign_name]
        print('Updating ' + campaign_name + ' campaign ...')
        # Make list of names of all Ad Groups currently in Used SEM - Make/Model campaign
        old_ad_groups = get_ad_groups(client, campaign_id)
        old_ad_group_names = old_ad_groups.keys()
        old_ad_group_ids = old_ad_groups.values()
        fresh_ad_group_ids = []

        # For each Make for this Type
        c.execute('SELECT DISTINCT make FROM masterInventory WHERE invType = ?', (inv_type,))
        make_results = c.fetchall()
        for makeTuple in make_results:
            make = makeTuple[0]

            # Select each Model for this Make
            c.execute('SELECT DISTINCT model FROM masterInventory WHERE make = ?', (make,))
            model_results = c.fetchall()
            for modelTuple in model_results:  # For each Model with this Make
                model = modelTuple[0]

                query = ('SELECT DISTINCT year '
                         'FROM masterInventory '
                         'WHERE invType = ? AND make = ? AND model = ?')
                to_db = (inv_type, make, model)
                c.execute(query, to_db)
                year_results = c.fetchall()
                for year in year_results:
                    year = year[0]

                    # Add specials info if vehicle is new
                    if inv_type == 'New':

                        query = ('SELECT apr, monthly_payment, term_length, down_payment, due_at_signing, expiration '
                                 'FROM salesSpecials '
                                 'WHERE model = ? AND year = ?')
                        to_db = (model, str(year))
                        c.execute(query, to_db)
                        special_results = c.fetchall()
                    else:
                        special_results = []

                    # Select lowest price, max discount, quantity, and rebate expiration for this Type/Model
                    query = ('SELECT min(NULLIF(intPrice, 0)), count(*), max(intTotalDiscount), rebateExpiration '
                             'FROM masterInventory '
                             'WHERE invType = ? AND make = ? AND model = ? AND year = ?')
                    to_db = (inv_type, make, model, year)
                    c.execute(query, to_db)
                    veh_results = c.fetchall()

                    # Skip some types of vehicles
                    if not veh_results[0][0]:  # skip if min price is 0
                        continue
                    if 'Mustang' in model or 'Chassis' in model:  # skip if model is mustang
                        continue
                    if year < 2017 and inv_type == 'New':  # skip if year is older than 2016
                        continue
                    if 'Transit' in model:  # skip transits for whatever reason
                        print('Skipping because vehicle is some kind of Transit.')
                        continue

                    year = str(year)  # don't think i need to use year as int after this point
                    min_price = veh_results[0][0]
                    quantity = veh_results[0][1]
                    max_discount = veh_results[0][2]
                    rebate_expiration = veh_results[0][3]

                    search_terms = {
                        'stock': [],
                        'APR': [],
                        'Lease': [],
                        'Financing': []
                    }

                    # Add search terms for specials in order to check for updates later
                    for special in special_results:
                        if special[0] and not special[1]:  # if apr and no monthly payment
                            if search_terms['APR']:
                                if search_terms['APR'][0] > special[0]:
                                    search_terms['APR'][0] = special[0]
                        elif special[1] and special[3]:
                            search_terms['Financing'].append(special[1])
                            search_terms['Financing'].append(special[3])
                        elif special[1] and special[4]:
                            search_terms['Lease'].append(special[1])
                            search_terms['Lease'].append(special[4])

                    if min_price:
                        min_price = locale.currency(min_price, grouping=True).replace('.00', '')
                        search_terms['stock'].append(min_price)
                    if quantity:
                        search_terms['stock'].append(' {} '.format(int_word_converter(quantity)))
                    if max_discount or max_discount == 0:
                        max_discount = locale.currency(max_discount, grouping=True).replace('.00', '')
                        search_terms['stock'].append(max_discount)

                    ad_group_name = inv_type + ' ' + year + ' ' + make + ' ' + model
                    print('Checking ad group \'{}\':\n'.format(ad_group_name))
                    print('\t\t\tType: ' + inv_type)
                    print('\t\t\tYear: ' + str(year))
                    print('\t\t\tMake: ' + make)
                    print('\t\t\tModel: ' + model)
                    print('\t\t\tQuantity: ' + str(quantity))
                    print('\t\t\tMin Price: ' + min_price)
                    print('\t\t\tMax Discount: ' + str(max_discount))
                    print('\t\t\tRebate Expiration: ' + str(rebate_expiration) + '\n')

                    if ad_group_name in old_ad_group_names:  # if ad group name already exists
                        print('Campaign already contains ad group with name \'' + ad_group_name + '\'.')
                        ad_group_id = get_ad_group_id(client, campaign_id, ad_group_name)
                        fresh_ad_group_ids.append(ad_group_id)
                        print('Updating ad group where ad_group_id=\'' + ad_group_id + '\' ...')
                        ad_ids = get_ad_ids(client, ad_group_id)

                        search_results = search_ads(client, ad_group_id, search_terms)

                        if not ad_ids:  # if ad group is empty
                            print('No ads found in ad group.')
                            update_make_model_keywords(ad_group_id, inv_type, year, make, model)
                            invalid_operations += update_make_model_ads(ad_group_id, ad_group_name, inv_type, year, make, model, min_price, max_discount, rebate_expiration, quantity, special_results)
                            updated_ad_groups.append({'id': ad_group_id, 'name': ad_group_name})
                        elif search_results:
                            for result in search_results:
                                if result[1] and not result[2]:  # if it has an ad_id and it didn't the search didn't find all the search terms
                                    remove_ad(client, ad_group_id, result[1])
                                    update_make_model_keywords(ad_group_id, inv_type, year, make, model)
                                    invalid_operations += update_make_model_ads(ad_group_id, ad_group_name, inv_type, year, make, model, min_price, max_discount, rebate_expiration, quantity, special_results, result[0])
                                    updated_ad_groups.append({'id': ad_group_id, 'name': ad_group_name})
                                elif not result[1] and not result[2]:  # if it has no ad_id and it didn't the search didn't find all the search terms
                                    update_make_model_keywords(ad_group_id, inv_type, year, make, model)
                                    invalid_operations += update_make_model_ads(ad_group_id, ad_group_name, inv_type, year, make, model, min_price, max_discount, rebate_expiration, quantity, special_results, result[0])
                                    updated_ad_groups.append({'id': ad_group_id, 'name': ad_group_name})
                        else:  # all search terms found
                            print('No updates necessary for ' + ad_group_name + ' ad group.\n\n')
                    else:  # if ad group name doesn't exist yet
                        print('Campaign does NOT contain ad group with name \'' + ad_group_name + '\'.')
                        ad_group_id = addAdGroup(client, campaign_id, ad_group_name)
                        update_make_model_keywords(ad_group_id, inv_type, year, make, model)
                        invalid_operations += update_make_model_ads(ad_group_id, ad_group_name, inv_type, year, make, model, min_price, max_discount, rebate_expiration, quantity, special_results)
                        # update_price_extension(year, make, model)

                        fresh_ad_group_ids.append({'id': ad_group_id, 'name': ad_group_name})
                        added_ad_groups.append({'id': ad_group_id, 'name': ad_group_name})

        # Remove ads from ad groups for vehicles that aren't in stock anymore
        print('Checking for outdated ads in campaign  with id \'' + campaign_name + '\' ...')
        for old_ad_group_id in old_ad_group_ids:
            if old_ad_group_id not in fresh_ad_group_ids:
                remove_ad_group(client, old_ad_group_id)
                deleted_ad_groups.append({'id': old_ad_group_id, 'name': 'unknown'})
                # instead pause ad group and remove all ads
        print('Finished checking for outdated ads in ' + campaign_name + ' campaign.\n\n')

        # Remove Ad Groups that have no ads or no keywords
        current_ad_groups = get_ad_groups(client, campaign_id)
        for ad_group_id in current_ad_groups.values():
            ads = get_ads(client, ad_group_id)
            keywords = get_keywords(client, ad_group_id)
            if ads == {} or keywords == []:
                print('Ad group either has no ads or no keywords.')
                remove_ad_group(client, ad_group_id)
                deleted_ad_groups.append({'id': ad_group_id, 'name': ad_group_name})

    # Print summary
    print('{} ad groups added.'.format(len(added_ad_groups)))
    for ad_group in added_ad_groups:
        print('\t' + ad_group['name'])
    print('{} ad groups removed.'.format(len(deleted_ad_groups)))
    for ad_group in deleted_ad_groups:
        print('\t' + ad_group['name'])
    print('{} ad groups updated.'.format(len(updated_ad_groups)))
    for ad_group in updated_ad_groups:
        print('\t' + ad_group['name'])
    print('{} invalid operations.'.format(len(invalid_operations)))
    for invalid_op in invalid_operations:
        pprint(invalid_op)


    # Close connection to database
    conn.commit()
    conn.close()


def simplify_model_name(model):
    simple_model_names = ['Silverado', 'Transit', 'F-150', 'F-250', 'F-350', 'Fusion']
    for name in simple_model_names:
        if name in model:
            return name
    return model



def main():
    update_sales_campaigns()


    # finance_operations = build_price_extension_operations('50519356218', 'New', 'Ford', 'Focus')
    # add_price_extension(client, finance_operations)
    #
    # ad_group_id = '50519356218'
    # get_price_extensions(client, ad_group_id)


if __name__ == '__main__':
    main()
