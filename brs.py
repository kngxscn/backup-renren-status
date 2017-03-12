#!/usr/bin/env python3
# encoding=utf-8
# Author: renzongxian
# Date: 2016/01/26
# Usage: 人人状态（及评论）备份,结果保存在当前目录下的renren_status文件中

import datetime
import getpass
import re
import json
import codecs
import requests

headers = {'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36'}

def login(username, password):
    session = requests.session()

    # 构造时间戳
    date = datetime.datetime.now()
    timestamp = str(date.year) + str(date.month-1) + str((date.weekday()+1)%7) + str(date.hour) + str(date.second) + (str(int(date.microsecond/1000)) if int(date.microsecond/1000) >0 else '0')

    url = 'http://www.renren.com/ajaxLogin/login?1=1&uniqueTimestamp=' + timestamp
    data = {
            'email': username,
            'password': password
            }
    resp = session.post(url, headers=headers, data=data)
    renren_id = re.match(r'.*id=(\d{9});.*', resp.headers['Set-Cookie'])
    if renren_id:
        print(renren_id.groups()[0] + '登录成功')
        return session, renren_id.groups()[0]
    else:
        print('账号或密码错误！')
        exit(-1)


def parse_html(session, renren_id):
    # 提取所有状态及其评论
    curpage = 0
    status_list = []
    while(1):
        status_url = 'http://status.renren.com/GetSomeomeDoingList.do?'+ 'userId=' + renren_id + '&curpage=' + str(curpage)
        status_json_str = session.get(status_url, headers=headers).content.decode('utf-8')
        # 从返回的json字符串中提取状态信息
        status_json_obj = json.loads(status_json_str)
        doingArray = status_json_obj['doingArray']
        if len(doingArray) > 0:
            print(status_url)
            curpage += 1
        else:
            break
        for item in doingArray:
            status_content = item['dtime'] + '  ' + item['content']
            # 若该状态为转发的状态，加上原状态
            if 'rootContent' in item.keys():
                status_content += '\n----> ' + item['rootDoingUserName'] + ': ' + item['rootContent']
            # 若该状态有评论，加上评论
            if item['comment_count'] > 0:
                comment_url = 'http://comment.renren.com/comment/xoa2?type=status&entryId=' + str(int(item['id'])) + '&entryOwnerId=' + str(item['userId'])
                comments_json_str = session.get(comment_url, headers=headers).content.decode('utf-8')
                # 从返回的json字符串提取评论信息
                comments_json_obj = json.loads(comments_json_str)
                commentsArray = comments_json_obj['comments']
                comments_content = ''
                for comment_item in commentsArray:
                    comments_content += '\n    ' +  comment_item['authorName'] + '  ' + comment_item['time'] + '\n    ' + comment_item['content']
                status_content += comments_content
            status_list.append(status_content)

    return status_list


if __name__ == '__main__':
    username = input('username or email:')
    password = getpass.getpass('password(输入时不显示):')
    session, renren_id = login(username, password)
    status_list = parse_html(session, renren_id)
    with codecs.open('renren_status', 'wb', encoding='utf-8') as fp:
        fp.write(u'{status}'.format(status='\n\n'.join(status_list)))
