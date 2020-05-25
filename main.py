import time
import datetime
import json
import traceback
from smt_reader import SMTReader
from helper_common import CommonHelper
from helper_ha import CustomHAHelper


class MeterReadHelper:

    def __init__(self, host_mapped_folder):
        self.__commonHelper = CommonHelper(host_mapped_folder)
        self.__customHAHelper = CustomHAHelper(host_mapped_folder)

        self.__log_info_line_at = self.__commonHelper.config["health_check"]["log_info_line_at"]
        self.__smt_poll_interval = int(
            self.__commonHelper.config["smartmetertexas"]["poll_interval_minutes"])
        self.__smt_force_first_read = self.__commonHelper.config[
            "smartmetertexas"]["force_first_read"]
        self.__smtreader = SMTReader(self.__commonHelper)
        self.__commonHelper.log_info("SMTReader meter needs to be polled every {} minutes with force first is {}".format(
            self.__smt_poll_interval, self.__smt_force_first_read))
        self.__ha_entity = self.__commonHelper.config["home_assistant"]["ha_entity"]

    def validate_config(self):
        config_status = 0
        value = self.__commonHelper.config["smartmetertexas"]["username"]
        if value == "_REPLACE_" or value == "":
            config_status = 1
            self.__commonHelper.log_error(
                "Config error: please make sure smartmetertexas username {} is valid".format(value))
        value = self.__commonHelper.config["smartmetertexas"]["password"]
        if value == "_REPLACE_" or value == "":
            config_status = 1
            self.__commonHelper.log_error(
                "Config error: please make sure smartmetertexas password {} is valid".format(value))
        value = self.__commonHelper.config["smartmetertexas"]["esiid"]
        if value == "_REPLACE_" or value == "":
            config_status = 1
            self.__commonHelper.log_error(
                "Config error: please make sure smartmetertexas esiid {} is valid".format(value))
        value = self.__commonHelper.config["smartmetertexas"]["meter_number"]
        if value == "_REPLACE_" or value == "":
            config_status = 1
            self.__commonHelper.log_error(
                "Config error: please make sure smartmetertexas meter_number {} is valid".format(value))
        value = self.__commonHelper.config["home_assistant"]["base_url"]
        if value == "_REPLACE_" or value == "":
            config_status = 1
            self.__commonHelper.log_error(
                "Config error: please make sure home_assistant base_url {} is valid".format(value))
        value = self.__commonHelper.config["home_assistant"]["access_token"]
        if value == "_REPLACE_" or value == "":
            config_status = 1
            self.__commonHelper.log_error(
                "Config error: please make sure home_assistant access_token {} is valid".format(value))
        return config_status

    def start(self):
        if self.validate_config() == 0:
            if self.__smt_force_first_read:
                self.__read_smt_meter()

            self.__commonHelper.log_info(
                "Going to sleep until exact minute starts")
            time.sleep(self.__commonHelper.get_seconds_till_next_minute())

            self.__commonHelper.log_info(
                "Now doing regular polling from config file interval")
            while True:
                cur_time = datetime.datetime.now()
                minutes_since_day_start = cur_time.hour * 60 + cur_time.minute

                if self.__log_info_line_at != 0 and minutes_since_day_start % self.__log_info_line_at == 0:
                    self.__commonHelper.log_info(
                        "Health check info line, still active and working!")

                if self.__smt_poll_interval != 0 and minutes_since_day_start % self.__smt_poll_interval == 0:
                    self.__read_smt_meter()

                time.sleep(self.__commonHelper.get_seconds_till_next_minute())

    def __read_smt_meter(self):
        try:
            status_code_read, meter_reading, odrusage = self.__smtreader.read_meter()
            if status_code_read == 0:
                self.__update_hass(meter_reading, odrusage)
            self.__commonHelper.log_info("SMT reading: " + meter_reading)
        except Exception as e:
            error_msg = "__read_smt_meter(): Exception: {}\n Call Stack: {}".format(
                str(e), traceback.format_exc())
            self.__commonHelper.log_critical(error_msg)

    def __update_hass(self, meter_reading, odrusage):
        self.__commonHelper.log_debug("Updating homeAssistant")
        response = self.__customHAHelper.ha_get_sensor(self.__ha_entity)
        if response.text.find("attributes") != -1 and response.text.find("current_state") != -1:
            prev_reading = response.json()['attributes']['current_state']
            self.__commonHelper.log_debug(
                "Found previous reading on homeAssistant: {}".format(str(prev_reading)))
        else:
            prev_reading = meter_reading

        attributes = dict()
        attributes['unit_of_measurement'] = "KW"
        attributes['prev_state'] = prev_reading
        attributes['current_state'] = meter_reading
        attributes['odrusage'] = odrusage
        attributes['last_timestamp'] = str(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
        try:
            attributes['difference'] = str(
                round(float(meter_reading) - float(prev_reading), 3))
        except Exception as e:
            error_msg = "update_hass(): Exception: {}\n Call Stack: {}".format(
                str(e), traceback.format_exc())
            self.__commonHelper.log_critical(error_msg)

        payload = {"state": meter_reading, "attributes": attributes}
        self.__commonHelper.log_debug(
            "Updating homeAssistant: payload: {}".format(str(payload)))
        response = self.__customHAHelper.ha_update_sensor(
            self.__ha_entity, payload)
        self.__commonHelper.log_debug(str(response.text))


# This is mapped volume from docker compose file, under this folder everything will be persisted on host
host_mapped_folder = "/config/"
#host_mapped_folder = "./"
meter_read_helper = MeterReadHelper(host_mapped_folder)
meter_read_helper.start()
