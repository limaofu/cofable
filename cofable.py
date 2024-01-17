#!/usr/bin/env python3
# coding=utf-8
# module name: cofable
# dependence: cofnet, cofnetclass
# author: Cof-Lee
# update: 2024-01-17

import uuid
import time
import cofnet
import cofnetclass


# 项目，是一个全局概念，一个项目包含若干资源（认证凭据，受管主机，巡检代码，巡检模板等）
# 同一项目里的资源可互相引用/使用，不同项目之间的资源不可互用
class Project:
    def __init__(self, name='default', description='default'):
        self.id = uuid.uuid4().__str__()  # <str>  project_id
        self.name = name  # <str>
        self.description = description  # <str>
        self.create_timestamp = time.time()  # <float>


# 认证凭据，telnet/ssh/sftp登录凭据，snmp团体字，container-registry认证凭据，git用户凭据，ftp用户凭据
class Credential:
    def __init__(self, name='default', description='default', project_id='default', cred_type='default',
                 username='default', password='default', private_key='default',
                 privilege_escalation_method='default', privilege_escalation_username='default',
                 privilege_escalation_password='default', first_auth_method='default', auth_url='default',
                 ssl_no_verify=True, last_modify_timestamp=0):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
        self.cred_type = cred_type
        self.username = username  # <str>
        self.password = password  # <str>
        self.private_key = private_key
        self.privilege_escalation_method = privilege_escalation_method
        self.privilege_escalation_username = privilege_escalation_username
        self.privilege_escalation_password = privilege_escalation_password
        self.first_auth_method = first_auth_method
        self.auth_url = auth_url  # 含container-registry,git等
        self.ssl_no_verify = ssl_no_verify  # 默认为True，不校验ssl证书
        self.last_modify_timestamp = last_modify_timestamp  # <float>


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

    def add_host(self, host_id):
        self.host_id_list.append(host_id)

    def add_host_group(self, host_group_id):  # 不能包含自己
        self.host_group_id_list.append(host_group_id)


# 巡检代码
class InspectionCode:
    def __init__(self, name='default', description='default', project_id='default',
                 code_source='local', last_modify_timestamp=0):
        self.id = uuid.uuid4().__str__()  # <str>
        self.name = name  # <str>
        self.description = description  # <str>
        self.project_id = project_id  # <str>
        self.create_timestamp = time.time()  # <float>
        self.code_source = code_source  # 可为本地的命令，也可为git仓库里的写有命令的某文件
        self.last_modify_timestamp = last_modify_timestamp  # <float>
        self.code_list = []  # 元素为 <str> 一行为一条命令，按顺序执行

    def add_code(self, code_string):
        self.code_list.append(code_string)


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
