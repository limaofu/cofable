#!/usr/bin/env python3
# coding=utf-8
# module name: cofable
# dependence:  cofnet  (https://github.com/limaofu/cofnet)  &  paramiko
# author: Cof-Lee
# update: 2024-02-05
# 本模块使用GPL-3.0开源协议

import io
import uuid
import time
import re
import sqlite3
import base64
import tkinter
from tkinter import messagebox
from tkinter import filedialog
from multiprocessing.dummy import Pool as ThreadPool

import paramiko

# 全局常量
COF_TRUE = 1
COF_FALSE = 0
CRED_TYPE_SSH_PASS = 0
CRED_TYPE_SSH_KEY = 1
CRED_TYPE_TELNET = 2
CRED_TYPE_FTP = 3
CRED_TYPE_REGISTRY = 4
CRED_TYPE_GIT = 5
PRIVILEGE_ESCALATION_METHOD_SU = 1
PRIVILEGE_ESCALATION_METHOD_SUDO = 2
FIRST_AUTH_METHOD_PRIKEY = 1
FIRST_AUTH_METHOD_PASSWORD = 2
CODE_SOURCE_LOCAL = 1
CODE_SOURCE_FILE = 2
CODE_SOURCE_GIT = 3
EXECUTION_METHOD_NONE = 1
EXECUTION_METHOD_AT = 2
EXECUTION_METHOD_CROND = 3
EXECUTION_METHOD_AFTER = 4
CODE_POST_WAIT_TIME_DEFAULT = 0.1  # 命令发送后等待的时间，秒
CODE_POST_WAIT_TIME_MAX_TIMEOUT_INTERVAL = 0.1
CODE_POST_WAIT_TIME_MAX_TIMEOUT_COUNT = 30
LOGIN_AUTH_TIMEOUT = 10  # 登录等待超时，秒
CODE_EXEC_METHOD_INVOKE_SHELL = 0
CODE_EXEC_METHOD_EXEC_COMMAND = 1
AUTH_METHOD_SSH_PASS = 0
AUTH_METHOD_SSH_KEY = 1
INTERACTIVE_PROCESS_METHOD_ONETIME = 1
INTERACTIVE_PROCESS_METHOD_ONCE = 1
INTERACTIVE_PROCESS_METHOD_TWICE = 2
INTERACTIVE_PROCESS_METHOD_LOOP = 3
DEFAULT_JOB_FORKS = 5  # 巡检作业时，目标主机的巡检并发数（同时巡检几台主机）
INSPECTION_CODE_JOB_EXEC_STATE_UNKNOWN = 0
INSPECTION_CODE_JOB_EXEC_STATE_STARTED = 1
INSPECTION_CODE_JOB_EXEC_STATE_FINISHED = 2
INSPECTION_CODE_JOB_EXEC_STATE_SUCCESSFUL = 3
INSPECTION_CODE_JOB_EXEC_STATE_PART_SUCCESSFUL = 4
INSPECTION_CODE_JOB_EXEC_STATE_FAILED = 5


# GUI_FOCUS_MAIN_INIT_WINDOW = 0
# GUI_FOCUS_MAIN_PROJECT_WINDOW = 1
# GUI_FOCUS_MAIN_CREDENTIAL_WINDOW = 2


# 项目，是一个全局概念，一个项目包含若干资源（认证凭据，受管主机，巡检代码，巡检模板等）
# 同一项目里的资源可互相引用/使用，不同项目之间的资源不可互用
class Project:
    def __init__(self, name='default', description='default', oid=None, create_timestamp=None):
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
        self.sqlite3_dbfile_name = self.name + ".db"  # 数据库所有数据存储在此文件中，默认数据库名称同文件名（不含.db后缀）

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
                        "create_timestamp double)"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_project where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql_list = [f"insert into tb_project (oid,name,description,create_timestamp) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"{self.create_timestamp})"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 认证凭据，telnet/ssh/sftp登录凭据，snmp团体字，container-registry认证凭据，git用户凭据，ftp用户凭据
