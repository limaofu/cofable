import cofable


def create_project():
    project_obj_list = []
    print('业务流程：')
    # 首先创建一个项目
    pro_test1 = cofable.Project(name='pro_test1', description='cofable测试项目1')
    pro_test1.save()
    project_obj_list.append(pro_test1)
    # ★再创建资源
    # 创建登录凭据
    cred_host1 = cofable.Credential(name='cred_host1', username='root', password='xxxxxx',
                                    cred_type=cofable.CRED_TYPE_SSH_PASS, project_oid=pro_test1.oid)
    cred_host1.save_to_project(pro_test1)
    prikey_content = '''-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
NhAAAAAwEAAQAAAYEA1at9EMtFIgsvfOXkUNU3C6d/XC4DTcvb1OR1cv8WI4eRBBLaLgtH
kZYgt0+Qi+1iP4GBVmToLyVVyi2N0yffbityYymXlB8/hpVOxcf+x1KdJ2HKifkGNdzjkB
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QvMiUgh92RbTtHAAAAFHJvb3RAZWxrLmNvZi1sZWUuY29tAQIDBAUG
-----END OPENSSH PRIVATE KEY-----
'''
    cred_host1_key = cofable.Credential(name='cred_host1_key', username='root', private_key=prikey_content,
                                        cred_type=cofable.CRED_TYPE_SSH_KEY,
                                        project_oid=pro_test1.oid)
    cred_host1_key.save_to_project(pro_test1)
    cred_host2 = cofable.Credential(name='cred_host2', username='root', password='xxxxxx',
                                    cred_type=cofable.CRED_TYPE_SSH_PASS, project_oid=pro_test1.oid)
    cred_host2.save_to_project(pro_test1)
    cred_host3 = cofable.Credential(name='cred_host3', username='admin', password='xxxxxx',
                                    cred_type=cofable.CRED_TYPE_SSH_PASS,
                                    project_oid=pro_test1.oid)
    cred_host3.save_to_project(pro_test1)
    # 创建主机
    host_1 = cofable.Host(name='host_1', address='10.99.1.233', ssh_port='22', project_oid=pro_test1.oid)
    # host_1.add_credential(cred_host1)  # 主机添加登录凭据
    host_1.add_credential(cred_host1_key)  # 主机添加登录凭据
    host_1.save_to_project(pro_test1)
    host_2 = cofable.Host(name='host_2', address='10.99.1.234', ssh_port='22', project_oid=pro_test1.oid)
    host_2.add_credential(cred_host2)  # 主机添加登录凭据
    host_2.save_to_project(pro_test1)
    host_3 = cofable.Host(name='host_3-switch', address='10.99.1.8', ssh_port='22', project_oid=pro_test1.oid)
    host_3.add_credential(cred_host3)  # 主机添加登录凭据
    host_3.save_to_project(pro_test1)
    # 创建主机组
    host_group1 = cofable.HostGroup(name='host_group1')
    host_group1.add_host(host_1)
    host_group1.add_host(host_2)
    host_group1.save_to_project(pro_test1)

    host_group2 = cofable.HostGroup(name='host_group2')
    host_group2.add_host(host_1)
    host_group2.add_host_group(host_group1)
    host_group2.add_host_group(host_group2)
    host_group2.save_to_project(pro_test1)
    # 创建巡检代码
    inspect_code_test1 = cofable.InspectionCode(name='inspect_code_test1', code_source=cofable.CODE_SOURCE_LOCAL,
                                                project_oid=pro_test1.oid)
    inspect_code_test2 = cofable.InspectionCode(name='inspect_code_test2', code_source=cofable.CODE_SOURCE_LOCAL,
                                                project_oid=pro_test1.oid)
    inspect_code_test3 = cofable.InspectionCode(name='inspect_code_test3', code_source=cofable.CODE_SOURCE_LOCAL,
                                                project_oid=pro_test1.oid)
    codeline1 = cofable.OneLineCode(code_content=r'hostname')
    codeline2 = cofable.OneLineCode(code_content=r'df -Th')
    codeline5 = cofable.OneLineCode(code_content=r'cat anaconda-ks.cfg')
    codeline3 = cofable.OneLineCode(code_content=r'more anaconda-ks.cfg', need_interactive=True,
                                    interactive_question_keyword=r'More',
                                    interactive_answer=r' ',
                                    interactive_process_method=cofable.INTERACTIVE_PROCESS_METHOD_LOOP)
    codeline4 = cofable.OneLineCode(code_content=r'save', need_interactive=True,
                                    interactive_question_keyword=r'\?\[Y/N\]',
                                    interactive_answer='y',
                                    interactive_process_method=cofable.INTERACTIVE_PROCESS_METHOD_ONCE)
    inspect_code_test1.add_code_line(codeline1)  # 巡检代码对象添加要执行的命令
    inspect_code_test1.add_code_line(codeline2)  # 巡检代码对象添加要执行的命令
    inspect_code_test1.add_code_line(codeline5)  # 巡检代码对象添加要执行的命令
    inspect_code_test2.add_code_line(codeline3)  # 巡检代码对象添加要执行的命令
    inspect_code_test3.add_code_line(codeline4)  # 巡检代码对象添加要执行的命令
    inspect_code_test1.save_to_project(pro_test1)
    inspect_code_test2.save_to_project(pro_test1)
    inspect_code_test3.save_to_project(pro_test1)

    # 创建巡检模板
    inspection_template_test1 = cofable.InspectionTemplate(name='template1',
                                                           execution_method=cofable.EXECUTION_METHOD_NONE,
                                                           project_oid=pro_test1.oid)
    inspection_template_test1.add_host(host_1)
    inspection_template_test1.add_host(host_1)
    inspection_template_test1.add_host_group(host_group2)
    inspection_template_test1.add_host_group(host_group2)
    inspection_template_test1.add_inspection_code(inspect_code_test1)
    inspection_template_test1.add_inspection_code(inspect_code_test2)  # 有交互的
    # 如果巡检模板创建了定时任务，则创建触发器
    if inspection_template_test1.execution_method != cofable.EXECUTION_METHOD_NONE:
        cron_trigger1 = cofable.LaunchTemplateTrigger(
            inspection_template_oid=inspection_template_test1.oid,
            project_oid=pro_test1.oid)
        inspection_template_test1.cron_detection_trigger_oid = cron_trigger1.oid  # 将触发器id添加到巡检模板对象上
        # 开始执行监视任务，达到触发条件就执行相应巡检模板（由start_crontab_job函数触发）
        cron_trigger1.start_crontab_job()
    else:
        pass
    inspection_template_test1.save_to_project(pro_test1)

    # 创建巡检模板-switch
    inspection_template_test2 = cofable.InspectionTemplate(name='template2-switch',
                                                           execution_method=cofable.EXECUTION_METHOD_NONE,
                                                           project_oid=pro_test1.oid)
    inspection_template_test2.add_host(host_3)
    inspection_template_test2.add_inspection_code(inspect_code_test3)
    inspection_template_test2.save_to_project(pro_test1)
    print("end of create ################################################")
    # 手动触发巡检模板
    job_1 = cofable.LaunchInspectionJob(name='job_1', inspection_template=inspection_template_test1)
    job_1.start_job()
    # job_2_switch = cofable.LaunchInspectionJob(name='job_2_switch', inspection_template=inspection_template_test2)
    # job_2_switch.start_job()


