#!/usr/bin/env python3
# coding=utf-8
# module name: cofable
# dependencies:  cofnet  (https://github.com/limaofu/cofnet)  &  paramiko
# author: Cof-Lee
# start_date: 2024-01-17
# this module uses the GPL-3.0 open source protocol
# update: 2024-03-05

"""
解决问题：
★. 执行命令时进行判断回复                                 2024年1月23日 基本完成
★. 登录凭据的选择与多次尝试各同类凭据（当同类型凭据有多个时），只选择第一个能成功登录的cred     2024年1月23日 完成
★. ssh密码登录，ssh密钥登录                              2024年1月23日 完成
★. 所有输出整理到txt文件                                 2024年1月24日 完成
★. 所有输出根据模板设置，确认是否自动保存到txt文件以及文件名风格                           2024年3月4日 完成
★. 使用多线程，每台主机用一个线程去巡检，并发几个线程          2024年1月25日 完成
★. 巡检作业执行完成情况的统计，执行完成，连接超时，认证失败     2024年1月28日 基本完成
★. 程序运行后，所有类的对象都要分别加载到一个全局列表里
★. 巡检命令输出保存到数据库                               2024年1月27日 基本完成
★. 定时/周期触发巡检模板作业
★. 本次作业命令输出与最近一次（上一次）输出做对比
★. 巡检命令输出做基础信息提取与判断并触发告警，告警如何通知人类用户？
★. Credential密钥保存时，会有换行符，sql语句不支持，需要修改，已将密钥字符串转为base64      2024年2月25日 完成
★. 主机 允许添加若干条ip，含ip地址范围
★. 巡检命令中有sleep N 之类的命令时，要判断是否完成，根据shell提示符进行判断

资源操作逻辑：
★创建-资源      CreateResourceInFrame.show()  →  SaveResourceInMainWindow.save()
★列出-资源列表   ListResourceInFrame.show
★查看-资源      ViewResourceInFrame.show()
★编辑-资源      EditResourceInFrame.show()    →  UpdateResourceInFrame.update()
★删除-资源      DeleteResourceInFrame.show()

巡检流程：
★列出-巡检模板列表   ListResourceInFrame.show
★启动-巡检模板      StartInspectionTemplateInFrame.start()  →  StartInspectionTemplateInFrame.show_inspection_job_status()
                   线程|→ LaunchInspectionJob.start_job()                                      ↓
                          线程|→ LaunchInspectionJob.operator_job_thread()                    ←|查询状态
"""

import io
import os
import threading
import uuid
import time
import re
import sqlite3
import base64
import tkinter
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from multiprocessing.dummy import Pool as ThreadPool

import paramiko

# Here we go, 全局常量
COF_TRUE = 1
COF_FALSE = 0
COF_YES = 1
COF_NO = 0
CRED_TYPE_SSH_PASS = 0
CRED_TYPE_SSH_KEY = 1
CRED_TYPE_TELNET = 2
CRED_TYPE_FTP = 3
CRED_TYPE_REGISTRY = 4
CRED_TYPE_GIT = 5
PRIVILEGE_ESCALATION_METHOD_SU = 0
PRIVILEGE_ESCALATION_METHOD_SUDO = 1
FIRST_AUTH_METHOD_PRIKEY = 0
FIRST_AUTH_METHOD_PASSWORD = 1
CODE_SOURCE_LOCAL = 0
CODE_SOURCE_FILE = 1
CODE_SOURCE_GIT = 2
EXECUTION_METHOD_NONE = 0
EXECUTION_METHOD_AT = 1
EXECUTION_METHOD_CROND = 2
EXECUTION_METHOD_AFTER = 3
CODE_POST_WAIT_TIME_DEFAULT = 0.1  # 命令发送后等待的时间，秒
CODE_POST_WAIT_TIME_MAX_TIMEOUT_INTERVAL = 0.1
CODE_POST_WAIT_TIME_MAX_TIMEOUT_COUNT = 30
LOGIN_AUTH_TIMEOUT = 10  # 登录等待超时，秒
CODE_EXEC_METHOD_INVOKE_SHELL = 0
CODE_EXEC_METHOD_EXEC_COMMAND = 1
AUTH_METHOD_SSH_PASS = 0
AUTH_METHOD_SSH_KEY = 1
INTERACTIVE_PROCESS_METHOD_ONETIME = 0
INTERACTIVE_PROCESS_METHOD_ONCE = 0
INTERACTIVE_PROCESS_METHOD_TWICE = 1
INTERACTIVE_PROCESS_METHOD_LOOP = 2
DEFAULT_JOB_FORKS = 5  # 巡检作业时，目标主机的巡检并发数（同时巡检几台主机）
INSPECTION_CODE_JOB_EXEC_STATE_UNKNOWN = 0
INSPECTION_CODE_JOB_EXEC_STATE_STARTED = 1
INSPECTION_CODE_JOB_EXEC_STATE_COMPLETED = 2
INSPECTION_CODE_JOB_EXEC_STATE_PART_COMPLETED = 3
INSPECTION_CODE_JOB_EXEC_STATE_FAILED = 4
RESOURCE_TYPE_PROJECT = 0
RESOURCE_TYPE_CREDENTIAL = 1
RESOURCE_TYPE_HOST = 2
RESOURCE_TYPE_HOST_GROUP = 3
RESOURCE_TYPE_INSPECTION_CODE_BLOCK = 4
RESOURCE_TYPE_INSPECTION_TEMPLATE = 5
OUTPUT_FILE_NAME_STYLE_HOSTNAME = 0
OUTPUT_FILE_NAME_STYLE_HOSTNAME_DATE = 1
OUTPUT_FILE_NAME_STYLE_HOSTNAME_DATE_TIME = 2
OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME = 3
OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME_DATE = 4
OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME_DATE_TIME = 5
LOGIN_PROTOCOL_SSH = 0
LOGIN_PROTOCOL_TELNET = 1


