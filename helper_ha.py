import json
from requests import post, get
import yaml
import traceback


class CustomHAHelper:
    def __init__(self, config_folder):
        try:
            self.config = yaml.safe_load(open(config_folder + 'config.yaml'))
            self.base_url = self.config["home_assistant"]["base_url"]
            self.access_token = self.config["home_assistant"]["access_token"]
        except Exception as e:
            exception_info = "\nException: {}\n Call Stack: {}".format(
                str(e), str(traceback.format_exc()))
            print("CustomHAHelper:__init__():Exception: " + exception_info)

    def ha_get_entity_state(self, entity_name):
        state = None
        response = self.ha_get_sensor(entity_name)
        if response:
            state = response.json()['state']
        return state

    def ha_get_entity_attribute(self, entity_name, attribute_name):
        attribute_value = None
        response = self.ha_get_sensor(entity_name)
        if response:
            attribute_value = response.json()['attributes'][attribute_name]
        return attribute_value

    def ha_set_entity_state(self, entity_name, state_str=None, attributes=None, payload=None):
        if payload == None:
            payload = {"state": state_str}
            if attributes:
                payload['attributes'] = attributes
        return self.ha_update_sensor(entity_name, payload)

    def ha_get_sensor(self, entity_name):
        get_url = "{}/api/states/{}".format(self.base_url, entity_name)
        headers = {
            'Authorization': "Bearer " + self.access_token
        }
        response = get(get_url, headers=headers)
        return response

    def ha_update_sensor(self, entity_name, payload):
        post_url = "{}/api/states/{}".format(self.base_url, entity_name)
        headers = {
            'Authorization': "Bearer " + self.access_token
        }
        response = post(post_url, data=json.dumps(payload), headers=headers)
        return response

    def ha_service_notify(self, message, whom):
        post_url = "{}/api/services/notify/{}".format(self.base_url, whom)
        headers = {
            'Authorization': "Bearer " + self.access_token
        }
        payload = {
            "message": message
        }
        response = post(post_url, data=json.dumps(payload), headers=headers)
        return response

    def ha_service_update_device_tracker(self, mac_address=None, status_str=None, payload=None):
        post_url = "{}/api/services/device_tracker/see".format(self.base_url)
        headers = {
            'Authorization': "Bearer " + self.access_token
        }
        if payload == None:
            payload = {
                "mac": mac_address,
                "location_name": status_str,
                "attributes": {"source_type": "script"}
            }
        response = post(post_url, data=json.dumps(payload), headers=headers)
        return response
