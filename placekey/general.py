import itertools
import json
import logging
from json import JSONDecodeError

import requests
from ratelimit import limits, RateLimitException
import backoff

def _post_request_function(headers, url, calls, period, max_tries):
        """
        Construct a rate limited function for making requests.

        :param url: request URL
        :param calls: number of calls that can be made in time period
        :param  period: length of rate limiting time period in seconds
        :param max_tries: the maximum number of retries before giving up
        """

        @backoff.on_exception(backoff.fibo, (RateLimitException, requests.exceptions.RequestException),
                              max_tries=max_tries)
        @limits(calls=calls, period=period)
        def make_request(request_data = None):
            try:
                payload = {
                    "url": url,
                    "headers": headers,
                }
                if request_data:
                    payload["data"] = json.dumps(request_data).encode('utf-8')
                response = requests.post(**payload)

                if response.status_code == 429:
                    raise RateLimitException("Rate limit exceeded", 0)
                elif response.status_code == 503:
                    raise requests.exceptions.RequestException("Service Unavailable")
                elif response.status_code == 504:
                    raise requests.exceptions.RequestException("Gateway Timeout")

                return response
            except requests.exceptions.RequestException as e:
                raise e

        return make_request

def _get_request_function(headers, url, calls, period, max_tries):
        """
        Construct a rate limited function for making requests.

        :param url: request URL
        :param calls: number of calls that can be made in time period
        :param  period: length of rate limiting time period in seconds
        :param max_tries: the maximum number of retries before giving up
        """

        @backoff.on_exception(backoff.fibo, (RateLimitException, requests.exceptions.RequestException),
                              max_tries=max_tries)
        @limits(calls=calls, period=period)
        def make_request(params = None):
            try:
                payload = {
                    "url": url,
                    "headers": headers,
                }
                if params:
                    payload["params"] = params
                response = requests.get(**payload)

                if response.status_code == 429:
                    raise RateLimitException("Rate limit exceeded", 0)
                elif response.status_code == 503:
                    raise requests.exceptions.RequestException("Service Unavailable")
                elif response.status_code == 504:
                    raise requests.exceptions.RequestException("Gateway Timeout")

                return response
            except requests.exceptions.RequestException as e:
                raise e

        return make_request