class Project:
    """
    项目，是一个全局概念，一个项目包含若干资源（认证凭据，受管主机，巡检代码，巡检模板等）
    同一项目里的资源可互相引用/使用，不同项目之间的资源不可互用
    """

    def __init__(self, name='default', description='default', last_modify_timestamp=0, oid=None, create_timestamp=None, global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str>  project_oid
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.global_info = global_info
        if self.global_info is None:
            self.sqlite3_dbfile_name = self.name + '.db'
        else:
            self.sqlite3_dbfile_name = self.global_info.sqlite3_dbfile_name  # 数据库所有数据存储在此文件中
        self.last_modify_timestamp = last_modify_timestamp  # <float>

    def save(self):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_project'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_project"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_project (oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "create_timestamp double,",
                        "last_modify_timestamp double )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_project where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项目记录，则创建此项目记录 ★★
            sql_list = [f"insert into tb_project (oid,name,description,create_timestamp,last_modify_timestamp) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"{self.create_timestamp},",
                        f"{self.last_modify_timestamp} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项目记录，则更新此项目记录 ★★
            sql_list = [f"update tb_project set ",
                        f"name='{self.name}',",
                        f"description='{self.description}',",
                        f"create_timestamp={self.create_timestamp},",
                        f"last_modify_timestamp={self.last_modify_timestamp}",
                        "where",
                        f"oid='{self.oid}'"]
            print(" ".join(sql_list))
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def update(self, name='default', description='default', last_modify_timestamp=None, create_timestamp=None, global_info=None):
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if last_modify_timestamp is not None:
            self.last_modify_timestamp = last_modify_timestamp
        else:
            self.last_modify_timestamp = time.time()  # 更新last_modify时间
        if create_timestamp is not None:
            self.create_timestamp = create_timestamp
        if global_info is not None:
            self.global_info = global_info
        # 最后更新数据库
        self.save()


class Credential:
    """
    认证凭据，telnet/ssh/sftp登录凭据，snmp团体字，container-registry认证凭据，git用户凭据，ftp用户凭据
    """

    def __init__(self, name='', description='', project_oid='', cred_type=CRED_TYPE_SSH_PASS,
                 username='', password='', private_key='',
                 privilege_escalation_method=PRIVILEGE_ESCALATION_METHOD_SUDO, privilege_escalation_username='',
                 privilege_escalation_password='',
                 auth_url='', ssl_verify=COF_TRUE, last_modify_timestamp=0, oid=None, create_timestamp=None, global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str>
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_oid = project_oid  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.cred_type = cred_type  # <int>
        self.username = username  # <str>
        self.password = password  # <str>
        self.private_key = private_key  # <str>
        self.privilege_escalation_method = privilege_escalation_method
        self.privilege_escalation_username = privilege_escalation_username
        self.privilege_escalation_password = privilege_escalation_password
        self.auth_url = auth_url  # 含container-registry,git等
        self.ssl_verify = ssl_verify  # 默认为True，不校验ssl证书
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.global_info = global_info

    def save(self):
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_credential'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_credential";'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # ★若未查询到有此表，则创建此表★
        if len(result) == 0:
            sql_list = ["create table tb_credential  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "create_timestamp double,",
                        "cred_type int,"
                        "username varchar(128),",
                        "password varchar(256),",
                        "private_key_b64 varchar(8192),",
                        "privilege_escalation_method int,",
                        "privilege_escalation_username varchar(128),",
                        "privilege_escalation_password varchar(256),",
                        "auth_url varchar(2048),",
                        "ssl_verify int,",
                        "last_modify_timestamp double )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★开始插入数据/更新数据
        sql = f"select * from tb_credential where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        private_key_b64 = base64.b64encode(self.private_key.encode("utf8")).decode("utf8")
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项目记录，则创建此项目记录 ★★
            sql_list = ["insert into tb_credential (oid,",
                        "name,",
                        "description,",
                        "project_oid,",
                        "create_timestamp,",
                        "cred_type,",
                        "username,",
                        "password,",
                        "private_key_b64,",
                        "privilege_escalation_method,",
                        "privilege_escalation_username,",
                        "privilege_escalation_password,",
                        "auth_url,",
                        "ssl_verify,",
                        "last_modify_timestamp ) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"{self.create_timestamp},",
                        f"{self.cred_type},",
                        f"'{self.username}',",
                        f"'{self.password}',",
                        f"'{private_key_b64}',",
                        f"{self.privilege_escalation_method},",
                        f"'{self.privilege_escalation_username}',",
                        f"'{self.privilege_escalation_password}',",
                        f"'{self.auth_url}',",
                        f"{self.ssl_verify},",
                        f"{self.last_modify_timestamp} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项目记录，则更新此项目记录 ★★
            sql_list = ["update tb_credential  set ",
                        f"description='{self.name}',",
                        f"description='{self.description}',",
                        f"project_oid='{self.project_oid}',",
                        f"create_timestamp={self.create_timestamp},",
                        f"cred_type={self.cred_type},",
                        f"username='{self.username}',",
                        f"password='{self.password}',",
                        f"private_key_b64='{private_key_b64}',",
                        f"privilege_escalation_method={self.privilege_escalation_method},",
                        f"privilege_escalation_username='{self.privilege_escalation_username}',",
                        f"privilege_escalation_password='{self.privilege_escalation_password}',",
                        f"auth_url='{self.auth_url}',",
                        f"ssl_verify={self.ssl_verify},",
                        f"last_modify_timestamp={self.last_modify_timestamp}",
                        "where",
                        f"oid='{self.oid}'"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def update(self, name=None, description=None, project_oid=None, cred_type=None,
               username=None, password=None, private_key=None,
               privilege_escalation_method=None, privilege_escalation_username=None,
               privilege_escalation_password=None,
               auth_url=None, ssl_verify=None, last_modify_timestamp=None, create_timestamp=None, global_info=None):
        """
        ★★ 资源对象的oid不能更新，oid不能变 ★★
        :param name:
        :param description:
        :param project_oid:
        :param cred_type:
        :param username:
        :param password:
        :param private_key:
        :param privilege_escalation_method:
        :param privilege_escalation_username:
        :param privilege_escalation_password:
        :param auth_url:
        :param ssl_verify:
        :param last_modify_timestamp:
        :param create_timestamp:
        :param global_info:
        :return:
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if project_oid is not None:
            self.project_oid = project_oid
        if cred_type is not None:
            self.cred_type = cred_type
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        if private_key is not None:
            self.private_key = private_key
        if privilege_escalation_method is not None:
            self.privilege_escalation_method = privilege_escalation_method
        if privilege_escalation_username is not None:
            self.privilege_escalation_username = privilege_escalation_username
        if privilege_escalation_password is not None:
            self.privilege_escalation_password = privilege_escalation_password
        if auth_url is not None:
            self.auth_url = auth_url
        if ssl_verify is not None:
            self.ssl_verify = ssl_verify
        if last_modify_timestamp is not None:
            self.last_modify_timestamp = last_modify_timestamp
        else:
            self.last_modify_timestamp = time.time()  # 更新last_modify时间
        if create_timestamp is not None:
            self.create_timestamp = create_timestamp
        if global_info is not None:
            self.global_info = global_info
        # 最后更新数据库
        self.save()


class Host:
    """
    目标主机，受管主机
    """

    def __init__(self, name='default', description='default', project_oid='default', address='default',
                 ssh_port=22, telnet_port=23, last_modify_timestamp=0, oid=None, create_timestamp=None,
                 login_protocol=LOGIN_PROTOCOL_SSH, first_auth_method=FIRST_AUTH_METHOD_PRIKEY, global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str>
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_oid = project_oid  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.address = address  # ip address or domain name # <str>
        self.ssh_port = ssh_port  # <int>
        self.telnet_port = telnet_port  # <int>
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.login_protocol = login_protocol
        self.first_auth_method = first_auth_method
        self.credential_oid_list = []  # 元素为 Credential对象的cred_oid
        self.global_info = global_info

    def add_credential(self, credential_object):  # 每台主机都会绑定一个或多个不同类型的登录/访问认证凭据
        self.credential_oid_list.append(credential_object.oid)

    def save(self):
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host'的表★
        sql = f'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_host  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "create_timestamp double,",
                        "address varchar(256),",
                        "ssh_port int,",
                        "telnet_port int,",
                        "last_modify_timestamp double,",
                        "login_protocol int,"
                        "first_auth_method int )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_host where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项目记录，则创建此项目记录 ★★
            sql_list = [f"insert into tb_host (oid,",
                        "name,",
                        "description,",
                        "project_oid,",
                        "create_timestamp,",
                        "address,",
                        "ssh_port,",
                        "telnet_port,",
                        "last_modify_timestamp,",
                        "login_protocol,",
                        "first_auth_method ) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"{self.create_timestamp},",
                        f"'{self.address}',",
                        f"{self.ssh_port},",
                        f"{self.telnet_port},",
                        f"{self.last_modify_timestamp},"
                        f"{self.login_protocol},"
                        f"{self.first_auth_method} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项目记录，则更新此项目记录 ★★
            sql_list = [f"update tb_host set ",
                        f"name='{self.name}',",
                        f"description='{self.description}',",
                        f"project_oid='{self.project_oid}',",
                        f"create_timestamp={self.create_timestamp},",
                        f"address='{self.address}',",
                        f"ssh_port={self.ssh_port},",
                        f"telnet_port={self.telnet_port},",
                        f"last_modify_timestamp={self.last_modify_timestamp},"
                        f"login_protocol={self.login_protocol},"
                        f"first_auth_method={self.first_auth_method}",
                        "where",
                        f"oid='{self.oid}'"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_host_credential_oid_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE \
                "type"="table" and "tbl_name"="tb_host_include_credential_oid_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_include_credential_oid_list  (host_oid varchar(36), credential_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"delete from tb_host_include_credential_oid_list where host_oid='{self.oid}'"
        sqlite_cursor.execute(sql)  # ★先清空Host所有的凭据，再重新插入（既可用于新建，又可用于更新）
        for cred_oid in self.credential_oid_list:
            # sql = f"select * from tb_host_include_credential_oid_list where host_oid='{self.oid}' and credential_oid='{cred_oid}'"
            # sqlite_cursor.execute(sql)
            if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
                sql_list = [f"insert into tb_host_include_credential_oid_list (host_oid,",
                            "credential_oid ) values ",
                            f"('{self.oid}',",
                            f"'{cred_oid}' )"]
                sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def update(self, name=None, description=None, project_oid=None, address=None,
               ssh_port=None, telnet_port=None, last_modify_timestamp=None, create_timestamp=None,
               login_protocol=None, first_auth_method=None, global_info=None):
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if project_oid is not None:
            self.project_oid = project_oid
        if address is not None:
            self.address = address
        if ssh_port is not None:
            self.ssh_port = ssh_port
        if telnet_port is not None:
            self.telnet_port = telnet_port
        if last_modify_timestamp is not None:
            self.last_modify_timestamp = last_modify_timestamp
        else:
            self.last_modify_timestamp = time.time()  # 更新last_modify时间
        if create_timestamp is not None:
            self.create_timestamp = create_timestamp
        if global_info is not None:
            self.global_info = global_info
        if login_protocol is not None:
            self.login_protocol = login_protocol
        if first_auth_method is not None:
            self.first_auth_method = first_auth_method
        # 最后更新数据库
        self.save()


class HostGroup:
    """
    目标主机组，受管主机组
    """

    def __init__(self, name='default', description='default', project_oid='default', last_modify_timestamp=0, oid=None,
                 create_timestamp=None, global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str>
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_oid = project_oid  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.host_oid_list = []
        self.host_group_oid_list = []  # 不能包含自己
        self.global_info = global_info

    def add_host(self, host):
        self.host_oid_list.append(host.oid)

    def add_host_group(self, host_group):  # 不能包含自己
        if host_group.oid != self.oid:
            self.host_group_oid_list.append(host_group.oid)
        else:
            pass

    def save(self):
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host_group'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_host_group  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "create_timestamp double,",
                        "last_modify_timestamp double )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_host_group where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项目记录，则创建此项目记录 ★★
            sql_list = ["insert into tb_host_group (oid,",
                        "name,",
                        "description,",
                        "project_oid,",
                        "create_timestamp,",
                        "last_modify_timestamp )  values ",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"{self.create_timestamp},",
                        f"{self.last_modify_timestamp} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项目记录，则更新此项目记录 ★★
            sql_list = ["update tb_host_group set ",
                        f"name='{self.name}',",
                        f"description='{self.description}',",
                        f"project_oid='{self.project_oid}',",
                        f"create_timestamp={self.create_timestamp},",
                        f"last_modify_timestamp={self.last_modify_timestamp}",
                        "where",
                        f"oid='{self.oid}'"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_host_group_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_group_include_host_list  ( host_group_oid varchar(36),\
                            host_index int, host_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"delete from tb_host_group_include_host_list where host_group_oid='{self.oid}' "
        sqlite_cursor.execute(sql)  # 每次保存host前，先删除所有host内容，再去重新插入（既可用于新建，又可用于更新）
        host_index = 0
        for host_oid in self.host_oid_list:
            sql_list = ["insert into tb_host_group_include_host_list (host_group_oid,",
                        "host_index, host_oid ) values",
                        f"('{self.oid}',",
                        f"{host_index},",
                        f"'{host_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_host_group_include_host_group_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group_include_host_group_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_group_include_host_group_list  ( host_group_oid varchar(36),\
                                group_index int, group_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"delete from tb_host_group_include_host_group_list where host_group_oid='{self.oid}' "
        sqlite_cursor.execute(sql)  # 每次保存group前，先删除所有group内容，再去重新插入（既可用于新建，又可用于更新）
        group_index = 0
        for group_oid in self.host_group_oid_list:
            sql_list = ["insert into tb_host_group_include_host_group_list (host_group_oid,",
                        "group_index, group_oid )  values ",
                        f"('{self.oid}',",
                        f"{group_index},",
                        f"'{group_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def update(self, name=None, description=None, project_oid=None, last_modify_timestamp=None,
               create_timestamp=None, global_info=None):
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if project_oid is not None:
            self.project_oid = project_oid
        if last_modify_timestamp is not None:
            self.last_modify_timestamp = last_modify_timestamp
        else:
            self.last_modify_timestamp = time.time()  # 更新last_modify时间
        if create_timestamp is not None:
            self.create_timestamp = create_timestamp
        if global_info is not None:
            self.global_info = global_info
        # 最后更新数据库
        self.save()


class InspectionCodeBlock:
    """
    巡检代码段，一个<InspectionCodeBlock>巡检代码段对象包含若干行命令，一行命令为一个<OneLineCode>对象
    """

    def __init__(self, name='default', description='default', project_oid='default', code_source=CODE_SOURCE_LOCAL,
                 last_modify_timestamp=0, oid=None, create_timestamp=None, global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str>
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_oid = project_oid  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.code_source = code_source  # <int> 可为本地的命令，也可为git仓库里的写有命令的某文件
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.code_list = []  # 元素为 <OneLineCode> 对象，一条命令为一个元素，按顺序执行
        self.global_info = global_info

    def add_code_line(self, one_line_code):
        if isinstance(one_line_code, OneLineCode):
            one_line_code.code_index = len(self.code_list)
            self.code_list.append(one_line_code)

    def save(self):
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_code_block'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_code_block"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_inspection_code_block  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "create_timestamp double,",
                        "code_source int,",
                        "last_modify_timestamp double )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_inspection_code_block where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项目记录，则创建此项目记录 ★★
            sql_list = ["insert into tb_inspection_code_block (oid,",
                        "name,",
                        "description,",
                        "project_oid,",
                        "create_timestamp,",
                        "code_source,",
                        "last_modify_timestamp )  values ",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"{self.create_timestamp},",
                        f"{self.code_source},",
                        f"{self.last_modify_timestamp} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项目记录，则更新此项目记录 ★★
            sql_list = ["update tb_inspection_code_block set ",
                        f"name='{self.name}',",
                        f"description='{self.description}',",
                        f"project_oid='{self.project_oid}',",
                        f"create_timestamp={self.create_timestamp},",
                        f"code_source={self.code_source},",
                        f"last_modify_timestamp={self.last_modify_timestamp}",
                        "where",
                        f"oid='{self.oid}'"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_inspection_code_block_include_code_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_code_block_include_code_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = ["create table tb_inspection_code_block_include_code_list  ( inspection_code_block_oid varchar(36),",
                        "code_index int,",
                        "code_content varchar(512),",
                        "code_post_wait_time double,",
                        "need_interactive int,",
                        "interactive_question_keyword varchar(128),",
                        "interactive_answer varchar(32),",
                        "interactive_process_method int )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        # ★每次保存代码前，先删除所有code内容，再去重新插入
        sql = f"delete from tb_inspection_code_block_include_code_list where inspection_code_block_oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        for code in self.code_list:
            sql_list = ["insert into tb_inspection_code_block_include_code_list (inspection_code_block_oid,",
                        "code_index,",
                        "code_content,",
                        "code_post_wait_time,",
                        "need_interactive,",
                        "interactive_question_keyword,",
                        "interactive_answer,"
                        "interactive_process_method ) values",
                        f"( '{self.oid}',",
                        f"{code.code_index},",
                        f"'{code.code_content}',",
                        f"{code.code_post_wait_time},",
                        f"{code.need_interactive},",
                        f"'{code.interactive_question_keyword}',",
                        f"'{code.interactive_answer}',",
                        f"{code.interactive_process_method} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def update(self, name=None, description=None, project_oid=None, code_source=None,
               last_modify_timestamp=None, create_timestamp=None, global_info=None):
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if project_oid is not None:
            self.project_oid = project_oid
        if code_source is not None:
            self.code_source = code_source
        if last_modify_timestamp is not None:
            self.last_modify_timestamp = last_modify_timestamp
        else:
            self.last_modify_timestamp = time.time()  # 更新last_modify时间
        if create_timestamp is not None:
            self.create_timestamp = create_timestamp
        if global_info is not None:
            self.global_info = global_info
        # 最后更新数据库
        self.save()


class InspectionTemplate:
    """
    巡检模板，包含目标主机，可手动触发执行，可定时执行，可周期执行
    每创建一个<InspecionTemplate>巡检模板 就要求绑定一个<LaunchTemplateTrigger>巡检触发检测对象
    """

    def __init__(self, name='default', description='default', project_oid='default',
                 execution_method=EXECUTION_METHOD_NONE, execution_at_time=0,
                 execution_after_time=0, execution_crond_time='default', update_code_on_launch=COF_FALSE,
                 last_modify_timestamp=0, oid=None, create_timestamp=None, forks=DEFAULT_JOB_FORKS, save_output_to_file=COF_YES,
                 output_file_name_style=OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME, global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str>
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_oid = project_oid  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.execution_method = execution_method  # <int>
        self.execution_at_time = execution_at_time  # <float>
        self.execution_after_time = execution_after_time  # <float>
        self.execution_crond_time = execution_crond_time  # <str>
        # self.enabled_crond_job = enabled_crond_job  # <bool>
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.host_oid_list = []
        self.host_group_oid_list = []
        self.inspection_code_block_oid_list = []  # 巡检代码InspectionCodeBlock对象的oid
        self.update_code_on_launch = update_code_on_launch  # <int> 是否在执行项目任务时自动更新巡检代码
        self.forks = forks
        self.launch_template_trigger_oid = ''  # <str> CronDetectionTrigger对象的oid，此信息不保存到数据库
        self.save_output_to_file = save_output_to_file  # 保存巡检输出到文本文件，一台主机的巡检输出为一个txt文件
        self.output_file_name_style = output_file_name_style  # 保存巡检输出的文本文件名称风格
        self.global_info = global_info

    def add_host(self, host):
        self.host_oid_list.append(host.oid)

    def add_host_group(self, host_group):
        self.host_group_oid_list.append(host_group.oid)

    def add_inspection_code_block(self, inspection_code):
        self.inspection_code_block_oid_list.append(inspection_code.oid)

    def save(self):
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_template'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_template"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_inspection_template  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "create_timestamp double,",
                        "execution_method int,",
                        "execution_at_time double,",
                        "execution_after_time,",
                        "execution_crond_time varchar(128),",
                        "last_modify_timestamp double,",
                        "update_code_on_launch int,",
                        "forks int,",
                        "save_output_to_file int,",
                        "output_file_name_style int )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_inspection_template where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项目记录，则创建此项目记录 ★★
            sql_list = ["insert into tb_inspection_template (oid,",
                        "name,",
                        "description,",
                        "project_oid,",
                        "create_timestamp,",
                        "execution_method,",
                        "execution_at_time,",
                        "execution_after_time,",
                        "execution_crond_time,",
                        "last_modify_timestamp,",
                        "update_code_on_launch,",
                        "forks,",
                        "save_output_to_file,",
                        "output_file_name_style ) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"{self.create_timestamp},",
                        f"{self.execution_method},",
                        f"{self.execution_at_time},",
                        f"{self.execution_after_time},",
                        f"'{self.execution_crond_time}',",
                        f"{self.last_modify_timestamp},",
                        f"{self.update_code_on_launch},",
                        f"{self.forks},",
                        f"{self.save_output_to_file},",
                        f"{self.output_file_name_style} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项目记录，则更新此项目记录 ★★
            sql_list = ["update tb_inspection_template set ",
                        f"name='{self.name}',",
                        f"description='{self.description}',",
                        f"project_oid='{self.project_oid}',",
                        f"create_timestamp={self.create_timestamp},",
                        f"execution_method={self.execution_method},",
                        f"execution_at_time={self.execution_at_time},",
                        f"execution_after_time={self.execution_after_time},",
                        f"execution_crond_time='{self.execution_crond_time}',",
                        f"last_modify_timestamp={self.last_modify_timestamp},",
                        f"update_code_on_launch={self.update_code_on_launch},",
                        f"forks={self.forks},",
                        f"save_output_to_file={self.save_output_to_file},",
                        f"output_file_name_style={self.output_file_name_style}",
                        "where",
                        f"oid='{self.oid}'"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_inspection_template_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_template_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = ["create table tb_inspection_template_include_host_list",
                        "( inspection_template_oid varchar(36),",
                        "host_index int,",
                        "host_oid varchar(36) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"delete from tb_inspection_template_include_host_list where inspection_template_oid='{self.oid}' "
        sqlite_cursor.execute(sql)  # 每次保存host前，先删除所有host内容，再去重新插入（既可用于新建，又可用于更新）
        host_index = 0
        for host_oid in self.host_oid_list:
            sql_list = ["insert into tb_inspection_template_include_host_list (inspection_template_oid,",
                        "host_index, host_oid ) values",
                        f"('{self.oid}',",
                        f"{host_index},",
                        f"'{host_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_inspection_template_include_group_list'的表★
        sql = f'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_template_include_group_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = [
                "create table tb_inspection_template_include_group_list  ( inspection_template_oid varchar(36),",
                "group_index int,",
                "group_oid varchar(36) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"delete from tb_inspection_template_include_group_list where inspection_template_oid='{self.oid}' "
        sqlite_cursor.execute(sql)  # 每次保存group前，先删除所有group内容，再去重新插入（既可用于新建，又可用于更新）
        group_index = 0
        for group_oid in self.host_group_oid_list:
            sql_list = ["insert into tb_inspection_template_include_group_list"
                        "( inspection_template_oid,",
                        "group_index,",
                        "group_oid )  values ",
                        f"('{self.oid}',",
                        f"{group_index},",
                        f"'{group_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_inspection_template_include_inspection_code_block_list'的表★
        sql = f'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template_include_inspection_code_block_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = ["create table tb_inspection_template_include_inspection_code_block_list",
                        "(inspection_template_oid varchar(36), ",
                        "inspection_code_block_index int, ",
                        "inspection_code_block_oid varchar(36) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"delete from tb_inspection_template_include_inspection_code_block_list where inspection_template_oid='{self.oid}' "
        sqlite_cursor.execute(sql)  # 每次保存inspection_code_block前，先删除所有inspection_code_block内容，再去重新插入（既可用于新建，又可用于更新）
        inspection_code_block_index = 0
        for inspection_code_block_oid in self.inspection_code_block_oid_list:
            sql_list = ["insert into tb_inspection_template_include_inspection_code_block_list ",
                        "( inspection_template_oid,",
                        "inspection_code_block_index,",
                        "inspection_code_block_oid ) values",
                        f"('{self.oid}',",
                        f"{inspection_code_block_index},",
                        f"'{inspection_code_block_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
            inspection_code_block_index += 1
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def update(self, name=None, description=None, project_oid=None,
               execution_method=None, execution_at_time=None,
               execution_after_time=None, execution_crond_time=None, update_code_on_launch=None,
               last_modify_timestamp=None, create_timestamp=None, forks=None, save_output_to_file=None, output_file_name_style=None,
               global_info=None):
        if name is not None:
            self.name = name  # <str>
        if description is not None:
            self.description = description
        if project_oid is not None:
            self.project_oid = project_oid
        if execution_method is not None:
            self.execution_method = execution_method
        if execution_at_time is not None:
            self.execution_at_time = execution_at_time
        if execution_after_time is not None:
            self.execution_after_time = execution_after_time
        if execution_crond_time is not None:
            self.execution_crond_time = execution_crond_time
        if update_code_on_launch is not None:
            self.update_code_on_launch = update_code_on_launch
        if forks is not None:
            self.forks = forks
        if save_output_to_file is not None:
            self.save_output_to_file = save_output_to_file
        if output_file_name_style is not None:
            self.output_file_name_style = output_file_name_style
        if last_modify_timestamp is not None:
            self.last_modify_timestamp = last_modify_timestamp
        else:
            self.last_modify_timestamp = time.time()  # 更新last_modify时间
        if create_timestamp is not None:
            self.create_timestamp = create_timestamp
        if global_info is not None:
            self.global_info = global_info
        # 最后更新数据库
        self.save()


class LaunchTemplateTrigger:
    """
    巡检触发检测类，周期检查是否需要执行某巡检模板，每创建一个<InspecionTemplate>巡检模板 就要求绑定一个<LaunchTemplateTrigger>巡检触发检测对象
    """

    def __init__(self, name='default', description='default', project_oid='default',
                 inspection_template_oid='uuid', last_modify_timestamp=0, oid=None, create_timestamp=None, global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str>
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_oid = project_oid  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.inspection_template_oid = inspection_template_oid
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.is_time_up = False
        self.global_info = global_info

    def start_crontab_job(self):
        if self.is_time_up:
            self.start_template()
        else:
            pass

    def start_template(self):
        pass


class LaunchInspectionJob:
    """
    执行巡检任务，一次性的，由巡检触发检测类<LaunchTemplateTrigger>对象去创建并执行巡检工作，完成后输出日志
    """

    def __init__(self, name='default', description='default', oid=None, create_timestamp=None, project_oid='',
                 inspection_template=None, global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str> job_id
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.project_oid = project_oid
        self.inspection_template = inspection_template  # InspectionTemplate对象
        if isinstance(inspection_template, InspectionTemplate):
            self.inspection_template_oid = inspection_template.oid  # InspectionTemplate对象oid
        else:
            self.inspection_template_oid = ""
        self.unduplicated_host_oid_list = []  # host_oid，无重复项
        self.unduplicated_host_job_status_list = []  # host的巡检作业状态，无重复项
        self.job_state = INSPECTION_CODE_JOB_EXEC_STATE_UNKNOWN
        self.job_exec_finished_host_oid_list = []
        self.job_exec_timeout_host_oid_list = []
        self.job_exec_failed_host_oid_list = []
        self.job_find_credential_failed_host_oid_list = []
        self.global_info = global_info
        self.start_time = 0
        self.end_time = 0

    def get_unduplicated_host_oid_from_group(self, host_group_oid):  # 从主机组中获取非重复主机
        host_group = self.global_info.get_host_group_by_oid(host_group_oid)
        for host_oid in host_group.host_oid_list:
            if host_oid in self.unduplicated_host_oid_list:
                print(f"get_unduplicated_host_oid_from_group:重复主机：{self.global_info.get_host_by_oid(host_oid).name} *************")
                continue
            else:
                self.unduplicated_host_oid_list.append(host_oid)
        for group_oid in host_group.host_group_oid_list:
            self.get_unduplicated_host_oid_from_group(group_oid)
        return None

    def get_unduplicated_host_oid_from_inspection_template(self):  # 从巡检模板的主机列表及主机组列表中获取非重复主机
        if self.inspection_template is None:
            print("巡检模板为空")
            return
        for host in self.inspection_template.host_oid_list:
            if host in self.unduplicated_host_oid_list:
                print(f"get_unduplicated_host_oid_from_inspection_template:重复主机：{host.name} **********")
                continue
            else:
                self.unduplicated_host_oid_list.append(host)
        for host_group_oid in self.inspection_template.host_group_oid_list:
            self.get_unduplicated_host_oid_from_group(host_group_oid)
        self.unduplicated_host_job_status_list = [INSPECTION_CODE_JOB_EXEC_STATE_UNKNOWN for _ in
                                                  range(len(self.unduplicated_host_oid_list))]

    def create_ssh_operator_invoke_shell(self, host, host_index, cred):
        for inspection_code_block_oid in self.inspection_template.inspection_code_block_oid_list:  # 注意：巡检代码块不去重
            inspection_code_obj = self.global_info.get_inspection_code_block_by_oid(inspection_code_block_oid)
            if cred.cred_type == CRED_TYPE_SSH_PASS:
                auth_method = AUTH_METHOD_SSH_PASS
            else:
                auth_method = AUTH_METHOD_SSH_KEY
            # 一个<SSHOperator>对象操作一个<InspectionCode>巡检代码块的所有命令
            ssh_operator = SSHOperator(hostname=host.address, port=host.ssh_port, username=cred.username,
                                       password=cred.password, private_key=cred.private_key, auth_method=auth_method,
                                       command_list=inspection_code_obj.code_list, timeout=LOGIN_AUTH_TIMEOUT)
            try:
                ssh_operator.run_invoke_shell()  # 执行巡检命令，输出信息保存在 SSHOperator.output_list里，元素为<SSHOperatorOutput>
            except paramiko.AuthenticationException as e:
                print(f"目标主机 {host.name} 登录时身份验证失败: {e}")  # 登录验证失败，则此host的所有巡检code都不再继续
                self.job_exec_failed_host_oid_list.append(host.oid)
                self.unduplicated_host_job_status_list[host_index] = INSPECTION_CODE_JOB_EXEC_STATE_FAILED
                break
            max_timeout_index = 0
            while True:
                if max_timeout_index >= CODE_POST_WAIT_TIME_MAX_TIMEOUT_COUNT:
                    print(f"inspection_code: {inspection_code_obj.name} 已达最大超时-未完成")
                    self.job_exec_timeout_host_oid_list.append(host.oid)
                    self.unduplicated_host_job_status_list[host_index] = INSPECTION_CODE_JOB_EXEC_STATE_FAILED
                    break
                time.sleep(CODE_POST_WAIT_TIME_MAX_TIMEOUT_INTERVAL)
                max_timeout_index += 1
                if ssh_operator.is_finished:
                    print(f"inspection_code: {inspection_code_obj.name} 已执行完成")
                    self.job_exec_finished_host_oid_list.append(host.oid)
                    self.unduplicated_host_job_status_list[host_index] = INSPECTION_CODE_JOB_EXEC_STATE_COMPLETED
                    break
            if len(ssh_operator.output_list) != 0:
                # 判断是否需要输出信息保存到文件
                if self.inspection_template.save_output_to_file == COF_YES:
                    self.save_ssh_operator_output_to_file(ssh_operator.output_list, host, self.inspection_template.output_file_name_style)
                # 输出信息保存到sqlite数据库
                self.save_ssh_operator_invoke_shell_output_to_sqlite(ssh_operator.output_list, host, inspection_code_obj)
        print(f"create_ssh_operator_invoke_shell : 目标主机：{host.name} 已巡检完成，远程方式: ssh <<<<<<<<<<<<<<<<<<")

    def operator_job_thread(self, host_index):
        """
        正式执行主机巡检任务，一台主机一个线程，本函数只处理一台主机
        :param host_index:
        :return:
        """
        host_obj = self.global_info.get_host_by_oid(self.unduplicated_host_oid_list[host_index])
        print(f"\nLaunchInspectionJob.operator_job_thread >>>>> 目标主机：{host_obj.name} 开始巡检 <<<<<")
        self.unduplicated_host_job_status_list[host_index] = INSPECTION_CODE_JOB_EXEC_STATE_STARTED
        if host_obj.login_protocol == LOGIN_PROTOCOL_SSH:
            try:
                cred = self.find_ssh_credential(host_obj)  # 查找可用的登录凭据，这里会登录一次目标主机
            except Exception as e:
                print("查找可用的凭据错误，", e)
                self.job_find_credential_failed_host_oid_list.append(host_obj.oid)
                return
            if cred is None:
                print("Credential is None, Could not find correct credential")
                return
            self.create_ssh_operator_invoke_shell(host_obj, host_index, cred)  # ★★开始正式作业工作，执行巡检命令，将输出信息保存到文件及数据库★★
        elif host_obj.login_protocol == LOGIN_PROTOCOL_TELNET:
            print("使用telnet协议远程目标主机")
        else:
            pass
        self.unduplicated_host_job_status_list[host_index] = INSPECTION_CODE_JOB_EXEC_STATE_COMPLETED
        print(f"\nLaunchInspectionJob.operator_job_thread >>>>> 目标主机：{host_obj.name} 巡检完成 <<<<<")

    def find_ssh_credential(self, host):
        """
        查找可用的ssh凭据，会登录一次目标主机
        :param host:
        :return:
        """
        # if host.login_protocol == LOGIN_PROTOCOL_SSH:
        for cred_oid in host.credential_oid_list:
            cred = self.global_info.get_credential_by_oid(cred_oid)
            if cred.cred_type == CRED_TYPE_SSH_PASS:
                ssh_client = paramiko.client.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接host_key不在know_hosts文件里的主机
                try:
                    ssh_client.connect(hostname=host.address, port=host.ssh_port, username=cred.username,
                                       password=cred.password,
                                       timeout=LOGIN_AUTH_TIMEOUT)
                except paramiko.AuthenticationException as e:
                    # print(f"Authentication Error: {e}")
                    raise e
                ssh_client.close()
                return cred
            if cred.cred_type == CRED_TYPE_SSH_KEY:
                ssh_client = paramiko.client.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接host_key不在know_hosts文件里的主机
                prikey_obj = io.StringIO(cred.private_key)
                try:
                    pri_key = paramiko.RSAKey.from_private_key(prikey_obj)
                except paramiko.ssh_exception.SSHException as e:
                    # print("not a valid RSA private key file")
                    raise e
                try:
                    ssh_client.connect(hostname=host.address, port=host.ssh_port, username=cred.username,
                                       pkey=pri_key,
                                       timeout=LOGIN_AUTH_TIMEOUT)
                except paramiko.AuthenticationException as e:
                    # print(f"Authentication Error: {e}")
                    raise e
                ssh_client.close()
                return cred
            else:
                continue
        return None

    def save_ssh_operator_output_to_file(self, ssh_operator_output_obj_list, host, output_file_name_style):
        """
        主机的所有巡检命令输出信息都保存在一个文件里
        :param ssh_operator_output_obj_list:
        :param host:
        :param output_file_name_style:
        :return:
        """
        localtime = time.localtime(time.time())
        timestamp_date_list = [str(localtime.tm_year), self.fmt_time(localtime.tm_mon), self.fmt_time(localtime.tm_mday)]
        timestamp_time_list = [str(localtime.tm_hour), str(localtime.tm_min), str(localtime.tm_sec)]
        timestamp_date = "-".join(timestamp_date_list)  # 年月日，例：2024-01-25
        timestamp_time = ".".join(timestamp_time_list)  # 年月日，例：8.50.01
        if output_file_name_style == OUTPUT_FILE_NAME_STYLE_HOSTNAME:
            file_name = host.name + '.log'
        elif output_file_name_style == OUTPUT_FILE_NAME_STYLE_HOSTNAME_DATE:
            file_name = host.name + "__" + timestamp_date + '.log'
        elif output_file_name_style == OUTPUT_FILE_NAME_STYLE_HOSTNAME_DATE_TIME:
            file_name = host.name + "__" + timestamp_date + "__" + timestamp_time + '.log'
        elif output_file_name_style == OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME:
            os.makedirs(timestamp_date, exist_ok=True)
            file_namex = host.name + '.log'
            file_name = os.path.join(timestamp_date, file_namex)
        elif output_file_name_style == OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME_DATE:
            os.makedirs(timestamp_date, exist_ok=True)
            file_namex = host.name + "__" + timestamp_date + '.log'
            file_name = os.path.join(timestamp_date, file_namex)
        elif output_file_name_style == OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME_DATE_TIME:
            os.makedirs(timestamp_date, exist_ok=True)
            file_namex = host.name + "__" + timestamp_date + "__" + timestamp_time + '.log'
            file_name = os.path.join(timestamp_date, file_namex)
        else:
            file_name = host.name + '.log'
        # 一台主机的所有巡检命令输出信息都保存在一个文件里：主机名_巡检模板名_日期.log
        with open(file_name, 'a', encoding='utf8') as file_obj:
            for ssh_operator_output_obj in ssh_operator_output_obj_list:
                if ssh_operator_output_obj.code_exec_method == CODE_EXEC_METHOD_INVOKE_SHELL:
                    file_obj.write(ssh_operator_output_obj.invoke_shell_output_str)
                    if len(ssh_operator_output_obj.interactive_output_str_list) != 0:
                        for interactive_output_str in ssh_operator_output_obj.interactive_output_str_list:
                            file_obj.write(interactive_output_str)
                if ssh_operator_output_obj.code_exec_method == CODE_EXEC_METHOD_EXEC_COMMAND:
                    for exec_command_stderr_line in ssh_operator_output_obj.exec_command_stderr_line_list:
                        file_obj.write(exec_command_stderr_line)
                    for exec_command_stdout_line in ssh_operator_output_obj.exec_command_stdout_line_list:
                        file_obj.write(exec_command_stdout_line)

    @staticmethod
    def fmt_time(t):
        """
        格式化时间，若不足2位数，则十位数补0，用0填充
        :param t:
        :return:
        """
        if t < 10:
            return "0" + str(t)
        else:
            return str(t)

    def save_ssh_operator_invoke_shell_output_to_sqlite(self, ssh_operator_output_obj_list, host, inspection_code_obj):
        """
        主机的所有巡检命令输出信息都保存到数据库里
        :param ssh_operator_output_obj_list:
        :param host:
        :param inspection_code_obj:
        :return:
        """
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_invoke_shell_output'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job_invoke_shell_output"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_inspection_job_invoke_shell_output  ( job_oid varchar(36),",
                        "host_oid varchar(36),",
                        "inspection_code_oid varchar(36),",
                        "project_oid varchar(36),",
                        "code_index int,",
                        "code_exec_method int,",
                        "code_invoke_shell_output_str_b64 varchar(8192),",
                        "code_invoke_shell_output_last_line_b64 varchar(2048),",
                        "code_interactive_output_str_lines_b64 varchar(8192) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据，一条命令的输出为一行记录
        for code_output in ssh_operator_output_obj_list:
            sql_list = ["select * from tb_inspection_job_invoke_shell_output where",
                        f"job_oid='{self.oid}' and host_oid='{host.oid}'",
                        f"and inspection_code_oid='{inspection_code_obj.oid}'",
                        f"and code_index='{code_output.code_index}' "]
            sqlite_cursor.execute(" ".join(sql_list))
            if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
                code_invoke_shell_output_str_b64 = base64.b64encode(
                    code_output.invoke_shell_output_str.encode('utf8')).decode('utf8')
                code_invoke_shell_output_last_line_b64 = base64.b64encode(
                    code_output.invoke_shell_output_last_line.encode('utf8')).decode('utf8')
                code_interactive_output_str_lines_b64 = base64.b64encode(
                    "".join(code_output.interactive_output_str_list).encode('utf8')).decode('utf8')
                sql_list = ["insert into tb_inspection_job_invoke_shell_output (job_oid,",
                            "host_oid,",
                            "inspection_code_oid,",
                            "project_oid,",
                            "code_index,",
                            "code_exec_method,",
                            "code_invoke_shell_output_str_b64,",
                            "code_invoke_shell_output_last_line_b64,",
                            "code_interactive_output_str_lines_b64 )  values ",
                            f"( '{self.oid}',",
                            f"'{host.oid}',",
                            f"'{inspection_code_obj.oid}',",
                            f"'{host.project_oid}',",
                            f"{code_output.code_index},",
                            f"{code_output.code_exec_method},",
                            f"'{code_invoke_shell_output_str_b64}',",
                            f"'{code_invoke_shell_output_last_line_b64}',",
                            f"'{code_interactive_output_str_lines_b64}'",
                            " )"]
                print("######################## ", " ".join(sql_list))
                sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def judge_completion_of_job(self):
        if len(self.job_exec_finished_host_oid_list) == len(self.unduplicated_host_oid_list):
            self.job_state = INSPECTION_CODE_JOB_EXEC_STATE_COMPLETED
        elif len(self.job_exec_finished_host_oid_list) > 0:
            self.job_state = INSPECTION_CODE_JOB_EXEC_STATE_PART_COMPLETED
        else:
            self.job_state = INSPECTION_CODE_JOB_EXEC_STATE_FAILED

    def save_to_sqlite(self, start_time, end_time):
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_inspection_job  ( job_oid varchar(36) NOT NULL PRIMARY KEY,",
                        "job_name varchar(256),",
                        "inspection_code_oid varchar(36),",
                        "project_oid varchar(36),",
                        "start_time int,",
                        "end_time int,",
                        "job_state int )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据，一条命令的输出为一行记录
        sql_list = ["select * from tb_inspection_job where",
                    f"job_oid='{self.oid}'"]
        sqlite_cursor.execute(" ".join(sql_list))
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql_list = ["insert into tb_inspection_job (job_oid,",
                        "job_name,",
                        "inspection_code_oid,",
                        "project_oid,",
                        "start_time,",
                        "end_time,",
                        "job_state )  values ",
                        f"( '{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.inspection_template_oid}',",
                        f"'{self.project_oid}',",
                        f"{start_time},",
                        f"{end_time},",
                        f"{self.job_state} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def start_job(self):
        print("开始巡检任务 ############################################################")
        if self.inspection_template is None:
            print("巡检模板对象为空，结束本次任务")
            return
        self.start_time = time.time()
        self.get_unduplicated_host_oid_from_inspection_template()  # ★主机去重
        print("巡检模板名称：", self.inspection_template.name)
        thread_pool = ThreadPool(processes=self.inspection_template.forks)  # 创建线程池，线程数量由<InspectionTemplate>.forks决定
        thread_pool.map(self.operator_job_thread, range(len(self.unduplicated_host_oid_list)))  # ★★线程池调用巡检作业函数★★
        thread_pool.close()
        thread_pool.join()  # 会等待所有线程完成
        self.end_time = time.time()
        print("巡检任务完成 ############################################################")
        print(f"巡检并发数为{self.inspection_template.forks}")
        print("用时 {:<6.4f} 秒".format(self.end_time - self.start_time))
        # 将作业信息保存到数据库，从数据库读取出来时，不可重构为一个<LaunchInspectionJob>对象
        self.judge_completion_of_job()  # 先判断作业完成情况
        self.save_to_sqlite(self.start_time, self.end_time)  # 这里保存的只是作业信息，而不是每台主机的巡检命令输出日志


class OneLineCode:
    """
    InspectionCodeBlock.code_list列表包含的元素，一行命令为一个<OneLineCode>对象
    """

    def __init__(self, code_index=0, code_content='', code_post_wait_time=CODE_POST_WAIT_TIME_DEFAULT,
                 need_interactive=False, interactive_question_keyword='', interactive_answer='',
                 interactive_process_method=INTERACTIVE_PROCESS_METHOD_ONETIME):
        self.code_index = code_index
        self.code_content = code_content
        self.code_post_wait_time = code_post_wait_time
        self.need_interactive = need_interactive
        self.interactive_question_keyword = interactive_question_keyword
        self.interactive_answer = interactive_answer
        self.interactive_process_method = interactive_process_method


class SSHOperatorOutput:
    """
    <OneLineCode>对象的一行命令执行后的所有输出信息都保存在一个<SSHOperatorOutput>对象里
    """

    def __init__(self, code_index=0, code_content=None, code_exec_method=CODE_EXEC_METHOD_INVOKE_SHELL,
                 invoke_shell_output_str=None, invoke_shell_output_last_line=None, is_empty_output=False,
                 interactive_output_str_list=None,
                 exec_command_stdout_line_list=None,
                 exec_command_stderr_line_list=None):
        self.code_index = code_index
        self.code_content = code_content
        self.code_exec_method = code_exec_method
        if invoke_shell_output_str is None:
            self.invoke_shell_output_str = ""
        else:
            self.invoke_shell_output_str = invoke_shell_output_str  # <str> 所有输出str，可有换行符
        if invoke_shell_output_last_line is None:
            self.invoke_shell_output_last_line = ""
        else:
            self.invoke_shell_output_last_line = invoke_shell_output_last_line  # <str> 输出的最后一行
        if interactive_output_str_list is None:
            self.interactive_output_str_list = []
        else:
            self.interactive_output_str_list = interactive_output_str_list
        if exec_command_stdout_line_list is None:
            self.exec_command_stdout_line_list = []
        else:
            self.exec_command_stdout_line_list = exec_command_stdout_line_list  # <list> 元素为 str_line <str>
        if exec_command_stderr_line_list is None:
            self.exec_command_stderr_line_list = []
        else:
            self.exec_command_stderr_line_list = exec_command_stderr_line_list  # <list> 元素为 str_line <str>
        self.is_empty_output = is_empty_output


class SSHOperator:
    """
    一个<SSHOperator>对象操作一个<InspectionCodeBlock>巡检代码块的所有命令
    """

    def __init__(self, hostname='', username='', password='', private_key='', port=22,
                 timeout=30, auth_method=AUTH_METHOD_SSH_PASS, command_list=None):
        self.oid = uuid.uuid4().__str__()  # <str>
        self.hostname = hostname
        self.username = username
        self.password = password
        self.private_key = private_key
        self.port = port
        self.timeout = timeout  # 单位:秒
        self.auth_method = auth_method
        self.command_list = command_list  # ★★元素为 <OneLineCode> 对象★★
        self.is_finished = False  # False表示命令未执行完成
        self.output_list = []  # 元素类型为 <SSHOperatorOutput>，一条执行命令<OneLineCode>只产生一个output元素

    def run_invoke_shell(self):
        """
        使用invoke_shell交互式shell进行发送命令
        :return:
        """
        if self.command_list is None:
            print("SSHOperator.run_invoke_shell : command_list is None")
            return None
        ssh_client = paramiko.client.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接host_key不在know_hosts文件里的主机
        try:
            if self.auth_method == AUTH_METHOD_SSH_PASS:
                print("使用ssh_password密码登录 ##########################")
                ssh_client.connect(hostname=self.hostname, port=self.port, username=self.username,
                                   password=self.password,
                                   timeout=self.timeout)
            elif self.auth_method == AUTH_METHOD_SSH_KEY:
                prikey_string_io = io.StringIO(self.private_key)
                pri_key = paramiko.RSAKey.from_private_key(prikey_string_io)
                print("使用ssh_key密钥登录 ##########################")
                ssh_client.connect(hostname=self.hostname, port=self.port, username=self.username,
                                   pkey=pri_key, timeout=self.timeout)
            else:
                pass
        except paramiko.AuthenticationException as e:
            # print(f"Authentication Error: {e}")
            raise e
        time.sleep(CODE_POST_WAIT_TIME_DEFAULT)  # 远程连接后，首先等待一会，可能会有信息输出
        ssh_shell = ssh_client.invoke_shell()  # 创建一个交互式shell
        try:
            recv = ssh_shell.recv(65535)  # 获取登录后的输出信息，此时未执行任何命令
        except Exception as e:
            print(e)
            return
        # 创建命令输出对象<SSHOperatorOutput>，一条命令对应一个<SSHOperatorOutput>对象
        invoke_shell_output_str = recv.decode('utf8').replace('\r', '')  # 登录后的输出信息，换行符为\r\n，这里去除一个\r，只留\n
        output = SSHOperatorOutput(code_index=-1, code_exec_method=CODE_EXEC_METHOD_INVOKE_SHELL,
                                   invoke_shell_output_str=invoke_shell_output_str)
        self.output_list.append(output)  # 刚登录后的输出信息保存到output_list里
        print("登录后输出内容如下 #############################################")
        print(invoke_shell_output_str)
        # ★★开始执行正式命令★★
        cmd_index = 0
        for one_line_code in self.command_list:
            if not isinstance(one_line_code, OneLineCode):
                return
            ssh_shell.send(one_line_code.code_content.strip().encode('utf8'))  # 发送巡检命令，一行命令
            ssh_shell.send("\n".encode('utf8'))  # 命令strip()后，不带\n换行，需要额外发送一个换行符
            time.sleep(one_line_code.code_post_wait_time)  # 发送完命令后，要等待系统回复★
            try:
                recv = ssh_shell.recv(65535)
            except Exception as e:
                print(e)
                return
            invoke_shell_output_str_list = recv.decode('utf8').split('\r\n')
            invoke_shell_output_str = '\n'.join(invoke_shell_output_str_list)  # 这与前面一行共同作用是去除'\r'
            output_str_lines = invoke_shell_output_str.split('\n')
            output_last_line_index = len(output_str_lines) - 1
            output_last_line = output_str_lines[output_last_line_index]  # 命令输出最后一行（shell提示符，不带换行符的）
            output = SSHOperatorOutput(code_index=cmd_index, code_exec_method=CODE_EXEC_METHOD_INVOKE_SHELL,
                                       code_content=one_line_code.code_content, invoke_shell_output_str=invoke_shell_output_str,
                                       invoke_shell_output_last_line=output_last_line)
            self.output_list.append(output)  # 命令输出结果保存到output_list里
            print(f"$$ 命令{cmd_index} $$ 输出结果如下 #############################################")
            print(invoke_shell_output_str)
            print(f"命令输出最后一行（shell提示符，不带换行符的）为:  {output_last_line.encode('utf8')}")  # 有的提示符末尾有个空格
            if one_line_code.need_interactive:  # 命令如果需要处理交互情况，则判断交互提问关键词
                self.process_code_interactive(one_line_code, output_last_line, ssh_shell, output)
            cmd_index += 1
        ssh_shell.close()
        ssh_client.close()
        self.is_finished = True

    @staticmethod
    def process_code_interactive(code, output_last_line, ssh_shell, output, second_time=False):
        """
        处理命令的交互式应答，有时执行某些命令执后，系统会提示输入[Y/N]?，要求回复
        :param code:
        :param output_last_line:
        :param ssh_shell:
        :param output:
        :param second_time:
        :return:
        """
        ret = re.search(code.interactive_question_keyword, output_last_line, re.I)
        if ret is not None:  # 如果匹配上需要交互的提问判断字符串
            print(f"★★匹配到交互关键字 {ret} ，执行交互回答:")
            ssh_shell.send(code.interactive_answer.encode('utf8'))  # 发送交互回答内容，这里不会额外发送\n换行
            # ssh_shell.send("\n".encode('utf8'))  # 命令strip()后，不带\n换行，需要额外发送一个换行符
            time.sleep(code.code_post_wait_time)  # 发送完命令后，要等待系统回复
            try:
                recv = ssh_shell.recv(65535)
            except Exception as e:
                print(e)
                return
            # interactive_output_str_list = recv.decode('utf8').split('\r\n')
            # interactive_output_str = '\n'.join(interactive_output_str_list)  # 这与前面一行共同作用是去除'\r'
            interactive_output_str = recv.decode('utf8').replace('\r', '')
            print(interactive_output_str)
            output.interactive_output_str_list.append(interactive_output_str)
            if second_time is True:
                print("上面输出为twice的★★★★★")
                return
            interactive_output_str_lines = interactive_output_str.split('\n')
            interactive_output_last_line_index = len(interactive_output_str_lines) - 1
            if code.interactive_process_method == INTERACTIVE_PROCESS_METHOD_LOOP and len(interactive_output_str_lines) != 0:
                SSHOperator.process_code_interactive(code, interactive_output_str_lines[interactive_output_last_line_index], ssh_shell,
                                                     output)
            if code.interactive_process_method == INTERACTIVE_PROCESS_METHOD_TWICE and len(interactive_output_str_lines) != 0:
                SSHOperator.process_code_interactive(code, interactive_output_str_lines[interactive_output_last_line_index], ssh_shell,
                                                     output, second_time=True)
        else:
            # 如果没有匹配上需要交互的提问判断字符串，就结束交互
            return

    def exec_command(self):
        """
        与 run_invoke_shell 相对应，非invoke_shell，不适用于交换机等设备
        :return:
        """
        if self.command_list is None:
            return None
        ssh_client = paramiko.client.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接host_key不在know_hosts文件里的主机
        try:
            ssh_client.connect(hostname=self.hostname, port=self.port, username=self.username, password=self.password,
                               timeout=self.timeout)
        except paramiko.AuthenticationException as e:
            print(f"Authentication Error: {e}")
            return None
        # ★下面这一段是连接linux主机的，非invoke_shell
        cmd_index = 0
        for code in self.command_list:
            if not isinstance(code, OneLineCode):
                return
            print(f"执行命令{cmd_index} : {code.code_content.strip()}")
            stdin, stdout, stderr = ssh_client.exec_command(code.code_content)
            stdout_line_list = stdout.readlines()
            if len(stdout_line_list) != 0:
                output = SSHOperatorOutput(code_index=cmd_index, code_exec_method=CODE_EXEC_METHOD_EXEC_COMMAND,
                                           code_content=code.code_content,
                                           exec_command_stdout_line_list=stdout_line_list)
                self.output_list.append(output)
                print(f"命令{cmd_index} 输出结果:")
                for ret_line in stdout_line_list:
                    print(ret_line, end="")
            stderr_line_list = stderr.readlines()
            if len(stderr_line_list) != 0:
                output = SSHOperatorOutput(code_index=cmd_index, code_exec_method=CODE_EXEC_METHOD_EXEC_COMMAND,
                                           code_content=code.code_content,
                                           exec_command_stderr_line_list=stderr_line_list)
                self.output_list.append(output)
                print(f"命令{cmd_index} stderr结果:")
                for ret_line in stderr_line_list:
                    print(ret_line, end="")
            if len(stdout_line_list) == 0 and len(stderr_line_list) == 0:
                output = SSHOperatorOutput(code_index=cmd_index, code_exec_method=CODE_EXEC_METHOD_EXEC_COMMAND,
                                           code_content=code.code_content,
                                           is_empty_output=True)
                self.output_list.append(output)
            cmd_index += 1
        ssh_client.close()
        self.is_finished = True


class GlobalInfo:
    """
    全局变量类，用于存储所有资源类的实例信息
    """

    def __init__(self, sqlite3_dbfile_name="cofable_default.db"):
        self.sqlite3_dbfile_name = sqlite3_dbfile_name  # 若未指定数据库文件名称，则默认为"cofable_default.db"
        self.project_obj_list = []
        self.credential_obj_list = []
        self.host_obj_list = []
        self.host_group_obj_list = []
        self.inspection_code_block_obj_list = []
        self.inspection_template_obj_list = []
        self.inspection_job_obj_list = []
        self.current_project_obj = None  # 需要在项目界面将某个项目设置为当前项目，才会赋值

    def set_sqlite3_dbfile_name(self, file_name):
        self.sqlite3_dbfile_name = file_name

    def load_all_data_from_sqlite3(self):  # 初始化global_info，从数据库加载所有数据到实例
        if self.sqlite3_dbfile_name is None:
            print("undefined sqlite3_dbfile_name")
            return
        elif self.sqlite3_dbfile_name == '':
            print("sqlite3_dbfile_name is null")
            return
        else:
            self.project_obj_list = self.load_project_from_dbfile()
            self.credential_obj_list = self.load_credential_from_dbfile()
            self.host_obj_list = self.load_host_from_dbfile()
            self.host_group_obj_list = self.load_host_group_from_dbfile()
            self.inspection_code_block_obj_list = self.load_inspection_code_block_from_dbfile()
            self.inspection_template_obj_list = self.load_inspection_template_from_dbfile()

    def load_project_from_dbfile(self):
        """
        从sqlite3数据库文件，查找所有project，并输出project对象列表，output <list[Project]>
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_project'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_project"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        sql = f"select * from tb_project"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        obj_list = []
        for obj_info_tuple in search_result:
            obj = Project(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                          create_timestamp=obj_info_tuple[3], last_modify_timestamp=obj_info_tuple[4], global_info=self)
            obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        return obj_list

    def load_credential_from_dbfile(self):
        """
        从sqlite3数据库文件，查找所有credential，并输出credential对象列表，output <list>
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_credential'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_credential"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        sql = f"select * from tb_credential"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        obj_list = []
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            obj = Credential(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                             project_oid=obj_info_tuple[3], create_timestamp=obj_info_tuple[4],
                             cred_type=obj_info_tuple[5],
                             username=obj_info_tuple[6],
                             password=obj_info_tuple[7],
                             private_key=base64.b64decode(obj_info_tuple[8]).decode('utf8'),
                             privilege_escalation_method=obj_info_tuple[9],
                             privilege_escalation_username=obj_info_tuple[10],
                             privilege_escalation_password=obj_info_tuple[11],
                             auth_url=obj_info_tuple[12],
                             ssl_verify=obj_info_tuple[13],
                             last_modify_timestamp=obj_info_tuple[14], global_info=self)
            obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        return obj_list

    def load_host_from_dbfile(self):
        """
        从sqlite3数据库文件，查找所有host，并输出host对象列表，output <list>
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        sql = f"select * from tb_host"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        obj_list = []
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            obj = Host(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                       project_oid=obj_info_tuple[3], create_timestamp=obj_info_tuple[4],
                       address=obj_info_tuple[5],
                       ssh_port=obj_info_tuple[6],
                       telnet_port=obj_info_tuple[7],
                       last_modify_timestamp=obj_info_tuple[8],
                       login_protocol=obj_info_tuple[9],
                       first_auth_method=obj_info_tuple[10], global_info=self)
            obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        self.load_host_include_credential_from_dbfile(obj_list)
        return obj_list

    def load_host_include_credential_from_dbfile(self, host_list):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host_include_credential_oid_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_include_credential_oid_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for host in host_list:
            sql = f"select * from tb_host_include_credential_oid_list where host_oid='{host.oid}'"
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                host.credential_oid_list.append(obj_info_tuple[1])

    def load_host_group_from_dbfile(self):
        """
        从sqlite3数据库文件，查找所有host_group，并输出host_group对象列表，output <list>
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host_group'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_group"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        sql = f"select * from tb_host_group"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        obj_list = []
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            obj = HostGroup(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                            project_oid=obj_info_tuple[3], create_timestamp=obj_info_tuple[4],
                            last_modify_timestamp=obj_info_tuple[5], global_info=self)
            obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        self.load_host_group_include_host_from_dbfile(obj_list)
        self.load_host_group_include_host_group_from_dbfile(obj_list)
        return obj_list

    def load_host_group_include_host_from_dbfile(self, host_group_list):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host_group_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_group_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for host_group in host_group_list:
            sql = f"select * from tb_host_group_include_host_list where host_group_oid='{host_group.oid}'"
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                host_group.host_oid_list.append(obj_info_tuple[2])

    def load_host_group_include_host_group_from_dbfile(self, host_group_list):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host_group_include_host_group_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_group_include_host_group_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for host_group in host_group_list:
            sql = f"select * from tb_host_group_include_host_group_list where host_group_oid='{host_group.oid}'"
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                host_group.host_group_oid_list.append(obj_info_tuple[2])

    def load_inspection_code_block_from_dbfile(self):
        """
        从sqlite3数据库文件，查找所有inspection_code，并输出inspection_code对象列表，output <list>
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_code'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_code_block"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        sql = f"select * from tb_inspection_code_block"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        obj_list = []
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            obj = InspectionCodeBlock(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                                      project_oid=obj_info_tuple[3], create_timestamp=obj_info_tuple[4],
                                      code_source=obj_info_tuple[5],
                                      last_modify_timestamp=obj_info_tuple[6], global_info=self)
            obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        self.load_inspection_code_list_from_dbfile(obj_list)
        return obj_list

    def load_inspection_code_list_from_dbfile(self, inspection_code_list):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_code_block_include_code_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_code_block_include_code_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for inspection_code in inspection_code_list:
            sql = f"select * from tb_inspection_code_block_include_code_list where inspection_code_block_oid='{inspection_code.oid}'"
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                code = OneLineCode(code_index=obj_info_tuple[1], code_content=obj_info_tuple[2],
                                   code_post_wait_time=obj_info_tuple[3], need_interactive=obj_info_tuple[4],
                                   interactive_question_keyword=obj_info_tuple[5],
                                   interactive_answer=obj_info_tuple[6],
                                   interactive_process_method=obj_info_tuple[7])
                inspection_code.code_list.append(code)

    def load_inspection_template_from_dbfile(self):
        """
        从sqlite3数据库文件，查找所有inspection_template，并输出inspection_template对象列表，output <list>
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_template'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        sql = f"select * from tb_inspection_template"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        obj_list = []
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            obj = InspectionTemplate(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                                     project_oid=obj_info_tuple[3], create_timestamp=obj_info_tuple[4],
                                     execution_method=obj_info_tuple[5],
                                     execution_at_time=obj_info_tuple[6],
                                     execution_after_time=obj_info_tuple[7],
                                     execution_crond_time=obj_info_tuple[8],
                                     last_modify_timestamp=obj_info_tuple[9],
                                     update_code_on_launch=obj_info_tuple[10],
                                     forks=obj_info_tuple[11],
                                     save_output_to_file=obj_info_tuple[12],
                                     output_file_name_style=obj_info_tuple[13],
                                     global_info=self)
            obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        self.load_inspection_template_include_host_from_dbfile(obj_list)
        self.load_inspection_template_include_host_group_from_dbfile(obj_list)
        self.load_inspection_template_include_inspection_code_block_from_dbfile(obj_list)
        return obj_list

    def load_inspection_template_include_host_from_dbfile(self, inspection_template_list):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_template_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for inspection_template in inspection_template_list:
            sql = f"select * from tb_inspection_template_include_host_list where \
                    inspection_template_oid='{inspection_template.oid}'"
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                inspection_template.host_oid_list.append(obj_info_tuple[2])

    def load_inspection_template_include_host_group_from_dbfile(self, inspection_template_list):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_template_include_group_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template_include_group_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for inspection_template in inspection_template_list:
            sql = f"select * from tb_inspection_template_include_group_list where \
                    inspection_template_oid='{inspection_template.oid}'"
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                inspection_template.host_group_oid_list.append(obj_info_tuple[2])

    def load_inspection_template_include_inspection_code_block_from_dbfile(self, inspection_template_list):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_template_include_inspection_code_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" \
                    and tbl_name="tb_inspection_template_include_inspection_code_block_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for inspection_template in inspection_template_list:
            sql = f"select * from tb_inspection_template_include_inspection_code_block_list where \
            inspection_template_oid='{inspection_template.oid}'"
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                inspection_template.inspection_code_block_oid_list.append(obj_info_tuple[2])

    def is_project_name_existed(self, project_name):  # 判断项目名称是否已存在项目obj_list里
        for project in self.project_obj_list:
            if project_name == project.name:
                return True
        return False

    def is_credential_name_existed(self, credential_name):  # 判断名称是否已存在obj_list里
        for credential in self.credential_obj_list:
            if credential_name == credential.name:
                return True
        return False

    def is_host_name_existed(self, host_name):  # 判断名称是否已存在obj_list里
        for host in self.host_obj_list:
            if host_name == host.name:
                return True
        return False

    def is_host_group_name_existed(self, host_group_name):  # 判断名称是否已存在obj_list里
        for host_group in self.host_group_obj_list:
            if host_group_name == host_group.name:
                return True
        return False

    def is_inspection_code_block_name_existed(self, inspect_code_name):  # 判断名称是否已存在obj_list里
        for inspection_code in self.inspection_code_block_obj_list:
            if inspect_code_name == inspection_code.name:
                return True
        return False

    def is_inspection_template_name_existed(self, inspect_template_name):  # 判断名称是否已存在obj_list里
        for inspection_template in self.inspection_template_obj_list:
            if inspect_template_name == inspection_template.name:
                return True
        return False

    def get_project_by_oid(self, oid):
        """
        根据项目oid/uuid<str>查找项目对象，找到时返回<Project>对象
        :param oid:
        :return:
        """
        for project in self.project_obj_list:
            if project.oid == oid:
                return project
        return None

    def get_credential_by_oid(self, oid):
        for credential in self.credential_obj_list:
            if credential.oid == oid:
                return credential
        return None

    def get_host_by_oid(self, oid):
        for host in self.host_obj_list:
            if host.oid == oid:
                return host
        return None

    def get_host_group_by_oid(self, oid):
        for host_group in self.host_group_obj_list:
            if host_group.oid == oid:
                return host_group
        return None

    def get_inspection_code_block_by_oid(self, oid):
        for inspection_code_block in self.inspection_code_block_obj_list:
            if inspection_code_block.oid == oid:
                return inspection_code_block
        return None

    def get_inspection_template_by_oid(self, oid):
        for inspection_template in self.inspection_template_obj_list:
            if inspection_template.oid == oid:
                return inspection_template
        return None

    def get_project_obj_index_of_list_by_oid(self, oid):
        index = 0
        for obj in self.project_obj_list:
            if obj.oid == oid:
                return index
            index += 1
        return None

    def get_credential_obj_index_of_list_by_oid(self, oid):
        index = 0
        for obj in self.credential_obj_list:
            if obj.oid == oid:
                return index
            index += 1
        return None

    def get_host_obj_index_of_list_by_oid(self, oid):
        index = 0
        for obj in self.host_obj_list:
            if obj.oid == oid:
                return index
            index += 1
        return None

    def get_host_group_obj_index_of_list_by_oid(self, oid):
        index = 0
        for obj in self.host_group_obj_list:
            if obj.oid == oid:
                return index
            index += 1
        return None

    def get_inspection_code_block_obj_index_of_list_by_oid(self, oid):
        index = 0
        for obj in self.inspection_code_block_obj_list:
            if obj.oid == oid:
                return index
            index += 1
        return None

    def get_inspection_template_obj_index_of_list_by_oid(self, oid):
        index = 0
        for obj in self.inspection_template_obj_list:
            if obj.oid == oid:
                return index
            index += 1
        return None

    def get_inspection_job_obj_by_inspection_template_oid(self, oid):
        index = 0
        existed_inspection_job_obj_list = []
        for obj in self.inspection_job_obj_list:
            if obj.inspection_template_oid == oid:
                existed_inspection_job_obj_list.append(obj)
            index += 1
        return existed_inspection_job_obj_list

    def delete_project_obj_by_oid(self, oid):
        """
        根据项目oid/uuid<str>删除项目对象
        :param oid:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_project'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_project"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_project where oid='{oid}'"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        for project in self.project_obj_list:
            if project.oid == oid:
                self.project_obj_list.remove(project)

    def delete_project_obj(self, obj):
        """
        直接删除 project 对象
        :param obj:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_project'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_project"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        # print("exist tables: ", result)
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_project where oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.project_obj_list.remove(obj)

    def delete_credential_obj(self, obj):
        """
        直接删除 credential 对象
        :param obj:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_credential'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_credential"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_credential where oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.credential_obj_list.remove(obj)

    def delete_host_obj(self, obj):
        """
        直接删除 host 对象
        :param obj:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_host where oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_host_credential_oid_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE \
                    "type"="table" and "tbl_name"="tb_host_include_credential_oid_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_host_include_credential_oid_list where host_oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.host_obj_list.remove(obj)

    def delete_host_group_obj(self, obj):
        """
        直接删除 host_group 对象
        :param obj:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host_group'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_group"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_host_group where oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_host_group_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        print("exist tables: ", result)
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_host_group_include_host_list where host_group_oid='{obj.oid}' "
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_host_group_include_host_group_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group_include_host_group_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        print("exist tables: ", result)
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_host_group_include_host_group_list where host_group_oid='{obj.oid}' "
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.host_group_obj_list.remove(obj)

    def delete_inspection_code_block_obj(self, obj):
        """
        直接删除 inspection_code_block 对象
        :param obj:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_code_block'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_code_block"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_code_block where oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_code_block_include_code_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_code_block_include_code_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_code_block_include_code_list where inspection_code_block_oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.inspection_code_block_obj_list.remove(obj)

    def delete_inspection_template_obj(self, obj):
        """
        直接删除 inspection_template 对象
        :param obj:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_template'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_template where oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_template_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_template_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_template_include_host_list where inspection_template_oid='{obj.oid}' "
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_template_include_group_list'的表★
        sql = f'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_template_include_group_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_template_include_group_list where inspection_template_oid='{obj.oid}' "
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_template_include_inspection_code_list'的表★
        sql = f'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template_include_inspection_code_block_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_template_include_inspection_code_list where inspection_template_oid='{obj.oid}' "
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.inspection_template_obj_list.remove(obj)


class MainWindow:
    """
    CofAble主界面类，包含菜单栏及左右2个frame
    """

    def __init__(self, width=640, height=400, title='', current_project=None, global_info=None):
        self.title = title
        self.width = width
        self.height = height
        self.position = "480x320+100+100"
        self.resizable = True  # True 表示宽度和高度可由用户手动调整
        self.minsize = (480, 320)
        self.maxsize = (1920, 1080)
        self.background = "#3A3A3A"  # 设置背景色，RGB
        self.window_obj = tkinter.Tk()  # ★★★创建窗口对象
        self.screen_width = self.window_obj.winfo_screenwidth()
        self.screen_height = self.window_obj.winfo_screenheight()
        self.win_pos_x = self.screen_width // 2 - self.width // 2
        self.win_pos_y = self.screen_height // 2 - self.height // 2
        self.win_pos = f"{self.width}x{self.height}+{self.win_pos_x}+{self.win_pos_y}"
        self.nav_frame_l = None
        self.nav_frame_r = None
        self.nav_frame_l_width = int(self.width * 0.2)
        self.nav_frame_r_width = int(self.width * 0.8)
        self.global_info = global_info  # <GlobalInfo>对象
        self.current_project = current_project
        self.about_info = "CofAble，自动化巡检平台，版本: v1.0\n本软件使用GPL-v3.0协议开源，作者: Cof-Lee"
        self.padx = 2
        self.pady = 2
        self.view_width = 20

    @staticmethod
    def clear_tkinter_frame(frame):
        for widget in frame.winfo_children():
            widget.destroy()

    @staticmethod
    def clear_tkinter_window(window):
        for widget in window.winfo_children():
            widget.destroy()

    def load_main_window_init_widget(self):
        """
        加载程序初始化界面控件
        :return:
        """
        # 首先清空主window
        self.clear_tkinter_window(self.window_obj)
        # 加载菜单栏
        self.create_menu_bar_init()
        # 创建导航框架1
        self.create_nav_frame_l_init()
        # 创建导航框架2
        self.create_nav_frame_r_init()

    def create_menu_bar_init(self):  # 创建菜单栏-init界面的
        menu_bar = tkinter.Menu(self.window_obj)  # 创建一个菜单，做菜单栏
        menu_open_db_file = tkinter.Menu(menu_bar, tearoff=1)  # 创建一个菜单，分窗，表示此菜单可拉出来变成一个可移动的独立弹窗
        menu_about = tkinter.Menu(menu_bar, tearoff=0, activebackground="green", activeforeground="white",
                                  background="white", foreground="black")  # 创建一个菜单，不分窗
        menu_open_db_file.add_command(label="打开数据库文件", command=self.click_menu_open_db_file_of_menu_bar_init)
        menu_about.add_command(label="About", command=self.click_menu_about_of_menu_bar_init)
        menu_bar.add_cascade(label="File", menu=menu_open_db_file)
        menu_bar.add_cascade(label="Help", menu=menu_about)
        self.window_obj.config(menu=menu_bar)

    def create_nav_frame_l_init(self):  # 创建导航框架1-init界面的 ★★★★★
        self.nav_frame_l = tkinter.Frame(self.window_obj, bg="green", width=self.nav_frame_l_width, height=self.height)
        self.nav_frame_l.grid_propagate(False)
        self.nav_frame_l.pack_propagate(False)
        self.nav_frame_l.grid(row=0, column=0)
        # ★ 在框架1中添加功能按钮 ★
        # Project项目-选项按钮
        menu_button_project = tkinter.Button(self.nav_frame_l, text="Project项目", width=self.nav_frame_l_width, height=2, bg="white",
                                             command=lambda: self.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_PROJECT))
        menu_button_project.pack(padx=self.padx, pady=self.pady)
        # Credentials凭据-选项按钮
        menu_button_credential = tkinter.Button(self.nav_frame_l, text="Credentials凭据", width=self.nav_frame_l_width, height=2,
                                                bg="white",
                                                command=lambda: self.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_CREDENTIAL))
        menu_button_credential.pack(padx=self.padx, pady=self.pady)
        # Host主机管理-选项按钮
        menu_button_host = tkinter.Button(self.nav_frame_l, text="Host主机管理", width=self.nav_frame_l_width, height=2, bg="white",
                                          command=lambda: self.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_HOST))
        menu_button_host.pack(padx=self.padx, pady=self.pady)
        # Host_group主机组管理-选项按钮
        menu_button_host = tkinter.Button(self.nav_frame_l, text="HostGroup管理", width=self.nav_frame_l_width, height=2, bg="white",
                                          command=lambda: self.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_HOST_GROUP))
        menu_button_host.pack(padx=self.padx, pady=self.pady)
        # Inspect巡检代码块-选项按钮
        menu_button_inspect_code = tkinter.Button(self.nav_frame_l, text="Inspect巡检代码块", width=self.nav_frame_l_width, height=2,
                                                  bg="white",
                                                  command=lambda: self.nav_frame_r_resource_top_page_display(
                                                      RESOURCE_TYPE_INSPECTION_CODE_BLOCK))
        menu_button_inspect_code.pack(padx=self.padx, pady=self.pady)
        # Template巡检模板-选项按钮
        menu_button_inspection_template = tkinter.Button(self.nav_frame_l, text="Template巡检模板", width=self.nav_frame_l_width,
                                                         height=2, bg="white",
                                                         command=lambda: self.nav_frame_r_resource_top_page_display(
                                                             RESOURCE_TYPE_INSPECTION_TEMPLATE))
        menu_button_inspection_template.pack(padx=self.padx, pady=self.pady)
        # 时间-标签
        label_current_time = tkinter.Label(self.nav_frame_l, text=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        label_current_time.pack(padx=self.padx, pady=self.pady)
        label_current_time.after(1000, self.refresh_label_current_time, label_current_time)
        # 当前项目-标签
        if self.global_info.current_project_obj is None:
            label_current_project_content = "当前无项目"
        else:
            label_current_project_content = "当前项目-" + self.global_info.current_project_obj.name
        label_current_project = tkinter.Label(self.nav_frame_l, text=label_current_project_content,
                                              width=self.nav_frame_l_width, height=2)

        label_current_project.pack(padx=self.padx, pady=self.pady)

    def create_nav_frame_r_init(self):  # 创建导航框架2-init界面的
        self.nav_frame_r = tkinter.Frame(self.window_obj, bg="blue", width=self.nav_frame_r_width, height=self.height)
        self.nav_frame_r.grid_propagate(False)
        self.nav_frame_r.pack_propagate(False)
        self.nav_frame_r.grid(row=0, column=1)
        # 在框架2中添加canvas-frame滚动框
        self.clear_tkinter_frame(self.nav_frame_r)
        scrollbar = tkinter.Scrollbar(self.nav_frame_r)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        canvas = tkinter.Canvas(self.nav_frame_r, yscrollcommand=scrollbar.set)  # 创建画布
        # canvas.pack(fill=tkinter.X, expand=tkinter.TRUE)
        canvas.place(x=0, y=0, width=self.nav_frame_r_width - 25, height=self.height - 50)
        scrollbar.config(command=canvas.yview)
        frame = tkinter.Frame(canvas)
        frame.pack()
        canvas.create_window((0, 0), window=frame, anchor='nw')
        # 添加控件
        label_init = tkinter.Label(self.nav_frame_r, text="初始化界面")
        label_init.grid(row=0, column=0)
        label_project_count_str = "项目数量".ljust(self.view_width, " ") + ": " + str(len(self.global_info.project_obj_list))
        label_project_count = tkinter.Label(self.nav_frame_r, text=label_project_count_str)
        label_project_count.grid(row=1, column=0)
        label_credential_count_str = "凭据数量".ljust(self.view_width, " ") + ": " + str(len(self.global_info.credential_obj_list))
        label_credential_count = tkinter.Label(self.nav_frame_r, text=label_credential_count_str)
        label_credential_count.grid(row=2, column=0)
        label_host_count_str = "主机数量".ljust(self.view_width, " ") + ": " + str(len(self.global_info.host_obj_list))
        label_host_count = tkinter.Label(self.nav_frame_r, text=label_host_count_str)
        label_host_count.grid(row=3, column=0)
        label_host_group_count_str = "主机组数量".ljust(self.view_width, " ") + ": " + str(len(self.global_info.host_group_obj_list))
        label_host_group_count = tkinter.Label(self.nav_frame_r, text=label_host_group_count_str)
        label_host_group_count.grid(row=4, column=0)
        label_inspect_code_count_str = "巡检代码块数量".ljust(self.view_width - 6, " ") \
                                       + ": " + str(len(self.global_info.inspection_code_block_obj_list))
        label_inspect_code_count = tkinter.Label(self.nav_frame_r, text=label_inspect_code_count_str)
        label_inspect_code_count.grid(row=5, column=0)
        label_inspect_template_count_str = "巡检模板数量".ljust(self.view_width - 4, " ") + ": " \
                                           + str(len(self.global_info.inspection_template_obj_list))
        label_inspect_template_count = tkinter.Label(self.nav_frame_r, text=label_inspect_template_count_str)
        label_inspect_template_count.grid(row=6, column=0)

    def refresh_label_current_time(self, label):
        label.__setitem__('text', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        # 继续调用回调函数更新label
        self.window_obj.after(1000, self.refresh_label_current_time, label)

    def click_menu_about_of_menu_bar_init(self):
        messagebox.showinfo("About", self.about_info)

    def click_menu_open_db_file_of_menu_bar_init(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.db"), ("All files", "*.*")])
        if not file_path:
            print("not choose a file")
        else:
            print(file_path)
            self.global_info.set_sqlite3_dbfile_name(file_path)
            self.global_info.load_all_data_from_sqlite3()  # 已有的obj_list会被清空，生成加载后的新的obj_list（要注意已有信息是否已保存到数据库）

    def reload_current_resized_window(self, event):  # 监听窗口大小变化事件，自动更新窗口内控件大小
        if event:
            if self.window_obj.winfo_width() == self.width and self.window_obj.winfo_height() == self.height:
                return
            else:
                self.width = self.window_obj.winfo_width()
                self.height = self.window_obj.winfo_height()
                self.nav_frame_l_width = int(self.width * 0.2)
                self.nav_frame_r_width = int(self.width * 0.8)
                print("size changed")
                # self.window_obj.__setitem__('width', self.width)
                # self.window_obj.__setitem__('height', self.height)
                self.window_obj.configure(width=self.width)
                self.window_obj.configure(height=self.height)
                self.window_obj.winfo_children()[1].__setitem__('width', self.width * 0.2)
                self.window_obj.winfo_children()[1].__setitem__('height', self.height)
                self.window_obj.winfo_children()[2].__setitem__('width', self.width * 0.8)
                self.window_obj.winfo_children()[2].__setitem__('height', self.height)

    def create_resource_of_nav_frame_r_page(self, resource_type):
        """
        ★★★★★ 创建资源-页面 ★★★★★
        :return:
        """
        # 更新导航框架2
        nav_frame_r = self.window_obj.winfo_children()[2]
        nav_frame_r.__setitem__("bg", "green")
        nav_frame_r_widget_dict = {}
        # 在框架2中添加canvas-frame滚动框
        self.clear_tkinter_frame(nav_frame_r)
        nav_frame_r_widget_dict["scrollbar"] = tkinter.Scrollbar(nav_frame_r)
        nav_frame_r_widget_dict["scrollbar"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        nav_frame_r_widget_dict["canvas"] = tkinter.Canvas(nav_frame_r, yscrollcommand=nav_frame_r_widget_dict["scrollbar"].set)  # 创建画布
        nav_frame_r_widget_dict["canvas"].place(x=0, y=0, width=self.nav_frame_r_width - 25, height=self.height - 50)
        nav_frame_r_widget_dict["scrollbar"].config(command=nav_frame_r_widget_dict["canvas"].yview)
        nav_frame_r_widget_dict["frame"] = tkinter.Frame(nav_frame_r_widget_dict["canvas"])
        nav_frame_r_widget_dict["frame"].pack()
        nav_frame_r_widget_dict["canvas"].create_window((0, 0), window=nav_frame_r_widget_dict["frame"], anchor='nw')
        # ★在canvas - frame滚动框内添加创建资源控件
        create_obj = CreateResourceInFrame(self, nav_frame_r_widget_dict, self.global_info, resource_type)
        create_obj.show()
        # ★创建“保存”按钮
        save_obj = SaveResourceInMainWindow(self, create_obj.resource_info_dict, self.global_info, resource_type)
        button_save = tkinter.Button(nav_frame_r, text="保存", command=save_obj.save)
        button_save.place(x=10, y=self.height - 40, width=50, height=25)
        # ★创建“取消”按钮
        button_cancel = tkinter.Button(nav_frame_r, text="取消",
                                       command=lambda: self.nav_frame_r_resource_top_page_display(resource_type))  # 返回资源选项卡主界面
        button_cancel.place(x=110, y=self.height - 40, width=50, height=25)

    def list_resource_of_nav_frame_r_page(self, resource_type):
        """
        ★★★★★ 列出资源-页面 ★★★★★
        :return:
        """
        # 更新导航框架2
        nav_frame_r = self.window_obj.winfo_children()[2]
        nav_frame_r.__setitem__("bg", "green")
        nav_frame_r_widget_dict = {}
        # 在框架2中添加canvas-frame滚动框
        self.clear_tkinter_frame(nav_frame_r)
        nav_frame_r_widget_dict["scrollbar"] = tkinter.Scrollbar(nav_frame_r)
        nav_frame_r_widget_dict["scrollbar"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        nav_frame_r_widget_dict["canvas"] = tkinter.Canvas(nav_frame_r, yscrollcommand=nav_frame_r_widget_dict["scrollbar"].set)
        nav_frame_r_widget_dict["canvas"].place(x=0, y=0, width=self.nav_frame_r_width - 25, height=self.height - 50)
        nav_frame_r_widget_dict["scrollbar"].config(command=nav_frame_r_widget_dict["canvas"].yview)
        nav_frame_r_widget_dict["frame"] = tkinter.Frame(nav_frame_r_widget_dict["canvas"])
        nav_frame_r_widget_dict["frame"].pack(fill=tkinter.X, expand=tkinter.TRUE)
        nav_frame_r_widget_dict["canvas"].create_window((0, 0), window=nav_frame_r_widget_dict["frame"], anchor='nw')
        # 在canvas-frame滚动框内添加资源列表控件
        list_obj = ListResourceInFrame(self, nav_frame_r_widget_dict, self.global_info, resource_type)
        list_obj.show()
        # ★创建“返回”按钮
        button_cancel = tkinter.Button(nav_frame_r, text="返回",
                                       command=lambda: self.nav_frame_r_resource_top_page_display(resource_type))  # 返回资源选项卡主界面
        button_cancel.place(x=10, y=self.height - 40, width=50, height=25)

    def nav_frame_r_resource_top_page_display(self, resource_type):
        """
        ★★★★★ 资源选项卡-主页面 ★★★★★
        :return:
        """
        # claer_tkinter_window(self.window_obj)
        # 更新导航框架1的当前选项卡背景色
        widget_index = 0
        for widget in self.nav_frame_l.winfo_children():
            if widget_index == resource_type:
                widget.config(bg="pink")
            else:
                widget.config(bg="white")
            widget_index += 1
        # 更新导航框架2
        nav_frame_r = self.window_obj.winfo_children()[2]
        nav_frame_r.__setitem__("bg", "gray")
        # 在框架2中添加功能控件
        self.clear_tkinter_frame(nav_frame_r)
        if resource_type == RESOURCE_TYPE_PROJECT:
            text_create = "创建项目"
            text_display = "列出项目"
        elif resource_type == RESOURCE_TYPE_CREDENTIAL:
            text_create = "创建凭据"
            text_display = "列出凭据"
        elif resource_type == RESOURCE_TYPE_HOST:
            text_create = "创建主机"
            text_display = "列出主机"
        elif resource_type == RESOURCE_TYPE_HOST_GROUP:
            text_create = "创建主机组"
            text_display = "列出主机组"
        elif resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
            text_create = "创建巡检代码块"
            text_display = "列出巡检代码块"
        elif resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
            text_create = "创建巡检模板"
            text_display = "列出巡检模板"
        else:
            print("unknown resource type")
            text_create = "创建项目"
            text_display = "列出项目"
        button_create_project = tkinter.Button(nav_frame_r, text=text_create,
                                               command=lambda: self.create_resource_of_nav_frame_r_page(resource_type))
        button_create_project.grid(row=0, column=1)
        button_display_project = tkinter.Button(nav_frame_r, text=text_display,
                                                command=lambda: self.list_resource_of_nav_frame_r_page(resource_type))
        button_display_project.grid(row=1, column=1)

    def show(self):
        self.window_obj.title(self.title)  # 设置窗口标题
        # self.window_obj.iconbitmap(bitmap="D:\\test.ico")  # 设置窗口图标，默认为羽毛图标
        self.window_obj.geometry(self.win_pos)  # 设置窗口大小及位置，居中
        self.window_obj.resizable(width=self.resizable, height=self.resizable)  # True 表示宽度和高度可由用户手动调整
        self.window_obj.minsize(*self.minsize)  # 可调整的最小宽度及高度
        self.window_obj.maxsize(*self.maxsize)  # 可调整的最大宽度及高度
        self.window_obj.pack_propagate(True)  # True表示窗口内的控件大小自适应
        self.window_obj.configure(bg=self.background)  # 设置背景色，RGB
        # 加载初始化界面控件
        self.load_main_window_init_widget()  # ★★★ 接下来，所有的事情都在此界面操作 ★★★
        # 监听窗口大小变化事件，自动更新窗口内控件大小（未完善，暂时不搞这个）
        self.window_obj.bind('<Configure>', self.reload_current_resized_window)
        # 运行窗口主循环
        self.window_obj.mainloop()


class CreateResourceInFrame:
    """
    在主窗口的创建资源界面，添加用于输入资源信息的控件
    """

    def __init__(self, main_window=None, nav_frame_r_widget_dict=None, global_info=None, resource_type=RESOURCE_TYPE_PROJECT):
        self.main_window = main_window
        self.nav_frame_r_widget_dict = nav_frame_r_widget_dict
        self.global_info = global_info
        self.resource_type = resource_type
        self.resource_info_dict = {}  # 用于存储资源对象信息的diction
        self.padx = 2
        self.pady = 2

    def proces_mouse_scroll(self, event):
        if event.delta > 0:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def update_frame(self):
        # 更新Frame的尺寸
        self.nav_frame_r_widget_dict["frame"].update_idletasks()
        self.nav_frame_r_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.nav_frame_r_widget_dict["frame"].winfo_width(),
                          self.nav_frame_r_widget_dict["frame"].winfo_height()))
        self.nav_frame_r_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll)
        # 滚动条移到最开头
        self.nav_frame_r_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def show(self):
        for widget in self.nav_frame_r_widget_dict["frame"].winfo_children():
            widget.destroy()
        if self.resource_type == RESOURCE_TYPE_PROJECT:
            self.create_project()
        elif self.resource_type == RESOURCE_TYPE_CREDENTIAL:
            self.create_credential()
        elif self.resource_type == RESOURCE_TYPE_HOST:
            self.create_host()
        elif self.resource_type == RESOURCE_TYPE_HOST_GROUP:
            self.create_host_group()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
            self.create_inspection_code_block()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
            self.create_inspection_template()
        else:
            print("<class CreateResourceInFrame> resource_type is Unknown")
        self.update_frame()  # 更新Frame的尺寸，并将滚动条移到最开头

    def create_project(self):
        # ★创建-project
        label_create_project = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 创建项目 ★★")
        label_create_project.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_create_project.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★project-名称
        label_project_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目名称")
        label_project_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_project_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_project_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_project_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_project_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★project-描述
        label_project_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_project_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_project_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_project_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_description"])
        entry_project_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_project_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)

    def create_credential(self):
        # ★创建-credential
        label_create_credential = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 创建凭据 ★★")
        label_create_credential.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_create_credential.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★credential-名称
        label_credential_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="凭据名称")
        label_credential_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_credential_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_credential_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★credential-描述
        label_credential_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_credential_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_credential_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                     textvariable=self.resource_info_dict["sv_description"])
        entry_credential_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★credential-所属项目
        label_credential_project = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_credential_project.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★credential-凭据类型
        label_credential_type = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="凭据类型")
        label_credential_type.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_type.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        cred_type_name_list = ["ssh_password", "ssh_key", "telnet", "ftp", "registry", "git"]
        self.resource_info_dict["combobox_cred_type"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=cred_type_name_list,
                                                                     state="readonly")
        self.resource_info_dict["combobox_cred_type"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★credential-用户名
        label_credential_username = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="username")
        label_credential_username.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_username.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_username"] = tkinter.StringVar()
        entry_credential_username = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_username"])
        entry_credential_username.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_username.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★credential-密码
        label_credential_password = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="password")
        label_credential_password.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_password.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_password"] = tkinter.StringVar()
        entry_credential_password = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_password"])
        entry_credential_password.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_password.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★credential-密钥
        label_credential_private_key = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="ssh_private_key")
        label_credential_private_key.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_private_key.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["text_private_key"] = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"], height=3, width=32)
        self.resource_info_dict["text_private_key"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权类型
        label_credential_privilege_escalation_method = tkinter.Label(self.nav_frame_r_widget_dict["frame"],
                                                                     text="privilege_escalation_method")
        label_credential_privilege_escalation_method.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_privilege_escalation_method.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        privilege_escalation_method_list = ["su", "sudo"]
        self.resource_info_dict["combobox_privilege_escalation_method"] = \
            ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=privilege_escalation_method_list, state="readonly")
        self.resource_info_dict["combobox_privilege_escalation_method"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权用户
        label_credential_privilege_escalation_username = tkinter.Label(self.nav_frame_r_widget_dict["frame"],
                                                                       text="privilege_escalation_username")
        label_credential_privilege_escalation_username.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_privilege_escalation_username.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_privilege_escalation_username"] = tkinter.StringVar()
        entry_credential_privilege_escalation_username = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                                       textvariable=self.resource_info_dict[
                                                                           "sv_privilege_escalation_username"])
        entry_credential_privilege_escalation_username.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_privilege_escalation_username.grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权密码
        label_credential_privilege_escalation_password = tkinter.Label(self.nav_frame_r_widget_dict["frame"],
                                                                       text="privilege_escalation_password")
        label_credential_privilege_escalation_password.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_privilege_escalation_password.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_privilege_escalation_password"] = tkinter.StringVar()
        entry_credential_privilege_escalation_password = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                                       textvariable=self.resource_info_dict[
                                                                           "sv_privilege_escalation_password"])
        entry_credential_privilege_escalation_password.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_privilege_escalation_password.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★credential-auth_url
        label_credential_auth_url = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="auth_url")
        label_credential_auth_url.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_auth_url.grid(row=11, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_auth_url"] = tkinter.StringVar()
        entry_credential_auth_url = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_auth_url"])
        entry_credential_auth_url.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_auth_url.grid(row=11, column=1, padx=self.padx, pady=self.pady)
        # ★credential-ssl_verify
        label_credential_ssl_verify = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="ssl_verify")
        label_credential_ssl_verify.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_ssl_verify.grid(row=12, column=0, padx=self.padx, pady=self.pady)
        ssl_verify_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_ssl_verify"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=ssl_verify_name_list,
                                                                      state="readonly")
        self.resource_info_dict["combobox_ssl_verify"].grid(row=12, column=1, padx=self.padx, pady=self.pady)

    def create_host(self):
        # ★创建-host
        label_create_host = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 创建主机 ★★")
        label_create_host.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_create_host.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★host-名称
        label_host_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机名称")
        label_host_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_host_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_host_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★host-描述
        label_host_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_host_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_host_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                               textvariable=self.resource_info_dict["sv_description"])
        entry_host_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★host-所属项目
        label_host_project = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_host_project.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★host-address
        label_host_address = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="address")
        label_host_address.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_address.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_address"] = tkinter.StringVar()
        entry_host_address = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                           textvariable=self.resource_info_dict["sv_address"])
        entry_host_address.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_address.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★host-ssh_port
        label_host_ssh_port = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="ssh_port")
        label_host_ssh_port.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_ssh_port.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_ssh_port"] = tkinter.StringVar()
        entry_host_ssh_port = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                            textvariable=self.resource_info_dict["sv_ssh_port"])
        entry_host_ssh_port.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_ssh_port.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★host-telnet_port
        label_host_telnet_port = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="telnet_port")
        label_host_telnet_port.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_telnet_port.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_telnet_port"] = tkinter.StringVar()
        entry_host_telnet_port = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                               textvariable=self.resource_info_dict["sv_telnet_port"])
        entry_host_telnet_port.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_telnet_port.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★host-login_protocol
        label_host_login_protocol = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="远程登录类型")
        label_host_login_protocol.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_login_protocol.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        login_protocol_name_list = ["ssh", "telnet"]
        self.resource_info_dict["combobox_login_protocol"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                          values=login_protocol_name_list,
                                                                          state="readonly")
        self.resource_info_dict["combobox_login_protocol"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★host-first_auth_method
        label_host_first_auth_method = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="优先认证类型")
        label_host_first_auth_method.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_first_auth_method.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        first_auth_method_name_list = ["priKey", "password"]
        self.resource_info_dict["combobox_first_auth_method"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                             values=first_auth_method_name_list,
                                                                             state="readonly")
        self.resource_info_dict["combobox_first_auth_method"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★host-凭据列表
        label_credential_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="凭据列表")
        label_credential_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_list.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_credential"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                        yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                        selectforeground='black', exportselection=False,
                                                                        selectborderwidth=2, activestyle='dotbox', height=6)
        for cred in self.global_info.credential_obj_list:
            self.resource_info_dict["listbox_credential"].insert(tkinter.END, cred.name)  # 添加item选项
        self.resource_info_dict["listbox_credential"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_credential"].yview)
        frame.grid(row=9, column=1, padx=self.padx, pady=self.pady)

    def create_host_group(self):
        # ★创建-host_group
        label_create_host_group = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 创建主机组 ★★")
        label_create_host_group.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_create_host_group.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★host_group-名称
        label_host_group_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机组名称")
        label_host_group_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_host_group_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_host_group_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_group_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-描述
        label_host_group_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_host_group_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_host_group_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                     textvariable=self.resource_info_dict["sv_description"])
        entry_host_group_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_group_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-所属项目
        label_host_group_project = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_host_group_project.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★添加host_group列表
        label_host_group_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机组列表")
        label_host_group_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_list.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_host_group"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                        yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                        selectforeground='black', exportselection=False,
                                                                        selectborderwidth=2, activestyle='dotbox', height=6)
        for host_group in self.global_info.host_group_obj_list:
            self.resource_info_dict["listbox_host_group"].insert(tkinter.END, host_group.name)  # 添加item选项
        self.resource_info_dict["listbox_host_group"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_host_group"].yview)
        frame.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★添加host列表
        label_host_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机列表")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_list.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_host"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                  yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                  selectforeground='black', exportselection=False,
                                                                  selectborderwidth=2, activestyle='dotbox', height=6)
        for host in self.global_info.host_obj_list:
            self.resource_info_dict["listbox_host"].insert(tkinter.END, host.name)  # 添加item选项
        self.resource_info_dict["listbox_host"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_host"].yview)
        frame.grid(row=5, column=1, padx=self.padx, pady=self.pady)

    def create_inspection_code_block(self):
        # ★创建-inspection_code_block
        label_create_inspection_code_block = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 创建巡检代码块 ★★")
        label_create_inspection_code_block.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_create_inspection_code_block.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-名称
        label_inspection_code_block_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检代码块名称")
        label_inspection_code_block_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_code_block_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_code_block_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                         textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_code_block_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_code_block_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-描述
        label_inspection_code_block_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_inspection_code_block_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_code_block_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_code_block_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                                textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_code_block_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_code_block_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-所属项目
        label_inspection_code_block_project = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_inspection_code_block_project.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_code_block_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★添加巡检代码内容
        label_inspection_code_block_code_content = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检代码内容")
        label_inspection_code_block_code_content.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["text_code_content"] = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"], width=40, height=12)
        self.resource_info_dict["text_code_content"].grid(row=4, column=1, padx=self.padx, pady=self.pady)

    def create_inspection_template(self):
        # ★创建-inspection_template
        label_create_inspection_template = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 创建巡检模板 ★★")
        label_create_inspection_template.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_create_inspection_template.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_template-名称
        label_inspection_template_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检模板名称")
        label_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_template_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                       textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_template_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-描述
        label_inspection_template_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_template_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                              textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_template_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-所属项目
        label_inspection_template_project = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_inspection_template_project.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_method
        label_inspection_template_execution_method = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="execution_method")
        label_inspection_template_execution_method.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_execution_method.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        execution_method_name_list = ["无", "定时执行", "周期执行", "After"]
        self.resource_info_dict["combobox_execution_method"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                            values=execution_method_name_list,
                                                                            state="readonly")
        self.resource_info_dict["combobox_execution_method"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-update_code_on_launch
        label_inspection_template_update_code_on_launch = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="运行前更新code")
        label_inspection_template_update_code_on_launch.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_update_code_on_launch.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        update_code_on_launch_name_list = ["Yes", "No"]
        self.resource_info_dict["combobox_update_code_on_launch"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                                 values=update_code_on_launch_name_list,
                                                                                 state="readonly")
        self.resource_info_dict["combobox_update_code_on_launch"].grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-forks
        label_inspection_template_forks = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="运行线程数")
        label_inspection_template_forks.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_forks.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_forks"] = tkinter.StringVar()
        spinbox_inspection_template_forks = tkinter.Spinbox(self.nav_frame_r_widget_dict["frame"], from_=1, to=256, increment=1,
                                                            textvariable=self.resource_info_dict["sv_forks"])
        spinbox_inspection_template_forks.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-save_output_to_file
        label_inspection_template_save_output_to_file = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="自动保存巡检日志到文件")
        label_inspection_template_save_output_to_file.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_save_output_to_file.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        save_output_to_file_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_save_output_to_file"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                               values=save_output_to_file_name_list,
                                                                               state="readonly")
        self.resource_info_dict["combobox_save_output_to_file"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-output_file_name_style
        label_inspection_template_output_file_name_style = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检日志文件名称")
        label_inspection_template_output_file_name_style.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_output_file_name_style.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        output_file_name_style_name_list = ["HOSTNAME", "HOSTNAME-DATE", "HOSTNAME-DATE-TIME", "DATE_DIR/HOSTNAME",
                                            "DATE_DIR/HOSTNAME-DATE",
                                            "DATE_DIR/HOSTNAME-DATE-TIME"]
        self.resource_info_dict["combobox_output_file_name_style"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                                  values=output_file_name_style_name_list,
                                                                                  state="readonly", width=32)
        self.resource_info_dict["combobox_output_file_name_style"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★添加host_group列表
        label_host_group_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机组列表")
        label_host_group_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_list.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_host_group"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                        yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                        selectforeground='black', exportselection=False,
                                                                        selectborderwidth=2, activestyle='dotbox', height=6)
        for host_group in self.global_info.host_group_obj_list:
            self.resource_info_dict["listbox_host_group"].insert(tkinter.END, host_group.name)  # 添加item选项
        self.resource_info_dict["listbox_host_group"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_host_group"].yview)
        frame.grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★添加host列表
        label_host_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机列表")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_list.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_host"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                  yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                  selectforeground='black', exportselection=False,
                                                                  selectborderwidth=2, activestyle='dotbox', height=6)
        for host in self.global_info.host_obj_list:
            self.resource_info_dict["listbox_host"].insert(tkinter.END, host.name)  # 添加item选项
        self.resource_info_dict["listbox_host"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_host"].yview)
        frame.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★添加-巡检代码块列表
        label_inspection_code_block_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检代码块列表")
        label_inspection_code_block_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_code_block_list.grid(row=11, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_inspection_code_block"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2,
                                                                                   cursor="arrow",
                                                                                   yscrollcommand=list_scrollbar.set,
                                                                                   selectbackground='pink',
                                                                                   selectforeground='black', exportselection=False,
                                                                                   selectborderwidth=2, activestyle='dotbox', height=6)
        for cred in self.global_info.inspection_code_block_obj_list:
            self.resource_info_dict["listbox_inspection_code_block"].insert(tkinter.END, cred.name)  # 添加item选项
        self.resource_info_dict["listbox_inspection_code_block"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_inspection_code_block"].yview)
        frame.grid(row=11, column=1, padx=self.padx, pady=self.pady)


class ListResourceInFrame:
    """
    在主窗口的查看资源界面，添加用于显示资源信息的控件
    """

    def __init__(self, main_window=None, nav_frame_r_widget_dict=None, global_info=None, resource_type=RESOURCE_TYPE_PROJECT):
        self.main_window = main_window
        self.nav_frame_r_widget_dict = nav_frame_r_widget_dict
        self.global_info = global_info
        self.resource_type = resource_type
        self.padx = 2
        self.pady = 2

    def proces_mouse_scroll(self, event):
        if event.delta > 0:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def show(self):  # 入口函数
        for widget in self.nav_frame_r_widget_dict["frame"].winfo_children():
            widget.destroy()
        if self.resource_type == RESOURCE_TYPE_PROJECT:
            resource_display_frame_title = "★★ 项目列表 ★★"
            resource_obj_list = self.global_info.project_obj_list
        elif self.resource_type == RESOURCE_TYPE_CREDENTIAL:
            resource_display_frame_title = "★★ 凭据列表 ★★"
            resource_obj_list = self.global_info.credential_obj_list
        elif self.resource_type == RESOURCE_TYPE_HOST:
            resource_display_frame_title = "★★ 主机列表 ★★"
            resource_obj_list = self.global_info.host_obj_list
        elif self.resource_type == RESOURCE_TYPE_HOST_GROUP:
            resource_display_frame_title = "★★ 主机组列表 ★★"
            resource_obj_list = self.global_info.host_group_obj_list
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
            resource_display_frame_title = "★★ 巡检代码块列表 ★★"
            resource_obj_list = self.global_info.inspection_code_block_obj_list
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
            resource_display_frame_title = "★★ 巡检模板列表 ★★"
            resource_obj_list = self.global_info.inspection_template_obj_list
        else:
            print("unknown resource type")
            resource_display_frame_title = "★★ 项目列表 ★★"
            resource_obj_list = self.global_info.project_obj_list
        # 列出资源
        label_display_resource = tkinter.Label(self.nav_frame_r_widget_dict["frame"],
                                               text=resource_display_frame_title + "    数量: " + str(len(resource_obj_list)))
        label_display_resource.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        index = 0
        for obj in resource_obj_list:
            print(obj.name)
            label_index = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text=str(index + 1) + " : ")
            label_index.bind("<MouseWheel>", self.proces_mouse_scroll)
            label_index.grid(row=index + 1, column=0, padx=self.padx, pady=self.pady)
            label_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text=obj.name)
            label_name.bind("<MouseWheel>", self.proces_mouse_scroll)
            label_name.grid(row=index + 1, column=1, padx=self.padx, pady=self.pady)
            # 查看对象信息
            view_obj = ViewResourceInFrame(self.main_window, self.nav_frame_r_widget_dict, self.global_info, obj,
                                           self.resource_type)
            button_view = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="查看", command=view_obj.show)
            button_view.bind("<MouseWheel>", self.proces_mouse_scroll)
            button_view.grid(row=index + 1, column=2, padx=self.padx, pady=self.pady)
            # 编辑对象信息
            edit_obj = EditResourceInFrame(self.main_window, self.nav_frame_r_widget_dict, self.global_info, obj,
                                           self.resource_type)
            button_edit = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="编辑", command=edit_obj.show)
            button_edit.bind("<MouseWheel>", self.proces_mouse_scroll)
            button_edit.grid(row=index + 1, column=3, padx=self.padx, pady=self.pady)
            # 删除对象
            delete_obj = DeleteResourceInFrame(self.main_window, self.nav_frame_r_widget_dict, self.global_info, obj,
                                               self.resource_type)
            button_delete = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="删除", command=delete_obj.show)
            button_delete.bind("<MouseWheel>", self.proces_mouse_scroll)
            button_delete.grid(row=index + 1, column=4, padx=self.padx, pady=self.pady)
            # ★巡检模板-start
            if self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
                start_obj = StartInspectionTemplateInFrame(self.main_window, self.nav_frame_r_widget_dict, self.global_info, obj)
                button_start = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="Start", command=start_obj.start)
                button_start.bind("<MouseWheel>", self.proces_mouse_scroll)
                button_start.grid(row=index + 1, column=5, padx=self.padx, pady=self.pady)
            index += 1
        # 信息控件添加完毕
        self.nav_frame_r_widget_dict["frame"].update_idletasks()  # 更新Frame的尺寸
        self.nav_frame_r_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.nav_frame_r_widget_dict["frame"].winfo_width(), self.nav_frame_r_widget_dict["frame"].winfo_height()))
        self.nav_frame_r_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll)