class Credential:
    def __init__(self, name='', description='', project_oid='', cred_type=CRED_TYPE_SSH_PASS,
                 username='', password='', private_key='',
                 privilege_escalation_method=PRIVILEGE_ESCALATION_METHOD_SUDO, privilege_escalation_username='',
                 privilege_escalation_password='',
                 auth_url='', ssl_no_verify=COF_TRUE, last_modify_timestamp=0, oid=None, create_timestamp=None):
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
        self.ssl_no_verify = ssl_no_verify  # 默认为True，不校验ssl证书
        self.last_modify_timestamp = last_modify_timestamp  # <float>

    def save_to_project(self, project):
        sqlite_conn = sqlite3.connect(project.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_credential'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_credential";'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_credential  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "create_timestamp double,",
                        "cred_type int,"
                        "username varchar(128),",
                        "password varchar(256),",
                        "private_key varchar(4096),",
                        "privilege_escalation_method int,",
                        "privilege_escalation_username varchar(128),",
                        "privilege_escalation_password varchar(256),",
                        "auth_url varchar(2048),",
                        "ssl_no_verify int,",
                        "last_modify_timestamp double )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_credential where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql_list = ["insert into tb_credential (oid,",
                        "name,",
                        "description,",
                        "project_oid,",
                        "create_timestamp,",
                        "cred_type,",
                        "username,",
                        "password,",
                        "private_key,",
                        "privilege_escalation_method,",
                        "privilege_escalation_username,",
                        "privilege_escalation_password,",
                        "auth_url,",
                        "ssl_no_verify,",
                        "last_modify_timestamp ) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"{self.create_timestamp},",
                        f"{self.cred_type},",
                        f"'{self.username}',",
                        f"'{self.password}',",
                        f"'{self.private_key}',",
                        f"{self.privilege_escalation_method},",
                        f"'{self.privilege_escalation_username}',",
                        f"'{self.privilege_escalation_password}',",
                        f"'{self.auth_url}',",
                        f"{self.ssl_no_verify},",
                        f"{self.last_modify_timestamp} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 目标主机，受管主机
class Host:
    def __init__(self, name='default', description='default', project_oid='default', address='default',
                 ssh_port=22, telnet_port=23, last_modify_timestamp=0, oid=None, create_timestamp=None,
                 login_protocol='ssh', first_auth_method=FIRST_AUTH_METHOD_PRIKEY):
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
        self.credential_obj_list = []  # 元素为 Credential对象（此信息不保存到数据库）

    def add_credential(self, credential_object):  # 每台主机都会绑定一个或多个不同类型的登录/访问认证凭据
        self.credential_oid_list.append(credential_object.oid)
        self.credential_obj_list.append(credential_object)

    def save_to_project(self, project):
        sqlite_conn = sqlite3.connect(project.sqlite3_dbfile_name)  # 连接数据库文件
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
                        "login_protocol varchar(32),"
                        "first_auth_method int )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_host where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
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
                        f"'{self.login_protocol}',"
                        f"{self.first_auth_method} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_host_credential_oid_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE \
                "type"="table" and "tbl_name"="tb_host_include_credential_oid_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_include_credential_oid_list  ( host_oid varchar(36),\
                            credential_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        for cred_oid in self.credential_oid_list:
            sql = f"select * from tb_host_include_credential_oid_list where \
                    host_oid='{self.oid}' and credential_oid='{cred_oid}'"
            sqlite_cursor.execute(sql)
            if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
                sql_list = [f"insert into tb_host_include_credential_oid_list (host_oid,",
                            "credential_oid ) values ",
                            f"('{self.oid}',",
                            f"'{cred_oid}' )"]
                sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 目标主机组，受管主机组
class HostGroup:
    def __init__(self, name='default', description='default', project_oid='default', last_modify_timestamp=0, oid=None,
                 create_timestamp=None):
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
        self.host_obj_list = []  # 元素为对象（此信息不保存到数据库）
        self.host_group_obj_list = []  # 元素为对象（此信息不保存到数据库）不能包含自己

    def add_host(self, host):
        self.host_oid_list.append(host.oid)
        self.host_obj_list.append(host)

    def add_host_group(self, host_group):  # 不能包含自己
        if host_group.oid != self.oid:
            self.host_group_oid_list.append(host_group.oid)
            self.host_group_obj_list.append(host_group)
        else:
            pass

    def save_to_project(self, project):
        sqlite_conn = sqlite3.connect(project.sqlite3_dbfile_name)  # 连接数据库文件
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
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
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
        # ★查询是否有名为'tb_host_group_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_group_include_host_list  ( host_group_oid varchar(36),\
                            host_index int, host_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 每次保存host前，先删除所有host内容，再去重新插入
        sql = f"delete from tb_host_group_include_host_list where host_group_oid='{self.oid}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        host_index = 0
        for host_oid in self.host_oid_list:
            sql_list = ["insert into tb_host_group_include_host_list (host_group_oid,",
                        "host_index, host_oid ) values",
                        f"('{self.oid}',",
                        f"{host_index},",
                        f"'{host_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_host_group_include_group_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group_include_group_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_group_include_group_list  ( host_group_oid varchar(36),\
                                group_index int, group_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 每次保存group前，先删除所有group内容，再去重新插入
        sql = f"delete from tb_host_group_include_group_list where host_group_oid='{self.oid}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        group_index = 0
        for group_oid in self.host_group_oid_list:
            sql_list = ["insert into tb_host_group_include_group_list (host_group_oid,",
                        "group_index, group_oid )  values ",
                        f"('{self.oid}',",
                        f"{group_index},",
                        f"'{group_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 巡检代码
class InspectionCode:
    def __init__(self, name='default', description='default', project_oid='default',
                 code_source=CODE_SOURCE_LOCAL, last_modify_timestamp=0, oid=None, create_timestamp=None):
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

    def add_code_line(self, one_line_code):
        if isinstance(one_line_code, OneLineCode):
            one_line_code.code_index = len(self.code_list)
            self.code_list.append(one_line_code)

    def save_to_project(self, project):
        sqlite_conn = sqlite3.connect(project.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_code'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_code"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_inspection_code  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "create_timestamp double,",
                        "code_source int,",
                        "last_modify_timestamp double )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_inspection_code where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql_list = ["insert into tb_inspection_code (oid,",
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
        # ★查询是否有名为'tb_inspection_code_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_code_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = ["create table tb_inspection_code_list  ( inspection_code_oid varchar(36),",
                        "code_index int,",
                        "code_content varchar(512),",
                        "code_post_wait_time double,",
                        "need_interactive int,",
                        "interactive_question_keyword varchar(128),",
                        "interactive_answer varchar(32),",
                        "interactive_process_method int )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 每次保存代码前，先删除所有code内容，再去重新插入
        sql = f"delete from tb_inspection_code_list where inspection_code_oid='{self.oid}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        for code in self.code_list:
            sql_list = ["insert into tb_inspection_code_list (inspection_code_oid,",
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

        # 巡检模板，包含目标主机，可手动触发执行，可定时执行，可周期执行


class InspectionTemplate:
    def __init__(self, name='default', description='default', project_oid='default',
                 execution_method=EXECUTION_METHOD_NONE, execution_at_time=0,
                 execution_after_time=0, execution_crond_time='default', update_code_on_launch=COF_FALSE,
                 last_modify_timestamp=0, oid=None, create_timestamp=None, forks=DEFAULT_JOB_FORKS):
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
        self.inspection_code_oid_list = []  # 巡检代码InspectionCode对象的oid
        self.update_code_on_launch = update_code_on_launch  # <int> 是否在执行项目任务时自动更新巡检代码
        self.forks = forks
        self.launch_template_trigger_oid = ''  # <str> CronDetectionTrigger对象的oid，此信息不保存到数据库
        self.host_obj_list = []  # 元素为对象（此信息不保存到数据库）
        self.host_group_obj_list = []  # 元素为对象（此信息不保存到数据库）
        self.inspection_code_obj_list = []  # 元素为InspectionCode对象（此信息不保存到数据库）

    def add_host(self, host):
        self.host_oid_list.append(host.oid)
        self.host_obj_list.append(host)

    def add_host_group(self, host_group):
        self.host_group_oid_list.append(host_group.oid)
        self.host_group_obj_list.append(host_group)

    def add_inspection_code(self, inspection_code):
        self.inspection_code_oid_list.append(inspection_code.oid)
        self.inspection_code_obj_list.append(inspection_code)

    def save_to_project(self, project):
        sqlite_conn = sqlite3.connect(project.sqlite3_dbfile_name)  # 连接数据库文件
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
                        "forks int )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_inspection_template where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
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
                        "forks ) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"{self.execution_method},",
                        f"{self.execution_at_time},",
                        f"{self.execution_after_time},",
                        f"'{self.execution_crond_time}',",
                        f"{self.create_timestamp},",
                        f"{self.last_modify_timestamp},",
                        f"{self.update_code_on_launch},",
                        f"{self.forks} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_inspection_template_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE \
                    "type"="table" and "tbl_name"="tb_inspection_template_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = ["create table tb_inspection_template_include_host_list",
                        "( inspection_template_oid varchar(36),",
                        "host_index int,",
                        "host_oid varchar(36) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 每次保存host前，先删除所有host内容，再去重新插入
        sql = f"delete from tb_inspection_template_include_host_list where inspection_template_oid='{self.oid}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        host_index = 0
        for host_oid in self.host_oid_list:
            sql_list = ["insert into tb_inspection_template_include_host_list (inspection_template_oid,",
                        "host_index, host_oid ) values",
                        f"('{self.oid}',",
                        f"{host_index},",
                        f"'{host_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_inspection_template_include_group_list'的表★
        sql = (f'SELECT * FROM sqlite_master WHERE \
                    "type"="table" and "tbl_name"="tb_inspection_template_include_group_list"')
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = [
                "create table tb_inspection_template_include_group_list  ( inspection_template_oid varchar(36),",
                "group_index int,",
                "group_oid varchar(36) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 每次保存group前，先删除所有group内容，再去重新插入
        sql = f"delete from tb_inspection_template_include_group_list where inspection_template_oid='{self.oid}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
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
        # ★查询是否有名为'tb_inspection_template_include_inspection_code_list'的表★
        sql = (f'SELECT * FROM sqlite_master WHERE \
                    type="table" and tbl_name="tb_inspection_template_include_inspection_code_list"')
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = ["create table tb_inspection_template_include_inspection_code_list",
                        "(inspection_template_oid varchar(36), ",
                        "inspection_code_index int, ",
                        "inspection_code_oid varchar(36) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 每次保存group前，先删除所有group内容，再去重新插入
        sql = (f"delete from tb_inspection_template_include_inspection_code_list where \
                    inspection_template_oid='{self.oid}' ")
        sqlite_cursor.execute(sql)
        # 开始插入数据
        inspection_code_index = 0
        for inspection_code_oid in self.inspection_code_oid_list:
            sql_list = ["insert into tb_inspection_template_include_inspection_code_list ",
                        "( inspection_template_oid,",
                        "inspection_code_index,",
                        "inspection_code_oid ) values",
                        f"('{self.oid}',",
                        f"{inspection_code_index},",
                        f"'{inspection_code_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 巡检触发检测类，周期检查是否需要执行某巡检模板，每创建一个巡检模板就要求绑定一个巡检触发检测对象
class LaunchTemplateTrigger:
    def __init__(self, name='default', description='default', project_oid='default',
                 inspection_template_oid='uuid', last_modify_timestamp=0, oid=None, create_timestamp=None):
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

    def start_crontab_job(self):
        if self.is_time_up:
            self.start_template()
        else:
            pass

    def start_template(self):
        pass


# 执行巡检任务，一次性的，由巡检触发检测对象去创建并执行巡检工作，完成后输出日志
def find_ssh_credential(host):
    # if host.login_protocol == "ssh":
    for cred in host.credential_obj_list:
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
            pri_key = paramiko.RSAKey.from_private_key(prikey_obj)
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


def fmt_time(t):
    if t < 10:
        return "0" + str(t)
    else:
        return str(t)


def save_ssh_operator_output_to_file(ssh_operator_output_obj_list, host, inspection_template):
    localtime = time.localtime(time.time())
    timestamp_list = [str(localtime.tm_year), fmt_time(localtime.tm_mon), fmt_time(localtime.tm_mday)]
    # str(localtime.tm_hour), str(localtime.tm_min), str(localtime.tm_sec)
    timestamp = "_".join(timestamp_list)  # 年月日，例：2024_01_25
    file_name_list = [host.name, inspection_template.name, timestamp]
    file_name = "-".join(file_name_list) + '.txt'  # 一台主机的所有巡检命令输出信息都保存在一个文件里：主机名-巡检模板名-日期.txt
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


def save_ssh_operator_invoke_shell_output_to_sqlite(job_oid, ssh_operator_output_obj_list, host, inspection_code_obj,
                                                    sqlite3_dbfile_name):
    sqlite_conn = sqlite3.connect(sqlite3_dbfile_name)  # 连接数据库文件
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
                    f"job_oid='{job_oid}' and host_oid='{host.oid}'",
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
                        f"( '{job_oid}',",
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


class LaunchInspectionJob:
    def __init__(self, name='default', description='default', project=None, oid=None, create_timestamp=None,
                 inspection_template=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str> job_id
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        self.project = project  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.inspection_template = inspection_template  # InspectionTemplate对象
        self.unduplicated_host_obj_list = []  # <Host>对象，无重复项
        self.job_state = INSPECTION_CODE_JOB_EXEC_STATE_UNKNOWN
        self.job_exec_finished_host_oid_list = []
        self.job_exec_timeout_host_oid_list = []
        self.job_exec_failed_host_oid_list = []
        self.job_find_credential_timeout_host_oid_list = []

    def get_unduplicated_host_obj_from_group(self, host_group):  # 从主机组中获取非重复主机
        for host in host_group.host_obj_list:
            if host in self.unduplicated_host_obj_list:
                print(f"get_unduplicated_host_obj_from_group:重复主机：{host.name} *************")
                continue
            else:
                self.unduplicated_host_obj_list.append(host)
        for group in host_group.host_group_obj_list:
            self.get_unduplicated_host_obj_from_group(group)
        return None

    def get_unduplicated_host_obj_from_inspection_template(self):  # 从巡检模板的主机列表及主机组列表中获取非重复主机
        if self.inspection_template is None:
            print("巡检模板为空")
            return
        for host in self.inspection_template.host_obj_list:
            if host in self.unduplicated_host_obj_list:
                print(f"get_unduplicated_host_obj_from_inspection_template:重复主机：{host.name} **********")
                continue
            else:
                self.unduplicated_host_obj_list.append(host)
        for host_group in self.inspection_template.host_group_obj_list:
            self.get_unduplicated_host_obj_from_group(host_group)

    def create_ssh_operator_invoke_shell(self, host, cred):
        for inspection_code_obj in self.inspection_template.inspection_code_obj_list:  # 注意：巡检代码不去重
            if cred.cred_type == CRED_TYPE_SSH_PASS:
                auth_method = AUTH_METHOD_SSH_PASS
            else:
                auth_method = AUTH_METHOD_SSH_KEY
            # 一个<SSHOperator>对象操作一个<InspectionCode>巡检代码的所有命令
            ssh_opt = SSHOperator(hostname=host.address, port=host.ssh_port, username=cred.username,
                                  password=cred.password, private_key=cred.private_key, auth_method=auth_method,
                                  command_list=inspection_code_obj.code_list, timeout=LOGIN_AUTH_TIMEOUT)
            try:
                ssh_opt.run_invoke_shell()  # 执行巡检命令，输出信息保存在 ssh_opt.output_list里，元素为<SSHOperatorOutput>
            except paramiko.AuthenticationException as e:
                print(f"目标主机 {host.name} 登录时身份验证失败: {e}")  # 登录验证失败，则此host的所有巡检code都不再继续
                self.job_exec_failed_host_oid_list.append(host.oid)
                break
            max_timeout_index = 0
            while True:
                if max_timeout_index >= CODE_POST_WAIT_TIME_MAX_TIMEOUT_COUNT:
                    print(f"inspection_code: {inspection_code_obj.name} 已达最大超时-未完成")
                    self.job_exec_timeout_host_oid_list.append(host.oid)
                    break
                time.sleep(CODE_POST_WAIT_TIME_MAX_TIMEOUT_INTERVAL)
                max_timeout_index += 1
                if ssh_opt.is_finished:
                    print(f"inspection_code: {inspection_code_obj.name} 已执行完成")
                    self.job_exec_finished_host_oid_list.append(host.oid)
                    break
            if len(ssh_opt.output_list) != 0:
                # 输出信息保存到文件
                save_ssh_operator_output_to_file(ssh_opt.output_list, host, self.inspection_template)
                # 输出信息保存到sqlite数据库
                save_ssh_operator_invoke_shell_output_to_sqlite(self.oid, ssh_opt.output_list, host,
                                                                inspection_code_obj, self.project.sqlite3_dbfile_name)
        print(f">>>>>>>>>>>>>>>>>> 目标主机：{host.name} 已巡检完成，远程方式: ssh <<<<<<<<<<<<<<<<<<")

    def operator_job_thread(self, host_index):
        host = self.unduplicated_host_obj_list[host_index]
        print(f"\n>>>>>>>>>>>>>>>>>> 目标主机：{host.name} 开始巡检 <<<<<<<<<<<<<<<<<<")
        if host.login_protocol == "ssh":
            try:
                cred = find_ssh_credential(host)  # 查找可用的登录凭据，这里会登录一次目标主机
            except TimeoutError as e:
                print("查找可用的凭据超时，", e)
                self.job_find_credential_timeout_host_oid_list.append(host.oid)
                return
            if cred is None:
                print("Could not find correct credential")
                return
            self.create_ssh_operator_invoke_shell(host, cred)  # 开始正式作业工作，执行巡检命令，将输出信息保存到文件及数据库
        elif host.login_protocol == "telnet":
            pass
        else:
            pass

    def judge_completion_of_job(self):
        if len(self.job_exec_finished_host_oid_list) == len(self.unduplicated_host_obj_list):
            self.job_state = INSPECTION_CODE_JOB_EXEC_STATE_SUCCESSFUL
        elif len(self.job_exec_finished_host_oid_list) > 0:
            self.job_state = INSPECTION_CODE_JOB_EXEC_STATE_PART_SUCCESSFUL
        else:
            self.job_state = INSPECTION_CODE_JOB_EXEC_STATE_FAILED

    def save_to_sqlite(self, start_time, end_time):
        sqlite_conn = sqlite3.connect(self.project.sqlite3_dbfile_name)  # 连接数据库文件
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
                        f"'{self.inspection_template.oid}',",
                        f"'{self.project.oid}',",
                        f"{start_time},",
                        f"{end_time},",
                        f"{self.job_state} )"]
            print("######################## ", " ".join(sql_list))
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def start_job(self):
        print("开始巡检任务 ############################################################")
        if self.inspection_template is None:
            print("巡检模板为空，结束本次任务")
            return
        start_time = time.time()
        self.get_unduplicated_host_obj_from_inspection_template()  # ★主机去重
        print("巡检模板名称：", self.inspection_template.name)
        thread_pool = ThreadPool(processes=self.inspection_template.forks)  # 创建线程池
        thread_pool.map(self.operator_job_thread, range(len(self.unduplicated_host_obj_list)))  # ★线程池调用巡检作业函数
        thread_pool.close()
        thread_pool.join()
        end_time = time.time()
        print("巡检任务完成 ############################################################")
        print(f"巡检并发数为{self.inspection_template.forks}")
        print("用时 {:<6.4f} 秒".format(end_time - start_time))
        # 将作业信息保存到数据库，从数据库读取出来时，不可重构为一个<LaunchInspectionJob>对象
        self.judge_completion_of_job()  # 先判断作业完成情况
        self.save_to_sqlite(start_time, end_time)


def load_projects_from_dbfile(dbfilepath):
    # input <str> , output <list>
    # 输入数据库文件名，输出项目对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_project'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_project"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    sql = f"select * from tb_project"
    sqlite_cursor.execute(sql)
    search_result = sqlite_cursor.fetchall()
    obj_list = []
    for obj_info_tuple in search_result:
        obj = Project(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                      create_timestamp=obj_info_tuple[3])
        obj_list.append(obj)
    sqlite_cursor.close()
    sqlite_conn.commit()  # 保存，提交
    sqlite_conn.close()  # 关闭数据库连接
    return obj_list


def load_credentials_from_dbfile(dbfilepath):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_credential'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_credential"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
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
                         private_key=obj_info_tuple[8],
                         privilege_escalation_method=obj_info_tuple[9],
                         privilege_escalation_username=obj_info_tuple[10],
                         privilege_escalation_password=obj_info_tuple[11],
                         auth_url=obj_info_tuple[12],
                         ssl_no_verify=obj_info_tuple[13],
                         last_modify_timestamp=obj_info_tuple[14])
        obj_list.append(obj)
    sqlite_cursor.close()
    sqlite_conn.commit()  # 保存，提交
    sqlite_conn.close()  # 关闭数据库连接
    return obj_list


def load_hosts_from_dbfile(dbfilepath):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_host'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
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
                   first_auth_method=obj_info_tuple[10])
        obj_list.append(obj)
    sqlite_cursor.close()
    sqlite_conn.commit()  # 保存，提交
    sqlite_conn.close()  # 关闭数据库连接
    load_hosts_include_creds_from_dbfile(dbfilepath, obj_list)
    return obj_list


def load_hosts_include_creds_from_dbfile(dbfilepath, host_list):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_host_include_credential_oid_list'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_include_credential_oid_list"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    for host in host_list:
        sql = f"select * from tb_host_include_credential_oid_list where host_oid='{host.oid}'"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            host.credential_oid_list.append(obj_info_tuple[1])


def load_host_groups_from_dbfile(dbfilepath):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_host_group'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_group"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    sql = f"select * from tb_host_group"
    sqlite_cursor.execute(sql)
    search_result = sqlite_cursor.fetchall()
    obj_list = []
    for obj_info_tuple in search_result:
        # print('tuple: ', obj_info_tuple)
        obj = HostGroup(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                        project_oid=obj_info_tuple[3], create_timestamp=obj_info_tuple[4],
                        last_modify_timestamp=obj_info_tuple[5])
        obj_list.append(obj)
    sqlite_cursor.close()
    sqlite_conn.commit()  # 保存，提交
    sqlite_conn.close()  # 关闭数据库连接
    load_host_groups_include_hosts_from_dbfile(dbfilepath, obj_list)
    load_host_groups_include_groups_from_dbfile(dbfilepath, obj_list)
    return obj_list


def load_host_groups_include_hosts_from_dbfile(dbfilepath, host_group_list):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_host_group_include_host_list'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_group_include_host_list"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    for host_group in host_group_list:
        sql = f"select * from tb_host_group_include_host_list where host_group_oid='{host_group.oid}'"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            host_group.host_oid_list.append(obj_info_tuple[2])


def load_host_groups_include_groups_from_dbfile(dbfilepath, host_group_list):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_host_group_include_group_list'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_host_group_include_group_list"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    for host_group in host_group_list:
        sql = f"select * from tb_host_group_include_group_list where host_group_oid='{host_group.oid}'"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            host_group.host_group_oid_list.append(obj_info_tuple[2])


def load_inspection_codes_from_dbfile(dbfilepath):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_inspection_code'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_code"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    sql = f"select * from tb_inspection_code"
    sqlite_cursor.execute(sql)
    search_result = sqlite_cursor.fetchall()
    obj_list = []
    for obj_info_tuple in search_result:
        # print('tuple: ', obj_info_tuple)
        obj = InspectionCode(oid=obj_info_tuple[0], name=obj_info_tuple[1], description=obj_info_tuple[2],
                             project_oid=obj_info_tuple[3], create_timestamp=obj_info_tuple[4],
                             code_source=obj_info_tuple[5],
                             last_modify_timestamp=obj_info_tuple[6])
        obj_list.append(obj)
    sqlite_cursor.close()
    sqlite_conn.commit()  # 保存，提交
    sqlite_conn.close()  # 关闭数据库连接
    load_inspection_code_lists_from_dbfile(dbfilepath, obj_list)
    return obj_list


def load_inspection_code_lists_from_dbfile(dbfilepath, inspection_code_list):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_inspection_code_list'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_code_list"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    for inspection_code in inspection_code_list:
        sql = f"select * from tb_inspection_code_list where inspection_code_oid='{inspection_code.oid}'"
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


def load_inspection_templates_from_dbfile(dbfilepath):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_inspection_template'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
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
                                 forks=obj_info_tuple[11])
        obj_list.append(obj)
    sqlite_cursor.close()
    sqlite_conn.commit()  # 保存，提交
    sqlite_conn.close()  # 关闭数据库连接
    load_inspection_templates_include_hosts_from_dbfile(dbfilepath, obj_list)
    load_inspection_templates_include_groups_from_dbfile(dbfilepath, obj_list)
    load_inspection_templates_include_codes_from_dbfile(dbfilepath, obj_list)
    return obj_list


def load_inspection_templates_include_hosts_from_dbfile(dbfilepath, inspection_template_list):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_inspection_template_include_host_list'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template_include_host_list"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    for inspection_template in inspection_template_list:
        sql = f"select * from tb_inspection_template_include_host_list where \
                inspection_template_oid='{inspection_template.oid}'"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            inspection_template.host_oid_list.append(obj_info_tuple[2])


def load_inspection_templates_include_groups_from_dbfile(dbfilepath, inspection_template_list):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_inspection_template_include_group_list'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template_include_group_list"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    for inspection_template in inspection_template_list:
        sql = f"select * from tb_inspection_template_include_group_list where \
                inspection_template_oid='{inspection_template.oid}'"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            inspection_template.host_group_oid_list.append(obj_info_tuple[2])


def load_inspection_templates_include_codes_from_dbfile(dbfilepath, inspection_template_list):
    # input <str> , output <list>
    # 输入数据库文件名，输出对象列表
    sqlite_conn = sqlite3.connect(dbfilepath)  # dbfilepath is <str> 连接数据库文件，若文件不存在则新建
    sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
    # ★查询是否有名为'tb_inspection_template_include_inspection_code_list'的表★
    sql = 'SELECT * FROM sqlite_master WHERE type="table" \
                and tbl_name="tb_inspection_template_include_inspection_code_list"'
    sqlite_cursor.execute(sql)
    result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
    print("exist tables: ", result)
    # 若未查询到有此表，则返回None
    if len(result) == 0:
        return None
    # 读取数据
    for inspection_template in inspection_template_list:
        sql = f"select * from tb_inspection_template_include_group_list where \
                inspection_template_oid='{inspection_template.oid}'"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            inspection_template.inspection_code_oid_list.append(obj_info_tuple[2])


class OneLineCode:
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


def process_code_interactive(code, output_last_line, ssh_shell, output, second_time=False):
    ret = re.search(code.interactive_question_keyword, output_last_line, re.I)
    if ret is not None:  # 如果匹配上需要交互的提问判断字符串
        print(f"★★匹配到交互关键字 {ret} ，执行交互回答:")
        ssh_shell.send(code.interactive_answer.encode('utf8'))
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
        if code.interactive_process_method == INTERACTIVE_PROCESS_METHOD_LOOP and len(
                interactive_output_str_lines) != 0:
            process_code_interactive(code, interactive_output_str_lines[interactive_output_last_line_index],
                                     ssh_shell, output)
        if code.interactive_process_method == INTERACTIVE_PROCESS_METHOD_TWICE and len(
                interactive_output_str_lines) != 0:
            process_code_interactive(code, interactive_output_str_lines[interactive_output_last_line_index],
                                     ssh_shell, output, second_time=True)
    else:
        return


class SSHOperator:  # 一个<SSHOperator>对象操作一个<InspectionCode>巡检代码的所有命令
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
        self.command_list = command_list  # 元素为 <OneLineCode>对象
        self.is_finished = False  # False表示命令未执行完成
        self.output_list = []  # 元素类型为 <SSHOperatorOutput>，一条执行命令<OneLineCode>只产生一个output元素

    def run_invoke_shell(self):
        if self.command_list is None:
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
                prikey_obj = io.StringIO(self.private_key)
                pri_key = paramiko.RSAKey.from_private_key(prikey_obj)
                print("使用ssh_key密钥登录 ##########################")
                ssh_client.connect(hostname=self.hostname, port=self.port, username=self.username,
                                   pkey=pri_key, timeout=self.timeout)
            else:
                pass
        except paramiko.AuthenticationException as e:
            # print(f"Authentication Error: {e}")
            raise e
        time.sleep(CODE_POST_WAIT_TIME_DEFAULT)
        ssh_shell = ssh_client.invoke_shell()  # 创建一个交互式shell
        try:
            recv = ssh_shell.recv(65535)  # 获取登录后的输出信息，此时未执行任何命令
        except Exception as e:
            print(e)
            return
        # 创建命令输出对象<SSHOperatorOutput>，一条命令对应一个<SSHOperatorOutput>对象
        # invoke_shell_output_str_list = recv.decode('utf8').split('\r\n')
        # invoke_shell_output_str = '\n'.join(invoke_shell_output_str_list)  # 这与前面一行共同作用是去除'\r'
        invoke_shell_output_str = recv.decode('utf8').replace('\r', '')
        output = SSHOperatorOutput(code_index=-1, code_exec_method=CODE_EXEC_METHOD_INVOKE_SHELL,
                                   invoke_shell_output_str=invoke_shell_output_str)
        self.output_list.append(output)  # 刚登录后的输出信息保存到output对象里
        print("登录后输出内容如下 #############################################")
        print(invoke_shell_output_str)
        cmd_index = 0
        for code in self.command_list:  # 开始执行正式命令
            if not isinstance(code, OneLineCode):
                return
            ssh_shell.send(code.code_content.strip().encode('utf8'))
            ssh_shell.send("\n".encode('utf8'))  # 命令strip()后，不带\n换行，需要额外发送一个换行符
            time.sleep(code.code_post_wait_time)  # 发送完命令后，要等待系统回复
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
                                       code_content=code.code_content, invoke_shell_output_str=invoke_shell_output_str,
                                       invoke_shell_output_last_line=output_last_line)
            self.output_list.append(output)  # 命令输出结果保存到output对象里
            print(f"$$ 命令{cmd_index} $$ 输出结果如下 #############################################")
            print(invoke_shell_output_str)
            print(f"命令输出最后一行（shell提示符，不带换行符的）为:  {output_last_line.encode('utf8')}")  # 提示符末尾有个空格
            if code.need_interactive:  # 命令如果有交互，则判断交互提问关键词
                process_code_interactive(code, output_last_line, ssh_shell, output)
            cmd_index += 1
        ssh_shell.close()
        ssh_client.close()
        self.is_finished = True

    def exec_command(self):
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


def claer_tkinter_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def claer_tkinter_window(window):
    for widget in window.winfo_children():
        widget.destroy()


class MainWindow:
    def __init__(self, width=640, height=400, title='', project=None):
        self.title = title
        self.width = width
        self.height = height
        self.position = "480x320+100+100"
        self.resizable = True  # True 表示宽度和高度可由用户手动调整
        self.minsize = (480, 320)
        self.maxsize = (1920, 1080)
        self.background = "#3A3A3A"  # 设置背景色，RGB
        self.window_obj = tkinter.Tk()  # 创建窗口对象
        self.screen_width = self.window_obj.winfo_screenwidth()
        self.screen_height = self.window_obj.winfo_screenheight()
        self.win_pos_x = self.screen_width // 2 - self.width // 2
        self.win_pos_y = self.screen_height // 2 - self.height // 2
        self.win_pos = f"{self.width}x{self.height}+{self.win_pos_x}+{self.win_pos_y}"
        self.nav_frame_l_width = int(self.width * 0.2)
        self.nav_frame_r_width = int(self.width * 0.8)
        # self.gui_focus = GUI_FOCUS_MAIN_INIT_WINDOW
        self.current_project = project
        self.about_info = "CofAble，自动化巡检平台，版本: v1.0\n本软件使用GPL-v3.0协议开源，作者: Cof-Lee"

    def click_menu_button_project(self):
        # messagebox.showinfo("消息框名称", "这是消息框内容")
        # self.gui_focus = GUI_FOCUS_MAIN_PROJECT_WINDOW
        self.load_nav_frame_r_project_display()
        # self.window_obj.after(0, self.refresh_window)

    def click_menu_button_credential(self):
        # messagebox.showinfo("消息框名称", "这是消息框内容")
        # self.gui_focus = GUI_FOCUS_MAIN_CREDENTIAL_WINDOW
        self.load_nav_frame_r_credential_display()

    def create_nav_frame_l(self):  # 创建导航框架1
        nav_frame_l = tkinter.Frame(self.window_obj, bg="green", width=self.nav_frame_l_width, height=self.height)
        nav_frame_l.grid_propagate(False)
        nav_frame_l.pack_propagate(False)
        nav_frame_l.grid(row=0, column=0)
        # 在框架1中添加功能按钮
        # claer_tkinter_frame(frame1)
        label_current_time = tkinter.Label(nav_frame_l, text=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        if self.current_project is None:
            label2_content = "当前无项目"
        else:
            label2_content = "当前项目-" + self.current_project.name
        label2 = tkinter.Label(nav_frame_l, text=label2_content, width=self.nav_frame_l_width, height=2)
        label_current_time.pack(padx=2, pady=2)
        label_current_time.after(1000, self.refresh_label_current_time, label_current_time)
        label2.pack(padx=2, pady=2)
        menu_button_project = tkinter.Button(nav_frame_l, text="Project项目", width=self.nav_frame_l_width, height=2,
                                             bg="#aaaaaa", command=self.click_menu_button_project)
        menu_button_project.pack(padx=2, pady=2)
        menu_button_credential = tkinter.Button(nav_frame_l, text="Credentials凭据", width=self.nav_frame_l_width,
                                                height=2, bg="#aaaaaa",
                                                command=self.click_menu_button_credential)
        menu_button_credential.pack(padx=2, pady=2)
        menu_button2 = tkinter.Button(nav_frame_l, text="Host主机管理", width=self.nav_frame_l_width,
                                      bg="#bbbbaa")
        menu_button2.pack(padx=2, pady=2)
        menu_button3 = tkinter.Button(nav_frame_l, text="Inspection巡检代码", width=self.nav_frame_l_width,
                                      bg="#f1f111")
        menu_button3.pack(padx=2, pady=2)
        menu_button4 = tkinter.Button(nav_frame_l, text="Template巡检作业模板", width=self.nav_frame_l_width,
                                      bg="#acada3")
        menu_button4.pack(padx=2, pady=2)

    def click_button_create_project(self):
        # 更新导航框架2
        nav_frame_r = self.window_obj.winfo_children()[2]
        nav_frame_r.__setitem__("bg", "green")
        # 在框架2中添加控件
        claer_tkinter_frame(nav_frame_r)

    def load_nav_frame_r_project_display(self):
        # claer_tkinter_window(self.window_obj)
        # 创建导航框架1
        # self.create_nav_frame_l()
        # 更新导航框架2
        nav_frame_r = self.window_obj.winfo_children()[2]
        nav_frame_r.__setitem__("bg", "gray")
        # 在框架2中添加控件
        claer_tkinter_frame(nav_frame_r)
        button_create_project = tkinter.Button(nav_frame_r, text="创建项目", command=self.click_button_create_project)
        button_create_project.grid(row=0, column=1)

    def load_nav_frame_r_credential_display(self):
        # claer_tkinter_window(self.window_obj)
        # 创建导航框架1
        # self.create_nav_frame_l()
        # 更新导航框架2
        nav_frame_r = self.window_obj.winfo_children()[2]
        nav_frame_r.__setitem__("bg", "yellow")
        # 在框架2中添加控件
        claer_tkinter_frame(nav_frame_r)
        button_2 = tkinter.Button(nav_frame_r, text="凭据")
        button_2.pack()

    def load_main_window_init_widget(self):  # 加载主界面初始化界面控件
        claer_tkinter_window(self.window_obj)
        # 加载菜单项
        self.load_menu_bar()
        # 创建导航框架1
        self.create_nav_frame_l()
        # 创建导航框架2
        nav_frame_r = tkinter.Frame(self.window_obj, bg="blue", width=self.nav_frame_r_width, height=self.height)
        nav_frame_r.grid_propagate(False)
        nav_frame_r.pack_propagate(False)
        nav_frame_r.grid(row=0, column=1)
        # 在框架2中添加控件
        # claer_tkinter_frame(frame2)
        button_2 = tkinter.Button(nav_frame_r, text="按钮2")
        button_2.pack()

    def refresh_label_current_time(self, label):
        label.__setitem__('text', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        # 继续调用回调函数更新window
        self.window_obj.after(1000, self.refresh_label_current_time, label)

    def click_menu_about(self):
        messagebox.showinfo("About", self.about_info)

    def click_menu_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not file_path:
            print("not choose a file")
        else:
            print(file_path)

    def load_menu_bar(self):
        menu_bar = tkinter.Menu(self.window_obj)  # 创建一个菜单，做菜单栏
        menu_file = tkinter.Menu(menu_bar, tearoff=1)  # 创建一个菜单，分窗，表示此菜单可拉出来变成一个可移动的独立弹窗
        menu_about = tkinter.Menu(menu_bar, tearoff=0, activebackground="green", activeforeground="white",
                                  background="white", foreground="black")  # 创建一个菜单，不分窗
        menu_file.add_command(label="File", command=self.click_menu_file)
        menu_about.add_command(label="About", command=self.click_menu_about)
        menu_bar.add_cascade(label="File", menu=menu_file)
        menu_bar.add_cascade(label="Help", menu=menu_about)
        self.window_obj.config(menu=menu_bar)

    def reload_current_resized_window(self, event):  # 监听窗口大小变化事件，自动更新窗口内控件大小
        if event:
            if self.window_obj.winfo_width() == self.width and self.window_obj.winfo_height() == self.height:
                return
            else:
                self.width = self.window_obj.winfo_width()
                self.height = self.window_obj.winfo_height()
                print("size changed")
                self.window_obj.__setitem__('width', self.width)
                self.window_obj.__setitem__('height', self.height)
                self.window_obj.winfo_children()[1].__setitem__('width', self.width * 0.2)
                self.window_obj.winfo_children()[1].__setitem__('height', self.height)
                self.window_obj.winfo_children()[2].__setitem__('width', self.width * 0.8)
                self.window_obj.winfo_children()[2].__setitem__('height', self.height)

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
        self.load_main_window_init_widget()
        print(f"当前window有{len(self.window_obj.winfo_children())}个子控件")
        for widget in self.window_obj.winfo_children():
            print(type(widget))
            print(widget)
        # 监听窗口大小变化事件，自动更新窗口内控件大小
        self.window_obj.bind('<Configure>', self.reload_current_resized_window)
        # 运行窗口主循环
        self.window_obj.mainloop()
