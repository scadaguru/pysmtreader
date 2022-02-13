import datetime
import os
import traceback
import yaml


class CommonHelper:
    log_level_debug = 1
    log_level_info = 2
    log_level_warning = 3
    log_level_error = 4
    log_level_critical = 5

    def __init__(self, config_folder):
        self.config_folder = config_folder
        self.config = yaml.safe_load(open(self.config_folder + 'config.yaml'))

        self.log_level = 2
        if self.config["logs"]["level"] == "debug":
            self.log_level = 1
        elif self.config["logs"]["level"] == "info":
            self.log_level = 2
        elif self.config["logs"]["level"] == "warning":
            self.log_level = 3
        elif self.config["logs"]["level"] == "error":
            self.log_level = 4
        elif self.config["logs"]["level"] == "critical":
            self.log_level = 5

        self.log_folder = self.config_folder + "logs/"
        self.log_file_name = self.log_folder + \
            self.config["logs"]["log_file_name"]

        if not os.path.exists(self.log_folder):
            os.makedirs(self.config_folder + "logs")
            self.log_info(
                "CommonHelper:__init__(): Creating log folder: " + self.log_folder)

    def get_seconds_till_next_minute(self):
        cur_time = datetime.datetime.now()
        next_minute = cur_time + \
            datetime.timedelta(seconds=59 - cur_time.second,
                               microseconds=999999 - cur_time.microsecond)
        diff = next_minute - cur_time
        diff_ms = (diff.seconds * 1000000 + diff.microseconds) / 1000000.0
        return diff_ms

    def log_debug(self, str_print):
        self._log(self.log_level_debug, str_print)

    def log_info(self, str_print):
        self._log(self.log_level_info, str_print)

    def log_warning(self, str_print):
        self._log(self.log_level_warning, str_print)

    def log_error(self, str_print):
        self._log(self.log_level_error, str_print)

    def log_critical(self, str_print):
        self._log(self.log_level_critical, str_print)

    def log_data(self, str_print):
        self._log(self.log_level_critical, str_print)

    def _log(self, log_level, str_print):
        if log_level >= self.log_level:
            try:
                log_file_name = self.log_file_name + "-" + \
                    datetime.datetime.now().strftime('%Y-%m-%d') + ".log"
                log_str = datetime.datetime.now().strftime('%H:%M:%S.%f')[
                    :-3] + self._get_log_level_to_string(log_level) + str_print
                print(log_str)
                with open(log_file_name, "a") as log_file:
                    log_file.write(log_str + "\n")
            except Exception as e:
                print(datetime.datetime.now().strftime('%H:%M:%S.%f')[
                      :-3] + " : CommonHelper:log():Exception: " + str(e))

    def _get_log_level_to_string(self, log_level):
        log_level_str = ": "
        if log_level == self.log_level_debug:
            log_level_str = ":debug: "
        elif log_level == self.log_level_info:
            log_level_str = ":info: "
        elif log_level == self.log_level_warning:
            log_level_str = ":warn: "
        elif log_level == self.log_level_error:
            log_level_str = ":error: "
        elif log_level == self.log_level_critical:
            log_level_str = ":critical: "
        return log_level_str