class ViewResourceInFrame:
    """
    在主窗口的查看资源界面，添加用于显示资源信息的控件
    """

    def __init__(self, main_window=None, nav_frame_r_widget_dict=None, global_info=None, resource_obj=None,
                 resource_type=RESOURCE_TYPE_PROJECT):
        self.main_window = main_window
        self.nav_frame_r_widget_dict = nav_frame_r_widget_dict
        self.global_info = global_info
        self.resource_obj = resource_obj
        self.resource_type = resource_type
        self.view_width = 20

    def show(self):  # 入口函数
        for widget in self.nav_frame_r_widget_dict["frame"].winfo_children():
            widget.destroy()
        if self.resource_type == RESOURCE_TYPE_PROJECT:
            self.view_project()
        elif self.resource_type == RESOURCE_TYPE_CREDENTIAL:
            self.view_credential()
        elif self.resource_type == RESOURCE_TYPE_HOST:
            self.view_host()
        elif self.resource_type == RESOURCE_TYPE_HOST_GROUP:
            self.view_host_group()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
            self.view_inspection_code_block()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
            self.view_inspection_template()
        else:
            print("<class ViewResourceInFrame> resource_type is Unknown")
        self.update_frame()  # 更新Frame的尺寸，并将滚动条移到最开头

    def proces_mouse_scroll(self, event):
        if event.delta > 0:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def update_frame(self):
        # 更新Frame的尺寸
        self.nav_frame_r_widget_dict["frame"].update_idletasks()
        self.nav_frame_r_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.nav_frame_r_widget_dict["frame"].winfo_width(),
                          self.nav_frame_r_widget_dict["frame"].winfo_height()))
        self.nav_frame_r_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll)
        # 滚动条移到最开头
        self.nav_frame_r_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def view_project(self):
        # ★查看-project
        print("查看项目")
        print(self.resource_obj)
        obj_info_text = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息，需要绑定滚动条
        obj_info_text.insert(tkinter.END, "★★ 查看项目 ★★\n")
        # ★project-名称
        project_name = "名称".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.name + "\n"
        print(project_name)
        obj_info_text.insert(tkinter.END, project_name)
        # ★project-描述
        project_description = "描述".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.description + "\n"
        obj_info_text.insert(tkinter.END, project_description)
        # ★credential-create_timestamp
        credential_create_timestamp = "create_time".ljust(self.view_width, " ") + ": " \
                                      + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.resource_obj.create_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, credential_create_timestamp)
        # ★credential-last_modify_timestamp
        if abs(self.resource_obj.last_modify_timestamp) < 1:
            last_modify_timestamp = self.resource_obj.create_timestamp
        else:
            last_modify_timestamp = self.resource_obj.last_modify_timestamp
        credential_last_modify_timestamp = "last_modify_time".ljust(self.view_width, " ") + ": " \
                                           + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modify_timestamp)) + "\n"
        print(last_modify_timestamp)
        obj_info_text.insert(tkinter.END, credential_last_modify_timestamp)
        # 显示info Text文本框
        obj_info_text.pack()
        # ★★添加返回“项目列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="返回项目列表",
                                       command=lambda: self.main_window.list_resource_of_nav_frame_r_page(
                                           RESOURCE_TYPE_PROJECT))  # 返回“项目列表”
        button_return.pack()

    def view_credential(self):
        # 查看-credential
        obj_info_text = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息
        obj_info_text.insert(tkinter.END, "★★ 查看凭据 ★★\n")
        # ★credential-名称
        credential_name = "名称".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.name + "\n"
        obj_info_text.insert(tkinter.END, credential_name)
        # ★credential-id
        credential_oid = "凭据id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.oid + "\n"
        obj_info_text.insert(tkinter.END, credential_oid)
        # ★credential-描述
        credential_description = "描述".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.description + "\n"
        obj_info_text.insert(tkinter.END, credential_description)
        # ★credential-所属项目+项目id
        if self.global_info.get_project_by_oid(self.resource_obj.project_oid) is None:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            project_name = "Unknown!"
        else:
            project_name = self.global_info.get_project_by_oid(self.resource_obj.project_oid).name
        credential_project_name = "所属项目".ljust(self.view_width - 4, " ") + ": " + project_name + "\n"
        obj_info_text.insert(tkinter.END, credential_project_name)
        credential_project_oid = "项目id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.project_oid + "\n"
        obj_info_text.insert(tkinter.END, credential_project_oid)
        # ★credential-cred_type
        cred_type_name_list = ["ssh_password", "ssh_key", "telnet", "ftp", "registry", "git"]
        credential_cred_type = "凭据类型".ljust(self.view_width - 4, " ") + ": " + cred_type_name_list[self.resource_obj.cred_type] + "\n"
        obj_info_text.insert(tkinter.END, credential_cred_type)
        # ★credential-username
        credential_username = "username".ljust(self.view_width, " ") + ": " + self.resource_obj.username + "\n"
        obj_info_text.insert(tkinter.END, credential_username)
        # ★credential-password
        credential_password = "password".ljust(self.view_width, " ") + ": " + self.resource_obj.password + "\n"
        obj_info_text.insert(tkinter.END, credential_password)
        # ★credential-private_key
        credential_private_key = "private_key".ljust(self.view_width, " ") + ": " + self.resource_obj.private_key + "\n"
        obj_info_text.insert(tkinter.END, credential_private_key)
        # ★credential-privilege_escalation_method
        privilege_escalation_method_list = ["su", "sudo"]
        credential_privilege_escalation_method = "提权_method".ljust(self.view_width - 2, " ") + ": " + privilege_escalation_method_list[
            self.resource_obj.privilege_escalation_method] + "\n"
        obj_info_text.insert(tkinter.END, credential_privilege_escalation_method)
        # ★credential-privilege_escalation_username
        credential_privilege_escalation_username = "提权_username".ljust(self.view_width - 2, " ") \
                                                   + ": " + self.resource_obj.privilege_escalation_username + "\n"
        obj_info_text.insert(tkinter.END, credential_privilege_escalation_username)
        # ★credential-privilege_escalation_password
        credential_privilege_escalation_password = "提权_password".ljust(self.view_width - 2, " ") \
                                                   + ": " + self.resource_obj.privilege_escalation_password + "\n"
        obj_info_text.insert(tkinter.END, credential_privilege_escalation_password)
        # ★credential-auth_url
        credential_auth_url = "auth_url".ljust(self.view_width, " ") + ": " + self.resource_obj.auth_url + "\n"
        obj_info_text.insert(tkinter.END, credential_auth_url)
        # ★credential-ssl_verify
        ssl_verify_list = ["NO", "YES"]
        credential_ssl_verify = "ssl_verify".ljust(self.view_width, " ") + ": " + ssl_verify_list[self.resource_obj.ssl_verify] + "\n"
        obj_info_text.insert(tkinter.END, credential_ssl_verify)
        # ★credential-create_timestamp
        credential_create_timestamp = "create_time".ljust(self.view_width, " ") + ": " \
                                      + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.resource_obj.create_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, credential_create_timestamp)
        # ★credential-last_modify_timestamp
        if self.resource_obj.last_modify_timestamp < 1:
            last_modify_timestamp = self.resource_obj.create_timestamp
        else:
            last_modify_timestamp = self.resource_obj.last_modify_timestamp
        credential_last_modify_timestamp = "last_modify_time".ljust(self.view_width, " ") + ": " \
                                           + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modify_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, credential_last_modify_timestamp)
        # 显示info Text文本框
        obj_info_text.pack()
        # ★★添加“返回项目列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="返回项目列表",
                                       command=lambda: self.main_window.list_resource_of_nav_frame_r_page(
                                           RESOURCE_TYPE_CREDENTIAL))  # 返回凭据列表
        button_return.pack()

    def view_host(self):
        # 查看-host
        obj_info_text = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息
        obj_info_text.insert(tkinter.END, "★★ 查看主机 ★★\n")
        # ★host-名称
        host_name = "名称".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.name + "\n"
        obj_info_text.insert(tkinter.END, host_name)
        # ★host-id
        host_oid = "主机id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.oid + "\n"
        obj_info_text.insert(tkinter.END, host_oid)
        # ★host-描述
        host_description = "描述".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.description + "\n"
        obj_info_text.insert(tkinter.END, host_description)
        # ★host-所属项目+项目id
        if self.global_info.get_project_by_oid(self.resource_obj.project_oid) is None:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            project_name = "Unknown!"
        else:
            project_name = self.global_info.get_project_by_oid(self.resource_obj.project_oid).name
        host_project_name = "所属项目".ljust(self.view_width - 4, " ") + ": " + project_name + "\n"
        obj_info_text.insert(tkinter.END, host_project_name)
        host_project_oid = "项目id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.project_oid + "\n"
        obj_info_text.insert(tkinter.END, host_project_oid)
        # ★host-address
        host_address = "address".ljust(self.view_width, " ") + ": " + self.resource_obj.address + "\n"
        obj_info_text.insert(tkinter.END, host_address)
        # ★host-login_protocol
        login_protocol_name_list = ["ssh", "telnet"]
        host_login_protocol = "远程登录类型".ljust(self.view_width - 6, " ") + ": " + login_protocol_name_list[
            self.resource_obj.login_protocol] + "\n"
        obj_info_text.insert(tkinter.END, host_login_protocol)
        # ★host-first_auth_method
        first_auth_method_name_list = ["priKey", "password"]
        host_first_auth_method = "优先认证类型".ljust(self.view_width - 6, " ") + ": " + first_auth_method_name_list[
            self.resource_obj.first_auth_method] + "\n"
        obj_info_text.insert(tkinter.END, host_first_auth_method)
        # ★host-ssh_port
        host_ssh_port = "ssh_port".ljust(self.view_width, " ") + ": " + str(self.resource_obj.ssh_port) + "\n"
        obj_info_text.insert(tkinter.END, host_ssh_port)
        # ★host-telnet_port
        host_telnet_port = "ssh_port".ljust(self.view_width, " ") + ": " + str(self.resource_obj.telnet_port) + "\n"
        obj_info_text.insert(tkinter.END, host_telnet_port)
        # ★host-create_timestamp
        host_create_timestamp = "create_time".ljust(self.view_width, " ") + ": " \
                                + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.resource_obj.create_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, host_create_timestamp)
        # ★host-last_modify_timestamp
        if self.resource_obj.last_modify_timestamp < 1:
            last_modify_timestamp = self.resource_obj.create_timestamp
        else:
            last_modify_timestamp = self.resource_obj.last_modify_timestamp
        host_last_modify_timestamp = "last_modify_time".ljust(self.view_width, " ") + ": " \
                                     + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modify_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, host_last_modify_timestamp)
        # ★host-凭据列表
        obj_info_text.insert(tkinter.END, "\n" + "凭据列表".ljust(self.view_width - 4, " ") + ": " + "\n")
        for cred_oid in self.resource_obj.credential_oid_list:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            cred_obj = self.global_info.get_credential_by_oid(cred_oid)
            if cred_obj is not None:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + cred_obj.name + "\n")
            else:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + cred_oid + " Unknown!\n")
        # 显示info Text文本框
        obj_info_text.pack()
        # ★★添加“返回主机列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="返回主机列表",
                                       command=lambda: self.main_window.list_resource_of_nav_frame_r_page(
                                           RESOURCE_TYPE_HOST))  # 返回主机列表
        button_return.pack()

    def view_host_group(self):
        # 查看-host_group
        obj_info_text = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息
        obj_info_text.insert(tkinter.END, "★★ 查看主机组 ★★\n")
        # ★host_group-名称
        host_group_name = "名称".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.name + "\n"
        obj_info_text.insert(tkinter.END, host_group_name)
        # ★host_group-id
        host_group_oid = "主机组id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.oid + "\n"
        obj_info_text.insert(tkinter.END, host_group_oid)
        # ★host_group-描述
        host_group_description = "描述".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.description + "\n"
        obj_info_text.insert(tkinter.END, host_group_description)
        # ★host_group-所属项目+项目id
        if self.global_info.get_project_by_oid(self.resource_obj.project_oid) is None:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            project_name = "Unknown!"
        else:
            project_name = self.global_info.get_project_by_oid(self.resource_obj.project_oid).name
        host_group_project_name = "所属项目".ljust(self.view_width - 4, " ") + ": " + project_name + "\n"
        obj_info_text.insert(tkinter.END, host_group_project_name)
        host_group_project_oid = "项目id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.project_oid + "\n"
        obj_info_text.insert(tkinter.END, host_group_project_oid)
        # ★host_group-create_timestamp
        host_group_create_timestamp = "create_time".ljust(self.view_width, " ") + ": " \
                                      + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.resource_obj.create_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, host_group_create_timestamp)
        # ★host_group-last_modify_timestamp
        if self.resource_obj.last_modify_timestamp < 1:
            last_modify_timestamp = self.resource_obj.create_timestamp
        else:
            last_modify_timestamp = self.resource_obj.last_modify_timestamp
        host_group_last_modify_timestamp = "last_modify_time".ljust(self.view_width, " ") + ": " \
                                           + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modify_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, host_group_last_modify_timestamp)
        # ★host_group-列表
        obj_info_text.insert(tkinter.END, "\n" + "主机组列表".ljust(self.view_width - 5, " ") + ": " + "\n")
        for host_group_oid in self.resource_obj.host_group_oid_list:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            host_group_obj = self.global_info.get_host_group_by_oid(host_group_oid)
            if host_group_obj is not None:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + host_group_obj.name + "\n")
            else:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + host_group_oid + " Unknown!\n")
        # ★host-列表
        obj_info_text.insert(tkinter.END, "\n" + "主机列表".ljust(self.view_width - 4, " ") + ": " + "\n")
        for host_oid in self.resource_obj.host_oid_list:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            host_obj = self.global_info.get_host_by_oid(host_oid)
            if host_obj is not None:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + host_obj.name + "\n")
            else:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + host_oid + " Unknown!\n")
        # 显示info Text文本框
        obj_info_text.pack()
        # ★★添加“返回主机组列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="返回主机组列表",
                                       command=lambda: self.main_window.list_resource_of_nav_frame_r_page(
                                           RESOURCE_TYPE_HOST_GROUP))  # 返回主机组列表
        button_return.pack()

    def view_inspection_code_block(self):
        # 查看-inspection_code_block
        obj_info_text = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"], height=9)  # 创建多行文本框，用于显示资源信息
        obj_info_text.insert(tkinter.END, "★★ 查看巡检代码块 ★★\n")
        # ★inspection_code_block-名称
        inspection_code_block_name = "名称".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.name + "\n"
        obj_info_text.insert(tkinter.END, inspection_code_block_name)
        # ★inspection_code_block-id
        inspection_code_block_oid = "巡检代码块id".ljust(self.view_width - 5, " ") + ": " + self.resource_obj.oid + "\n"
        obj_info_text.insert(tkinter.END, inspection_code_block_oid)
        # ★inspection_code_block-描述
        inspection_code_block_description = "描述".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.description + "\n"
        obj_info_text.insert(tkinter.END, inspection_code_block_description)
        # ★inspection_code_block-所属项目+项目id
        if self.global_info.get_project_by_oid(self.resource_obj.project_oid) is None:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            project_name = "Unknown!"
        else:
            project_name = self.global_info.get_project_by_oid(self.resource_obj.project_oid).name
        inspection_code_block_project_name = "所属项目".ljust(self.view_width - 4, " ") + ": " + project_name + "\n"
        obj_info_text.insert(tkinter.END, inspection_code_block_project_name)
        inspection_code_block_project_oid = "项目id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.project_oid + "\n"
        obj_info_text.insert(tkinter.END, inspection_code_block_project_oid)
        # ★inspection_code_block-create_timestamp
        inspection_code_block_create_timestamp = "create_time".ljust(self.view_width, " ") + ": " \
                                                 + time.strftime("%Y-%m-%d %H:%M:%S",
                                                                 time.localtime(self.resource_obj.create_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, inspection_code_block_create_timestamp)
        # ★inspection_code_block-last_modify_timestamp
        if self.resource_obj.last_modify_timestamp < 1:
            last_modify_timestamp = self.resource_obj.create_timestamp
        else:
            last_modify_timestamp = self.resource_obj.last_modify_timestamp
        inspection_code_block_last_modify_timestamp = "last_modify_time".ljust(self.view_width, " ") + ": " \
                                                      + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modify_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, inspection_code_block_last_modify_timestamp)
        # 显示info Text文本框
        obj_info_text.pack()
        # 列出代码内容
        label_code_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检命令内容")
        label_code_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_code_list.pack()
        # list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        # list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        treeview_code_content = ttk.Treeview(self.nav_frame_r_widget_dict["frame"], cursor="arrow", height=7,
                                             columns=("index", "code_content"), show="headings")
        # 设置每一个列的宽度和对齐的方式
        treeview_code_content.column("index", width=60, anchor="w")
        treeview_code_content.column("code_content", width=320, anchor="w")
        # 设置每个列的标题
        treeview_code_content.heading("index", text="index")
        treeview_code_content.heading("code_content", text="code_content")
        # 插入数据
        index = 0
        for code_obj in self.resource_obj.code_list:
            treeview_code_content.insert("", index, values=(index, code_obj.code_content))  # 添加item选项
            index += 1
        # list_scrollbar.config(command=listbox_code_content.yview)
        treeview_code_content.pack()
        # ★★添加“返回主机组列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="返回巡检代码块列表",
                                       command=lambda: self.main_window.list_resource_of_nav_frame_r_page(
                                           RESOURCE_TYPE_INSPECTION_CODE_BLOCK))  # 返回巡检代码块列表
        button_return.pack()

    def view_inspection_template(self):
        # 查看-inspection_template
        obj_info_text = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息
        obj_info_text.insert(tkinter.END, "★★ 查看巡检模板 ★★\n")
        # ★inspection_template-名称
        inspection_template_name = "名称".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.name + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_name)
        # ★inspection_template-id
        inspection_template_oid = "巡检模板id".ljust(self.view_width - 4, " ") + ": " + self.resource_obj.oid + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_oid)
        # ★inspection_template-描述
        inspection_template_description = "描述".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.description + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_description)
        # ★inspection_template-所属项目+项目id
        if self.global_info.get_project_by_oid(self.resource_obj.project_oid) is None:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            project_name = "Unknown!"
        else:
            project_name = self.global_info.get_project_by_oid(self.resource_obj.project_oid).name
        inspection_template_project_name = "所属项目".ljust(self.view_width - 4, " ") + ": " + project_name + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_project_name)
        inspection_template_project_oid = "项目id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.project_oid + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_project_oid)
        # ★inspection_template-execution_method
        execution_method_name_list = ["无", "定时执行", "周期执行", "After"]
        inspection_template_name = "execution_method".ljust(self.view_width, " ") + ": " + execution_method_name_list[
            self.resource_obj.execution_method] + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_name)
        # ★inspection_template-update_code_on_launch
        update_code_on_launch_name_list = ["Yes", "No"]
        inspection_template_name = "运行前更新code".ljust(self.view_width - 5, " ") + ": " + update_code_on_launch_name_list[
            self.resource_obj.update_code_on_launch] + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_name)
        # ★inspection_template-forks
        inspection_template_forks = "运行线程数".ljust(self.view_width - 5, " ") + ": " + str(self.resource_obj.forks) + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_forks)
        # ★inspection_template-save_output_to_file
        save_output_to_file_name_list = ["No", "Yes"]
        inspection_template_name = "自动保存巡检日志到文件".ljust(self.view_width - 11, " ") + ": " + save_output_to_file_name_list[
            self.resource_obj.save_output_to_file] + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_name)
        # ★inspection_template-output_file_name_style
        output_file_name_style_name_list = ["HOSTNAME", "HOSTNAME-DATE", "HOSTNAME-DATE-TIME", "DATE_DIR/HOSTNAME",
                                            "DATE_DIR/HOSTNAME-DATE",
                                            "DATE_DIR/HOSTNAME-DATE-TIME"]
        inspection_template_name = "巡检日志文件名称".ljust(self.view_width - 8, " ") + ": " + output_file_name_style_name_list[
            self.resource_obj.output_file_name_style] + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_name)
        # ★inspection_template-create_timestamp
        inspection_template_create_timestamp = "create_time".ljust(self.view_width, " ") + ": " \
                                               + time.strftime("%Y-%m-%d %H:%M:%S",
                                                               time.localtime(self.resource_obj.create_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_create_timestamp)
        # ★inspection_template-last_modify_timestamp
        if self.resource_obj.last_modify_timestamp < 1:
            last_modify_timestamp = self.resource_obj.create_timestamp
        else:
            last_modify_timestamp = self.resource_obj.last_modify_timestamp
        inspection_template_last_modify_timestamp = "last_modify_time".ljust(self.view_width, " ") + ": " \
                                                    + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_modify_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, inspection_template_last_modify_timestamp)
        # ★host_group-列表
        obj_info_text.insert(tkinter.END, "\n" + "主机组列表".ljust(self.view_width - 5, " ") + ": " + "\n")
        for host_group_oid in self.resource_obj.host_group_oid_list:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            host_group_obj = self.global_info.get_host_group_by_oid(host_group_oid)
            if host_group_obj is not None:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + host_group_obj.name + "\n")
            else:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + host_group_oid + " Unknown!\n")
        # ★host-列表
        obj_info_text.insert(tkinter.END, "\n" + "主机列表".ljust(self.view_width - 4, " ") + ": " + "\n")
        for host_oid in self.resource_obj.host_oid_list:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            host_obj = self.global_info.get_host_by_oid(host_oid)
            if host_obj is not None:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + host_obj.name + "\n")
            else:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + host_oid + " Unknown!\n")
        # ★巡检代码块-列表
        obj_info_text.insert(tkinter.END, "\n" + "巡检代码块列表".ljust(self.view_width - 4, " ") + ": " + "\n")
        for inspection_code_block_oid in self.resource_obj.inspection_code_block_oid_list:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            inspection_code_block_obj = self.global_info.get_inspection_code_block_by_oid(inspection_code_block_oid)
            if inspection_code_block_obj is not None:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + inspection_code_block_obj.name + "\n")
            else:
                obj_info_text.insert(tkinter.END, "".ljust(self.view_width + 2, " ") + inspection_code_block_oid + " Unknown!\n")
        # 显示info Text文本框
        obj_info_text.pack()
        # ★★添加“返回巡检代码块列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="返回巡检代码块列表",
                                       command=lambda: self.main_window.list_resource_of_nav_frame_r_page(
                                           RESOURCE_TYPE_INSPECTION_TEMPLATE))  # 返回巡检代码块列表
        button_return.pack()


