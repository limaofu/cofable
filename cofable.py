#!/usr/bin/env python3
# coding=utf-8
# module name: cofable
# dependence: cofnet, cofnetclass  (https://github.com/limaofu/cofnet)
# author: Cof-Lee
# update: 2024-01-18
# 本模块使用GPL-3.0开源协议

import uuid
import time
import sqlite3
import cofnet
import cofnetclass

# 全局常量
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


# 项目，是一个全局概念，一个项目包含若干资源（认证凭据，受管主机，巡检代码，巡检模板等）
# 同一项目里的资源可互相引用/使用，不同项目之间的资源不可互用
class Project:
    def __init__(self, name='default', description='default'):
        self.id = uuid.uuid4().__str__()  # <str>  project_id
        self.name = name  # <str>
        self.description = description  # <str>
        self.create_timestamp = time.time()  # <float>
        self.sqlite3_dbfile_name = self.name + ".db"

    def save(self):
        sqlite_conn = sqlite3.connect(self.sqlite3_dbfile_name)  # 连接数据库文件，若文件不存在则新建
        # 数据库所有数据存储在此文件中，默认数据库名称同文件名（不含.db后缀）
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_project'的表★
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_project";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql = "create table tb_project (id varchar(36) NOT NULL PRIMARY KEY,name varchar(128),\
                description varchar(256), create_timestamp double);"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_project where id='{self.id}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = f"insert into tb_project (id,name,description,create_timestamp) values \
            ('{self.id}','{self.name}','{self.description}',{self.create_timestamp})"
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 认证凭据，telnet/ssh/sftp登录凭据，snmp团体字，container-registry认证凭据，git用户凭据，ftp用户凭据
class Credential:
    def __init__(self, name='default', description='default', project_id='default', cred_type=CRED_TYPE_SSH,
                 username='default', password='default', private_key='default',
                 privilege_escalation_method=PRIVILEGE_ESCALATION_METHOD_SUDO, privilege_escalation_username='default',
                 privilege_escalation_password='default', first_auth_method=FIRST_AUTH_METHOD_PRIKEY,
                 auth_url='default',
                 ssl_no_verify=True, last_modify_timestamp=0):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
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
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_credential";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql = "create table tb_credential  ( id varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_id varchar(36),\
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
        sql = f"select * from tb_credential where id='{self.id}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_credential (id,\
                        name,\
                        description,\
                        project_id,\
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
                        ('{self.id}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_id}',\
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
    def __init__(self, name='default', description='default', project_id='default', address='default',
                 ssh_port=22, telnet_port=23, last_modify_timestamp=0):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
        self.address = address  # ip address or domain name # <str>
        self.ssh_port = ssh_port  # <int>
        self.telnet_port = telnet_port  # <int>
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.credential_id_list = []  # 元素为 Credential对象的cred_id

    def add_credential(self, credential_object):  # 每台主机都会绑定一个或多个不同类型的登录/访问认证凭据
        self.credential_id_list.append(credential_object)

    def save_to_project(self, project):
        sqlite_conn = sqlite3.connect(project.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_host'的表★
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql = "create table tb_host  ( id varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_id varchar(36),\
                        create_timestamp double,\
                        address varchar(256),\
                        ssh_port int,\
                        telnet_port int,\
                        last_modify_timestamp double );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_host where id='{self.id}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_host (id,\
                        name,\
                        description,\
                        project_id,\
                        create_timestamp,\
                        address,\
                        ssh_port,\
                        telnet_port,\
                        last_modify_timestamp )  values \
                        ('{self.id}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_id}',\
                        {self.create_timestamp},\
                        '{self.address}',\
                        {self.ssh_port},\
                        {self.telnet_port},\
                        {self.last_modify_timestamp} );"
                   )
            print(sql)
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_host_credential_id_list'的表★
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_credential_id_list";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_credential_id_list  ( host_id varchar(36),\
                            credential_id varchar(36) );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        for cred_id in self.credential_id_list:
            sql = f"select * from tb_host_credential_id_list where host_id='{self.id}' and credential_id='cred_id'"
            sqlite_cursor.execute(sql)
            if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
                sql = (f"insert into tb_host_credential_id_list (host_id,\
                                credential_id )  values \
                                ('{self.id}',\
                                '{cred_id}' );"
                       )
                # print(sql)
                sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 目标主机组，受管主机组
class HostGroup:
    def __init__(self, name='default', description='default', project_id='default', last_modify_timestamp=0):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.host_id_list = []
        self.host_group_id_list = []  # 不能包含自己

    def add_host(self, host):
        self.host_id_list.append(host.id)

    def add_host_group(self, host_group):  # 不能包含自己
        if host_group.id != self.id:
            self.host_group_id_list.append(host_group.id)
        else:
            pass

    def save_to_project(self, project):
        sqlite_conn = sqlite3.connect(project.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # 查询是否有名为'tb_host_group'的表
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # ★若未查询到有此表，则创建此表★
        if len(result) == 0:
            sql = "create table tb_host_group  ( id varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_id varchar(36),\
                        create_timestamp double,\
                        last_modify_timestamp double );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_host_group where id='{self.id}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_host_group (id,\
                        name,\
                        description,\
                        project_id,\
                        create_timestamp,\
                        last_modify_timestamp )  values \
                        ('{self.id}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_id}',\
                        {self.create_timestamp},\
                        {self.last_modify_timestamp} );"
                   )
            print(sql)
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_host_group_include_host_list'的表★
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group_include_host_list";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_group_include_host_list  ( host_group_id varchar(36),\
                            host_index int, host_id varchar(36) );"
            sqlite_cursor.execute(sql)
        # 每次保存host前，先删除所有host内容，再去重新插入
        sql = f"delete from tb_host_group_include_host_list where host_group_id='{self.id}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        index = 0
        for host_id in self.host_id_list:
            sql = (f"insert into tb_host_group_include_host_list (host_group_id,\
                            host_index, host_id )  values \
                            ('{self.id}', {index}, '{host_id}' );"
                   )
            # print(sql)
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_host_group_include_group_list'的表★
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_host_group_include_group_list";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_host_group_include_group_list  ( host_group_id varchar(36),\
                                host_index int, group_id varchar(36) );"
            sqlite_cursor.execute(sql)
        # 每次保存group前，先删除所有group内容，再去重新插入
        sql = f"delete from tb_host_group_include_group_list where host_group_id='{self.id}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        index = 0
        for group_id in self.host_group_id_list:
            sql = (f"insert into tb_host_group_include_group_list (host_group_id,\
                                host_index, group_id )  values \
                                ('{self.id}', {index}, '{group_id}' );"
                   )
            # print(sql)
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 巡检代码
class InspectionCode:
    def __init__(self, name='default', description='default', project_id='default',
                 code_source=CODE_SOURCE_LOCAL, last_modify_timestamp=0):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
        self.code_source = code_source  # <int> 可为本地的命令，也可为git仓库里的写有命令的某文件
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.code_list = []  # 元素为 <str> 一行为一条命令，按顺序执行

    def add_code(self, code_string):
        self.code_list.append(code_string)

    def save_to_project(self, project):
        sqlite_conn = sqlite3.connect(project.sqlite3_dbfile_name)  # 连接数据库文件
        sqlite_cursor = sqlite_conn.cursor()  # 创建一个游标，用于执行sql语句
        # ★查询是否有名为'tb_inspection_code'的表★
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_code";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        # 若未查询到有此表，则创建此表
        if len(result) == 0:
            sql = "create table tb_inspection_code  ( id varchar(36) NOT NULL PRIMARY KEY,\
                        name varchar(128),\
                        description varchar(256),\
                        project_id varchar(36),\
                        create_timestamp double,\
                        code_source int,\
                        last_modify_timestamp double );"
            sqlite_cursor.execute(sql)
        # 开始插入数据
        sql = f"select * from tb_inspection_code where id='{self.id}'"
        sqlite_cursor.execute(sql)
        if len(sqlite_cursor.fetchall()) == 0:  # 若未查询到有此项目记录，则创建此项目记录
            sql = (f"insert into tb_inspection_code (id,\
                        name,\
                        description,\
                        project_id,\
                        create_timestamp,\
                        code_source,\
                        last_modify_timestamp )  values \
                        ('{self.id}',\
                        '{self.name}',\
                        '{self.description}',\
                        '{self.project_id}',\
                        {self.create_timestamp},\
                        {self.code_source},\
                        {self.last_modify_timestamp} );"
                   )
            print(sql)
            sqlite_cursor.execute(sql)
        # ★查询是否有名为'tb_inspection_code_list'的表★
        sqlite_cursor.execute(
            'SELECT * FROM sqlite_master WHERE "type"="table" and "tbl_name"="tb_inspection_code_list";')
        result = sqlite_cursor.fetchall()  # fetchall()从结果中获取所有记录，返回一个list，元素为<tuple>（即查询到的结果）
        print("exist tables: ", result)
        if len(result) == 0:  # 若未查询到有此表，则创建此表
            sql = "create table tb_inspection_code_list  ( inspection_code_id varchar(36),\
                            code_index int, code_contenet varchar(36) );"
            sqlite_cursor.execute(sql)
        # 每次保存代码前，先删除所有code内容，再去重新插入
        sql = f"delete from tb_inspection_code_list where inspection_code_id='{self.id}' "
        sqlite_cursor.execute(sql)
        # 开始插入数据
        index = 0
        for code_contenet in self.code_list:
            sql = (f"insert into tb_inspection_code_list (inspection_code_id,\
                            code_index, code_contenet )  values \
                            ('{self.id}', {index}, '{code_contenet}' );"
                   )
            # print(sql)
            sqlite_cursor.execute(sql)
        sqlite_cursor.close()
        sqlite_conn.commit()  # 保存，提交
        sqlite_conn.close()  # 关闭数据库连接


# 巡检模板，包含目标主机，可手动触发执行，可定时执行，可周期执行
class InspectionTemplate:
    def __init__(self, name='default', description='default', project_id='default',
                 execution_method='default', execution_start_time='default', update_revision_on_launch=False,
                 enabled_crond_job=False, last_modify_timestamp=0):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
        self.execution_method = execution_method
        self.execution_start_time = execution_start_time  # <float>
        self.enabled_crond_job = enabled_crond_job  # <bool>
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.host_id_list = []
        self.host_group_id_list = []
        self.inspection_code_id_list = []  # 巡检代码InspectionCode对象的id
        self.update_revision_on_launch = update_revision_on_launch  # 是否在执行项目任务时自动更新巡检代码
        self.cron_detection_trigger_id = None  # CronDetectionTrigger对象的id

    def add_host(self, host_id):
        self.host_id_list.append(host_id)

    def add_host_group(self, host_group_id):
        self.host_group_id_list.append(host_group_id)

    def add_inspection_code(self, inspection_code_id):
        self.inspection_code_id_list.append(inspection_code_id)


# 巡检触发检测类，周期检查是否需要执行某巡检模板，每创建一个巡检模板就要求绑定一个巡检触发检测对象
class CronDetectionTrigger:
    def __init__(self, name='default', description='default', project_id='default',
                 inspection_template_id='uuid', last_modify_timestamp=0):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
        self.inspection_template_id = inspection_template_id
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
    def __init__(self, name='default', description='default', project_id='default'):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
        self.host_id_list = []
        self.host_group_id_list = []
        self.inspection_code_id_list = []  # 巡检代码id
