import os
from placekey.api import PlacekeyAPI

def main():
    api_key = os.environ['PLACEKEY_API_KEY']
    api = PlacekeyAPI(api_key=api_key, user_agent_comment='placekey-py-tests')
    place = {
        'location_name': 'Pinecrest Food Market',
        'street_address': '401 Pinecrest Lake Rd',
        'city': 'Pinecrest',
        'region': 'CA',
        'postal_code': '95364',
        'iso_country_code': 'US'
    }
    print(api.lookup_placekeys([place], verbose=True))


if __name__ == '__main__':
    main()
