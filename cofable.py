#!/usr/bin/env python3
# coding=utf-8
# module name: cofable
# external_dependencies:  cofnet (https://github.com/limaofu/cofnet)  &  paramiko  &  schedule  &  pyglet
# author: Cof-Lee
# start_date: 2024-01-17
# this module uses the GPL-3.0 open source protocol
# update: 2024-04-18

"""
开发日志：
★. 执行命令时进行判断回复                                                           2024年1月23日 基本完成
★. 登录凭据的选择与多次尝试各同类凭据（当同类型凭据有多个时），只选择第一个能成功登录的cred     2024年1月23日 完成
★. ssh密码登录，ssh密钥登录                                                        2024年1月23日 完成
★. 所有输出整理到txt文件                                                           2024年1月24日 完成
★. 所有输出根据模板设置，确认是否自动保存到txt文件以及文件名风格                           2024年3月4日 完成
★. 使用多线程，每台主机用一个线程去巡检，并发几个线程                                    2024年1月25日 完成
★. 巡检作业执行完成情况的统计，执行完成，连接超时，认证失败                               2024年1月28日 基本完成
★. 程序运行后，所有类的对象都要分别加载到一个全局列表里                                  已完成
★. 巡检命令输出保存到数据库                                                         2024年1月27日 基本完成
★. 定时/周期触发巡检模板作业                                                        2024年3月14日 定时的已完成
★. 本次作业命令输出与最近一次（上一次）输出做对比
★. 巡检命令输出做基础信息提取与判断并触发告警，告警如何通知人类用户？
★. Credential密钥保存时，会有换行符，sql语句不支持，需要修改，已将密钥字符串转为base64      2024年2月25日 完成
★. 主机 允许添加若干条ip，含ip地址范围
★. 巡检命令中有sleep N 之类的命令时，要判断是否完成，根据shell提示符进行判断
★. 编辑或创建巡检代码时，要求能设置每条命令的 交互回复及其他细节                           已完成
★. 没有创建项目时，就创建其他资源，要生成默认的项目，名为default的项目                     2024年3月7日 完成
★. shell通道设置字符界面宽度及长度                                                  2024年3月8日 完成
★. 输出巡检实时状态，及进度展示                                                      2024年3月15日 完成
★. 更新资源名称时，要检查新名称是否和已存在的同类资源名称重复                              2024年3月15日 完成
★. 巡检前进行ping检测及tcp端口连通检测
★. 查看历史巡检作业日志时，如果巡检模板已更改，则显示的是更改后对应的输出，而不是更改前的，这个需要改进，
    对历史巡检模板做一个快照，展示历史作业日志时按旧的资源来显示
★. 支持工作流，一个工作流包含多个巡检模板，依次进行，可进行分支判断
★. 在host_job_item的text界面看巡检输出信息，不全，有很多缺失，                           2024年3月14日 已解决
    原因是显示是未遍历SSHOperatorOutput.interactive_output_bytes_list
★. 主机命令在线批量执行，在“主机组”界面，对这一组主机在线下发命令
★. 首次登录后，对输出进行判断，有的设备首次登录后会要求改密码，或者长时间未登录的设备要求修改密码
★. 不同巡检线程都去读写sqlite3数据库文件时，报错了，得加个锁                               2024年3月23日 完成
★. 在vt100终端里实现了 光标的左右移动及插入/删除字符                                     2024年3月23日 完成
★. 实现 vt100终端的 普通输出 与 应用输出模式的切换                                      2024年3月27日 完成
★. 实现 复制会话日志到文件，以及在会话中查找字符串                                        2024年3月29日 完成
★. 根据字体大小，获取单个字（半角）的宽高大小，方便调整Text的宽度及高度                      2024年3月30日 完成
★. 支持设置主机的字符集，如utf8,gbk等  默认使用utf8
★. 在向Terminal终端会话粘贴内容时，如果内容有多行，需要弹出确认框，用户确认才发送要粘贴的内容    2024年4月3日 完成
★. 支持用户自定义高亮字符设置（着色方案），支持正则表达式匹配并设置显示样式，每台主机可单独设置着色方案    2024年4月6日 完成
★. 优化了vt100输出显示逻辑，先输出内容，后上色（系统自带的颜色属性）                        2024年4月9日 完成
★. 修复了tkinter.Text组件的索引操作错误导致的闪退问题，以及引入结束线程机制，防止内存泄露      2024年4月12日 完成
★. 处理用户自定义配色方案时，需要使用多线程，速度才够快                                    2024年4月16日 完成
★. 优化输出逻辑，提升显示速度，如 TerminalFrontend.app_mode_print_all 这个函数          2024年4月17日 完成

资源操作逻辑：
★创建-资源        CreateResourceInFrame.show()  →  SaveResourceInMainWindow.save()
★列出-资源列表     ListResourceInFrame.show()
★列出-作业列表     ListInspectionJobInFrame.show()
★查看-资源        ViewResourceInFrame.show()
★编辑-资源        EditResourceInFrame.show()    →  UpdateResourceInFrame.update()
★删除-资源        DeleteResourceInFrame.show()

巡检流程：
★列出-巡检模板列表   ListResourceInFrame.show
                   触发↓
★启动-巡检模板      StartInspectionTemplateInFrame.start()  →  StartInspectionTemplateInFrame.show_inspection_job_status()
                   1级子线程|→ LaunchInspectionJob.start_job()                                  ←|查询状态
                             2级子线程 |→operator_job_thread()                                   |
                                      3级子线程 |→SSHOperator.run_invoke_shell()                 |
★列出-作业列表      ListInspectionJobInFrame.show()                                             ←|退出作业详情
                                            ↓查看某个作业详情
                  ViewInspectionJobInFrame.show_inspection_job_status()
                                            ↓点击单台主机
                  ViewInspectionJobInFrame.view_inspection_host_item()
"""

import io
import os
import threading
import uuid
import time
import re
import sqlite3
import base64
import sched
import queue
import struct
import gc
import ctypes
import tkinter
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from tkinter import font
from tkinter import colorchooser
from multiprocessing.dummy import Pool as ThreadPool
from concurrent.futures import ThreadPoolExecutor
# external_dependencies:
import paramiko
import pyglet
import pyperclip

# import schedule

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
CODE_POST_WAIT_TIME_DEFAULT = 0.2  # 命令发送后等待的时间，秒，这里不能为0
MAX_INTERACTIVE_COUNT = 5000  # 最大交互处理次数，在 SSHOperator.process_code_interactive()里使用
MAX_EXEC_WAIT_COUNT = 10000  # 判断巡检线程超时最大等待次数，此参数乘以CODE_POST_WAIT_TIME_DEFAULT为等待超时时间
LOGIN_AUTH_TIMEOUT = 30  # 登录等待超时，秒
CODE_EXEC_METHOD_INVOKE_SHELL = 0
CODE_EXEC_METHOD_EXEC_COMMAND = 1
AUTH_METHOD_SSH_PASS = 0
AUTH_METHOD_SSH_KEY = 1
INTERACTIVE_PROCESS_METHOD_ONETIME = 0
INTERACTIVE_PROCESS_METHOD_ONCE = 0
INTERACTIVE_PROCESS_METHOD_TWICE = 1
INTERACTIVE_PROCESS_METHOD_LOOP = 2
DEFAULT_JOB_FORKS = 5  # 巡检作业时，目标主机的巡检并发数（同时巡检几台主机）
# 巡检作业状态
INSPECTION_JOB_EXEC_STATE_UNKNOWN = 0
INSPECTION_JOB_EXEC_STATE_STARTED = 1
INSPECTION_JOB_EXEC_STATE_COMPLETED = 2
INSPECTION_JOB_EXEC_STATE_PART_COMPLETED = 3
INSPECTION_JOB_EXEC_STATE_FAILED = 4
FIND_CREDENTIAL_STATUS_SUCCEED = 0
FIND_CREDENTIAL_STATUS_TIMEOUT = 1
FIND_CREDENTIAL_STATUS_FAILED = 2
RESOURCE_TYPE_PROJECT = 0
RESOURCE_TYPE_CREDENTIAL = 1
RESOURCE_TYPE_HOST = 2
RESOURCE_TYPE_HOST_GROUP = 3
RESOURCE_TYPE_INSPECTION_CODE_BLOCK = 4
RESOURCE_TYPE_INSPECTION_TEMPLATE = 5
RESOURCE_TYPE_INSPECTION_JOB = 6
RESOURCE_TYPE_CUSTOM_SCHEME = 7
OUTPUT_FILE_NAME_STYLE_HOSTNAME = 0
OUTPUT_FILE_NAME_STYLE_HOSTNAME_DATE = 1
OUTPUT_FILE_NAME_STYLE_HOSTNAME_DATE_TIME = 2
OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME = 3
OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME_DATE = 4
OUTPUT_FILE_NAME_STYLE_DATE_DIR__HOSTNAME_DATE_TIME = 5
LOGIN_PROTOCOL_SSH = 0
LOGIN_PROTOCOL_TELNET = 1
# vt100终端的默认宽度和高度
SHELL_TERMINAL_WIDTH = 140
SHELL_TERMINAL_HEIGHT = 48
# vt100终端tag_config类型
TAG_CONFIG_TYPE_FONT = 0
TAG_CONFIG_TYPE_COLOR = 1
TAG_CONFIG_TYPE_FONT_AND_COLOR = 2
TAG_CONFIG_TYPE_SCREEN = 3
TAG_CONFIG_TYPE_CURSOR = 4
# vt100终端tag_config_record里的字体类型
FONT_TYPE_NORMAL = 0
FONT_TYPE_BOLD = 1
FONT_TYPE_ITALIC = 2
FONT_TYPE_BOLD_ITALIC = 3
VT100_TERMINAL_MODE_NORMAL = 0
VT100_TERMINAL_MODE_APP = 1
# 调用某对象的发起对象类型
CALL_BACK_CLASS_CREATE_RESOURCE = 0
CALL_BACK_CLASS_EDIT_RESOURCE = 1
CALL_BACK_CLASS_LIST_RESOURCE = 2
# 一个终端会话的当前所处模式，显示的Text类型
CURRENT_TERMINAL_TEXT_NORMAL = 0
CURRENT_TERMINAL_TEXT_APP = 1


def cofable_stop_thread(thread):
    """
    结束线程，如果线程里有time.sleep(n)之类的操作，则需要等待这个时长之后，才会结束此线程
    即此方法无法立即结束sleep及其他阻塞函数导致的休眼线程，得等线程获得响应时才结束它
    raises the exception, performs cleanup if needed
    注意：本函数会抛出一个SystemError异常，外部调用时需要处理此异常
    """
    if thread is None:
        raise ValueError("cofable_stop_thread: thread obj is None")
    thread_id = ctypes.c_long(thread.ident)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
    # 正常结束线程时会返回数值1
    if res == 0:
        raise ValueError("cofable_stop_thread: invalid thread id")
    elif res != 1:
        # 如果返回的值不为0，也不为1，则 you're in trouble
        # if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, None)
        raise SystemError("cofable_stop_thread: PyThreadState_SetAsyncExc failed")


def cofable_stop_thread_silently(thread):
    """
    结束线程，如果线程里有time.sleep(n)之类的操作，则需要等待这个时长之后，才会结束此线程
    即此方法无法立即结束sleep及其他阻塞函数导致的休眼线程，得等线程获得响应时才结束它
    本函数不会抛出异常
    """
    if thread is None:
        print("cofable_stop_thread_silently: thread obj is None")
        return
    thread_id = ctypes.c_long(thread.ident)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
    # 正常结束线程时会返回数值1
    if res == 0:
        print("cofable_stop_thread_silently: invalid thread id")
    elif res == 1:
        print("cofable_stop_thread_silently: thread stopped")
    else:
        # 如果返回的值不为0，也不为1，则 you're in trouble
        # if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, None)
        print("cofable_stop_thread_silently: PyThreadState_SetAsyncExc failed")


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
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项记录，则创建此项记录 ★★
            sql_list = [f"insert into tb_project (oid,name,description,create_timestamp,last_modify_timestamp) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"{self.create_timestamp},",
                        f"{self.last_modify_timestamp} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项记录，则更新此项记录 ★★
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
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项记录，则创建此项记录 ★★
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
        else:  # ★★ 若查询到有此项记录，则更新此项记录 ★★
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
    目标主机，受管主机，巡检操作对象
    """

    def __init__(self, name='default', description='default', project_oid='default', address='default',
                 ssh_port=22, telnet_port=23, last_modify_timestamp=0, oid=None, create_timestamp=None,
                 login_protocol=LOGIN_PROTOCOL_SSH, first_auth_method=FIRST_AUTH_METHOD_PRIKEY,
                 custome_tag_config_scheme_oid='', global_info=None):
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
        self.custome_tag_config_scheme_oid = custome_tag_config_scheme_oid  # <str> 为<CustomeTagConfigScheme>对象的oid
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
                        "first_auth_method int,",
                        "custome_tag_config_scheme_oid varchar(36) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_host where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项记录，则创建此项记录 ★★
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
                        "first_auth_method,",
                        "custome_tag_config_scheme_oid ) values",
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
                        f"{self.first_auth_method},",
                        f"'{self.custome_tag_config_scheme_oid}' )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项记录，则更新此项记录 ★★
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
                        f"first_auth_method={self.first_auth_method},",
                        f"custome_tag_config_scheme_oid='{self.custome_tag_config_scheme_oid}'",
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
            sql = f"select * from tb_host_include_credential_oid_list where host_oid='{self.oid}' and credential_oid='{cred_oid}'"
            sqlite_cursor.execute(sql)
            if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项记录，则创建此项记录
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
               login_protocol=None, first_auth_method=None, custome_tag_config_scheme_oid=None, global_info=None):
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
        if custome_tag_config_scheme_oid is not None:
            self.custome_tag_config_scheme_oid = custome_tag_config_scheme_oid
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
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项记录，则创建此项记录 ★★
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
        else:  # ★★ 若查询到有此项记录，则更新此项记录 ★★
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
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项记录，则创建此项记录 ★★
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
        else:  # ★★ 若查询到有此项记录，则更新此项记录 ★★
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
                        "code_content varchar(2048),",
                        "code_post_wait_time double,",
                        "need_interactive int,",
                        "interactive_question_keyword varchar(512),",
                        "interactive_answer varchar(512),",
                        "interactive_process_method int,",
                        "description varchar(2048)",
                        " )"]
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
                        "interactive_process_method,",
                        "description",
                        " ) values",
                        f"( '{self.oid}',",
                        f"{code.code_index},",
                        f"'{code.code_content}',",
                        f"{code.code_post_wait_time},",
                        f"{code.need_interactive},",
                        f"'{code.interactive_question_keyword}',",
                        f"'{code.interactive_answer}',",
                        f"{code.interactive_process_method},",
                        f"'{code.description}'",
                        " )"]
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
    巡检模板，包含目标主机，巡检代码段。可手动触发执行，可定时执行，可周期执行
    每创建一个<InspecionTemplate>巡检模板 就要求绑定一个<LaunchTemplateTrigger>巡检触发检测对象
    """

    def __init__(self, name='default', description='default', project_oid='default',
                 execution_method=EXECUTION_METHOD_NONE, execution_at_time=0.0,
                 execution_after_time=0.0, execution_crond_time='default', update_code_on_launch=COF_FALSE,
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
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项记录，则创建此项记录 ★★
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
        else:  # ★★ 若查询到有此项记录，则更新此项记录 ★★
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

    def __init__(self, name='', description='', inspection_template_obj=None, last_modify_timestamp=0.0, oid=None, create_timestamp=None,
                 global_info=None):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str>
        else:
            self.oid = oid
        self.name = name  # <str>
        self.description = description  # <str>
        if inspection_template_obj is None:
            self.project_oid = ''  # <str>
        else:
            self.project_oid = inspection_template_obj.project_oid  # <str>
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float>
        else:
            self.create_timestamp = create_timestamp
        self.inspection_template_obj = inspection_template_obj  # <InspectionTemplate>
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.is_time_up = False
        self.global_info = global_info

    def start_crond_job(self):  # 入口函数
        if self.inspection_template_obj.execution_method == EXECUTION_METHOD_AT:
            self.start_template_at()
        elif self.inspection_template_obj.execution_method == EXECUTION_METHOD_AFTER:
            self.start_template_after()
        elif self.inspection_template_obj.execution_method == EXECUTION_METHOD_CROND:
            self.start_template_crond()
        else:
            pass

    def existed_uncompleted_inspection_job(self):
        existed_inspection_job_obj_list = self.global_info.get_inspection_job_record_obj_by_inspection_template_oid(
            self.inspection_template_obj.oid)
        if len(existed_inspection_job_obj_list) > 0:
            print("LaunchTemplateTrigger.existed_uncompleted_inspection_job: 已有历史巡检作业！")
            for job in existed_inspection_job_obj_list:
                if job.job_state == INSPECTION_JOB_EXEC_STATE_STARTED:
                    print("LaunchTemplateTrigger.existed_uncompleted_inspection_job: 还有历史作业未完成，无法启动新的巡检作业！")
                    return True
            return False
        else:
            return False

    def sched_start_job(self):
        print(f"LaunchTemplateTrigger.sched_start_job: 开始启动巡检作业: {self.inspection_template_obj.name}")
        inspect_job_name = "job@" + self.inspection_template_obj.name + "@" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        current_inspection_job_obj = LaunchInspectionJob(name=inspect_job_name,
                                                         project_oid=self.inspection_template_obj.project_oid,
                                                         inspection_template=self.inspection_template_obj,
                                                         global_info=self.global_info)
        launch_job_thread = threading.Thread(target=current_inspection_job_obj.start_job)
        launch_job_thread.start()  # 线程start后，不要join()，主界面才不会卡住

    def start_template_at(self):
        current_time = time.time()
        if self.inspection_template_obj.execution_at_time > current_time:
            sched_obj = sched.scheduler(time.time, time.sleep)  # 创建一个调度器
            # enter()函数参数1为等待的时间（秒），参数2为优先级，参数3为到时间后要调度的函数
            sched_obj.enter(self.inspection_template_obj.execution_at_time - current_time, 1, self.sched_start_job)
            # 运行调度器，默认是blocking=True，阻塞模式，等时间到了才运行，运行回调函数后才继续
            sched_t = threading.Thread(target=sched_obj.run)
            sched_t.start()  # 线程start后，不要join()，主界面才不会卡住
        else:
            at_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.inspection_template_obj.execution_at_time))
            print(f"LaunchTemplateTrigger.start_template_at: 巡检模板 {self.inspection_template_obj.name} 时间已过: {at_time}")

    def start_template_after(self):
        pass

    def start_template_crond(self):
        pass

    def update(self):
        self.start_crond_job()


class HostJobStatus:
    """
    记录被巡检主机的巡检作业状态，一个HostJobStatus对象 对应一台主机的作业状态
    """

    def __init__(self, host_oid='', job_status=INSPECTION_JOB_EXEC_STATE_UNKNOWN, start_time=0.0, end_time=0.0,
                 find_credential_status=INSPECTION_JOB_EXEC_STATE_UNKNOWN, exec_timeout=COF_NO, sum_of_code_block=0,
                 current_exec_code_block=0, sum_of_code_lines=0, current_exec_code_num=0):
        self.host_oid = host_oid  # <str>
        self.job_status = job_status  # <int> INSPECTION_JOB_EXEC_STATE_UNKNOWN
        self.find_credential_status = find_credential_status  # <int>
        self.exec_timeout = exec_timeout  # <int>
        self.start_time = start_time  # <float>
        self.end_time = end_time  # <float>
        self.sum_of_code_block = sum_of_code_block  # <int> 所有巡检代码段的数量<InspectionCodeBlock>的数量
        self.current_exec_code_block = current_exec_code_block  # <int> 当前执行的巡检代码段序号，从0开始编号
        self.sum_of_code_lines = sum_of_code_lines  # <int> 所有巡检代码段的代码总行数<OneLineCode>的数量
        self.current_exec_code_num = current_exec_code_num  # <int>当前执行了的总代码行数，从1开始
        # current_exec_code_num/sum_of_code_lines 为 执行总进度


class LaunchInspectionJob:
    """
    执行巡检任务，一次性的，具有实时性，由巡检触发检测类<LaunchTemplateTrigger>对象去创建并执行巡检工作（也可手动触发），完成后输出日志
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
        self.unduplicated_host_job_status_obj_list = []  # host的巡检作业状态信息<HostJobStatus>对象，与上面的unduplicated_host_oid_list一一对应
        self.job_state = INSPECTION_JOB_EXEC_STATE_UNKNOWN  # 一个巡检作业的所有主机整体完成情况
        self.global_info = global_info
        self.start_time = 0.0
        self.end_time = 0.0

    def get_unduplicated_host_oid_from_group(self, host_group_oid):  # 从主机组中获取非重复主机
        host_group = self.global_info.get_host_group_by_oid(host_group_oid)
        for host_oid in host_group.host_oid_list:
            if host_oid in self.unduplicated_host_oid_list:
                print("LaunchInspectionJob.get_unduplicated_host_oid_from_group:",
                      f"重复主机: {self.global_info.get_host_by_oid(host_oid).name}")
                continue
            else:
                self.unduplicated_host_oid_list.append(host_oid)
        for group_oid in host_group.host_group_oid_list:
            self.get_unduplicated_host_oid_from_group(group_oid)
        return None

    def get_unduplicated_host_oid_from_inspection_template(self):  # 从巡检模板的主机列表及主机组列表中获取非重复主机
        if self.inspection_template is None:
            print("LaunchInspectionJob.get_unduplicated_host_oid_from_inspection_template: 巡检模板为空")
            return
        for host_oid in self.inspection_template.host_oid_list:
            if host_oid in self.unduplicated_host_oid_list:
                print("LaunchInspectionJob.get_unduplicated_host_oid_from_inspection_template:",
                      f"重复主机: {self.global_info.get_host_by_oid(host_oid).name}")
                continue
            else:
                self.unduplicated_host_oid_list.append(host_oid)
        for host_group_oid in self.inspection_template.host_group_oid_list:
            self.get_unduplicated_host_oid_from_group(host_group_oid)
        # ★主机去重后生成主机列表及对应的主机状态信息对象列表
        for host_oid in self.unduplicated_host_oid_list:
            host_job_status_obj = HostJobStatus(host_oid=host_oid)  # job_status默认为INSPECTION_CODE_JOB_EXEC_STATE_UNKNOWN
            self.unduplicated_host_job_status_obj_list.append(host_job_status_obj)

    def create_ssh_operator_invoke_shell(self, host_obj, host_job_status_obj, cred):
        # 先统计巡检代码块及巡检命令总数
        host_job_status_obj.sum_of_code_block = len(self.inspection_template.inspection_code_block_oid_list)
        inspection_code_block_obj_list = []
        host_job_status_obj.sum_of_code_lines = 0
        for inspection_code_block_oid in self.inspection_template.inspection_code_block_oid_list:
            inspection_code_block_obj = self.global_info.get_inspection_code_block_by_oid(inspection_code_block_oid)
            host_job_status_obj.sum_of_code_lines += len(inspection_code_block_obj.code_list)
            inspection_code_block_obj_list.append(inspection_code_block_obj)
        # 巡检代码块不去重，依次执行，串行执行
        inspection_code_block_index = 0
        for inspection_code_block_obj in inspection_code_block_obj_list:
            host_job_status_obj.current_exec_code_block = inspection_code_block_index
            # inspection_code_block_exec_estimated_time = 0.0
            # for code in inspection_code_block_obj.code_list:
            #     inspection_code_block_exec_estimated_time += code.code_post_wait_time  # 交互处理的次数不好判断
            # max_exec_wait_count = inspection_code_block_exec_estimated_time // CODE_POST_WAIT_TIME_DEFAULT  # 判断巡检线程超时最大等待次数
            if cred.cred_type == CRED_TYPE_SSH_PASS:
                auth_method = AUTH_METHOD_SSH_PASS
            else:
                auth_method = AUTH_METHOD_SSH_KEY
            # 一个<SSHOperator>对象操作一个<InspectionCodeBlock>巡检代码块的所有命令
            ssh_operator = SSHOperator(hostname=host_obj.address, port=host_obj.ssh_port, username=cred.username,
                                       password=cred.password, private_key=cred.private_key, auth_method=auth_method,
                                       command_list=inspection_code_block_obj.code_list, timeout=LOGIN_AUTH_TIMEOUT,
                                       host_job_status_obj=host_job_status_obj)
            try:
                job_thread = threading.Thread(target=ssh_operator.run_invoke_shell)  # 执行巡检命令，输出信息保存在 SSHOperator.output_list里
                job_thread.start()  # 线程start后，不要join()，主程序才不会卡住
            except paramiko.AuthenticationException as e:
                print("LaunchInspectionJob.create_ssh_operator_invoke_shell:",
                      f"目标主机 {host_obj.name} 登录时身份验证失败: {e}")  # 登录验证失败，则此host的所有巡检code都不再继续
                host_job_status_obj.job_status = INSPECTION_JOB_EXEC_STATE_FAILED
                host_job_status_obj.find_credential_status = INSPECTION_JOB_EXEC_STATE_FAILED
                return  # 验证失败则直接退出本函数
            max_timeout_index = 0
            while True:  # 这里是判断 ssh_operator.run_invoke_shell() 是否完成，否就等待直到最大超时
                if max_timeout_index >= MAX_EXEC_WAIT_COUNT:  # 判断巡检线程超时最大等待次数
                    print("LaunchInspectionJob.create_ssh_operator_invoke_shell:",
                          f"巡检代码块: {inspection_code_block_obj.name} 已达最大超时-未完成")
                    host_job_status_obj.job_status = INSPECTION_JOB_EXEC_STATE_FAILED
                    host_job_status_obj.exec_timeout = COF_YES
                    break
                time.sleep(CODE_POST_WAIT_TIME_DEFAULT)
                max_timeout_index += 1
                if ssh_operator.is_finished:
                    print("LaunchInspectionJob.create_ssh_operator_invoke_shell:",
                          f"巡检代码块: {inspection_code_block_obj.name} 已执行完成")
                    # 部分完成，只是完成了当前巡检代码块，可能还有其他的巡检代码块
                    host_job_status_obj.job_status = INSPECTION_JOB_EXEC_STATE_PART_COMPLETED
                    break
            if len(ssh_operator.output_list) != 0:
                # 如果ssh_operator.run_invoke_shell() 有输出信息，则判断是否需要输出信息保存到文件
                if self.inspection_template.save_output_to_file == COF_YES:
                    self.save_ssh_operator_output_to_file(ssh_operator.output_list, host_obj,
                                                          self.inspection_template.output_file_name_style)
                # 输出信息保存到sqlite数据库★★★★★
                self.save_ssh_operator_invoke_shell_output_to_sqlite(ssh_operator.output_list, host_obj, inspection_code_block_obj)
            inspection_code_block_index += 1
        if host_job_status_obj.exec_timeout == COF_NO and host_job_status_obj.find_credential_status == FIND_CREDENTIAL_STATUS_SUCCEED:
            host_job_status_obj.job_status = INSPECTION_JOB_EXEC_STATE_COMPLETED  # 全部完成，没有超时的，没有验证失败的
        print("LaunchInspectionJob.create_ssh_operator_invoke_shell: 目标主机",
              f"{host_obj.name} 已巡检完成，远程方式: ssh <<<<<<<<<<<<<<<<<<")

    def operator_job_thread(self, host_index):
        """
        正式执行主机巡检任务，一台主机一个线程，本函数只处理一台主机，本函数调用self.create_ssh_operator_invoke_shell去执行命令
        :param host_index:
        :return:
        """
        host_obj = self.global_info.get_host_by_oid(self.unduplicated_host_oid_list[host_index])
        host_job_status_obj = self.unduplicated_host_job_status_obj_list[host_index]
        print(f"\nLaunchInspectionJob.operator_job_thread >>>>> 目标主机：{host_obj.name} 开始巡检 <<<<<")
        host_job_status_obj.job_status = INSPECTION_JOB_EXEC_STATE_STARTED
        host_job_status_obj.start_time = time.time()  # 开始计时
        if host_obj.login_protocol == LOGIN_PROTOCOL_SSH:
            try:
                cred = self.find_ssh_credential(host_obj)  # 查找可用的登录凭据，这里会登录一次目标主机
            except Exception as e:
                print("LaunchInspectionJob.operator_job_thread: 查找可用的凭据错误，", e)
                host_job_status_obj.job_status = INSPECTION_JOB_EXEC_STATE_FAILED  # 无可用凭据，就退出巡检线程了，宣告失败
                host_job_status_obj.find_credential_status = FIND_CREDENTIAL_STATUS_FAILED
                host_job_status_obj.end_time = time.time()  # 结束计时
                return
            if cred is None:
                print("LaunchInspectionJob.operator_job_thread: Credential is None, Could not find correct credential")
                host_job_status_obj.job_status = INSPECTION_JOB_EXEC_STATE_FAILED  # 无可用凭据，就退出巡检线程了，宣告失败
                host_job_status_obj.find_credential_status = FIND_CREDENTIAL_STATUS_FAILED
                host_job_status_obj.end_time = time.time()  # 结束计时
                return
            self.create_ssh_operator_invoke_shell(host_obj, host_job_status_obj, cred)  # ★★开始正式执行巡检命令，输出信息保存到文件及数据库★★
        elif host_obj.login_protocol == LOGIN_PROTOCOL_TELNET:
            print("LaunchInspectionJob.operator_job_thread: 使用telnet协议远程目标主机")
        else:
            pass
        # 完成情况由相应登录协议处理函数去判断，比如ssh由self.create_ssh_operator_invoke_shell去判断此主机的巡检情况
        host_job_status_obj.end_time = time.time()  # 结束计时
        print(f"LaunchInspectionJob.operator_job_thread: >>>>> 目标主机：{host_obj.name} 巡检完成 <<<<<")

    def find_ssh_credential(self, host):
        """
        查找可用的ssh凭据，会登录一次目标主机（因为一台主机可以绑定多个同类型的凭据，依次尝试，直到找到可用的凭据）
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
        主机的一个巡检代码段所有命令输出信息都保存在一个文件里，不同的巡检代码段输出保存在不同文件里
        :param ssh_operator_output_obj_list:
        :param host:
        :param output_file_name_style:
        :return:
        """
        localtime = time.localtime(time.time())
        timestamp_date_list = [str(localtime.tm_year), self.fmt_time(localtime.tm_mon), self.fmt_time(localtime.tm_mday)]
        timestamp_time_list = [str(localtime.tm_hour), str(localtime.tm_min), str(localtime.tm_sec)]
        timestamp_date = "-".join(timestamp_date_list)  # 年月日，例：2024-01-25
        timestamp_time = ".".join(timestamp_time_list)  # 时分秒，例：8.50.01
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
        # 一台主机的所有巡检命令输出信息都保存在一个文件里
        with open(file_name, 'a', encoding='utf8') as file_obj:  # 追加，不存在则新建
            for ssh_operator_output_obj in ssh_operator_output_obj_list:
                if ssh_operator_output_obj.code_exec_method == CODE_EXEC_METHOD_INVOKE_SHELL:
                    file_obj.write('\n'.join(ssh_operator_output_obj.invoke_shell_output_bytes.decode("utf8").split('\r\n')))
                    if len(ssh_operator_output_obj.interactive_output_bytes_list) != 0:
                        for interactive_output_bytes in ssh_operator_output_obj.interactive_output_bytes_list:
                            file_obj.write('\n'.join(interactive_output_bytes.decode("utf8").split('\r\n')))
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

    def save_ssh_operator_invoke_shell_output_to_sqlite(self, ssh_operator_output_obj_list, host_obj, inspection_code_obj):
        """
        主机的所有巡检命令输出信息都保存到数据库里
        :param ssh_operator_output_obj_list:
        :param host_obj:
        :param inspection_code_obj:
        :return:
        """
        self.global_info.lock_sqlite3_db.acquire()  # 获取操作数据库的全局锁
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★★★查询是否有名为'tb_inspection_job_invoke_shell_output'的表★★★
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
                        "invoke_shell_output_bytes_b64 varchar(8192),",
                        "invoke_shell_output_last_line_str_b64 varchar(8192) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★★★查询是否有名为'tb_inspection_job_invoke_shell_interactive_output'的表★★★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job_invoke_shell_interactive_output"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_inspection_job_invoke_shell_interactive_output  ( job_oid varchar(36),",
                        "host_oid varchar(36),",
                        "inspection_code_oid varchar(36),",
                        "project_oid varchar(36),",
                        "code_index int,",
                        "code_exec_interactive_output_index int,",
                        "interactive_output_bytes_b64 varchar(8192) )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # ★★★开始插入数据，一条命令的输出为一行记录（job_oid为LaunchInspectionJob的oid，也同InspectionJobRecord的oid）★★★
        for code_output in ssh_operator_output_obj_list:
            sql_list = ["select * from tb_inspection_job_invoke_shell_output where",
                        f"job_oid='{self.oid}' and host_oid='{host_obj.oid}'",
                        f"and inspection_code_oid='{inspection_code_obj.oid}'",
                        f"and code_index='{code_output.code_index}' "]
            sqlite_cursor.execute(" ".join(sql_list))
            if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项记录，则创建此项记录
                invoke_shell_output_bytes_b64 = base64.b64encode(code_output.invoke_shell_output_bytes).decode('utf8')
                invoke_shell_output_last_line_str_b64 = base64.b64encode(
                    code_output.invoke_shell_output_last_line_str.encode('utf8')).decode('utf8')
                sql_list = ["insert into tb_inspection_job_invoke_shell_output (job_oid,",
                            "host_oid,",
                            "inspection_code_oid,",
                            "project_oid,",
                            "code_index,",
                            "code_exec_method,",
                            "invoke_shell_output_bytes_b64,",
                            "invoke_shell_output_last_line_str_b64 )  values ",
                            f"( '{self.oid}',",
                            f"'{host_obj.oid}',",
                            f"'{inspection_code_obj.oid}',",
                            f"'{host_obj.project_oid}',",
                            f"{code_output.code_index},",
                            f"{code_output.code_exec_method},",
                            f"'{invoke_shell_output_bytes_b64}',",
                            f"'{invoke_shell_output_last_line_str_b64}'",
                            " )"]
                sqlite_cursor.execute(" ".join(sql_list))
                self.save_interactive_output_bytes_list(sqlite_cursor, host_obj, inspection_code_obj, code_output)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        self.global_info.lock_sqlite3_db.release()  # 释放操作数据库的全局锁

    def save_interactive_output_bytes_list(self, sqlite_cursor, host_obj, inspection_code_obj, code_output):
        # 开始插入数据，一条记录为SSHOperatorOutput.interactive_output_bytes_list的一个元素
        index = 0
        for interactive_output_bytes in code_output.interactive_output_bytes_list:
            interactive_output_bytes_b64 = base64.b64encode(interactive_output_bytes).decode("utf8")
            sql_list = ["insert into tb_inspection_job_invoke_shell_interactive_output (job_oid,",
                        "host_oid,",
                        "inspection_code_oid,",
                        "project_oid,",
                        "code_index,",
                        "code_exec_interactive_output_index,",
                        "interactive_output_bytes_b64 )  values ",
                        f"( '{self.oid}',",
                        f"'{host_obj.oid}',",
                        f"'{inspection_code_obj.oid}',",
                        f"'{host_obj.project_oid}',",
                        f"{code_output.code_index},",
                        f"{index},",
                        f"'{interactive_output_bytes_b64}'",
                        " )"]
            sqlite_cursor.execute(" ".join(sql_list))
            index += 1

    def judge_completion_of_job(self):
        completed_host_num = 0
        for host_status_obj in self.unduplicated_host_job_status_obj_list:
            if host_status_obj.job_status == INSPECTION_JOB_EXEC_STATE_COMPLETED:
                completed_host_num += 1
        if completed_host_num == len(self.unduplicated_host_job_status_obj_list):
            self.job_state = INSPECTION_JOB_EXEC_STATE_COMPLETED
        elif completed_host_num == 0:
            self.job_state = INSPECTION_JOB_EXEC_STATE_FAILED
        else:
            self.job_state = INSPECTION_JOB_EXEC_STATE_FAILED

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
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项记录，则创建此项记录
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
        self.job_state = INSPECTION_JOB_EXEC_STATE_STARTED
        if self.inspection_template is None:
            print("巡检模板对象为空，结束本次任务")
            self.job_state = INSPECTION_JOB_EXEC_STATE_FAILED
            return
        self.start_time = time.time()
        self.get_unduplicated_host_oid_from_inspection_template()  # ★主机去重，去重后生成主机列表及对应的主机状态信息对象列表
        job_record_obj = InspectionJobRecord(name=self.name, description=self.description, oid=self.oid,
                                             create_timestamp=self.create_timestamp, project_oid=self.project_oid,
                                             inspection_template_oid=self.inspection_template_oid, job_state=self.job_state,
                                             unduplicated_host_job_status_obj_list=self.unduplicated_host_job_status_obj_list,
                                             start_time=self.start_time, end_time=self.end_time, global_info=self.global_info)
        self.global_info.inspection_job_record_obj_list.insert(0, job_record_obj)
        print("巡检模板名称：", self.inspection_template.name)
        thread_pool = ThreadPool(processes=self.inspection_template.forks)  # 创建线程池，线程数量由<InspectionTemplate>.forks决定
        thread_pool.map(self.operator_job_thread, range(len(self.unduplicated_host_oid_list)))  # ★★线程池调用巡检作业函数★★
        thread_pool.close()
        thread_pool.join()  # 会等待所有线程完成: self.operator_job_thread()
        self.end_time = time.time()
        print("巡检任务完成 ############################################################")
        print(f"巡检并发数为{self.inspection_template.forks}")
        print("用时 {:<6.4f} 秒".format(self.end_time - self.start_time))
        # 将作业信息保存到数据库，从数据库读取出来时，不可重构为一个<LaunchInspectionJob>对象，只可重构为<InspectionJobRecord>对象
        self.judge_completion_of_job()  # 先判断作业完成情况
        job_record_obj.end_time = self.end_time
        job_record_obj.job_state = self.job_state
        job_record_obj.unduplicated_host_job_status_obj_list = self.unduplicated_host_job_status_obj_list
        job_record_obj.save()  # 保存巡检作业情况到数据库，这里不是保存每台主机的巡检命令巡出，而是每台主机的巡检完成情况


class InspectionJobRecord:
    """
    巡检任务记录，当前的巡检作业及历史的巡检作业情况记录，具有历史性，由<LaunchInspectionJob>对象去创建或者由GlobalInfo从数据库导入生成
    """

    def __init__(self, name='default', description='default', oid=None, create_timestamp=None, project_oid='',
                 inspection_template_oid='', job_state=INSPECTION_JOB_EXEC_STATE_UNKNOWN, unduplicated_host_job_status_obj_list=None,
                 global_info=None, start_time=0.0, end_time=0.0):
        if oid is None:
            self.oid = uuid.uuid4().__str__()  # <str> 同<LaunchInspectionJob>对象的属性
        else:
            self.oid = oid
        self.name = name  # <str> 同<LaunchInspectionJob>对象的属性
        self.description = description  # <str> 同<LaunchInspectionJob>对象的属性
        if create_timestamp is None:
            self.create_timestamp = time.time()  # <float> 同<LaunchInspectionJob>对象的属性
        else:
            self.create_timestamp = create_timestamp
        self.project_oid = project_oid  # <str> 同<LaunchInspectionJob>对象的属性
        self.inspection_template_oid = inspection_template_oid  # <str> InspectionTemplate对象oid
        if unduplicated_host_job_status_obj_list is None:
            self.unduplicated_host_job_status_obj_list = []  # host的巡检作业状态信息<HostJobStatus>对象
        else:
            self.unduplicated_host_job_status_obj_list = unduplicated_host_job_status_obj_list  # 同<LaunchInspectionJob>对象的属性
        self.job_state = job_state  # <int> 同<LaunchInspectionJob>对象的属性
        self.global_info = global_info  # 同<LaunchInspectionJob>对象的属性
        self.start_time = start_time  # <float> 同<LaunchInspectionJob>对象的属性
        self.end_time = end_time  # <float> 同<LaunchInspectionJob>对象的属性

    def save(self):
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_record'的表★
        sql = f'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job_record"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_inspection_job_record  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "inspection_template_oid varchar(36),",
                        "job_state int,",
                        "start_time double,",
                        "end_time double )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_inspection_job_record where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项记录，则创建此项记录 ★★
            sql_list = [f"insert into tb_inspection_job_record (oid,",
                        "name,",
                        "description,",
                        "project_oid,",
                        "inspection_template_oid,",
                        "job_state,",
                        "start_time,",
                        "end_time ) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"'{self.inspection_template_oid}',",
                        f"{self.job_state},",
                        f"{self.start_time},",
                        f"{self.end_time} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项记录，则不用更新此项记录 ★★
            pass
        # ★查询是否有名为'tb_inspection_job_record_host_job_status_obj_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job_record_host_job_status_obj_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = ["create table tb_inspection_job_record_host_job_status_obj_list",
                        "(job_record_oid varchar(36),",
                        "host_oid varchar(36),",
                        "job_status int,",
                        "find_credential_status int,",
                        "exec_timeout int,",
                        "start_time double,",
                        "end_time double,",
                        "sum_of_code_block int,",
                        "current_exec_code_block int,",
                        "sum_of_code_lines int,",
                        "current_exec_code_num int",
                        " );"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"delete from tb_inspection_job_record_host_job_status_obj_list where host_oid='{self.oid}'"
        sqlite_cursor.execute(sql)  # ★先清空所有，再重新插入（既可用于新建，又可用于更新）
        for host_job_status_obj in self.unduplicated_host_job_status_obj_list:
            sql_list = [f"insert into tb_inspection_job_record_host_job_status_obj_list (job_record_oid,",
                        "host_oid,",
                        "job_status,",
                        "find_credential_status,",
                        "exec_timeout,",
                        "start_time,",
                        "end_time,",
                        "sum_of_code_block,",
                        "current_exec_code_block,",
                        "sum_of_code_lines,",
                        "current_exec_code_num",
                        " ) values ",
                        f"('{self.oid}',",
                        f"'{host_job_status_obj.host_oid}',",
                        f"{host_job_status_obj.job_status},",
                        f"{host_job_status_obj.find_credential_status},",
                        f"{host_job_status_obj.exec_timeout},",
                        f"{host_job_status_obj.start_time},",
                        f"{host_job_status_obj.end_time},",
                        f"{host_job_status_obj.sum_of_code_block},",
                        f"{host_job_status_obj.current_exec_code_block},",
                        f"{host_job_status_obj.sum_of_code_lines},",
                        f"{host_job_status_obj.current_exec_code_num}",
                        ")"]
            sqlite_cursor.execute(" ".join(sql_list))
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


class OneLineCode:
    """
    InspectionCodeBlock.code_list列表包含的元素，巡检任务中要执行的每一行命令都是一个<OneLineCode>对象
    """

    def __init__(self, code_index=0, code_content='', code_post_wait_time=CODE_POST_WAIT_TIME_DEFAULT,
                 need_interactive=COF_NO, interactive_question_keyword='', interactive_answer='',
                 interactive_process_method=INTERACTIVE_PROCESS_METHOD_ONETIME, description=''):
        self.code_index = code_index  # <int>
        self.code_content = code_content  # <str>
        self.code_post_wait_time = code_post_wait_time  # <float>
        self.need_interactive = need_interactive  # <int>
        self.interactive_question_keyword = interactive_question_keyword  # <str>
        self.interactive_answer = interactive_answer  # <str>
        self.interactive_process_method = interactive_process_method  # <int>
        self.description = description  # <str>


class SSHOperatorOutput:
    """
    <OneLineCode>对象的一行命令执行后的所有输出信息都保存在一个<SSHOperatorOutput>对象里
    """

    def __init__(self, code_index=0, code_content=None, code_exec_method=CODE_EXEC_METHOD_INVOKE_SHELL,
                 invoke_shell_output_bytes=None, invoke_shell_output_last_line_str=None, is_empty_output=False,
                 interactive_output_bytes_list=None,
                 exec_command_stdout_line_list=None,
                 exec_command_stderr_line_list=None):
        self.code_index = code_index  # <int> 命令序号
        self.code_content = code_content  # <str> 命令内容，一行
        self.code_exec_method = code_exec_method  # <int> 默认是CODE_EXEC_METHOD_INVOKE_SHELL
        if invoke_shell_output_bytes is None:
            self.invoke_shell_output_bytes = b""  # <bytes>
        else:
            self.invoke_shell_output_bytes = invoke_shell_output_bytes  # <bytes> 所有输出，可有换行符，ESC，NUL等
        if invoke_shell_output_last_line_str is None:
            self.invoke_shell_output_last_line_str = ""  # <str>
        else:
            self.invoke_shell_output_last_line_str = invoke_shell_output_last_line_str  # <str> 命令输出的最后一行
        if interactive_output_bytes_list is None:
            self.interactive_output_bytes_list = []
        else:
            self.interactive_output_bytes_list = interactive_output_bytes_list  # <list> 元素为 <bytes> 一次交互输出为一个元素
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
                 timeout=30, auth_method=AUTH_METHOD_SSH_PASS, command_list=None, host_job_status_obj=None):
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
        self.output_list = []  # 元素类型为 <SSHOperatorOutput>，一条执行命令<OneLineCode>只产生一个output对象
        self.host_job_status_obj = host_job_status_obj  # <HostJobStatus>

    def run_invoke_shell(self):
        """
        使用invoke_shell交互式shell执行命令
        :return:
        """
        if self.command_list is None:
            print("SSHOperator.run_invoke_shell : command_list(inspection_code_block_obj.code_list) is None")
            return None
        # ★★创建ssh连接★★
        ssh_client = paramiko.client.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接host_key不在know_hosts文件里的主机
        try:
            if self.auth_method == AUTH_METHOD_SSH_PASS:
                print("SSHOperator.run_invoke_shell : 使用ssh_password密码登录")
                ssh_client.connect(hostname=self.hostname, port=self.port, username=self.username,
                                   password=self.password, timeout=self.timeout)
            elif self.auth_method == AUTH_METHOD_SSH_KEY:
                prikey_string_io = io.StringIO(self.private_key)
                pri_key = paramiko.RSAKey.from_private_key(prikey_string_io)
                print("SSHOperator.run_invoke_shell : 使用ssh_priKey密钥登录")
                ssh_client.connect(hostname=self.hostname, port=self.port, username=self.username,
                                   pkey=pri_key, timeout=self.timeout)
            else:
                pass
        except paramiko.AuthenticationException as e:
            print(f"SSHOperator.run_invoke_shell : Authentication Error: {e}")
            raise e
        # ★★连接后，创建invoke_shell交互式shell★★
        ssh_shell = ssh_client.invoke_shell(width=SHELL_TERMINAL_WIDTH, height=SHELL_TERMINAL_HEIGHT)  # 创建一个交互式shell
        time.sleep(CODE_POST_WAIT_TIME_DEFAULT)  # 远程连接后，首先等待一会，可能会有信息输出
        try:
            login_recv = ssh_shell.recv(65535)  # 获取登录后的输出信息，此时未执行任何命令
        except Exception as e:
            print(e)
            return
        # 创建命令输出对象<SSHOperatorOutput>，一条命令对应一个<SSHOperatorOutput>对象
        invoke_shell_output_str_list = login_recv.decode('utf8').split('\r\n')
        invoke_shell_output_str = '\n'.join(invoke_shell_output_str_list)  # 这与前面一行共同作用是去除'\r'
        # invoke_shell_output_str = recv.decode('utf8').replace('\r', '')  # 登录后的输出信息，换行符为\r\n，这里去除一个\r，只留\n
        output_login = SSHOperatorOutput(code_index=-1, code_exec_method=CODE_EXEC_METHOD_INVOKE_SHELL,
                                         invoke_shell_output_bytes=login_recv)
        self.output_list.append(output_login)  # 刚登录后的输出信息保存到output_list里
        print("SSHOperator.run_invoke_shell : 登录后输出内容如下 #################\n", invoke_shell_output_str)
        # ★★开始执行正式命令★★
        cmd_index = 0
        for one_line_code in self.command_list:
            if not isinstance(one_line_code, OneLineCode):
                return
            ssh_shell.send(one_line_code.code_content.strip().encode('utf8'))  # 发送巡检命令，一行命令（会过滤命令前后的空白字符）
            ssh_shell.send("\n".encode('utf8'))  # 命令strip()后，不带\n换行，需要额外发送一个换行符
            time.sleep(one_line_code.code_post_wait_time)  # 发送完命令后，要等待系统回复★★★
            try:
                cmd_recv = ssh_shell.recv(65535)
            except Exception as e:
                print(e)
                return
            invoke_shell_output_str_list = cmd_recv.decode('utf8').split('\r\n')
            invoke_shell_output_str = '\n'.join(invoke_shell_output_str_list)  # 这与前面一行共同作用是去除'\r'
            output_str_lines = invoke_shell_output_str.split('\n')
            output_last_line_index = len(output_str_lines) - 1
            output_last_line = output_str_lines[output_last_line_index]  # 命令输出最后一行（shell提示符，不带换行符的）
            output_cmd = SSHOperatorOutput(code_index=cmd_index, code_exec_method=CODE_EXEC_METHOD_INVOKE_SHELL,
                                           code_content=one_line_code.code_content, invoke_shell_output_bytes=cmd_recv,
                                           invoke_shell_output_last_line_str=output_last_line)
            self.output_list.append(output_cmd)  # 命令输出结果保存到output_list里
            print(f"SSHOperator.run_invoke_shell : $$ 命令{cmd_index} $$ 输出结果如下 ##############\n", invoke_shell_output_str)
            # 有的shell提示符末尾有个空格，当然了，也有的shell提示符末尾没有空格
            print(f"SSHOperator.run_invoke_shell : 命令输出最后一行（可能是shell提示符，无换行符）为:  {output_last_line.encode('utf8')}")
            if one_line_code.need_interactive:  # 命令如果需要处理交互情况，则判断交互提问关键词
                self.process_code_interactive(one_line_code, output_last_line, ssh_shell, output_cmd)
            self.host_job_status_obj.current_exec_code_num += 1
            cmd_index += 1
        ssh_shell.close()
        ssh_client.close()
        self.is_finished = True

    @staticmethod
    def process_code_interactive(code, output_last_line, ssh_shell, output, second_time=False, interactive_times=0):
        """
        处理命令的交互式应答，有时执行某些命令执后，系统会提示输入[Y/N]?，要求回复
        :param interactive_times: <int>
        :param code: <OneLineCode>
        :param output_last_line: <str>
        :param ssh_shell: ssh_client.invoke_shell()
        :param output: <SSHOperatorOutput>
        :param second_time: bool
        :return:
        """
        ret = re.search(code.interactive_question_keyword, output_last_line, re.I)  # 对命令输出的最后一行进行关键词匹配，不区分大小写
        if ret is not None:  # 如果匹配上需要交互的提问字符串
            print(f"SSHOperator.process_code_interactive : 匹配到交互关键字 {ret} ，执行交互回答:")
            ssh_shell.send(code.interactive_answer.encode('utf8'))  # 发送交互回答内容，这里不会额外发送\n换行，也不过滤空白字符
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
            output.interactive_output_bytes_list.append(recv)
            if second_time is True:
                print("SSHOperator.process_code_interactive : 上面输出为twice的★★★★★")
                return
            if interactive_times > MAX_INTERACTIVE_COUNT:
                return
            interactive_times += 1
            interactive_output_str_lines = interactive_output_str.split('\n')
            interactive_output_last_line_index = len(interactive_output_str_lines) - 1
            if code.interactive_process_method == INTERACTIVE_PROCESS_METHOD_LOOP and len(interactive_output_str_lines) != 0:
                SSHOperator.process_code_interactive(code, interactive_output_str_lines[interactive_output_last_line_index], ssh_shell,
                                                     output, interactive_times=interactive_times)
            if code.interactive_process_method == INTERACTIVE_PROCESS_METHOD_TWICE and len(interactive_output_str_lines) != 0:
                SSHOperator.process_code_interactive(code, interactive_output_str_lines[interactive_output_last_line_index], ssh_shell,
                                                     output, second_time=True, interactive_times=interactive_times)
        else:
            # 如果没有匹配上需要交互的提问判断字符串，就结束交互
            return

    def exec_command(self):
        """
        与 run_invoke_shell 相对应，非invoke_shell，不适用于交换机等设备，本函数暂时用不上，CofAble主要使用invoke_shell这类交互式的处理方式
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
    全局变量类，用于存储所有资源类的实例信息，从数据库导入数据变为内存中的类对象，以及新建的类对象追加到某个list列表中
    """

    def __init__(self, sqlite3_dbfile_name="cofable_default.db", builtin_font_file_path=''):
        self.sqlite3_dbfile_name = sqlite3_dbfile_name  # 若未指定数据库文件名称，则默认为"cofable_default.db"
        self.project_obj_list = []
        self.credential_obj_list = []
        self.host_obj_list = []
        self.host_group_obj_list = []
        self.inspection_code_block_obj_list = []
        self.inspection_template_obj_list = []
        self.inspection_job_record_obj_list = []
        self.launch_template_trigger_obj_list = []
        self.custome_tag_config_scheme_obj_list = []
        self.current_project_obj = None  # 需要在项目界面将某个项目设置为当前项目，才会赋值
        self.lock_sqlite3_db = threading.Lock()  # 操作本地sqlite3数据库文件的锁，同一时间段内只能有一个线程操作此数据库
        self.builtin_font_file_path = builtin_font_file_path
        self.main_window = None  # 程序的主窗口，全局只有一个主窗口对象
        self.division_terminal_window = None  # 主机的terminal终端子窗口
        self.multi_terminal_window = None  # 主机组的terminal终端子窗口，终端窗口组
        self.font_size_map_list_jetbrains_mono = [(8, 7, 14),
                                                  (9, 7, 16),
                                                  (10, 8, 17),
                                                  (11, 9, 19),
                                                  (12, 10, 21),
                                                  (13, 10, 22),
                                                  (14, 11, 25),
                                                  (15, 12, 26),
                                                  (16, 13, 27),
                                                  (17, 14, 30),
                                                  (18, 14, 31),
                                                  (19, 15, 32),
                                                  (20, 16, 36),
                                                  (21, 17, 37),
                                                  (22, 17, 39),
                                                  (23, 19, 41),
                                                  (24, 19, 43),
                                                  (25, 20, 44),
                                                  (26, 21, 47),
                                                  (27, 22, 48),
                                                  (28, 22, 49),
                                                  (29, 23, 52),
                                                  (30, 24, 53),
                                                  (31, 25, 54),
                                                  (32, 26, 57),
                                                  (33, 26, 58),
                                                  (34, 27, 59),
                                                  (35, 28, 62),
                                                  (36, 29, 63)]

        self.font_size_map_list_songti = [(8, 6, 11),
                                          (9, 6, 12),
                                          (10, 7, 13),
                                          (11, 8, 15),
                                          (12, 8, 16),
                                          (13, 9, 17),
                                          (14, 10, 19),
                                          (15, 10, 20),
                                          (16, 11, 21),
                                          (17, 12, 23),
                                          (18, 12, 24),
                                          (19, 13, 25),
                                          (20, 14, 27),
                                          (21, 14, 28),
                                          (22, 15, 29),
                                          (23, 16, 31),
                                          (24, 16, 33),
                                          (25, 17, 33),
                                          (26, 18, 35),
                                          (27, 18, 36),
                                          (28, 19, 37),
                                          (29, 20, 39),
                                          (30, 20, 40),
                                          (31, 21, 41),
                                          (32, 22, 43),
                                          (33, 22, 44),
                                          (34, 23, 45),
                                          (35, 24, 47),
                                          (36, 24, 48)]

    def get_font_mapped_width(self, font_size=12, font_family_or_name=""):
        if font_family_or_name == "":
            return self.get_font_mapped_width_songti(font_size)
        elif font_family_or_name == "JetBrains Mono":
            return self.get_font_mapped_width_jetbrains_mono(font_size)
        else:
            return 8  # 如果都没匹配上，则返回默认字体大小

    def get_font_mapped_height(self, font_size=12, font_family_or_name=""):
        if font_family_or_name == "":
            return self.get_font_mapped_height_songti(font_size)
        elif font_family_or_name == "JetBrains Mono":
            return self.get_font_mapped_height_jetbrains_mono(font_size)
        else:
            return 16  # 如果都没匹配上，则返回默认字体大小

    def get_font_mapped_width_songti(self, font_size=12):
        for size, width, height in self.font_size_map_list_songti:
            if size == font_size:
                return width
        return 8  # 如果都没匹配上，则返回默认字体大小

    def get_font_mapped_height_songti(self, font_size=12):
        for size, width, height in self.font_size_map_list_songti:
            if size == font_size:
                return height
        return 16  # 如果都没匹配上，则返回默认字体大小

    def get_font_mapped_width_jetbrains_mono(self, font_size=12):
        for size, width, height in self.font_size_map_list_jetbrains_mono:
            if size == font_size:
                return width
        return 10  # 如果都没匹配上，则返回默认字体大小

    def get_font_mapped_height_jetbrains_mono(self, font_size=12):
        for size, width, height in self.font_size_map_list_jetbrains_mono:
            if size == font_size:
                return height
        return 21  # 如果都没匹配上，则返回默认字体大小

    def load_builtin_font_file(self):
        pyglet.options['win32_gdi_font'] = True
        pyglet.font.add_file(self.builtin_font_file_path)

    def set_sqlite3_dbfile_name(self, file_name):
        self.sqlite3_dbfile_name = file_name

    def open_session_in_division_terminal_window(self, host_oid):
        host_obj = self.get_host_by_oid(host_oid)
        print(f"GlobalInfo.open_session_in_division_terminal_window: {host_obj.name}")
        if self.division_terminal_window is None:
            # 如果还未创建division_terminal_window对象，则先创建，再在此窗口里添加目标主机的会话信息
            self.division_terminal_window = DivisionTerminalWindow(global_info=self)
            self.division_terminal_window.add_new_session(host_obj)
        else:
            self.division_terminal_window.add_new_session(host_obj)

    def exit_division_terminal_window(self):
        if self.division_terminal_window is not None:
            for host_session_record_obj in self.division_terminal_window.host_session_record_obj_list:
                if host_session_record_obj.terminal_backend_obj.ssh_invoke_shell is not None:
                    try:
                        host_session_record_obj.terminal_backend_obj.ssh_invoke_shell.close()  # 如果已经关闭了，则再次关闭会抛出EOFError异常
                    except EOFError as err:
                        print(err)
                if host_session_record_obj.terminal_backend_obj.ssh_client is not None:
                    host_session_record_obj.terminal_backend_obj.ssh_client.close()
                cofable_stop_thread_silently(host_session_record_obj.parse_received_vt100_data_thread)
                cofable_stop_thread_silently(host_session_record_obj.set_custom_color_tag_config_thread)
                cofable_stop_thread_silently(host_session_record_obj.terminal_backend_run_thread)
                cofable_stop_thread_silently(host_session_record_obj.recv_vt100_output_data_thread)
                cofable_stop_thread_silently(host_session_record_obj.send_user_input_data_thread)
            time.sleep(0.1)
            self.division_terminal_window.pop_window.quit()

    def load_all_data_from_sqlite3(self):  # 初始化global_info，从数据库加载所有数据到实例
        if self.sqlite3_dbfile_name is None:
            print("undefined sqlite3_dbfile_name")
            return
        elif self.sqlite3_dbfile_name == '':
            print("sqlite3_dbfile_name is null")
            return
        else:
            # self.project_obj_list = self.load_project_from_dbfile()
            self.credential_obj_list = self.load_credential_from_dbfile()
            self.host_obj_list = self.load_host_from_dbfile()
            self.host_group_obj_list = self.load_host_group_from_dbfile()
            self.inspection_code_block_obj_list = self.load_inspection_code_block_from_dbfile()
            self.inspection_template_obj_list = self.load_inspection_template_from_dbfile()
            self.inspection_job_record_obj_list = self.load_inspection_job_record_from_dbfile()
            self.inspection_job_record_obj_list.reverse()  # 逆序，按时间从新到旧
            self.create_builtin_custome_tag_config_scheme()  # 创★★建内置的shell着色方案★★
            self.custome_tag_config_scheme_obj_list = self.load_custome_tag_config_scheme()  # 加载所有着色方案，含刚刚创建的内置方案
            # 加载完成所有资源后，创建定时作业监听器
            self.launch_template_trigger()

    def launch_template_trigger(self):
        for inspection_template in self.inspection_template_obj_list:
            if inspection_template.execution_method != EXECUTION_METHOD_NONE:
                cron_trigger1 = LaunchTemplateTrigger(inspection_template_obj=inspection_template,
                                                      global_info=self)
                inspection_template.launch_template_trigger_oid = cron_trigger1.oid  # 将触发器id添加到巡检模板对象上
                self.launch_template_trigger_obj_list.append(cron_trigger1)
                # 开始执行监视任务，达到触发条件就执行相应巡检模板（由LaunchTemplateTrigger.start_crontab_job()方法触发）
                cron_trigger1.start_crond_job()

    def create_builtin_custome_tag_config_scheme(self):
        self.create_builtin_custome_tag_config_scheme_linux()
        self.create_builtin_custome_tag_config_scheme_huawei()

    def create_builtin_custome_tag_config_scheme_linux(self):
        project_obj = self.get_project_by_name("default")
        if project_obj is not None:
            project_oid = project_obj.oid
        else:
            project_oid = "None"
        scheme_linux = CustomTagConfigScheme(name="linux", description="system builtin scheme for linux device",
                                             oid="7d285a2c-cf94-4012-9846-19ac7ac070e1",
                                             project_oid=project_oid,
                                             global_info=self)
        # ★ ip-mac地址 前景色-紫色
        match_pattern_ip_mac_addr = [r'(\d{1,3}\.){3}\d{1,3}', r'([0-9a-f]{2}:){5}[0-9a-f]{2}', r'[^:]([0-9a-f]{4}:){2}[0-9a-f]{4}[^:]',
                                     r'([0-9a-f]{2}-){5}[0-9a-f]{2}', r'[^-]([0-9a-f]{4}-){2}[0-9a-f]{4}[^-]']  # ipv6暂未匹配
        scheme_linux.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_ip_mac_addr), foreground="#ff4dff"))
        # ★ 错误，禁止，关闭等词语 前景色-红色
        match_pattern_error_disable = [r'\bdown\b', r'\berror\b', r'\bdisable\b', r'\bdisabled\b']
        scheme_linux.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_error_disable), foreground="red"))
        # ★ 完成，成功，开启等词语 前景色-绿色 #18ed92
        match_pattern_completed_enable = [r'\bcomplete\b', r'\bcompleted\b', r'\bdone\b', r'\bfinish\b', r'\bfinished\b',
                                          r'\bsucceed\b', r'\bsuccess\b', r'\bsuccessful\b', r'\bsuccessfully\b',
                                          r'\benable\b', r'\benabled\b', r'\bok\b', r'\bup\b']
        scheme_linux.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_completed_enable), foreground="#18ed92"))
        # ★ 默认，未知等词语 前景色-棕 #ba7131
        match_pattern_default_unknown = [r'\bdefault\b', r'\bunknow\b', r'\bunknown\b']
        scheme_linux.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_default_unknown), foreground="#ba7131"))
        # ★ 数字+大小（G,M,K），表示磁盘大小，网络大小 前景色-青色
        match_pattern_disk_size_net_speed = [r'\b(\d{1,}\.){,1}\d{1,}T[b]{,1}\b', r'\b(\d{1,}\.){,1}\d{1,}G[i]{,1}[b]{,1}\b',
                                             r'\b(\d{1,}\.){,1}\d{1,}M[i]{,1}[b]{,1}\b', r'\b(\d{1,}\.){,1}\d{1,}K[i]{,1}[b]{,1}\b']
        scheme_linux.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_disk_size_net_speed), foreground="cyan"))
        # ★ yes,true,all 前景色-绿 #7ffd01
        match_pattern_yes_true = [r'\byes\b', r'\btrue\b', r'\ball\b']
        scheme_linux.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_yes_true), foreground="#7ffd01"))
        # ★ no,false,none,null 前景色-棕 #fcc560
        match_pattern_no_false = [r'\bno\b', r'\bfalse\b', r'\bnone\b', r'\bnul\b', r'\bnull\b']
        scheme_linux.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_no_false), foreground="#fcc560"))
        scheme_linux.save()
        self.custome_tag_config_scheme_obj_list.append(scheme_linux)

    def create_builtin_custome_tag_config_scheme_huawei(self):
        project_obj = self.get_project_by_name("default")
        if project_obj is not None:
            project_oid = project_obj.oid
        else:
            project_oid = "None"
        scheme_huawei = CustomTagConfigScheme(name="huawei", description="system builtin scheme for huawei network device",
                                              oid="7d285a2c-cf94-4012-9846-19ac7ac070e2",
                                              project_oid=project_oid,
                                              global_info=self)
        # ★ 日期 时间  前景色-蓝色 #52a3f6
        match_pattern_disk_size_net_speed = [r'\b\d{4}-\d{2}-\d{2}\b', r'\b\d{2}:\d{2}:\d{2}\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_disk_size_net_speed),
                              foreground="#52a3f6", backgroun="#323232"))
        # ★ ip-mac地址 前景色-紫色
        match_pattern_ip_mac_addr = [r'(\d{1,3}\.){3}\d{1,3}', r'([0-9a-f]{2}:){5}[0-9a-f]{2}',
                                     r'[^:]([0-9a-f]{4}:){2}[0-9a-f]{4}[^:]',
                                     r'([0-9a-f]{2}-){5}[0-9a-f]{2}',
                                     r'[^-]([0-9a-f]{4}-){2}[0-9a-f]{4}[^-]']  # ipv6暂未匹配
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_ip_mac_addr), foreground="#ff4dff"))
        # ★ 错误，禁止，关闭等词语 前景色-红色
        match_pattern_error_disable = [r'\bdown\b', r'\berror\b', r'\bdisable\b', r'\bdisabled\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_error_disable), foreground="red"))
        # ★ 完成，成功，开启等词语 前景色-绿色 #18ed92
        match_pattern_completed_enable = [r'\bcomplete\b', r'\bcompleted\b', r'\bdone\b', r'\bfinish\b', r'\bfinished\b',
                                          r'\bsucceed\b', r'\bsuccess\b', r'\bsuccessful\b', r'\bsuccessfully\b',
                                          r'\benable\b', r'\benabled\b', r'\bok\b', r'\bup\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_completed_enable), foreground="#18ed92"))
        # ★ 默认，未知等词语 前景色-棕 #ba7131
        match_pattern_default_unknown = [r'\bdefault\b', r'\bunknow\b', r'\bunknown\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_default_unknown), foreground="#ba7131"))
        # ★ 数字+大小（G,M,K），表示磁盘大小，网络大小 前景色-青色
        match_pattern_disk_size_net_speed = [r'\b(\d{1,}\.){,1}\d{1,}T[b]{,1}\b',
                                             r'\b(\d{1,}\.){,1}\d{1,}G[i]{,1}[b]{,1}\b',
                                             r'\b(\d{1,}\.){,1}\d{1,}M[i]{,1}[b]{,1}\b',
                                             r'\b(\d{1,}\.){,1}\d{1,}K[i]{,1}[b]{,1}\b',
                                             r'\b\d{1,}[" "]{,1}byte[s]{,1}']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_disk_size_net_speed), foreground="cyan"))
        # ★ 数字+ packets  表示网络发包数量 前景色-黄色 #e2ed14
        match_pattern_disk_size_net_speed = [r'\b\d{1,}[" "]{,1}packet[s]{,1}']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_disk_size_net_speed), foreground="#e2ed14"))
        # ★ 数字%  前景色-绿色 #6bb520
        match_pattern_disk_size_net_speed = [r'\b\d{1,}[" "]{,1}\%']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_disk_size_net_speed), foreground="#6bb520"))
        # ★ yes,true,all 前景色-绿 #7ffd01
        match_pattern_yes_true = [r'\byes\b', r'\btrue\b', r'\ball\b', r'\btagged\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_yes_true), foreground="#7ffd01"))
        # ★ no,false,none,null 前景色-棕 #fcc560
        match_pattern_no_false = [r'\bno\b', r'\bfalse\b', r'\bnone\b', r'\bnul\b', r'\bnull\b', r'\buntagged\b',
                                  r'\bunassigned\b', r'\bN/A\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_no_false), foreground="#fcc560"))
        # ★ 匹配网口名称+序号 前景色-青色
        match_pattern_interface_number = [r'\bmeth[" "]{,1}(\d{1,3}/){2,}\d{1,3}\b',
                                          r'\bGigabitEthernet[" "]{,1}(\d{1,3}/){2,}\d{1,3}\b',
                                          r'\bGe[" "]{,1}(\d{1,3}/){2,}\d{1,3}\b',
                                          r'\bEthernet[" "]{,1}(\d{1,3}/){2,}\d{1,3}\b',
                                          r'\bvlan(if){,1}[" "]{,1}\d{1,4}\b',
                                          r'\bnull[" "]{,1}\d{1,4}\b',
                                          r'\b(in){,1}loop(back){,1}[" "]{,1}\d{1,4}\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_interface_number), foreground="cyan"))
        # ★ 匹配 关键字 前景色-青 #0095d3
        match_pattern_key_words = [r'\binterface[^:]\b',
                                   r'\baaa\b',
                                   r'\breturn\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_key_words), foreground="#0095d3"))
        # ★ 匹配 undo 前景色-红 下划线
        match_pattern_undo = [r'\bundo\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_undo), foreground="red", underline=True,
                              underlinefg="pink"))
        # ★ 匹配 shutdown 前景色-棕 #a34826 粗体
        match_pattern_shutdown = [r'\bshutdown\b', r'\bdrop\b']
        scheme_huawei.custom_match_object_list.append(
            CustomMatchObject(match_pattern_lines="\n".join(match_pattern_shutdown), foreground="#a34826",
                              bold=True))
        scheme_huawei.save()
        self.custome_tag_config_scheme_obj_list.append(scheme_huawei)

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
                       first_auth_method=obj_info_tuple[10],
                       custome_tag_config_scheme_oid=obj_info_tuple[11],
                       global_info=self)
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
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

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
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

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
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

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

    def load_inspection_code_list_from_dbfile(self, inspection_code_block_obj_list):
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
        for inspection_code_block_obj in inspection_code_block_obj_list:
            sql = f"select * from tb_inspection_code_block_include_code_list where \
            inspection_code_block_oid='{inspection_code_block_obj.oid}'"
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                code = OneLineCode(code_index=obj_info_tuple[1], code_content=obj_info_tuple[2],
                                   code_post_wait_time=obj_info_tuple[3], need_interactive=obj_info_tuple[4],
                                   interactive_question_keyword=obj_info_tuple[5],
                                   interactive_answer=obj_info_tuple[6],
                                   interactive_process_method=obj_info_tuple[7],
                                   description=obj_info_tuple[8])
                inspection_code_block_obj.code_list.append(code)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

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
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

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
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

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
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def load_inspection_job_record_from_dbfile(self):
        """
        从sqlite3数据库文件，查找所有inspection_job_record，并输出InspectionJobRecord对象列表，output <list>
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_record'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_job_record"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        sql = f"select * from tb_inspection_job_record"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        obj_list = []
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            obj = InspectionJobRecord(oid=obj_info_tuple[0],
                                      name=obj_info_tuple[1],
                                      description=obj_info_tuple[2],
                                      project_oid=obj_info_tuple[3],
                                      inspection_template_oid=obj_info_tuple[4],
                                      job_state=int(obj_info_tuple[5]),
                                      start_time=float(obj_info_tuple[6]),
                                      end_time=float(obj_info_tuple[7]),
                                      global_info=self)
            obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        self.load_inspection_job_record_host_job_status_from_dbfile(obj_list)
        return obj_list

    def load_inspection_job_record_host_job_status_from_dbfile(self, inspection_job_record_obj_list):
        """
        从sqlite3数据库文件，xxx
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_record_host_job_status_obj_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job_record_host_job_status_obj_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for job_record_obj in inspection_job_record_obj_list:
            sql = f'select * from tb_inspection_job_record_host_job_status_obj_list where "job_record_oid"="{job_record_obj.oid}"'
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                obj = HostJobStatus(host_oid=obj_info_tuple[1],
                                    job_status=int(obj_info_tuple[2]),
                                    find_credential_status=int(obj_info_tuple[3]),
                                    exec_timeout=int(obj_info_tuple[4]),
                                    start_time=float(obj_info_tuple[5]),
                                    end_time=float(obj_info_tuple[6]),
                                    sum_of_code_block=int(obj_info_tuple[7]),
                                    current_exec_code_block=int(obj_info_tuple[8]),
                                    sum_of_code_lines=int(obj_info_tuple[9]),
                                    current_exec_code_num=int(obj_info_tuple[9]))
                job_record_obj.unduplicated_host_job_status_obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def load_inspection_job_log_for_host(self, inspection_job_record_oid, host_oid, inspection_code_block_oid):
        """
        从sqlite3数据库文件，查询某台主机的巡检作业日志，输出为<SSHOperatorOutput>对象列表
        :return:
        """
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_invoke_shell_output'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job_invoke_shell_output"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        ssh_operator_output_obj_list = []
        sql_list = ['select * from tb_inspection_job_invoke_shell_output where',
                    f'"job_oid"="{inspection_job_record_oid}"',
                    f'and "host_oid"="{host_oid}"',
                    f'and "inspection_code_oid"="{inspection_code_block_oid}"']
        sqlite_cursor.execute(" ".join(sql_list))
        search_result = sqlite_cursor.fetchall()
        for obj_info_tuple in search_result:
            obj = SSHOperatorOutput(code_index=obj_info_tuple[4],
                                    code_content='',
                                    code_exec_method=int(obj_info_tuple[5]),
                                    invoke_shell_output_bytes=base64.b64decode(obj_info_tuple[6]),
                                    invoke_shell_output_last_line_str=base64.b64decode(obj_info_tuple[7]).decode("utf8"),
                                    )
            ssh_operator_output_obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        self.load_inspection_job_interactive_output_for_host(ssh_operator_output_obj_list, inspection_job_record_oid, host_oid,
                                                             inspection_code_block_oid)
        return ssh_operator_output_obj_list

    def load_inspection_job_interactive_output_for_host(self, ssh_operator_output_obj_list, inspection_job_record_oid, host_oid,
                                                        inspection_code_block_oid):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_invoke_shell_interactive_output'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job_invoke_shell_interactive_output"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for output_obj in ssh_operator_output_obj_list:
            output_obj.interactive_output_bytes_list = []
            sql_list = ['select * from tb_inspection_job_invoke_shell_interactive_output where',
                        f'"job_oid"="{inspection_job_record_oid}"',
                        f'and "host_oid"="{host_oid}"',
                        f'and "inspection_code_oid"="{inspection_code_block_oid}"',
                        f'and "code_index"="{output_obj.code_index}"']
            sqlite_cursor.execute(" ".join(sql_list))
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                interactive_output_bytes = base64.b64decode(obj_info_tuple[6])
                output_obj.interactive_output_bytes_list.append(interactive_output_bytes)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def load_custome_tag_config_scheme(self):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_record'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_custome_tag_config_scheme"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        sql = f"select * from tb_custome_tag_config_scheme"
        sqlite_cursor.execute(sql)
        search_result = sqlite_cursor.fetchall()
        obj_list = []
        for obj_info_tuple in search_result:
            # print('tuple: ', obj_info_tuple)
            obj = CustomTagConfigScheme(oid=obj_info_tuple[0],
                                        name=obj_info_tuple[1],
                                        description=obj_info_tuple[2],
                                        project_oid=obj_info_tuple[3],
                                        create_timestamp=obj_info_tuple[4],
                                        last_modify_timestamp=obj_info_tuple[5],
                                        global_info=self)
            obj_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接
        self.load_custome_tag_config_scheme_include_match_object(obj_list)
        return obj_list

    def load_custome_tag_config_scheme_include_match_object(self, obj_list):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_record_host_job_status_obj_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_custome_tag_config_scheme_include_match_object"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则返回None
        if len(result) == 0:
            return []
        # 读取数据
        for scheme_obj in obj_list:
            sql = f'select * from tb_custome_tag_config_scheme_include_match_object where "scheme_oid"="{scheme_obj.oid}"'
            sqlite_cursor.execute(sql)
            search_result = sqlite_cursor.fetchall()
            for obj_info_tuple in search_result:
                # print('tuple: ', obj_info_tuple)
                obj = CustomMatchObject(match_pattern_lines=base64.b64decode(obj_info_tuple[1]).decode("utf8"),
                                        foreground=obj_info_tuple[2],
                                        backgroun=obj_info_tuple[3],
                                        underline=obj_info_tuple[4],
                                        underlinefg=obj_info_tuple[5],
                                        overstrike=obj_info_tuple[6],
                                        overstrikefg=obj_info_tuple[7],
                                        bold=obj_info_tuple[8],
                                        italic=obj_info_tuple[9])
                scheme_obj.custom_match_object_list.append(obj)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接

    def is_project_name_existed(self, project_name):  # 判断项目名称是否已存在项目obj_list里
        for project in self.project_obj_list:
            if project_name == project.name:
                return True
        return False

    def is_project_name_existed_except_self(self, project_name, except_obj):  # 判断名称是否已存在obj_list里
        for project in self.project_obj_list:
            if project == except_obj:
                continue
            if project_name == project.name:
                return True
        return False

    def is_credential_name_existed(self, credential_name):  # 判断名称是否已存在obj_list里
        for credential in self.credential_obj_list:
            if credential_name == credential.name:
                return True
        return False

    def is_credential_name_existed_except_self(self, credential_name, except_obj):  # 判断名称是否已存在obj_list里
        for credential in self.credential_obj_list:
            if credential == except_obj:
                continue
            if credential_name == credential.name:
                return True
        return False

    def is_host_name_existed(self, host_name):  # 判断名称是否已存在obj_list里
        for host in self.host_obj_list:
            if host_name == host.name:
                return True
        return False

    def is_host_name_existed_except_self(self, host_name, except_obj):  # 判断名称是否已存在obj_list里
        for host in self.host_obj_list:
            if host == except_obj:
                continue
            if host_name == host.name:
                return True
        return False

    def is_host_group_name_existed(self, host_group_name):  # 判断名称是否已存在obj_list里
        for host_group in self.host_group_obj_list:
            if host_group_name == host_group.name:
                return True
        return False

    def is_host_group_name_existed_except_self(self, host_group_name, except_obj):  # 判断名称是否已存在obj_list里
        for host_group in self.host_group_obj_list:
            if host_group == except_obj:
                continue
            if host_group_name == host_group.name:
                return True
        return False

    def is_inspection_code_block_name_existed(self, inspect_code_name):  # 判断名称是否已存在obj_list里
        for inspection_code in self.inspection_code_block_obj_list:
            if inspect_code_name == inspection_code.name:
                return True
        return False

    def is_inspection_code_block_name_existed_except_self(self, inspection_code_block_name, except_obj):  # 判断名称是否已存在obj_list里
        for inspection_code_block in self.inspection_code_block_obj_list:
            if inspection_code_block == except_obj:
                continue
            if inspection_code_block_name == inspection_code_block.name:
                return True
        return False

    def is_inspection_template_name_existed(self, inspect_template_name):  # 判断名称是否已存在obj_list里
        for inspection_template in self.inspection_template_obj_list:
            if inspect_template_name == inspection_template.name:
                return True
        return False

    def is_inspection_template_name_existed_except_self(self, inspection_template_name, except_obj):  # 判断名称是否已存在obj_list里
        for inspection_template in self.inspection_template_obj_list:
            if inspection_template == except_obj:
                continue
            if inspection_template_name == inspection_template.name:
                return True
        return False

    def is_custome_tag_config_scheme_name_existed(self, scheme_name):  # 判断custome_tag_config_scheme名称是否已存在
        for scheme in self.custome_tag_config_scheme_obj_list:
            if scheme_name == scheme.name:
                return True
        return False

    def is_custome_tag_config_scheme_name_existed_except_self(self, scheme_name, except_obj):  # 判断custome_tag_config_scheme名称是否已存在
        for scheme in self.custome_tag_config_scheme_obj_list:
            if scheme == except_obj:
                continue
            if scheme_name == scheme.name:
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

    def get_project_by_name(self, name):
        """
        根据项目oid/uuid<str>查找项目对象，找到时返回<Project>对象
        :param name:
        :return:
        """
        for project in self.project_obj_list:
            if project.name == name:
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

    def get_inspection_job_record_obj_by_inspection_template_oid(self, oid):
        index = 0
        existed_inspection_job_obj_list = []
        for obj in self.inspection_job_record_obj_list:
            if obj.inspection_template_oid == oid:
                existed_inspection_job_obj_list.append(obj)
            index += 1
        return existed_inspection_job_obj_list

    def get_launch_template_trigger_obj_by_oid(self, oid):
        index = 0
        for obj in self.launch_template_trigger_obj_list:
            if obj.oid == oid:
                return obj
            index += 1
        return None

    def get_custome_tag_config_scheme_by_oid(self, oid):
        for scheme in self.custome_tag_config_scheme_obj_list:
            if scheme.oid == oid:
                return scheme
        return None

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
        # ★查询是否有名为'tb_host_include_credential_oid_list'的表★
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
        # ★查询是否有名为'tb_inspection_template_include_inspection_code_block_list'的表★
        sql = f'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_template_include_inspection_code_block_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_template_include_inspection_code_block_list where inspection_template_oid='{obj.oid}' "
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.inspection_template_obj_list.remove(obj)

    def delete_inspection_job_record_obj(self, obj):
        """
        直接删除 inspection_job_record 对象
        :param obj:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_job_record'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_job_record"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_job_record where oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_job_record_host_job_status_obj_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_job_record_host_job_status_obj_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_job_record_host_job_status_obj_list where job_record_oid='{obj.oid}' "
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_job_invoke_shell_output'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_job_invoke_shell_output"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_job_invoke_shell_output where job_oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_job_invoke_shell_interactive_output'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_inspection_job_invoke_shell_interactive_output"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_inspection_job_invoke_shell_interactive_output where job_oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.inspection_job_record_obj_list.remove(obj)

    def delete_custome_tag_config_scheme_obj(self, obj):
        """
        直接删除 CustomTagConfigScheme 对象
        :param obj:
        :return:
        """
        # ★先从数据库删除
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_custome_tag_config_scheme'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_custome_tag_config_scheme"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_custome_tag_config_scheme where oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_custome_tag_config_scheme_include_match_object'的表★
        sql = 'SELECT * FROM sqlite_master WHERE \
                    "type"="table" and "tbl_name"="tb_custome_tag_config_scheme_include_match_object"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()
        if len(result) != 0:  # 若查询到有此表，才删除相应数据
            sql = f"delete from tb_custome_tag_config_scheme_include_match_object where scheme_oid='{obj.oid}'"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()
        sqlite_conn.close()
        # ★最后再从内存obj_list删除
        self.custome_tag_config_scheme_obj_list.remove(obj)


class MainWindow:
    """
    CofAble主界面类，包含菜单栏及左右2个frame
    """

    def __init__(self, width=800, height=480, title='', current_project=None, global_info=None):
        self.title = title
        self.width = width
        self.height = height
        self.resizable = True  # True 表示宽度和高度可由用户手动调整
        self.minsize = (480, 320)
        self.maxsize = (1920, 1080)
        self.background = "#3A3A3A"  # 设置背景色，RGB
        self.window_obj = None  # 在 MainWindow.show()里创建
        self.menu_bar = None  # 在 MainWindow.create_menu_bar_init()里创建
        self.nav_frame_l = None  # 在 MainWindow.create_nav_frame_l_init()里创建
        self.nav_frame_r = None  # 在 MainWindow.create_nav_frame_r_init()里创建
        self.screen_width = 0  # 在 MainWindow.show()里赋值
        self.screen_height = 0  # 在 MainWindow.show()里赋值
        self.nav_frame_l_width = int(self.width * 0.2)
        self.nav_frame_r_width = int(self.width * 0.8)
        self.nav_frame_r_top_height = 35
        self.nav_frame_r_bottom_height = self.height - 35
        self.global_info = global_info  # <GlobalInfo>对象
        self.current_project = current_project
        self.about_info_list = ["CofAble，可视化运维巡检工具，个人运维工具中的瑞士军刀",
                                "版本:  v1.0 dev",
                                "本软件使用GPL-v3.0协议开源",
                                "作者:  Cof-Lee（李茂福）",
                                "更新时间: 2024-04-12"]
        self.padx = 2
        self.pady = 2
        self.view_width = 20
        self.menu_bar = None

    @staticmethod
    def clear_tkinter_widget(root):
        for widget in root.winfo_children():
            widget.destroy()

    def load_main_window_init_widget(self):
        """
        加载程序初始化界面控件
        :return:
        """
        # 首先清空主window
        self.clear_tkinter_widget(self.window_obj)
        # 加载菜单栏
        self.create_menu_bar_init()
        # 创建导航框架1，主界面左边的导航框
        self.create_nav_frame_l_init()
        # 创建导航框架2，主界面右边的资源信息框
        self.create_nav_frame_r_init()

    def create_menu_bar_init(self):
        """
        创建菜单栏-主界面的
        创建完菜单栏后，一般不会再修改此组件了
        :return:
        """
        self.menu_bar = tkinter.Menu(self.window_obj)  # 创建一个菜单，做菜单栏
        # 创建一个菜单，做1级子菜单，不分窗，表示此菜单不可拉出来变成一个可移动的独立弹窗
        menu_file = tkinter.Menu(self.menu_bar, tearoff=0, activebackground="green", activeforeground="white",
                                 background="white", foreground="black")
        menu_settings = tkinter.Menu(self.menu_bar, tearoff=0, activebackground="green", activeforeground="white",
                                     background="white", foreground="black")  # 创建一个菜单，1级子菜单
        menu_tools = tkinter.Menu(self.menu_bar, tearoff=0, activebackground="green", activeforeground="white",
                                  background="white", foreground="black")  # 创建一个菜单，1级子菜单
        menu_help = tkinter.Menu(self.menu_bar, tearoff=0, activebackground="green", activeforeground="white",
                                 background="white", foreground="black")  # 创建一个菜单，做1级子菜单
        # 菜单栏添加1级子菜单
        self.menu_bar.add_cascade(label="File", menu=menu_file)
        self.menu_bar.add_cascade(label="Settings", menu=menu_settings)
        self.menu_bar.add_cascade(label="Tools", menu=menu_tools)
        self.menu_bar.add_cascade(label="Help", menu=menu_help)
        # 1级子菜单添加2级子菜单（功能按钮）
        menu_file.add_command(label="打开数据库文件", command=self.click_menu_open_db_file_of_menu_bar_init)
        menu_settings.add_command(label="配色方案设置", command=self.click_menu_settings_scheme_of_menu_bar_init)
        menu_settings.add_command(label="vt100终端设置", command=self.click_menu_settings_vt100_of_menu_bar_init, background="#aaaaaa")
        menu_tools.add_command(label="工具")
        menu_help.add_command(label="About", command=self.click_menu_about_of_menu_bar_init)
        self.window_obj.config(menu=self.menu_bar)

    def create_nav_frame_l_init(self):
        """
        创建导航框架1-init界面的，主界面左边的导航框 ★★★★★
        :return:
        """
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
        # Jobs巡检作业-选项按钮
        menu_button_inspection_template = tkinter.Button(self.nav_frame_l, text="Jobs巡检作业", width=self.nav_frame_l_width,
                                                         height=2, bg="white",
                                                         command=lambda: self.nav_frame_r_resource_top_page_display(
                                                             RESOURCE_TYPE_INSPECTION_JOB))
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
        print(label_current_project_content)

    def create_nav_frame_r_init(self):
        """
        创建导航框架2-init界面的，主界面右边的资源信息框
        此界面为运行程序后的初始化界面，点击左侧导航栏的各个资源按钮后，此界面就被更新了，变成其他的功能界面了
        :return:
        """
        self.nav_frame_r = tkinter.Frame(self.window_obj, bg="blue", width=self.nav_frame_r_width, height=self.height)
        self.nav_frame_r.grid_propagate(False)
        self.nav_frame_r.pack_propagate(False)
        self.nav_frame_r.grid(row=0, column=1)
        # 在框架2中添加canvas-frame滚动框
        self.clear_tkinter_widget(self.nav_frame_r)
        scrollbar = tkinter.Scrollbar(self.nav_frame_r)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        canvas = tkinter.Canvas(self.nav_frame_r, yscrollcommand=scrollbar.set)  # 创建画布
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
        label_inspect_job_count_str = "巡检作业数量".ljust(self.view_width - 4, " ") + ": " \
                                      + str(len(self.global_info.inspection_job_record_obj_list))
        label_inspect_job_count = tkinter.Label(self.nav_frame_r, text=label_inspect_job_count_str)
        label_inspect_job_count.grid(row=7, column=0)

    def refresh_label_current_time(self, label):
        """
        每秒钟更新左侧导航栏下面的时间
        :param label:
        :return:
        """
        label.__setitem__('text', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        # 继续调用回调函数更新label
        self.window_obj.after(1000, self.refresh_label_current_time, label)

    def click_menu_about_of_menu_bar_init(self):
        messagebox.showinfo("About", "\n".join(self.about_info_list))

    def click_menu_settings_vt100_of_menu_bar_init(self):
        pass

    def click_menu_settings_scheme_of_menu_bar_init(self):
        """
        点击菜单栏上的 “Settings”→"配色方案设置" 后，进入配色方案设置界面（子窗口）
        :return:
        """
        pop_window = tkinter.Toplevel(self.window_obj)
        pop_window.title("配色方案设置")
        screen_width = self.window_obj.winfo_screenwidth()
        screen_height = self.window_obj.winfo_screenheight()
        width = self.nav_frame_r_width
        height = self.height
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.window_obj.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        pop_window.protocol("WM_DELETE_WINDOW", lambda: self.on_closing_settings_scheme_pop_window(pop_window))
        # 创建2个容器Frame
        top_frame = tkinter.Frame(pop_window, width=width, height=35, bg="pink")
        bottom_frame = tkinter.Frame(pop_window, width=width, height=height - 35, bg="green")
        top_frame.grid_propagate(False)
        bottom_frame.pack_propagate(False)
        top_frame.grid(row=0, column=0)
        bottom_frame.grid(row=1, column=0)
        # 在top_frame添加功能按钮
        button_create_resource = tkinter.Button(top_frame, text="创建方案",
                                                command=lambda: self.create_custom_tag_config_scheme_of_pop_window(pop_window))
        button_create_resource.grid(row=0, column=0, padx=self.padx)
        button_load_resource = tkinter.Button(top_frame, text="导入方案",
                                              command=lambda: self.create_custom_tag_config_scheme_of_pop_window(pop_window))
        button_load_resource.grid(row=0, column=1, padx=self.padx)
        button_other = tkinter.Button(top_frame, text="其他")
        button_other.grid(row=0, column=2, padx=self.padx)
        # 在bottom_frame创建滚动Frame，用于列出配色方案列表
        bottom_frame_widget_dict = {"pop_window": pop_window}
        self.clear_tkinter_widget(bottom_frame)
        bottom_frame_widget_dict["scrollbar_normal"] = tkinter.Scrollbar(bottom_frame)
        bottom_frame_widget_dict["scrollbar_normal"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        bottom_frame_widget_dict["canvas"] = tkinter.Canvas(bottom_frame, yscrollcommand=bottom_frame_widget_dict["scrollbar_normal"].set)
        bottom_frame_widget_dict["canvas"].place(x=0, y=0, width=width - 20, height=height - 35)
        bottom_frame_widget_dict["scrollbar_normal"].config(command=bottom_frame_widget_dict["canvas"].yview)
        bottom_frame_widget_dict["frame"] = tkinter.Frame(bottom_frame_widget_dict["canvas"])
        bottom_frame_widget_dict["frame"].pack(fill=tkinter.X, expand=tkinter.TRUE)
        bottom_frame_widget_dict["canvas"].create_window((0, 0), window=bottom_frame_widget_dict["frame"], anchor='nw')
        # 在canvas-frame滚动框内添加资源列表控件
        list_obj = ListResourceInFrame(bottom_frame_widget_dict, self.global_info, RESOURCE_TYPE_CUSTOM_SCHEME)
        list_obj.show()

    def on_closing_settings_scheme_pop_window(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.window_obj.focus_force()  # 使主窗口获得焦点

    def create_custom_tag_config_scheme_of_pop_window(self, pop_window):
        for widget in pop_window.winfo_children():
            widget.destroy()
        # 在配色方案设置pop_window中添加canvas-frame滚动框
        pop_window_widget_dict = {"scrollbar_normal": tkinter.Scrollbar(pop_window)}
        pop_window_widget_dict["scrollbar_normal"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        pop_window_widget_dict["canvas"] = tkinter.Canvas(pop_window, yscrollcommand=pop_window_widget_dict["scrollbar_normal"].set)
        pop_window_widget_dict["canvas"].place(x=0, y=0, width=self.nav_frame_r_width - 25, height=self.height - 50)
        pop_window_widget_dict["scrollbar_normal"].config(command=pop_window_widget_dict["canvas"].yview)
        pop_window_widget_dict["frame"] = tkinter.Frame(pop_window_widget_dict["canvas"])
        pop_window_widget_dict["frame"].pack()
        pop_window_widget_dict["canvas"].create_window((0, 0), window=pop_window_widget_dict["frame"], anchor='nw')
        pop_window_widget_dict["pop_window"] = pop_window
        # ★在canvas-frame滚动框内添加创建资源控件
        create_obj = CreateResourceInFrame(pop_window_widget_dict, self.global_info, RESOURCE_TYPE_CUSTOM_SCHEME)
        create_obj.show()
        # ★创建“保存”按钮
        save_obj = SaveResourceInMainWindow(create_obj.resource_info_dict, self.global_info, RESOURCE_TYPE_CUSTOM_SCHEME)
        button_save = tkinter.Button(pop_window, text="保存", command=save_obj.save)
        button_save.place(x=10, y=self.height - 40, width=50, height=25)
        # ★创建“取消”按钮
        button_cancel = tkinter.Button(pop_window, text="取消",
                                       command=lambda: self.back_to_custom_tag_config_pop_window(pop_window))  # 返回
        button_cancel.place(x=110, y=self.height - 40, width=50, height=25)

    def back_to_custom_tag_config_pop_window(self, pop_window):
        pop_window.destroy()
        self.window_obj.focus_force()
        self.click_menu_settings_scheme_of_menu_bar_init()

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
                self.nav_frame_r_top_height = 35
                self.nav_frame_r_bottom_height = int(self.height - 35)
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
        在 资源选项卡-主页面 点击“创建资源”时，进入此界面（更新资源选项卡-主页面）
        :return:
        """
        # 更新导航框架2
        self.nav_frame_r.__setitem__("bg", "green")
        nav_frame_r_widget_dict = {}
        # 在框架2中添加canvas-frame滚动框
        self.clear_tkinter_widget(self.nav_frame_r)
        nav_frame_r_widget_dict["scrollbar_normal"] = tkinter.Scrollbar(self.nav_frame_r)
        nav_frame_r_widget_dict["scrollbar_normal"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        nav_frame_r_widget_dict["canvas"] = tkinter.Canvas(self.nav_frame_r, yscrollcommand=nav_frame_r_widget_dict["scrollbar_normal"].set)
        nav_frame_r_widget_dict["canvas"].place(x=0, y=0, width=self.nav_frame_r_width - 25, height=self.height - 50)
        nav_frame_r_widget_dict["scrollbar_normal"].config(command=nav_frame_r_widget_dict["canvas"].yview)
        nav_frame_r_widget_dict["frame"] = tkinter.Frame(nav_frame_r_widget_dict["canvas"])
        nav_frame_r_widget_dict["frame"].pack()
        nav_frame_r_widget_dict["canvas"].create_window((0, 0), window=nav_frame_r_widget_dict["frame"], anchor='nw')
        # ★在canvas - frame滚动框内添加创建资源控件
        create_obj = CreateResourceInFrame(nav_frame_r_widget_dict, self.global_info, resource_type)
        create_obj.show()
        # ★创建“保存”按钮
        save_obj = SaveResourceInMainWindow(create_obj.resource_info_dict, self.global_info, resource_type)
        button_save = tkinter.Button(self.nav_frame_r, text="保存", command=save_obj.save)
        button_save.place(x=10, y=self.height - 40, width=50, height=25)
        # ★创建“取消”按钮
        button_cancel = tkinter.Button(self.nav_frame_r, text="取消",
                                       command=lambda: self.nav_frame_r_resource_top_page_display(resource_type))  # 返回资源选项卡主界面
        button_cancel.place(x=110, y=self.height - 40, width=50, height=25)

    def list_resource_of_nav_frame_r_bottom_page(self, resource_type):
        """
        ★★★★★ 列出资源-页面 ★★★★★
        :return:
        """
        # 更新bottom_frame
        bottom_frame = self.nav_frame_r.winfo_children()[1]
        bottom_frame.__setitem__("bg", "pink")
        nav_frame_r_widget_dict = {}
        # 在框架2的bottom_frame中添加canvas-frame滚动框
        self.clear_tkinter_widget(bottom_frame)
        nav_frame_r_widget_dict["scrollbar_normal"] = tkinter.Scrollbar(bottom_frame)
        nav_frame_r_widget_dict["scrollbar_normal"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        nav_frame_r_widget_dict["canvas"] = tkinter.Canvas(bottom_frame, yscrollcommand=nav_frame_r_widget_dict["scrollbar_normal"].set)
        nav_frame_r_widget_dict["canvas"].place(x=0, y=0, width=int(self.nav_frame_r_width - 25),
                                                height=self.nav_frame_r_bottom_height)
        nav_frame_r_widget_dict["scrollbar_normal"].config(command=nav_frame_r_widget_dict["canvas"].yview)
        nav_frame_r_widget_dict["frame"] = tkinter.Frame(nav_frame_r_widget_dict["canvas"])
        nav_frame_r_widget_dict["frame"].pack(fill=tkinter.X, expand=tkinter.TRUE)
        nav_frame_r_widget_dict["canvas"].create_window((0, 0), window=nav_frame_r_widget_dict["frame"], anchor='nw')
        # 在canvas-frame滚动框内添加资源列表控件
        list_obj = ListResourceInFrame(nav_frame_r_widget_dict, self.global_info, resource_type)
        list_obj.show()

    def nav_frame_r_resource_top_page_display(self, resource_type):
        """
        资源选项卡-主页面，将self.nav_frame_r再分为上下2个界面:
        frame_top_of_nav_frame_r_page 和 frame_bottom_of_nav_frame_r_page （局部变量，非全局）
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
        self.nav_frame_r.__setitem__("bg", "gray")
        # 在框架2中添加功能控件
        self.clear_tkinter_widget(self.nav_frame_r)
        if resource_type == RESOURCE_TYPE_PROJECT:
            text_create = "创建项目"
            text_load = "导入项目"
        elif resource_type == RESOURCE_TYPE_CREDENTIAL:
            text_create = "创建凭据"
            text_load = "导入凭据"
        elif resource_type == RESOURCE_TYPE_HOST:
            text_create = "创建主机"
            text_load = "导入主机"
        elif resource_type == RESOURCE_TYPE_HOST_GROUP:
            text_create = "创建主机组"
            text_load = "导入主机组"
        elif resource_type == RESOURCE_TYPE_INSPECTION_CODE_BLOCK:
            text_create = "创建巡检代码块"
            text_load = "导入巡检代码块"
        elif resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
            text_create = "创建巡检模板"
            text_load = "导入巡检模板"
        elif resource_type == RESOURCE_TYPE_INSPECTION_JOB:
            text_create = "创建巡检作业"
            text_load = "导入巡检作业"
        else:
            print("unknown resource type")
            text_create = "创建项目"
            text_load = "导入项目"
        if resource_type != RESOURCE_TYPE_INSPECTION_JOB:
            for widget in self.nav_frame_r.winfo_children():
                widget.destroy()
            # 将主界面右侧frame一分为二，self.nav_frame_r分为上下2个frame
            frame_top_of_nav_frame_r_page = tkinter.Frame(self.nav_frame_r, bg="green", width=self.nav_frame_r_width, height=35)
            frame_bottom_of_nav_frame_r_page = tkinter.Frame(self.nav_frame_r, bg="pink", width=self.nav_frame_r_width,
                                                             height=self.height - 35)
            frame_top_of_nav_frame_r_page.grid_propagate(False)
            frame_top_of_nav_frame_r_page.pack_propagate(False)
            frame_top_of_nav_frame_r_page.grid(row=0, column=0)
            frame_bottom_of_nav_frame_r_page.grid_propagate(False)
            frame_bottom_of_nav_frame_r_page.pack_propagate(False)
            frame_bottom_of_nav_frame_r_page.grid(row=1, column=0)
            # 在 frame_top_of_nav_frame_r_page 中添加功能按钮
            button_create_resource = tkinter.Button(frame_top_of_nav_frame_r_page, text=text_create,
                                                    command=lambda: self.create_resource_of_nav_frame_r_page(resource_type))
            button_create_resource.pack(padx=self.padx, side=tkinter.LEFT)
            button_load_resource = tkinter.Button(frame_top_of_nav_frame_r_page, text=text_load,
                                                  command=lambda: self.create_resource_of_nav_frame_r_page(resource_type))
            button_load_resource.pack(padx=self.padx, side=tkinter.LEFT)
            button_other = tkinter.Button(frame_top_of_nav_frame_r_page, text="其他")
            button_other.pack(padx=self.padx, side=tkinter.LEFT)
            # 在 frame_bottom_of_nav_frame_r_page 中列出资源列表
            self.list_resource_of_nav_frame_r_bottom_page(resource_type)
        else:
            self.list_inspection_job_of_nav_frame_r_page()

    def list_inspection_job_of_nav_frame_r_page(self):
        # 更新导航框架2
        self.nav_frame_r.__setitem__("bg", "green")
        nav_frame_r_widget_dict = {}
        # 在框架2中添加canvas-frame滚动框
        self.clear_tkinter_widget(self.nav_frame_r)
        # 没有将self.nav_frame_r分为多个frame，就一个frame用于显示作业列表
        nav_frame_r_widget_dict["scrollbar_normal"] = tkinter.Scrollbar(self.nav_frame_r)
        nav_frame_r_widget_dict["scrollbar_normal"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        nav_frame_r_widget_dict["canvas"] = tkinter.Canvas(self.nav_frame_r,
                                                           yscrollcommand=nav_frame_r_widget_dict["scrollbar_normal"].set)
        nav_frame_r_widget_dict["canvas"].place(x=0, y=0, width=self.nav_frame_r_width - 25, height=self.height - 50)
        nav_frame_r_widget_dict["scrollbar_normal"].config(command=nav_frame_r_widget_dict["canvas"].yview)
        nav_frame_r_widget_dict["frame"] = tkinter.Frame(nav_frame_r_widget_dict["canvas"])
        nav_frame_r_widget_dict["frame"].pack(fill=tkinter.X, expand=tkinter.TRUE)
        nav_frame_r_widget_dict["canvas"].create_window((0, 0), window=nav_frame_r_widget_dict["frame"], anchor='nw')
        # 在canvas-frame滚动框内添加资源列表控件
        list_obj = ListInspectionJobInFrame(nav_frame_r_widget_dict, self.global_info)
        list_obj.show()

    def show(self):
        self.window_obj = tkinter.Tk()  # ★★★创建主窗口对象★★★
        self.screen_width = self.window_obj.winfo_screenwidth()
        self.screen_height = self.window_obj.winfo_screenheight()
        self.window_obj.title(self.title)  # 设置窗口标题
        # self.window_obj.iconbitmap(bitmap="D:\\test.ico")  # 设置窗口图标，默认为羽毛图标
        win_pos_x = self.screen_width // 2 - self.width // 2
        win_pos_y = self.screen_height // 2 - self.height // 2
        win_pos = f"{self.width}x{self.height}+{win_pos_x}+{win_pos_y}"
        self.window_obj.geometry(win_pos)  # 设置窗口大小及位置，居中
        self.window_obj.resizable(width=self.resizable, height=self.resizable)  # True 表示宽度和高度可由用户手动调整
        self.window_obj.minsize(*self.minsize)  # 可调整的最小宽度及高度
        self.window_obj.maxsize(*self.maxsize)  # 可调整的最大宽度及高度
        self.window_obj.pack_propagate(True)  # True表示窗口内的控件大小自适应
        self.window_obj.configure(bg=self.background)  # 设置主窗口背景色，RGB
        # 加载初始化界面控件
        self.load_main_window_init_widget()  # ★★★ 接下来，所有的事情都在此界面操作 ★★★
        # 监听窗口大小变化事件，自动更新窗口内控件大小（未完善，暂时不搞这个）
        self.window_obj.bind('<Configure>', self.reload_current_resized_window)
        # 子窗口点击右上角的关闭按钮后，触发此函数
        self.window_obj.protocol("WM_DELETE_WINDOW", self.on_closing_main_window)
        # 运行窗口主循环
        self.window_obj.mainloop()

    def on_closing_main_window(self):
        self.global_info.exit_division_terminal_window()
        print("MainWindow: 退出了主程序")
        # self.window_obj.destroy()
        self.window_obj.quit()


class CreateResourceInFrame:
    """
    在主窗口的创建资源界面，添加用于输入资源信息的控件
    """

    def __init__(self, top_frame_widget_dict=None, global_info=None, resource_type=RESOURCE_TYPE_PROJECT):
        self.top_frame_widget_dict = top_frame_widget_dict  # 在 top_frame_widget_dict["frame"]里添加组件，用于设置要创建的资源的属性
        self.global_info = global_info
        self.resource_type = resource_type
        self.resource_info_dict = {}  # 用于存储要创建的资源对象信息，传出信息给其<SaveResourceInMainWindow>对象进行处理
        self.padx = 2
        self.pady = 2

    def proces_mouse_scroll_of_top_frame(self, event):
        if event.delta > 0:
            self.top_frame_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.top_frame_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def update_top_frame(self):
        # 更新Frame的尺寸
        self.top_frame_widget_dict["frame"].update_idletasks()
        self.top_frame_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.top_frame_widget_dict["frame"].winfo_width(),
                          self.top_frame_widget_dict["frame"].winfo_height()))
        self.top_frame_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        self.top_frame_widget_dict["frame"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        # 滚动条移到最开头
        self.top_frame_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def show(self):
        for widget in self.top_frame_widget_dict["frame"].winfo_children():
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
        elif self.resource_type == RESOURCE_TYPE_CUSTOM_SCHEME:
            self.create_custom_tag_config_scheme()
        else:
            print("<class CreateResourceInFrame> resource_type is Unknown")
        self.update_top_frame()  # 更新Frame的尺寸，并将滚动条移到最开头

    def create_project(self):
        # ★创建-project
        label_create_project = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 创建项目 ★★")
        label_create_project.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_create_project.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★project-名称
        label_project_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目名称")
        label_project_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_project_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_project_name = tkinter.Entry(self.top_frame_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_project_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_project_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★project-描述
        label_project_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_project_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_project_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_project_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_description"])
        entry_project_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_project_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)

    def create_credential(self):
        # ★创建-credential
        label_create_credential = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 创建凭据 ★★")
        label_create_credential.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_create_credential.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★credential-名称
        label_credential_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="凭据名称")
        label_credential_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_credential_name = tkinter.Entry(self.top_frame_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_credential_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★credential-描述
        label_credential_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_credential_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_credential_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                     textvariable=self.resource_info_dict["sv_description"])
        entry_credential_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★credential-所属项目
        label_credential_project = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_credential_project.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★credential-凭据类型
        label_credential_type = tkinter.Label(self.top_frame_widget_dict["frame"], text="凭据类型")
        label_credential_type.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_type.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        cred_type_name_list = ["ssh_password", "ssh_key", "telnet", "ftp", "registry", "git"]
        self.resource_info_dict["combobox_cred_type"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=cred_type_name_list,
                                                                     state="readonly")
        self.resource_info_dict["combobox_cred_type"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★credential-用户名
        label_credential_username = tkinter.Label(self.top_frame_widget_dict["frame"], text="username")
        label_credential_username.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_username.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_username"] = tkinter.StringVar()
        entry_credential_username = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_username"])
        entry_credential_username.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_username.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★credential-密码
        label_credential_password = tkinter.Label(self.top_frame_widget_dict["frame"], text="password")
        label_credential_password.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_password.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_password"] = tkinter.StringVar()
        entry_credential_password = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_password"])
        entry_credential_password.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_password.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★credential-密钥
        label_credential_private_key = tkinter.Label(self.top_frame_widget_dict["frame"], text="ssh_private_key")
        label_credential_private_key.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_private_key.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["text_private_key"] = tkinter.Text(master=self.top_frame_widget_dict["frame"], height=3, width=32)
        self.resource_info_dict["text_private_key"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权类型
        label_credential_privilege_escalation_method = tkinter.Label(self.top_frame_widget_dict["frame"],
                                                                     text="privilege_escalation_method")
        label_credential_privilege_escalation_method.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_privilege_escalation_method.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        privilege_escalation_method_list = ["su", "sudo"]
        self.resource_info_dict["combobox_privilege_escalation_method"] = \
            ttk.Combobox(self.top_frame_widget_dict["frame"], values=privilege_escalation_method_list, state="readonly")
        self.resource_info_dict["combobox_privilege_escalation_method"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权用户
        label_credential_privilege_escalation_username = tkinter.Label(self.top_frame_widget_dict["frame"],
                                                                       text="privilege_escalation_username")
        label_credential_privilege_escalation_username.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_privilege_escalation_username.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_privilege_escalation_username"] = tkinter.StringVar()
        entry_credential_privilege_escalation_username = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                                       textvariable=self.resource_info_dict[
                                                                           "sv_privilege_escalation_username"])
        entry_credential_privilege_escalation_username.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_privilege_escalation_username.grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权密码
        label_credential_privilege_escalation_password = tkinter.Label(self.top_frame_widget_dict["frame"],
                                                                       text="privilege_escalation_password")
        label_credential_privilege_escalation_password.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_privilege_escalation_password.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_privilege_escalation_password"] = tkinter.StringVar()
        entry_credential_privilege_escalation_password = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                                       textvariable=self.resource_info_dict[
                                                                           "sv_privilege_escalation_password"])
        entry_credential_privilege_escalation_password.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_privilege_escalation_password.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★credential-auth_url
        label_credential_auth_url = tkinter.Label(self.top_frame_widget_dict["frame"], text="auth_url")
        label_credential_auth_url.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_auth_url.grid(row=11, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_auth_url"] = tkinter.StringVar()
        entry_credential_auth_url = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_auth_url"])
        entry_credential_auth_url.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_auth_url.grid(row=11, column=1, padx=self.padx, pady=self.pady)
        # ★credential-ssl_verify
        label_credential_ssl_verify = tkinter.Label(self.top_frame_widget_dict["frame"], text="ssl_verify")
        label_credential_ssl_verify.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_ssl_verify.grid(row=12, column=0, padx=self.padx, pady=self.pady)
        ssl_verify_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_ssl_verify"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=ssl_verify_name_list,
                                                                      state="readonly")
        self.resource_info_dict["combobox_ssl_verify"].grid(row=12, column=1, padx=self.padx, pady=self.pady)

    def create_host(self):
        # ★创建-host
        label_create_host = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 创建主机 ★★")
        label_create_host.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_create_host.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★host-名称
        label_host_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机名称")
        label_host_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_host_name = tkinter.Entry(self.top_frame_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_host_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★host-描述
        label_host_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_host_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_host_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                               textvariable=self.resource_info_dict["sv_description"])
        entry_host_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★host-所属项目
        label_host_project = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_host_project.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★host-address
        label_host_address = tkinter.Label(self.top_frame_widget_dict["frame"], text="address")
        label_host_address.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_address.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_address"] = tkinter.StringVar()
        entry_host_address = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                           textvariable=self.resource_info_dict["sv_address"])
        entry_host_address.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_address.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★host-ssh_port
        label_host_ssh_port = tkinter.Label(self.top_frame_widget_dict["frame"], text="ssh_port")
        label_host_ssh_port.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_ssh_port.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_ssh_port"] = tkinter.StringVar()
        entry_host_ssh_port = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                            textvariable=self.resource_info_dict["sv_ssh_port"])
        entry_host_ssh_port.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_ssh_port.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★host-telnet_port
        label_host_telnet_port = tkinter.Label(self.top_frame_widget_dict["frame"], text="telnet_port")
        label_host_telnet_port.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_telnet_port.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_telnet_port"] = tkinter.StringVar()
        entry_host_telnet_port = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                               textvariable=self.resource_info_dict["sv_telnet_port"])
        entry_host_telnet_port.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_telnet_port.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★host-login_protocol
        label_host_login_protocol = tkinter.Label(self.top_frame_widget_dict["frame"], text="远程登录类型")
        label_host_login_protocol.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_login_protocol.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        login_protocol_name_list = ["ssh", "telnet"]
        self.resource_info_dict["combobox_login_protocol"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                          values=login_protocol_name_list,
                                                                          state="readonly")
        self.resource_info_dict["combobox_login_protocol"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★host-first_auth_method
        label_host_first_auth_method = tkinter.Label(self.top_frame_widget_dict["frame"], text="优先认证类型")
        label_host_first_auth_method.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_first_auth_method.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        first_auth_method_name_list = ["priKey", "password"]
        self.resource_info_dict["combobox_first_auth_method"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                             values=first_auth_method_name_list,
                                                                             state="readonly")
        self.resource_info_dict["combobox_first_auth_method"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★host-custom_scheme 终端配色方案
        label_host_custom_scheme = tkinter.Label(self.top_frame_widget_dict["frame"], text="终端配色方案")
        label_host_custom_scheme.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_custom_scheme.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        custom_scheme_name_list = []
        for scheme in self.global_info.custome_tag_config_scheme_obj_list:
            custom_scheme_name_list.append(scheme.name)
        self.resource_info_dict["combobox_custom_scheme"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                         values=custom_scheme_name_list,
                                                                         state="readonly")
        self.resource_info_dict["combobox_custom_scheme"].grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★host-凭据列表
        label_credential_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="凭据列表")
        label_credential_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_list.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        frame.grid(row=10, column=1, padx=self.padx, pady=self.pady)

    def create_host_group(self):
        # ★创建-host_group
        label_create_host_group = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 创建主机组 ★★")
        label_create_host_group.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_create_host_group.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★host_group-名称
        label_host_group_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机组名称")
        label_host_group_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_host_group_name = tkinter.Entry(self.top_frame_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_host_group_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_group_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-描述
        label_host_group_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_host_group_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_host_group_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                     textvariable=self.resource_info_dict["sv_description"])
        entry_host_group_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_group_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-所属项目
        label_host_group_project = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_host_group_project.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★添加host_group列表
        label_host_group_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机组列表")
        label_host_group_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_list.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        label_host_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机列表")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_list.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        label_create_inspection_code_block = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 创建巡检代码块 ★★")
        label_create_inspection_code_block.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_create_inspection_code_block.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-名称
        label_inspection_code_block_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检代码块名称")
        label_inspection_code_block_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_code_block_name = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                         textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_code_block_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_code_block_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-描述
        label_inspection_code_block_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_inspection_code_block_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_code_block_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                                textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_code_block_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_code_block_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-所属项目
        label_inspection_code_block_project = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_inspection_code_block_project.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★★★添加巡检代码内容并在treeview里显示★★★
        self.resource_info_dict["one_line_code_obj_list"] = []
        label_inspection_code_block_code_content = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检代码内容:")
        label_inspection_code_block_code_content.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_code_content.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        button_add_code_list = tkinter.Button(self.top_frame_widget_dict["frame"], text="添加",
                                              command=lambda: self.create_inspection_code_block__click_button_add_code_list(
                                                  treeview_code_content))  # 添加代码
        button_add_code_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        button_add_code_list.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        treeview_code_content = ttk.Treeview(self.top_frame_widget_dict["frame"], cursor="arrow", height=7,
                                             columns=("index", "code_content", "need_interactive"), show="headings")
        # 设置每一个列的宽度和对齐的方式
        treeview_code_content.column("index", width=50, anchor="w")
        treeview_code_content.column("code_content", width=300, anchor="w")
        treeview_code_content.column("need_interactive", width=80, anchor="w")
        # 设置每个列的标题
        treeview_code_content.heading("index", text="index", anchor="w")
        treeview_code_content.heading("code_content", text="code_content", anchor="w")
        treeview_code_content.heading("need_interactive", text="需要交互", anchor="w")
        treeview_code_content.grid(row=5, column=0, columnspan=2, padx=self.padx, pady=self.pady)
        # 单击每行命令后，可单独设置每行命令的高级属性
        treeview_code_content.bind("<<TreeviewSelect>>", lambda event: self.create_inspection_code_block__edit_treeview_code_content_item(
            event, treeview_code_content))

    def create_inspection_code_block__click_button_add_code_list(self, treeview_code_content):
        self.resource_info_dict["one_line_code_obj_list"] = []
        pop_window = tkinter.Toplevel(self.global_info.main_window.window_obj)
        pop_window.title("添加巡检代码内容")
        screen_width = self.global_info.main_window.window_obj.winfo_screenwidth()
        screen_height = self.global_info.main_window.window_obj.winfo_screenheight()
        width = 420
        height = 300
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.global_info.main_window.window_obj.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        pop_window.protocol("WM_DELETE_WINDOW", lambda: self.create_inspection_code_block__edit_or_add_treeview_code_content_on_closing(
            pop_window))
        label_inspection_code_block_code_content = tkinter.Label(pop_window, text="巡检代码内容")
        label_inspection_code_block_code_content.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        text_code_content = tkinter.Text(master=pop_window, width=50, height=16)
        text_code_content.grid(row=1, column=0, columnspan=2, padx=self.padx, pady=self.pady)
        ok_button = tkinter.Button(pop_window, text="确定",
                                   command=lambda: self.create_inspection_code_block__click_button_add_code_list_ok(treeview_code_content,
                                                                                                                    text_code_content,
                                                                                                                    pop_window))
        ok_button.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        cancel_button = tkinter.Button(pop_window, text="取消",
                                       command=lambda: self.create_inspection_code_block__click_button_add_code_list_cancel(
                                           pop_window))
        cancel_button.grid(row=2, column=1, padx=self.padx, pady=self.pady)

    def create_inspection_code_block__click_button_add_code_list_cancel(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def create_inspection_code_block__click_button_add_code_list_ok(self, treeview_code_content, text_code_content, pop_window):
        code_content_str = text_code_content.get("1.0", tkinter.END).strip()
        code_index = 0
        for code_line_str in code_content_str.split("\n"):
            code_line_str_strip = code_line_str.strip()
            if code_line_str_strip != "":
                one_line_code_obj = OneLineCode(code_index=code_index, code_content=code_line_str_strip)
                self.resource_info_dict["one_line_code_obj_list"].append(one_line_code_obj)
                code_index += 1
        print("CreateResourceInFrame.click_button_add_code_list_ok: 添加代码行数:",
              len(self.resource_info_dict["one_line_code_obj_list"]))
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点
        # 刷新一次treeview
        treeview_code_content.delete(*treeview_code_content.get_children())
        index = 0
        need_interactive_value = ["No", "Yes"]
        for code_obj in self.resource_info_dict["one_line_code_obj_list"]:
            treeview_code_content.insert("", index,
                                         values=(index, code_obj.code_content, need_interactive_value[code_obj.need_interactive]))
            index += 1

    def create_inspection_code_block__edit_treeview_code_content_item(self, _, treeview_code_content):
        item_index = treeview_code_content.focus()
        print("item_index=", item_index)
        if item_index == "":
            return
        one_line_code_index, _, _ = treeview_code_content.item(item_index, "values")
        print("one_line_code_index", one_line_code_index)
        one_line_code_obj = self.resource_info_dict["one_line_code_obj_list"][int(one_line_code_index)]  # 获取选中的命令对象
        pop_window = tkinter.Toplevel(self.global_info.main_window.window_obj)
        pop_window.title("设置巡检代码")
        screen_width = self.global_info.main_window.window_obj.winfo_screenwidth()
        screen_height = self.global_info.main_window.window_obj.winfo_screenheight()
        width = 420
        height = 300
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.global_info.main_window.window_obj.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        pop_window.protocol("WM_DELETE_WINDOW", lambda: self.create_inspection_code_block__edit_or_add_treeview_code_content_on_closing(
            pop_window))
        one_line_code_info_dict = {}
        # OneLineCode-code_index
        label_code_index = tkinter.Label(pop_window, text="巡检代码index")
        label_code_index.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        entry_code_index = tkinter.Entry(pop_window)
        entry_code_index.insert(0, str(one_line_code_obj.code_index))  # 显示初始值，index不可编辑★
        entry_code_index.grid(row=0, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-code_content
        label_code_content = tkinter.Label(pop_window, text="巡检代码内容")
        label_code_content.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_code_content"] = tkinter.StringVar()
        entry_code_content = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_code_content"])
        entry_code_content.insert(0, str(one_line_code_obj.code_content))  # 显示初始值，可编辑
        entry_code_content.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-code_post_wait_time
        label_code_post_wait_time = tkinter.Label(pop_window, text="代码执行后等待时间")
        label_code_post_wait_time.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_code_post_wait_time"] = tkinter.StringVar()
        entry_code_post_wait_time = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_code_post_wait_time"])
        entry_code_post_wait_time.insert(0, str(one_line_code_obj.code_post_wait_time))  # 显示初始值，可编辑
        entry_code_post_wait_time.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-need_interactive
        label_need_interactive = tkinter.Label(pop_window, text="是否需要交互")
        label_need_interactive.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        need_interactive_name_list = ["No", "Yes"]
        one_line_code_info_dict["combobox_need_interactive"] = ttk.Combobox(pop_window,
                                                                            values=need_interactive_name_list,
                                                                            state="readonly")
        one_line_code_info_dict["combobox_need_interactive"].current(one_line_code_obj.need_interactive)
        one_line_code_info_dict["combobox_need_interactive"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_question_keyword
        label_interactive_question_keyword = tkinter.Label(pop_window, text="交互问题关键词")
        label_interactive_question_keyword.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_interactive_question_keyword"] = tkinter.StringVar()
        entry_interactive_question_keyword = tkinter.Entry(pop_window,
                                                           textvariable=one_line_code_info_dict["sv_interactive_question_keyword"])
        entry_interactive_question_keyword.insert(0, str(one_line_code_obj.interactive_question_keyword))  # 显示初始值，可编辑
        entry_interactive_question_keyword.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_answer
        label_interactive_answer = tkinter.Label(pop_window, text="交互问题回答")
        label_interactive_answer.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_interactive_answer"] = tkinter.StringVar()
        entry_interactive_answer = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_interactive_answer"])
        entry_interactive_answer.insert(0, str(one_line_code_obj.interactive_answer))  # 显示初始值，可编辑
        entry_interactive_answer.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_process_method
        label_interactive_process_method = tkinter.Label(pop_window, text="交互回答次数")
        label_interactive_process_method.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        interactive_process_method_name_list = ["ONETIME", "TWICE", "LOOP"]
        one_line_code_info_dict["combobox_interactive_process_method"] = ttk.Combobox(pop_window,
                                                                                      values=interactive_process_method_name_list,
                                                                                      state="readonly")
        one_line_code_info_dict["combobox_interactive_process_method"].current(one_line_code_obj.interactive_process_method)
        one_line_code_info_dict["combobox_interactive_process_method"].grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-description
        label_description = tkinter.Label(pop_window, text="描述")
        label_description.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_description"] = tkinter.StringVar()
        entry_description = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_description"])
        entry_description.insert(0, str(one_line_code_obj.description))  # 显示初始值，可编辑
        entry_description.grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # 添加按钮
        ok_button = tkinter.Button(pop_window, text="确定",
                                   command=lambda: self.create_inspection_code_block__edit_treeview_code_content_item_save(
                                       one_line_code_info_dict, one_line_code_obj, pop_window, treeview_code_content))
        ok_button.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        cancel_button = tkinter.Button(pop_window, text="取消",
                                       command=lambda: self.create_inspection_code_block__edit_treeview_code_content_item_cancel(
                                           pop_window))
        cancel_button.grid(row=8, column=1, padx=self.padx, pady=self.pady)

    def create_inspection_code_block__edit_treeview_code_content_item_cancel(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def create_inspection_code_block__edit_treeview_code_content_item_save(self, one_line_code_info_dict, one_line_code_obj, pop_window,
                                                                           treeview_code_content):
        one_line_code_obj.code_content = one_line_code_info_dict["sv_code_content"].get()
        one_line_code_obj.code_post_wait_time = float(one_line_code_info_dict["sv_code_post_wait_time"].get())
        if one_line_code_info_dict["combobox_need_interactive"].current() == -1:
            one_line_code_obj.need_interactive = 0
        else:
            one_line_code_obj.need_interactive = one_line_code_info_dict["combobox_need_interactive"].current()
        one_line_code_obj.interactive_question_keyword = one_line_code_info_dict["sv_interactive_question_keyword"].get()
        one_line_code_obj.interactive_answer = one_line_code_info_dict["sv_interactive_answer"].get()
        if one_line_code_info_dict["combobox_interactive_process_method"].current() == -1:
            one_line_code_obj.interactive_process_method = 0
        else:
            one_line_code_obj.interactive_process_method = one_line_code_info_dict["combobox_interactive_process_method"].current()
        one_line_code_obj.description = one_line_code_info_dict["sv_description"].get()
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点
        # ★刷新一次treeview
        item_id_list = treeview_code_content.get_children()
        index = 0
        need_interactive_value = ["No", "Yes"]
        for code_obj in self.resource_info_dict["one_line_code_obj_list"]:
            treeview_code_content.set(item_id_list[index], 1, code_obj.code_content)
            treeview_code_content.set(item_id_list[index], 2, need_interactive_value[code_obj.need_interactive])
            index += 1

    def create_inspection_code_block__edit_or_add_treeview_code_content_on_closing(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def create_inspection_template(self):
        # ★创建-inspection_template
        label_create_inspection_template = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 创建巡检模板 ★★")
        label_create_inspection_template.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_create_inspection_template.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_template-名称
        label_inspection_template_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检模板名称")
        label_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_template_name = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                       textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-描述
        label_inspection_template_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_template_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                              textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-所属项目
        label_inspection_template_project = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_inspection_template_project.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_method
        label_inspection_template_execution_method = tkinter.Label(self.top_frame_widget_dict["frame"], text="execution_method")
        label_inspection_template_execution_method.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_execution_method.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        execution_method_name_list = ["无", "定时执行", "周期执行", "After"]
        self.resource_info_dict["combobox_execution_method"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                            values=execution_method_name_list,
                                                                            state="readonly")
        self.resource_info_dict["combobox_execution_method"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_at_time 这里应该使用日历框及时间设置框，先简化为直接输入 "2024-03-14 09:51:26" 这类字符串
        label_inspection_template_execution_at_time = tkinter.Label(self.top_frame_widget_dict["frame"], text="execution_at_time")
        label_inspection_template_execution_at_time.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_execution_at_time.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_execution_at_time"] = tkinter.StringVar()
        entry_inspection_template_execution_at_time = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                                    textvariable=self.resource_info_dict["sv_execution_at_time"])
        entry_inspection_template_execution_at_time.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_execution_at_time.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-update_code_on_launch
        label_inspection_template_update_code_on_launch = tkinter.Label(self.top_frame_widget_dict["frame"], text="运行前更新code")
        label_inspection_template_update_code_on_launch.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_update_code_on_launch.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        update_code_on_launch_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_update_code_on_launch"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                                 values=update_code_on_launch_name_list,
                                                                                 state="readonly")
        self.resource_info_dict["combobox_update_code_on_launch"].grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-forks
        label_inspection_template_forks = tkinter.Label(self.top_frame_widget_dict["frame"], text="运行线程数")
        label_inspection_template_forks.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_forks.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_forks"] = tkinter.StringVar()
        spinbox_inspection_template_forks = tkinter.Spinbox(self.top_frame_widget_dict["frame"], from_=1, to=256, increment=1,
                                                            textvariable=self.resource_info_dict["sv_forks"])
        spinbox_inspection_template_forks.grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-save_output_to_file
        label_inspection_template_save_output_to_file = tkinter.Label(self.top_frame_widget_dict["frame"], text="自动保存巡检日志到文件")
        label_inspection_template_save_output_to_file.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_save_output_to_file.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        save_output_to_file_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_save_output_to_file"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                               values=save_output_to_file_name_list,
                                                                               state="readonly")
        self.resource_info_dict["combobox_save_output_to_file"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-output_file_name_style
        label_inspection_template_output_file_name_style = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检日志文件名称")
        label_inspection_template_output_file_name_style.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_output_file_name_style.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        output_file_name_style_name_list = ["HOSTNAME", "HOSTNAME-DATE", "HOSTNAME-DATE-TIME", "DATE_DIR/HOSTNAME",
                                            "DATE_DIR/HOSTNAME-DATE",
                                            "DATE_DIR/HOSTNAME-DATE-TIME"]
        self.resource_info_dict["combobox_output_file_name_style"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                                  values=output_file_name_style_name_list,
                                                                                  state="readonly", width=32)
        self.resource_info_dict["combobox_output_file_name_style"].grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★添加host_group列表
        label_host_group_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机组列表")
        label_host_group_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_list.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        frame.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★添加host列表
        label_host_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机列表")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_list.grid(row=11, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        frame.grid(row=11, column=1, padx=self.padx, pady=self.pady)
        # ★添加-巡检代码块列表
        label_inspection_code_block_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检代码块列表")
        label_inspection_code_block_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_list.grid(row=12, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        frame.grid(row=12, column=1, padx=self.padx, pady=self.pady)

    def create_custom_tag_config_scheme(self):
        self.resource_info_dict["pop_window"] = self.top_frame_widget_dict["pop_window"]
        # ★创建-custom_scheme
        label_create_custom_scheme = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 创建巡检模板 ★★")
        label_create_custom_scheme.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_create_custom_scheme.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★custom_scheme-名称
        label_custom_scheme_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检模板名称")
        label_custom_scheme_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_custom_scheme_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_custom_scheme_name = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                 textvariable=self.resource_info_dict["sv_name"])
        entry_custom_scheme_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_custom_scheme_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★custom_scheme-描述
        label_custom_scheme_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_custom_scheme_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_custom_scheme_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_custom_scheme_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                        textvariable=self.resource_info_dict["sv_description"])
        entry_custom_scheme_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_custom_scheme_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★custom_scheme-所属项目
        label_custom_scheme_project = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_custom_scheme_project.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_custom_scheme_project.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★添加匹配对象 CustomMatchObject
        self.resource_info_dict["custome_match_obj_list"] = []
        custome_match_obj_frame_width = self.global_info.main_window.nav_frame_r_width - 25
        custome_match_obj_frame_height = self.global_info.main_window.height - 220
        custome_match_obj_frame = tkinter.Frame(self.top_frame_widget_dict["frame"], width=custome_match_obj_frame_width,
                                                height=custome_match_obj_frame_height, bg="pink")
        # 在custome_match_obj_frame中添加canvas-frame滚动框
        self.resource_info_dict["custome_match_obj_frame_scrollbar"] = tkinter.Scrollbar(custome_match_obj_frame)
        self.resource_info_dict["custome_match_obj_frame_scrollbar"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.resource_info_dict["custome_match_obj_frame_canvas"] = tkinter.Canvas(custome_match_obj_frame, bg="black",
                                                                                   width=custome_match_obj_frame_width - 25,
                                                                                   height=custome_match_obj_frame_height,
                                                                                   yscrollcommand=self.resource_info_dict[
                                                                                       "custome_match_obj_frame_scrollbar"].set)
        self.resource_info_dict["custome_match_obj_frame_canvas"].pack()
        self.resource_info_dict["custome_match_obj_frame_scrollbar"].config(
            command=self.resource_info_dict["custome_match_obj_frame_canvas"].yview)
        self.resource_info_dict["custome_match_obj_frame_frame"] = tkinter.Frame(self.resource_info_dict["custome_match_obj_frame_canvas"],
                                                                                 bg="black")
        self.resource_info_dict["custome_match_obj_frame_frame"].pack()
        self.resource_info_dict["custome_match_obj_frame_canvas"].create_window((0, 0), window=self.resource_info_dict[
            "custome_match_obj_frame_frame"], anchor='nw')
        add_custome_match_obj_button = tkinter.Button(self.top_frame_widget_dict["frame"], text="添加匹配对象",
                                                      command=lambda: self.create_custom_tag_config_scheme__add_custome_match_object())
        add_custome_match_obj_button.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        custome_match_obj_frame.grid(row=5, column=0, columnspan=2, padx=self.padx, pady=self.pady)

    def create_custom_tag_config_scheme__add_custome_match_object(self):
        add_match_obj_pop_window = tkinter.Toplevel(self.resource_info_dict["pop_window"])
        add_match_obj_pop_window.title("配色方案设置")
        screen_width = add_match_obj_pop_window.winfo_screenwidth()
        screen_height = add_match_obj_pop_window.winfo_screenheight()
        width = self.global_info.main_window.nav_frame_r_width - 50
        height = self.global_info.main_window.height - 50
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        add_match_obj_pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.resource_info_dict["pop_window"].attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        add_match_obj_pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        add_match_obj_pop_window.protocol("WM_DELETE_WINDOW",
                                          lambda: self.create_custom_tag_config_scheme__on_closing_add_match_obj_pop_window(
                                              add_match_obj_pop_window))
        # 添加用于设置CustomMatchObject属性的控件
        match_obj_info_dict = {}
        label_match_pattern_lines = tkinter.Label(add_match_obj_pop_window, text="添加需要匹配的字符串或正则表达式，一行一个")
        label_match_pattern_lines.grid(row=0, column=0, columnspan=4, padx=self.padx, pady=self.pady, sticky="w")
        match_obj_info_dict["text_match_pattern_lines"] = tkinter.Text(add_match_obj_pop_window, height=9)
        match_obj_info_dict["text_match_pattern_lines"].grid(row=1, column=0, columnspan=4, padx=self.padx, pady=self.pady)
        # -- 匹配字符-前景色
        label_foreground = tkinter.Label(add_match_obj_pop_window, text="匹配字符-前景色")
        label_foreground.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        match_obj_info_dict["sv_foreground"] = tkinter.StringVar()
        entry_foreground = tkinter.Entry(add_match_obj_pop_window, textvariable=match_obj_info_dict["sv_foreground"])
        entry_foreground.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        color_button_foreground = tkinter.Button(add_match_obj_pop_window, text="选择颜色",
                                                 command=lambda: self.create_custom_tag_config_scheme__choose_color_of_custome_match_object(
                                                     entry_foreground, add_match_obj_pop_window))
        color_button_foreground.grid(row=2, column=2, padx=self.padx, pady=self.pady)
        # -- 匹配字符-背景色
        label_backgroun = tkinter.Label(add_match_obj_pop_window, text="匹配字符-背景色")
        label_backgroun.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        match_obj_info_dict["sv_backgroun"] = tkinter.StringVar()
        entry_backgroun = tkinter.Entry(add_match_obj_pop_window, textvariable=match_obj_info_dict["sv_backgroun"])
        entry_backgroun.grid(row=3, column=1, padx=self.padx, pady=self.pady)
        color_button_backgroun = tkinter.Button(add_match_obj_pop_window, text="选择颜色",
                                                command=lambda: self.create_custom_tag_config_scheme__choose_color_of_custome_match_object(
                                                    entry_backgroun, add_match_obj_pop_window))
        color_button_backgroun.grid(row=3, column=2, padx=self.padx, pady=self.pady)
        # -- 匹配字符-下划线
        match_obj_info_dict["var_ck_underline"] = tkinter.BooleanVar()
        ck_underline = tkinter.Checkbutton(add_match_obj_pop_window, text="添加下划线", variable=match_obj_info_dict["var_ck_underline"])
        ck_underline.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        # -- 匹配字符-下划线颜色
        label_underlinefg = tkinter.Label(add_match_obj_pop_window, text="下划线颜色")
        label_underlinefg.grid(row=4, column=1, padx=self.padx, pady=self.pady, sticky="e")
        match_obj_info_dict["sv_underlinefg"] = tkinter.StringVar()
        entry_underlinefg = tkinter.Entry(add_match_obj_pop_window, textvariable=match_obj_info_dict["sv_underlinefg"])
        entry_underlinefg.grid(row=4, column=2, padx=self.padx, pady=self.pady)
        color_button_underlinefg = tkinter.Button(add_match_obj_pop_window, text="选择颜色",
                                                  command=lambda: self.create_custom_tag_config_scheme__choose_color_of_custome_match_object(
                                                      entry_underlinefg, add_match_obj_pop_window))
        color_button_underlinefg.grid(row=4, column=3, padx=self.padx, pady=self.pady)
        # -- 匹配字符-删除线
        match_obj_info_dict["var_ck_overstrike"] = tkinter.BooleanVar()
        ck_overstrike = tkinter.Checkbutton(add_match_obj_pop_window, text="添加删除线", variable=match_obj_info_dict["var_ck_overstrike"])
        ck_overstrike.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        # -- 匹配字符-删除线颜色
        label_overstrikefg = tkinter.Label(add_match_obj_pop_window, text="删除线颜色")
        label_overstrikefg.grid(row=5, column=1, padx=self.padx, pady=self.pady, sticky="e")
        match_obj_info_dict["sv_overstrikefg"] = tkinter.StringVar()
        entry_overstrikefg = tkinter.Entry(add_match_obj_pop_window, textvariable=match_obj_info_dict["sv_overstrikefg"])
        entry_overstrikefg.configure()
        entry_overstrikefg.grid(row=5, column=2, padx=self.padx, pady=self.pady)
        color_button_overstrikefg = tkinter.Button(add_match_obj_pop_window, text="选择颜色",
                                                   command=lambda: self.create_custom_tag_config_scheme__choose_color_of_custome_match_object(
                                                       entry_overstrikefg, add_match_obj_pop_window))
        color_button_overstrikefg.grid(row=5, column=3, padx=self.padx, pady=self.pady)
        # -- 匹配字符-粗体
        match_obj_info_dict["var_ck_bold"] = tkinter.BooleanVar()
        ck_bold = tkinter.Checkbutton(add_match_obj_pop_window, text="粗体", variable=match_obj_info_dict["var_ck_bold"])
        ck_bold.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        # -- 匹配字符-斜体
        match_obj_info_dict["var_ck_italic"] = tkinter.BooleanVar()
        ck_italic = tkinter.Checkbutton(add_match_obj_pop_window, text="斜体", variable=match_obj_info_dict["var_ck_italic"])
        ck_italic.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # 添加确定按钮
        button_ok = tkinter.Button(add_match_obj_pop_window, text="确定",
                                   command=lambda: self.create_custom_tag_config_scheme__add_custome_match_object__ok(match_obj_info_dict,
                                                                                                                      add_match_obj_pop_window))
        button_ok.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        # 添加取消按钮
        button_cancel = tkinter.Button(add_match_obj_pop_window, text="取消",
                                       command=lambda: self.create_custom_tag_config_scheme__add_custome_match_object__cancel(
                                           add_match_obj_pop_window))
        button_cancel.grid(row=7, column=1, padx=self.padx, pady=self.pady)

    def create_custom_tag_config_scheme__add_custome_match_object__ok(self, match_obj_info_dict,
                                                                      add_match_obj_pop_window):
        # 先在 custome_match_obj_frame_frame 列出刚刚添加的match_obj
        match_obj = CustomMatchObject(match_pattern_lines=match_obj_info_dict["text_match_pattern_lines"].get("1.0", tkinter.END + "-1c"),
                                      foreground=match_obj_info_dict["sv_foreground"].get(),
                                      backgroun=match_obj_info_dict["sv_backgroun"].get(),
                                      underline=match_obj_info_dict["var_ck_underline"].get(),
                                      underlinefg=match_obj_info_dict["sv_underlinefg"].get(),
                                      overstrike=match_obj_info_dict["var_ck_overstrike"].get(),
                                      overstrikefg=match_obj_info_dict["sv_overstrikefg"].get(),
                                      bold=match_obj_info_dict["var_ck_bold"].get(),
                                      italic=match_obj_info_dict["var_ck_italic"].get()
                                      )
        self.resource_info_dict["custome_match_obj_list"].append(match_obj)
        self.create_custom_tag_config_scheme__list_custome_match_obj_in_frame_frame()
        # 再返回到 创建配色方案 界面
        add_match_obj_pop_window.destroy()  # 关闭子窗口
        self.resource_info_dict["pop_window"].attributes("-disabled", 0)  # 使主窗口响应
        self.resource_info_dict["pop_window"].focus_force()  # 使主窗口获得焦点

    def create_custom_tag_config_scheme__add_custome_match_object__cancel(self, add_match_obj_pop_window):
        # 返回到 创建配色方案 界面
        add_match_obj_pop_window.destroy()  # 关闭子窗口
        self.resource_info_dict["pop_window"].attributes("-disabled", 0)  # 使主窗口响应
        self.resource_info_dict["pop_window"].focus_force()  # 使主窗口获得焦点

    def create_custom_tag_config_scheme__list_custome_match_obj_in_frame_frame(self):
        for widget in self.resource_info_dict["custome_match_obj_frame_frame"].winfo_children():
            widget.destroy()
        row = 0
        for match_obj in self.resource_info_dict["custome_match_obj_list"]:
            label_index = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"], text=str(row))
            text_demo = tkinter.Text(self.resource_info_dict["custome_match_obj_frame_frame"], fg="white",
                                     bg="black", width=18, height=3,
                                     font=("", 12),
                                     wrap=tkinter.NONE, spacing1=0, spacing2=0, spacing3=0)
            text_demo.insert(tkinter.END, match_obj.match_pattern_lines)
            label_foreground = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                             text="前景色: \n" + match_obj.foreground)
            label_backgroun = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                            text="背景色: \n" + match_obj.backgroun)
            if match_obj.underline:
                is_underline = "Yes"
            else:
                is_underline = "No"
            label_underline = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                            text="下划线: " + is_underline + "\n" + match_obj.underlinefg)
            if match_obj.overstrike:
                is_overstrike = "Yes"
            else:
                is_overstrike = "No"
            label_overstrike = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                             text="删除线: " + is_overstrike + "\n" + match_obj.overstrikefg)
            custom_match_font = font.Font(size=12, name="")
            if match_obj.bold:
                is_bold = "Yes"
                custom_match_font.configure(weight="bold")
            else:
                is_bold = "No"
            label_bold = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                       text="粗体: " + "\n" + is_bold)
            if match_obj.italic:
                is_italic = "Yes"
                custom_match_font.configure(slant="italic")
            else:
                is_italic = "No"
            label_italic = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                         text="斜体: " + "\n" + is_italic)
            tag_config_name = uuid.uuid4().__str__()  # <str>
            text_demo.tag_add(f"{tag_config_name}", "1.0", tkinter.END)
            text_demo.tag_config(f"{tag_config_name}",
                                 foreground=match_obj.foreground,
                                 backgroun=match_obj.backgroun,
                                 underline=match_obj.underline,
                                 underlinefg=match_obj.underlinefg,
                                 overstrike=match_obj.overstrike,
                                 overstrikefg=match_obj.overstrikefg,
                                 font=custom_match_font)
            edit_match_obj_obj = EditCustomMatchObject(top_window=self.resource_info_dict["pop_window"],
                                                       call_back_class_obj=self,
                                                       match_obj=match_obj, global_info=self.global_info,
                                                       call_back_class=CALL_BACK_CLASS_CREATE_RESOURCE)
            button_edit = tkinter.Button(self.resource_info_dict["custome_match_obj_frame_frame"], text="编辑",
                                         command=edit_match_obj_obj.edit_custome_match_object)
            delete_match_obj_obj = DeleteCustomMatchObject(call_back_class_obj=self,
                                                           match_obj=match_obj,
                                                           call_back_class=CALL_BACK_CLASS_CREATE_RESOURCE)
            button_delete = tkinter.Button(self.resource_info_dict["custome_match_obj_frame_frame"], text="删除",
                                           command=delete_match_obj_obj.delete_custome_match_object)
            label_index.grid(row=row, column=0, padx=self.padx, pady=self.pady, sticky="nswe")
            label_index.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            text_demo.grid(row=row, column=1, padx=self.padx, pady=self.pady, sticky="nswe")
            label_foreground.grid(row=row, column=2, padx=self.padx, pady=self.pady, sticky="nswe")
            label_foreground.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            label_backgroun.grid(row=row, column=3, padx=self.padx, pady=self.pady, sticky="nswe")
            label_backgroun.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            label_underline.grid(row=row, column=4, padx=self.padx, pady=self.pady, sticky="nswe")
            label_underline.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            label_overstrike.grid(row=row, column=5, padx=self.padx, pady=self.pady, sticky="nswe")
            label_overstrike.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            label_bold.grid(row=row, column=6, padx=self.padx, pady=self.pady, sticky="nswe")
            label_bold.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            label_italic.grid(row=row, column=7, padx=self.padx, pady=self.pady, sticky="nswe")
            label_italic.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            button_edit.grid(row=row, column=8, padx=self.padx, pady=self.pady, sticky="nswe")
            button_edit.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            button_delete.grid(row=row, column=9, padx=self.padx, pady=self.pady, sticky="nswe")
            button_delete.bind("<MouseWheel>", self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
            row += 1
        # 还要更新frame和canvas才可滚动
        self.resource_info_dict["custome_match_obj_frame_frame"].update_idletasks()
        self.resource_info_dict["custome_match_obj_frame_canvas"].configure(
            scrollregion=(0, 0, self.resource_info_dict["custome_match_obj_frame_frame"].winfo_width(),
                          self.resource_info_dict["custome_match_obj_frame_frame"].winfo_height()))
        self.resource_info_dict["custome_match_obj_frame_canvas"].bind("<MouseWheel>",
                                                                       self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
        self.resource_info_dict["custome_match_obj_frame_frame"].bind("<MouseWheel>",
                                                                      self.create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame)
        # 滚动条移到最开头
        self.resource_info_dict["custome_match_obj_frame_canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def create_custom_tag_config_scheme__proces_mouse_scroll__frame_frame(self, event):
        if event.delta > 0:
            self.resource_info_dict["custome_match_obj_frame_canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.resource_info_dict["custome_match_obj_frame_canvas"].yview_scroll(1, 'units')  # 向下移动

    @staticmethod
    def create_custom_tag_config_scheme__choose_color_of_custome_match_object(entry, add_match_obj_pop_window):
        add_match_obj_pop_window.focus_force()
        color = tkinter.colorchooser.askcolor()
        if color[1] is not None:
            entry.delete(0, tkinter.END)
            entry.insert(0, color[1])
            entry.configure(bg=color[1])
        add_match_obj_pop_window.focus_force()

    def create_custom_tag_config_scheme__on_closing_add_match_obj_pop_window(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.resource_info_dict["pop_window"].attributes("-disabled", 0)  # 使主窗口响应
        self.resource_info_dict["pop_window"].focus_force()  # 使主窗口获得焦点


class DeleteCustomMatchObject:
    def __init__(self, call_back_class_obj=None, match_obj=None, call_back_class=CALL_BACK_CLASS_EDIT_RESOURCE):
        self.call_back_class_obj = call_back_class_obj
        self.match_obj = match_obj
        self.call_back_class = call_back_class

    def delete_custome_match_object(self):
        if self.call_back_class == CALL_BACK_CLASS_CREATE_RESOURCE:
            self.call_back_class_obj.resource_info_dict["custome_match_obj_list"].remove(self.match_obj)
            self.call_back_class_obj.create_custom_tag_config_scheme__list_custome_match_obj_in_frame_frame()
        elif self.call_back_class == CALL_BACK_CLASS_EDIT_RESOURCE:
            self.call_back_class_obj.resource_obj.custom_match_object_list.remove(self.match_obj)
            self.call_back_class_obj.edit_custome_tag_config_scheme__list_custome_match_obj_in_frame_frame()


class EditCustomMatchObject:
    def __init__(self, top_window=None, match_obj=None, call_back_class_obj=None,
                 call_back_class=CALL_BACK_CLASS_EDIT_RESOURCE, global_info=None):
        self.top_window = top_window
        self.match_obj = match_obj
        self.call_back_class_obj = call_back_class_obj
        self.call_back_class = call_back_class  # <int>
        self.global_info = global_info
        self.padx = 2
        self.pady = 2
        self.match_obj_info_dict = {}
        self.edit_match_obj_pop_window = None

    def edit_custome_match_object(self):
        self.edit_match_obj_pop_window = tkinter.Toplevel(self.top_window)
        self.edit_match_obj_pop_window.title("编辑匹配对象")
        screen_width = self.edit_match_obj_pop_window.winfo_screenwidth()
        screen_height = self.edit_match_obj_pop_window.winfo_screenheight()
        width = self.global_info.main_window.nav_frame_r_width - 50
        height = self.global_info.main_window.height - 25
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        self.edit_match_obj_pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.top_window.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        self.edit_match_obj_pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        self.edit_match_obj_pop_window.protocol("WM_DELETE_WINDOW", self.edit_custome_match_object__cancel)
        # 添加用于设置CustomMatchObject属性的控件
        label_match_pattern_lines = tkinter.Label(self.edit_match_obj_pop_window, text="添加需要匹配的单词或正则表达式，一行一个")
        label_match_pattern_lines.grid(row=0, column=0, columnspan=4, padx=self.padx, pady=self.pady, sticky="w")
        self.match_obj_info_dict["text_match_pattern_lines"] = tkinter.Text(self.edit_match_obj_pop_window, height=9)
        self.match_obj_info_dict["text_match_pattern_lines"].grid(row=1, column=0, columnspan=4, padx=self.padx, pady=self.pady)
        self.match_obj_info_dict["text_match_pattern_lines"].insert("1.0", self.match_obj.match_pattern_lines)
        # -- 匹配字符-前景色
        label_foreground = tkinter.Label(self.edit_match_obj_pop_window, text="匹配字符-前景色")
        label_foreground.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.match_obj_info_dict["sv_foreground"] = tkinter.StringVar()
        entry_foreground = tkinter.Entry(self.edit_match_obj_pop_window, textvariable=self.match_obj_info_dict["sv_foreground"])
        entry_foreground.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        entry_foreground.insert(0, self.match_obj.foreground)
        entry_foreground.configure(bg=self.match_obj.foreground)
        color_button_foreground = tkinter.Button(self.edit_match_obj_pop_window, text="选择颜色",
                                                 command=lambda: self.choose_color_of_custome_match_object(entry_foreground))
        color_button_foreground.grid(row=2, column=2, padx=self.padx, pady=self.pady)
        # -- 匹配字符-背景色
        label_backgroun = tkinter.Label(self.edit_match_obj_pop_window, text="匹配字符-背景色")
        label_backgroun.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        self.match_obj_info_dict["sv_backgroun"] = tkinter.StringVar()
        entry_backgroun = tkinter.Entry(self.edit_match_obj_pop_window, textvariable=self.match_obj_info_dict["sv_backgroun"])
        entry_backgroun.grid(row=3, column=1, padx=self.padx, pady=self.pady)
        entry_backgroun.insert(0, self.match_obj.backgroun)
        entry_backgroun.configure(bg=self.match_obj.backgroun)
        color_button_backgroun = tkinter.Button(self.edit_match_obj_pop_window, text="选择颜色",
                                                command=lambda: self.choose_color_of_custome_match_object(entry_backgroun))
        color_button_backgroun.grid(row=3, column=2, padx=self.padx, pady=self.pady)
        # -- 匹配字符-下划线
        self.match_obj_info_dict["var_ck_underline"] = tkinter.BooleanVar()
        ck_underline = tkinter.Checkbutton(self.edit_match_obj_pop_window, text="添加下划线",
                                           variable=self.match_obj_info_dict["var_ck_underline"])
        ck_underline.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        self.match_obj_info_dict["var_ck_underline"].set(self.match_obj.underline)
        # -- 匹配字符-下划线颜色
        label_underlinefg = tkinter.Label(self.edit_match_obj_pop_window, text="下划线颜色")
        label_underlinefg.grid(row=4, column=1, padx=self.padx, pady=self.pady, sticky="e")
        self.match_obj_info_dict["sv_underlinefg"] = tkinter.StringVar()
        entry_underlinefg = tkinter.Entry(self.edit_match_obj_pop_window, textvariable=self.match_obj_info_dict["sv_underlinefg"])
        entry_underlinefg.grid(row=4, column=2, padx=self.padx, pady=self.pady)
        entry_underlinefg.insert(0, self.match_obj.underlinefg)
        entry_underlinefg.configure(bg=self.match_obj.underlinefg)
        color_button_underlinefg = tkinter.Button(self.edit_match_obj_pop_window, text="选择颜色",
                                                  command=lambda: self.choose_color_of_custome_match_object(entry_underlinefg))
        color_button_underlinefg.grid(row=4, column=3, padx=self.padx, pady=self.pady)
        # -- 匹配字符-删除线
        self.match_obj_info_dict["var_ck_overstrike"] = tkinter.BooleanVar()
        ck_overstrike = tkinter.Checkbutton(self.edit_match_obj_pop_window, text="添加删除线",
                                            variable=self.match_obj_info_dict["var_ck_overstrike"])
        ck_overstrike.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.match_obj_info_dict["var_ck_overstrike"].set(self.match_obj.overstrike)
        # -- 匹配字符-删除线颜色
        label_overstrikefg = tkinter.Label(self.edit_match_obj_pop_window, text="删除线颜色")
        label_overstrikefg.grid(row=5, column=1, padx=self.padx, pady=self.pady, sticky="e")
        self.match_obj_info_dict["sv_overstrikefg"] = tkinter.StringVar()
        entry_overstrikefg = tkinter.Entry(self.edit_match_obj_pop_window, textvariable=self.match_obj_info_dict["sv_overstrikefg"])
        entry_overstrikefg.grid(row=5, column=2, padx=self.padx, pady=self.pady)
        entry_overstrikefg.insert(0, self.match_obj.overstrikefg)
        entry_overstrikefg.configure(bg=self.match_obj.overstrikefg)
        color_button_overstrikefg = tkinter.Button(self.edit_match_obj_pop_window, text="选择颜色",
                                                   command=lambda: self.choose_color_of_custome_match_object(entry_overstrikefg))
        color_button_overstrikefg.grid(row=5, column=3, padx=self.padx, pady=self.pady)
        # -- 匹配字符-粗体
        self.match_obj_info_dict["var_ck_bold"] = tkinter.BooleanVar()
        ck_bold = tkinter.Checkbutton(self.edit_match_obj_pop_window, text="粗体", variable=self.match_obj_info_dict["var_ck_bold"])
        ck_bold.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.match_obj_info_dict["var_ck_bold"].set(self.match_obj.bold)
        # -- 匹配字符-斜体
        self.match_obj_info_dict["var_ck_italic"] = tkinter.BooleanVar()
        ck_italic = tkinter.Checkbutton(self.edit_match_obj_pop_window, text="斜体", variable=self.match_obj_info_dict["var_ck_italic"])
        ck_italic.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        self.match_obj_info_dict["var_ck_italic"].set(self.match_obj.italic)
        # 添加确定按钮
        button_ok = tkinter.Button(self.edit_match_obj_pop_window, text="确定",
                                   command=self.edit_custome_match_object__ok)
        button_ok.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        # 添加取消按钮
        button_cancel = tkinter.Button(self.edit_match_obj_pop_window, text="取消",
                                       command=self.edit_custome_match_object__cancel)
        button_cancel.grid(row=7, column=1, padx=self.padx, pady=self.pady)

    def edit_custome_match_object__cancel(self):
        # 返回到 创建配色方案 界面
        self.edit_match_obj_pop_window.destroy()  # 关闭子窗口
        self.top_window.attributes("-disabled", 0)  # 使主窗口响应
        self.top_window.focus_force()  # 使主窗口获得焦点

    def edit_custome_match_object__ok(self):
        # 先更新信息
        self.match_obj.update(match_pattern_lines=self.match_obj_info_dict["text_match_pattern_lines"].get("1.0", tkinter.END + "-1c"),
                              foreground=self.match_obj_info_dict["sv_foreground"].get(),
                              backgroun=self.match_obj_info_dict["sv_backgroun"].get(),
                              underline=self.match_obj_info_dict["var_ck_underline"].get(),
                              underlinefg=self.match_obj_info_dict["sv_underlinefg"].get(),
                              overstrike=self.match_obj_info_dict["var_ck_overstrike"].get(),
                              overstrikefg=self.match_obj_info_dict["sv_overstrikefg"].get(),
                              bold=self.match_obj_info_dict["var_ck_bold"].get(),
                              italic=self.match_obj_info_dict["var_ck_italic"].get()
                              )
        if self.call_back_class == CALL_BACK_CLASS_EDIT_RESOURCE:
            self.call_back_class_obj.edit_custome_tag_config_scheme__list_custome_match_obj_in_frame_frame()
        elif self.call_back_class == CALL_BACK_CLASS_CREATE_RESOURCE:
            self.call_back_class_obj.create_custom_tag_config_scheme__list_custome_match_obj_in_frame_frame()
        else:
            pass
        # 返回到 创建配色方案 界面
        self.edit_match_obj_pop_window.destroy()  # 关闭子窗口
        self.top_window.attributes("-disabled", 0)  # 使主窗口响应
        self.top_window.focus_force()  # 使主窗口获得焦点

    def choose_color_of_custome_match_object(self, entry):
        self.edit_match_obj_pop_window.focus_force()
        color = tkinter.colorchooser.askcolor()
        if color[1] is not None:
            entry.delete(0, tkinter.END)
            entry.insert(0, color[1])
            entry.configure(bg=color[1])
        self.edit_match_obj_pop_window.focus_force()


class ListResourceInFrame:
    """
    在主窗口的查看资源界面，添加用于显示资源信息的控件
    """

    def __init__(self, top_frame_widget_dict=None, global_info=None, resource_type=RESOURCE_TYPE_PROJECT):
        self.top_frame_widget_dict = top_frame_widget_dict  # 在 top_frame_widget_dict["frame"]里添加组件，用于列出资源列表
        self.global_info = global_info
        self.resource_type = resource_type
        self.padx = 2
        self.pady = 2

    def proces_mouse_scroll_of_top_frame(self, event):
        if event.delta > 0:
            self.top_frame_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.top_frame_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def show(self):  # 入口函数
        for widget in self.top_frame_widget_dict["frame"].winfo_children():
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
        elif self.resource_type == RESOURCE_TYPE_CUSTOM_SCHEME:
            resource_display_frame_title = "★★ 配色方案列表 ★★"
            resource_obj_list = self.global_info.custome_tag_config_scheme_obj_list
        else:
            print("unknown resource type")
            resource_display_frame_title = "★★ 项目列表 ★★"
            resource_obj_list = self.global_info.project_obj_list
        # 列出资源
        label_display_resource = tkinter.Label(self.top_frame_widget_dict["frame"],
                                               text=resource_display_frame_title + "    数量: " + str(len(resource_obj_list)))
        label_display_resource.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        label_display_resource.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        index = 0
        for obj in resource_obj_list:
            print(obj.name)
            label_index = tkinter.Label(self.top_frame_widget_dict["frame"], text=str(index + 1) + " : ")
            label_index.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
            label_index.grid(row=index + 1, column=0, padx=self.padx, pady=self.pady)
            label_name = tkinter.Label(self.top_frame_widget_dict["frame"], text=obj.name)
            label_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
            label_name.grid(row=index + 1, column=1, padx=self.padx, pady=self.pady)
            # 查看对象信息
            view_obj = ViewResourceInFrame(self.top_frame_widget_dict, self.global_info, obj,
                                           self.resource_type)
            button_view = tkinter.Button(self.top_frame_widget_dict["frame"], text="查看", command=view_obj.show)
            button_view.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
            button_view.grid(row=index + 1, column=2, padx=self.padx, pady=self.pady)
            # 编辑对象信息
            edit_obj = EditResourceInFrame(self.top_frame_widget_dict, self.global_info, obj,
                                           self.resource_type)
            button_edit = tkinter.Button(self.top_frame_widget_dict["frame"], text="编辑", command=edit_obj.show)
            button_edit.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
            button_edit.grid(row=index + 1, column=3, padx=self.padx, pady=self.pady)
            # 删除对象
            delete_obj = DeleteResourceInFrame(self.top_frame_widget_dict, self.global_info, obj,
                                               self.resource_type, call_back_class_obj=self,
                                               call_back_class=CALL_BACK_CLASS_LIST_RESOURCE)
            button_delete = tkinter.Button(self.top_frame_widget_dict["frame"], text="删除", command=delete_obj.show)
            button_delete.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
            button_delete.grid(row=index + 1, column=4, padx=self.padx, pady=self.pady)
            # ★巡检模板-start
            if self.resource_type == RESOURCE_TYPE_INSPECTION_TEMPLATE:
                start_obj = StartInspectionTemplateInFrame(self.global_info, obj)
                button_start = tkinter.Button(self.top_frame_widget_dict["frame"], text="Start", command=start_obj.start)
                button_start.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
                button_start.grid(row=index + 1, column=5, padx=self.padx, pady=self.pady)
            # ★Host-open_terminal
            if self.resource_type == RESOURCE_TYPE_HOST:
                # 打开单独式终端
                open_division_terminal_obj = OpenDivisionTerminalVt100(global_info=self.global_info, host_oid=obj.oid)
                button_open_terminal2 = tkinter.Button(self.top_frame_widget_dict["frame"], text="打开终端2",
                                                       command=open_division_terminal_obj.open_session)
                button_open_terminal2.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
                button_open_terminal2.grid(row=index + 1, column=5, padx=self.padx, pady=self.pady)
            index += 1
        # 信息控件添加完毕
        self.top_frame_widget_dict["frame"].update_idletasks()  # 更新Frame的尺寸
        self.top_frame_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.top_frame_widget_dict["frame"].winfo_width(), self.top_frame_widget_dict["frame"].winfo_height()))
        self.top_frame_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        self.top_frame_widget_dict["frame"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)


class ViewResourceInFrame:
    """
    在主窗口的查看资源界面，添加用于显示资源信息的控件
    """

    def __init__(self, top_frame_widget_dict=None, global_info=None, resource_obj=None,
                 resource_type=RESOURCE_TYPE_PROJECT):
        self.top_frame_widget_dict = top_frame_widget_dict
        self.global_info = global_info
        self.resource_obj = resource_obj
        self.resource_type = resource_type
        self.view_width = 20
        self.padx = 2
        self.pady = 2
        self.resource_info_dict = {}

    def show(self):  # 入口函数
        for widget in self.top_frame_widget_dict["frame"].winfo_children():
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
        elif self.resource_type == RESOURCE_TYPE_CUSTOM_SCHEME:
            self.view_custome_tag_config_scheme()
        else:
            print("<class ViewResourceInFrame> resource_type is Unknown")
        self.update_top_frame()  # 更新Frame的尺寸，并将滚动条移到最开头

    def proces_mouse_scroll_of_top_frame(self, event):
        if event.delta > 0:
            self.top_frame_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.top_frame_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def update_top_frame(self):
        # 更新Frame的尺寸
        self.top_frame_widget_dict["frame"].update_idletasks()
        self.top_frame_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.top_frame_widget_dict["frame"].winfo_width(),
                          self.top_frame_widget_dict["frame"].winfo_height()))
        self.top_frame_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        self.top_frame_widget_dict["frame"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        # 滚动条移到最开头
        self.top_frame_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def view_project(self):
        # ★查看-project
        print("查看项目")
        print(self.resource_obj)
        obj_info_text = tkinter.Text(master=self.top_frame_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息，需要绑定滚动条
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
        button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="返回项目列表",
                                       command=lambda: self.global_info.main_window.nav_frame_r_resource_top_page_display(
                                           RESOURCE_TYPE_PROJECT))  # 返回“项目列表”
        button_return.pack()

    def view_credential(self):
        # 查看-credential
        obj_info_text = tkinter.Text(master=self.top_frame_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息
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
        button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="返回项目列表",
                                       command=lambda: self.global_info.main_window.nav_frame_r_resource_top_page_display(
                                           RESOURCE_TYPE_CREDENTIAL))  # 返回凭据列表
        button_return.pack()

    def view_host(self):
        # 查看-host
        obj_info_text = tkinter.Text(master=self.top_frame_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息
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
        # ★host-custom_scheme 终端配色方案
        custom_scheme = self.global_info.get_custome_tag_config_scheme_by_oid(self.resource_obj.custome_tag_config_scheme_oid)
        if custom_scheme is None:
            custom_scheme_name = "无"
        else:
            custom_scheme_name = custom_scheme.name
        host_custom_scheme = "终端配色方案".ljust(self.view_width - 6, " ") + ": " + custom_scheme_name + "\n"
        obj_info_text.insert(tkinter.END, host_custom_scheme)
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
        button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="返回主机列表",
                                       command=lambda: self.global_info.main_window.nav_frame_r_resource_top_page_display(
                                           RESOURCE_TYPE_HOST))  # 返回主机列表
        button_return.pack()

    def view_host_group(self):
        # 查看-host_group
        obj_info_text = tkinter.Text(master=self.top_frame_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息
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
        button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="返回主机组列表",
                                       command=lambda: self.global_info.main_window.nav_frame_r_resource_top_page_display(
                                           RESOURCE_TYPE_HOST_GROUP))  # 返回主机组列表
        button_return.pack()

    def view_inspection_code_block(self):
        # 查看-inspection_code_block
        obj_info_text = tkinter.Text(master=self.top_frame_widget_dict["frame"], height=9)  # 创建多行文本框，用于显示资源信息
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
        label_code_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检命令内容")
        label_code_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_code_list.pack()
        treeview_code_content = ttk.Treeview(self.top_frame_widget_dict["frame"], cursor="arrow", height=7,
                                             columns=("index", "code_content", "need_interactive"), show="headings")
        # 设置每一个列的宽度和对齐的方式
        treeview_code_content.column("index", width=50, anchor="w")
        treeview_code_content.column("code_content", width=300, anchor="w")
        treeview_code_content.column("need_interactive", width=80, anchor="w")
        # 设置每个列的标题
        treeview_code_content.heading("index", text="index", anchor="w")
        treeview_code_content.heading("code_content", text="code_content", anchor="w")
        treeview_code_content.heading("need_interactive", text="需要交互", anchor="w")
        # 插入数据
        index = 0
        need_interactive_value = ["No", "Yes"]
        for code_obj in self.resource_obj.code_list:
            treeview_code_content.insert("", index,
                                         values=(index, code_obj.code_content, need_interactive_value[code_obj.need_interactive]))
            index += 1
        treeview_code_content.pack()
        # 单击指定的命令行，显示其高级属性
        treeview_code_content.bind("<<TreeviewSelect>>", lambda event: self.view_treeview_code_content_item(event, treeview_code_content))
        # ★★添加“返回主机组列表”按钮★★
        button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="返回巡检代码块列表",
                                       command=lambda: self.global_info.main_window.nav_frame_r_resource_top_page_display(
                                           RESOURCE_TYPE_INSPECTION_CODE_BLOCK))  # 返回巡检代码块列表
        button_return.pack()

    def view_treeview_code_content_item(self, _, treeview_code_content):
        item_index = treeview_code_content.focus()
        one_line_code_index = treeview_code_content.item(item_index, "values")[0]
        print("one_line_code_index", one_line_code_index)
        one_line_code_obj = self.resource_obj.code_list[int(one_line_code_index)]  # 获取选中的命令对象
        pop_window = tkinter.Toplevel(self.global_info.main_window.window_obj)
        pop_window.title("设置巡检代码")
        screen_width = self.global_info.main_window.window_obj.winfo_screenwidth()
        screen_height = self.global_info.main_window.window_obj.winfo_screenheight()
        width = 420
        height = 300
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        one_line_code_info_dict = {}
        # OneLineCode-code_index
        label_code_index = tkinter.Label(pop_window, text="巡检代码index")
        label_code_index.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        entry_code_index = tkinter.Entry(pop_window)
        entry_code_index.insert(0, str(one_line_code_obj.code_index))  # 显示初始值，index不可编辑★
        entry_code_index.grid(row=0, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-code_content
        label_code_content = tkinter.Label(pop_window, text="巡检代码内容")
        label_code_content.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_code_content"] = tkinter.StringVar()
        entry_code_content = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_code_content"])
        entry_code_content.insert(0, str(one_line_code_obj.code_content))  # 显示初始值，可编辑
        entry_code_content.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-code_post_wait_time
        label_code_post_wait_time = tkinter.Label(pop_window, text="代码执行后等待时间")
        label_code_post_wait_time.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_code_post_wait_time"] = tkinter.StringVar()
        entry_code_post_wait_time = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_code_post_wait_time"])
        entry_code_post_wait_time.insert(0, str(one_line_code_obj.code_post_wait_time))  # 显示初始值，可编辑
        entry_code_post_wait_time.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-need_interactive
        label_need_interactive = tkinter.Label(pop_window, text="是否需要交互")
        label_need_interactive.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        need_interactive_name_list = ["No", "Yes"]
        one_line_code_info_dict["combobox_need_interactive"] = ttk.Combobox(pop_window,
                                                                            values=need_interactive_name_list,
                                                                            state="readonly")
        one_line_code_info_dict["combobox_need_interactive"].current(one_line_code_obj.need_interactive)
        one_line_code_info_dict["combobox_need_interactive"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_question_keyword
        label_interactive_question_keyword = tkinter.Label(pop_window, text="交互问题关键词")
        label_interactive_question_keyword.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_interactive_question_keyword"] = tkinter.StringVar()
        entry_interactive_question_keyword = tkinter.Entry(pop_window,
                                                           textvariable=one_line_code_info_dict["sv_interactive_question_keyword"])
        entry_interactive_question_keyword.insert(0, str(one_line_code_obj.interactive_question_keyword))  # 显示初始值，可编辑
        entry_interactive_question_keyword.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_answer
        label_interactive_answer = tkinter.Label(pop_window, text="交互问题回答")
        label_interactive_answer.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_interactive_answer"] = tkinter.StringVar()
        entry_interactive_answer = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_interactive_answer"])
        entry_interactive_answer.insert(0, str(one_line_code_obj.interactive_answer))  # 显示初始值，可编辑
        entry_interactive_answer.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_process_method
        label_interactive_process_method = tkinter.Label(pop_window, text="交互回答次数")
        label_interactive_process_method.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        interactive_process_method_name_list = ["ONETIME", "TWICE", "LOOP"]
        one_line_code_info_dict["combobox_interactive_process_method"] = ttk.Combobox(pop_window,
                                                                                      values=interactive_process_method_name_list,
                                                                                      state="readonly")
        one_line_code_info_dict["combobox_interactive_process_method"].current(one_line_code_obj.interactive_process_method)
        one_line_code_info_dict["combobox_interactive_process_method"].grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-description
        label_description = tkinter.Label(pop_window, text="描述")
        label_description.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_description"] = tkinter.StringVar()
        entry_description = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_description"])
        entry_description.insert(0, str(one_line_code_obj.description))  # 显示初始值，可编辑
        entry_description.grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # 添加按钮
        exit_button = tkinter.Button(pop_window, text="返回", command=pop_window.destroy)
        exit_button.grid(row=8, column=1, padx=self.padx, pady=self.pady)

    def view_inspection_template(self):
        # 查看-inspection_template
        obj_info_text = tkinter.Text(master=self.top_frame_widget_dict["frame"])  # 创建多行文本框，用于显示资源信息
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
        # ★inspection_template-execution_at_time
        execution_at_time_list = ["execution_at_time".ljust(self.view_width, " "),
                                  ": ",
                                  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.resource_obj.execution_at_time)),
                                  "\n"]
        obj_info_text.insert(tkinter.END, "".join(execution_at_time_list))
        # ★inspection_template-update_code_on_launch
        update_code_on_launch_name_list = ["No", "Yes"]
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
        button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="返回巡检模板列表",
                                       command=lambda: self.global_info.main_window.nav_frame_r_resource_top_page_display(
                                           RESOURCE_TYPE_INSPECTION_TEMPLATE))  # 返回巡检模板列表
        button_return.pack()

    def view_custome_tag_config_scheme(self):
        # ★查看-scheme
        print("查看配色方案")
        print(self.resource_obj)
        obj_info_text = tkinter.Text(master=self.top_frame_widget_dict["frame"], height=9)  # 创建多行文本框，用于显示资源信息，需要绑定滚动条
        obj_info_text.insert(tkinter.END, "★★ 查看配色方案 ★★\n")
        # ★配色方案-名称
        scheme_name = "名称".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.name + "\n"
        obj_info_text.insert(tkinter.END, scheme_name)
        # ★配色方案-oid
        scheme_name = "id".ljust(self.view_width, " ") + ": " + self.resource_obj.oid + "\n"
        obj_info_text.insert(tkinter.END, scheme_name)
        # ★配色方案-描述
        scheme_description = "描述".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.description + "\n"
        obj_info_text.insert(tkinter.END, scheme_description)
        # ★配色方案-所属项目+项目id
        if self.global_info.get_project_by_oid(self.resource_obj.project_oid) is None:  # ★凡是有根据oid查找资源对象的，都要处理None的情况
            project_name = "Unknown!"
        else:
            project_name = self.global_info.get_project_by_oid(self.resource_obj.project_oid).name
        scheme_project_name = "所属项目".ljust(self.view_width - 4, " ") + ": " + project_name + "\n"
        obj_info_text.insert(tkinter.END, scheme_project_name)
        scheme_project_oid = "项目id".ljust(self.view_width - 2, " ") + ": " + self.resource_obj.project_oid + "\n"
        obj_info_text.insert(tkinter.END, scheme_project_oid)
        # ★配色方案-create_timestamp
        credential_create_timestamp = "create_time".ljust(self.view_width, " ") + ": " \
                                      + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.resource_obj.create_timestamp)) + "\n"
        obj_info_text.insert(tkinter.END, credential_create_timestamp)
        # ★配色方案-last_modify_timestamp
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
        # 添加custome_match_obj_frame用于列出匹配对象
        custome_match_obj_frame_width = self.global_info.main_window.nav_frame_r_width - 25
        custome_match_obj_frame_height = self.global_info.main_window.height - 220
        custome_match_obj_frame = tkinter.Frame(self.top_frame_widget_dict["frame"], width=custome_match_obj_frame_width,
                                                height=custome_match_obj_frame_height, bg="pink")
        # 在custome_match_obj_frame中添加canvas-frame滚动框
        self.resource_info_dict["custome_match_obj_frame_scrollbar"] = tkinter.Scrollbar(custome_match_obj_frame)
        self.resource_info_dict["custome_match_obj_frame_scrollbar"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.resource_info_dict["custome_match_obj_frame_canvas"] = tkinter.Canvas(custome_match_obj_frame, bg="black",
                                                                                   width=custome_match_obj_frame_width - 25,
                                                                                   height=custome_match_obj_frame_height,
                                                                                   yscrollcommand=self.resource_info_dict[
                                                                                       "custome_match_obj_frame_scrollbar"].set)
        self.resource_info_dict["custome_match_obj_frame_canvas"].pack()
        self.resource_info_dict["custome_match_obj_frame_scrollbar"].config(
            command=self.resource_info_dict["custome_match_obj_frame_canvas"].yview)
        self.resource_info_dict["custome_match_obj_frame_frame"] = tkinter.Frame(self.resource_info_dict["custome_match_obj_frame_canvas"],
                                                                                 bg="black")
        self.resource_info_dict["custome_match_obj_frame_frame"].pack()
        self.resource_info_dict["custome_match_obj_frame_canvas"].create_window((0, 0), window=self.resource_info_dict[
            "custome_match_obj_frame_frame"], anchor='nw')
        custome_match_obj_frame.pack()
        self.list_custome_match_obj_in_frame_frame()
        # ★★添加返回“配色方案列表”按钮★★
        button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="返回配色方案列表",
                                       command=self.back_to_custom_tag_config_pop_window)  # 返回“配色方案列表”
        button_return.pack()

    def list_custome_match_obj_in_frame_frame(self):
        for widget in self.resource_info_dict["custome_match_obj_frame_frame"].winfo_children():
            widget.destroy()
        row = 0
        for match_obj in self.resource_obj.custom_match_object_list:
            label_index = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"], text=str(row))
            text_demo = tkinter.Text(self.resource_info_dict["custome_match_obj_frame_frame"], fg="white",
                                     bg="black", width=26, height=3,
                                     font=("", 12),
                                     wrap=tkinter.NONE, spacing1=0, spacing2=0, spacing3=0)
            text_demo.insert(tkinter.END, match_obj.match_pattern_lines)
            label_foreground = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                             text="前景色: \n" + match_obj.foreground)
            label_backgroun = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                            text="背景色: \n" + match_obj.backgroun)
            if match_obj.underline:
                is_underline = "Yes"
            else:
                is_underline = "No"
            label_underline = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                            text="下划线: " + is_underline + "\n" + match_obj.underlinefg)
            if match_obj.overstrike:
                is_overstrike = "Yes"
            else:
                is_overstrike = "No"
            label_overstrike = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                             text="删除线: " + is_overstrike + "\n" + match_obj.overstrikefg)
            custom_match_font = font.Font(size=12, name="")
            if match_obj.bold:
                is_bold = "Yes"
                custom_match_font.configure(weight="bold")
            else:
                is_bold = "No"
            label_bold = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                       text="粗体: " + "\n" + is_bold)
            if match_obj.italic:
                is_italic = "Yes"
                custom_match_font.configure(slant="italic")
            else:
                is_italic = "No"
            label_italic = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                         text="斜体: " + "\n" + is_italic)
            tag_config_name = uuid.uuid4().__str__()  # <str>
            text_demo.tag_add(f"{tag_config_name}", "1.0", tkinter.END)
            text_demo.tag_config(f"{tag_config_name}",
                                 foreground=match_obj.foreground,
                                 backgroun=match_obj.backgroun,
                                 underline=match_obj.underline,
                                 underlinefg=match_obj.underlinefg,
                                 overstrike=match_obj.overstrike,
                                 overstrikefg=match_obj.overstrikefg,
                                 font=custom_match_font)
            label_index.grid(row=row, column=0, padx=self.padx, pady=self.pady, sticky="nswe")
            label_index.bind("<MouseWheel>", self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
            text_demo.grid(row=row, column=1, padx=self.padx, pady=self.pady, sticky="nswe")
            label_foreground.grid(row=row, column=2, padx=self.padx, pady=self.pady, sticky="nswe")
            label_foreground.bind("<MouseWheel>", self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_backgroun.grid(row=row, column=3, padx=self.padx, pady=self.pady, sticky="nswe")
            label_backgroun.bind("<MouseWheel>", self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_underline.grid(row=row, column=4, padx=self.padx, pady=self.pady, sticky="nswe")
            label_underline.bind("<MouseWheel>", self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_overstrike.grid(row=row, column=5, padx=self.padx, pady=self.pady, sticky="nswe")
            label_overstrike.bind("<MouseWheel>", self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_bold.grid(row=row, column=6, padx=self.padx, pady=self.pady, sticky="nswe")
            label_bold.bind("<MouseWheel>", self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_italic.grid(row=row, column=7, padx=self.padx, pady=self.pady, sticky="nswe")
            label_italic.bind("<MouseWheel>", self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
            row += 1
        # 还要更新frame和canvas才可滚动
        self.resource_info_dict["custome_match_obj_frame_frame"].update_idletasks()
        self.resource_info_dict["custome_match_obj_frame_canvas"].configure(
            scrollregion=(0, 0, self.resource_info_dict["custome_match_obj_frame_frame"].winfo_width(),
                          self.resource_info_dict["custome_match_obj_frame_frame"].winfo_height()))
        self.resource_info_dict["custome_match_obj_frame_canvas"].bind("<MouseWheel>",
                                                                       self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
        self.resource_info_dict["custome_match_obj_frame_frame"].bind("<MouseWheel>",
                                                                      self.view_custom_tag_config__proces_mouse_scroll__frame_frame)
        # 滚动条移到最开头
        self.resource_info_dict["custome_match_obj_frame_canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def view_custom_tag_config__proces_mouse_scroll__frame_frame(self, event):
        if event.delta > 0:
            self.resource_info_dict["custome_match_obj_frame_canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.resource_info_dict["custome_match_obj_frame_canvas"].yview_scroll(1, 'units')  # 向下移动

    def back_to_custom_tag_config_pop_window(self):
        self.top_frame_widget_dict["pop_window"].destroy()
        self.global_info.main_window.window_obj.focus_force()
        self.global_info.main_window.click_menu_settings_scheme_of_menu_bar_init()


class EditResourceInFrame:
    """
    在主窗口的查看资源界面，添加用于编辑资源信息的控件
    """

    def __init__(self, top_frame_widget_dict=None, global_info=None, resource_obj=None,
                 resource_type=RESOURCE_TYPE_PROJECT):
        self.top_frame_widget_dict = top_frame_widget_dict
        self.global_info = global_info
        self.resource_obj = resource_obj
        self.resource_type = resource_type
        self.resource_info_dict = {}  # 用于存储资源对象信息的diction，传出信息给<UpdateResourceInFrame>对象进行处理的
        self.padx = 2
        self.pady = 2
        self.current_row_index = 0

    def show(self):  # 入口函数
        for widget in self.top_frame_widget_dict["frame"].winfo_children():
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
        elif self.resource_type == RESOURCE_TYPE_CUSTOM_SCHEME:
            self.edit_custome_tag_config_scheme()
        else:
            print("<class EditResourceInFrame> resource_type is Unknown")
        self.add_save_and_return_button_in_top_frame()
        self.update_top_frame()  # 更新Frame的尺寸，并将滚动条移到最开头

    def add_save_and_return_button_in_top_frame(self):
        # ★创建“保存更新”按钮
        save_obj = UpdateResourceInFrame(self.resource_info_dict, self.global_info, self.resource_obj,
                                         self.resource_type)
        button_save = tkinter.Button(self.top_frame_widget_dict["frame"], text="保存更新", command=save_obj.update)
        button_save.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        button_save.grid(row=self.current_row_index + 1, column=0, padx=self.padx, pady=self.pady)
        # ★★添加“返回资源列表”按钮★★
        if self.resource_type == RESOURCE_TYPE_CUSTOM_SCHEME:
            button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="取消编辑",
                                           command=self.back_to_custom_tag_config_pop_window)
        else:
            button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="取消编辑",
                                           command=lambda: self.global_info.main_window.nav_frame_r_resource_top_page_display(
                                               self.resource_type))
        button_return.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        button_return.grid(row=self.current_row_index + 1, column=1, padx=self.padx, pady=self.pady)

    def back_to_custom_tag_config_pop_window(self):
        self.top_frame_widget_dict["pop_window"].destroy()
        self.global_info.main_window.window_obj.focus_force()
        self.global_info.main_window.click_menu_settings_scheme_of_menu_bar_init()

    def proces_mouse_scroll_of_top_frame(self, event):
        if event.delta > 0:
            self.top_frame_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.top_frame_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def update_top_frame(self):
        # 更新Frame的尺寸
        self.top_frame_widget_dict["frame"].update_idletasks()
        self.top_frame_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.top_frame_widget_dict["frame"].winfo_width(),
                          self.top_frame_widget_dict["frame"].winfo_height()))
        self.top_frame_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        self.top_frame_widget_dict["frame"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        # 滚动条移到最开头
        self.top_frame_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def edit_project(self):
        # ★编辑-project
        label_edit_project = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 编辑项目 ★★")
        label_edit_project.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★project-名称
        label_project_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目名称")
        label_project_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_project_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_project_name = tkinter.Entry(self.top_frame_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_project_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_project_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_project_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★project-描述
        label_project_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_project_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_project_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_project_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_description"])
        entry_project_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_project_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_project_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 2

    def edit_credential(self):
        # ★编辑-credential
        label_edit_credential = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 编辑凭据 ★★")
        label_edit_credential.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★credential-名称
        label_credential_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="凭据名称")
        label_credential_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_credential_name = tkinter.Entry(self.top_frame_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_credential_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_credential_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★credential-描述
        label_credential_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_credential_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_credential_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                     textvariable=self.resource_info_dict["sv_description"])
        entry_credential_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_credential_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★credential-所属项目
        label_credential_project_oid = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_credential_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★credential-凭据类型
        label_credential_type = tkinter.Label(self.top_frame_widget_dict["frame"], text="凭据类型")
        label_credential_type.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_type.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        cred_type_name_list = ["ssh_password", "ssh_key", "telnet", "ftp", "registry", "git"]
        self.resource_info_dict["combobox_cred_type"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=cred_type_name_list,
                                                                     state="readonly")
        if self.resource_obj.cred_type != -1:
            self.resource_info_dict["combobox_cred_type"].current(self.resource_obj.cred_type)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_cred_type"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★credential-用户名
        label_credential_username = tkinter.Label(self.top_frame_widget_dict["frame"], text="username")
        label_credential_username.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_username.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_username"] = tkinter.StringVar()
        entry_credential_username = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_username"])
        entry_credential_username.insert(0, self.resource_obj.username)  # 显示初始值，可编辑
        entry_credential_username.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_username.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★credential-密码
        label_credential_password = tkinter.Label(self.top_frame_widget_dict["frame"], text="password")
        label_credential_password.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_password.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_password"] = tkinter.StringVar()
        entry_credential_password = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_password"])
        entry_credential_password.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_password.insert(0, self.resource_obj.password)  # 显示初始值，可编辑
        entry_credential_password.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★credential-密钥
        label_credential_private_key = tkinter.Label(self.top_frame_widget_dict["frame"], text="ssh_private_key")
        label_credential_private_key.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_private_key.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["text_private_key"] = tkinter.Text(master=self.top_frame_widget_dict["frame"], height=3, width=32)
        self.resource_info_dict["text_private_key"].insert(1.0, self.resource_obj.private_key)  # 显示初始值，可编辑
        self.resource_info_dict["text_private_key"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权类型
        label_credential_privilege_escalation_method = tkinter.Label(self.top_frame_widget_dict["frame"],
                                                                     text="privilege_escalation_method")
        label_credential_privilege_escalation_method.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_privilege_escalation_method.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        privilege_escalation_method_list = ["su", "sudo"]
        self.resource_info_dict["combobox_privilege_escalation_method"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                                       values=privilege_escalation_method_list,
                                                                                       state="readonly")
        if self.resource_obj.privilege_escalation_method != -1:
            self.resource_info_dict["combobox_privilege_escalation_method"].current(self.resource_obj.privilege_escalation_method)
        self.resource_info_dict["combobox_privilege_escalation_method"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权用户
        label_credential_privilege_escalation_username = tkinter.Label(self.top_frame_widget_dict["frame"],
                                                                       text="privilege_escalation_username")
        label_credential_privilege_escalation_username.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_privilege_escalation_username.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_privilege_escalation_username"] = tkinter.StringVar()
        entry_credential_privilege_escalation_username = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                                       textvariable=self.resource_info_dict[
                                                                           "sv_privilege_escalation_username"])
        entry_credential_privilege_escalation_username.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_privilege_escalation_username.insert(0, self.resource_obj.privilege_escalation_username)  # 显示初始值，可编辑
        entry_credential_privilege_escalation_username.grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★credential-提权密码
        label_credential_privilege_escalation_password = tkinter.Label(self.top_frame_widget_dict["frame"],
                                                                       text="privilege_escalation_password")
        label_credential_privilege_escalation_password.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_privilege_escalation_password.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_privilege_escalation_password"] = tkinter.StringVar()
        entry_credential_privilege_escalation_password = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                                       textvariable=self.resource_info_dict[
                                                                           "sv_privilege_escalation_password"])
        entry_credential_privilege_escalation_password.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_privilege_escalation_password.insert(0, self.resource_obj.privilege_escalation_password)  # 显示初始值，可编辑
        entry_credential_privilege_escalation_password.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★credential-auth_url
        label_credential_auth_url = tkinter.Label(self.top_frame_widget_dict["frame"], text="auth_url")
        label_credential_auth_url.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_auth_url.grid(row=11, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_auth_url"] = tkinter.StringVar()
        entry_credential_auth_url = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                  textvariable=self.resource_info_dict["sv_auth_url"])
        entry_credential_auth_url.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_credential_auth_url.insert(0, self.resource_obj.auth_url)  # 显示初始值，可编辑
        entry_credential_auth_url.grid(row=11, column=1, padx=self.padx, pady=self.pady)
        # ★credential-ssl_verify
        label_credential_ssl_verify = tkinter.Label(self.top_frame_widget_dict["frame"], text="ssl_verify")
        label_credential_ssl_verify.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_ssl_verify.grid(row=12, column=0, padx=self.padx, pady=self.pady)
        ssl_verify_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_ssl_verify"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=ssl_verify_name_list,
                                                                      state="readonly")
        if self.resource_obj.ssl_verify != -1:
            self.resource_info_dict["combobox_ssl_verify"].current(self.resource_obj.ssl_verify)  # 显示初始值
        self.resource_info_dict["combobox_ssl_verify"].grid(row=12, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 12

    def edit_host(self):
        # ★创建-host
        label_edit_host = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 编辑主机 ★★")
        label_edit_host.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_edit_host.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★host-名称
        label_host_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机名称")
        label_host_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_host_name = tkinter.Entry(self.top_frame_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_host_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_host_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★host-描述
        label_host_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_host_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_host_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                               textvariable=self.resource_info_dict["sv_description"])
        entry_host_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_host_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★host-所属项目
        label_host_project_oid = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_host_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★host-address
        label_host_address = tkinter.Label(self.top_frame_widget_dict["frame"], text="address")
        label_host_address.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_address.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_address"] = tkinter.StringVar()
        entry_host_address = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                           textvariable=self.resource_info_dict["sv_address"])
        entry_host_address.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_address.insert(0, self.resource_obj.address)  # 显示初始值，可编辑
        entry_host_address.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★host-ssh_port
        label_host_ssh_port = tkinter.Label(self.top_frame_widget_dict["frame"], text="ssh_port")
        label_host_ssh_port.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_ssh_port.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_ssh_port"] = tkinter.StringVar()
        entry_host_ssh_port = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                            textvariable=self.resource_info_dict["sv_ssh_port"])
        entry_host_ssh_port.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_ssh_port.insert(0, self.resource_obj.ssh_port)  # 显示初始值，可编辑
        entry_host_ssh_port.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★host-telnet_port
        label_host_telnet_port = tkinter.Label(self.top_frame_widget_dict["frame"], text="telnet_port")
        label_host_telnet_port.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_telnet_port.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_telnet_port"] = tkinter.StringVar()
        entry_host_telnet_port = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                               textvariable=self.resource_info_dict["sv_telnet_port"])
        entry_host_telnet_port.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_telnet_port.insert(0, self.resource_obj.telnet_port)  # 显示初始值，可编辑
        entry_host_telnet_port.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★host-login_protocol
        label_host_login_protocol = tkinter.Label(self.top_frame_widget_dict["frame"], text="远程登录类型")
        label_host_login_protocol.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_login_protocol.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        login_protocol_name_list = ["ssh", "telnet"]
        self.resource_info_dict["combobox_login_protocol"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                          values=login_protocol_name_list,
                                                                          state="readonly")
        self.resource_info_dict["combobox_login_protocol"].current(self.resource_obj.login_protocol)
        self.resource_info_dict["combobox_login_protocol"].grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★host-first_auth_method
        label_host_first_auth_method = tkinter.Label(self.top_frame_widget_dict["frame"], text="优先认证类型")
        label_host_first_auth_method.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_first_auth_method.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        first_auth_method_name_list = ["priKey", "password"]
        self.resource_info_dict["combobox_first_auth_method"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                             values=first_auth_method_name_list,
                                                                             state="readonly")
        self.resource_info_dict["combobox_first_auth_method"].current(self.resource_obj.first_auth_method)
        self.resource_info_dict["combobox_first_auth_method"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★host-custom_scheme 终端配色方案
        label_host_custom_scheme = tkinter.Label(self.top_frame_widget_dict["frame"], text="终端配色方案")
        label_host_custom_scheme.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_custom_scheme.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        custom_scheme_name_list = []
        current_scheme_index = 0
        index = 0
        for scheme in self.global_info.custome_tag_config_scheme_obj_list:
            custom_scheme_name_list.append(scheme.name)
            if self.resource_obj.custome_tag_config_scheme_oid == scheme.oid:
                current_scheme_index = index
            index += 1
        self.resource_info_dict["combobox_custom_scheme"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                         values=custom_scheme_name_list,
                                                                         state="readonly")
        self.resource_info_dict["combobox_custom_scheme"].current(current_scheme_index)
        self.resource_info_dict["combobox_custom_scheme"].grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★host-凭据列表
        label_credential_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="凭据列表")
        label_credential_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_credential_list.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        frame.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 10

    def edit_host_group(self):
        # ★创建-host_group
        label_edit_host_group = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 编辑主机 ★★")
        label_edit_host_group.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_edit_host_group.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★host_group-名称
        label_host_group_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机名称")
        label_host_group_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_host_group_name = tkinter.Entry(self.top_frame_widget_dict["frame"], textvariable=self.resource_info_dict["sv_name"])
        entry_host_group_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_group_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_host_group_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-描述
        label_host_group_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_host_group_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_host_group_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                     textvariable=self.resource_info_dict["sv_description"])
        entry_host_group_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_host_group_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_host_group_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-所属项目
        label_host_group_project_oid = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_host_group_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-列表
        label_host_group_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机组列表")
        label_host_group_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_list.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        label_host_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机列表")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_list.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        label_edit_inspection_code_block = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 编辑巡检代码块 ★★")
        label_edit_inspection_code_block.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_edit_inspection_code_block.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-名称
        label_inspection_code_block_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检代码块名称")
        label_inspection_code_block_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_code_block_name = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                         textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_code_block_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_code_block_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_inspection_code_block_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-描述
        label_inspection_code_block_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_inspection_code_block_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_code_block_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                                textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_code_block_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_code_block_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_inspection_code_block_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_code_block-所属项目
        label_inspection_code_block_project_oid = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_inspection_code_block_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★命令内容-列表
        # ★★★编辑巡检代码内容并在treeview里显示★★★
        self.resource_info_dict["one_line_code_obj_list"] = []
        label_inspection_code_block_code_content = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检代码内容:")
        label_inspection_code_block_code_content.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_code_content.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        button_add_code_list = tkinter.Button(self.top_frame_widget_dict["frame"], text="编辑",
                                              command=lambda: self.click_button_add_code_list(treeview_code_content))  # 新建代码
        button_add_code_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        button_add_code_list.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        treeview_code_content = ttk.Treeview(self.top_frame_widget_dict["frame"], cursor="arrow", height=7,
                                             columns=("index", "code_content", "need_interactive"), show="headings")
        # 设置每一个列的宽度和对齐的方式
        treeview_code_content.column("index", width=50, anchor="w")
        treeview_code_content.column("code_content", width=300, anchor="w")
        treeview_code_content.column("need_interactive", width=80, anchor="w")
        # 设置每个列的标题
        treeview_code_content.heading("index", text="index", anchor="w")
        treeview_code_content.heading("code_content", text="code_content", anchor="w")
        treeview_code_content.heading("need_interactive", text="需要交互", anchor="w")
        # 插入code item
        index = 0
        need_interactive_value = ["No", "Yes"]
        for code_obj in self.resource_obj.code_list:
            treeview_code_content.insert("", index,
                                         values=(index, code_obj.code_content, need_interactive_value[code_obj.need_interactive]))
            index += 1
        treeview_code_content.grid(row=5, column=0, columnspan=2, padx=self.padx, pady=self.pady)
        # 单击指定的命令行，进行高级属性编辑
        treeview_code_content.bind("<<TreeviewSelect>>", lambda event: self.edit_treeview_code_content_item(event, treeview_code_content))
        # ★★更新row_index
        self.current_row_index = 5

    def click_button_add_code_list(self, treeview_code_content):
        pop_window = tkinter.Toplevel(self.global_info.main_window.window_obj)
        pop_window.title("添加巡检代码内容")
        screen_width = self.global_info.main_window.window_obj.winfo_screenwidth()
        screen_height = self.global_info.main_window.window_obj.winfo_screenheight()
        width = 420
        height = 300
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.global_info.main_window.window_obj.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        pop_window.protocol("WM_DELETE_WINDOW", lambda: self.edit_or_add_treeview_code_content_on_closing(pop_window))
        label_inspection_code_block_code_content = tkinter.Label(pop_window, text="巡检代码内容")
        label_inspection_code_block_code_content.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        text_code_content = tkinter.Text(master=pop_window, width=50, height=16)
        text_code_content.grid(row=1, column=0, columnspan=2, padx=self.padx, pady=self.pady)
        ok_button = tkinter.Button(pop_window, text="确定",
                                   command=lambda: self.click_button_add_code_list_ok(treeview_code_content, text_code_content, pop_window))
        ok_button.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        cancel_button = tkinter.Button(pop_window, text="取消", command=lambda: self.click_button_add_code_list_cancel(pop_window))
        cancel_button.grid(row=2, column=1, padx=self.padx, pady=self.pady)

    def click_button_add_code_list_cancel(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def click_button_add_code_list_ok(self, treeview_code_content, text_code_content, pop_window):
        self.resource_obj.code_list = []
        code_content_str = text_code_content.get("1.0", tkinter.END).strip()
        code_index = 0
        for code_line_str in code_content_str.split("\n"):
            code_line_str_strip = code_line_str.strip()
            if code_line_str_strip != "":
                one_line_code_obj = OneLineCode(code_index=code_index, code_content=code_line_str_strip)
                self.resource_obj.code_list.append(one_line_code_obj)
                code_index += 1
        print("CreateResourceInFrame.click_button_add_code_list_ok: 添加代码行数:",
              len(self.resource_obj.code_list))
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点
        # 刷新一次treeview
        treeview_code_content.delete(*treeview_code_content.get_children())
        index = 0
        need_interactive_value = ["No", "Yes"]
        for code_obj in self.resource_obj.code_list:
            treeview_code_content.insert("", index,
                                         values=(index, code_obj.code_content, need_interactive_value[code_obj.need_interactive]))
            index += 1

    def edit_treeview_code_content_item(self, _, treeview_code_content):
        item_index = treeview_code_content.focus()
        print("item_index=", item_index)
        if item_index == "":
            return
        one_line_code_index, _, _ = treeview_code_content.item(item_index, "values")
        print("one_line_code_index", one_line_code_index)
        one_line_code_obj = self.resource_obj.code_list[int(one_line_code_index)]  # 获取选中的命令对象
        pop_window = tkinter.Toplevel(self.global_info.main_window.window_obj)
        pop_window.title("设置巡检代码")
        screen_width = self.global_info.main_window.window_obj.winfo_screenwidth()
        screen_height = self.global_info.main_window.window_obj.winfo_screenheight()
        width = 420
        height = 300
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.global_info.main_window.window_obj.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        pop_window.protocol("WM_DELETE_WINDOW", lambda: self.edit_or_add_treeview_code_content_on_closing(pop_window))
        one_line_code_info_dict = {}
        # OneLineCode-code_index
        label_code_index = tkinter.Label(pop_window, text="巡检代码index")
        label_code_index.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        entry_code_index = tkinter.Entry(pop_window)
        entry_code_index.insert(0, str(one_line_code_obj.code_index))  # 显示初始值，index不可编辑★
        entry_code_index.grid(row=0, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-code_content
        label_code_content = tkinter.Label(pop_window, text="巡检代码内容")
        label_code_content.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_code_content"] = tkinter.StringVar()
        entry_code_content = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_code_content"])
        entry_code_content.insert(0, str(one_line_code_obj.code_content))  # 显示初始值，可编辑
        entry_code_content.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-code_post_wait_time
        label_code_post_wait_time = tkinter.Label(pop_window, text="代码执行后等待时间")
        label_code_post_wait_time.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_code_post_wait_time"] = tkinter.StringVar()
        entry_code_post_wait_time = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_code_post_wait_time"])
        entry_code_post_wait_time.insert(0, str(one_line_code_obj.code_post_wait_time))  # 显示初始值，可编辑
        entry_code_post_wait_time.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-need_interactive
        label_need_interactive = tkinter.Label(pop_window, text="是否需要交互")
        label_need_interactive.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        need_interactive_name_list = ["No", "Yes"]
        one_line_code_info_dict["combobox_need_interactive"] = ttk.Combobox(pop_window,
                                                                            values=need_interactive_name_list,
                                                                            state="readonly")
        one_line_code_info_dict["combobox_need_interactive"].current(one_line_code_obj.need_interactive)
        one_line_code_info_dict["combobox_need_interactive"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_question_keyword
        label_interactive_question_keyword = tkinter.Label(pop_window, text="交互问题关键词")
        label_interactive_question_keyword.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_interactive_question_keyword"] = tkinter.StringVar()
        entry_interactive_question_keyword = tkinter.Entry(pop_window,
                                                           textvariable=one_line_code_info_dict["sv_interactive_question_keyword"])
        entry_interactive_question_keyword.insert(0, str(one_line_code_obj.interactive_question_keyword))  # 显示初始值，可编辑
        entry_interactive_question_keyword.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_answer
        label_interactive_answer = tkinter.Label(pop_window, text="交互问题回答")
        label_interactive_answer.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_interactive_answer"] = tkinter.StringVar()
        entry_interactive_answer = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_interactive_answer"])
        entry_interactive_answer.insert(0, str(one_line_code_obj.interactive_answer))  # 显示初始值，可编辑
        entry_interactive_answer.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-interactive_process_method
        label_interactive_process_method = tkinter.Label(pop_window, text="交互回答次数")
        label_interactive_process_method.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        interactive_process_method_name_list = ["ONETIME", "TWICE", "LOOP"]
        one_line_code_info_dict["combobox_interactive_process_method"] = ttk.Combobox(pop_window,
                                                                                      values=interactive_process_method_name_list,
                                                                                      state="readonly")
        one_line_code_info_dict["combobox_interactive_process_method"].current(one_line_code_obj.interactive_process_method)
        one_line_code_info_dict["combobox_interactive_process_method"].grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # OneLineCode-description
        label_description = tkinter.Label(pop_window, text="描述")
        label_description.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        one_line_code_info_dict["sv_description"] = tkinter.StringVar()
        entry_description = tkinter.Entry(pop_window, textvariable=one_line_code_info_dict["sv_description"])
        entry_description.insert(0, str(one_line_code_obj.description))  # 显示初始值，可编辑
        entry_description.grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # 添加按钮
        ok_button = tkinter.Button(pop_window, text="保存修改",
                                   command=lambda: self.edit_treeview_code_content_item_save(one_line_code_info_dict,
                                                                                             one_line_code_obj,
                                                                                             pop_window, treeview_code_content))
        ok_button.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        cancel_button = tkinter.Button(pop_window, text="取消", command=lambda: self.edit_treeview_code_content_item_cancel(pop_window))
        cancel_button.grid(row=8, column=1, padx=self.padx, pady=self.pady)

    def edit_treeview_code_content_item_cancel(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def edit_treeview_code_content_item_save(self, one_line_code_info_dict, one_line_code_obj, pop_window, treeview_code_content):
        one_line_code_obj.code_content = one_line_code_info_dict["sv_code_content"].get()
        one_line_code_obj.code_post_wait_time = float(one_line_code_info_dict["sv_code_post_wait_time"].get())
        if one_line_code_info_dict["combobox_need_interactive"].current() == -1:
            one_line_code_obj.need_interactive = 0
        else:
            one_line_code_obj.need_interactive = one_line_code_info_dict["combobox_need_interactive"].current()
        one_line_code_obj.interactive_question_keyword = one_line_code_info_dict["sv_interactive_question_keyword"].get()
        one_line_code_obj.interactive_answer = one_line_code_info_dict["sv_interactive_answer"].get()
        if one_line_code_info_dict["combobox_interactive_process_method"].current() == -1:
            one_line_code_obj.interactive_process_method = 0
        else:
            one_line_code_obj.interactive_process_method = one_line_code_info_dict["combobox_interactive_process_method"].current()
        one_line_code_obj.description = one_line_code_info_dict["sv_description"].get()
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点
        # ★刷新一次treeview
        item_id_list = treeview_code_content.get_children()
        index = 0
        need_interactive_value = ["No", "Yes"]
        for code_obj in self.resource_obj.code_list:
            treeview_code_content.set(item_id_list[index], 1, code_obj.code_content)
            treeview_code_content.set(item_id_list[index], 2, need_interactive_value[code_obj.need_interactive])
            index += 1

    def edit_or_add_treeview_code_content_on_closing(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def edit_inspection_template(self):
        # ★创建-inspection_template
        label_edit_inspection_template = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 编辑巡检模板 ★★")
        label_edit_inspection_template.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_edit_inspection_template.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_template-名称
        label_inspection_template_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检模板名称")
        label_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_template_name = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                       textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_inspection_template_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-描述
        label_inspection_template_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_template_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                              textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_inspection_template_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-所属项目
        label_inspection_template_project_oid = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_inspection_template_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_method
        label_inspection_template_execution_method = tkinter.Label(self.top_frame_widget_dict["frame"], text="execution_method")
        label_inspection_template_execution_method.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_execution_method.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        execution_method_name_list = ["无", "定时执行", "周期执行", "After"]
        self.resource_info_dict["combobox_execution_method"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                            values=execution_method_name_list,
                                                                            state="readonly")
        self.resource_info_dict["combobox_execution_method"].current(self.resource_obj.execution_method)
        self.resource_info_dict["combobox_execution_method"].grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_at_time 这里应该使用日历框及时间设置框，先简化为直接输入 "2024-03-14 09:51:26" 这类字符串
        label_inspection_template_execution_at_time = tkinter.Label(self.top_frame_widget_dict["frame"], text="execution_at_time")
        label_inspection_template_execution_at_time.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_execution_at_time.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_execution_at_time"] = tkinter.StringVar()
        entry_inspection_template_execution_at_time = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                                    textvariable=self.resource_info_dict["sv_execution_at_time"])
        execution_at_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.resource_obj.execution_at_time))
        entry_inspection_template_execution_at_time.insert(0, execution_at_time)
        entry_inspection_template_execution_at_time.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_execution_at_time.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-update_code_on_launch
        label_inspection_template_update_code_on_launch = tkinter.Label(self.top_frame_widget_dict["frame"], text="运行前更新code")
        label_inspection_template_update_code_on_launch.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_update_code_on_launch.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        update_code_on_launch_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_update_code_on_launch"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                                 values=update_code_on_launch_name_list,
                                                                                 state="readonly")
        self.resource_info_dict["combobox_update_code_on_launch"].current(self.resource_obj.update_code_on_launch)
        self.resource_info_dict["combobox_update_code_on_launch"].grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-forks
        label_inspection_template_forks = tkinter.Label(self.top_frame_widget_dict["frame"], text="运行线程数")
        label_inspection_template_forks.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_forks.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_forks"] = tkinter.StringVar()
        spinbox_inspection_template_forks = tkinter.Spinbox(self.top_frame_widget_dict["frame"], from_=1, to=256, increment=1,
                                                            textvariable=self.resource_info_dict["sv_forks"])
        self.resource_info_dict["sv_forks"].set(self.resource_obj.forks)  # 显示初始值，可编辑
        spinbox_inspection_template_forks.grid(row=7, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-save_output_to_file
        label_inspection_template_save_output_to_file = tkinter.Label(self.top_frame_widget_dict["frame"], text="自动保存巡检日志到文件")
        label_inspection_template_save_output_to_file.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_save_output_to_file.grid(row=8, column=0, padx=self.padx, pady=self.pady)
        save_output_to_file_name_list = ["No", "Yes"]
        self.resource_info_dict["combobox_save_output_to_file"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                               values=save_output_to_file_name_list,
                                                                               state="readonly")
        self.resource_info_dict["combobox_save_output_to_file"].current(self.resource_obj.save_output_to_file)
        self.resource_info_dict["combobox_save_output_to_file"].grid(row=8, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-output_file_name_style
        label_inspection_template_output_file_name_style = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检日志文件名称")
        label_inspection_template_output_file_name_style.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_output_file_name_style.grid(row=9, column=0, padx=self.padx, pady=self.pady)
        output_file_name_style_name_list = ["HOSTNAME", "HOSTNAME-DATE", "HOSTNAME-DATE-TIME", "DATE_DIR/HOSTNAME",
                                            "DATE_DIR/HOSTNAME-DATE",
                                            "DATE_DIR/HOSTNAME-DATE-TIME"]
        self.resource_info_dict["combobox_output_file_name_style"] = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                                                  values=output_file_name_style_name_list,
                                                                                  state="readonly", width=32)
        self.resource_info_dict["combobox_output_file_name_style"].current(self.resource_obj.output_file_name_style)
        self.resource_info_dict["combobox_output_file_name_style"].grid(row=9, column=1, padx=self.padx, pady=self.pady)
        # ★host_group-列表
        label_host_group_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机组列表")
        label_host_group_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_group_list.grid(row=10, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        frame.grid(row=10, column=1, padx=self.padx, pady=self.pady)
        # ★host-列表
        label_host_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="主机列表")
        label_host_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_host_list.grid(row=11, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        frame.grid(row=11, column=1, padx=self.padx, pady=self.pady)
        # ★巡检代码块-列表
        label_inspection_code_block_list = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检代码块列表")
        label_inspection_code_block_list.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_code_block_list.grid(row=12, column=0, padx=self.padx, pady=self.pady)
        frame = tkinter.Frame(self.top_frame_widget_dict["frame"])
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
        frame.grid(row=12, column=1, padx=self.padx, pady=self.pady)
        # ★★更新row_index
        self.current_row_index = 12

    def edit_custome_tag_config_scheme(self):
        self.resource_info_dict["pop_window"] = self.top_frame_widget_dict["pop_window"]
        # ★创建-scheme
        label_edit_inspection_template = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 编辑配色方案 ★★")
        label_edit_inspection_template.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_edit_inspection_template.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★scheme-名称
        label_inspection_template_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="配色方案名称")
        label_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_name"] = tkinter.StringVar()
        entry_inspection_template_name = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                       textvariable=self.resource_info_dict["sv_name"])
        entry_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_name.insert(0, self.resource_obj.name)  # 显示初始值，可编辑
        entry_inspection_template_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★scheme-描述
        label_inspection_template_description = tkinter.Label(self.top_frame_widget_dict["frame"], text="描述")
        label_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_description.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        self.resource_info_dict["sv_description"] = tkinter.StringVar()
        entry_inspection_template_description = tkinter.Entry(self.top_frame_widget_dict["frame"],
                                                              textvariable=self.resource_info_dict["sv_description"])
        entry_inspection_template_description.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_description.insert(0, self.resource_obj.description)  # 显示初始值，可编辑
        entry_inspection_template_description.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★scheme-所属项目
        label_inspection_template_project_oid = tkinter.Label(self.top_frame_widget_dict["frame"], text="项目")
        label_inspection_template_project_oid.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_project_oid.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        project_obj_name_list = []
        project_obj_index = 0
        index = 0
        for project_obj in self.global_info.project_obj_list:
            project_obj_name_list.append(project_obj.name)
            if self.resource_obj.project_oid == project_obj.oid:
                project_obj_index = index
            index += 1
        self.resource_info_dict["combobox_project"] = ttk.Combobox(self.top_frame_widget_dict["frame"], values=project_obj_name_list,
                                                                   state="readonly")
        self.resource_info_dict["combobox_project"].current(project_obj_index)  # 显示初始值，可重新选择
        self.resource_info_dict["combobox_project"].grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # 添加custome_match_obj_frame用于列出匹配对象
        add_custome_match_obj_button = tkinter.Button(self.top_frame_widget_dict["frame"], text="添加匹配对象",
                                                      command=lambda: self.edit_custom_tag_config_scheme__add_custome_match_object())
        add_custome_match_obj_button.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        custome_match_obj_frame_width = self.global_info.main_window.nav_frame_r_width - 25
        custome_match_obj_frame_height = self.global_info.main_window.height - 220
        custome_match_obj_frame = tkinter.Frame(self.top_frame_widget_dict["frame"], width=custome_match_obj_frame_width,
                                                height=custome_match_obj_frame_height, bg="pink")
        # 在custome_match_obj_frame中添加canvas-frame滚动框
        self.resource_info_dict["custome_match_obj_frame_scrollbar"] = tkinter.Scrollbar(custome_match_obj_frame)
        self.resource_info_dict["custome_match_obj_frame_scrollbar"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.resource_info_dict["custome_match_obj_frame_canvas"] = tkinter.Canvas(custome_match_obj_frame, bg="black",
                                                                                   width=custome_match_obj_frame_width - 25,
                                                                                   height=custome_match_obj_frame_height,
                                                                                   yscrollcommand=self.resource_info_dict[
                                                                                       "custome_match_obj_frame_scrollbar"].set)
        self.resource_info_dict["custome_match_obj_frame_canvas"].pack()
        self.resource_info_dict["custome_match_obj_frame_scrollbar"].config(
            command=self.resource_info_dict["custome_match_obj_frame_canvas"].yview)
        self.resource_info_dict["custome_match_obj_frame_frame"] = tkinter.Frame(self.resource_info_dict["custome_match_obj_frame_canvas"],
                                                                                 bg="black")
        self.resource_info_dict["custome_match_obj_frame_frame"].pack()
        self.resource_info_dict["custome_match_obj_frame_canvas"].create_window((0, 0), window=self.resource_info_dict[
            "custome_match_obj_frame_frame"], anchor='nw')
        custome_match_obj_frame.grid(row=5, column=0, columnspan=2, padx=self.padx, pady=self.pady)
        self.edit_custome_tag_config_scheme__list_custome_match_obj_in_frame_frame()
        # ★★更新row_index
        self.current_row_index = 5

    def edit_custom_tag_config_scheme__add_custome_match_object(self):
        add_match_obj_pop_window = tkinter.Toplevel(self.resource_info_dict["pop_window"])
        add_match_obj_pop_window.title("配色方案设置")
        screen_width = add_match_obj_pop_window.winfo_screenwidth()
        screen_height = add_match_obj_pop_window.winfo_screenheight()
        width = self.global_info.main_window.nav_frame_r_width - 50
        height = self.global_info.main_window.height - 50
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        add_match_obj_pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.resource_info_dict["pop_window"].attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        add_match_obj_pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        add_match_obj_pop_window.protocol("WM_DELETE_WINDOW",
                                          lambda: self.edit_custom_tag_config_scheme__add_custome_match_object__cancel(
                                              add_match_obj_pop_window))
        # 添加用于设置CustomMatchObject属性的控件
        match_obj_info_dict = {}
        label_match_pattern_lines = tkinter.Label(add_match_obj_pop_window, text="添加需要匹配的字符串或正则表达式，一行一个")
        label_match_pattern_lines.grid(row=0, column=0, columnspan=4, padx=self.padx, pady=self.pady, sticky="w")
        match_obj_info_dict["text_match_pattern_lines"] = tkinter.Text(add_match_obj_pop_window, height=9)
        match_obj_info_dict["text_match_pattern_lines"].grid(row=1, column=0, columnspan=4, padx=self.padx, pady=self.pady)
        # -- 匹配字符-前景色
        label_foreground = tkinter.Label(add_match_obj_pop_window, text="匹配字符-前景色")
        label_foreground.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        match_obj_info_dict["sv_foreground"] = tkinter.StringVar()
        entry_foreground = tkinter.Entry(add_match_obj_pop_window, textvariable=match_obj_info_dict["sv_foreground"])
        entry_foreground.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        color_button_foreground = tkinter.Button(add_match_obj_pop_window, text="选择颜色",
                                                 command=lambda: self.edit_custom_tag_config_scheme__choose_color_of_custome_match_object(
                                                     entry_foreground, add_match_obj_pop_window))
        color_button_foreground.grid(row=2, column=2, padx=self.padx, pady=self.pady)
        # -- 匹配字符-背景色
        label_backgroun = tkinter.Label(add_match_obj_pop_window, text="匹配字符-背景色")
        label_backgroun.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        match_obj_info_dict["sv_backgroun"] = tkinter.StringVar()
        entry_backgroun = tkinter.Entry(add_match_obj_pop_window, textvariable=match_obj_info_dict["sv_backgroun"])
        entry_backgroun.grid(row=3, column=1, padx=self.padx, pady=self.pady)
        color_button_backgroun = tkinter.Button(add_match_obj_pop_window, text="选择颜色",
                                                command=lambda: self.edit_custom_tag_config_scheme__choose_color_of_custome_match_object(
                                                    entry_backgroun, add_match_obj_pop_window))
        color_button_backgroun.grid(row=3, column=2, padx=self.padx, pady=self.pady)
        # -- 匹配字符-下划线
        match_obj_info_dict["var_ck_underline"] = tkinter.BooleanVar()
        ck_underline = tkinter.Checkbutton(add_match_obj_pop_window, text="添加下划线", variable=match_obj_info_dict["var_ck_underline"])
        ck_underline.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        # -- 匹配字符-下划线颜色
        label_underlinefg = tkinter.Label(add_match_obj_pop_window, text="下划线颜色")
        label_underlinefg.grid(row=4, column=1, padx=self.padx, pady=self.pady, sticky="e")
        match_obj_info_dict["sv_underlinefg"] = tkinter.StringVar()
        entry_underlinefg = tkinter.Entry(add_match_obj_pop_window, textvariable=match_obj_info_dict["sv_underlinefg"])
        entry_underlinefg.grid(row=4, column=2, padx=self.padx, pady=self.pady)
        color_button_underlinefg = tkinter.Button(add_match_obj_pop_window, text="选择颜色",
                                                  command=lambda: self.edit_custom_tag_config_scheme__choose_color_of_custome_match_object(
                                                      entry_underlinefg, add_match_obj_pop_window))
        color_button_underlinefg.grid(row=4, column=3, padx=self.padx, pady=self.pady)
        # -- 匹配字符-删除线
        match_obj_info_dict["var_ck_overstrike"] = tkinter.BooleanVar()
        ck_overstrike = tkinter.Checkbutton(add_match_obj_pop_window, text="添加删除线", variable=match_obj_info_dict["var_ck_overstrike"])
        ck_overstrike.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        # -- 匹配字符-删除线颜色
        label_overstrikefg = tkinter.Label(add_match_obj_pop_window, text="删除线颜色")
        label_overstrikefg.grid(row=5, column=1, padx=self.padx, pady=self.pady, sticky="e")
        match_obj_info_dict["sv_overstrikefg"] = tkinter.StringVar()
        entry_overstrikefg = tkinter.Entry(add_match_obj_pop_window, textvariable=match_obj_info_dict["sv_overstrikefg"])
        entry_overstrikefg.configure()
        entry_overstrikefg.grid(row=5, column=2, padx=self.padx, pady=self.pady)
        color_button_overstrikefg = tkinter.Button(add_match_obj_pop_window, text="选择颜色",
                                                   command=lambda: self.edit_custom_tag_config_scheme__choose_color_of_custome_match_object(
                                                       entry_overstrikefg, add_match_obj_pop_window))
        color_button_overstrikefg.grid(row=5, column=3, padx=self.padx, pady=self.pady)
        # -- 匹配字符-粗体
        match_obj_info_dict["var_ck_bold"] = tkinter.BooleanVar()
        ck_bold = tkinter.Checkbutton(add_match_obj_pop_window, text="粗体", variable=match_obj_info_dict["var_ck_bold"])
        ck_bold.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        # -- 匹配字符-斜体
        match_obj_info_dict["var_ck_italic"] = tkinter.BooleanVar()
        ck_italic = tkinter.Checkbutton(add_match_obj_pop_window, text="斜体", variable=match_obj_info_dict["var_ck_italic"])
        ck_italic.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        # 添加确定按钮
        button_ok = tkinter.Button(add_match_obj_pop_window, text="确定",
                                   command=lambda: self.edit_custom_tag_config_scheme__add_custome_match_object__ok(match_obj_info_dict,
                                                                                                                    add_match_obj_pop_window))
        button_ok.grid(row=7, column=0, padx=self.padx, pady=self.pady)
        # 添加取消按钮
        button_cancel = tkinter.Button(add_match_obj_pop_window, text="取消",
                                       command=lambda: self.edit_custom_tag_config_scheme__add_custome_match_object__cancel(
                                           add_match_obj_pop_window))
        button_cancel.grid(row=7, column=1, padx=self.padx, pady=self.pady)

    def edit_custom_tag_config_scheme__add_custome_match_object__ok(self, match_obj_info_dict,
                                                                    add_match_obj_pop_window):
        # 先在 custome_match_obj_frame_frame 列出刚刚添加的match_obj
        match_obj = CustomMatchObject(match_pattern_lines=match_obj_info_dict["text_match_pattern_lines"].get("1.0", tkinter.END + "-1c"),
                                      foreground=match_obj_info_dict["sv_foreground"].get(),
                                      backgroun=match_obj_info_dict["sv_backgroun"].get(),
                                      underline=match_obj_info_dict["var_ck_underline"].get(),
                                      underlinefg=match_obj_info_dict["sv_underlinefg"].get(),
                                      overstrike=match_obj_info_dict["var_ck_overstrike"].get(),
                                      overstrikefg=match_obj_info_dict["sv_overstrikefg"].get(),
                                      bold=match_obj_info_dict["var_ck_bold"].get(),
                                      italic=match_obj_info_dict["var_ck_italic"].get()
                                      )
        self.resource_obj.custom_match_object_list.append(match_obj)
        self.edit_custome_tag_config_scheme__list_custome_match_obj_in_frame_frame()
        # 再返回到 编辑配色方案 界面
        add_match_obj_pop_window.destroy()  # 关闭子窗口
        self.resource_info_dict["pop_window"].attributes("-disabled", 0)  # 使主窗口响应
        self.resource_info_dict["pop_window"].focus_force()  # 使主窗口获得焦点

    def edit_custom_tag_config_scheme__add_custome_match_object__cancel(self, add_match_obj_pop_window):
        # 返回到 创建配色方案 界面
        add_match_obj_pop_window.destroy()  # 关闭子窗口
        self.resource_info_dict["pop_window"].attributes("-disabled", 0)  # 使主窗口响应
        self.resource_info_dict["pop_window"].focus_force()  # 使主窗口获得焦点

    @staticmethod
    def edit_custom_tag_config_scheme__choose_color_of_custome_match_object(entry, add_match_obj_pop_window):
        add_match_obj_pop_window.focus_force()
        color = tkinter.colorchooser.askcolor()
        if color[1] is not None:
            entry.delete(0, tkinter.END)
            entry.insert(0, color[1])
            entry.configure(bg=color[1])
        add_match_obj_pop_window.focus_force()

    def edit_custome_tag_config_scheme__list_custome_match_obj_in_frame_frame(self):
        for widget in self.resource_info_dict["custome_match_obj_frame_frame"].winfo_children():
            widget.destroy()
        row = 0
        for match_obj in self.resource_obj.custom_match_object_list:
            label_index = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"], text=str(row))
            text_demo = tkinter.Text(self.resource_info_dict["custome_match_obj_frame_frame"], fg="white",
                                     bg="black", width=18, height=3,
                                     font=("", 12),
                                     wrap=tkinter.NONE, spacing1=0, spacing2=0, spacing3=0)
            text_demo.insert(tkinter.END, match_obj.match_pattern_lines)
            label_foreground = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                             text="前景色: \n" + match_obj.foreground)
            label_backgroun = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                            text="背景色: \n" + match_obj.backgroun)
            if match_obj.underline:
                is_underline = "Yes"
            else:
                is_underline = "No"
            label_underline = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                            text="下划线: " + is_underline + "\n" + match_obj.underlinefg)
            if match_obj.overstrike:
                is_overstrike = "Yes"
            else:
                is_overstrike = "No"
            label_overstrike = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                             text="删除线: " + is_overstrike + "\n" + match_obj.overstrikefg)
            custom_match_font = font.Font(size=12, name="")
            if match_obj.bold:
                is_bold = "Yes"
                custom_match_font.configure(weight="bold")
            else:
                is_bold = "No"
            label_bold = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                       text="粗体: " + "\n" + is_bold)
            if match_obj.italic:
                is_italic = "Yes"
                custom_match_font.configure(slant="italic")
            else:
                is_italic = "No"
            label_italic = tkinter.Label(self.resource_info_dict["custome_match_obj_frame_frame"],
                                         text="斜体: " + "\n" + is_italic)
            tag_config_name = uuid.uuid4().__str__()  # <str>
            text_demo.tag_add(f"{tag_config_name}", "1.0", tkinter.END)
            text_demo.tag_config(f"{tag_config_name}",
                                 foreground=match_obj.foreground,
                                 backgroun=match_obj.backgroun,
                                 underline=match_obj.underline,
                                 underlinefg=match_obj.underlinefg,
                                 overstrike=match_obj.overstrike,
                                 overstrikefg=match_obj.overstrikefg,
                                 font=custom_match_font)
            edit_match_obj_obj = EditCustomMatchObject(top_window=self.resource_info_dict["pop_window"],
                                                       call_back_class_obj=self,
                                                       match_obj=match_obj, global_info=self.global_info,
                                                       call_back_class=CALL_BACK_CLASS_EDIT_RESOURCE)
            button_edit = tkinter.Button(self.resource_info_dict["custome_match_obj_frame_frame"], text="编辑",
                                         command=edit_match_obj_obj.edit_custome_match_object)
            delete_match_obj_obj = DeleteCustomMatchObject(call_back_class_obj=self,
                                                           match_obj=match_obj,
                                                           call_back_class=CALL_BACK_CLASS_EDIT_RESOURCE)
            button_delete = tkinter.Button(self.resource_info_dict["custome_match_obj_frame_frame"], text="删除",
                                           command=delete_match_obj_obj.delete_custome_match_object)
            label_index.grid(row=row, column=0, padx=self.padx, pady=self.pady, sticky="nswe")
            label_index.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            text_demo.grid(row=row, column=1, padx=self.padx, pady=self.pady, sticky="nswe")
            label_foreground.grid(row=row, column=2, padx=self.padx, pady=self.pady, sticky="nswe")
            label_foreground.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_backgroun.grid(row=row, column=3, padx=self.padx, pady=self.pady, sticky="nswe")
            label_backgroun.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_underline.grid(row=row, column=4, padx=self.padx, pady=self.pady, sticky="nswe")
            label_underline.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_overstrike.grid(row=row, column=5, padx=self.padx, pady=self.pady, sticky="nswe")
            label_overstrike.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_bold.grid(row=row, column=6, padx=self.padx, pady=self.pady, sticky="nswe")
            label_bold.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            label_italic.grid(row=row, column=7, padx=self.padx, pady=self.pady, sticky="nswe")
            label_italic.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            button_edit.grid(row=row, column=8, padx=self.padx, pady=self.pady, sticky="nswe")
            button_edit.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            button_delete.grid(row=row, column=9, padx=self.padx, pady=self.pady, sticky="nswe")
            button_delete.bind("<MouseWheel>", self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
            row += 1
        # 还要更新frame和canvas才可滚动
        self.resource_info_dict["custome_match_obj_frame_frame"].update_idletasks()
        self.resource_info_dict["custome_match_obj_frame_canvas"].configure(
            scrollregion=(0, 0, self.resource_info_dict["custome_match_obj_frame_frame"].winfo_width(),
                          self.resource_info_dict["custome_match_obj_frame_frame"].winfo_height()))
        self.resource_info_dict["custome_match_obj_frame_canvas"].bind("<MouseWheel>",
                                                                       self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
        self.resource_info_dict["custome_match_obj_frame_frame"].bind("<MouseWheel>",
                                                                      self.edit_custom_tag_config__proces_mouse_scroll__frame_frame)
        # 滚动条移到最开头
        self.resource_info_dict["custome_match_obj_frame_canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def edit_custom_tag_config__proces_mouse_scroll__frame_frame(self, event):
        if event.delta > 0:
            self.resource_info_dict["custome_match_obj_frame_canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.resource_info_dict["custome_match_obj_frame_canvas"].yview_scroll(1, 'units')  # 向下移动


class UpdateResourceInFrame:
    """
    在主窗口的创建资源界面，点击“保存更新”按钮时，更新并保存资源信息
    """

    def __init__(self, resource_info_dict=None, global_info=None, resource_obj=None,
                 resource_type=None):
        self.resource_info_dict = resource_info_dict  # 由<EditResourceInFrame>对象返回的被编辑资源的信息
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
        elif self.resource_type == RESOURCE_TYPE_CUSTOM_SCHEME:
            self.update_custome_tag_config_scheme()
        else:
            print("<class UpdateResourceInFrame> resource_type is Unknown")

    def update_project(self):
        project_name = self.resource_info_dict["sv_name"].get()
        project_description = self.resource_info_dict["sv_description"].get()
        print(project_name, project_description)
        # 更新-project
        if project_name == '':
            messagebox.showinfo("更新项目-Error", f"项目名称不能为空")
        elif len(project_name) > 128:
            messagebox.showinfo("更新项目-Error", f"项目名称>128字符")
        elif len(project_description) > 256:
            messagebox.showinfo("更新项目-Error", f"项目描述>256字符")
        elif self.global_info.is_project_name_existed_except_self(project_name, self.resource_obj):
            messagebox.showinfo("更新项目-Error", f"项目名称已存在")
        else:
            self.resource_obj.update(name=project_name, description=project_description, global_info=self.global_info)
            self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_PROJECT)  # 更新项目信息后，返回项目展示页面

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
            messagebox.showinfo("更新凭据-Error", f"凭据名称不能为空")
        elif len(credential_name) > 128:
            messagebox.showinfo("更新凭据-Error", f"凭据名称>128字符")
        elif len(credential_description) > 256:
            messagebox.showinfo("更新凭据-Error", f"凭据描述>256字符")
        elif self.global_info.is_credential_name_existed_except_self(credential_name, self.resource_obj):
            messagebox.showinfo("更新凭据-Error", f"凭据名称已存在")
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
            self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(
                RESOURCE_TYPE_CREDENTIAL, )  # 更新credential信息后，返回“显示credential列表”页面

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
        # ★custom_scheme 终端配色方案
        if self.resource_info_dict["combobox_custom_scheme"].current() == -1:
            host_custom_scheme_index = 0
        else:
            host_custom_scheme_index = self.resource_info_dict["combobox_custom_scheme"].current()
        host_custom_scheme = self.global_info.custome_tag_config_scheme_obj_list[host_custom_scheme_index]
        # 先更新host的credential_oid_list
        self.resource_obj.credential_oid_list = []
        for selected_credential_index in self.resource_info_dict["listbox_credential"].curselection():  # host对象添加凭据列表
            self.resource_obj.add_credential(self.global_info.credential_obj_list[selected_credential_index])
        # 更新-host-对象本身
        if host_name == '':
            messagebox.showinfo("更新主机-Error", f"主机名称不能为空")
        elif len(host_name) > 128:
            messagebox.showinfo("更新主机-Error", f"主机名称>128字符")
        elif len(host_description) > 256:
            messagebox.showinfo("更新主机-Error", f"主机描述>256字符")
        elif self.global_info.is_host_name_existed_except_self(host_name, self.resource_obj):
            messagebox.showinfo("更新主机-Error", f"主机名称已存在")
        else:
            self.resource_obj.update(name=host_name, description=host_description, project_oid=project_oid,
                                     address=host_address,
                                     ssh_port=host_ssh_port, telnet_port=host_telnet_port,
                                     login_protocol=host_login_protocol,
                                     first_auth_method=host_first_auth_method,
                                     custome_tag_config_scheme_oid=host_custom_scheme.oid,
                                     global_info=self.global_info)
            self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_HOST, )  # 更新host信息后，返回“显示host列表”页面

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
            messagebox.showinfo("更新主机组-Error", f"主机组名称不能为空")
        elif len(host_group_name) > 128:
            messagebox.showinfo("更新主机组-Error", f"主机组名称>128字符")
        elif len(host_group_description) > 256:
            messagebox.showinfo("更新主机组-Error", f"主机组描述>256字符")
        elif self.global_info.is_host_group_name_existed_except_self(host_group_name, self.resource_obj):
            messagebox.showinfo("更新主机组-Error", f"主机组名称已存在")
        else:
            self.resource_obj.update(name=host_group_name, description=host_group_description, project_oid=project_oid,
                                     global_info=self.global_info)
            self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(
                RESOURCE_TYPE_HOST_GROUP, )  # 更新host_group信息后，返回“显示host_group列表”页面

    def update_inspection_code_block(self):
        inspection_code_block_name = self.resource_info_dict["sv_name"].get()
        inspection_code_block_description = self.resource_info_dict["sv_description"].get()
        # ★项目  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # 这里不用更新inspection_code_block的 code_list，已在编辑窗口那里完成了
        # 更新-inspection_code_block-对象本身
        if inspection_code_block_name == '':
            messagebox.showinfo("更新巡检代码块-Error", f"巡检代码块名称不能为空")
        elif len(inspection_code_block_name) > 128:
            messagebox.showinfo("更新巡检代码块-Error", f"巡检代码块名称>128字符")
        elif len(inspection_code_block_description) > 256:
            messagebox.showinfo("更新巡检代码块-Error", f"巡检代码块名称>256字符")
        elif self.global_info.is_inspection_code_block_name_existed_except_self(inspection_code_block_name, self.resource_obj):
            messagebox.showinfo("更新巡检代码块-Error", f"巡检代码块名称已存在")
        else:
            self.resource_obj.update(name=inspection_code_block_name, description=inspection_code_block_description,
                                     project_oid=project_oid,
                                     global_info=self.global_info)
            self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(
                RESOURCE_TYPE_INSPECTION_CODE_BLOCK, )  # 更新inspection_code_block信息后，返回

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
        # ★execution_at_time
        execution_at_time_str = self.resource_info_dict["sv_execution_at_time"].get()  # "2024-03-14 09:56:48"
        execution_at_time = time.mktime(time.strptime(execution_at_time_str, "%Y-%m-%d %H:%M:%S"))
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
            messagebox.showinfo("更新巡检模板-Error", f"巡检模板名称不能为空")
        elif len(inspection_template_name) > 128:
            messagebox.showinfo("更新巡检模板-Error", f"巡检模板名称>128字符")
        elif len(inspection_template_description) > 256:
            messagebox.showinfo("更新巡检模板-Error", f"巡检模板描述>256字符")
        elif self.global_info.is_inspection_template_name_existed_except_self(inspection_template_name, self.resource_obj):
            messagebox.showinfo("更新巡检模板-Error", f"巡检模板名称已存在")
        else:
            self.resource_obj.update(name=inspection_template_name, description=inspection_template_description,
                                     project_oid=project_oid, execution_method=inspection_template_execution_method,
                                     execution_at_time=execution_at_time,
                                     update_code_on_launch=inspection_template_update_code_on_launch, forks=inspection_template_forks,
                                     save_output_to_file=inspection_template_save_output_to_file,
                                     output_file_name_style=inspection_template_output_file_name_style,
                                     global_info=self.global_info)
            if self.resource_obj.launch_template_trigger_oid != "":
                launch_template_trigger_obj = self.global_info.get_launch_template_trigger_obj_by_oid(
                    self.resource_obj.launch_template_trigger_oid)
                print("xxxxxxxxxxxxxxyyyyyyyyyyyy update update update")
                launch_template_trigger_obj.update()
            self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_INSPECTION_TEMPLATE, )  # 更新信息后，返回“显示资源列表”页面

    def update_custome_tag_config_scheme(self):
        scheme_name = self.resource_info_dict["sv_name"].get()
        scheme_description = self.resource_info_dict["sv_description"].get()
        # ★项目  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # 更新-scheme-对象本身
        if scheme_name == '':
            messagebox.showinfo("更新scheme-Error", f"scheme名称不能为空")
        elif len(scheme_name) > 128:
            messagebox.showinfo("更新scheme-Error", f"scheme名称>128字符")
        elif len(scheme_description) > 256:
            messagebox.showinfo("更新scheme-Error", f"scheme描述>256字符")
        elif self.global_info.is_custome_tag_config_scheme_name_existed_except_self(scheme_name, self.resource_obj):
            messagebox.showinfo("更新scheme-Error", f"scheme名称已存在")
        else:
            self.resource_obj.update(name=scheme_name, description=scheme_description,
                                     project_oid=project_oid,
                                     global_info=self.global_info)
            # 更新信息后，返回“显示资源列表”页面
            self.resource_info_dict["pop_window"].destroy()
            self.global_info.main_window.window_obj.focus_force()
            self.global_info.main_window.click_menu_settings_scheme_of_menu_bar_init()


class DeleteResourceInFrame:
    """
    在主窗口的查看资源界面，删除选中的资源对象
    """

    def __init__(self, top_frame_widget_dict=None, global_info=None, resource_obj=None,
                 resource_type=RESOURCE_TYPE_PROJECT, call_back_class_obj=None, call_back_class=CALL_BACK_CLASS_LIST_RESOURCE):
        self.top_frame_widget_dict = top_frame_widget_dict
        self.global_info = global_info
        self.resource_obj = resource_obj
        self.resource_type = resource_type
        self.call_back_class_obj = call_back_class_obj
        self.call_back_class = call_back_class

    def show(self):  # 入口函数
        result = messagebox.askyesno("删除资源", f"是否删除'{self.resource_obj.name}'资源对象？")
        # messagebox.askyesno()参数1为弹窗标题，参数2为弹窗内容，有2个按钮（是，否），点击"是"时返回True
        if result:
            # for widget in self.top_frame_widget_dict["frame"].winfo_children():
            #     widget.destroy()
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
            elif self.resource_type == RESOURCE_TYPE_INSPECTION_JOB:
                self.delete_inspection_job_record()
            elif self.resource_type == RESOURCE_TYPE_CUSTOM_SCHEME:
                self.delete_custome_tag_config_scheme()
            else:
                print("<class DeleteResourceInFrame> resource_type is Unknown")
        else:
            print("用户取消了删除操作")
            if self.call_back_class == CALL_BACK_CLASS_LIST_RESOURCE:
                self.top_frame_widget_dict["frame"].focus_force()
            else:
                self.top_frame_widget_dict["pop_window"].focus_force()

    def delete_project(self):
        self.global_info.delete_project_obj(self.resource_obj)
        self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_PROJECT)

    def delete_credential(self):
        self.global_info.delete_credential_obj(self.resource_obj)
        self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_CREDENTIAL)

    def delete_host(self):
        self.global_info.delete_host_obj(self.resource_obj)
        self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_HOST)

    def delete_host_group(self):
        self.global_info.delete_host_group_obj(self.resource_obj)
        self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_HOST_GROUP)

    def delete_inspection_code_block(self):
        self.global_info.delete_inspection_code_block_obj(self.resource_obj)
        self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_INSPECTION_CODE_BLOCK)

    def delete_inspection_template(self):
        self.global_info.delete_inspection_template_obj(self.resource_obj)
        self.global_info.main_window.list_resource_of_nav_frame_r_bottom_page(RESOURCE_TYPE_INSPECTION_TEMPLATE)

    def delete_inspection_job_record(self):
        self.global_info.delete_inspection_job_record_obj(self.resource_obj)
        self.global_info.main_window.list_inspection_job_of_nav_frame_r_page()

    def delete_custome_tag_config_scheme(self):
        self.global_info.delete_custome_tag_config_scheme_obj(self.resource_obj)
        if self.call_back_class == CALL_BACK_CLASS_LIST_RESOURCE:
            self.call_back_class_obj.show()
            self.top_frame_widget_dict["pop_window"].focus_force()
        else:
            self.global_info.main_window.click_menu_settings_scheme_of_menu_bar_init()


class SaveResourceInMainWindow:
    """
    在主窗口的创建资源界面，点击“保存”按钮时，保存资源信息
    """

    def __init__(self, resource_info_dict=None, global_info=None, resource_type=RESOURCE_TYPE_PROJECT):
        self.resource_info_dict = resource_info_dict  # 由<CreateResourceInFrame>对象返回的被创建资源的信息
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
        elif self.resource_type == RESOURCE_TYPE_CUSTOM_SCHEME:
            self.save_custom_tag_config()
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
            self.global_info.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_PROJECT)  # 保存项目信息后，返回项目展示页面

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
            self.global_info.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_CREDENTIAL)  # 保存credential信息后，返回credential展示页面

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
        # ★custom_scheme 终端配色方案
        if self.resource_info_dict["combobox_custom_scheme"].current() == -1:
            host_custom_scheme_index = 0
        else:
            host_custom_scheme_index = self.resource_info_dict["combobox_custom_scheme"].current()
        host_custom_scheme = self.global_info.custome_tag_config_scheme_obj_list[host_custom_scheme_index]
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
                        custome_tag_config_scheme_oid=host_custom_scheme.oid,
                        global_info=self.global_info)
            for selected_credential_index in self.resource_info_dict["listbox_credential"].curselection():  # host对象添加凭据列表
                host.add_credential(self.global_info.credential_obj_list[selected_credential_index])
            host.save()  # 保存资源对象
            self.global_info.host_obj_list.append(host)
            self.global_info.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_HOST)  # 保存host信息后，返回host展示页面

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
            self.global_info.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_HOST_GROUP)  # 保存host_group信息后，返回host_group展示页面

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
            inspection_code_block.code_list = self.resource_info_dict["one_line_code_obj_list"]  # inspection_code_block对象添加code_line列表
            inspection_code_block.save()  # 保存资源对象
            self.global_info.inspection_code_block_obj_list.append(inspection_code_block)
            self.global_info.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_INSPECTION_CODE_BLOCK)  # 保存后，返回展示页面

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
        # ★execution_at_time
        execution_at_time_str = self.resource_info_dict["sv_execution_at_time"].get()  # "2024-03-14 09:56:48"
        if execution_at_time_str == "":
            execution_at_time = 0.0
        else:
            execution_at_time = time.mktime(time.strptime(execution_at_time_str, "%Y-%m-%d %H:%M:%S"))
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
                                                     execution_at_time=execution_at_time,
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
            # 如果巡检模板创建了定时任务，则创建触发器
            if inspection_template.execution_method != EXECUTION_METHOD_NONE:
                cron_trigger1 = LaunchTemplateTrigger(inspection_template_obj=inspection_template,
                                                      global_info=self.global_info)
                inspection_template.launch_template_trigger_oid = cron_trigger1.oid  # 将触发器id添加到巡检模板对象上
                self.global_info.launch_template_trigger_obj_list.append(cron_trigger1)
                # 开始执行监视任务，达到触发条件就执行相应巡检模板（由cofable.LaunchTemplateTrigger.start_crontab_job()方法触发）
                cron_trigger1.start_crond_job()
            else:
                pass
            self.global_info.main_window.nav_frame_r_resource_top_page_display(RESOURCE_TYPE_INSPECTION_TEMPLATE)  # 返回顶级展示页面

    def save_custom_tag_config(self):
        custom_scheme_name = self.resource_info_dict["sv_name"].get()
        custom_scheme_description = self.resource_info_dict["sv_description"].get()
        # ★project_oid  凡是combobox未选择的（值为-1）都要设置为默认值0
        combobox_project_current = self.resource_info_dict["combobox_project"].current()
        if combobox_project_current == -1:
            project_oid = self.global_info.project_obj_list[0].oid
        else:
            project_oid = self.global_info.project_obj_list[combobox_project_current].oid
        # 创建custom_scheme
        if custom_scheme_name == '':
            messagebox.showinfo("创建配色方案-Error", f"配色方案名称不能为空")
        elif len(custom_scheme_name) > 128:
            messagebox.showinfo("创建配色方案-Error", f"配色方案名称>128字符")
        elif len(custom_scheme_description) > 256:
            messagebox.showinfo("创建配色方案-Error", f"配色方案描述>256字符")
        elif self.global_info.is_custome_tag_config_scheme_name_existed(custom_scheme_name):
            messagebox.showinfo("创建配色方案-Error", f"配色方案名称 {custom_scheme_name} 已存在")
        else:
            custom_scheme = CustomTagConfigScheme(name=custom_scheme_name, description=custom_scheme_description,
                                                  project_oid=project_oid,
                                                  global_info=self.global_info)
            # ★custom_scheme对象添加CustomMatchObject对象
            custom_scheme.custom_match_object_list = self.resource_info_dict["custome_match_obj_list"]
            custom_scheme.save()  # 保存资源对象
            self.global_info.custome_tag_config_scheme_obj_list.append(custom_scheme)
            # 返回配色方案设置页面
            self.resource_info_dict["pop_window"].destroy()
            self.global_info.main_window.window_obj.focus_force()
            self.global_info.main_window.click_menu_settings_scheme_of_menu_bar_init()
            return
        self.resource_info_dict["pop_window"].focus_force()


class StartInspectionTemplateInFrame:
    """
    在主窗口的查看资源界面，启动目标巡检模板作业，并添加用于显示巡检模板执行情况的控件
    """

    def __init__(self, global_info=None, inspection_template_obj=None):
        self.nav_frame_r_widget_dict = {}
        self.global_info = global_info
        self.inspection_template_obj = inspection_template_obj
        self.padx = 2
        self.pady = 2
        # self.resource_info_dict = {}  # 用于存储资源对象信息的diction，这个可不要了
        self.current_inspection_job_obj = None  # 为 <LaunchInspectionJob> 类对象
        self.current_row_index = 0

    def start(self):
        existed_inspection_job_obj_list = self.global_info.get_inspection_job_record_obj_by_inspection_template_oid(
            self.inspection_template_obj.oid)
        if len(existed_inspection_job_obj_list) > 0:
            print("StartInspectionTemplateInFrame.start: 已有历史巡检作业！")
            for job in existed_inspection_job_obj_list:
                if job.job_state == INSPECTION_JOB_EXEC_STATE_STARTED:
                    messagebox.showinfo("启动巡检作业", "还有历史作业未完成，无法启动新的巡检作业！")
                    return
        result = messagebox.askyesno("启动巡检作业", "是否立即启动巡检作业？")
        if result:
            print(f"StartInspectionTemplateInFrame.start: 开始启动巡检作业: {self.inspection_template_obj.name}")
            inspect_job_name = "job@" + self.inspection_template_obj.name + "@" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # template_project_name=self.global_info.get_project_by_oid(self.inspection_template_obj.project_oid)
            self.current_inspection_job_obj = LaunchInspectionJob(name=inspect_job_name,
                                                                  project_oid=self.inspection_template_obj.project_oid,
                                                                  inspection_template=self.inspection_template_obj,
                                                                  global_info=self.global_info)
            launch_job_thread = threading.Thread(target=self.current_inspection_job_obj.start_job)
            launch_job_thread.start()  # 线程start后，不要join()，主界面才不会卡住
            # ★进入作业详情页面★
            for widget in self.global_info.main_window.nav_frame_r.winfo_children():
                widget.destroy()
            self.create_frame_with_scrollbar()
            self.show_inspection_job_status()
            self.add_return_button()
            self.update_frame()  # 更新Frame的尺寸，并将滚动条移到最开头
        else:
            print("StartInspectionTemplateInFrame.start: 取消启动巡检作业")

    def create_frame_with_scrollbar(self):
        self.global_info.main_window.nav_frame_r.__setitem__("bg", "pink")
        # 在框架2中添加canvas-frame滚动框
        self.nav_frame_r_widget_dict["scrollbar_normal"] = tkinter.Scrollbar(self.global_info.main_window.nav_frame_r)
        self.nav_frame_r_widget_dict["scrollbar_normal"].pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.nav_frame_r_widget_dict["canvas"] = tkinter.Canvas(self.global_info.main_window.nav_frame_r,
                                                                yscrollcommand=self.nav_frame_r_widget_dict["scrollbar_normal"].set)
        self.nav_frame_r_widget_dict["canvas"].place(x=0, y=0, width=int(self.global_info.main_window.nav_frame_r_width - 25),
                                                     height=self.global_info.main_window.height)
        self.nav_frame_r_widget_dict["scrollbar_normal"].config(command=self.nav_frame_r_widget_dict["canvas"].yview)
        self.nav_frame_r_widget_dict["frame"] = tkinter.Frame(self.nav_frame_r_widget_dict["canvas"])
        self.nav_frame_r_widget_dict["frame"].pack(fill=tkinter.X, expand=tkinter.TRUE)
        self.nav_frame_r_widget_dict["canvas"].create_window((0, 0), window=self.nav_frame_r_widget_dict["frame"], anchor='nw')

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
        self.nav_frame_r_widget_dict["frame"].bind("<MouseWheel>", self.proces_mouse_scroll)
        # 滚动条移到最开头
        self.nav_frame_r_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def add_return_button(self):
        # ★★添加“返回资源列表”按钮★★
        button_return = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="返回资源列表",
                                       command=lambda: self.global_info.main_window.nav_frame_r_resource_top_page_display(
                                           RESOURCE_TYPE_INSPECTION_TEMPLATE))
        button_return.bind("<MouseWheel>", self.proces_mouse_scroll)
        button_return.grid(row=self.current_row_index + 1, column=1, padx=self.padx, pady=self.pady)

    def show_inspection_job_status(self):
        # ★巡检作业详情 这里要把 self.top_frame_widget_dict["frame"] 改为 main_window.nav_frame_r ，并添加滚动条
        label_show_inspection_job_status = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="★★ 巡检作业详情 ★★")
        label_show_inspection_job_status.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_show_inspection_job_status.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        # ★inspection_template-名称
        label_inspection_template_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检模板名称")
        label_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        entry_inspection_template_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], width=42)
        entry_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_template_name.insert(0, self.inspection_template_obj.name)  # 显示初始值，可编辑
        entry_inspection_template_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_job-名称
        label_inspection_job_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="巡检作业名称")
        label_inspection_job_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_job_name.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        entry_inspection_job_name = tkinter.Entry(self.nav_frame_r_widget_dict["frame"], width=42)
        entry_inspection_job_name.bind("<MouseWheel>", self.proces_mouse_scroll)
        entry_inspection_job_name.insert(0, self.current_inspection_job_obj.name)  # 显示初始值，可编辑
        entry_inspection_job_name.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_method
        label_inspection_template_execution_method = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="execution_method")
        label_inspection_template_execution_method.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_execution_method.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        execution_method_name_list = ["无", "定时执行", "周期执行", "After"]
        combobox_execution_method = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                 values=execution_method_name_list,
                                                 state="readonly")
        combobox_execution_method.current(self.inspection_template_obj.execution_method)
        combobox_execution_method.grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-update_code_on_launch
        label_inspection_template_update_code_on_launch = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="运行前更新code")
        label_inspection_template_update_code_on_launch.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_update_code_on_launch.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        update_code_on_launch_name_list = ["No", "Yes"]
        combobox_update_code_on_launch = ttk.Combobox(self.nav_frame_r_widget_dict["frame"],
                                                      values=update_code_on_launch_name_list,
                                                      state="readonly")
        combobox_update_code_on_launch.current(self.inspection_template_obj.update_code_on_launch)
        combobox_update_code_on_launch.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-forks
        label_inspection_template_forks = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="运行线程数")
        label_inspection_template_forks.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_template_forks.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        sv_forks = tkinter.StringVar()
        spinbox_inspection_template_forks = tkinter.Spinbox(self.nav_frame_r_widget_dict["frame"], from_=1, to=256, increment=1,
                                                            textvariable=sv_forks)
        sv_forks.set(self.inspection_template_obj.forks)  # 显示初始值，可编辑
        spinbox_inspection_template_forks.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_job-作业完成情况
        label_inspection_job_status = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text="作业完成情况:")
        label_inspection_job_status.bind("<MouseWheel>", self.proces_mouse_scroll)
        label_inspection_job_status.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        # ★host-列表
        inspection_host_treeview = ttk.Treeview(self.nav_frame_r_widget_dict["frame"], cursor="arrow", height=9,
                                                columns=("index", "host", "status", "rate_or_progress", "time"), show="headings")
        inspection_host_treeview.bind("<MouseWheel>", self.proces_mouse_scroll)
        # 设置每一个列的宽度和对齐的方式
        inspection_host_treeview.column("index", width=60, anchor="w")
        inspection_host_treeview.column("host", width=180, anchor="w")
        inspection_host_treeview.column("status", width=100, anchor="w")
        inspection_host_treeview.column("rate_or_progress", width=60, anchor="w")
        inspection_host_treeview.column("time", width=60, anchor="w")
        # 设置每个列的标题
        inspection_host_treeview.heading("index", text="index", anchor="w")
        inspection_host_treeview.heading("host", text="host", anchor="w")
        inspection_host_treeview.heading("status", text="状态", anchor="w")
        inspection_host_treeview.heading("rate_or_progress", text="进度", anchor="w")
        inspection_host_treeview.heading("time", text="耗时(秒)", anchor="w")  # 单位：秒
        # 插入数据，这里需要定时刷新★★
        index = 0
        status_name_list = ["unknown", "started", "completed", "part_completed", "failed"]
        for host_oid in self.current_inspection_job_obj.unduplicated_host_oid_list:
            host_obj = self.global_info.get_host_by_oid(host_oid)
            host_job_status_obj = self.current_inspection_job_obj.unduplicated_host_job_status_obj_list[index]
            time_usage = host_job_status_obj.end_time - host_job_status_obj.start_time
            if time_usage < 0:
                time_usage_2 = 0
            else:
                time_usage_2 = time_usage
            if host_job_status_obj.sum_of_code_lines <= 0:
                rate_or_progress = 0.0
            else:
                rate_or_progress = host_job_status_obj.current_exec_code_num / host_job_status_obj.sum_of_code_lines
            inspection_host_treeview.insert("", index, values=(
                index, host_obj.name,
                status_name_list[host_job_status_obj.job_status],
                "{:.2%}".format(rate_or_progress),
                time_usage_2))
            index += 1
        inspection_host_treeview.grid(row=6, column=0, columnspan=2, padx=self.padx, pady=self.pady)
        inspection_host_treeview.bind("<<TreeviewSelect>>", lambda event: self.view_inspection_host_item(event, inspection_host_treeview))
        # 只有巡检作业未完成时才刷新主机巡检作业状态，完成（包含失败）都不再去更新主机状态
        if self.current_inspection_job_obj.job_state == INSPECTION_JOB_EXEC_STATE_UNKNOWN:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)
        elif self.current_inspection_job_obj.job_state == INSPECTION_JOB_EXEC_STATE_STARTED:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)
        # ★★更新row_index
        self.current_row_index = 7

    def refresh_host_status(self, inspection_host_treeview):
        inspection_host_treeview.delete(*inspection_host_treeview.get_children())
        # 插入数据，这里需要定时刷新★★
        index = 0
        status_name_list = ["unknown", "started", "completed", "part_completed", "failed"]
        for host_oid in self.current_inspection_job_obj.unduplicated_host_oid_list:
            host_obj = self.global_info.get_host_by_oid(host_oid)
            host_job_status_obj = self.current_inspection_job_obj.unduplicated_host_job_status_obj_list[index]
            time_usage = host_job_status_obj.end_time - host_job_status_obj.start_time
            if time_usage < 0:
                time_usage_2 = 0
            else:
                time_usage_2 = time_usage
            if host_job_status_obj.sum_of_code_lines <= 0:
                rate_or_progress = 0.0
            else:
                rate_or_progress = host_job_status_obj.current_exec_code_num / host_job_status_obj.sum_of_code_lines
            inspection_host_treeview.insert("", index, values=(
                index, host_obj.name,
                status_name_list[host_job_status_obj.job_status],
                "{:.2%}".format(rate_or_progress),
                time_usage_2))
            index += 1
        # 只有巡检作业未完成时才刷新主机巡检作业状态，完成（包含失败）都不再去更新主机状态
        if self.current_inspection_job_obj.job_state == INSPECTION_JOB_EXEC_STATE_UNKNOWN:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)
        elif self.current_inspection_job_obj.job_state == INSPECTION_JOB_EXEC_STATE_STARTED:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)

    def view_inspection_host_item(self, _, inspection_host_treeview):
        item_index = inspection_host_treeview.focus()
        print("view_inspection_host_item: item_index=", item_index)
        if item_index == "":
            return
        host_job_status_obj_index = inspection_host_treeview.item(item_index, "values")[0]
        # 获取选中的命令对象
        host_job_status_obj = self.current_inspection_job_obj.unduplicated_host_job_status_obj_list[int(host_job_status_obj_index)]
        pop_window = tkinter.Toplevel(self.global_info.main_window.window_obj)  # 创建子窗口★
        pop_window.title("主机巡检详情")
        screen_width = self.global_info.main_window.window_obj.winfo_screenwidth()
        screen_height = self.global_info.main_window.window_obj.winfo_screenheight()
        width = self.global_info.main_window.width - 20
        height = self.global_info.main_window.height
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.global_info.main_window.window_obj.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        pop_window.protocol("WM_DELETE_WINDOW", lambda: self.on_closing_view_inspection_host_item(pop_window))
        # 创建滚动条
        scrollbar = tkinter.Scrollbar(pop_window)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        canvas = tkinter.Canvas(pop_window, yscrollcommand=scrollbar.set, bg="#f0f0f0", width=width, height=height)
        canvas.pack()
        scrollbar.config(command=canvas.yview)
        frame = tkinter.Frame(canvas)
        frame.pack()
        canvas.create_window((0, 0), window=frame, anchor='nw')
        canvas.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        frame.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-name
        host_obj = self.global_info.get_host_by_oid(host_job_status_obj.host_oid)
        label_host_name = tkinter.Label(frame, text="主机名称")
        label_host_name.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        label_host_name.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_host_name = tkinter.Entry(frame)
        entry_host_name.insert(0, host_obj.name)  # 显示初始值，不可编辑★
        entry_host_name.grid(row=0, column=1, padx=self.padx, pady=self.pady)
        entry_host_name.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-job_status
        label_host_job_status = tkinter.Label(frame, text="作业状态")
        label_host_job_status.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        label_host_job_status.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        status_name_list = ["unknown", "started", "completed", "part_completed", "failed"]
        combobox_job_status = ttk.Combobox(frame, values=status_name_list, state="readonly")
        combobox_job_status.current(host_job_status_obj.job_status)
        combobox_job_status.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        combobox_job_status.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-find_credential_status
        label_host_find_credential_status = tkinter.Label(frame, text="凭据验证情况")
        label_host_find_credential_status.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        label_host_find_credential_status.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        status_name_list = ["Succeed", "Timeout", "Failed"]
        combobox_find_credential_status = ttk.Combobox(frame, values=status_name_list, state="readonly")
        combobox_find_credential_status.current(host_job_status_obj.find_credential_status)
        combobox_find_credential_status.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        combobox_find_credential_status.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-time_usage
        label_host_time_usage = tkinter.Label(frame, text="执行时长(秒)")
        label_host_time_usage.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        label_host_time_usage.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_host_time_usage = tkinter.Entry(frame)
        if host_job_status_obj.exec_timeout == COF_YES:
            time_usage = "执行超时"
        elif host_job_status_obj.find_credential_status != FIND_CREDENTIAL_STATUS_SUCCEED:
            time_usage = "登录验证失败"
        else:
            time_usage = str(host_job_status_obj.end_time - host_job_status_obj.start_time)
        entry_host_time_usage.insert(0, time_usage)  # 显示初始值，不可编辑★
        entry_host_time_usage.grid(row=3, column=1, padx=self.padx, pady=self.pady)
        entry_host_time_usage.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-sum_of_code_block
        label_sum_of_code_block = tkinter.Label(frame, text="巡检代码段数量")
        label_sum_of_code_block.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        label_sum_of_code_block.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_sum_of_code_block = tkinter.Entry(frame)
        entry_sum_of_code_block.insert(0, host_job_status_obj.sum_of_code_block)  # 显示初始值，不可编辑★
        entry_sum_of_code_block.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        entry_sum_of_code_block.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-sum_of_code_lines
        label_sum_of_code_lines = tkinter.Label(frame, text="巡检命令总行数")
        label_sum_of_code_lines.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        label_sum_of_code_lines.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_sum_of_code_lines = tkinter.Entry(frame)
        entry_sum_of_code_lines.insert(0, host_job_status_obj.sum_of_code_lines)  # 显示初始值，不可编辑★
        entry_sum_of_code_lines.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        entry_sum_of_code_lines.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-rate_or_progress
        label_rate_or_progress = tkinter.Label(frame, text="巡检命令执行进度")
        label_rate_or_progress.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        label_rate_or_progress.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_rate_or_progress = tkinter.Entry(frame)
        if host_job_status_obj.sum_of_code_lines <= 0:
            rate_or_progress = 0.0
        else:
            rate_or_progress = host_job_status_obj.current_exec_code_num / host_job_status_obj.sum_of_code_lines
        entry_rate_or_progress.insert(0, "{:.2%}".format(rate_or_progress))
        entry_rate_or_progress.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        entry_rate_or_progress.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # 显示巡检命令及输出结果
        index = 0
        for inspection_code_block_oid in self.inspection_template_obj.inspection_code_block_oid_list:
            # <SSHOperatorOutput>对象列表，一行命令执行后的所有输出信息都保存在一个<SSHOperatorOutput>对象里
            code_exec_output_obj_list = self.global_info.load_inspection_job_log_for_host(self.current_inspection_job_obj.oid,
                                                                                          host_job_status_obj.host_oid,
                                                                                          inspection_code_block_oid)
            inspection_code_block_obj = self.global_info.get_inspection_code_block_by_oid(inspection_code_block_oid)
            label_inspection_code_block_name = tkinter.Label(frame, text=f"{inspection_code_block_obj.name} 巡检命令详情:")
            label_inspection_code_block_name.grid(row=7 + index * 2, column=0, padx=self.padx, pady=self.pady)
            code_exec_log_text = tkinter.Text(master=frame, height=20)  # 创建多行文本框，用于显示资源信息，需要绑定滚动条
            for output_obj in code_exec_output_obj_list:
                code_exec_log_text.insert(tkinter.END, output_obj.invoke_shell_output_bytes.decode("utf8"))
                for interactive_output in output_obj.interactive_output_bytes_list:
                    code_exec_log_text.insert(tkinter.END, interactive_output.decode("utf8"))
            # 显示info Text文本框
            code_exec_log_text.grid(row=7 + index * 2 + 1, column=0, columnspan=2, padx=self.padx, pady=self.pady)
            index += 1
        # 添加按钮
        save_to_file_button = tkinter.Button(frame, text="保存到文件",
                                             command=lambda: self.save_to_file_inspection_host_item(pop_window, host_job_status_obj))
        save_to_file_button.grid(row=7 + index * 2, column=0, padx=self.padx, pady=self.pady)
        save_to_file_button.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        cancel_button = tkinter.Button(frame, text="返回", command=lambda: self.exit_view_inspection_host_item(pop_window))
        cancel_button.grid(row=7 + index * 2, column=1, padx=self.padx, pady=self.pady)
        cancel_button.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # 更新Frame的尺寸
        frame.update_idletasks()
        canvas.configure(scrollregion=(0, 0, frame.winfo_width(), frame.winfo_height()))
        canvas.yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def save_to_file_inspection_host_item(self, pop_window, host_job_status_obj):
        file_path = filedialog.asksaveasfile(title="保存到文件", filetypes=[("Text files", "*.log"), ("All files", "*.*")],
                                             defaultextension=".log")
        if not file_path:
            print("未选择文件")
        else:
            print(file_path)
            # 保存巡检命令及输出结果
            with open(file_path.name, "a", encoding="utf8") as fileobj:  # 追加，不存在则新建
                for inspection_code_block_oid in self.inspection_template_obj.inspection_code_block_oid_list:
                    # <SSHOperatorOutput>对象列表，一行命令执行后的所有输出信息都保存在一个<SSHOperatorOutput>对象里
                    code_exec_output_obj_list = self.global_info.load_inspection_job_log_for_host(self.current_inspection_job_obj.oid,
                                                                                                  host_job_status_obj.host_oid,
                                                                                                  inspection_code_block_oid)
                    inspection_code_block_obj = self.global_info.get_inspection_code_block_by_oid(inspection_code_block_oid)
                    fileobj.write(f"\n################{inspection_code_block_obj.name} 巡检命令详情 ################↓\n")
                    for output_obj in code_exec_output_obj_list:
                        fileobj.write('\n'.join(output_obj.invoke_shell_output_bytes.decode("utf8").split('\r\n')))
                        for interactive_output in output_obj.interactive_output_bytes_list:
                            fileobj.write('\n'.join(interactive_output.decode("utf8").split('\r\n')))
        pop_window.focus_force()  # 使子窗口获得焦点

    @staticmethod
    def proces_mouse_scroll_on_pop_window(event, canvas):
        if event.delta > 0:
            canvas.yview_scroll(-1, 'units')  # 向上移动
        else:
            canvas.yview_scroll(1, 'units')  # 向下移

    def exit_view_inspection_host_item(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def on_closing_view_inspection_host_item(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点


class ListInspectionJobInFrame:
    """
    在主窗口的查看巡检作业界面，添加用于显示巡检作业信息的控件
    """

    def __init__(self, nav_frame_r_widget_dict=None, global_info=None):
        self.nav_frame_r_widget_dict = nav_frame_r_widget_dict
        self.global_info = global_info
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
        resource_display_frame_title = "★★ 巡检作业列表 ★★"
        inspection_job_record_obj_list = self.global_info.inspection_job_record_obj_list
        # 列出资源
        label_display_resource = tkinter.Label(self.nav_frame_r_widget_dict["frame"],
                                               text=resource_display_frame_title + "    数量: " + str(len(inspection_job_record_obj_list)))
        label_display_resource.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        index = 0
        for obj in inspection_job_record_obj_list:
            label_index = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text=str(index + 1) + " :")
            label_index.bind("<MouseWheel>", self.proces_mouse_scroll)
            label_index.grid(row=index + 1, column=0, padx=self.padx, pady=self.pady)
            label_name = tkinter.Label(self.nav_frame_r_widget_dict["frame"], text=obj.name)
            label_name.bind("<MouseWheel>", self.proces_mouse_scroll)
            label_name.grid(row=index + 1, column=1, padx=self.padx, pady=self.pady)
            # 查看对象信息
            view_obj = ViewInspectionJobInFrame(self.nav_frame_r_widget_dict, self.global_info, obj)
            button_view = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="查看", command=view_obj.show)
            button_view.bind("<MouseWheel>", self.proces_mouse_scroll)
            button_view.grid(row=index + 1, column=2, padx=self.padx, pady=self.pady)
            # 删除对象-->未完善
            delete_obj = DeleteResourceInFrame(self.nav_frame_r_widget_dict, self.global_info, obj,
                                               resource_type=RESOURCE_TYPE_INSPECTION_JOB)
            button_delete = tkinter.Button(self.nav_frame_r_widget_dict["frame"], text="删除", command=delete_obj.show)
            button_delete.bind("<MouseWheel>", self.proces_mouse_scroll)
            button_delete.grid(row=index + 1, column=3, padx=self.padx, pady=self.pady)
            index += 1
        # 信息控件添加完毕
        self.nav_frame_r_widget_dict["frame"].update_idletasks()  # 更新Frame的尺寸
        self.nav_frame_r_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.nav_frame_r_widget_dict["frame"].winfo_width(), self.nav_frame_r_widget_dict["frame"].winfo_height()))
        self.nav_frame_r_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll)
        self.nav_frame_r_widget_dict["frame"].bind("<MouseWheel>", self.proces_mouse_scroll)


class ViewInspectionJobInFrame:
    """
    在主窗口的查看资源界面，显示巡检模板执行作业的详情
    """

    def __init__(self, top_frame_widget_dict=None, global_info=None, inspection_job_record_obj=None):
        self.top_frame_widget_dict = top_frame_widget_dict
        self.global_info = global_info
        self.inspection_job_record_obj = inspection_job_record_obj
        self.padx = 2
        self.pady = 2
        self.current_row_index = 0
        self.inspection_template_obj = self.global_info.get_inspection_template_by_oid(inspection_job_record_obj.inspection_template_oid)

    def show(self):
        # ★进入作业详情页面★
        for widget in self.top_frame_widget_dict["frame"].winfo_children():
            widget.destroy()
        self.show_inspection_job_status()
        self.add_return_button_in_top_frame()
        self.update_top_frame()  # 更新Frame的尺寸，并将滚动条移到最开头

    def proces_mouse_scroll_of_top_frame(self, event):
        if event.delta > 0:
            self.top_frame_widget_dict["canvas"].yview_scroll(-1, 'units')  # 向上移动
        else:
            self.top_frame_widget_dict["canvas"].yview_scroll(1, 'units')  # 向下移动

    def update_top_frame(self):
        # 更新Frame的尺寸
        self.top_frame_widget_dict["frame"].update_idletasks()
        self.top_frame_widget_dict["canvas"].configure(
            scrollregion=(0, 0, self.top_frame_widget_dict["frame"].winfo_width(),
                          self.top_frame_widget_dict["frame"].winfo_height()))
        self.top_frame_widget_dict["canvas"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        self.top_frame_widget_dict["frame"].bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        # 滚动条移到最开头
        self.top_frame_widget_dict["canvas"].yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def add_return_button_in_top_frame(self):
        # ★★添加“返回资源列表”按钮★★
        button_return = tkinter.Button(self.top_frame_widget_dict["frame"], text="返回巡检作业列表",
                                       command=lambda: self.global_info.main_window.list_inspection_job_of_nav_frame_r_page())
        button_return.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        button_return.grid(row=self.current_row_index + 1, column=1, padx=self.padx, pady=self.pady)

    def show_inspection_job_status(self):
        # ★巡检作业详情
        label_show_inspection_job_status = tkinter.Label(self.top_frame_widget_dict["frame"], text="★★ 巡检作业详情 ★★")
        label_show_inspection_job_status.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_show_inspection_job_status.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        label_show_inspection_job_status.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        # ★inspection_template-名称
        label_inspection_template_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检模板名称")
        label_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_name.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        entry_inspection_template_name = tkinter.Entry(self.top_frame_widget_dict["frame"], width=42)
        entry_inspection_template_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_template_name.insert(0, self.inspection_template_obj.name)  # 显示初始值，可编辑
        entry_inspection_template_name.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_job-名称
        label_inspection_job_name = tkinter.Label(self.top_frame_widget_dict["frame"], text="巡检作业名称")
        label_inspection_job_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_job_name.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        entry_inspection_job_name = tkinter.Entry(self.top_frame_widget_dict["frame"], width=42)
        entry_inspection_job_name.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        entry_inspection_job_name.insert(0, self.inspection_job_record_obj.name)  # 显示初始值，可编辑
        entry_inspection_job_name.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-execution_method
        label_inspection_template_execution_method = tkinter.Label(self.top_frame_widget_dict["frame"], text="execution_method")
        label_inspection_template_execution_method.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_execution_method.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        execution_method_name_list = ["无", "定时执行", "周期执行", "After"]
        combobox_execution_method = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                 values=execution_method_name_list,
                                                 state="readonly")
        combobox_execution_method.current(self.inspection_template_obj.execution_method)
        combobox_execution_method.grid(row=3, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-update_code_on_launch
        label_inspection_template_update_code_on_launch = tkinter.Label(self.top_frame_widget_dict["frame"], text="运行前更新code")
        label_inspection_template_update_code_on_launch.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_update_code_on_launch.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        update_code_on_launch_name_list = ["No", "Yes"]
        combobox_update_code_on_launch = ttk.Combobox(self.top_frame_widget_dict["frame"],
                                                      values=update_code_on_launch_name_list,
                                                      state="readonly")
        combobox_update_code_on_launch.current(self.inspection_template_obj.update_code_on_launch)
        combobox_update_code_on_launch.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_template-forks
        label_inspection_template_forks = tkinter.Label(self.top_frame_widget_dict["frame"], text="运行线程数")
        label_inspection_template_forks.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_template_forks.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        sv_forks = tkinter.StringVar()
        spinbox_inspection_template_forks = tkinter.Spinbox(self.top_frame_widget_dict["frame"], from_=1, to=256, increment=1,
                                                            textvariable=sv_forks)
        sv_forks.set(self.inspection_template_obj.forks)  # 显示初始值，可编辑
        spinbox_inspection_template_forks.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        # ★inspection_job-作业完成情况
        label_inspection_job_status = tkinter.Label(self.top_frame_widget_dict["frame"], text="作业完成情况:")
        label_inspection_job_status.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        label_inspection_job_status.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        # ★host-列表
        inspection_host_treeview = ttk.Treeview(self.top_frame_widget_dict["frame"], cursor="arrow", height=9,
                                                columns=("index", "host", "status", "rate_or_progress", "time"), show="headings")
        inspection_host_treeview.bind("<MouseWheel>", self.proces_mouse_scroll_of_top_frame)
        # 设置每一个列的宽度和对齐的方式
        inspection_host_treeview.column("index", width=60, anchor="w")
        inspection_host_treeview.column("host", width=180, anchor="w")
        inspection_host_treeview.column("status", width=100, anchor="w")
        inspection_host_treeview.column("rate_or_progress", width=60, anchor="w")
        inspection_host_treeview.column("time", width=60, anchor="w")
        # 设置每个列的标题
        inspection_host_treeview.heading("index", text="index", anchor="w")
        inspection_host_treeview.heading("host", text="host", anchor="w")
        inspection_host_treeview.heading("status", text="状态", anchor="w")
        inspection_host_treeview.heading("rate_or_progress", text="进度", anchor="w")
        inspection_host_treeview.heading("time", text="耗时(秒)", anchor="w")  # 单位：秒
        # 插入数据，这里需要定时刷新★★
        index = 0
        status_name_list = ["unknown", "started", "completed", "part_completed", "failed"]
        for host_job_status_obj in self.inspection_job_record_obj.unduplicated_host_job_status_obj_list:
            host_obj = self.global_info.get_host_by_oid(host_job_status_obj.host_oid)
            time_usage = host_job_status_obj.end_time - host_job_status_obj.start_time
            if time_usage < 0:
                time_usage_2 = 0
            else:
                time_usage_2 = time_usage
            if host_job_status_obj.sum_of_code_lines <= 0:
                rate_or_progress = 0.0
            else:
                rate_or_progress = host_job_status_obj.current_exec_code_num / host_job_status_obj.sum_of_code_lines
            inspection_host_treeview.insert("", index, values=(
                index, host_obj.name,
                status_name_list[host_job_status_obj.job_status],
                "{:.2%}".format(rate_or_progress),
                time_usage_2))
            index += 1
        inspection_host_treeview.grid(row=6, column=0, columnspan=2, padx=self.padx, pady=self.pady)
        inspection_host_treeview.bind("<<TreeviewSelect>>", lambda event: self.view_inspection_host_item(event, inspection_host_treeview))
        # 只有巡检作业未完成时才刷新主机巡检作业状态，完成（包含失败）都不再去更新主机状态
        if self.inspection_job_record_obj.job_state == INSPECTION_JOB_EXEC_STATE_UNKNOWN:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)
        elif self.inspection_job_record_obj.job_state == INSPECTION_JOB_EXEC_STATE_STARTED:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)
        # ★★更新row_index
        self.current_row_index = 6

    def refresh_host_status(self, inspection_host_treeview):
        inspection_host_treeview.delete(*inspection_host_treeview.get_children())
        # 插入数据，这里需要定时刷新★★
        index = 0
        status_name_list = ["unknown", "started", "completed", "part_completed", "failed"]
        for host_job_status_obj in self.inspection_job_record_obj.unduplicated_host_job_status_obj_list:
            host_obj = self.global_info.get_host_by_oid(host_job_status_obj.host_oid)
            time_usage = host_job_status_obj.end_time - host_job_status_obj.start_time
            if time_usage < 0:
                time_usage_2 = 0
            else:
                time_usage_2 = time_usage
            if host_job_status_obj.sum_of_code_lines <= 0:
                rate_or_progress = 0.0
            else:
                rate_or_progress = host_job_status_obj.current_exec_code_num / host_job_status_obj.sum_of_code_lines
            inspection_host_treeview.insert("", index, values=(
                index, host_obj.name,
                status_name_list[host_job_status_obj.job_status],
                "{:.2%}".format(rate_or_progress),
                time_usage_2))
            index += 1
        # 只有巡检作业未完成时才刷新主机巡检作业状态，完成（包含失败）都不再去更新主机状态
        if self.inspection_job_record_obj.job_state == INSPECTION_JOB_EXEC_STATE_UNKNOWN:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)
        elif self.inspection_job_record_obj.job_state == INSPECTION_JOB_EXEC_STATE_STARTED:
            inspection_host_treeview.after(1000, self.refresh_host_status, inspection_host_treeview)

    def view_inspection_host_item(self, _, inspection_host_treeview):
        item_index = inspection_host_treeview.focus()
        print("view_inspection_host_item: item_index=", item_index)
        if item_index == "":
            return
        host_job_status_obj_index = inspection_host_treeview.item(item_index, "values")[0]
        # 获取选中的命令对象
        host_job_status_obj = self.inspection_job_record_obj.unduplicated_host_job_status_obj_list[int(host_job_status_obj_index)]
        pop_window = tkinter.Toplevel(self.global_info.main_window.window_obj)  # 创建子窗口★
        pop_window.title("主机巡检详情")
        screen_width = self.global_info.main_window.window_obj.winfo_screenwidth()
        screen_height = self.global_info.main_window.window_obj.winfo_screenheight()
        width = self.global_info.main_window.width - 20
        height = self.global_info.main_window.height
        win_pos = f"{width}x{height}+{screen_width // 2 - width // 2}+{screen_height // 2 - height // 2}"
        pop_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
        self.global_info.main_window.window_obj.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        pop_window.protocol("WM_DELETE_WINDOW", lambda: self.on_closing_view_inspection_host_item(pop_window))
        # 创建滚动条
        scrollbar = tkinter.Scrollbar(pop_window)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        canvas = tkinter.Canvas(pop_window, yscrollcommand=scrollbar.set, bg="#f0f0f0", width=width, height=height)
        canvas.pack()
        scrollbar.config(command=canvas.yview)
        frame = tkinter.Frame(canvas)
        frame.pack()
        canvas.create_window((0, 0), window=frame, anchor='nw')
        canvas.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        frame.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-name
        host_obj = self.global_info.get_host_by_oid(host_job_status_obj.host_oid)
        label_host_name = tkinter.Label(frame, text="主机名称")
        label_host_name.grid(row=0, column=0, padx=self.padx, pady=self.pady)
        label_host_name.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_host_name = tkinter.Entry(frame)
        entry_host_name.insert(0, host_obj.name)  # 显示初始值，不可编辑★
        entry_host_name.grid(row=0, column=1, padx=self.padx, pady=self.pady)
        entry_host_name.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-job_status
        label_host_job_status = tkinter.Label(frame, text="作业状态")
        label_host_job_status.grid(row=1, column=0, padx=self.padx, pady=self.pady)
        label_host_job_status.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        status_name_list = ["unknown", "started", "completed", "part_completed", "failed"]
        combobox_job_status = ttk.Combobox(frame, values=status_name_list, state="readonly")
        combobox_job_status.current(host_job_status_obj.job_status)
        combobox_job_status.grid(row=1, column=1, padx=self.padx, pady=self.pady)
        combobox_job_status.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-find_credential_status
        label_host_find_credential_status = tkinter.Label(frame, text="凭据验证情况")
        label_host_find_credential_status.grid(row=2, column=0, padx=self.padx, pady=self.pady)
        label_host_find_credential_status.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        status_name_list = ["Succeed", "Timeout", "Failed"]
        combobox_find_credential_status = ttk.Combobox(frame, values=status_name_list, state="readonly")
        combobox_find_credential_status.current(host_job_status_obj.find_credential_status)
        combobox_find_credential_status.grid(row=2, column=1, padx=self.padx, pady=self.pady)
        combobox_find_credential_status.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-time_usage
        label_host_time_usage = tkinter.Label(frame, text="执行时长(秒)")
        label_host_time_usage.grid(row=3, column=0, padx=self.padx, pady=self.pady)
        label_host_time_usage.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_host_time_usage = tkinter.Entry(frame)
        if host_job_status_obj.exec_timeout == COF_YES:
            time_usage = "执行超时"
        elif host_job_status_obj.find_credential_status != FIND_CREDENTIAL_STATUS_SUCCEED:
            time_usage = "登录验证失败"
        else:
            time_usage = str(host_job_status_obj.end_time - host_job_status_obj.start_time)
        entry_host_time_usage.insert(0, time_usage)  # 显示初始值，不可编辑★
        entry_host_time_usage.grid(row=3, column=1, padx=self.padx, pady=self.pady)
        entry_host_time_usage.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-sum_of_code_block
        label_sum_of_code_block = tkinter.Label(frame, text="巡检代码段数量")
        label_sum_of_code_block.grid(row=4, column=0, padx=self.padx, pady=self.pady)
        label_sum_of_code_block.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_sum_of_code_block = tkinter.Entry(frame)
        entry_sum_of_code_block.insert(0, host_job_status_obj.sum_of_code_block)  # 显示初始值，不可编辑★
        entry_sum_of_code_block.grid(row=4, column=1, padx=self.padx, pady=self.pady)
        entry_sum_of_code_block.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-sum_of_code_lines
        label_sum_of_code_lines = tkinter.Label(frame, text="巡检命令总行数")
        label_sum_of_code_lines.grid(row=5, column=0, padx=self.padx, pady=self.pady)
        label_sum_of_code_lines.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_sum_of_code_lines = tkinter.Entry(frame)
        entry_sum_of_code_lines.insert(0, host_job_status_obj.sum_of_code_lines)  # 显示初始值，不可编辑★
        entry_sum_of_code_lines.grid(row=5, column=1, padx=self.padx, pady=self.pady)
        entry_sum_of_code_lines.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # Host-rate_or_progress
        label_rate_or_progress = tkinter.Label(frame, text="巡检命令执行进度")
        label_rate_or_progress.grid(row=6, column=0, padx=self.padx, pady=self.pady)
        label_rate_or_progress.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        entry_rate_or_progress = tkinter.Entry(frame)
        if host_job_status_obj.sum_of_code_lines <= 0:
            rate_or_progress = 0.0
        else:
            rate_or_progress = host_job_status_obj.current_exec_code_num / host_job_status_obj.sum_of_code_lines
        entry_rate_or_progress.insert(0, "{:.2%}".format(rate_or_progress))
        entry_rate_or_progress.grid(row=6, column=1, padx=self.padx, pady=self.pady)
        entry_rate_or_progress.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # 显示巡检命令及输出结果
        index = 0
        for inspection_code_block_oid in self.inspection_template_obj.inspection_code_block_oid_list:
            # <SSHOperatorOutput>对象列表，一行命令执行后的所有输出信息都保存在一个<SSHOperatorOutput>对象里
            code_exec_output_obj_list = self.global_info.load_inspection_job_log_for_host(self.inspection_job_record_obj.oid,
                                                                                          host_job_status_obj.host_oid,
                                                                                          inspection_code_block_oid)
            inspection_code_block_obj = self.global_info.get_inspection_code_block_by_oid(inspection_code_block_oid)
            label_inspection_code_block_name = tkinter.Label(frame, text=f"{inspection_code_block_obj.name} 巡检命令详情:")
            label_inspection_code_block_name.grid(row=7 + index * 2, column=0, padx=self.padx, pady=self.pady)
            code_exec_log_text = tkinter.Text(master=frame, height=20)  # 创建多行文本框，用于显示资源信息，需要绑定滚动条
            for output_obj in code_exec_output_obj_list:
                code_exec_log_text.insert(tkinter.END, output_obj.invoke_shell_output_bytes.decode("utf8"))
                for interactive_output in output_obj.interactive_output_bytes_list:
                    code_exec_log_text.insert(tkinter.END, interactive_output.decode("utf8"))
            # 显示info Text文本框
            code_exec_log_text.grid(row=7 + index * 2 + 1, column=0, columnspan=2, padx=self.padx, pady=self.pady)
            index += 1
        # 添加按钮
        # ok_button = tkinter.Button(frame, text="xxx")
        save_to_file_button = tkinter.Button(frame, text="保存到文件",
                                             command=lambda: self.save_to_file_inspection_host_item(pop_window, host_job_status_obj))
        save_to_file_button.grid(row=7 + index * 2, column=0, padx=self.padx, pady=self.pady)
        save_to_file_button.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        return_button = tkinter.Button(frame, text="返回", command=lambda: self.exit_view_inspection_host_item(pop_window))
        return_button.grid(row=7 + index * 2, column=1, padx=self.padx, pady=self.pady)
        return_button.bind("<MouseWheel>", lambda event: self.proces_mouse_scroll_on_pop_window(event, canvas))
        # 更新Frame的尺寸
        frame.update_idletasks()
        canvas.configure(scrollregion=(0, 0, frame.winfo_width(), frame.winfo_height()))
        canvas.yview(tkinter.MOVETO, 0.0)  # MOVETO表示移动到，0.0表示最开头

    def save_to_file_inspection_host_item(self, pop_window, host_job_status_obj):
        file_path = filedialog.asksaveasfile(title="保存到文件", filetypes=[("Text files", "*.log"), ("All files", "*.*")],
                                             defaultextension=".log")
        if not file_path:
            print("未选择文件")
        else:
            print(file_path)
            # 保存巡检命令及输出结果
            with open(file_path.name, "a", encoding="utf8") as fileobj:  # 追加，不存在则新建
                for inspection_code_block_oid in self.inspection_template_obj.inspection_code_block_oid_list:
                    # <SSHOperatorOutput>对象列表，一行命令执行后的所有输出信息都保存在一个<SSHOperatorOutput>对象里
                    code_exec_output_obj_list = self.global_info.load_inspection_job_log_for_host(self.inspection_job_record_obj.oid,
                                                                                                  host_job_status_obj.host_oid,
                                                                                                  inspection_code_block_oid)
                    inspection_code_block_obj = self.global_info.get_inspection_code_block_by_oid(inspection_code_block_oid)
                    fileobj.write(f"\n################{inspection_code_block_obj.name} 巡检命令详情 ################↓\n")
                    for output_obj in code_exec_output_obj_list:
                        fileobj.write('\n'.join(output_obj.invoke_shell_output_bytes.decode("utf8").split('\r\n')))
                        for interactive_output in output_obj.interactive_output_bytes_list:
                            fileobj.write('\n'.join(interactive_output.decode("utf8").split('\r\n')))
        pop_window.focus_force()  # 使子窗口获得焦点

    @staticmethod
    def proces_mouse_scroll_on_pop_window(event, canvas):
        if event.delta > 0:
            canvas.yview_scroll(-1, 'units')  # 向上移动
        else:
            canvas.yview_scroll(1, 'units')  # 向下移

    def exit_view_inspection_host_item(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def on_closing_view_inspection_host_item(self, pop_window):
        pop_window.destroy()  # 关闭子窗口
        self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点


class OpenDivisionTerminalVt100:
    """
    这个类主要目的是保存host_obj主机信息的，真正实现功能是由 <DivisionTerminalWindow> 这个类的 add_new_session 函数去实现的
    因为在列出主机列表时，在for循环里的host_obj，如果不用某个类的对象去存储，等主机清单展示完成后，host_obj就总是为最后一个对象
    """

    def __init__(self, global_info=None, host_oid=""):
        self.global_info = global_info
        self.host_oid = host_oid

    def open_session(self):
        self.global_info.open_session_in_division_terminal_window(self.host_oid)


class DivisionTerminalWindow:
    """
    打开终端窗口，里面的主机是单独的会话，会创建一个PopWindow，在popwindow里创建一个用于显示终端输入及输出信息的Frame
    """

    def __init__(self, global_info=None):
        self.global_info = global_info
        self.pop_window = None  # DivisionTerminalWindow 的主窗口，全局只有一个，在 self.create_init_top_level_window()创建
        self.screen_width = self.global_info.main_window.window_obj.winfo_screenwidth()
        self.screen_height = self.global_info.main_window.window_obj.winfo_screenheight()
        self.pop_win_width = self.screen_width - 250
        self.pop_win_height = self.screen_height - 150
        self.terminal_tools_frame_height = 30
        self.font_family = "JetBrains Mono"  # 程序自带内置字体
        self.font_name = ''  # <str>
        self.font_size = 12  # <int>
        self.bg_color = "black"  # <str> color
        self.fg_color = "white"  # <str> color
        self.padx = 2  # <int>
        self.pady = 2  # <int>
        self.terminal_backend_obj = None  # <TerminalVt100>对象
        self.text_pad = 4
        self.host_list_frame = None
        self.terminal_frame = None
        self.terminal_tools_frame = None
        self.host_session_record_obj_list = []  # 元素为<HostSessionRecord>对象
        self.create_init_top_level_window()
        self.scrollbar_width = 25

    def create_init_top_level_window(self):
        # ★★创建DivisionTerminalWindow窗口★★
        self.pop_window = tkinter.Toplevel(self.global_info.main_window.window_obj)
        self.pop_window.title("Cof_Shell")
        win_pos_1 = f"{self.pop_win_width}x{self.pop_win_height}+"
        win_pos_2 = f"{self.screen_width // 2 - int(self.pop_win_width // 2)}+{self.screen_height // 2 - self.pop_win_height // 2}"
        self.pop_window.geometry(win_pos_1 + win_pos_2)  # 设置子窗口大小及位置，居中
        # self.global_info.main_window.window_obj.attributes("-disabled", 1)  # 使主窗口关闭响应，无法点击它
        self.pop_window.focus_force()  # 使子窗口获得焦点
        # 子窗口点击右上角的关闭按钮后，触发此函数
        self.pop_window.protocol("WM_DELETE_WINDOW", self.on_closing_terminal_pop_window)
        # 创建功能按钮Frame
        self.host_list_frame = tkinter.Frame(self.pop_window, bg="white", bd=0,
                                             width=int(self.pop_win_width * 0.2), height=self.pop_win_height)
        self.terminal_frame = tkinter.Frame(self.pop_window, bg="green", bd=0,
                                            width=int(self.pop_win_width * 0.8),
                                            height=self.pop_win_height - self.terminal_tools_frame_height)
        self.terminal_tools_frame = tkinter.Frame(self.pop_window, bg="gray", bd=0,
                                                  width=int(self.pop_win_width * 0.8), height=self.terminal_tools_frame_height)
        # self.host_list_frame.grid_propagate(False)
        # self.terminal_frame.pack_propagate(False)
        self.host_list_frame.place(x=0, y=0, width=int(self.pop_win_width * 0.2), height=self.pop_win_height)
        self.terminal_frame.place(x=int(self.pop_win_width * 0.2), y=0, width=int(self.pop_win_width * 0.8),
                                  height=self.pop_win_height - self.terminal_tools_frame_height)
        self.terminal_tools_frame.place(x=int(self.pop_win_width * 0.2), y=self.pop_win_height - self.terminal_tools_frame_height,
                                        width=int(self.pop_win_width * 0.8),
                                        height=self.terminal_tools_frame_height)
        # 添加其他控件
        label_host_name = tkinter.Label(self.host_list_frame, text="xx", bd=1)
        label_host_name.pack(padx=self.padx)
        button_exit = tkinter.Button(self.host_list_frame, text="退出", command=self.on_closing_terminal_pop_window)
        button_exit.pack(padx=self.padx)

    def on_closing_terminal_pop_window(self):
        print("DivisionTerminalWindow.on_closing_terminal_pop_window: 本子窗口隐藏了，并未删除，可再次显示")
        # self.pop_window.destroy()  # 关闭子窗口
        self.pop_window.withdraw()  # 隐藏窗口
        # self.global_info.main_window.window_obj.attributes("-disabled", 0)  # 使主窗口响应
        self.global_info.main_window.window_obj.focus_force()  # 使主窗口获得焦点

    def add_new_session(self, host_obj):
        print("DivisionTerminalWindow.add_new_session:", host_obj.name)
        host_existed_session_recored_obj = self.get_host_existed_session(host_obj)
        if host_existed_session_recored_obj is not None:  # ★★若目标主机已存在会话
            print(f"DivisionTerminalWindow.add_new_session:{host_obj.name}已存在会话")
            self.pop_window.deiconify()  # 显示终端窗口，使隐藏的窗口再次显示出来
            self.list_host_session_in_host_list_frame(host_existed_session_recored_obj)  # 已存在会话的主机，直接列出主机列表并展示当前主机的会话
            return
        # ★★若目标主机未存在会话，则新建会话
        host_session_record_obj = HostSessionRecord(host_obj=host_obj, global_info=self.global_info,
                                                    shell_terminal_width_pixel=int(self.pop_win_width * 0.8),
                                                    shell_terminal_height_pixel=self.pop_win_height - self.terminal_tools_frame_height)
        # 查找目标主机对应的配色方案，CustomTagConfigScheme对象
        scheme_obj = self.global_info.get_custome_tag_config_scheme_by_oid(host_obj.custome_tag_config_scheme_oid)
        if scheme_obj is not None:
            print("CustomTagConfigSet.set_custom_tag_normal: 找到目标主机的配色方案，下面的self.要改为 scheme_obj. 在配色方案增加以下属性！")
            host_session_record_obj.font_family = self.font_family
            host_session_record_obj.font_name = self.font_name
            host_session_record_obj.font_size = self.font_size
            host_session_record_obj.bg_color = self.bg_color
            host_session_record_obj.fg_color = self.fg_color
        # 创建目标主机的 终端会话前端显示对象 以及 后端远程登录交互对象
        terminal_frontend_obj = TerminalFrontend(terminal_frame=self.terminal_frame, host_obj=host_obj,
                                                 global_info=self.global_info,
                                                 host_session_record_obj=host_session_record_obj,
                                                 shell_terminal_width_pixel=int(self.pop_win_width * 0.8),
                                                 shell_terminal_height_pixel=self.pop_win_height - self.terminal_tools_frame_height,
                                                 user_input_byte_queue=host_session_record_obj.user_input_byte_queue,
                                                 vt100_receive_byte_queue=host_session_record_obj.vt100_receive_byte_queue,
                                                 font_family=host_session_record_obj.font_family,
                                                 font_name=host_session_record_obj.font_name,
                                                 font_size=host_session_record_obj.font_size,
                                                 bg_color=host_session_record_obj.bg_color,
                                                 fg_color=host_session_record_obj.fg_color,
                                                 scrollbar_width=self.scrollbar_width)
        shell_terminal_width = int(self.pop_win_width * 0.8 - self.scrollbar_width) // self.global_info.get_font_mapped_width(
            self.font_size, self.font_family)
        shell_terminal_height = int(
            (self.pop_win_height - self.terminal_tools_frame_height) // self.global_info.get_font_mapped_height(self.font_size,
                                                                                                                self.font_family))
        terminal_backend_obj = TerminalBackend(host_obj=host_obj, global_info=self.global_info,
                                               host_session_record_obj=host_session_record_obj,
                                               user_input_byte_queue=host_session_record_obj.user_input_byte_queue,
                                               vt100_receive_byte_queue=host_session_record_obj.vt100_receive_byte_queue,
                                               shell_terminal_width=shell_terminal_width,
                                               shell_terminal_height=shell_terminal_height,
                                               )
        host_session_record_obj.terminal_frontend_obj = terminal_frontend_obj
        host_session_record_obj.terminal_backend_obj = terminal_backend_obj
        # ★★显示目标主机的终端界面，刚创建会话的主机，必须先show一下，才能 list_host_session_in_host_list_frame
        terminal_frontend_obj.show()
        host_session_record_obj.terminal_backend_run_thread = threading.Thread(target=terminal_backend_obj.run)  # 终端-后端主线程
        host_session_record_obj.terminal_backend_run_thread.start()
        self.terminal_frame.config(bg=host_session_record_obj.bg_color)
        self.host_session_record_obj_list.append(host_session_record_obj)
        # 列出所有主机会话列表 并在终端窗口显示指定的会话Text
        self.list_host_session_in_host_list_frame(host_session_record_obj)
        self.pop_window.deiconify()  # 显示窗口，使隐藏的窗口再次显示出来

    def list_host_session_in_host_list_frame(self, selected_host_session_record_obj=None):
        for widget in self.host_list_frame.winfo_children():
            widget.destroy()
        self.hide_all_host_terminal_frontend_text()
        for host_session_record_obj in self.host_session_record_obj_list:
            if host_session_record_obj == selected_host_session_record_obj:
                bg = "pink"
                host_session_record_obj.terminal_frontend_obj.show_terminal_children_frame()
            else:
                bg = "#c8e1ef"
                # host_session_record_obj.terminal_frontend_obj.hide()
            click_host_session_obj = ClickHostSession(division_terminal_window=self, host_session_record_obj=host_session_record_obj)
            button_host_session = tkinter.Button(self.host_list_frame, text=host_session_record_obj.host_obj.name, bg=bg,
                                                 width=int(self.pop_win_width * 0.2), height=2,
                                                 command=click_host_session_obj.show_clicked_host)
            button_host_session.pack(padx=self.padx)

    def get_host_existed_session(self, host_obj):
        for host_session_record in self.host_session_record_obj_list:
            if host_session_record.host_obj == host_obj:
                return host_session_record
            else:
                continue
        return None

    def hide_all_host_terminal_frontend_text(self):
        for host_session_record_obj in self.host_session_record_obj_list:
            host_session_record_obj.terminal_frontend_obj.hide()


class ClickHostSession:
    def __init__(self, division_terminal_window=None, host_session_record_obj=None):
        self.division_terminal_window = division_terminal_window
        self.host_session_record_obj = host_session_record_obj

    def show_clicked_host(self):
        if self.division_terminal_window is not None:
            # self.division_terminal_window.hide_all_host_terminal_frontend_text()
            self.division_terminal_window.list_host_session_in_host_list_frame(self.host_session_record_obj)


class HostSessionRecord:
    def __init__(self, host_obj=None, global_info=None, shell_terminal_width_pixel=800, shell_terminal_height_pixel=600,
                 font_family='JetBrains Mono', font_name='', font_size=12, bg_color='black', fg_color='white'):
        self.host_obj = host_obj  # <Host>对象
        self.global_info = global_info
        self.user_input_byte_queue = queue.Queue(maxsize=2048)  # 存储的是用户输入的按键（含组合键）对应的ASCII码，元素为bytes(1到N个字节）
        self.vt100_receive_byte_queue = queue.Queue(maxsize=2048)  # 存储的是服务器返回的信息，元素为bytes(1到N个字节）
        self.terminal_frontend_obj = None
        self.terminal_backend_obj = None
        self.shell_terminal_width_pixel = shell_terminal_width_pixel  # <int> self.terminal_text-width
        self.shell_terminal_height_pixel = shell_terminal_height_pixel  # <int> self.terminal_text-height
        self.font_family = font_family  # <str>
        self.font_name = font_name  # <str>
        self.font_size = font_size  # <int>
        self.bg_color = bg_color  # <str> color
        self.fg_color = fg_color  # <str> color
        # 以下线程，在结束主机会话或退出主程序时，需要强制退出线程
        self.parse_received_vt100_data_thread = None  # 终端-前端线程-处理接收到的vt100数据
        self.set_custom_color_tag_config_thread = None  # 终端-前端线程-给接收到的vt100数据进行用户自定义颜色匹配
        self.terminal_backend_run_thread = None  # 终端-后端主线程
        self.recv_vt100_output_data_thread = None  # 终端-后端线程-接收服务器返回的数据
        self.send_user_input_data_thread = None  # 终端-后端线程-发送用户输入数据给服务器

    def reset_ssh_shell_size(self):
        # self.terminal_frontend_obj.show()
        # self.terminal_backend_obj.reset_ssh_shell_tty_size()
        self.terminal_backend_obj.ssh_invoke_shell.resize_pty(
            width=int(self.shell_terminal_width_pixel // self.global_info.get_font_mapped_width(self.font_size, self.font_family)),
            height=int(self.shell_terminal_height_pixel // self.global_info.get_font_mapped_height(self.font_size, self.font_family)))


class TerminalFrontend:
    """
    ★vt100特性总结
    1. 客户端按下 ← 左方向键          发送的是 b'\033OD'    服务端回复的是  b'\x08'    对应操作 vt100_cursor 回退一格
    2. 客户端按下 Backspace 回退键    发送的是 b'\x08'       服务端回复的是  b'\x08\x1b[K\x00\x00\x00\x00\x00\x00'  回退一格并清除到行尾
    3. vt100认为 b'\x08' 只是回退一格，不删除任何字符，b'\x08\x1b[K' 才是回退1格并删除光标到行尾
    4. 在当前行中间位置插入字符时，会覆盖当前vt100_cursor后面的字符，插入的字符有多少个，后面被覆盖的字符就有多少个，剩余字符不动它，除非有其他指令要清除这些剩余字符
    5. 如果vt100_cursor不在当前行末尾，且收到的字符串中含有'\r\n'，则'\r\n'之后的字符串直接从下一行插入，而不是从当前vt100_cursor处插入，
        即当前行字符不动它，当前行不会被拆成2行，这个真实原因如下：
    6. vt100中，\r表示将光标移到当前行行首，然后啥也不做，\n表示插入新行（光标下移一行），所以'\r\n'表示先将光标移回当前行行首，再下移一行，即移动到下一行行首
        有时，只有\r，不一定是要换行，可能只是将光标移到当前行行首，然后后面紧跟一个\033[K 清除从光标处到行尾的所有字符，即清除当前行所有内容
        终端客户端按下回车键，发送的是'\r'字符

    ★概念说明
        vt100_cursor:  vt100光标，vt100发回的对于光标操作的指令（控制序列）
        text_cursor:   tkinter.Text组件的光标（是在Text组件里的闪烁的那个光标-->mark）
    """

    def __init__(self, terminal_frame=None, host_obj=None, global_info=None, host_session_record_obj=None,
                 shell_terminal_width_pixel=1008, shell_terminal_height_pixel=560, scrollbar_width=25,
                 font_size=14, font_family='', font_name='', bg_color="black", fg_color="white",
                 user_input_byte_queue=None, vt100_receive_byte_queue=None):
        self.terminal_frame = terminal_frame  # 在Frame里展示一台主机的终端，在此Frame里创建子frame
        self.terminal_children_frame = None  # 在此Frame里创建相应的Text及Scrollbar
        self.host_obj = host_obj
        self.global_info = global_info
        self.host_session_record_obj = host_session_record_obj
        self.user_input_byte_queue = user_input_byte_queue
        self.vt100_receive_byte_queue = vt100_receive_byte_queue
        self.shell_terminal_width_pixel = shell_terminal_width_pixel  # <int> self.terminal_text-width
        self.shell_terminal_height_pixel = shell_terminal_height_pixel  # <int> self.terminal_text-height
        self.font_family = font_family  # <str>
        self.font_name = font_name  # <str>
        self.font_size = font_size  # <int>
        self.bg_color = bg_color  # <str> color
        self.fg_color = fg_color  # <str> color
        self.scrollbar_normal = None  # 在 show_terminal_on_terminal_frame()里赋值
        self.terminal_normal_text = None  # 在 show_terminal_on_terminal_frame()里赋值，tkinter.Text()，普通模式下显示
        self.terminal_application_text = None  # 在 show_terminal_on_terminal_frame()里赋值，tkinter.Text()，退出应用模式后，就隐藏了
        self.current_terminal_text = CURRENT_TERMINAL_TEXT_NORMAL
        self.padx = 2  # <int>
        self.pady = 2  # <int>
        self.scrollbar_width = scrollbar_width
        self.ctrl_pressed = False  # 仅当Ctrl键按下时，此参数置为True，否则置False
        self.need_reset_ssh_shell_size = False
        self.is_alternate_keypad_mode = False
        self.exit_alternate_keypad_mode = False
        self.text_pad = 4
        # self.vt100_cursor_normal = None  # <str>默认值为 current , self.terminal_normal_text的vt100光标索引
        # self.vt100_cursor_app = None  # <Vt100Cursor> , self.terminal_application_text的vt100光标索引
        self.before_recv_text_index = "1.0"  # <str>
        self.last_set_color_end_line = 1
        self.parse_received_vt100_data_thread = None
        self.set_custom_color_tag_config_thread = None
        self.process_received_pool = ThreadPoolExecutor(max_workers=10000)
        # 整个类的实例只使用以下4个字体对象
        self.terminal_font_normal = font.Font(size=self.font_size, family=self.font_family)
        self.terminal_font_bold = font.Font(size=self.font_size, family=self.font_family,
                                            weight="bold")
        self.terminal_font_italic = font.Font(size=self.font_size, family=self.font_family,
                                              slant="italic")
        self.terminal_font_bold_italic = font.Font(size=self.font_size, family=self.font_family,
                                                   weight="bold", slant="italic")

    def show(self):
        # ★★创建Text文本框及滚动条★★
        self.terminal_children_frame = tkinter.Frame(master=self.terminal_frame, width=self.shell_terminal_width_pixel,
                                                     height=self.shell_terminal_height_pixel, bd=0)
        self.terminal_children_frame.place(x=0, y=0, width=self.shell_terminal_width_pixel,
                                           height=self.shell_terminal_height_pixel)
        self.scrollbar_normal = tkinter.Scrollbar(self.terminal_children_frame)
        self.scrollbar_normal.place(x=self.shell_terminal_width_pixel - self.scrollbar_width, y=0, width=self.scrollbar_width,
                                    height=self.shell_terminal_height_pixel)
        text_width = int((self.shell_terminal_width_pixel - self.scrollbar_width) // self.global_info.get_font_mapped_width(self.font_size,
                                                                                                                            self.font_family))
        text_height = int(self.shell_terminal_height_pixel // self.global_info.get_font_mapped_height(self.font_size, self.font_family))
        # output_block_font_normal = font.Font(size=self.font_size, family=self.font_family)
        self.terminal_normal_text = tkinter.Text(master=self.terminal_children_frame, yscrollcommand=self.scrollbar_normal.set,
                                                 width=text_width, height=text_height, borderwidth=0,
                                                 font=self.terminal_font_normal, bg=self.bg_color, fg=self.fg_color,
                                                 wrap=tkinter.CHAR, spacing1=0, spacing2=0, spacing3=0)
        self.terminal_application_text = tkinter.Text(master=self.terminal_children_frame,
                                                      width=text_width, height=text_height, borderwidth=0,
                                                      font=self.terminal_font_normal, bg=self.bg_color, fg=self.fg_color,
                                                      wrap=tkinter.NONE, spacing1=0, spacing2=0, spacing3=0)
        self.terminal_normal_text.tag_config("default", foreground=self.fg_color, backgroun=self.bg_color,
                                             font=self.terminal_font_normal,
                                             spacing1=0, spacing2=0, spacing3=0)
        self.terminal_application_text.tag_config("default", foreground=self.fg_color, backgroun=self.bg_color,
                                                  font=self.terminal_font_normal,
                                                  spacing1=0, spacing2=0, spacing3=0)
        # self.vt100_cursor_normal = Vt100Cursor(index="1.0", text_obj=self.terminal_application_text)
        # self.vt100_cursor_app = Vt100Cursor(index="1.0", text_obj=self.terminal_application_text)
        # self.terminal_application_text.pack()  # 显示Text控件，self.terminal_application_text暂时不显示
        self.terminal_normal_text.place(x=0, y=0, width=self.shell_terminal_width_pixel - self.scrollbar_width,
                                        height=self.shell_terminal_height_pixel)
        # spacing1为当前行与上一行之间距离，像素
        # spacing2为当前行内如果有折行，则折行之间的距离，像素
        # spacing3为当前行与下一行之间距离，像素
        self.scrollbar_normal.config(command=self.terminal_normal_text.yview)
        self.terminal_normal_text.configure(insertbackground='green')  # Text设置光标颜色
        self.terminal_application_text.configure(insertbackground='green')  # Text设置光标颜色
        # ★★★★★ Text控件绑定鼠标点击事件 ★★★★★
        # 鼠标左键单击事件，先清空选中的文本属性
        self.terminal_normal_text.bind("<Button-1>", lambda event: self.clear_selected_text_color(event, self.terminal_normal_text))
        self.terminal_application_text.bind("<Button-1>",
                                            lambda event: self.clear_selected_text_color(event, self.terminal_application_text))
        # 鼠标左击并移动（拖动）事件，动态设置选中的文本属性
        self.terminal_normal_text.bind("<B1-Motion>", lambda event: self.set_selected_text_color_b1_motion(event,
                                                                                                           self.terminal_normal_text))
        self.terminal_application_text.bind("<B1-Motion>",
                                            lambda event: self.set_selected_text_color_b1_motion(event, self.terminal_application_text))
        # 鼠标左击释放事件，移动text_cursor光标到文本框末尾，不滚动内容
        self.terminal_normal_text.bind("<ButtonRelease-1>",
                                       lambda event: self.set_selected_text_color_b1_release(event, self.terminal_normal_text))
        self.terminal_application_text.bind("<ButtonRelease-1>",
                                            lambda event: self.set_selected_text_color_b1_release(event, self.terminal_application_text))
        # 鼠标右键单击事件，弹出功能菜单
        self.terminal_normal_text.bind("<Button-3>", lambda event: self.pop_menu_on_terminal_text(event, self.terminal_normal_text))
        self.terminal_application_text.bind("<Button-3>",
                                            lambda event: self.pop_menu_on_terminal_text(event, self.terminal_application_text))
        # 下面这个匹配组合键，以单个ascii码的方式发送
        # self.terminal_application_text.bind("<Control-c>", self.front_end_thread_func_ctrl_comb_key)
        # self.terminal_application_text.bind("<Control-z>", self.front_end_thread_func_ctrl_comb_key)
        # 下面这个也能发送Ctrl+A之类的组合键，以单个ascii码的方式发送
        self.terminal_normal_text.bind("<KeyPress>", self.front_end_input_func_printable_char)  # 监听键盘输入的字符
        self.terminal_normal_text.bind("<KeyRelease>", self.front_end_ctrl_key_release)  # 监听Ctrl键释放事件
        self.terminal_normal_text.bind("<MouseWheel>", self.scroll_mouse_wheel_and_press_ctl)  # 监听鼠标滚轮滚动事件
        self.terminal_application_text.bind("<KeyPress>", self.front_end_input_func_printable_char)
        self.terminal_application_text.bind("<KeyRelease>", self.front_end_ctrl_key_release)  # 监听Ctrl键释放事件
        self.terminal_application_text.bind("<MouseWheel>", self.scroll_mouse_wheel_and_press_ctl)
        self.parse_received_vt100_data_thread = threading.Thread(target=self.parse_received_vt100_data)
        self.parse_received_vt100_data_thread.start()
        self.host_session_record_obj.parse_received_vt100_data_thread = self.parse_received_vt100_data_thread
        self.set_custom_color_tag_config_thread = threading.Thread(target=self.set_custom_color_tag_config)
        self.set_custom_color_tag_config_thread.start()
        self.host_session_record_obj.set_custom_color_tag_config_thread = self.set_custom_color_tag_config_thread

    def set_custom_color_tag_config(self):
        while True:
            current_end_line = int(self.terminal_normal_text.index(tkinter.INSERT).split(".")[0])
            print("current_end_line", current_end_line)
            print("self.last_set_color_end_line", self.last_set_color_end_line)
            if current_end_line > self.last_set_color_end_line:
                last_recv_content_str = self.terminal_normal_text.get(str(self.last_set_color_end_line) + ".0", tkinter.INSERT)
                custom_tag_config_obj = CustomTagConfigSet(output_recv_content=last_recv_content_str, terminal_vt100_obj=self,
                                                           start_index=str(self.last_set_color_end_line) + ".0", host_obj=self.host_obj,
                                                           terminal_mode=VT100_TERMINAL_MODE_NORMAL, global_info=self.global_info)
                self.last_set_color_end_line = current_end_line
                custom_tag_config_obj.set_custom_tag()
            time.sleep(0.1)

    @staticmethod
    def clear_selected_text_color(_, terminal_text):
        terminal_text.tag_delete("selected")

    @staticmethod
    def set_selected_text_color_b1_motion(_, terminal_text):
        terminal_text.tag_delete("selected")
        try:
            terminal_text.tag_add("selected", tkinter.SEL_FIRST, tkinter.SEL_LAST)
            terminal_text.tag_config("selected", foreground="white", backgroun="gray")  # 将选中的文本设置属性
        except tkinter.TclError as e:
            print("TerminalVt100.set_selected_text_color: 移动鼠标时未选择任何文字", e)  # 因为移动鼠标的位置没有超过1个字符的距离

    @staticmethod
    def set_selected_text_color_b1_release(_, terminal_text):
        # 选择完文本后，text_cursor光标会停留在tkinter.SEL_LAST
        # self.terminal_text.mark_set("tkinter_END", tkinter.END)  # 使text_cursor光标移动到末尾
        # self.terminal_text.see("tkinter_END")  # 这个会使文本框滚动内容到末尾，选择的内容如果不在最后一页，则被滚动了，当前页面看不到了
        # terminal_text.mark_set(tkinter.INSERT, "end lineend")  # 这个会使闪烁的光标(text_cursor)移到最后一行行末，但页面不会滚动，选中的内容仍在当前界面
        terminal_text.mark_set(tkinter.INSERT, tkinter.END)

    def front_end_input_func_printable_char(self, event):
        """
        处理普通可打印字符，控制键及组合按键
        ★★★ 按键，ascii字符，vt100控制符是3个不同的概念
        按键可以对应一个字符，也可没有相应字符，
        按下shift/ctrl等控制键后再按其他键，可能会产生换档字符（如按下shift加数字键2，产生字符@）
        vt100控制符是由ESC（十六进制为\0x1b，八进制为\033）加其他可打印字符组成，比如:
        按键↑（方向键Up）对应的vt100控制符为 ESC加字母OA，即b'\033OA'
        ★★★
        :param event:
        :return:
        """
        print("普通字符输入如下：")
        print(event.keysym)
        print(event.keycode)
        # 非可打印字符没有event.char，event.char为空，需要发送event.keycode或转为vt100控制序列再发送
        if event.keysym == "BackSpace":
            input_byte = struct.pack('b', event.keycode)
        elif event.keysym == "Delete":
            input_byte = struct.pack('b', event.keycode)
        elif event.keysym == "Down":
            # input_byte = b'\033OB'  # ESC O B    对应  方向键(↓)    VK_DOWN (40)
            input_byte = b'\033[B'  # ESC [ B    对应  方向键(↓)    VK_DOWN (40)
        elif event.keysym == "Up":
            # input_byte = b'\033OA'  # ESC O A    对应  方向键(↑)    VK_UP (38)
            input_byte = b'\033[A'  # ESC [ A    对应  方向键(↑)    VK_UP (38)
        elif event.keysym == "Left":
            # input_byte = b'\033OD'  # ESC O D    对应  方向键(←)    VK_LEFT (37)
            input_byte = b'\033[D'  # ESC [ D    对应  方向键(←)    VK_LEFT (37)
        elif event.keysym == "Right":
            # input_byte = b'\033OC'  # ESC O C    对应  方向键(→)    VK_RIGHT (39)
            input_byte = b'\033[C'  # ESC [ C    对应  方向键(→)    VK_RIGHT (39)
        elif event.keysym == "Control_L":
            self.ctrl_pressed = True
            input_byte = event.char.encode("utf8")
        elif event.keysym == "Control_R":
            self.ctrl_pressed = True
            input_byte = event.char.encode("utf8")
        else:
            # 可打印字符只能发送event.char，因为输入!@#$%^&*()这些换档符号时，需要先按下Shift键再按下相应数字键，
            # Shift键本身不发送（Shift键没有event.char），要发送的是换档后的符号
            # ctrl+字母 这类组合键也是单一字符\0x01到\0x1A
            input_byte = event.char.encode("utf8")
        if len(input_byte) != 0:
            self.user_input_byte_queue.put(input_byte)
            print("往 user_input_byte_queue 里输入数据", input_byte)
        return "break"  # 事件处理脚本返回 "break" 会中断后面的绑定，所以键盘输入不会被插入到文本框

    def scroll_mouse_wheel_and_press_ctl(self, event):
        direction = event.delta
        if self.ctrl_pressed and direction > 0:
            print("按下了Ctrl且滚轮向上滚动", direction)
            if self.font_size < 36:
                self.font_size += 1
                self.reset_text_tag_config_font_size()  # 实时设置Text字体大小
                self.need_reset_ssh_shell_size = True  # self.front_end_ctrl_key_release()
                self.host_session_record_obj.font_size = self.font_size
            return "break"
        elif self.ctrl_pressed and direction < 0:
            print("按下了Ctrl且滚轮向下滚动", direction)
            if self.font_size > 10:
                self.font_size -= 1
                self.reset_text_tag_config_font_size()  # 实时设置Text字体大小
                self.need_reset_ssh_shell_size = True  # self.front_end_ctrl_key_release()
                self.host_session_record_obj.font_size = self.font_size
            return "break"
        else:
            pass

    def front_end_ctrl_key_release(self, event):
        if event.keysym == "Control_L":
            self.ctrl_pressed = False  # Ctrl键释放了，就置False
            if self.need_reset_ssh_shell_size:
                self.host_session_record_obj.reset_ssh_shell_size()
        elif event.keysym == "Control_R":
            self.ctrl_pressed = False  # Ctrl键释放了，就置False
            if self.need_reset_ssh_shell_size:
                self.host_session_record_obj.reset_ssh_shell_size()
                pass
        else:
            pass

    def reset_text_tag_config_font_size(self):
        text_width = int(self.shell_terminal_width_pixel // self.global_info.get_font_mapped_width(self.font_size, self.font_family))
        text_height = int(self.shell_terminal_height_pixel // self.global_info.get_font_mapped_height(self.font_size, self.font_family))
        self.terminal_normal_text.configure(width=text_width, height=text_height, borderwidth=0, spacing1=0, spacing2=0, spacing3=0)
        self.terminal_application_text.configure(width=text_width, height=text_height, borderwidth=0, spacing1=0, spacing2=0, spacing3=0)
        self.terminal_font_normal.config(size=self.font_size)
        self.terminal_font_bold.config(size=self.font_size)
        self.terminal_font_italic.config(size=self.font_size)
        self.terminal_font_bold_italic.config(size=self.font_size)

    def pop_menu_on_terminal_text(self, event, terminal_text):
        print("点击了右键")
        pop_menu_bar = tkinter.Menu(terminal_text, tearoff=0)
        pop_menu_bar.add_command(label="全选", command=lambda: self.selecte_all_text_on_terminal_text(terminal_text))
        pop_menu_bar.add_command(label="复制", command=lambda: self.copy_selected_text_on_terminal_text(terminal_text))
        # pop_menu_bar.add_command(label="复制为RTF", command=lambda: self.copy_selected_text_on_terminal_text_rtf(terminal_text))
        pop_menu_bar.add_command(label="粘贴", command=lambda: self.paste_text_on_terminal_text(terminal_text))
        pop_menu_bar.add_command(label="查找", command=lambda: self.search_text_on_terminal_text(terminal_text))
        pop_menu_bar.add_command(label="保存会话内容", command=lambda: self.save_all_text_on_terminal_text(terminal_text))
        pop_menu_bar.add_command(label="清空会话内容★", command=lambda: self.clear_all_text_on_terminal_text(terminal_text))
        pop_menu_bar.post(event.x_root, event.y_root)

    @staticmethod
    def selecte_all_text_on_terminal_text(terminal_text):
        terminal_text.tag_delete("selected")
        try:
            terminal_text.tag_add(tkinter.SEL, "1.0", tkinter.END + "-1c")
            terminal_text.tag_add("selected", tkinter.SEL_FIRST, tkinter.SEL_LAST)
            terminal_text.tag_config("selected", foreground="white", backgroun="gray")  # 将选中的文本设置属性
        except tkinter.TclError as e:
            print("TerminalVt100.set_selected_text_color: 未选择任何文字", e)
            return

    @staticmethod
    def copy_selected_text_on_terminal_text(terminal_text):
        try:
            selected_text = terminal_text.get(tkinter.SEL_FIRST, tkinter.SEL_LAST)
            pyperclip.copy(selected_text)
        except tkinter.TclError as e:
            print("TerminalVt100.copy_selected_text_on_terminal_text: 未选择任何文字", e)
            return

    def paste_text_on_terminal_text(self, terminal_text):
        pasted_text = pyperclip.paste()
        pasted_text_r = pasted_text.replace("\r\n", "\r").replace("\n", "\r")  # 只发送\r回车，不发送\n换行
        match_pattern = '\\r'
        ret = re.search(match_pattern, pasted_text_r)
        if ret is not None:  # 要粘贴的内容有换行，需要先询问一下人类用户，是否粘贴
            terminal_text.focus_force()
            # result = messagebox.askyesno("粘贴内容确认", f"是否粘贴以下内容:\n{pasted_text}")
            # messagebox.askyesno()参数1为弹窗标题，参数2为弹窗内容，有2个按钮（是，否），点击"是"时返回True
            pop_askyesno_window = tkinter.Toplevel(self.terminal_frame)
            pop_askyesno_window.title("粘贴内容确认")
            screen_width = self.terminal_frame.winfo_screenwidth()
            screen_height = self.terminal_frame.winfo_screenheight()
            pop_win_width = 480
            pop_win_height = 180
            win_pos = f"{pop_win_width}x{pop_win_height}+{screen_width // 2 - pop_win_width // 2}+{screen_height // 2 - pop_win_height // 2}"
            pop_askyesno_window.geometry(win_pos)  # 设置子窗口大小及位置，居中
            pop_askyesno_window.configure(bg="pink")
            # 子窗口点击右上角的关闭按钮后，触发此函数:
            pop_askyesno_window.protocol("WM_DELETE_WINDOW",
                                         lambda: self.pop_pop_askyesno_window_window_on_closing(pop_askyesno_window,
                                                                                                terminal_text))
            # 查找窗口中添加控件
            text = tkinter.Text(pop_askyesno_window)
            button_ok = tkinter.Button(pop_askyesno_window, text="确定",
                                       command=lambda: self.paste_text_on_terminal_text_ok(pop_askyesno_window,
                                                                                           terminal_text, text))
            button_cancel = tkinter.Button(pop_askyesno_window, text="取消",
                                           command=lambda: self.pop_pop_askyesno_window_window_on_closing(pop_askyesno_window,
                                                                                                          terminal_text))
            text.place(x=10, y=0, width=pop_win_width - 20, height=pop_win_height - 35)
            button_ok.place(x=100, y=pop_win_height - 32, width=50, height=30)
            button_cancel.place(x=260, y=pop_win_height - 32, width=50, height=30)
            text.insert(tkinter.END, pasted_text)
            text.focus_force()
        else:
            # 要粘贴的内容无换行，直接粘贴
            self.user_input_byte_queue.put(pasted_text_r.encode("utf8"))
            terminal_text.focus_force()

    @staticmethod
    def pop_pop_askyesno_window_window_on_closing(pop_askyesno_window, terminal_text):
        print("TerminalVt100.pop_pop_askyesno_window_window_on_closing: 用户取消了粘贴")
        pop_askyesno_window.destroy()
        terminal_text.focus_force()

    def paste_text_on_terminal_text_ok(self, pop_askyesno_window, terminal_text, content_text):
        pasted_text_r = content_text.get("1.0", tkinter.END + "-1c").replace("\r\n", "\r").replace("\n", "\r")  # 只发送\r回车，不发送\n换行
        pop_askyesno_window.destroy()
        terminal_text.focus_force()
        self.user_input_byte_queue.put(pasted_text_r.encode("utf8"))

    def search_text_on_terminal_text(self, terminal_text):
        try:
            all_text = terminal_text.get("1.0", tkinter.END)
        except tkinter.TclError as e:
            print("TerminalVt100.search_text_on_terminal_text: 获取Text内容失败", e)
            return
        print(all_text)
        pop_widget_dict = {"pop_search_window": tkinter.Toplevel(self.terminal_frame)}
        pop_widget_dict["pop_search_window"].title("在当前会话内容中查找")
        screen_width = self.terminal_frame.winfo_screenwidth()
        screen_height = self.terminal_frame.winfo_screenheight()
        pop_win_width = 340
        pop_win_height = 30
        win_pos = f"{pop_win_width}x{pop_win_height}+{screen_width // 2 - pop_win_width // 2}+{screen_height // 2 - pop_win_height // 2}"
        pop_widget_dict["pop_search_window"].geometry(win_pos)  # 设置子窗口大小及位置，居中
        pop_widget_dict["pop_search_window"].configure(bg="pink")
        # 子窗口点击右上角的关闭按钮后，触发此函数:
        pop_widget_dict["pop_search_window"].protocol("WM_DELETE_WINDOW",
                                                      lambda: self.pop_search_window_on_closing(pop_widget_dict,
                                                                                                terminal_text))
        # 查找窗口中添加控件
        pop_widget_dict["sv_searh_text"] = tkinter.StringVar()
        entry_search = tkinter.Entry(pop_widget_dict["pop_search_window"],
                                     textvariable=pop_widget_dict["sv_searh_text"], width=30)
        entry_search.pack(side=tkinter.LEFT, padx=5)
        search_button = tkinter.Button(pop_widget_dict["pop_search_window"], text="查找",
                                       command=lambda: self.pop_search_window_click_search_button(pop_widget_dict,
                                                                                                  terminal_text, all_text))
        search_button.pack(side=tkinter.LEFT, padx=5)
        pop_widget_dict["search_up_button"] = tkinter.Button(pop_widget_dict["pop_search_window"], text="↑",
                                                             state=tkinter.DISABLED, width=2,
                                                             command=lambda: self.pop_search_window_click_search_up_button(pop_widget_dict,
                                                                                                                           terminal_text))
        pop_widget_dict["search_up_button"].pack(side=tkinter.LEFT, padx=5)
        pop_widget_dict["search_down_button"] = tkinter.Button(pop_widget_dict["pop_search_window"], text="↓",
                                                               state=tkinter.DISABLED, width=2,
                                                               command=lambda: self.pop_search_window_click_search_down_button(
                                                                   pop_widget_dict,
                                                                   terminal_text))
        pop_widget_dict["search_down_button"].pack(side=tkinter.LEFT, padx=5)
        entry_search.focus_force()

    @staticmethod
    def pop_search_window_on_closing(pop_search_window_widget_dict, terminal_text):
        pop_search_window_widget_dict["pop_search_window"].destroy()
        try:
            terminal_text.tag_delete("matched")
            terminal_text.focus_force()
        except tkinter.TclError as e:
            print("TerminalVt100.highlight_search_text_on_terminal_text: 未选匹配何文字", e)
            terminal_text.focus_force()
            return

    def pop_search_window_click_search_up_button(self, pop_widget_dict, terminal_text):
        len_ret_list = len(pop_widget_dict["ret_list"])
        if len_ret_list > 1:
            print(f"TerminalVt100.pop_search_window_click_search_up_button: 向上查找")
            pop_widget_dict["ret_index"] = (pop_widget_dict["ret_index"] - 1) % len_ret_list
            self.highlight_search_text_on_terminal_text(pop_widget_dict, terminal_text)

    def pop_search_window_click_search_down_button(self, pop_widget_dict, terminal_text):
        len_ret_list = len(pop_widget_dict["ret_list"])
        if len_ret_list > 1:
            print(f"TerminalVt100.pop_search_window_click_search_up_button: 向下查找")
            pop_widget_dict["ret_index"] = (pop_widget_dict["ret_index"] + 1) % len_ret_list
            self.highlight_search_text_on_terminal_text(pop_widget_dict, terminal_text)

    def pop_search_window_click_search_button(self, pop_widget_dict, terminal_text, all_text):
        search_text = pop_widget_dict["sv_searh_text"].get()
        if len(search_text) != 0:
            print(f"TerminalVt100.pop_search_window_click_search_button: 开始查找{search_text}")
            match_pattern = search_text
            ret = re.finditer(match_pattern, all_text, re.I)
            pop_widget_dict["ret_list"] = []
            for ret_item in ret:
                pop_widget_dict["ret_list"].append(ret_item)
            if len(pop_widget_dict["ret_list"]) > 0:
                print(f"TerminalVt100.pop_search_window_click_search_button: 匹配到了{search_text}")
                pop_widget_dict["search_up_button"].configure(state=tkinter.NORMAL)
                pop_widget_dict["search_down_button"].configure(state=tkinter.NORMAL)
                pop_widget_dict["ret_index"] = len(pop_widget_dict["ret_list"]) - 1
                self.highlight_search_text_on_terminal_text(pop_widget_dict, terminal_text)
            else:
                try:
                    terminal_text.tag_delete("matched")
                    terminal_text.see(tkinter.END)
                except tkinter.TclError as e:
                    print("TerminalVt100.pop_search_window_click_search_button: 未选匹配何文字", e)
                    return

    @staticmethod
    def highlight_search_text_on_terminal_text(pop_widget_dict, terminal_text):
        start_index, end_index = pop_widget_dict["ret_list"][pop_widget_dict["ret_index"]].span()
        print(start_index, end_index)
        start_index_count = "+" + str(start_index) + "c"
        end_index_count = "+" + str(end_index) + "c"
        print(terminal_text.get("1.0" + start_index_count, "1.0" + end_index_count))
        try:
            terminal_text.tag_delete("matched")
            terminal_text.tag_add("matched", "1.0" + start_index_count, "1.0" + end_index_count)
            terminal_text.tag_config("matched", foreground="red", backgroun="white")  # 将选中的文本设置属性
            terminal_text.see("1.0" + end_index_count)
        except tkinter.TclError as e:
            print("TerminalVt100.highlight_search_text_on_terminal_text: 未选匹配何文字", e)
            return

    @staticmethod
    def save_all_text_on_terminal_text(terminal_text):
        try:
            all_text = terminal_text.get("1.0", tkinter.END)
        except tkinter.TclError as e:
            print("TerminalVt100.save_all_text_on_terminal_text: 获取Text内容失败", e)
            terminal_text.focus_force()
            return
        file_path = filedialog.asksaveasfile(title="保存到文件", filetypes=[("Text files", "*.log"), ("All files", "*.*")],
                                             defaultextension=".log")
        if not file_path:
            print("未选择文件")
            terminal_text.focus_force()
        else:
            # 保存巡检命令及输出结果到文本文件
            all_text_n = all_text.replace("\r\n", "\n")
            with open(file_path.name, "a", encoding="utf8") as fileobj:  # 追加，不存在文件则新建
                fileobj.write(all_text_n)
            terminal_text.focus_force()

    def clear_all_text_on_terminal_text(self, terminal_text):
        try:
            terminal_text.delete("1.0", tkinter.END)
            # terminal_text.mark_set(tkinter.INSERT,"1.0")  # 可不设置，默认自动回到"1.0"
            self.last_set_color_end_line = 1
        except tkinter.TclError as e:
            print("TerminalVt100.save_all_text_on_terminal_text: 获取Text内容失败", e)
            terminal_text.focus_force()
            return

    def parse_received_vt100_data(self):
        while True:
            try:
                # 从vt100数据队列中取出最先输入的字符 ★非阻塞★ 队列中无内容时弹出 _queue.Empty报错，这里之所以用非阻塞，是因为可能要关闭此线程
                received_bytes = self.vt100_receive_byte_queue.get(block=False)
                print("TerminalFrontend.parse_received_vt100_data: 接收到信息:", received_bytes)
                # ★★★开始解析接收到的vt100输出★★★
                if len(received_bytes) == 0:
                    print("TerminalFrontend.parse_received_vt100_data: received_bytes为空，")
                    continue
                # ★★ enter alternate_keypad_mode 进入应用模式 ★★
                match_pattern = b'\x1b\[\?1h\x1b='
                ret = re.search(match_pattern, received_bytes)
                if ret is not None:
                    print(f"TerminalFrontend.parse_received_vt100_data: 匹配到了★Enter Alternate Keypad Mode★ {match_pattern}")
                    # 首次匹配，首次进入alternate_keypad_mode需要清空此模式下Text控件内容
                    new_received_bytes = received_bytes[ret.end():]
                    self.enter_alternate_keypad_mode_text(new_received_bytes)
                    continue
                if self.is_alternate_keypad_mode:
                    # 如果已经处于应用模式，则本次所有数据直接交给 self.enter_alternate_keypad_mode_text() 处理
                    self.enter_alternate_keypad_mode_text(received_bytes)
                    continue
                # ★★ 不是应用模式，则由以下函数处理（普通模式） ★★
                self.current_terminal_text = CURRENT_TERMINAL_TEXT_NORMAL
                self.process_received_bytes_on_normal_mode(received_bytes)
            except queue.Empty:
                # print("队列中无内容", e)
                time.sleep(0.001)
                continue
            # time.sleep(0.001)

    def parse_received_vt100_data_2(self, received_bytes):
        print("TerminalFrontend.parse_received_vt100_data: 接收到信息:", received_bytes)
        # ★★★开始解析接收到的vt100输出★★★
        if len(received_bytes) == 0:
            print("TerminalFrontend.parse_received_vt100_data: received_bytes为空，")
            return
        # ★★ enter alternate_keypad_mode 进入应用模式 ★★
        match_pattern = b'\x1b\[\?1h\x1b='
        ret = re.search(match_pattern, received_bytes)
        if ret is not None:
            print(f"TerminalFrontend.parse_received_vt100_data: 匹配到了★Enter Alternate Keypad Mode★ {match_pattern}")
            # 首次匹配，首次进入alternate_keypad_mode需要清空此模式下Text控件内容
            new_received_bytes = received_bytes[ret.end():]
            self.enter_alternate_keypad_mode_text(new_received_bytes)
            return
        if self.is_alternate_keypad_mode:
            # 如果已经处于应用模式，则本次所有数据直接交给 self.enter_alternate_keypad_mode_text() 处理
            self.enter_alternate_keypad_mode_text(received_bytes)
            return
        # ★★ 不是应用模式，则由以下函数处理（普通模式） ★★
        self.current_terminal_text = CURRENT_TERMINAL_TEXT_NORMAL
        self.process_received_bytes_on_normal_mode(received_bytes)

    def process_received_bytes_on_normal_mode(self, received_bytes):
        self.before_recv_text_index = self.terminal_normal_text.index(tkinter.INSERT)  # 对每次接收信息处理前的索引
        output_block_ctrl_and_normal_content_list = received_bytes.split(b'\033')
        output_block_ctrl_and_normal_content_list_new = [x for x in output_block_ctrl_and_normal_content_list if x]  # 新列表不含空元素
        if len(output_block_ctrl_and_normal_content_list_new) == 0:
            print(f"TerminalFrontend.process_received_bytes_on_normal_mode: 本次接收到的信息拆分后列表为空")
            self.terminal_normal_text.yview(tkinter.MOVETO, 1.0)  # MOVETO表示移动到，0.0表示最开头，1.0表示最底端
            self.terminal_normal_text.focus_force()
            return
        # with ThreadPoolExecutor(max_workers=10000) as process_received_pool:
        # ★★★★★★ 对一次recv接收后的信息拆分后的每个属性块进行解析，普通输出模式 ★★★★★★
        for block_bytes in output_block_ctrl_and_normal_content_list_new:
            block_str = block_bytes.decode("utf8").replace("\r\n", "\n")
            # ★匹配 [m 或 [0m  -->清除所有属性
            match_pattern = r'^\[0{,1}m'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                # print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: 匹配到了 {match_pattern}")
                # 在self.terminal_text里输出解析后的内容
                new_block_str = block_str[ret.end():]
                # print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: 匹配到了 {match_pattern}")
                if len(new_block_str) > 0:
                    self.normal_mode_print_all_no_replace(new_block_str, 'default')
                continue
            # ★匹配 [01m 到 [08m  [01;34m  [01;34;42m   -->字体风格
            match_pattern = r'^\[([0-9]{1,2};){,3}[0-9]{1,2}m'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                # print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: 匹配到了 {match_pattern}")
                new_block_str = block_str[ret.end():]
                output_block_control_seq = block_str[ret.start() + 1:ret.end() - 1]
                vt100_output_block_obj = Vt100OutputBlockNormal(output_block_control_seq=output_block_control_seq,
                                                                terminal_normal_text=self.terminal_normal_text,
                                                                start_index=self.terminal_normal_text.index(tkinter.INSERT),
                                                                fg_color=self.fg_color,
                                                                bg_color=self.bg_color)
                self.normal_mode_print_all_no_replace(new_block_str, "default")  # 输出内容到Text组件
                vt100_output_block_obj.end_index = self.terminal_normal_text.index(tkinter.INSERT)
                # 处理vt100输出自带的颜色风格
                # set_vt100_tag_thread = threading.Thread(target=vt100_output_block_obj.set_tag_config_font_and_color)
                # set_vt100_tag_thread.start()
                self.process_received_pool.submit(vt100_output_block_obj.set_tag_config_font_and_color)
                continue
            # ★匹配 [C  [8C  -->[数字C  向右移动vt100_cursor（text_cursor光标在本轮for循环结束后，一次recv处理完成后，再显示）
            match_pattern = r'^\[[0-9]*C'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: 匹配到了 {match_pattern}")
                new_block_str = block_str[ret.end():]
                output_block_control_seq = block_str[ret.start() + 1:ret.end() - 1].replace("\0", "")
                vt100_output_block_obj = Vt100OutputBlock(output_block_content=new_block_str,
                                                          output_block_control_seq=output_block_control_seq,
                                                          terminal_vt100_obj=self, terminal_mode=VT100_TERMINAL_MODE_NORMAL)
                vt100_output_block_obj.move_text_index_right()  # 向右移动索引
                # 有时匹配了控制序列后，在其末尾还会有回退符，这里得再匹配一次
                self.normal_mode_print_chars(new_block_str, 'default')
                continue
            # ★匹配 [K  -->从当前vt100_cursor光标位置向右清除到本行行尾所有内容
            match_pattern = r'^\[K'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: 匹配到了 {match_pattern}")
                # if self.vt100_cursor_normal.get_current_right_counts() > 0:
                self.terminal_normal_text.delete(tkinter.INSERT, tkinter.INSERT + " lineend")
                # 有时匹配了控制序列后，在其末尾还会有回退符，这里得再匹配一次
                new_block_str = block_str[ret.end():]
                self.normal_mode_print_chars(new_block_str, "default")
                continue
            # ★匹配 [H  -->vt100_cursor光标回到屏幕开头，复杂清屏，一般vt100光标回到开头后，插入的内容会覆盖原界面的内容，未覆盖到的内容还得继续展示
            match_pattern = r'^\[H'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: 匹配到了 {match_pattern}")
                self.terminal_normal_text.mark_set(tkinter.INSERT, "1.0")
                continue
            # ★匹配 [42D  -->vt100_cursor光标左移42格，一般vt100光标回到当前行开头后，插入的内容会覆盖同行相应位置的内容，
            # 未覆盖的地方不动它，不折行，不产生新行
            match_pattern = r'^\[[0-9]*D'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: 匹配到了 {match_pattern}")
                # 匹配到之后，可能 block_bytes[ret.end():] 是新的内容，要覆盖同一行相应长度的字符
                # need to copy_current_page_move_cursor_to_head_and_cover_content
                new_block_str = block_str[ret.end():]
                output_block_control_seq = block_str[ret.start() + 1:ret.end() - 1]
                print("TerminalFrontend.process_received_bytes_on_normal_mode ★匹配 [数字D -->光标左移n格，复杂清屏",
                      block_str.encode("utf8"))
                vt100_output_block_obj = Vt100OutputBlock(
                    output_block_content=new_block_str,
                    output_block_control_seq=output_block_control_seq,
                    terminal_vt100_obj=self, terminal_mode=VT100_TERMINAL_MODE_NORMAL)
                vt100_output_block_obj.left_move_vt100_cursor_and_or_overwrite_content_in_current_line()
                continue
            # ★匹配 [J  -->清空屏幕，一般和[H一起出现
            match_pattern = r'^\[J'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: ★单独匹配到了 {match_pattern}")
                # to do
                self.terminal_normal_text.insert(tkinter.END, "\n", 'default')  # 暂时在Text组件末尾插入一个空行
                continue
            # ★匹配  b'\x08'  -->回退符，向左移动光标
            match_pattern = b'\x08'
            ret = re.search(match_pattern, block_bytes)
            if ret is not None:
                self.normal_mode_print_chars(block_str, "default")
                continue
            # ★匹配  b'\x07'  -->响铃
            match_pattern = b'\x07'
            ret = re.search(match_pattern, block_bytes)
            if ret is not None:
                self.normal_mode_print_chars(block_str, "default")
                continue
            # ★匹配  b'\x0d'  --> '\r'
            match_pattern = '^\\r'
            new_block_str = block_str.replace("\r\n", "\n")
            ret = re.search(match_pattern, new_block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_normal_mode 普通输出模式: ★单独匹配到了 {match_pattern}")
                self.normal_mode_print_chars(new_block_str, "default")
                continue
            # ★匹配 [6;26H  -->光标移动到指定行列，普通模式暂不处理这个，直接在当前位置插入剩下的普通字符
            match_pattern = r'^\[\d{1,};\d{1,}H'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_normal_mode: 匹配到了 {match_pattern}")
                # 匹配到之后，可能 block_bytes[ret.end():] 没有其他内容了，要覆盖的内容在接下来的几轮循环
                # 如果有内容，那就输出呗
                new_block_str = block_str[ret.end():]
                if len(new_block_str) > 0:
                    self.normal_mode_print_lines(new_block_str, "default")
                continue
            # ★★最后，未匹配到任何属性（非控制序列，非特殊字符如\x08\x07这些）则视为普通文本，使用默认颜色方案
            # print("TerminalFrontend.process_received_bytes_on_normal_mode: 最后未匹配到任何属性，视为普通文本，使用默认颜色方案")
            current_index = self.terminal_normal_text.index(tkinter.INSERT)
            end_index = self.terminal_normal_text.index(tkinter.END + "-1c")
            if current_index == end_index:
                self.normal_mode_print_all_no_replace(block_str, "default")
            else:
                self.normal_mode_print_lines(block_str, "default")
        # ★★★ 对一次recv接收后的信息解析输出完成后，页面滚动到Text末尾 ★★★
        # 一次输出解析完成后，要等待所有的字体颜色设置线程完成再继续，不再单独等待，全部都放一个线程池里
        # 匹配用户自定义高亮词汇，已单独做成一个线程了
        # 字体颜色风格设置完成后，再显示焦点
        self.terminal_normal_text.yview(tkinter.MOVETO, 1.0)  # MOVETO表示移动到，0.0表示最开头，1.0表示最底端
        self.terminal_normal_text.focus_force()

    def enter_alternate_keypad_mode_text(self, received_bytes):
        if not self.is_alternate_keypad_mode:
            # 说明是首次进入此模式
            self.current_terminal_text = CURRENT_TERMINAL_TEXT_APP
            self.terminal_normal_text.place_forget()  # 先隐藏普通模式Text控件，再显示应用模式Text控件
            self.terminal_application_text.place(x=0, y=0, width=self.shell_terminal_width_pixel - self.scrollbar_width,
                                                 height=self.shell_terminal_height_pixel)
            # self.terminal_application_text.yview(tkinter.MOVETO, 1.0)  # MOVETO表示移动到，0.0表示最开头，1.0表示最底端
            self.terminal_application_text.focus_force()
            self.is_alternate_keypad_mode = True
        # ★ match exit alternate_keypad_mode
        match_pattern = b'\x1b\[\?1l\x1b>'
        ret = re.search(match_pattern, received_bytes)
        if ret is not None:
            print(f"TerminalFrontend.enter_alternate_keypad_mode_text: 匹配到了★Exit Alternate Keypad Mode★ {match_pattern}")
            self.is_alternate_keypad_mode = False
            self.exit_alternate_keypad_mode = False
            # 退出应用模式前，先清空其内容
            self.terminal_application_text.delete("1.0", tkinter.END)  # 清空Text内容
            self.terminal_application_text.place_forget()  # 先隐藏应用模式Text控件
            # 再展示普通模式Text控件
            self.current_terminal_text = CURRENT_TERMINAL_TEXT_NORMAL
            self.terminal_normal_text.place(x=0, y=0, width=self.shell_terminal_width_pixel - self.scrollbar_width,
                                            height=self.shell_terminal_height_pixel)
            new_received_bytes = received_bytes[ret.end():]
            if len(new_received_bytes) > 0:
                self.process_received_bytes_on_normal_mode(new_received_bytes)
            else:
                self.terminal_normal_text.yview(tkinter.MOVETO, 1.0)  # MOVETO表示移动到，0.0表示最开头，1.0表示最底端
                self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.END)
                self.terminal_normal_text.focus_force()
            return
        # ★★★解析输出信息★★★
        # 发送命令已有相应线程: self.run_invoke_shell()
        # 接收命令已有相应线程: self.run_invoke_shell_recv() 由它负责接收并将收到的内容初步判断后 传参给本函数的received_bytes
        # 解析received_bytes并输出到self.terminal_application_text 由以下函数处理（应用模式）
        self.process_received_bytes_on_alternate_keypad_mode(received_bytes)

    def process_received_bytes_on_alternate_keypad_mode(self, received_bytes):
        sub_pattern = b'\x1b\[m\x0f'
        received_bytes_sub = re.sub(sub_pattern, b'', received_bytes)
        # print("sub", received_bytes_sub)
        output_block_ctrl_and_normal_content_list = received_bytes_sub.split(b'\033')
        output_block_ctrl_and_normal_content_list_new = [x for x in output_block_ctrl_and_normal_content_list if x]  # 新列表不含空元素
        # ★★★★★★ 对一次recv接收后的信息拆分后的每个属性块进行解析 ★★★★★★
        if len(output_block_ctrl_and_normal_content_list_new) == 0:
            print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode: 本次接收到的信息拆分后列表为空")
            return
        # with ThreadPoolExecutor(max_workers=10000) as process_received_pool:
        for block_bytes in output_block_ctrl_and_normal_content_list_new:
            block_str = block_bytes.decode("utf8").replace("\r\n", "\n")
            # ★匹配 [m 或 [0m  -->清除所有属性
            match_pattern = r'^\[[0]?m'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                # print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode: 匹配到了 {match_pattern}")
                new_block_str = block_str[ret.end():]
                if len(new_block_str) > 0:
                    # self.app_mode_print_chars(new_block_str, "default")
                    self.app_mode_print_all(new_block_str, "default")
                continue
            # ★匹配 [01m 到 [08m  [01;34m  [01;34;42m  [0;1;4;31m  -->这种字体风格
            match_pattern = r'^\[([0-9]{1,2};){,3}[0-9]{1,2}m'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode: 匹配到了 {match_pattern}")
                output_block_control_seq = block_str[ret.start() + 1:ret.end() - 1]
                new_block_str = block_str[ret.end():].replace('\0', '')
                if len(new_block_str) > 0:
                    vt100_output_block_obj = Vt100OutputBlockApp(output_block_control_seq=output_block_control_seq,
                                                                 terminal_application_text=self.terminal_application_text,
                                                                 start_index=self.terminal_application_text.index(tkinter.INSERT),
                                                                 fg_color=self.fg_color,
                                                                 bg_color=self.bg_color)
                    self.app_mode_print_all(new_block_str, vt100_output_block_obj.output_block_tag_config_name)
                    vt100_output_block_obj.end_index = self.terminal_application_text.index(tkinter.INSERT)
                    # 处理vt100输出自带有的颜色风格
                    # set_vt100_tag_thread = threading.Thread(target=vt100_output_block_obj.set_tag_config_font_and_color)
                    # set_vt100_tag_thread.start()
                    self.process_received_pool.submit(vt100_output_block_obj.set_tag_config_font_and_color)
                continue
            # ★匹配 [C  [8C  -->[数字C  向右移动vt100_cursor（Text_cursor在本轮for循环结束后（一次recv处理完成后）再显示光标
            match_pattern = r'^\[[0-9]{,3}C'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode: 匹配到了 {match_pattern}")
                output_block_control_seq = block_str[ret.start() + 1:ret.end() - 1]
                new_block_str = block_str[ret.end():].replace('\0', '')
                if len(new_block_str) > 0:
                    vt100_output_block_obj = Vt100OutputBlock(output_block_content=new_block_str,
                                                              output_block_control_seq=output_block_control_seq,
                                                              terminal_vt100_obj=self, terminal_mode=VT100_TERMINAL_MODE_APP)
                    vt100_output_block_obj.move_text_index_right()  # 向右移动索引
                    # 有时匹配了控制序列后，在其末尾还会有回退符，普通字符等  这里得再处理一次
                    self.app_mode_print_chars(new_block_str, "default")
                    # del vt100_output_block_obj  # 含有循环引用的对象，一旦使用完成就要立即删除，避免内存泄露。这里有必要吗？
                    # gc.collect()
                continue
            # ★匹配 [K  -->从当前光标位置向右清除到本行行尾所有内容 app
            match_pattern = r'^\[K'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode: 匹配到了 {match_pattern}")
                right_content_counts = len(self.terminal_application_text.get(tkinter.INSERT, tkinter.INSERT + " lineend"))
                if right_content_counts > 0:
                    self.terminal_application_text.delete(tkinter.INSERT, tkinter.INSERT + " lineend")
                # 有时匹配了控制序列后，在其末尾还会有回退符，普通字符等  这里得再处理一次
                new_block_str = block_str[ret.end():]
                if len(new_block_str) > 0:
                    self.app_mode_print_lines(new_block_str, "default")
                continue
            # ★匹配 [H  -->光标回到屏幕开头，复杂清屏，一般vt100光标回到开头后，插入的内容会覆盖原界面的内容，未覆盖到的内容还得继续展示
            match_pattern = r'^\[H'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(
                    f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode: 匹配到了 {match_pattern} 光标回到屏幕开头，复杂清屏")
                # 匹配到之后，可能 block_bytes[ret.end():] 没有其他内容了，要覆盖的内容在接下来的几轮循环
                self.terminal_application_text.mark_set(tkinter.INSERT, "1.0")
                # 如果有内容，那就输出呗
                new_block_str = block_str[ret.end():]
                if len(new_block_str) > 0:
                    self.app_mode_print_all(new_block_str, "default")
                continue
            # ★匹配 [6;26H  -->光标移动到指定行列
            match_pattern = r'^\[\d{1,};\d{1,}H'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode: 匹配到了 {match_pattern}")
                # 匹配到之后，可能 block_bytes[ret.end():] 没有其他内容了，要覆盖的内容在接下来的几轮循环
                # 如果有内容，那就输出呗
                line_column_list = block_str[ret.start() + 1:ret.end() - 1].split(";")
                self.terminal_application_text.mark_set(tkinter.INSERT, f"{line_column_list[0]}.{str(int(line_column_list[1]) - 1)}")
                new_block_str = block_str[ret.end():]
                if len(new_block_str) > 0:
                    self.app_mode_print_chars(new_block_str, "default")
                continue
            # ★匹配 [J  -->清空屏幕，一般和[H一起出现
            match_pattern = r'^\[J'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode: ★单独匹配到了 {match_pattern}")
                # self.terminal_application_text.insert(tkinter.END, "\n", 'default')  # 暂时在末尾插入一个空行
                # 有时匹配了控制序列后，在其末尾还会有回退符，普通字符等  这里得再处理一次
                new_block_str = block_str[ret.end():]
                if len(new_block_str) > 0:
                    self.app_mode_print_all(new_block_str, "default")
                continue
            # ★匹配 [42D  -->光标左移42格，一般vt100光标回到当前行开头后，插入的内容会覆盖同行相应位置的内容，未覆盖的地方不动它，不折行，不产生新行
            match_pattern = r'^\[[0-9]*D'
            ret = re.search(match_pattern, block_str)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode app输出模式: 匹配到了 {match_pattern}")
                # 匹配到之后，可能 block_bytes[ret.end():] 是新的内容，要覆盖同一行相应长度的字符
                output_block_control_seq = block_str[ret.start() + 1:ret.end() - 1]
                vt100_output_block_obj = Vt100OutputBlock(
                    output_block_content=block_str[ret.end():],
                    output_block_control_seq=output_block_control_seq,
                    terminal_vt100_obj=self, terminal_mode=VT100_TERMINAL_MODE_APP)
                vt100_output_block_obj.left_move_vt100_cursor_and_or_overwrite_content_in_current_line()
                continue
            # ★匹配  b'\x0d'  --> '\r'
            match_pattern = '^\\r'
            block_str_filter = block_str  # .replace("\r\n", "\n")
            ret = re.search(match_pattern, block_str_filter)
            if ret is not None:
                print(f"TerminalFrontend.process_received_bytes_on_alternate_keypad_mode app输出模式: ★单独匹配到了 {match_pattern}")
                if len(block_str_filter) > 0:
                    self.app_mode_print_chars(block_str_filter, "default")
                continue
            # ★★最后，未匹配到任何属性（非控制序列，非特殊字符如\x08\x07这些）则视为普通文本，使用默认颜色方案
            # print("TerminalVt100.process_received_bytes_on_alternate_keypad_mode: 最后未匹配到任何属性，视为普通文本，使用默认颜色方案")
            # self.app_mode_print_all(block_str, "default")
            current_index = self.terminal_application_text.index(tkinter.INSERT)
            end_index = self.terminal_application_text.index(tkinter.END + "-1c")
            if current_index == end_index:
                self.app_mode_print_all_no_replace(block_str, "default")
            else:
                self.app_mode_print_all(block_str, "default")
        # ★★★★★★ 对一次recv接收后的信息解析输出完成后，页面滚动到Text末尾 ★★★★★★
        self.terminal_application_text.see(tkinter.INSERT)
        self.terminal_application_text.focus_force()

    def app_mode_print_chars(self, content_str, tag_config_name):
        if len(content_str) > 0:
            for char in content_str:
                # print(f"TerminalFrontend.app_mode_print_chars: {char.encode('utf8')}")
                if char == '\0':
                    continue
                elif char == '\r':
                    self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + " linestart")
                elif char == '\n':
                    current_line = int(self.terminal_application_text.index(tkinter.INSERT).split(".")[0])
                    end_line = int(self.terminal_application_text.index(tkinter.END + "-1c").split(".")[0])
                    if current_line < end_line:
                        self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + " linestart")
                        self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + "+1l")
                    else:
                        self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + " lineend")
                        self.terminal_application_text.insert(tkinter.INSERT, "\n", tag_config_name)
                elif char == chr(0x08):
                    self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + "-1c")  # 到行首了还能左移吗？
                elif char == chr(0x0f):
                    continue
                elif char == chr(0x07):  # 响铃
                    continue
                else:
                    try:
                        right_content_counts = len(self.terminal_application_text.get(tkinter.INSERT, tkinter.INSERT + " lineend"))
                        if right_content_counts > 0:
                            self.terminal_application_text.replace(tkinter.INSERT, tkinter.INSERT + "+1c", char, tag_config_name)
                        else:
                            self.terminal_application_text.insert(tkinter.INSERT, char, tag_config_name)
                    except tkinter.TclError as e:
                        print("TerminalFrontend.app_mode_print_chars except:", e)
                        return

    def app_mode_print_lines(self, content_str, tag_config_name):
        """
        content_str  # <str> 要打印的字符串，含有特殊字符，未过滤，未替换，原始的（仅移除了ESC控制序列）
        :param content_str:
        :param tag_config_name:
        :return:
        """
        # content_str_filter = content_str.replace("\r\n", "\n").replace("\0", '').replace(chr(0x0f), "")
        content_str_filter = content_str.replace("\0", '').replace(chr(0x0f), "")
        if len(content_str_filter) > 0:
            line_index = 0
            for line in content_str_filter.split("\n"):
                try:
                    if line_index > 0:
                        current_line = int(self.terminal_application_text.index(tkinter.INSERT).split(".")[0])
                        end_line = int(self.terminal_application_text.index(tkinter.END + "-1c").split(".")[0])
                        if current_line < end_line:
                            self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + " linestart")
                            self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + "+1l")
                        else:
                            self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + " lineend")
                            self.terminal_application_text.insert(tkinter.INSERT, "\n", tag_config_name)
                    line_length = len(line)
                    if line_length > 0:
                        # 每插入n个字符前，先向右删除n个字符（覆盖）
                        right_content_counts = len(self.terminal_application_text.get(tkinter.INSERT, tkinter.INSERT + " lineend"))
                        if right_content_counts >= line_length:
                            self.terminal_application_text.replace(tkinter.INSERT, tkinter.INSERT + f"+{str(line_length)}c", line,
                                                                   tag_config_name)
                        elif right_content_counts > 0:
                            self.terminal_application_text.replace(tkinter.INSERT, tkinter.INSERT + " lineend", line,
                                                                   tag_config_name)
                        else:
                            self.terminal_application_text.insert(tkinter.INSERT, line, tag_config_name)
                    line_index += 1
                except tkinter.TclError as e:
                    print("TerminalFrontend.app_mode_print_lines except:", e)
                    return

    def app_mode_print_all(self, content_str, tag_config_name):
        # content_str_filter = content_str.replace("\r\n", "\n").replace("\0", '').replace(chr(0x0f), "")
        content_str_filter = content_str.replace("\0", '')
        len_content_str_filter = len(content_str_filter)
        if len_content_str_filter > 0:
            try:
                # 每插入n个字符前，先向右删除n个字符（覆盖）
                right_content_counts = len(self.terminal_application_text.get(tkinter.INSERT, tkinter.INSERT + " lineend"))
                if right_content_counts >= len_content_str_filter:
                    self.terminal_application_text.replace(tkinter.INSERT, tkinter.INSERT + f"+{str(len_content_str_filter)}c",
                                                           content_str_filter, tag_config_name)
                elif right_content_counts > 0:
                    self.terminal_application_text.replace(tkinter.INSERT, tkinter.INSERT + " lineend",
                                                           content_str_filter, tag_config_name)
                else:
                    self.terminal_application_text.insert(tkinter.INSERT, content_str_filter, tag_config_name)
            except tkinter.TclError as e:
                print("TerminalFrontend.app_mode_print_lines except:", e)

    def app_mode_print_all_no_replace(self, content_str, tag_config_name):
        # content_str_filter = content_str.replace("\r\n", "\n").replace("\0", '').replace(chr(0x0f), "")
        content_str_filter = content_str.replace("\0", '')
        len_content_str_filter = len(content_str_filter)
        if len_content_str_filter > 0:
            try:
                # 每插入n个字符前，不向右删除n个字符（不覆盖）
                self.terminal_application_text.insert(tkinter.INSERT, content_str_filter, tag_config_name)
            except tkinter.TclError as e:
                print("TerminalFrontend.app_mode_print_all_no_replace except:", e)

    def normal_mode_print_chars(self, content_str, tag_config_name):
        """
        content_str  # <str> 要打印的字符串，含有特殊字符，未过滤，未替换，原始的（仅移除了ESC控制序列）
        :param content_str:
        :param tag_config_name:
        :return:
        """
        # 按每字符输出时，不过滤
        # content_str_filter = content_str.replace("\r\n", "\n").replace("\0", '')
        if len(content_str) > 0:
            for char in content_str:
                # print(f"TerminalFrontend.normal_mode_print_chars: {char.encode('utf8')}")
                if char == '\0':
                    continue
                elif char == '\r':
                    self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + " linestart")
                elif char == '\n':
                    current_line = int(self.terminal_normal_text.index(tkinter.INSERT).split(".")[0])
                    end_line = int(self.terminal_normal_text.index(tkinter.END + "-1c").split(".")[0])
                    if current_line < end_line:
                        self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + " linestart")
                        self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + "+1l")
                    else:
                        self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + " lineend")
                        self.terminal_normal_text.insert(tkinter.INSERT, "\n", tag_config_name)
                elif char == chr(0x08):
                    self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + "-1c")
                elif char == chr(0x0f):
                    continue
                elif char == chr(0x07):  # 响铃
                    continue
                else:
                    try:
                        # print(f"TerminalFrontend.normal_mode_print_chars: 输出普通字符: {char.encode('utf8')}")
                        right_content_counts = len(self.terminal_normal_text.get(tkinter.INSERT, tkinter.INSERT + " lineend"))
                        if right_content_counts > 0:
                            self.terminal_normal_text.replace(tkinter.INSERT, tkinter.INSERT + "+1c", char, tag_config_name)
                        else:
                            self.terminal_normal_text.insert(tkinter.INSERT, char, tag_config_name)
                    except tkinter.TclError as e:
                        print("TerminalFrontend.normal_mode_print_chars except:", e)
                        return

    def normal_mode_print_lines(self, content_str, tag_config_name):
        """
        content_str  # <str> 要打印的字符串，含有特殊字符，未过滤，未替换，原始的（仅移除了ESC控制序列）
        :param content_str:
        :param tag_config_name:
        :return:
        """
        # content_str_filter = content_str.replace("\r\n", "\n").replace("\0", '').replace(chr(0x0f), "")
        content_str_filter = content_str.replace("\0", '').replace(chr(0x0f), "")
        if len(content_str_filter) > 0:
            line_index = 0
            for line in content_str_filter.split("\n"):
                try:
                    # print(f"TerminalFrontend.normal_mode_print_lines: {char.encode('utf8')}")
                    if line_index > 0:
                        current_line = int(self.terminal_normal_text.index(tkinter.INSERT).split(".")[0])
                        end_line = int(self.terminal_normal_text.index(tkinter.END + "-1c").split(".")[0])
                        if current_line < end_line:
                            self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + " linestart")
                            self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + "+1l")
                        else:
                            self.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + " lineend")
                            self.terminal_normal_text.insert(tkinter.INSERT, "\n", tag_config_name)
                    line_length = len(line)
                    if line_length > 0:
                        # 每插入n个字符前，先向右删除n个字符（覆盖）
                        right_content_counts = len(self.terminal_normal_text.get(tkinter.INSERT, tkinter.INSERT + " lineend"))
                        if right_content_counts >= line_length:
                            self.terminal_normal_text.replace(tkinter.INSERT, tkinter.INSERT + f"+{str(line_length)}c", line,
                                                              tag_config_name)
                        elif right_content_counts > 0:
                            self.terminal_normal_text.replace(tkinter.INSERT, tkinter.INSERT + " lineend", line,
                                                              tag_config_name)
                        else:
                            self.terminal_normal_text.insert(tkinter.INSERT, line, tag_config_name)
                    line_index += 1
                except tkinter.TclError as e:
                    print("TerminalFrontend.normal_mode_print_lines except:", e)
                    return

    def normal_mode_print_all(self, content_str, tag_config_name):
        # content_str_filter = content_str.replace("\r\n", "\n").replace("\0", '').replace(chr(0x0f), "")
        content_str_filter = content_str.replace("\0", '')
        len_content_str_filter = len(content_str_filter)
        if len_content_str_filter > 0:
            try:
                # 每插入n个字符前，先向右删除n个字符（覆盖）
                right_content_counts = len(self.terminal_normal_text.get(tkinter.INSERT, tkinter.INSERT + " lineend"))
                if right_content_counts >= len_content_str_filter:
                    self.terminal_normal_text.replace(tkinter.INSERT, tkinter.INSERT + f"+{str(len_content_str_filter)}c",
                                                      content_str_filter, tag_config_name)
                elif right_content_counts > 0:
                    self.terminal_normal_text.replace(tkinter.INSERT, tkinter.INSERT + " lineend",
                                                      content_str_filter, tag_config_name)
                else:
                    self.terminal_normal_text.insert(tkinter.INSERT, content_str_filter, tag_config_name)
            except tkinter.TclError as e:
                print("TerminalFrontend.app_mode_print_lines except:", e)

    def normal_mode_print_all_no_replace(self, content_str, tag_config_name):
        # content_str_filter = content_str.replace("\r\n", "\n").replace("\0", '').replace(chr(0x0f), "")
        content_str_filter = content_str.replace("\0", '')
        len_content_str_filter = len(content_str_filter)
        if len_content_str_filter > 0:
            try:
                # 每插入n个字符前，不向右删除n个字符（不覆盖）
                self.terminal_normal_text.insert(tkinter.INSERT, content_str_filter, tag_config_name)
            except tkinter.TclError as e:
                print("TerminalFrontend.normal_mode_print_all_no_replace except:", e)

    def hide(self):
        self.terminal_children_frame.place_forget()  # 隐藏子Frame
        # self.terminal_application_text.place_forget()  # 隐藏普通模式Text控件
        # self.terminal_application_text.place_forget()  # 隐藏应用模式Text控件

    def show_terminal_children_frame(self):
        self.terminal_children_frame.place(x=0, y=0, width=self.shell_terminal_width_pixel,
                                           height=self.shell_terminal_height_pixel)
        if self.current_terminal_text == CURRENT_TERMINAL_TEXT_NORMAL:
            # self.terminal_application_text.place_forget()  # 隐藏应用模式Text控件，显示普通模式Text控件
            # self.terminal_application_text.place(x=0, y=0, width=self.shell_terminal_width_pixel - self.scrollbar_width,
            #                                 height=self.shell_terminal_height_pixel)
            # self.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT)
            self.terminal_normal_text.focus_force()
        elif self.current_terminal_text == CURRENT_TERMINAL_TEXT_APP:
            # self.terminal_application_text.place_forget()  # 隐藏普通模式Text控件，显示应用模式Text控件
            # self.terminal_application_text.place(x=0, y=0, width=self.shell_terminal_width_pixel - self.scrollbar_width,
            #                                      height=self.shell_terminal_height_pixel)
            self.terminal_application_text.focus_force()
        else:
            pass


class TerminalBackend:
    def __init__(self, terminal_frame=None, host_obj=None, global_info=None, host_session_record_obj=None,
                 user_input_byte_queue=None, vt100_receive_byte_queue=None,
                 shell_terminal_width=80, shell_terminal_height=24):
        self.terminal_frame = terminal_frame
        self.host_obj = host_obj
        self.global_info = global_info
        self.host_session_record_obj = host_session_record_obj
        self.user_input_byte_queue = user_input_byte_queue
        self.vt100_receive_byte_queue = vt100_receive_byte_queue
        self.is_closed = False
        self.ssh_client = None
        self.ssh_invoke_shell = None
        self.shell_terminal_width = shell_terminal_width
        self.shell_terminal_height = shell_terminal_height
        self.send_user_input_data_thread = None
        self.recv_vt100_output_data_thread = None

    def run(self):
        cred = self.find_credential_by_login_protocol()
        if cred is None:
            self.vt100_receive_byte_queue.put("TerminalBackend.run 未找到可用凭据，退出TerminalBackend.run()函数".encode("utf8"))
            return
        self.create_invoke_shell(cred)
        self.recv_vt100_output_data_thread = threading.Thread(target=self.recv_vt100_output_data)
        self.recv_vt100_output_data_thread.start()
        self.send_user_input_data_thread = threading.Thread(target=self.send_user_input_data)
        self.send_user_input_data_thread.start()
        self.host_session_record_obj.recv_vt100_output_data_thread = self.recv_vt100_output_data_thread
        self.host_session_record_obj.send_user_input_data_thread = self.send_user_input_data_thread

    def find_credential_by_login_protocol(self):
        if self.host_obj.login_protocol == LOGIN_PROTOCOL_SSH:
            try:
                cred = self.find_ssh_credential(self.host_obj)
            except Exception as e:
                print("TerminalBackend.find_credential_by_login_protocol: 查找可用的凭据错误，", e)
                return None
            if cred is None:
                print("TerminalBackend.find_credential_by_login_protocol: Credential is None, Could not find correct credential")
                return None
            return cred
        elif self.host_obj.login_protocol == LOGIN_PROTOCOL_TELNET:
            print("TerminalBackend.find_credential_by_login_protocol: 使用telnet协议远程目标主机")
            return None
        else:
            return None

    def find_ssh_credential(self, host):
        """
        查找可用的ssh凭据，会登录一次目标主机（因为一台主机可以绑定多个同类型的凭据，依次尝试，直到找到可用的凭据）
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

    def create_invoke_shell(self, cred):
        # ★★创建ssh连接★★
        self.ssh_client = paramiko.client.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接host_key不在known_hosts文件里的主机
        try:
            if cred.cred_type == CRED_TYPE_SSH_PASS:
                print("TerminalBackend.create_invoke_shell : 使用ssh_password密码登录")
                self.ssh_client.connect(hostname=self.host_obj.address, port=self.host_obj.ssh_port, username=cred.username,
                                        password=cred.password, timeout=LOGIN_AUTH_TIMEOUT)
            elif cred.cred_type == CRED_TYPE_SSH_KEY:
                prikey_string_io = io.StringIO(cred.private_key)
                pri_key = paramiko.RSAKey.from_private_key(prikey_string_io)
                print("TerminalBackend.create_invoke_shell : 使用ssh_priKey密钥登录")
                self.ssh_client.connect(hostname=self.host_obj.address, port=self.host_obj.ssh_port, username=cred.username,
                                        pkey=pri_key, timeout=LOGIN_AUTH_TIMEOUT)
            else:
                pass
        except paramiko.AuthenticationException as e:
            print(f"TerminalBackend.create_invoke_shell : Authentication Error: {e}")
            raise e
        # ★★连接后，创建invoke_shell交互式shell★★
        self.ssh_invoke_shell = self.ssh_client.invoke_shell(width=self.shell_terminal_width, height=self.shell_terminal_height)

    def send_user_input_data(self):
        # ★★下面只负责发送用户输入的所有字符，包括从剪贴板复制的★★
        cmd_index = 0
        while True:
            if self.is_closed:
                self.ssh_invoke_shell.close()
                self.ssh_client.close()
                print("TerminalBackend.send_user_input_data: 本函数结束了 在 while True: 处")
                return
            try:
                # 从用户输入字符队列中取出最先输入的字符 ★非阻塞★ 队列中无内容时弹出 _queue.Empty报错，这里之所以用非阻塞，是因为要判断self.is_closed
                user_cmd = self.user_input_byte_queue.get(block=False)
                self.ssh_invoke_shell.send(user_cmd)  # 发送命令，一行命令（不过滤命令前后的空白字符，发送的是utf8编码后的bytes）
            except queue.Empty as err:
                # print("user_input_byte_queue队列中无内容", err)
                time.sleep(0.01)
                continue
            cmd_index += 1
            time.sleep(0.01)

    def recv_vt100_output_data(self):
        # 不停地从ssh_shell接收输出信息，直到关闭了终端窗口
        with ThreadPoolExecutor(max_workers=1) as pool:
            index = 0
            while True:
                if self.is_closed:
                    print("TerminalBackend.recv_vt100_output_data: 关闭了终端窗口，退出了本函数")
                    return
                try:
                    received_bytes = self.ssh_invoke_shell.recv(65535)
                    # print("TerminalBackend.recv_vt100_output_data: 接收到信息:", received_bytes)
                    print("TerminalBackend.recv_vt100_output_data: 接收到信息:", index)
                    # ★★★开始解析接收到的vt100输出★★★
                    if len(received_bytes) == 0:
                        print("TerminalBackend.recv_vt100_output_data: received_bytes为空，关闭 ssh_client, 退出了本函数")
                        self.is_closed = True
                        return
                    # 有数据就往列队里扔
                    # self.vt100_receive_byte_queue.put(received_bytes)
                    # self.host_session_record_obj.terminal_frontend_obj.parse_received_vt100_data_2(received_bytes)  # 有数据就直接调前端界面处理
                    pool.submit(self.host_session_record_obj.terminal_frontend_obj.parse_received_vt100_data_2, received_bytes)
                    index += 1
                except Exception as e:
                    print(e)
                    self.is_closed = True
                    return


class Vt100OutputBlockNormal:
    def __init__(self, output_block_control_seq="", terminal_normal_text=None, start_index="1.0", end_index="1.0",
                 fg_color="white", bg_color="black"):
        self.output_block_control_seq = output_block_control_seq
        self.terminal_normal_text = terminal_normal_text
        self.start_index = start_index  # 这段需要修饰的字符串所处位置 起始坐标
        self.end_index = end_index  # 这段需要修饰的字符串所处位置 结束坐标
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.output_block_tag_config_name = ""

    def set_tag_config_font_and_color(self):
        self.output_block_tag_config_name = uuid.uuid4().__str__()  # <str>
        self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}",
                                             foreground=self.fg_color,
                                             backgroun=self.bg_color,
                                             spacing1=0, spacing2=0, spacing3=0)
        ctrl_seq_seg_list = self.output_block_control_seq.split(";")
        # already_set_font = False
        for ctrl_seq_seg in ctrl_seq_seg_list:
            # 前景色设置
            if int(ctrl_seq_seg) == 30:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", foreground="black")
            elif int(ctrl_seq_seg) == 31:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", foreground="red")
            elif int(ctrl_seq_seg) == 32:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", foreground="green")
            elif int(ctrl_seq_seg) == 33:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", foreground="yellow")
            elif int(ctrl_seq_seg) == 34:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", foreground="blue")
            elif int(ctrl_seq_seg) == 35:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", foreground="purple")
            elif int(ctrl_seq_seg) == 36:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", foreground="cyan")
            elif int(ctrl_seq_seg) == 37:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", foreground="white")
            # 背景色设置
            elif int(ctrl_seq_seg) == 40:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="black")
            elif int(ctrl_seq_seg) == 41:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="red")
            elif int(ctrl_seq_seg) == 42:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="green")
            elif int(ctrl_seq_seg) == 43:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="yellow")
            elif int(ctrl_seq_seg) == 44:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="blue")
            elif int(ctrl_seq_seg) == 45:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="purple")
            elif int(ctrl_seq_seg) == 46:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="cyan")
            elif int(ctrl_seq_seg) == 47:
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="white")
            # 字体设置
            elif int(ctrl_seq_seg) == 1:  # 粗体
                # output_block_font_bold = font.Font(weight='bold', size=self.terminal_vt100_obj.font_size,
                #                                   family=self.terminal_vt100_obj.font_family)
                # self.terminal_vt100_obj.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}",
                #                                                         font=self.terminal_vt100_obj.terminal_font_bold)
                # already_set_font = True
                continue
            elif int(ctrl_seq_seg) == 4:  # 下划线
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}", underline=1)
            elif int(ctrl_seq_seg) == 7:  # 反显，一般就单独出现不会有其他颜色设置了
                self.terminal_normal_text.tag_config(f"{self.output_block_tag_config_name}",
                                                     foreground=self.bg_color,
                                                     backgroun=self.fg_color)
            else:
                continue
        # if not already_set_font:
        #     # output_block_font_normal = font.Font(size=self.terminal_vt100_obj.font_size, family=self.terminal_vt100_obj.font_family)
        #     self.terminal_vt100_obj.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}",
        #                                                             font=self.terminal_vt100_obj.terminal_font_normal)
        # print("Vt100OutputBlock.set_tag_config_font_and_color_normal start_index ",
        #       self.terminal_vt100_obj.terminal_application_text.index(self.start_index))
        # print("Vt100OutputBlock.set_tag_config_font_and_color_normal end_index ",
        #       self.terminal_vt100_obj.terminal_application_text.index(self.end_index))
        self.terminal_normal_text.tag_add(f"{self.output_block_tag_config_name}",
                                          self.start_index,
                                          self.end_index)


class Vt100OutputBlockApp:
    def __init__(self, output_block_control_seq="", terminal_application_text=None, start_index="1.0", end_index="1.0",
                 fg_color="white", bg_color="black"):
        self.output_block_control_seq = output_block_control_seq
        self.terminal_application_text = terminal_application_text
        self.start_index = start_index  # 这段需要修饰的字符串所处位置 起始坐标
        self.end_index = end_index  # 这段需要修饰的字符串所处位置 结束坐标
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.output_block_tag_config_name = ""

    def set_tag_config_font_and_color(self):
        self.output_block_tag_config_name = uuid.uuid4().__str__()  # <str>
        self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}",
                                                  foreground=self.fg_color,
                                                  backgroun=self.bg_color,
                                                  spacing1=0, spacing2=0, spacing3=0)
        ctrl_seq_seg_list = self.output_block_control_seq.split(";")
        # already_set_font = False
        for ctrl_seq_seg in ctrl_seq_seg_list:
            # 前景色设置
            if int(ctrl_seq_seg) == 30:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", foreground="black")
            elif int(ctrl_seq_seg) == 31:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", foreground="red")
            elif int(ctrl_seq_seg) == 32:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", foreground="green")
            elif int(ctrl_seq_seg) == 33:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", foreground="yellow")
            elif int(ctrl_seq_seg) == 34:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", foreground="blue")
            elif int(ctrl_seq_seg) == 35:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", foreground="purple")
            elif int(ctrl_seq_seg) == 36:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", foreground="cyan")
            elif int(ctrl_seq_seg) == 37:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", foreground="white")
            # 背景色设置
            elif int(ctrl_seq_seg) == 40:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="black")
            elif int(ctrl_seq_seg) == 41:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="red")
            elif int(ctrl_seq_seg) == 42:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="green")
            elif int(ctrl_seq_seg) == 43:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="yellow")
            elif int(ctrl_seq_seg) == 44:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="blue")
            elif int(ctrl_seq_seg) == 45:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="purple")
            elif int(ctrl_seq_seg) == 46:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="cyan")
            elif int(ctrl_seq_seg) == 47:
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", backgroun="white")
            # 字体设置
            elif int(ctrl_seq_seg) == 1:  # 粗体
                # output_block_font_bold = font.Font(weight='bold', size=self.terminal_vt100_obj.font_size,
                #                                   family=self.terminal_vt100_obj.font_family)
                # self.terminal_vt100_obj.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}",
                #                                                         font=self.terminal_vt100_obj.terminal_font_bold)
                # already_set_font = True
                continue
            elif int(ctrl_seq_seg) == 4:  # 下划线
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}", underline=1)
            elif int(ctrl_seq_seg) == 7:  # 反显，一般就单独出现不会有其他颜色设置了
                self.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}",
                                                          foreground=self.bg_color,
                                                          backgroun=self.fg_color)
            else:
                continue
        # if not already_set_font:
        #     # output_block_font_normal = font.Font(size=self.terminal_vt100_obj.font_size, family=self.terminal_vt100_obj.font_family)
        #     self.terminal_vt100_obj.terminal_application_text.tag_config(f"{self.output_block_tag_config_name}",
        #                                                             font=self.terminal_vt100_obj.terminal_font_normal)
        # print("Vt100OutputBlock.set_tag_config_font_and_color_normal start_index ",
        #       self.terminal_vt100_obj.terminal_application_text.index(self.start_index))
        # print("Vt100OutputBlock.set_tag_config_font_and_color_normal end_index ",
        #       self.terminal_vt100_obj.terminal_application_text.index(self.end_index))
        self.terminal_application_text.tag_add(f"{self.output_block_tag_config_name}",
                                               self.start_index,
                                               self.end_index)


class Vt100OutputBlock:
    def __init__(self, output_block_content='', output_block_tag_config_name='', output_block_control_seq='',
                 terminal_vt100_obj=None, terminal_mode=VT100_TERMINAL_MODE_NORMAL, start_index="1.0", end_index="1.0"):
        self.output_block_content = output_block_content  # <str> 匹配上的普通字符（不含最前面的控制序列字符）
        self.output_block_tag_config_name = output_block_tag_config_name  # <str> 根据匹配上的控制序列，而设置的文字颜色风格名称
        self.output_block_control_seq = output_block_control_seq  # <str> 匹配上的控制序列字符，如 [0m
        # [01;34m 这种在output_block_control_seq里不带最前面的[及最后面的m，只剩下 02  01;34  01;34;42 这种
        self.terminal_vt100_obj = terminal_vt100_obj
        self.terminal_mode = terminal_mode
        self.start_index = start_index  # 这段需要修饰的字符串所处位置 起始坐标
        self.end_index = end_index  # 这段需要修饰的字符串所处位置 结束坐标

    def move_text_index_right(self):
        if self.output_block_control_seq == "":
            count = "1"
        else:
            count = self.output_block_control_seq
        if self.terminal_mode == VT100_TERMINAL_MODE_NORMAL:
            self.terminal_vt100_obj.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + f"+{count}c")
        else:
            self.terminal_vt100_obj.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + f"+{count}c")

    def left_move_vt100_cursor_and_or_overwrite_content_in_current_line(self):
        if self.terminal_mode == VT100_TERMINAL_MODE_NORMAL:
            self.left_move_vt100_cursor_and_or_overwrite_content_in_current_line_normal()
        else:
            self.left_move_vt100_cursor_and_or_overwrite_content_in_current_line_app()

    def left_move_vt100_cursor_and_or_overwrite_content_in_current_line_normal(self):
        if self.output_block_control_seq.isdigit():
            left_move_count = int(self.output_block_control_seq)
            current_column = int(self.terminal_vt100_obj.terminal_normal_text.index(tkinter.INSERT).split(".")[1])
            if current_column >= left_move_count:
                self.terminal_vt100_obj.terminal_normal_text.mark_set(tkinter.INSERT,
                                                                      tkinter.INSERT + f"-{self.output_block_control_seq}c")
            elif current_column > 0:
                self.terminal_vt100_obj.terminal_normal_text.mark_set(tkinter.INSERT, tkinter.INSERT + " linestart")
            else:
                pass
        # 移动vt100_cursor后，右边剩下的字符
        self.terminal_vt100_obj.normal_mode_print_chars(self.output_block_content, "default")

    def left_move_vt100_cursor_and_or_overwrite_content_in_current_line_app(self):
        if self.output_block_control_seq.isdigit():
            left_move_count = int(self.output_block_control_seq)
            current_column = int(self.terminal_vt100_obj.terminal_application_text.index(tkinter.INSERT).split(".")[1])
            if current_column >= left_move_count:
                self.terminal_vt100_obj.terminal_application_text.mark_set(tkinter.INSERT,
                                                                           tkinter.INSERT + f"-{self.output_block_control_seq}c")
            elif current_column > 0:
                self.terminal_vt100_obj.terminal_application_text.mark_set(tkinter.INSERT, tkinter.INSERT + " linestart")
            else:
                pass
        # 移动vt100_cursor后，右边剩下的字符
        self.terminal_vt100_obj.app_mode_print_chars(self.output_block_content, "default")


class CustomMatchObject:
    def __init__(self, match_pattern_lines='', foreground='', backgroun='', underline=False, underlinefg='', overstrike=False,
                 overstrikefg='', bold=False, italic=False):
        self.match_pattern_lines = match_pattern_lines  # <str>
        if foreground == "":
            self.foreground = "white"
        else:
            self.foreground = foreground  # <color_str> 如 '#ff00bb'
        if backgroun == "":
            self.backgroun = "black"
        else:
            self.backgroun = backgroun  # <color_str> 如 '#ff00bb'
        self.underline = underline  # <bool> <int> 置True时表示使用下划线，置False时表示不使用下划线
        if underlinefg == "":
            self.underlinefg = "yellow"
        else:
            self.underlinefg = underlinefg  # <color_str> 如 '#ff00bb' 仅设置下划线时有效
        self.overstrike = overstrike  # <bool> <int> 置True时表示使用删除线，置False时表示不使用删除线
        if overstrikefg == "":
            self.overstrikefg = "pink"
        else:
            self.overstrikefg = overstrikefg  # <color_str> 如 '#ff00bb' 仅设置删除线时有效
        self.bold = bold  # <bool>字体是否加粗，默认不加粗
        self.italic = italic  # <bool>字体是否使用斜体，默认不使用斜体

    def update(self, match_pattern_lines=None, foreground=None, backgroun=None, underline=None, underlinefg=None, overstrike=None,
               overstrikefg=None, bold=None, italic=None):
        if match_pattern_lines is not None:
            self.match_pattern_lines = match_pattern_lines  # <str>
        if foreground is not None:
            self.foreground = foreground  # <color_str> 如 '#ff00bb'
        if backgroun is not None:
            self.backgroun = backgroun  # <color_str> 如 '#ff00bb'
        if underline is not None:
            self.underline = underline  # <bool> <int> 置True时表示使用下划线，置False时表示不使用下划线
        if underlinefg is not None:
            self.underlinefg = underlinefg  # <color_str> 如 '#ff00bb' 仅设置下划线时有效
        if overstrike is not None:
            self.overstrike = overstrike  # <bool> <int> 置True时表示使用删除线，置False时表示不使用删除线
        if overstrikefg is not None:
            self.overstrikefg = "pink"
        if bold is not None:
            self.bold = bold  # <bool>字体是否加粗，默认不加粗
        if italic is not None:
            self.italic = italic  # <bool>字体是否使用斜体，默认不使用斜体


class CustomTagConfigScheme:
    def __init__(self, name='default', description='default', project_oid='default', create_timestamp=None,
                 last_modify_timestamp=0, oid=None, global_info=None):
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
        self.custom_match_object_list = []  # 元素为<CustomMatchObject>对象
        self.global_info = global_info

    def save(self):
        sqlite_conn = sqlite3.connect(self.global_info.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host'的表★
        sql = f'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_custome_tag_config_scheme"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql_list = ["create table tb_custome_tag_config_scheme  ( oid varchar(36) NOT NULL PRIMARY KEY,",
                        "name varchar(128),",
                        "description varchar(256),",
                        "project_oid varchar(36),",
                        "create_timestamp double,",
                        "last_modify_timestamp double )"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"select * from tb_custome_tag_config_scheme where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # ★★ 若未查询到有此项记录，则创建此项记录 ★★
            sql_list = [f"insert into tb_custome_tag_config_scheme (oid,",
                        "name,",
                        "description,",
                        "project_oid,",
                        "create_timestamp,",
                        "last_modify_timestamp ) values",
                        f"('{self.oid}',",
                        f"'{self.name}',",
                        f"'{self.description}',",
                        f"'{self.project_oid}',",
                        f"{self.create_timestamp},",
                        f"{self.last_modify_timestamp} )"]
            sqlite_cursor.execute(" ".join(sql_list))
        else:  # ★★ 若查询到有此项记录，则更新此项记录 ★★
            sql_list = [f"update tb_custome_tag_config_scheme set ",
                        f"name='{self.name}',",
                        f"description='{self.description}',",
                        f"project_oid='{self.project_oid}',",
                        f"create_timestamp={self.create_timestamp},",
                        f"last_modify_timestamp={self.last_modify_timestamp}",
                        "where",
                        f"oid='{self.oid}'"]
            print(" ".join(sql_list))
            sqlite_cursor.execute(" ".join(sql_list))
        # ★查询是否有名为'tb_custome_tag_config_scheme_include_match_object'的表★
        sql = 'SELECT * FROM sqlite_master WHERE \
                        "type"="table" and "tbl_name"="tb_custome_tag_config_scheme_include_match_object"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql_list = ["create table tb_custome_tag_config_scheme_include_match_object  (scheme_oid varchar(36),",
                        "match_pattern_lines varchar(4096),",
                        "foreground varchar(32),",
                        "backgroun varchar(32),",
                        "underline int,",
                        "underlinefg varchar(32),",
                        "overstrike int,",
                        "overstrikefg varchar(32),",
                        "bold int,",
                        "italic int",
                        " );"]
            sqlite_cursor.execute(" ".join(sql_list))
        # 开始插入数据
        sql = f"delete from tb_custome_tag_config_scheme_include_match_object where scheme_oid='{self.oid}'"
        sqlite_cursor.execute(sql)  # ★先清空所有的match_obj，再重新插入（既可用于新建，又可用于更新）
        for match_obj_oid in self.custom_match_object_list:
            match_pattern_lines_b64 = base64.b64encode(match_obj_oid.match_pattern_lines.encode("utf8")).decode("utf8")
            sql_list = [f"insert into tb_custome_tag_config_scheme_include_match_object (scheme_oid,",
                        "match_pattern_lines,",
                        "foreground,",
                        "backgroun,",
                        "underline,",
                        "underlinefg,",
                        "overstrike,",
                        "overstrikefg,",
                        "bold,",
                        "italic ) values ",
                        f"('{self.oid}',",
                        f"'{match_pattern_lines_b64}',",
                        f"'{match_obj_oid.foreground}',",
                        f"'{match_obj_oid.backgroun}',",
                        f"{match_obj_oid.underline},",
                        f"'{match_obj_oid.underlinefg}',",
                        f"{match_obj_oid.overstrike},",
                        f"'{match_obj_oid.overstrikefg}',",
                        f"{match_obj_oid.bold},",
                        f"{match_obj_oid.italic}",
                        " )"]
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


class CustomTagConfigSet:
    def __init__(self, output_recv_content='', terminal_vt100_obj=None, start_index="", host_obj=None,
                 terminal_mode=VT100_TERMINAL_MODE_NORMAL, global_info=None):
        self.output_recv_content = output_recv_content  # <str> 一次recv接收到的所有字符（不含控制序列字符）
        self.terminal_vt100_obj = terminal_vt100_obj
        self.terminal_mode = terminal_mode
        self.start_index = start_index  # <str> "line.column"这种格式
        self.host_obj = host_obj
        self.global_info = global_info

    def __del__(self):
        self.terminal_vt100_obj = None
        self.host_obj = None
        self.global_info = None

    def set_custom_tag(self):
        if self.terminal_mode == VT100_TERMINAL_MODE_NORMAL:
            self.set_custom_tag_normal()
        self.terminal_vt100_obj.terminal_normal_text.yview(tkinter.MOVETO, 1.0)  # MOVETO表示移动到，0.0表示最开头，1.0表示最底端
        self.__del__()

    def set_custom_tag_normal(self):
        # 查找目标主机对应的配色方案，CustomTagConfigScheme对象
        scheme_obj = self.global_info.get_custome_tag_config_scheme_by_oid(self.host_obj.custome_tag_config_scheme_oid)
        if scheme_obj is None:
            print("CustomTagConfigSet.set_custom_tag_normal: 未找到目标主机的配色方案，已退出此函数")
            return
        with ThreadPoolExecutor(max_workers=1000) as tag_config_set_pool:
            for custom_match_object in scheme_obj.custom_match_object_list:
                # custom_match_font = font.Font(size=self.terminal_vt100_obj.font_size, family=self.terminal_vt100_obj.font_family)
                tag_config_set_match_object_obj = CustomTagConfigSetMatchObject(custom_match_object=custom_match_object,
                                                                                terminal_vt100_obj=self.terminal_vt100_obj,
                                                                                start_index=self.start_index,
                                                                                output_recv_content=self.output_recv_content)
                # tag_config_set_match_object_set_thread = threading.Thread(target=tag_config_set_match_object_obj.set)
                # tag_config_set_match_object_set_thread.start()
                tag_config_set_pool.submit(tag_config_set_match_object_obj.set)


class CustomTagConfigSetMatchObject:
    def __init__(self, custom_match_object=None, terminal_vt100_obj=None, start_index="", output_recv_content=""):
        self.custom_match_object = custom_match_object
        self.terminal_vt100_obj = terminal_vt100_obj
        self.start_index = start_index
        self.output_recv_content = output_recv_content

    def __del__(self):
        self.custom_match_object = None
        self.terminal_vt100_obj = None

    def set(self):
        font_type = FONT_TYPE_NORMAL
        if self.custom_match_object.bold:
            font_type += 1
        if self.custom_match_object.italic:
            font_type += 2
        with ThreadPoolExecutor(max_workers=10000) as tag_config_set_pool:
            for match_pattern in self.custom_match_object.match_pattern_lines.split("\n"):
                if match_pattern == "":
                    continue
                ret = re.finditer(match_pattern, self.output_recv_content, re.I)
                tag_config_name = uuid.uuid4().__str__()  # <str>
                for ret_item in ret:
                    # print(f"CustomTagConfigSetMatchObject.set: 匹配到了{match_pattern}")
                    set_match_item_obj = CustomTagConfigSetMatchObjectRetItem(ret_item=ret_item, start_index=self.start_index,
                                                                              custom_match_object=self.custom_match_object,
                                                                              terminal_vt100_obj=self.terminal_vt100_obj,
                                                                              tag_config_name=tag_config_name, font_type=font_type)
                    tag_config_set_pool.submit(set_match_item_obj.set)


class CustomTagConfigSetMatchObjectRetItem:
    def __init__(self, ret_item=None, start_index="1.0", custom_match_object=None,
                 terminal_vt100_obj=None, tag_config_name="", font_type=FONT_TYPE_NORMAL):
        self.ret_item = ret_item
        self.start_index = start_index
        self.custom_match_object = custom_match_object
        self.terminal_vt100_obj = terminal_vt100_obj
        self.tag_config_name = tag_config_name
        self.font_type = font_type

    def set(self):
        start_index, end_index = self.ret_item.span()
        start_index_count = "+" + str(start_index) + "c"
        end_index_count = "+" + str(end_index) + "c"
        try:
            # terminal_text.tag_delete("matched")
            # print("CustomTagConfigSetMatchObjectRetItem.set:匹配内容",
            #       self.terminal_vt100_obj.terminal_normal_text.get(self.start_index + start_index_count,
            #                                                        self.start_index + end_index_count))
            self.terminal_vt100_obj.terminal_normal_text.tag_add(f"{self.tag_config_name}", self.start_index + start_index_count,
                                                                 self.start_index + end_index_count)
            self.terminal_vt100_obj.terminal_normal_text.tag_config(f"{self.tag_config_name}",
                                                                    foreground=self.custom_match_object.foreground,
                                                                    backgroun=self.custom_match_object.backgroun,
                                                                    underline=self.custom_match_object.underline,
                                                                    underlinefg=self.custom_match_object.underlinefg,
                                                                    overstrike=self.custom_match_object.overstrike,
                                                                    overstrikefg=self.custom_match_object.overstrikefg)
            if self.font_type == FONT_TYPE_NORMAL:
                self.terminal_vt100_obj.terminal_normal_text.tag_config(f"{self.tag_config_name}",
                                                                        font=self.terminal_vt100_obj.terminal_font_normal)
            elif self.font_type == FONT_TYPE_BOLD:
                self.terminal_vt100_obj.terminal_normal_text.tag_config(f"{self.tag_config_name}",
                                                                        font=self.terminal_vt100_obj.terminal_font_bold)
            elif self.font_type == FONT_TYPE_ITALIC:
                self.terminal_vt100_obj.terminal_normal_text.tag_config(f"{self.tag_config_name}",
                                                                        font=self.terminal_vt100_obj.terminal_font_italic)
            elif self.font_type == FONT_TYPE_BOLD_ITALIC:
                self.terminal_vt100_obj.terminal_normal_text.tag_config(f"{self.tag_config_name}",
                                                                        font=self.terminal_vt100_obj.terminal_font_bold_italic)
        except tkinter.TclError as e:
            print("CustomTagConfigSetMatchObjectRetItem.set:", e)
            return


if __name__ == '__main__':
    # 创建全局信息类，用于存储所有资源类的对象，（若未指定数据库文件名称，则默认为"cofable_default.db"）
    builtin_font_file_path1 = os.path.join(os.path.dirname(__file__), "builtin_resource", "JetBrainsMono-Regular.ttf")
    global_info_obj = GlobalInfo(builtin_font_file_path=builtin_font_file_path1)
    print("当前程序路径:", __file__)
    global_info_obj.project_obj_list = global_info_obj.load_project_from_dbfile()  # 首先加载数据库，加载项目资源
    if len(global_info_obj.project_obj_list) == 0:  # 如果项目为空，默认先自动创建一个名为default的项目
        project_default = Project(global_info=global_info_obj)
        global_info_obj.project_obj_list.append(project_default)
        project_default.save()
    global_info_obj.load_all_data_from_sqlite3()  # 项目加载完成后，再加载其他资源，★★创建内置的shell着色方案
    global_info_obj.load_builtin_font_file()  # 加载程序内置字体文件 family="JetBrains Mono"
    # 创建程序主界面对象，全局只有一个
    main_window_obj = MainWindow(width=800, height=480, title='CofAble', global_info=global_info_obj)
    global_info_obj.main_window = main_window_obj
    main_window_obj.show()  # 显示主界面，一切从这里开始