class EditResourceInFrame:
    """
    在主窗口的查看资源界面，添加用于编辑资源信息的控件
    """

    def __init__(self, main_window=None, nav_frame_r_widget_dict=None, global_info=None, resource_obj=None,
                 resource_type=RESOURCE_TYPE_PROJECT):
        self.main_window = main_window
        self.nav_frame_r_widget_dict = nav_frame_r_widget_dict
        self.global_info = global_info
        self.resource_obj = resource_obj
        self.resource_type = resource_type
        self.resource_info_dict = {}  # 用于存储资源对象信息的diction
        self.padx = 2
        self.pady = 2
        self.current_row_index = 0

    def show(self):  # 入口函数
        for widget in self.nav_frame_r_widget_dict["frame"].winfo_children():
            widget.destroy()
        if self.resource_type == RESOURCE_TYPE_PROJECT:
            self.edit_project()
        elif self.resource_type == RESOURCE_TYPE_CREDENTIAL:
            self.edit_credential()
        elif self.resource_type == RESOURCE_TYPE_HOST:
            self.edit_host()
        elif self.resource_type == RESOURCE_TYPE_HOST_GROUP:
            self.edit_host_group()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
            self.edit_inspection_code_block()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
            self.edit_inspection_template()
        else:
            print("<class EditResourceInFrame> resource_type is Unknown")
        self.add_save_and_return_button()
        self.update_frame()  # 更新Frame的尺寸，并将滚动条移到最开头

    def add_save_and_return_button(self):
        # ★创建“保存更新”按钮
        save_obj = UpdateResourceInFrame(self.main_window, self.resource_info_dict, self.global_info, self.resource_obj,
                                         self.resource_type)
        button_save = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="保存更新", command=save_obj.update)
        button_save.bind("<MouseWheel>", self.proces_mouse_scroll)
        button_save.grid(row=self.current_row_index + 1, column=0, padx=self.padx, pady=self.pady)
        # ★★添加“返回资源列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="取消编辑",
                                       command=lambda: self.main_window.list_resource_of_nav_frame_r_page(self.resource_type))
        button_return.bind("<MouseWheel>", self.proces_mouse_scroll)
        button_return.grid(row=self.current_row_index + 1, column=1, padx=self.padx, pady=self.pady)

    def proces_mouse_scroll(self, event):
        if event.delta > 0:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def update_frame(self):
        # 更新Frame的尺寸
        self.nav_frame_r_widget_dict["frame"].update_idletasks()
        self.nav_frame_r_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.nav_frame_r_widget_dict["frame"].winfo_width(),
                          self.nav_frame_r_widget_dict["frame"].winfo_height()))
        self.nav_frame_r_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll)
        # 滚动条移到最开头
        self.nav_frame_r_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def edit_project(self):
        # ★编辑-project
        label_edit_project = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 编辑项目 ★★")
        label_edit_project.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★project-名称
        label_project_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目名称")
        label_project_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_project_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_project_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_project_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_project_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_project_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★project-描述
        label_project_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_project_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_project_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_project_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_description"])
        entry_project_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_project_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_project_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 2

    def edit_credential(self):
        # ★编辑-credential
        label_edit_credential = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 编辑凭据 ★★")
        label_edit_credential.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★credential-名称
        label_credential_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="凭据名称")
        label_credential_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_credential_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_credential_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_credential_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★credential-描述
        label_credential_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_credential_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_credential_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                     textvariable=self.resource_info_dict["sv_description"])
        entry_credential_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_credential_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★credential-所属项目
        label_credential_project_oid = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_credential_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★credential-凭据类型
        label_credential_type = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="凭据类型")
        label_credential_type.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_type.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        cred_type_name_list = ["ssh_password", "ssh_key", "telnet", "ftp", "registry", "git"]
        self.resource_info_dict["combobox_cred_type"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=cred_type_name_list,
                                                                     state="readonly")
        if self.resource_obj.cred_type != -1:
            self.resource_info_dict["combobox_cred_type"].current(self.resource_obj.cred_type)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_cred_type"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★credential-用户名
        label_credential_username = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="username")
        label_credential_username.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_username.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_username"] = tkinter.StringVar()
        entry_credential_username = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_username"])
        entry_credential_username.insert(0, self.resource_obj.username)  # 显示初始值，可编辑
        entry_credential_username.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_username.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★credential-密码
        label_credential_password = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="password")
        label_credential_password.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_password.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_password"] = tkinter.StringVar()
        entry_credential_password = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_password"])
        entry_credential_password.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_password.insert(0, self.resource_obj.password)  # 显示初始值，可编辑
        entry_credential_password.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★credential-密钥
        label_credential_private_key = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="ssh_private_key")
        label_credential_private_key.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_private_key.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["text_private_key"] = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"], height=3, width=32)
        self.resource_info_dict["text_private_key"].insert(1.0, self.resource_obj.private_key)  # 显示初始值，可编辑
        self.resource_info_dict["text_private_key"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权类型
        label_credential_privilege_escalation_method = tkinter.Label(self.nav_frame_r_widget_dict["frame"],
                                                                     text="privilege_escalation_method")
        label_credential_privilege_escalation_method.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_privilege_escalation_method.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        privilege_escalation_method_list = ["su", "sudo"]
        self.resource_info_dict["combobox_privilege_escalation_method"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                                       values=privilege_escalation_method_list,
                                                                                       state="readonly")
        if self.resource_obj.privilege_escalation_method != -1:
            self.resource_info_dict["combobox_privilege_escalation_method"].current(self.resource_obj.privilege_escalation_method)
        self.resource_info_dict["combobox_privilege_escalation_method"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权用户
        label_credential_privilege_escalation_username = tkinter.Label(self.nav_frame_r_widget_dict["frame"],
                                                                       text="privilege_escalation_username")
        label_credential_privilege_escalation_username.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_privilege_escalation_username.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_privilege_escalation_username"] = tkinter.StringVar()
        entry_credential_privilege_escalation_username = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                                       textvariable=self.resource_info_dict[
                                                                           "sv_privilege_escalation_username"])
        entry_credential_privilege_escalation_username.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_privilege_escalation_username.insert(0, self.resource_obj.privilege_escalation_username)  # 显示初始值，可编辑
        entry_credential_privilege_escalation_username.grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权密码
        label_credential_privilege_escalation_password = tkinter.Label(self.nav_frame_r_widget_dict["frame"],
                                                                       text="privilege_escalation_password")
        label_credential_privilege_escalation_password.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_privilege_escalation_password.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_privilege_escalation_password"] = tkinter.StringVar()
        entry_credential_privilege_escalation_password = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                                       textvariable=self.resource_info_dict[
                                                                           "sv_privilege_escalation_password"])
        entry_credential_privilege_escalation_password.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_privilege_escalation_password.insert(0, self.resource_obj.privilege_escalation_password)  # 显示初始值，可编辑
        entry_credential_privilege_escalation_password.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★credential-auth_url
        label_credential_auth_url = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="auth_url")
        label_credential_auth_url.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_auth_url.grid(row=11, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_auth_url"] = tkinter.StringVar()
        entry_credential_auth_url = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_auth_url"])
        entry_credential_auth_url.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_credential_auth_url.insert(0, self.resource_obj.auth_url)  # 显示初始值，可编辑
        entry_credential_auth_url.grid(row=11, column=1, padx=self.padx, pady=self.pady)
        # ★credential-ssl_verify
        label_credential_ssl_verify = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="ssl_verify")
        label_credential_ssl_verify.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_ssl_verify.grid(row=12, column=0, padx=self.padx, pady=self.pady)
        ssl_verify_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_ssl_verify"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=ssl_verify_name_list,
                                                                      state="readonly")
        if self.resource_obj.ssl_verify != -1:
            self.resource_info_dict["combobox_ssl_verify"].current(self.resource_obj.ssl_verify)  # 显示初始值
        self.resource_info_dict["combobox_ssl_verify"].grid(row=12, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 12

    def edit_host(self):
        # ★创建-host
        label_edit_host = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 编辑主机 ★★")
        label_edit_host.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_edit_host.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★host-名称
        label_host_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机名称")
        label_host_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_host_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_host_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_host_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★host-描述
        label_host_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_host_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_host_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                               textvariable=self.resource_info_dict["sv_description"])
        entry_host_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_host_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★host-所属项目
        label_host_project_oid = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_host_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★host-address
        label_host_address = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="address")
        label_host_address.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_address.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_address"] = tkinter.StringVar()
        entry_host_address = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                           textvariable=self.resource_info_dict["sv_address"])
        entry_host_address.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_address.insert(0, self.resource_obj.address)  # 显示初始值，可编辑
        entry_host_address.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★host-ssh_port
        label_host_ssh_port = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="ssh_port")
        label_host_ssh_port.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_ssh_port.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_ssh_port"] = tkinter.StringVar()
        entry_host_ssh_port = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                            textvariable=self.resource_info_dict["sv_ssh_port"])
        entry_host_ssh_port.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_ssh_port.insert(0, self.resource_obj.ssh_port)  # 显示初始值，可编辑
        entry_host_ssh_port.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★host-telnet_port
        label_host_telnet_port = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="telnet_port")
        label_host_telnet_port.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_telnet_port.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_telnet_port"] = tkinter.StringVar()
        entry_host_telnet_port = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                               textvariable=self.resource_info_dict["sv_telnet_port"])
        entry_host_telnet_port.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_telnet_port.insert(0, self.resource_obj.telnet_port)  # 显示初始值，可编辑
        entry_host_telnet_port.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★host-login_protocol
        label_host_login_protocol = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="远程登录类型")
        label_host_login_protocol.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_login_protocol.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        login_protocol_name_list = ["ssh", "telnet"]
        self.resource_info_dict["combobox_login_protocol"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                          values=login_protocol_name_list,
                                                                          state="readonly")
        self.resource_info_dict["combobox_login_protocol"].current(self.resource_obj.login_protocol)
        self.resource_info_dict["combobox_login_protocol"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★host-first_auth_method
        label_host_first_auth_method = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="优先认证类型")
        label_host_first_auth_method.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_first_auth_method.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        first_auth_method_name_list = ["priKey", "password"]
        self.resource_info_dict["combobox_first_auth_method"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                             values=first_auth_method_name_list,
                                                                             state="readonly")
        self.resource_info_dict["combobox_first_auth_method"].current(self.resource_obj.first_auth_method)
        self.resource_info_dict["combobox_first_auth_method"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★host-凭据列表
        label_credential_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="凭据列表")
        label_credential_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_credential_list.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_credential"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                        yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                        selectforeground='black', exportselection=False,
                                                                        selectborderwidth=2, activestyle='dotbox', height=6)
        for cred in self.global_info.credential_obj_list:
            self.resource_info_dict["listbox_credential"].insert(tkinter.END, cred.name)  # 添加item选项
        for cred_oid in self.resource_obj.credential_oid_list:  # 设置已选择项★★★
            cred_index = self.global_info.get_credential_obj_index_of_list_by_oid(cred_oid)
            if cred_index is not None:
                self.resource_info_dict["listbox_credential"].select_set(cred_index)
        self.resource_info_dict["listbox_credential"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_credential"].yview)
        frame.grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 9

    def edit_host_group(self):
        # ★创建-host_group
        label_edit_host_group = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 编辑主机 ★★")
        label_edit_host_group.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_edit_host_group.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★host_group-名称
        label_host_group_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机名称")
        label_host_group_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_host_group_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_host_group_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_group_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_host_group_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-描述
        label_host_group_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_host_group_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_host_group_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                     textvariable=self.resource_info_dict["sv_description"])
        entry_host_group_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_host_group_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_host_group_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-所属项目
        label_host_group_project_oid = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_host_group_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-列表
        label_host_group_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机组列表")
        label_host_group_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_list.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_host_group"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                        yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                        selectforeground='black', exportselection=False,
                                                                        selectborderwidth=2, activestyle='dotbox', height=6)
        for host_group in self.global_info.host_group_obj_list:
            self.resource_info_dict["listbox_host_group"].insert(tkinter.END, host_group.name)  # 添加item选项
        for host_group_oid in self.resource_obj.host_group_oid_list:  # 设置已选择项★★★
            host_group_index = self.global_info.get_host_group_obj_index_of_list_by_oid(host_group_oid)
            if host_group_index is not None:
                self.resource_info_dict["listbox_host_group"].select_set(host_group_index)
        self.resource_info_dict["listbox_host_group"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_host_group"].yview)
        frame.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★host-列表
        label_host_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机列表")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_list.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_host"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                  yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                  selectforeground='black', exportselection=False,
                                                                  selectborderwidth=2, activestyle='dotbox', height=6)
        for host in self.global_info.host_obj_list:
            self.resource_info_dict["listbox_host"].insert(tkinter.END, host.name)  # 添加item选项
        for host_oid in self.resource_obj.host_oid_list:  # 设置已选择项★★★
            host_index = self.global_info.get_host_obj_index_of_list_by_oid(host_oid)
            if host_index is not None:
                self.resource_info_dict["listbox_host"].select_set(host_index)
        self.resource_info_dict["listbox_host"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_host"].yview)
        frame.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 5

    def edit_inspection_code_block(self):
        # ★创建-inspection_code_block
        label_edit_inspection_code_block = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 编辑巡检代码块 ★★")
        label_edit_inspection_code_block.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_edit_inspection_code_block.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-名称
        label_inspection_code_block_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检代码块名称")
        label_inspection_code_block_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_code_block_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_code_block_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                         textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_code_block_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_code_block_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_inspection_code_block_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-描述
        label_inspection_code_block_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_inspection_code_block_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_code_block_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_code_block_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                                textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_code_block_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_code_block_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_inspection_code_block_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-所属项目
        label_inspection_code_block_project_oid = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_inspection_code_block_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_code_block_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★命令内容-列表
        label_host_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检命令内容")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_list.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        # frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        # list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        # list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        # self.resource_info_dict["listbox_code_content"] = tkinter.Listbox(frame, selectmode="single", bg="white", bd=2, cursor="arrow",
        #                                                                   yscrollcommand=list_scrollbar.set, selectbackground='pink',
        #                                                                   selectforeground='black', exportselection=False,
        #                                                                   selectborderwidth=2, activestyle='dotbox', height=7, width=40)
        # for code_obj in self.resource_obj.code_list:
        #     self.resource_info_dict["listbox_code_content"].insert(tkinter.END, code_obj.code_content)  # 添加item选项
        # self.resource_info_dict["listbox_code_content"].pack(side="left")
        # list_scrollbar.config(command=self.resource_info_dict["listbox_code_content"].yview)
        # frame.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        self.resource_info_dict["text_code_content"] = tkinter.Text(master=self.nav_frame_r_widget_dict["frame"], width=40, height=12)
        for code_obj in self.resource_obj.code_list:
            self.resource_info_dict["text_code_content"].insert(tkinter.END, code_obj.code_content + "\n")
        self.resource_info_dict["text_code_content"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 4

    def edit_inspection_template(self):
        # ★创建-inspection_template
        label_edit_inspection_template = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 编辑巡检模板 ★★")
        label_edit_inspection_template.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_edit_inspection_template.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_template-名称
        label_inspection_template_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检模板名称")
        label_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_template_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                       textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_template_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_inspection_template_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-描述
        label_inspection_template_description = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="描述")
        label_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_template_description = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                              textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_template_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_inspection_template_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-所属项目
        label_inspection_template_project_oid = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="项目")
        label_inspection_template_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_method
        label_inspection_template_execution_method = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="execution_method")
        label_inspection_template_execution_method.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_execution_method.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        execution_method_name_list = ["无", "定时执行", "周期执行", "After"]
        self.resource_info_dict["combobox_execution_method"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                            values=execution_method_name_list,
                                                                            state="readonly")
        self.resource_info_dict["combobox_execution_method"].current(self.resource_obj.execution_method)
        self.resource_info_dict["combobox_execution_method"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-update_code_on_launch
        label_inspection_template_update_code_on_launch = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="运行前更新code")
        label_inspection_template_update_code_on_launch.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_update_code_on_launch.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        update_code_on_launch_name_list = ["Yes", "No"]
        self.resource_info_dict["combobox_update_code_on_launch"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                                 values=update_code_on_launch_name_list,
                                                                                 state="readonly")
        self.resource_info_dict["combobox_update_code_on_launch"].current(self.resource_obj.update_code_on_launch)
        self.resource_info_dict["combobox_update_code_on_launch"].grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-forks
        label_inspection_template_forks = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="运行线程数")
        label_inspection_template_forks.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_forks.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_forks"] = tkinter.StringVar()
        spinbox_inspection_template_forks = tkinter.Spinbox(self.nav_frame_r_widget_dict["frame"], from_=1, to=256, increment=1,
                                                            textvariable=self.resource_info_dict["sv_forks"])
        self.resource_info_dict["sv_forks"].set(self.resource_obj.forks)  # 显示初始值，可编辑
        spinbox_inspection_template_forks.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-save_output_to_file
        label_inspection_template_save_output_to_file = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="自动保存巡检日志到文件")
        label_inspection_template_save_output_to_file.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_save_output_to_file.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        save_output_to_file_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_save_output_to_file"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                               values=save_output_to_file_name_list,
                                                                               state="readonly")
        self.resource_info_dict["combobox_save_output_to_file"].current(self.resource_obj.save_output_to_file)
        self.resource_info_dict["combobox_save_output_to_file"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-output_file_name_style
        label_inspection_template_output_file_name_style = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检日志文件名称")
        label_inspection_template_output_file_name_style.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_output_file_name_style.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        output_file_name_style_name_list = ["HOSTNAME", "HOSTNAME-DATE", "HOSTNAME-DATE-TIME", "DATE_DIR/HOSTNAME",
                                            "DATE_DIR/HOSTNAME-DATE",
                                            "DATE_DIR/HOSTNAME-DATE-TIME"]
        self.resource_info_dict["combobox_output_file_name_style"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                                  values=output_file_name_style_name_list,
                                                                                  state="readonly", width=32)
        self.resource_info_dict["combobox_output_file_name_style"].current(self.resource_obj.output_file_name_style)
        self.resource_info_dict["combobox_output_file_name_style"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-列表
        label_host_group_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机组列表")
        label_host_group_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_group_list.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_host_group"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                        yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                        selectforeground='black', exportselection=False,
                                                                        selectborderwidth=2, activestyle='dotbox', height=6)
        for host_group in self.global_info.host_group_obj_list:
            self.resource_info_dict["listbox_host_group"].insert(tkinter.END, host_group.name)  # 添加item选项
        for host_group_oid in self.resource_obj.host_group_oid_list:  # 设置已选择项★★★
            host_group_index = self.global_info.get_host_group_obj_index_of_list_by_oid(host_group_oid)
            if host_group_index is not None:
                self.resource_info_dict["listbox_host_group"].select_set(host_group_index)
        self.resource_info_dict["listbox_host_group"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_host_group"].yview)
        frame.grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★host-列表
        label_host_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="主机列表")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_host_list.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_host"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2, cursor="arrow",
                                                                  yscrollcommand=list_scrollbar.set, selectbackground='pink',
                                                                  selectforeground='black', exportselection=False,
                                                                  selectborderwidth=2, activestyle='dotbox', height=6)
        for host in self.global_info.host_obj_list:
            self.resource_info_dict["listbox_host"].insert(tkinter.END, host.name)  # 添加item选项
        for host_oid in self.resource_obj.host_oid_list:  # 设置已选择项★★★
            host_index = self.global_info.get_host_obj_index_of_list_by_oid(host_oid)
            if host_index is not None:
                self.resource_info_dict["listbox_host"].select_set(host_index)
        self.resource_info_dict["listbox_host"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_host"].yview)
        frame.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★巡检代码块-列表
        label_inspection_code_block_list = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检代码块列表")
        label_inspection_code_block_list.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_code_block_list.grid(row=11, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.nav_frame_r_widget_dict["frame"])
        list_scrollbar = tkinter.Scrollbar(frame)  # 创建窗口滚动条
        list_scrollbar.pack(side="right", fill="y")  # 设置窗口滚动条位置
        self.resource_info_dict["listbox_inspection_code_block"] = tkinter.Listbox(frame, selectmode="multiple", bg="white", bd=2,
                                                                                   cursor="arrow",
                                                                                   yscrollcommand=list_scrollbar.set,
                                                                                   selectbackground='pink',
                                                                                   selectforeground='black', exportselection=False,
                                                                                   selectborderwidth=2, activestyle='dotbox', height=6)
        for inspection_code_block in self.global_info.inspection_code_block_obj_list:
            self.resource_info_dict["listbox_inspection_code_block"].insert(tkinter.END, inspection_code_block.name)  # 添加item选项
        for inspection_code_block_oid in self.resource_obj.inspection_code_block_oid_list:  # 设置已选择项★★★
            inspection_code_block_index = self.global_info.get_inspection_code_block_obj_index_of_list_by_oid(inspection_code_block_oid)
            if inspection_code_block_index is not None:
                self.resource_info_dict["listbox_inspection_code_block"].select_set(inspection_code_block_index)
        self.resource_info_dict["listbox_inspection_code_block"].pack(side="left")
        list_scrollbar.config(command=self.resource_info_dict["listbox_inspection_code_block"].yview)
        frame.grid(row=11, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 11


class UpdateResourceInFrame:
    """
    在主窗口的创建资源界面，点击“保存更新”按钮时，更新并保存资源信息
    """

    def __init__(self, main_window=None, resource_info_dict=None, global_info=None, resource_obj=None,
                 resource_type=None):
        self.main_window = main_window
        self.resource_info_dict = resource_info_dict
        self.global_info = global_info
        self.resource_obj = resource_obj
        self.resource_type = resource_type

    def update(self):  # 入口函数
        if self.resource_type == RESOURCE_TYPE_PROJECT:
            self.update_project()
        elif self.resource_type == RESOURCE_TYPE_CREDENTIAL:
            self.update_credential()
        elif self.resource_type == RESOURCE_TYPE_HOST:
            self.update_host()
        elif self.resource_type == RESOURCE_TYPE_HOST_GROUP:
            self.update_host_group()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
            self.update_inspection_code_block()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
            self.update_inspection_template()
        else:
            print("<class UpdateResourceInFrame> resource_type is Unknown")

    def update_project(self):
        project_name = self.resource_info_dict["sv_name"].get()
        project_description = self.resource_info_dict["sv_description"].get()
        print(project_name, project_description)
        # 更新-project
        if project_name == '':
            messagebox.showinfo("创建项目-Error", f"项目名称不能为空")
        elif len(project_name) > 128:
            messagebox.showinfo("创建项目-Error", f"项目名称>128字符")
        elif len(project_description) > 256:
            messagebox.showinfo("创建项目-Error", f"项目描述>256字符")
        else:
            self.resource_obj.update(name=project_name, description=project_description, global_info=self.global_info)
            self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_PROJECT)  # 更新项目信息后，返回项目展示页面

    def update_credential(self):
        credential_name = self.resource_info_dict["sv_name"].get()
        credential_description = self.resource_info_dict["sv_description"].get()
        # ★项目  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # ★cred_type
        if self.resource_info_dict["combobox_cred_type"].current() == -1:
            credential_cred_type = 0
        else:
            credential_cred_type = self.resource_info_dict["combobox_cred_type"].current()
        credential_username = self.resource_info_dict["sv_username"].get()
        credential_password = self.resource_info_dict["sv_password"].get()
        credential_private_key = self.resource_info_dict["text_private_key"].get("1.0", tkinter.END)
        # ★privilege_escalation_method
        if self.resource_info_dict["combobox_privilege_escalation_method"].current() == -1:
            credential_privilege_escalation_method = 0
        else:
            credential_privilege_escalation_method = self.resource_info_dict["combobox_privilege_escalation_method"].current()
        credential_privilege_escalation_username = self.resource_info_dict["sv_privilege_escalation_username"].get()
        credential_privilege_escalation_password = self.resource_info_dict["sv_privilege_escalation_password"].get()
        credential_auth_url = self.resource_info_dict["sv_auth_url"].get()
        # ★ssl_verify
        if self.resource_info_dict["combobox_ssl_verify"].current() == -1:
            credential_ssl_verify = 0
        else:
            credential_ssl_verify = self.resource_info_dict["combobox_ssl_verify"].current()
        # 更新-credential
        if credential_name == '':
            messagebox.showinfo("创建凭据-Error", f"凭据名称不能为空")
        elif len(credential_name) > 128:
            messagebox.showinfo("创建凭据-Error", f"凭据名称>128字符")
        elif len(credential_description) > 256:
            messagebox.showinfo("创建凭据-Error", f"凭据描述>256字符")
        else:
            self.resource_obj.update(name=credential_name, description=credential_description, project_oid=project_oid,
                                     cred_type=credential_cred_type,
                                     username=credential_username, password=credential_password, private_key=credential_private_key,
                                     privilege_escalation_method=credential_privilege_escalation_method,
                                     privilege_escalation_username=credential_privilege_escalation_username,
                                     privilege_escalation_password=credential_privilege_escalation_password,
                                     auth_url=credential_auth_url,
                                     ssl_verify=credential_ssl_verify,
                                     global_info=self.global_info)
            self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_CREDENTIAL)  # 更新credential信息后，返回“显示credential列表”页面

    def update_host(self):
        host_name = self.resource_info_dict["sv_name"].get()
        host_description = self.resource_info_dict["sv_description"].get()
        # ★项目  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        host_address = self.resource_info_dict["sv_address"].get()
        host_ssh_port_str = self.resource_info_dict["sv_ssh_port"].get()
        # ★ssh_port
        if host_ssh_port_str != "" and host_ssh_port_str.isdigit():
            host_ssh_port = int(host_ssh_port_str)
        else:
            host_ssh_port = 22
        # ★telnet_port
        host_telnet_port_str = self.resource_info_dict["sv_telnet_port"].get()
        if host_telnet_port_str != "" and host_telnet_port_str.isdigit():
            host_telnet_port = int(host_telnet_port_str)
        else:
            host_telnet_port = 23
        # ★login_protocol
        if self.resource_info_dict["combobox_login_protocol"].current() == -1:
            host_login_protocol = 0
        else:
            host_login_protocol = self.resource_info_dict["combobox_login_protocol"].current()
        # ★first_auth_method
        if self.resource_info_dict["combobox_first_auth_method"].current() == -1:
            host_first_auth_method = 0
        else:
            host_first_auth_method = self.resource_info_dict["combobox_first_auth_method"].current()
        # 先更新host的credential_oid_list
        self.resource_obj.credential_oid_list = []
        for selected_credential_index in self.resource_info_dict["listbox_credential"].curselection():  # host对象添加凭据列表
            self.resource_obj.add_credential(self.global_info.credential_obj_list[selected_credential_index])
        # 更新-host-对象本身
        if host_name == '':
            messagebox.showinfo("编辑主机-Error", f"主机名称不能为空")
        elif len(host_name) > 128:
            messagebox.showinfo("编辑主机-Error", f"主机名称>128字符")
        elif len(host_description) > 256:
            messagebox.showinfo("编辑主机-Error", f"主机描述>256字符")
        else:
            self.resource_obj.update(name=host_name, description=host_description, project_oid=project_oid,
                                     address=host_address,
                                     ssh_port=host_ssh_port, telnet_port=host_telnet_port,
                                     login_protocol=host_login_protocol,
                                     first_auth_method=host_first_auth_method,
                                     global_info=self.global_info)
            self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_HOST)  # 更新host信息后，返回“显示host列表”页面

    def update_host_group(self):
        host_group_name = self.resource_info_dict["sv_name"].get()
        host_group_description = self.resource_info_dict["sv_description"].get()
        # ★项目  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # 先更新host_group的 host_group_oid_list
        self.resource_obj.host_group_oid_list = []
        for selected_host_group_index in self.resource_info_dict["listbox_host_group"].curselection():  # host_group对象添加host_group列表
            self.resource_obj.add_host_group(self.global_info.host_group_obj_list[selected_host_group_index])
        # 先更新host_group的 host_oid_list
        self.resource_obj.host_oid_list = []
        for selected_host_index in self.resource_info_dict["listbox_host"].curselection():  # host对象添加host列表
            self.resource_obj.add_host(self.global_info.host_obj_list[selected_host_index])
        # 更新-host_group-对象本身
        if host_group_name == '':
            messagebox.showinfo("编辑主机组-Error", f"主机组名称不能为空")
        elif len(host_group_name) > 128:
            messagebox.showinfo("编辑主机组-Error", f"主机组名称>128字符")
        elif len(host_group_description) > 256:
            messagebox.showinfo("编辑主机组-Error", f"主机组描述>256字符")
        else:
            self.resource_obj.update(name=host_group_name, description=host_group_description, project_oid=project_oid,
                                     global_info=self.global_info)
            self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_HOST_GROUP)  # 更新host_group信息后，返回“显示host_group列表”页面

    def update_inspection_code_block(self):
        inspection_code_block_name = self.resource_info_dict["sv_name"].get()
        inspection_code_block_description = self.resource_info_dict["sv_description"].get()
        # ★项目  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # 先更新inspection_code_block的 code_list
        self.resource_obj.code_list = []
        code_content_str = self.resource_info_dict["text_code_content"].get("1.0", tkinter.END).strip()
        code_index = 0
        for code_line_str in code_content_str.split("\n"):
            code_line_str_strip = code_line_str.strip()
            if code_line_str_strip != "":
                one_line_code_obj = OneLineCode(code_index=code_index, code_content=code_line_str_strip)
                self.resource_obj.add_code_line(one_line_code_obj)
        # 更新-inspection_code_block-对象本身
        if inspection_code_block_name == '':
            messagebox.showinfo("编辑巡检代码块-Error", f"巡检代码块名称不能为空")
        elif len(inspection_code_block_name) > 128:
            messagebox.showinfo("编辑巡检代码块-Error", f"巡检代码块名称>128字符")
        elif len(inspection_code_block_description) > 256:
            messagebox.showinfo("编辑巡检代码块-Error", f"巡检代码块名称>256字符")
        else:
            self.resource_obj.update(name=inspection_code_block_name, description=inspection_code_block_description,
                                     project_oid=project_oid,
                                     global_info=self.global_info)
            self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_INSPECTION_CODE_BLOCK)  # 更新inspection_code_block信息后，返回

    def update_inspection_template(self):
        inspection_template_name = self.resource_info_dict["sv_name"].get()
        inspection_template_description = self.resource_info_dict["sv_description"].get()
        # ★项目  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # ★execution_method
        if self.resource_info_dict["combobox_execution_method"].current() == -1:
            inspection_template_execution_method = 0
        else:
            inspection_template_execution_method = self.resource_info_dict["combobox_execution_method"].current()
        # ★update_code_on_launch
        if self.resource_info_dict["combobox_update_code_on_launch"].current() == -1:
            inspection_template_update_code_on_launch = 0
        else:
            inspection_template_update_code_on_launch = self.resource_info_dict["combobox_update_code_on_launch"].current()
        # ★forks
        inspection_template_forks = int(self.resource_info_dict["sv_forks"].get())
        # ★save_output_to_file
        if self.resource_info_dict["combobox_save_output_to_file"].current() == -1:
            inspection_template_save_output_to_file = 0
        else:
            inspection_template_save_output_to_file = self.resource_info_dict["combobox_save_output_to_file"].current()
        # ★output_file_name_style
        if self.resource_info_dict["combobox_output_file_name_style"].current() == -1:
            inspection_template_output_file_name_style = 0
        else:
            inspection_template_output_file_name_style = self.resource_info_dict["combobox_output_file_name_style"].current()
        # 先更新inspection_template的 host_group_oid_list
        self.resource_obj.host_group_oid_list = []
        for selected_host_group_index in self.resource_info_dict["listbox_host_group"].curselection():  # 添加host_group列表
            self.resource_obj.add_host_group(self.global_info.host_group_obj_list[selected_host_group_index])
        # 先更新inspection_template的 host_oid_list
        self.resource_obj.host_oid_list = []
        for selected_host_index in self.resource_info_dict["listbox_host"].curselection():  # 添加host列表
            self.resource_obj.add_host(self.global_info.host_obj_list[selected_host_index])
        # 先更新inspection_template的 inspection_code_block_obj_list
        self.resource_obj.inspection_code_block_oid_list = []
        for selected_code_block_index in self.resource_info_dict["listbox_inspection_code_block"].curselection():  # 添加巡检代码块列表
            self.resource_obj.add_inspection_code_block(self.global_info.inspection_code_block_obj_list[selected_code_block_index])
        # 更新-inspection_template-对象本身
        if inspection_template_name == '':
            messagebox.showinfo("编辑巡检模板-Error", f"巡检模板名称不能为空")
        elif len(inspection_template_name) > 128:
            messagebox.showinfo("编辑巡检模板-Error", f"巡检模板名称>128字符")
        elif len(inspection_template_description) > 256:
            messagebox.showinfo("编辑巡检模板-Error", f"巡检模板描述>256字符")
        else:
            self.resource_obj.update(name=inspection_template_name, description=inspection_template_description,
                                     project_oid=project_oid, execution_method=inspection_template_execution_method,
                                     update_code_on_launch=inspection_template_update_code_on_launch, forks=inspection_template_forks,
                                     save_output_to_file=inspection_template_save_output_to_file,
                                     output_file_name_style=inspection_template_output_file_name_style,
                                     global_info=self.global_info)
            self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_INSPECTION_TEMPLATE)  # 更新信息后，返回“显示资源列表”页面


