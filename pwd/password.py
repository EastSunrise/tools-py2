#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Description 密码生成器
@Module password

@Author Kingen
@Date 2019/10/10
@Version 1.0
"""
import getopt
import hashlib
import re
import sys
import time
from xml.etree import ElementTree

from yinxiang.client import YinXiangClient

COMPLEX_DICT = ['!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4',
                '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
                'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']',
                '^', '_', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
                't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~']

SIMPLE_DICT = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
               'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f',
               'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

NUMBER_DICT = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

NOTE_ACCOUNT_GUID = 'a9a63408-9876-4b2b-be91-e0a3df2561eb'

NOTE_ENML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>' \
                   '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'


def generate(domain, user=None, key=None, account=None, service=None, length=16, ascii_dict=None):
    """
    生成md5加密的密码
    :param domain: 域名，标志网站的域名，如126.com，seu.edu.cn
    :param user: 用户关键词
    :param key: 指定关键词
    :param account: 多账户时，账户关键词
    :param service: 多服务时，相关服务关键词，默认为空
    :param length: 所需密码长度
    :param ascii_dict: 密码字典
    :return: 密码
    """
    # 原始字符串
    if ascii_dict is None:
        ascii_dict = COMPLEX_DICT
    domain = domain.lower()
    parts = domain.split('.')
    top = ''
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] != '':
            top = parts[i]
            break
    src_str = ''
    src_str += top + '.' + domain[0:2]
    if not isBlank(user):
        src_str += '$' + user
    if not isBlank(key):
        src_str += '#' + key + '#'
    if not isBlank(account):
        src_str += '@' + account
    if not isBlank(service):
        src_str += '-' + service
    src_str += '%' + str(len(domain))

    # 多重md5加密
    times = (2 * length + 31) / 32
    md5 = hashlib.md5()
    str_md5 = ''
    for i in range(times):
        md5.update(src_str.encode(encoding='UTF-8'))
        src_str = md5.hexdigest()
        str_md5 += src_str

    # 最终的密码
    password = ''
    ascii_length = len(ascii_dict)
    for i in range(0, 2 * length, 2):
        index = int(str_md5[i:i + 2], 16)
        password += ascii_dict[index % ascii_length]
    return password


def update_evernote(note_store, domain, account='default', service='default'):
    """
    更新印象笔记数据
    :param note_store:
    :param service:
    :param account:
    :param domain: 域名
    :return:
    """
    if note_store is None:
        return
    note_account = note_store.getNote(NOTE_ACCOUNT_GUID, True, False, False, False)
    str_xml = note_account.content

    # parse to python object
    root = ElementTree.fromstring(str_xml)
    domain_ul = root.find('div/ul')
    account_ul = search_li(domain_ul, domain)
    service_ul = search_li(account_ul, account)
    time_ul = search_li(service_ul, service)
    if time_ul.find('li/div', None) is None:
        time_ul.insert(0, get_li(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
    note_account.content = NOTE_ENML_HEADER + ElementTree.tostring(root)
    print note_store.updateNote(note_account)


def search_li(ul_ele, value):
    """
    search the value under the ul element
    :param ul_ele:
    :param value:
    :return:
    """
    if value is None:
        value = 'default'
    sub_ul = None
    li_list = list(ul_ele)
    ele_index = 0
    for ele in li_list:
        if ele.tag == 'li':
            cur_value = ele.find('div').text
            if cur_value == value:
                sub_ul = li_list[ele_index + 1]
                break
            if cur_value > value:
                break
        ele_index += 1
    if sub_ul is None:
        ul_ele.insert(ele_index, get_li(value))
        sub_ul = ElementTree.XML('<ul></ul>')
        ul_ele.insert(ele_index + 1, sub_ul)
    return sub_ul


def get_li(value):
    """
    get li element
    """
    li_str = '<li><div>%s</div></li>' % value
    return ElementTree.XML(li_str)


def start():
    """
    启动程序
    :return:
    """
    print '©2019 Gen Kings'

    # login to account of evernote
    app_opts, app_args = getopt.getopt(sys.argv[1:], 'u:p:')
    app_dict = dict(app_opts)
    username = app_dict.get('-u')
    password = app_dict.get('-p')
    note_store = None
    try:
        note_store = YinXiangClient(username, password).get_note_store()
    except IndexError as e:
        print 'Won\'t be updated to evernote. Enter your account and password of evernote if you want.'

    while True:
        str_input = raw_input('Please enter the password:\n')
        str_time = time.strftime('%y%m%d%H%M%S', time.localtime())
        password = str_time[7:8] + str_time[9:10] + str_time[1:2] + str_time[3:4] + str_time[5:6]
        if str_input == password:
            break

    while True:
        str_input = raw_input('Please enter the domain and extra optional args(space to split and \'-\' to mark the arg, -1 to exit):\n')
        if str_input == '-1':
            break
        if not isBlank(str_input):
            args = re.split(r"\s+", str_input.strip())
            domain = args[0]
            try:
                opts, args = getopt.getopt(args[1:], 'u:k:a:s:')
                option_map = dict(opts)
                params = {
                    'user': option_map.get('-u'),
                    'key': option_map.get('-k'),
                    'account': option_map.get('-a'),
                    'service': option_map.get('-s')
                }
                print 'Generating passwords with the params: ' + ', '.join(option_map.keys())
                update_evernote(note_store, domain, params['account'], params['service'])
                print generate(domain, **(dict(params, length=12, ascii_dict=COMPLEX_DICT)))
                print generate(domain, **(dict(params, length=16, ascii_dict=SIMPLE_DICT)))
                print generate(domain, **(dict(params, length=6, ascii_dict=NUMBER_DICT)))
            except getopt.GetoptError as error:
                print error


def isBlank(string):
    return string is None or string.strip() == ''


if __name__ == '__main__':
    start()
