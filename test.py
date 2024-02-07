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
Omsz/LlJRbNdzaeYIaMKrqRJ6tOU/8gSbb6qG42VwUnB7Q7NgiGMWfZu0Yc/dGkT7rvF3v
TJbXSiUbScHY0AM414+tE0W/ZwL3EBW97qkCc8NTT1RQRF6F8Ge1nyuyhdLTz7e4S7tL93
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
    host_4 = cofable.Host(name='host_4', address='10.99.1.232', ssh_port='22', project_oid=pro_test1.oid)
    host_4.add_credential(cred_host2)  # 主机添加登录凭据
    host_4.save_to_project(pro_test1)
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
    codeline1 = cofable.OneLineCode(code_content=r'ping -c 3 10.99.1.1', code_post_wait_time=6)
    codeline2 = cofable.OneLineCode(code_content=r'df -Th')
    codeline5 = cofable.OneLineCode(code_content=r'ip addr')
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
                                                           project_oid=pro_test1.oid, forks=3)
    inspection_template_test1.add_host(host_1)
    inspection_template_test1.add_host(host_4)
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
        # 开始执行监视任务，达到触发条件就执行相应巡检模板（由cofable.LaunchTemplateTrigger.start_crontab_job()方法触发）
        cron_trigger1.start_crontab_job()
    else:
        pass
    inspection_template_test1.save_to_project(pro_test1)

    # 创建巡检模板-switch
    inspection_template_test2 = cofable.InspectionTemplate(name='template2-switch',
                                                           execution_method=cofable.EXECUTION_METHOD_NONE,
                                                           project_oid=pro_test1.oid, forks=2)
    inspection_template_test2.add_host(host_3)
    inspection_template_test2.add_inspection_code(inspect_code_test3)
    inspection_template_test2.save_to_project(pro_test1)
    print("end of create ################################################")
    # 手动触发巡检模板
    job_1 = cofable.LaunchInspectionJob(name='job_1', project=pro_test1, inspection_template=inspection_template_test1)
    job_1.start_job()
    # job_2_switch = cofable.LaunchInspectionJob(name='job_2_switch', inspection_template=inspection_template_test2)
    # job_2_switch.start_job()


def test_window():
    global_info = cofable.GlobalInfo()
    # global_info.load_all_data_from_sqlite3()
    window = cofable.MainWindow(width=640, height=400, title='cofAble', global_info=global_info)
    window.show()


if __name__ == '__main__':
    # create_project()
    test_window()

"""
解决问题：
★. 执行命令时进行判断回复                                 2024年1月23日 基本完成
★. 登录凭据的选择与多次尝试各同类凭据（当同类型凭据有多个时），只选择第一个能成功登录的cred     2024年1月23日 完成
★. ssh密码登录，ssh密钥登录                              2024年1月23日 完成
★. 所有输出整理到txt文件                                 2024年1月24日 完成
★. 使用多线程，每台主机用一个线程去巡检，并发几个线程          2024年1月25日 完成
★. 巡检作业执行完成情况的统计，执行完成，连接超时，认证失败     2024年1月28日 基本完成
★. 程序运行后，所有类的对象都要分别加载到一个全局列表里
★. 巡检命令输出保存到数据库                               2024年1月27日 基本完成
★. 定时/周期触发巡检模板作业
★. 本次作业命令输出与最近一次（上一次）输出做对比
★. 巡检命令输出做基础信息提取与判断并触发告警，告警如何通知人类用户？
"""
