import requests
import json
import logging
import itertools
from ratelimit import limits, RateLimitException
from backoff import on_exception, fibo

console_log = logging.StreamHandler()
console_log.setFormatter(
    logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s')
)
log = logging.getLogger()
log.setLevel(logging.INFO)
log.handlers = [console_log]


class PlacekeyAPI:
    """
    PlacekeyAPI class

    This class provides functionality for looking up Placekeys using the Placekey
    API. Places to be looked a specified by a **place dictionary** whose keys and value types
    must be a subset of

    * latitude (float)
    * longitude (float)
    * location_name (string)
    * street_address (string)
    * city (string)
    * region (string)
    * postal_code (string)
    * iso_country_code (string)
    * query_id (string)

    See the `Placekey API documentation <https://docs.placekey.io/>`_ for more
    information on how to use the API.

    :param api_key: Placekey API key (string)
    :param logger: A logging object. Logs are sent to the console by default.

    """
    URL = 'https://api.placekey.io/v1/placekey'
    REQUEST_LIMIT = 1000
    REQUEST_WINDOW = 60

    BULK_URL = 'https://api.placekey.io/v1/placekeys'
    BULK_REQUEST_LIMIT = 100
    BULK_REQUEST_WINDOW = 60
    MAX_BATCH_SIZE = 100

    DEFAULT_MAX_RETRIES = 20

    QUERY_PARAMETERS = {
        'latitude',
        'longitude',
        'location_name',
        'street_address',
        'city',
        'region',
        'postal_code',
        'iso_country_code',
        'query_id'
    }

    def __init__(self, api_key=None, logger=log):
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': api_key
        }
        self.logger = logger

    @on_exception(fibo, RateLimitException, max_tries=DEFAULT_MAX_RETRIES)
    @limits(calls=REQUEST_LIMIT, period=REQUEST_WINDOW)
    def lookup_placekey(self,
                        strict_address_match=False,
                        strict_name_match=False,
                        **kwargs):
        """
        Lookup the Placekey for a single place.

        :param strict_address_match: Boolean for whether or not to strict match
            on address fields. Defaults to `False`.
        :param strict_name_match: Boolean for whether or not to strict match
            on `location_name`. Defaults to `False`.
        :kwargs: Place fields can be passed to this method as keyword arguments. The allowed
            keyword arguments are ['latitude', 'longitude', 'location_name','street_address',
            'city', 'region', 'postal_code', 'iso_country_code', 'query_id']

        :return: A Placekey API response (dict)

        """
        if not self._validate_query(kwargs):
            raise ValueError(
                "Query contains keys other than: {}".format(self.QUERY_PARAMETERS))

        payload = {"query": kwargs}
        if strict_address_match:
            payload['options'] = {"strict_address_match": True}
        if strict_name_match:
            payload['options'] = {"strict_name_match": True}

        r = requests.post(
            self.URL, headers=self.headers, data=json.dumps(payload).encode("utf-8")
        )
        return json.loads(r.text)

    def lookup_placekeys(self,
                         places,
                         strict_address_match=False,
                         strict_name_match=False,
                         max_retries=DEFAULT_MAX_RETRIES,
                         batch_size=MAX_BATCH_SIZE,
                         verbose=False):
        """
        Lookup Placekeys for an iterable of places specified by place dictionaries.
        This method checks that the place dictionaries are valid before querying
        the API, and it will return partial results if it encounters a fatal error.
        This method follows the rate limits of the Placekey API. This function is a
        wrapper for `lookup_batch`, and that function may be used if different error
        handling or logic around batch processing is desired.

        :param places: An iterable of of place dictionaries.
        :param strict_address_match: Boolean for whether or not to strict match
            on address fields. Defaults to `False`.
        :param strict_name_match: Boolean for whether or not to strict match
            on `location_name`. Defaults to `False`.
        :param max_retries: Integer value for the maximum number of retries to make when encountering
            an error. Defaults to 20
        :param batch_size: Integer for the number of places to lookup in a single batch.
            Defaults to 100, and cannot exceeded 100.
        :param verbose: Boolean for whether or not to log additional information.
            Defaults to False

        :return: A list of Placekey API responses for each place (list(dict))

        """
        if batch_size > self.MAX_BATCH_SIZE:
            raise ValueError("Batch size cannot exceed {}.".format(self.MAX_BATCH_SIZE))

        if not all([self._validate_query(a) for a in places]):
            raise ValueError(
                "Some queries contain keys other than: {}".format(self.QUERY_PARAMETERS))

        results = []
        for i in range(0, len(places), batch_size):
            max_batch_idx = min(i + batch_size, len(places))

            # Catch too many retries, and return partial results
            try:
                res = self.lookup_batch(
                    places[i:max_batch_idx],
                    strict_address_match=strict_address_match,
                    strict_name_match=strict_name_match
                )
            except RateLimitException as e:
                logging.error(
                    'max_tries ({}) exceeded. Returning processed items.'.format(
                        max_retries))
                break

            # Catch case where all queries in batch having an error,
            # and generate rows for individual items.
            if isinstance(res, dict) and 'error' in res:
                if verbose:
                    self.logger.info('All queries in batch ({}, {}) had errors'.format(
                        i, max_batch_idx))

                res = [{'query_id': str(i), 'error': res['error']}
                       for i in range(i, max_batch_idx)]

            # Catch malformed input cases. TODO:Remove this
            elif 'message' in res:
                if verbose:
                    self.logger.error(res['message'])
                    self.logger.info('Returning completed queries')
                break
            else:
                # Remap the 'query_id' field to match address index
                for r in res:
                    if r['query_id'].isdigit():
                        r['query_id'] = str(int(r['query_id']) + i)

            results.append(res)

            if verbose and max_batch_idx % (10 * batch_size) == 0 and i > 0:
                logging.info('Processed {} items'.format(max_batch_idx))

        return list(itertools.chain.from_iterable(results))

    @on_exception(fibo, RateLimitException, max_tries=DEFAULT_MAX_RETRIES)
    @limits(calls=BULK_REQUEST_LIMIT, period=BULK_REQUEST_WINDOW)
    def lookup_batch(self, places,
                     strict_address_match=False,
                     strict_name_match=False):
        """
        Lookup Placekeys for a single batch of places specified by place dictionaries.
        The batch size can be at most 100 places. This method follows the rate limits
        of the Placekey API.

        :param places: An iterable of of place dictionaries.
        :param strict_address_match: Boolean for whether or not to strict match
            on address fields. Defaults to `False`.
        :param strict_name_match: Boolean for whether or not to strict match
            on `location_name`. Defaults to `False`.

        :return: A list of Placekey API responses for each place (list(dict))

        """
        if len(places) > self.MAX_BATCH_SIZE:
            raise ValueError(
                '{} places submitted. The number of places in a batch can be at most {}'
                .format(len(places), self.MAX_BATCH_SIZE)
            )

        batch_payload = {
            "queries": places
        }
        if strict_address_match:
            batch_payload['options'] = {"strict_address_match": True}
        if strict_name_match:
            batch_payload['options'] = {"strict_name_match": True}

        r = requests.post(
            self.BULK_URL, headers=self.headers, data=json.dumps(batch_payload).encode('utf-8')
        )
        return json.loads(r.text)

    def _validate_query(self, query_dict):
        return set(query_dict.keys()).issubset(self.QUERY_PARAMETERS)