class DeleteResourceInFrame:
    """
    在主窗口的查看资源界面，删除选中的资源对象
    """

    def __init__(self, main_window=None, nav_frame_r_widget_dict=None, global_info=None, resource_obj=None,
                 resource_type=RESOURCE_TYPE_PROJECT):
        self.main_window = main_window
        self.nav_frame_r_widget_dict = nav_frame_r_widget_dict
        self.global_info = global_info
        self.resource_obj = resource_obj
        self.resource_type = resource_type

    def show(self):  # 入口函数
        result = messagebox.askyesno("删除资源", f"是否删除'{self.resource_obj.name}'资源对象？")
        # messagebox.askyesno()参数1为弹窗标题，参数2为弹窗内容，有2个按钮（是，否），点击"是"时返回True
        if result:
            for widget in self.nav_frame_r_widget_dict["frame"].winfo_children():
                widget.destroy()
            if self.resource_type == RESOURCE_TYPE_PROJECT:
                self.delete_project()
            elif self.resource_type == RESOURCE_TYPE_CREDENTIAL:
                self.delete_credential()
            elif self.resource_type == RESOURCE_TYPE_HOST:
                self.delete_host()
            elif self.resource_type == RESOURCE_TYPE_HOST_GROUP:
                self.delete_host_group()
            elif self.resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
                self.delete_inspection_code_block()
            elif self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
                self.delete_inspection_template()
            else:
                print("<class DeleteResourceInFrame> resource_type is Unknown")
        else:
            print("用户取消了删除操作")

    def delete_project(self):
        self.global_info.delete_project_obj(self.resource_obj)
        self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_PROJECT)

    def delete_credential(self):
        self.global_info.delete_credential_obj(self.resource_obj)
        self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_CREDENTIAL)

    def delete_host(self):
        self.global_info.delete_host_obj(self.resource_obj)
        self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_HOST)

    def delete_host_group(self):
        self.global_info.delete_host_group_obj(self.resource_obj)
        self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_HOST_GROUP)

    def delete_inspection_code_block(self):
        self.global_info.delete_inspection_code_block_obj(self.resource_obj)
        self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_INSPECTION_CODE_BLOCK)

    def delete_inspection_template(self):
        self.global_info.delete_inspection_template_obj(self.resource_obj)
        self.main_window.list_resource_of_nav_frame_r_page(RESOURCE_TYPE_INSPECTION_TEMPLATE)


