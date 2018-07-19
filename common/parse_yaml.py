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
    - template: {template}

'''.format(**kwargs)
        return yaml

    @staticmethod
    def cmd_run(name, cmd, env, unless, require):
        yaml = '''{name}:
  cmd.run:
    - name: {cmd}
'''.format(name=name, cmd=cmd)
        if env:
            yaml += "    - env: {env}\n".format(env=env)
        if unless:
            yaml += "    - unless: {unless}\n".format(unless=unless)
        if require:
            yaml += "    - require_in:\n      - file: {require}\n".format(require=require)
        return yaml

    @staticmethod
    def pkg_installed(name, pkgs):
        yaml = '''{name}:
  pkg.installed:
    - pkgs:
'''.format(name=name)
        for pkg in pkgs.split("\n"):
            yaml += "      - {pkg}\n".format(pkg=pkg)
        return yaml

    @staticmethod
    def file_directory(**kwargs):
        yaml = '''{destination}:
  file.directory:
    - user: {user}
    - group: {group}
    - mode: {mode}
    - makedirs: {makedirs}

'''.format(**kwargs)
        return yaml