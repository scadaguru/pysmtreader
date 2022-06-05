import requests
import json
import time
import datetime
import traceback


class SMTReader:

    def __init__(self, commonHelper):
        self.__commonHelper = commonHelper

        self.__base_url = self.__commonHelper.config["smartmetertexas"]["base_url"]
        self.__username = self.__commonHelper.config["smartmetertexas"]["username"]
        self.__password = self.__commonHelper.config["smartmetertexas"]["password"]
        self.__esiid = self.__commonHelper.config["smartmetertexas"]["esiid"]
        self.__meter_number = self.__commonHelper.config["smartmetertexas"]["meter_number"]
        self.__wait_interval = self.__commonHelper.config["smartmetertexas"][
            "wait_interval_before_ondemand_read_minutes"]

    def read_meter(self):
        status_code_read = -1
        meter_reading = ""
        odrusage = ""

        self.__commonHelper.log_debug("About to read SMT meter")
        status_code_auth, auth_token = self.__get_auth_token()
        if status_code_auth == 0:
            status_code_ondemand = self.__request_ondemand_read(auth_token)

            if status_code_ondemand == "0":
                self.__commonHelper.log_debug(
                    "Starting timer for {} minutes".format(str(self.__wait_interval)))
                time.sleep(self.__wait_interval * 60)
                status_code_read, meter_reading, odrusage = self.__process_read_request(
                    auth_token)

                # if an error occured when getting the reading, wait another 5 minutes and then try to get the reading
                while status_code_read == 1:
                    self.__commonHelper.log_error(
                        "Still pending, starting another timer for {} minutes".format(str(self.__wait_interval)))
                    time.sleep(self.__wait_interval * 60)
                    status_code_read, meter_reading, odrusage = self.__process_read_request(
                        auth_token)
            elif status_code_ondemand == "5031":  # 5031 represents too many requests in an hour
                self.__commonHelper.log_error(
                    "Looks like too many requests have been sent, can't get the reading this hour")
            else:  # some other error occured calling the api
                self.__commonHelper.log_error(
                    "There was a problem calling the rest api")
        return status_code_read, meter_reading, odrusage

    # Will return 0 if a request was successfully
    # Will return -1 if there was an error making a request to the server
    def __get_auth_token(self):
        self.__commonHelper.log_debug('Getting auth token')
        status_code = -1
        auth_token = ""

        session = requests.Session()
        payload = {'username': self.__username,
                   'password': self.__password, 'rememberMe': True}
        response = session.post(self.__base_url + '/user/authenticate',
                                data=payload, verify=False)
        self.__commonHelper.log_debug(
            "Authorization request response: {}".format(str(response.text)))
        if response.ok:
            json_data = json.loads(response.text)
            auth_token = json_data['token']
            status_code = 0
            self.__commonHelper.log_info("Authorization successful")
        else:
            self.__commonHelper.log_error(
                "Authorization request failed, response: {}".format(str(response.text)))
        return status_code, auth_token

    # Will return 0 if a request was successfully sent and currently pending
    # Will return 5031 if the request is not allowed due to the fact it is too soon
    # Will return -1 if there was an error making a request to the server
    def __request_ondemand_read(self, auth_token):
        self.__commonHelper.log_debug('Requesting ondemand reading')
        status_code = -1

        header = {'Authorization': 'Bearer ' + auth_token}
        payload = {'ESIID': self.__esiid, 'MeterNumber': self.__meter_number}

        session = requests.Session()
        response = session.post(self.__base_url + '/ondemandread', data=payload,
                                headers=header, verify=False)
        self.__commonHelper.log_debug(
            "Ondemand request response: {}".format(str(response.text)))
        if response.ok:
            json_data = json.loads(response.text)
            status_code = json_data['data']['statusCode']
            self.__commonHelper.log_info("Ondemand request sent successfully")
        else:
            self.__commonHelper.log_error(
                "Ondemand request send failed, response: {}".format(str(response.text)))
        return status_code

    # Will return 0 if a request was successfully sent and updated on home assistant
    # Will return 1 if the request is still not ready, will try again in 5 minutes
    # Will return -1 if there was an error making a request to the server
    def __process_read_request(self, auth_token):
        self.__commonHelper.log_debug("Starting read of the processed data")
        status_code = -1
        meter_reading = ""
        odrusage = ""

        header = {'Authorization': 'Bearer ' + auth_token}
        payload = {'ESIID': self.__esiid}

        session = requests.Session()
        response = session.post(self.__base_url + '/usage/latestodrread', data=payload,
                                headers=header, verify=False)
        self.__commonHelper.log_debug(
            "Read request response: {}".format(str(response.text)))
        if response.ok:
            json_data = json.loads(response.text)
            status_string = json_data['data']['odrstatus']

            if status_string == 'COMPLETED':
                self.__commonHelper.log_info("Read request successful")
                meter_reading = json_data['data']['odrread']
                odrusage = json_data['data']['odrusage']
                status_code = 0
            elif status_string == 'PENDING':
                self.__commonHelper.log_info("Read request is still pending")
                status_code = 1
        else:
            self.__commonHelper.log_error(
                "Read request failed: {}".format(str(response.text)))
            status_code = 1
        return status_code, meter_reading, odrusage
