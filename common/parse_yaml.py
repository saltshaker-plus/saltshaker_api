# -*- coding:utf-8 -*-


class ParseYaml(object):
    @staticmethod
    def file_managed(**kwargs):
        yaml = '''{destination}:
  file.managed:
    - source: {source}
    - user: {user}
    - group: {group}
    - mode: {mode}
    - attrs: {attrs}
    - template: {template}

'''.format(**kwargs)
        return yaml