class SaveResourceInMainWindow:
    """
    在主窗口的创建资源界面，点击“保存”按钮时，保存资源信息
    """

    def __init__(self, main_window=None, resource_info_dict=None, global_info=None, resource_type=RESOURCE_TYPE_PROJECT):
        self.main_window = main_window
        self.resource_info_dict = resource_info_dict
        self.global_info = global_info
        self.resource_type = resource_type

    def save(self):  # 入口函数
        if self.resource_type == RESOURCE_TYPE_PROJECT:
            self.save_project()
        elif self.resource_type == RESOURCE_TYPE_CREDENTIAL:
            self.save_credential()
        elif self.resource_type == RESOURCE_TYPE_HOST:
            self.save_host()
        elif self.resource_type == RESOURCE_TYPE_HOST_GROUP:
            self.save_host_group()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
            self.save_inspection_code_block()
        elif self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
            self.save_inspection_template()
        else:
            print("<class SaveResourceInMainWindow> resource_type is Unknown")

    def save_project(self):
        project_name = self.resource_info_dict["sv_name"].get()
        project_description = self.resource_info_dict["sv_description"].get()
        print(project_name, project_description)
        # 创建项目
        if project_name == '':
            messagebox.showinfo("创建项目-Error", f"项目名称不能为空")
        elif len(project_name) > 128:
            messagebox.showinfo("创建项目-Error", f"项目名称>128字符")
        elif len(project_description) > 256:
            messagebox.showinfo("创建项目-Error", f"项目描述>256字符")
        elif self.global_info.is_project_name_existed(project_name):
            messagebox.showinfo("创建项目-Error", f"项目名称 {project_name} 已存在")
        else:
            project = Project(name=project_name, description=project_description, global_info=self.global_info)
            project.save()
            self.global_info.project_obj_list.append(project)
            self.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_PROJECT)  # 保存项目信息后，返回项目展示页面

    def save_credential(self):
        credential_name = self.resource_info_dict["sv_name"].get()
        credential_description = self.resource_info_dict["sv_description"].get()
        # 凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        if self.resource_info_dict["combobox_cred_type"].current() == -1:
            credential_cred_type = 0
        else:
            credential_cred_type = self.resource_info_dict["combobox_cred_type"].current()
        credential_username = self.resource_info_dict["sv_username"].get()
        credential_password = self.resource_info_dict["sv_password"].get()
        credential_private_key = self.resource_info_dict["text_private_key"].get("1.0", tkinter.END)
        if self.resource_info_dict["combobox_privilege_escalation_method"].current() == -1:
            credential_privilege_escalation_method = 0
        else:
            credential_privilege_escalation_method = self.resource_info_dict["combobox_privilege_escalation_method"].current()
        credential_privilege_escalation_username = self.resource_info_dict["sv_privilege_escalation_username"].get()
        credential_privilege_escalation_password = self.resource_info_dict["sv_privilege_escalation_password"].get()
        credential_auth_url = self.resource_info_dict["sv_auth_url"].get()
        if self.resource_info_dict["combobox_ssl_verify"].current() == -1:
            credential_ssl_verify = 0
        else:
            credential_ssl_verify = self.resource_info_dict["combobox_ssl_verify"].current()
        # print(credential_name, credential_description)
        # 创建credential
        if credential_name == '':
            messagebox.showinfo("创建凭据-Error", f"凭据名称不能为空")
        elif len(credential_name) > 128:
            messagebox.showinfo("创建凭据-Error", f"凭据名称>128字符")
        elif len(credential_description) > 256:
            messagebox.showinfo("创建凭据-Error", f"凭据描述>256字符")
        elif self.global_info.is_credential_name_existed(credential_name):
            messagebox.showinfo("创建凭据-Error", f"凭据名称 {credential_name} 已存在")
        else:
            credential = Credential(name=credential_name, description=credential_description, project_oid=project_oid,
                                    cred_type=credential_cred_type,
                                    username=credential_username, password=credential_password, private_key=credential_private_key,
                                    privilege_escalation_method=credential_privilege_escalation_method,
                                    privilege_escalation_username=credential_privilege_escalation_username,
                                    privilege_escalation_password=credential_privilege_escalation_password,
                                    auth_url=credential_auth_url,
                                    ssl_verify=credential_ssl_verify,
                                    global_info=self.global_info)
            credential.save()
            self.global_info.credential_obj_list.append(credential)
            self.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_CREDENTIAL)  # 保存credential信息后，返回credential展示页面

    def save_host(self):
        host_name = self.resource_info_dict["sv_name"].get()
        host_description = self.resource_info_dict["sv_description"].get()
        # ★project_oid  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        host_address = self.resource_info_dict["sv_address"].get()
        host_ssh_port_str = self.resource_info_dict["sv_ssh_port"].get()
        # ★ssh_port
        if host_ssh_port_str != "" and host_ssh_port_str.isdigit():
            host_ssh_port = int(host_ssh_port_str)
        else:
            host_ssh_port = 22
        # ★telnet_port
        host_telnet_port_str = self.resource_info_dict["sv_telnet_port"].get()
        if host_telnet_port_str != "" and host_telnet_port_str.isdigit():
            host_telnet_port = int(host_telnet_port_str)
        else:
            host_telnet_port = 23
        # ★login_protocol
        if self.resource_info_dict["combobox_login_protocol"].current() == -1:
            host_login_protocol = 0  # LOGIN_PROTOCOL_SSH
        else:
            host_login_protocol = self.resource_info_dict["combobox_login_protocol"].current()
        # ★first_auth_method
        if self.resource_info_dict["combobox_first_auth_method"].current() == -1:
            host_first_auth_method = 0
        else:
            host_first_auth_method = self.resource_info_dict["combobox_first_auth_method"].current()
        # 创建host
        if host_name == '':
            messagebox.showinfo("创建主机-Error", f"主机名称不能为空")
        elif len(host_name) > 128:
            messagebox.showinfo("创建主机-Error", f"主机名称>128字符")
        elif len(host_description) > 256:
            messagebox.showinfo("创建主机-Error", f"主机描述>256字符")
        elif self.global_info.is_host_name_existed(host_name):
            messagebox.showinfo("创建主机-Error", f"主机名称 {host_name} 已存在")
        else:
            host = Host(name=host_name, description=host_description, project_oid=project_oid,
                        address=host_address,
                        ssh_port=host_ssh_port, telnet_port=host_telnet_port,
                        login_protocol=host_login_protocol,
                        first_auth_method=host_first_auth_method,
                        global_info=self.global_info)
            for selected_credential_index in self.resource_info_dict["listbox_credential"].curselection():  # host对象添加凭据列表
                host.add_credential(self.global_info.credential_obj_list[selected_credential_index])
            host.save()  # 保存资源对象
            self.global_info.host_obj_list.append(host)
            self.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_HOST)  # 保存host信息后，返回host展示页面

    def save_host_group(self):
        host_group_name = self.resource_info_dict["sv_name"].get()
        host_group_description = self.resource_info_dict["sv_description"].get()
        # ★project_oid  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # 创建host_group
        if host_group_name == '':
            messagebox.showinfo("创建主机-Error", f"主机名称不能为空")
        elif len(host_group_name) > 128:
            messagebox.showinfo("创建主机-Error", f"主机名称>128字符")
        elif len(host_group_description) > 256:
            messagebox.showinfo("创建主机-Error", f"主机描述>256字符")
        elif self.global_info.is_host_group_name_existed(host_group_name):
            messagebox.showinfo("创建主机-Error", f"主机名称 {host_group_name} 已存在")
        else:
            host_group = HostGroup(name=host_group_name, description=host_group_description, project_oid=project_oid,
                                   global_info=self.global_info)
            for selected_host_index in self.resource_info_dict["listbox_host"].curselection():  # host_group对象添加主机列表
                host_group.add_host(self.global_info.host_obj_list[selected_host_index])
            for selected_host_group_index in self.resource_info_dict["listbox_host_group"].curselection():  # host_group对象添加主机组列表
                host_group.add_host_group(self.global_info.host_group_obj_list[selected_host_group_index])
            host_group.save()  # 保存资源对象
            self.global_info.host_group_obj_list.append(host_group)
            self.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_HOST_GROUP)  # 保存host_group信息后，返回host_group展示页面

    def save_inspection_code_block(self):
        inspection_code_block_name = self.resource_info_dict["sv_name"].get()
        inspection_code_block_description = self.resource_info_dict["sv_description"].get()
        # ★project_oid  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # 创建inspection_code_block
        if inspection_code_block_name == '':
            messagebox.showinfo("创建巡检代码块-Error", f"巡检代码块名称不能为空")
        elif len(inspection_code_block_name) > 128:
            messagebox.showinfo("创建巡检代码块-Error", f"巡检代码块名称>128字符")
        elif len(inspection_code_block_description) > 256:
            messagebox.showinfo("创建巡检代码块-Error", f"巡检代码块描述>256字符")
        elif self.global_info.is_inspection_code_block_name_existed(inspection_code_block_name):
            messagebox.showinfo("创建巡检代码块-Error", f"巡检代码块名称 {inspection_code_block_name} 已存在")
        else:
            inspection_code_block = InspectionCodeBlock(name=inspection_code_block_name, description=inspection_code_block_description,
                                                        project_oid=project_oid,
                                                        global_info=self.global_info)
            # ★inspection_code_block对象添加code_line列表
            code_content_str = self.resource_info_dict["text_code_content"].get("1.0", tkinter.END).strip()
            code_index = 0
            for code_line_str in code_content_str.split("\n"):
                code_line_str_strip = code_line_str.strip()
                if code_line_str_strip != "":
                    one_line_code_obj = OneLineCode(code_index=code_index, code_content=code_line_str_strip)
                    inspection_code_block.add_code_line(one_line_code_obj)
            inspection_code_block.save()  # 保存资源对象
            self.global_info.inspection_code_block_obj_list.append(inspection_code_block)
            self.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_INSPECTION_CODE_BLOCK)  # 保存后，返回展示页面

    def save_inspection_template(self):
        inspection_template_name = self.resource_info_dict["sv_name"].get()
        inspection_template_description = self.resource_info_dict["sv_description"].get()
        # ★project_oid  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # ★execution_method
        if self.resource_info_dict["combobox_execution_method"].current() == -1:
            inspection_template_execution_method = 0
        else:
            inspection_template_execution_method = self.resource_info_dict["combobox_execution_method"].current()
        # ★update_code_on_launch
        if self.resource_info_dict["combobox_update_code_on_launch"].current() == -1:
            inspection_template_update_code_on_launch = 0
        else:
            inspection_template_update_code_on_launch = self.resource_info_dict["combobox_update_code_on_launch"].current()
        # ★forks
        inspection_template_forks = int(self.resource_info_dict["sv_forks"].get())
        # ★save_output_to_file
        if self.resource_info_dict["combobox_save_output_to_file"].current() == -1:
            inspection_template_save_output_to_file = 0
        else:
            inspection_template_save_output_to_file = self.resource_info_dict["combobox_save_output_to_file"].current()
        # ★output_file_name_style
        if self.resource_info_dict["combobox_output_file_name_style"].current() == -1:
            inspection_template_output_file_name_style = 0
        else:
            inspection_template_output_file_name_style = self.resource_info_dict["combobox_output_file_name_style"].current()
        # 创建inspection_template
        if inspection_template_name == '':
            messagebox.showinfo("创建巡检模板-Error", f"巡检模板名称不能为空")
        elif len(inspection_template_name) > 128:
            messagebox.showinfo("创建巡检模板-Error", f"巡检模板名称>128字符")
        elif len(inspection_template_description) > 256:
            messagebox.showinfo("创建巡检模板-Error", f"巡检模板描述>256字符")
        elif self.global_info.is_inspection_template_name_existed(inspection_template_name):
            messagebox.showinfo("创建巡检模板-Error", f"巡检模板名称 {inspection_template_name} 已存在")
        else:
            inspection_template = InspectionTemplate(name=inspection_template_name, description=inspection_template_description,
                                                     project_oid=project_oid, forks=inspection_template_forks,
                                                     execution_method=inspection_template_execution_method,
                                                     update_code_on_launch=inspection_template_update_code_on_launch,
                                                     save_output_to_file=inspection_template_save_output_to_file,
                                                     output_file_name_style=inspection_template_output_file_name_style,
                                                     global_info=self.global_info)
            # ★inspection_template对象添加 主机、主机组、巡检代码块
            for selected_host_index in self.resource_info_dict["listbox_host"].curselection():  # 添加主机列表
                inspection_template.add_host(self.global_info.host_obj_list[selected_host_index])
            for selected_host_group_index in self.resource_info_dict["listbox_host_group"].curselection():  # 添加主机组列表
                inspection_template.add_host_group(self.global_info.host_group_obj_list[selected_host_group_index])
            for selected_code_block_index in self.resource_info_dict["listbox_inspection_code_block"].curselection():  # 添加巡检代码块列表
                inspection_template.add_inspection_code_block(self.global_info.inspection_code_block_obj_list[selected_code_block_index])
            inspection_template.save()  # 保存资源对象
            self.global_info.inspection_template_obj_list.append(inspection_template)
            self.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_INSPECTION_TEMPLATE)  # 保存后，返回展示页面


