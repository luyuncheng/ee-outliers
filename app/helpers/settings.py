import configparser
import argparse
import re

from helpers.singleton import singleton

parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(help="Run mode", dest="run_mode")
interactive_parser = subparsers.add_parser('interactive')
daemon_parser = subparsers.add_parser('daemon')
tests_parser = subparsers.add_parser('tests')

# Interactive mode - options
interactive_parser.add_argument("--config", action='append', help="Configuration file location", required=True)

# Daemon mode - options
daemon_parser.add_argument("--config", action='append', help="Configuration file location", required=True)

# Tests mode - options
tests_parser.add_argument("--config", action='append', help="Configuration file location", required=True)


@singleton
class Settings:

    def __init__(self):
        self.args = None
        self.config = None

        self.loaded_config_paths = None
        self.failed_config_paths = None

        self.whitelist_literals_config = None
        self.whitelist_regexps_config = None
        self.failing_regular_expressions = set()

        self.args = parser.parse_args()
        self.process_configuration_files()

    def process_configuration_files(self):
        """
        Parse configuration and save some value
        """
        config_paths = self.args.config

        # Read configuration files
        config = configparser.ConfigParser(interpolation=None)
        config.optionxform = str  # preserve case sensitivity in config keys, important for derived field names

        self.loaded_config_paths = config.read(config_paths)
        self.failed_config_paths = set(config_paths) - set(self.loaded_config_paths)

        self.config = config

        # Literal whitelist
        self.whitelist_literals_config = self._extract_whitelist_literals_from_settings_section("whitelist_literals")
        # Regex whitelist
        self.whitelist_regexps_config, self.failing_regular_expressions = \
            self._extract_whitelist_regex_from_settings_section("whitelist_regexps")

    def _extract_whitelist_literals_from_settings_section(self, settings_section):
        list_whitelist_literals = list()
        fetch_whitelist_literals_elements = list(dict(self.config.items(settings_section)).values())

        for each_whitelist_configuration_file_value in fetch_whitelist_literals_elements:
            list_whitelist_literals.append(self.extract_whitelist_literal_from_value(str(
                each_whitelist_configuration_file_value)))
        return list_whitelist_literals

    def extract_whitelist_literal_from_value(self, value):
        list_whitelist_element = set()
        for one_whitelist_config_file_value in value.split(','):
            list_whitelist_element.add(one_whitelist_config_file_value.strip())
        return list_whitelist_element

    def _extract_whitelist_regex_from_settings_section(self, settings_section):
        whitelist_regexps_config_items = list(dict(self.config.items(settings_section)).values())
        list_whitelist_regexps = list()
        failing_regular_expressions = set()

        # Verify that all regular expressions in the whitelist are valid.
        # If this is not the case, log an error to the user, as these will be ignored.
        for each_whitelist_configuration_file_value in whitelist_regexps_config_items:
            new_compile_regex_whitelist_value, value_failing_regular_expressions = \
                self.extract_whitelist_regex_from_value(each_whitelist_configuration_file_value)
            list_whitelist_regexps.append(new_compile_regex_whitelist_value)
            failing_regular_expressions.union(value_failing_regular_expressions)

        return list_whitelist_regexps, failing_regular_expressions

    def extract_whitelist_regex_from_value(self, value):
        list_compile_regex_whitelist_value = set()
        failing_regular_expressions = set()
        for whitelist_val_to_check in value.split(","):
            try:
                list_compile_regex_whitelist_value.add(re.compile(whitelist_val_to_check.strip(), re.IGNORECASE))
            except Exception:
                failing_regular_expressions.add(whitelist_val_to_check)

        return list_compile_regex_whitelist_value, failing_regular_expressions