def load_project():
    pro_list = cofable.load_proects_from_dbfile('pro_test1.db')
    for pro in pro_list:
        print(pro.name)
    cred_list = cofable.load_credentials_from_dbfile('pro_test1.db')
    for cred in cred_list:
        print(cred.name)
    host_list = cofable.load_hosts_from_dbfile('pro_test1.db')
    for host in host_list:
        print(host.name, host.credential_oid_list)
    host_group_list = cofable.load_host_groups_from_dbfile('pro_test1.db')
    for host_group in host_group_list:
        print(host_group.name, host_group.host_oid_list, host_group.host_group_oid_list)
    inspect_code_list = cofable.load_inspection_codes_from_dbfile('pro_test1.db')
    for code in inspect_code_list:
        print(code.name, code.code_list[0].code_content)

    inspect_template_list = cofable.load_inspection_templates_from_dbfile('pro_test1.db')
    for template in inspect_template_list:
        print(template.name, template.host_oid_list, template.host_group_oid_list, template.inspection_code_oid_list)


if __name__ == '__main__':
    create_project()
    # load_project()

"""
遗留问题：
1. 执行命令时进行判断回复，基本完成
2. 登录凭据的选择与多次尝试各同类凭据（当同类型凭据有多个时），只选择第一个能成功登录的cred，完成
3. ssh密码登录，ssh密钥登录，完成
4. 所有输出整理到txt文件，基本完成
"""