class StartInspectionTemplateInFrame:
    """
    在主窗口的查看资源界面，启动目标巡检模板作业，并添加用于显示巡检模板执行情况的控件
    """

    def __init__(self, main_window=None, nav_frame_r_widget_dict=None, global_info=None, inspection_template_obj=None):
        self.main_window = main_window
        self.nav_frame_r_widget_dict = nav_frame_r_widget_dict
        self.global_info = global_info
        self.inspection_template_obj = inspection_template_obj
        self.padx = 2
        self.pady = 2
        self.resource_info_dict = {}  # 用于存储资源对象信息的diction，这个可不要了
        self.current_inspection_job_obj = None  # 为 <LaunchInspectionJob> 类对象
        self.current_row_index = 0

    def start(self):
        existed_inspection_job_obj_list = self.global_info.get_inspection_job_obj_by_inspection_template_oid(
            self.inspection_template_obj.oid)
        if len(existed_inspection_job_obj_list) > 0:
            print("已有历史巡检作业！")
            for job in existed_inspection_job_obj_list:
                if job.job_state == INSPECTION_CODE_JOB_EXEC_STATE_STARTED:
                    messagebox.showinfo("启动巡检作业", "还有历史作业未完成，无法启动新的巡检作业！")
                    return
        else:
            pass
        result = messagebox.askyesno("启动巡检作业", "是否立即启动巡检作业？")
        if result:
            print(f"开始启动巡检作业: {self.inspection_template_obj.name}")
            inspect_job_name = "job-" + self.inspection_template_obj.name + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # template_project_name=self.global_info.get_project_by_oid(self.inspection_template_obj.project_oid)
            self.current_inspection_job_obj = LaunchInspectionJob(name=inspect_job_name,
                                                                  project_oid=self.inspection_template_obj.project_oid,
                                                                  inspection_template=self.inspection_template_obj,
                                                                  global_info=self.global_info)
            self.global_info.inspection_job_obj_list.append(self.current_inspection_job_obj)
            job_thread = threading.Thread(target=self.current_inspection_job_obj.start_job)
            job_thread.start()  # 线程start后，不要join()，主界面才不会卡住
            # ★进入作业详情页面★
            for widget in self.nav_frame_r_widget_dict["frame"].winfo_children():
                widget.destroy()
            self.show_inspection_job_status()
            self.add_return_button()
            self.update_frame()  # 更新Frame的尺寸，并将滚动条移到最开头
        else:
            print("取消启动巡检作业")

    def proces_mouse_scroll(self, event):
        if event.delta > 0:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.nav_frame_r_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def update_frame(self):
        # 更新Frame的尺寸
        self.nav_frame_r_widget_dict["frame"].update_idletasks()
        self.nav_frame_r_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.nav_frame_r_widget_dict["frame"].winfo_width(),
                          self.nav_frame_r_widget_dict["frame"].winfo_height()))
        self.nav_frame_r_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll)
        # 滚动条移到最开头
        self.nav_frame_r_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def add_return_button(self):
        # ★★添加“返回资源列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="返回资源列表",
                                       command=lambda: self.main_window.list_resource_of_nav_frame_r_page(
                                           RESOURCE_TYPE_INSPECTION_TEMPLATE))
        button_return.bind("<MouseWheel>", self.proces_mouse_scroll)
        button_return.grid(row=self.current_row_index + 1, column=1, padx=self.padx, pady=self.pady)

    def show_inspection_job_status(self):
        # ★巡检作业详情
        label_show_inspection_job_status = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 巡检作业详情 ★★")
        label_show_inspection_job_status.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_show_inspection_job_status.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_template-名称
        label_inspection_template_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检模板名称")
        label_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_template_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                       textvariable=self.resource_info_dict["sv_name"], width=42)
        entry_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_template_name.insert(0, self.inspection_template_obj.name)  # 显示初始值，可编辑
        entry_inspection_template_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_job-名称
        label_inspection_job_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检作业名称")
        label_inspection_job_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_job_name.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_job_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_name"], width=42)
        entry_inspection_job_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_job_name.insert(0, self.current_inspection_job_obj.name)  # 显示初始值，可编辑
        entry_inspection_job_name.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_method
        label_inspection_template_execution_method = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="execution_method")
        label_inspection_template_execution_method.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_execution_method.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        execution_method_name_list = ["无", "定时执行", "周期执行", "After"]
        self.resource_info_dict["combobox_execution_method"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                            values=execution_method_name_list,
                                                                            state="readonly")
        self.resource_info_dict["combobox_execution_method"].current(self.inspection_template_obj.execution_method)
        self.resource_info_dict["combobox_execution_method"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-update_code_on_launch
        label_inspection_template_update_code_on_launch = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="运行前更新code")
        label_inspection_template_update_code_on_launch.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_update_code_on_launch.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        update_code_on_launch_name_list = ["Yes", "No"]
        self.resource_info_dict["combobox_update_code_on_launch"] = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                                                 values=update_code_on_launch_name_list,
                                                                                 state="readonly")
        self.resource_info_dict["combobox_update_code_on_launch"].current(self.inspection_template_obj.update_code_on_launch)
        self.resource_info_dict["combobox_update_code_on_launch"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-forks
        label_inspection_template_forks = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="运行线程数")
        label_inspection_template_forks.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_forks.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_forks"] = tkinter.StringVar()
        spinbox_inspection_template_forks = tkinter.Spinbox(self.nav_frame_r_widget_dict["frame"], from_=1, to=256, increment=1,
                                                            textvariable=self.resource_info_dict["sv_forks"])
        self.resource_info_dict["sv_forks"].set(self.inspection_template_obj.forks)  # 显示初始值，可编辑
        spinbox_inspection_template_forks.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_job-作业完成情况
        label_inspection_job_status = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="作业完成情况:")
        label_inspection_job_status.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_job_status.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        # ★host-列表
        inspection_host_treeview = ttk.Treeview(self.nav_frame_r_widget_dict["frame"], cursor="arrow", height=6,
                                                columns=("index", "host", "status"), show="headings")
        # 设置每一个列的宽度和对齐的方式
        inspection_host_treeview.column("index", width=60, anchor="w")
        inspection_host_treeview.column("host", width=180, anchor="w")
        inspection_host_treeview.column("status", width=100, anchor="w")
        # 设置每个列的标题
        inspection_host_treeview.heading("index", text="index", anchor="w")
        inspection_host_treeview.heading("host", text="host", anchor="w")
        inspection_host_treeview.heading("status", text="status", anchor="w")
        # 插入数据，这里需要定时刷新★★
        index = 0
        status_name_list = ["unknown", "started", "completed", "part_completed", "failed"]
        for host_oid in self.current_inspection_job_obj.unduplicated_host_oid_list:
            host_obj = self.global_info.get_host_by_oid(host_oid)
            inspection_host_treeview.insert("", index, values=(
                index, host_obj.name, status_name_list[self.current_inspection_job_obj.unduplicated_host_job_status_list[index]]))
            index += 1
        inspection_host_treeview.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)  # 定时刷新主机巡检作业状态
        # ★★更新row_index
        self.current_row_index = 6

    def refresh_host_status(self, inspection_host_treeview):
        inspection_host_treeview.delete(*inspection_host_treeview.get_children())
        # 插入数据，这里需要定时刷新★★
        index = 0
        status_name_list = ["unknown", "started", "completed", "part_completed", "failed"]
        for host_oid in self.current_inspection_job_obj.unduplicated_host_oid_list:
            host_obj = self.global_info.get_host_by_oid(host_oid)
            inspection_host_treeview.insert("", index, values=(
                index, host_obj.name, status_name_list[self.current_inspection_job_obj.unduplicated_host_job_status_list[index]]))
            index += 1
        # 只有巡检作业未完成时才刷新主机巡检作业状态，完成（包含失败）都不再去更新主机状态
        if self.current_inspection_job_obj.job_state == INSPECTION_CODE_JOB_EXEC_STATE_UNKNOWN:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)


if __name__ == '__main__':
    global_info_obj = GlobalInfo()  # 创建全局信息类，用于存储所有资源类的对象
    global_info_obj.load_all_data_from_sqlite3()  # 首先加载数据库，加载所有资源（若未指定数据库文件名称，则默认为"cofable_default.db"）
    main_window_obj = MainWindow(width=640, height=400, title='CofAble', global_info=global_info_obj)  # 创建程序主界面
    main_window_obj.show()
