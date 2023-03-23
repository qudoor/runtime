#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
"""
配置分类：
1. Django使用的配置文件，写到settings中
2. 程序需要, 用户不需要更改的写到settings中
3. 程序需要, 用户需要更改的写到本config中
"""
import errno
import json
import os.path

import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config(dict):

    def __init__(self, *args):
        super().__init__(*args)

    def get_from_config(self, item):
        try:
            value = super().__getitem__(item)
        except KeyError:
            value = None
        return value

    def get_from_env(self, item):
        value = os.environ.get(item, None)
        if value is not None:
            value = self.convert_type(value)
        return value

    def convert_type(self, v):
        tp = type(v)
        # 对bool特殊处理
        if tp is bool and isinstance(v, str):
            if v.lower() in ("true", "1"):
                return True
            else:
                return False
        if tp in [list, dict] and isinstance(v, str):
            try:
                v = json.loads(v)
                return v
            except json.JSONDecodeError:
                return v

        try:
            if tp in [list, dict]:
                v = json.loads(v)
            else:
                v = tp(v)
        except Exception:
            pass
        return

    def __getitem__(self, item):
        return self.get(item)

    def __getattr__(self, item):
        return self.get(item)

    def get(self, item):
        value = self.get_from_env(item)
        if value is None:
            # 再从配置文件中获取
            value = self.get_from_config(item)
        return value


class ConfigManager:
    config_class = Config

    def __init__(self):
        self.CONFIG_PATH = os.path.join(BASE_DIR, "config")
        self.config = self.config_class()

    def from_mapping(self, *mapping, **kwargs):
        """Updates the config like :meth:`update` ignoring items with non-upper
        keys.

        .. versionadded:: 0.11
        """
        mappings = []
        if len(mapping) == 1:
            if hasattr(mapping[0], 'items'):
                mappings.append(mapping[0].items())
            else:
                mappings.append(mapping[0])
        elif len(mapping) > 1:
            raise TypeError(
                'expected at most 1 positional argument, got %d' % len(mapping)
            )
        mappings.append(kwargs.items())
        for mapping in mappings:
            for (key, value) in mapping:
                if key.isupper():
                    self.config[key] = value
        return True

    def from_yaml(self, filename, silent=False):
        if self.CONFIG_PATH:
            filename = os.path.join(self.CONFIG_PATH, filename)
        try:
            with open(filename, 'rt', encoding='utf8') as f:
                obj = yaml.safe_load(f)
        except IOError as e:
            if silent and e.errno in (errno.ENOENT, errno.EISDIR):
                return False
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
        if obj:
            return self.from_mapping(obj)
        return True

    def load_from_yml(self):

        for i in ['config.yml', 'config.yaml']:
            if not os.path.isfile(os.path.join(self.CONFIG_PATH, i)):
                continue
            loaded = self.from_yaml(i)
            if loaded:
                return True
        return False

    @classmethod
    def load_user_config(cls):
        manager = cls()
        if manager.load_from_yml():
            config = manager.config
        else:
            msg = """

            Error: No config file found.

            You can run `cp config_example.yml config.yml`, and edit it.
            """
            raise ImportError(msg)

        # 对config进行兼容处理
        return config
