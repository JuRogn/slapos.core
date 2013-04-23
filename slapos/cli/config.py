# -*- coding: utf-8 -*-

import ConfigParser
import os

from cliff.command import Command


class ConfigError(Exception):
    pass


class ConfigCommand(Command):
    "Base class for commands that require a configuration file"

    log = None

    default_config_var = 'SLAPOS_CONFIGURATION'

    # use this is default_config_var does not exist
    default_config_path = '/etc/opt/slapos/slapos.cfg'

    def get_parser(self, prog_name):
        parser = super(ConfigCommand, self).get_parser(prog_name)
        parser.add_argument('--cfg', help='SlapOS configuration file')
        return parser

    def _get_config(self, cfg_path, required=False):
        """
        Returns a configuration object if file exists/readable/valid,
        None otherwise.
        Will raise an error instead of returning None if required is True.
        Even if required is False, may still raise an exception from the
        configparser if the configuration content is very broken.
        We don't catch that exception as it will clearly show what is
        wrong with the file.
        """

        if not os.path.exists(cfg_path):
            if required:
                raise ConfigError('Configuration file does not exist: %s' % cfg_path)
            else:
                return None

        config = ConfigParser.SafeConfigParser()
        if config.read(cfg_path) != [cfg_path]:
            # bad permission, etc.
            if required:
                raise ConfigError('Cannot parse configuration file: %s' % cfg_path)
            else:
                return None

        return config

    def fetch_config(self, args):
        if args.cfg:
            cfg_path = os.path.expanduser(args.cfg)
        else:
            cfg_path = os.environ.get(self.default_config_var, self.default_config_path)

        self.log.debug('Loading config: %s' % cfg_path)

        return self._get_config(cfg_path, required=True)


class ClientConfigCommand(ConfigCommand):
    # XXX does not fallback to SLAPOS_CONFIGURATION
    default_config_var = 'SLAPOS_CLIENT_CONFIGURATION'
    default_config_path = '~/.slapos/slapos.cfg'
