#!/usr/bin/env python3
# coding=utf-8
# module name: cofable
# dependence: cofnet, cofnetclass  (https://github.com/limaofu/cofnet)
# author: Cof-Lee
# update: 2024-01-19
# 本模块使用GPL-3.0开源协议

import uuid
import time
import sqlite3
import cofnet

# 全局常量
COF_TRUE = 1
COF_FALSE = 0
CRED_TYPE_SSH = 1
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
        self.sqlite3_dbfile_name = self.name + ".db"

    def save(self):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        # 数据库所有数据存储在此文件中，默认数据库名称同文件名（不含.db后缀）
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_project'的表★
        sql = 'SELECT * FROM sqlite_master WHERE type="table" and tbl_name="tb_project"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql = "create table tb_project (oid varchar(36) NOT NULL PRIMARY KEY,name varchar(128),\
                description varchar(256), create_timestamp double);"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_project where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = f"insert into tb_project (oid,name,description,create_timestamp) values \
            ('{self.oid}','{self.name}','{self.description}',{self.create_timestamp})"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 认证凭据，telnet/ssh/sftp登录凭据，snmp团体字，container-registry认证凭据，git用户凭据，ftp用户凭据
class Credential:
    def __init__(self, name='default', description='default', project_oid='default', cred_type=CRED_TYPE_SSH,
                 username='default', password='default', private_key='default',
                 privilege_escalation_method=PRIVILEGE_ESCALATION_METHOD_SUDO, privilege_escalation_username='default',
                 privilege_escalation_password='default', first_auth_method=FIRST_AUTH_METHOD_PRIKEY,
                 auth_url='default', ssl_no_verify=COF_TRUE, last_modify_timestamp=0, oid=None, create_timestamp=None):
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
        self.first_auth_method = first_auth_method
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
            sql = "create table tb_credential  ( oid varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_oid varchar(36),\
                        create_timestamp double,\
                        cred_type int,\
                        username varchar(128),\
                        password varchar(256),\
                        private_key varchar(1024),\
                        privilege_escalation_method int,\
                        privilege_escalation_username varchar(128),\
                        privilege_escalation_password varchar(256),\
                        first_auth_method int,\
                        auth_url varchar(2048),\
                        ssl_no_verify int,\
                        last_modify_timestamp double );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_credential where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_credential (oid,\
                        name,\
                        description,\
                        project_oid,\
                        create_timestamp,\
                        cred_type,\
                        username,\
                        password,\
                        private_key,\
                        privilege_escalation_method,\
                        privilege_escalation_username,\
                        privilege_escalation_password,\
                        first_auth_method,\
                        auth_url,\
                        ssl_no_verify,\
                        last_modify_timestamp ) values \
                        ('{self.oid}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_oid}',\
                        {self.create_timestamp},\
                        {self.cred_type},\
                        '{self.username}',\
                        '{self.password}',\
                        '{self.private_key}',\
                        {self.privilege_escalation_method},\
                        '{self.privilege_escalation_username}',\
                        '{self.privilege_escalation_password}',\
                        {self.first_auth_method},\
                        '{self.auth_url}',\
                        {self.ssl_no_verify},\
                        {self.last_modify_timestamp} );"
                   )
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 目标主机，受管主机
class Host:
    def __init__(self, name='default', description='default', project_oid='default', address='default',
                 ssh_port=22, telnet_port=23, last_modify_timestamp=0, oid=None, create_timestamp=None):
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
        self.credential_oid_list = []  # 元素为 Credential对象的cred_oid

    def add_credential(self, credential_object):  # 每台主机都会绑定一个或多个不同类型的登录/访问认证凭据
        self.credential_oid_list.append(credential_object.oid)

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
            sql = "create table tb_host  ( oid varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_oid varchar(36),\
                        create_timestamp double,\
                        address varchar(256),\
                        ssh_port int,\
                        telnet_port int,\
                        last_modify_timestamp double );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_host where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_host (oid,\
                        name,\
                        description,\
                        project_oid,\
                        create_timestamp,\
                        address,\
                        ssh_port,\
                        telnet_port,\
                        last_modify_timestamp )  values \
                        ('{self.oid}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_oid}',\
                        {self.create_timestamp},\
                        '{self.address}',\
                        {self.ssh_port},\
                        {self.telnet_port},\
                        {self.last_modify_timestamp} );"
                   )
            print(sql)
            sqlite_cursor.execute(sql)
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
                sql = (f"insert into tb_host_include_credential_oid_list (host_oid,\
                                credential_oid )  values \
                                ('{self.oid}',\
                                '{cred_oid}' );"
                       )
                # print(sql)
                sqlite_cursor.execute(sql)
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

    def add_host(self, host):
        self.host_oid_list.append(host.oid)

    def add_host_group(self, host_group):  # 不能包含自己
        if host_group.oid != self.oid:
            self.host_group_oid_list.append(host_group.oid)
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
            sql = "create table tb_host_group  ( oid varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_oid varchar(36),\
                        create_timestamp double,\
                        last_modify_timestamp double );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_host_group where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_host_group (oid,\
                        name,\
                        description,\
                        project_oid,\
                        create_timestamp,\
                        last_modify_timestamp )  values \
                        ('{self.oid}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_oid}',\
                        {self.create_timestamp},\
                        {self.last_modify_timestamp} );"
                   )
            print(sql)
            sqlite_cursor.execute(sql)
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
            sql = (f"insert into tb_host_group_include_host_list (host_group_oid,\
                            host_index, host_oid )  values \
                            ('{self.oid}', {host_index}, '{host_oid}' );"
                   )
            # print(sql)
            sqlite_cursor.execute(sql)
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
            sql = (f"insert into tb_host_group_include_group_list (host_group_oid,\
                                group_index, group_oid )  values \
                                ('{self.oid}', {group_index}, '{group_oid}' );"
                   )
            # print(sql)
            sqlite_cursor.execute(sql)
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
        self.code_list = []  # 元素为 <dictionary> 一行为一条命令（一个元素），按顺序执行

    def add_code_line(self, code_index=None, code_content='', code_post_wait_time=None, interactive_answer=None):
        if code_index is None:
            code_index = len(self.code_list)
        else:
            pass
        if code_post_wait_time is None:
            code_post_wait_time = 0
        else:
            pass
        if interactive_answer is None:
            interactive_answer = ''
        else:
            pass
        self.code_list.append(
            {"code_index": code_index, "code_content": code_content, "code_post_wait_time": code_post_wait_time,
             "interactive_answer": interactive_answer})

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
            sql = "create table tb_inspection_code  ( oid varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_oid varchar(36),\
                        create_timestamp double,\
                        code_source int,\
                        last_modify_timestamp double );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_inspection_code where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_inspection_code (oid,\
                        name,\
                        description,\
                        project_oid,\
                        create_timestamp,\
                        code_source,\
                        last_modify_timestamp )  values \
                        ('{self.oid}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_oid}',\
                        {self.create_timestamp},\
                        {self.code_source},\
                        {self.last_modify_timestamp} );"
                   )
            print(sql)
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_code_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_code_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_inspection_code_list  ( inspection_code_oid varchar(36),\
                            code_index int, code_content varchar(512), code_post_wait_time double,\
                            interactive_answer varchar(32) );"
            sqlite_cursor.execute(sql)
        # 每次保存代码前，先删除所有code内容，再去重新插入
        sql = f"delete from tb_inspection_code_list where inspection_code_oid='{self.oid}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        for code_dict in self.code_list:
            sql = (f"insert into tb_inspection_code_list (inspection_code_oid,\
                            code_index, code_content, code_post_wait_time, interactive_answer )  values \
                            ('{self.oid}', {code_dict['code_index']}, '{code_dict['code_content']}',\
                            {code_dict['code_post_wait_time']}, '{code_dict['interactive_answer']}' )"
                   )
            print(sql)
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 巡检模板，包含目标主机，可手动触发执行，可定时执行，可周期执行
class InspectionTemplate:
    def __init__(self, name='default', description='default', project_oid='default',
                 execution_method=EXECUTION_METHOD_NONE, execution_at_time=0,
                 execution_after_time=0, execution_crond_time='default', update_code_on_launch=COF_FALSE,
                 last_modify_timestamp=0, oid=None, create_timestamp=None):
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
        self.launch_template_trigger_oid = ''  # <str> CronDetectionTrigger对象的oid，此信息不保存到数据库

    def add_host(self, host):
        self.host_oid_list.append(host.oid)

    def add_host_group(self, host_group):
        self.host_group_oid_list.append(host_group.oid)

    def add_inspection_code(self, inspection_code):
        self.inspection_code_oid_list.append(inspection_code.oid)

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
            sql = "create table tb_inspection_template  ( oid varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_oid varchar(36),\
                        create_timestamp double,\
                        execution_method int,\
                        execution_at_time double,\
                        execution_after_time,\
                        execution_crond_time varchar(128),\
                        last_modify_timestamp double,\
                        update_code_on_launch int );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_inspection_template where oid='{self.oid}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_inspection_template (oid,\
                        name,\
                        description,\
                        project_oid,\
                        create_timestamp,\
                        execution_method,\
                        execution_at_time,\
                        execution_after_time,\
                        execution_crond_time,\
                        last_modify_timestamp,\
                        update_code_on_launch )  values \
                        ('{self.oid}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_oid}',\
                        {self.execution_method},\
                        {self.execution_at_time},\
                        {self.execution_after_time},\
                        '{self.execution_crond_time}',\
                        {self.create_timestamp},\
                        {self.last_modify_timestamp},\
                        {self.update_code_on_launch} );"
                   )
            print(sql)
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_template_include_host_list'的表★
        sql = 'SELECT * FROM sqlite_master WHERE \
                    "type"="table" and "tbl_name"="tb_inspection_template_include_host_list"'
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_inspection_template_include_host_list  ( inspection_template_oid varchar(36),\
                            host_index int, host_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 每次保存host前，先删除所有host内容，再去重新插入
        sql = f"delete from tb_inspection_template_include_host_list where inspection_template_oid='{self.oid}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        host_index = 0
        for host_oid in self.host_oid_list:
            sql = (f"insert into tb_inspection_template_include_host_list (inspection_template_oid,\
                            host_index, host_oid )  values \
                            ('{self.oid}', {host_index}, '{host_oid}' );"
                   )
            # print(sql)
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_template_include_group_list'的表★
        sql = (f'SELECT * FROM sqlite_master WHERE \
                    "type"="table" and "tbl_name"="tb_inspection_template_include_group_list"')
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_inspection_template_include_group_list  ( inspection_template_oid varchar(36),\
                                group_index int, group_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 每次保存group前，先删除所有group内容，再去重新插入
        sql = f"delete from tb_inspection_template_include_group_list where inspection_template_oid='{self.oid}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        group_index = 0
        for group_oid in self.host_group_oid_list:
            sql = (f"insert into tb_inspection_template_include_group_list (inspection_template_oid,\
                                group_index, group_oid )  values \
                                ('{self.oid}', {group_index}, '{group_oid}' );"
                   )
            # print(sql)
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_template_include_inspection_code_list'的表★
        sql = (f'SELECT * FROM sqlite_master WHERE \
                    type="table" and tbl_name="tb_inspection_template_include_inspection_code_list"')
        sqlite_cursor.execute(sql)
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_inspection_template_include_inspection_code_list  ( \
            inspection_template_oid varchar(36), inspection_code_index int, inspection_code_oid varchar(36) );"
            sqlite_cursor.execute(sql)
        # 每次保存group前，先删除所有group内容，再去重新插入
        sql = (f"delete from tb_inspection_template_include_inspection_code_list where \
                    inspection_template_oid='{self.oid}' ")
        sqlite_cursor.execute(sql)
        # 开始插入数据
        inspection_code_index = 0
        for inspection_code_oid in self.inspection_code_oid_list:
            sql = (f"insert into tb_inspection_template_include_inspection_code_list \
                                    (inspection_template_oid, inspection_code_index,\
                                    inspection_code_oid )  values \
                                    ('{self.oid}', {inspection_code_index}, '{inspection_code_oid}' );"
                   )
            # print(sql)
            sqlite_cursor.execute(sql)
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
class LaunchInspectionJob:
    def __init__(self, name='default', description='default', project_oid='default', oid=None, create_timestamp=None):
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
        self.host_oid_list = []
        self.host_group_oid_list = []
        self.inspection_code_oid_list = []  # 巡检代码oid

    def start_job(self, inspection_template):
        print(inspection_template.name)
        pass


def load_proects_from_dbfile(dbfilepath):
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
                         first_auth_method=obj_info_tuple[12],
                         auth_url=obj_info_tuple[13],
                         ssl_no_verify=obj_info_tuple[14],
                         last_modify_timestamp=obj_info_tuple[15])
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
                   last_modify_timestamp=obj_info_tuple[8])
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
            inspection_code.code_list.append(
                {"code_index": obj_info_tuple[1], "code_content": obj_info_tuple[2],
                 "code_post_wait_time": obj_info_tuple[3], "interactive_answer": obj_info_tuple[4]})


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
                                 execution_at_time=obj_info_tuple[5],
                                 execution_after_time=obj_info_tuple[5],
                                 execution_crond_time=obj_info_tuple[5],
                                 last_modify_timestamp=obj_info_tuple[6],
                                 update_code_on_launch=obj_info_tuple[5])
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
