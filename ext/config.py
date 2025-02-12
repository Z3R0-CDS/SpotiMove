import os.path
import json

class ConfigHandle():
    __version__ = "0.1"

    def __init__(self, name="config.json", ui=None, logger = None):

        self.load = json.load
        self.fileName = name
        from zero_industries_devpackage.logger import Logger
        if logger!=None:
            self.logger=logger
        else:
            if ui!=None:
                self.logger = Logger("Config-Handle", ui=ui)
            else:
                self.logger = Logger("Config-Handle")


    def validateConfig(self):
        """
        Checks if config-file is in the local path

        :return: Bool
        """
        if not os.path.exists(f"{self.fileName}"):
            self.logger.warn(f"Config-file [{self.fileName}] is not on your drive!")
            return False
        return True

    def get_config(self):
        """
        Gets entire config for own filters.

        :return: None or json dict of config file
        """
        if self.validateConfig():
            try:
                with open(f"{self.fileName}", "r") as config_file:
                    return self.load(config_file)

            except Exception as x:
                self.logger.warn(f"get_config: {x}")
                return None
        else:
            return None

    def write_config(self, config):
        try:
            with open(f"{self.fileName}", "w") as config_file:
                json.dump(config, config_file, indent=2, ensure_ascii=False)
        except Exception as x:
            self.logger.warn(f"set_config: {x}")

    def get_item(self, item):
        """
        Gets specific json element from obj.
        item is case-sensitive!

        :param item: str name of json item
        :return: None or value of the item
        """
        if self.validateConfig():
            try:
                cfg = self.get_config()
                if cfg!=None:
                    return cfg[f"{item}"]
                else:
                    return None
            except Exception as x:
                self.logger.warn(f"get_item: {x}")
                return None
        else:
            return None

    def set_item(self, item, newValue):
        """
        Sets specific json element from obj.
        item is case-sensitive!

        :param item: str name of json item
                newValue: new value for item
        """
        if self.validateConfig():
            try:
                cfg = self.get_config()
                if cfg!=None:
                    cfg[f"{item}"]=newValue
                    self.write_config(cfg)
                else:
                    self.logger.warn(f"set_item: Got no valid config from load!")

            except Exception as x:
                self.logger.warn(f"set_item: {x}")