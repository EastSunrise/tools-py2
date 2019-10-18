#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Description 印象笔记客户端
@Module client

@Author Kingen
@Date 2019/9/20
@Version 1.0
"""
import re
import time

import requests
from bs4 import BeautifulSoup
from evernote.api.client import EvernoteClient


class LoginError(Exception):
    """登录异常"""
    pass


class EvernoteSession(object):
    def __init__(self, username, password):
        super(EvernoteSession, self).__init__()
        self.headers = {
            'Host': 'app.yinxiang.com',
            'Origin': 'https://app.yinxiang.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        }
        self.login_url = 'https://app.yinxiang.com/Login.action'
        self.token_url = 'https://app.yinxiang.com/api/DeveloperToken.action'
        self.store_url = 'https://app.yinxiang.com/shard/s1/notestore'
        self.session = requests.session()
        self.__username = username
        self.__password = password
        self.__login()

    def __login(self):
        """
        模拟登录，初始化session
        :return:
        """
        login_headers = dict(self.headers, Referer=self.login_url)
        login_html = self.session.get(self.login_url, headers=login_headers).content
        soup = BeautifulSoup(login_html, features='html.parser')

        script = soup.findAll('script')[3].string
        hpts = re.search(r'hpts".*= "(.*)";', script).group(1)
        hptsh = re.search(r'hptsh".*= "(.*)";', script).group(1)
        _sourcePage = soup.find(name='input', attrs={'name': '_sourcePage'}).get('value')
        __fp = soup.find(name='input', attrs={'name': '__fp'}).get('value')

        form_data = {
            'username': self.__username,
            'password': self.__password,
            'login': '登录',
            'analyticsLoginOrigin': 'login_action',
            'clipperFlow': 'false',
            'showSwitchService': 'true',
            'usernameImmutable': 'false',
            'hpts': hpts,
            'hptsh': hptsh,
            '_sourcePage': _sourcePage,
            '__fp': __fp
        }
        response = self.session.post(self.login_url, data=form_data, headers=login_headers)
        if response.url == u'https://app.yinxiang.com/Login.action':
            # 登录失败
            raise LoginError('Failed to login the evernote. Won\'t update the account.')

    def create_token(self):
        """
        新生成token
        :return:
        """
        token_headers = dict(self.headers, Referer='https://app.yinxiang.com/api/DeveloperToken.action')
        token_page = self.session.get(self.token_url, headers=token_headers).text
        soup = BeautifulSoup(token_page, features='html.parser')
        p = soup.findAll('p')[1].string
        is_expired = True if re.search(r'Your Developer Token has already been created', p) is None else False

        # data
        secret = soup.find(name='input', attrs={'name': 'secret'}).get('value')
        csrfBusterToken = soup.find(name='input', attrs={'name': 'csrfBusterToken'}).get('value')
        _sourcePage = soup.find(name='input', attrs={'name': '_sourcePage'}).get('value')
        __fp = soup.find(name='input', attrs={'name': '__fp'}).get('value')
        form_data = {
            'secret': secret,
            'csrfBusterToken': csrfBusterToken,
            '_sourcePage': _sourcePage,
            '__fp': __fp
        }

        # revoke the token
        if not is_expired:
            print 'Revoking the token.'
            note_store_url = self.store_url
            remove = 'Revoke your developer token'
            self.session.post(self.token_url, data=dict(form_data, noteStoreUrl=note_store_url, remove=remove), headers=token_headers)

        # create a new token
        print 'Creating a new token'
        create_token_page = self.session.post(self.token_url, data=dict(form_data, create='Create a developer token'), headers=token_headers)
        soup = BeautifulSoup(create_token_page.text, features='html.parser')
        token = soup.find(id='token').get('value')
        note_store_url = soup.find(id='noteStoreUrl').get('value')
        h3 = soup.find(name='h3', text='Expires:')
        expires_str = h3.next.next.next.strip()
        return token, note_store_url, time.strptime(expires_str, '%d %B %Y, %H:%M')


class YinXiangClient(object):
    def __init__(self, username, password):
        super(YinXiangClient, self).__init__()
        self.evernote_session = EvernoteSession(username, password)
        self.token = self.note_store_url = self.expires = None
        self.update_token()

    def update_token(self):
        if self.token is None or self.expires < time.localtime():
            self.token, self.note_store_url, self.expires = self.evernote_session.create_token()

    def get_client(self):
        """
        获取client
        :return:
        """
        self.update_token()
        return EvernoteClient(token=self.token, sandbox=False, china=True)

    def get_note_store(self):
        return self.get_client().get_note_store()
