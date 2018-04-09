#!/usr/bin/env python
import urllib.request
import urllib.parse
import json
import requests


class SaltAPI(object):
    __token_id = ''

    def __init__(self, url, user, passwd):
        self.__url = url
        self.__user = user
        self.__password = passwd
        self.__token_id = self.get_token_id()

    def get_token_id(self):
        # user login and get token id
        params = {'eauth': 'pam', 'username': self.__user, 'password': self.__password}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        url = str(self.__url) + '/login'
        req = urllib.request.Request(url, obj)
        try:
            opener = urllib.request.urlopen(req, timeout=60)
            content = json.loads(opener.read())
            token_id = content['return'][0]['token']
        except Exception as _:
            return ""
        return token_id

    def post_request(self, obj, prefix='/'):
        url = str(self.__url) + prefix
        headers = {'X-Auth-Token': self.__token_id}
        req = urllib.request.Request(url, obj, headers)
        try:
            opener = urllib.request.urlopen(req, timeout=180)
            content = json.loads(opener.read())
        except Exception as e:
            return str(e)
        return content

    def list_all_key(self):
        params = {'client': 'wheel', 'fun': 'key.list_all'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            minions = content['return'][0]['data']['return']
            return minions
        else:
            return {"status": False, "message": "salt api error : " + content}

    def delete_key(self, node_name):
        params = {'client': 'wheel', 'fun': 'key.delete', 'match': node_name}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0]['data']['success']
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def accept_key(self, node_name):
        params = {'client': 'wheel', 'fun': 'key.accept', 'match': node_name}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0]['data']['success']
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def reject_key(self, node_name):
        params = {'client': 'wheel', 'fun': 'key.reject', 'match': node_name}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0]['data']['success']
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def remote_noarg_execution(self, tgt, fun):
        # Execute commands without parameters
        params = {'client': 'local', 'tgt': tgt, 'fun': fun, 'expr_form': 'list'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0][tgt]
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def remote_noarg_execution_notgt(self, tgt, fun):
        # Execute commands without parameters
        params = {'client': 'local', 'tgt': tgt, 'fun': fun, 'expr_form': 'list'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0]
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def remote_execution(self, tgt, fun, arg):
        # Command execution with parameters
        params = {'client': 'local', 'tgt': tgt, 'fun': fun, 'arg': arg, 'expr_form': 'list'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0][tgt]
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def remote_execution_notgt(self, tgt, fun, arg):
        # Command execution with parameters
        params = {'client': 'local', 'tgt': tgt, 'fun': fun, 'arg': arg, 'expr_form': 'list'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0]
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def shell_remote_execution(self, tgt, arg):
        # Shell command execution with parameters
        params = {'client': 'local', 'tgt': tgt, 'fun': 'cmd.run', 'arg': arg, 'expr_form': 'list'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0]
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def grain(self, tgt, arg):
        # Grains.item
        params = {'client': 'local', 'tgt': tgt, 'fun': 'grains.item', 'arg': arg}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0]
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def grains(self, tgt):
        # Grains.items
        params = {'client': 'local', 'tgt': tgt, 'fun': 'grains.items'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            ret = content['return'][0]
            return ret
        else:
            return {"status": False, "message": "salt api error : " + content}

    def target_remote_execution(self, tgt, fun, arg):
        # Use targeting for remote execution
        params = {'client': 'local', 'tgt': tgt, 'fun': fun, 'arg': arg, 'expr_form': 'nodegroup'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            jid = content['return'][0]['jid']
            return jid
        else:
            return {"status": False, "message": "salt api error : " + content}

    def deploy(self, tgt, arg):
        # Module deployment
        params = {'client': 'local', 'tgt': tgt, 'fun': 'state.sls', 'arg': arg}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        return content

    def async_deploy(self, tgt, arg):
        # Asynchronously send a command to connected minions
        params = {'client': 'local_async', 'tgt': tgt, 'fun': 'state.sls', 'arg': arg}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            jid = content['return'][0]['jid']
            return jid
        else:
            return {"status": False, "message": "salt api error : " + content}

    def target_deploy(self, tgt, arg):
        # Based on the list forms deployment
        params = {'client': 'local', 'tgt': tgt, 'fun': 'state.sls', 'arg': arg, 'expr_form': 'list'}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            return content
        else:
            return {"status": False, "message": "salt api error : " + content}

    def jobs_list(self):
        # Get Cache Jobs Default 24h '''
        url = self.__url + '/jobs/'
        headers = {'X-Auth-Token': self.__token_id}
        req = urllib.request.Request(url, headers=headers)
        opener = urllib.request.urlopen(req)
        content = json.loads(opener.read())
        if isinstance(content, dict):
            jid = content['return'][0]
            return jid
        else:
            return {"status": False, "message": "salt api error : " + content}

    def jobs_info(self, arg):
        # Get Job detail info '''
        url = self.__url + '/jobs/' + arg
        headers = {'X-Auth-Token': self.__token_id}
        req = urllib.request.Request(url, headers=headers)
        opener = urllib.request.urlopen(req)
        content = json.loads(opener.read())
        if isinstance(content, dict):
            jid = content['return'][0]
            return jid
        else:
            return {"status": False, "message": "salt api error : " + content}

    def stats(self):
        # Expose statistics on the running CherryPy server
        url = self.__url + '/stats'
        headers = {'X-Auth-Token': self.__token_id}
        req = urllib.request.Request(url, headers=headers)
        opener = urllib.request.urlopen(req)
        content = json.loads(opener.read())
        if isinstance(content, dict):
            return content
        else:
            return {"status": False, "message": "salt api error : " + content}

    def runner_status(self, arg):
        # Return minion status
        params = {'client': 'runner', 'fun': 'manage.' + arg}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            jid = content['return'][0]
            return jid
        else:
            return {"status": False, "message": "salt api error : " + content}

    def runner(self, arg):
        # Return minion status
        params = {'client': 'runner', 'fun': arg}
        obj = urllib.parse.urlencode(params).encode('utf-8')
        content = self.post_request(obj)
        if isinstance(content, dict):
            jid = content['return'][0]
            return jid
        else:
            return {"status": False, "message": "salt api error : " + content}

    def events(self):
        # SSE get job info '''
        url = self.__url + '/events'
        headers = {'X-Auth-Token': self.__token_id}
        req = requests.get(url, stream=True, headers=headers)
        return req

