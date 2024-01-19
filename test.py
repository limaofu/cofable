import time
import cofable


def create_project():
    start_time = time.time()
    project_obj_list = []
    print('业务流程：')
    # 首先创建一个项目
    pro_test1 = cofable.Project(name='pro_test1', description='cofable测试项目1')
    pro_test1.save()
    project_obj_list.append(pro_test1)

    # 再创建资源
    cred_host1 = cofable.Credential(name='cred_host1', username='root', password='xxxxxx', project_oid=pro_test1.oid)
    cred_host1.save_to_project(pro_test1)

    cred_host2 = cofable.Credential(name='cred_host2', username='root', password='xxxxxx', project_oid=pro_test1.oid)
    cred_host2.save_to_project(pro_test1)

    host_1 = cofable.Host(name='host_01', address='10.99.1.233', ssh_port='22', project_oid=pro_test1.oid)
    host_1.add_credential(cred_host1)  # 主机添加登录凭据
    host_1.add_credential(cred_host2)  # 主机添加登录凭据
    host_1.save_to_project(pro_test1)
    host_1.save_to_project(pro_test1)

    host_group1 = cofable.HostGroup(name='host_group1')
    host_group1.add_host(host_1)
    host_group1.save_to_project(pro_test1)

    host_group2 = cofable.HostGroup(name='host_group2')
    host_group2.add_host(host_1)
    host_group2.add_host_group(host_group1)
    host_group2.add_host_group(host_group2)
    host_group2.save_to_project(pro_test1)

    inspect_code_test1 = cofable.InspectionCode(name='inspect_code_test1', code_source=cofable.CODE_SOURCE_LOCAL,
                                                project_oid=pro_test1.oid)
    inspect_code_test1.add_code_line(code_content=r'df -Th')  # 巡检代码对象添加要执行的命令
    inspect_code_test1.add_code_line(code_content=r'ls -lh')  # 巡检代码对象添加要执行的命令
    inspect_code_test1.add_code_line(code_content=r'cat /etc/fstab')  # 巡检代码对象添加要执行的命令
    inspect_code_test1.save_to_project(pro_test1)
    inspect_code_test1.save_to_project(pro_test1)

    # 创建巡检模板
    inspection_template_test1 = cofable.InspectionTemplate(name='template1',
                                                           execution_method=cofable.EXECUTION_METHOD_NONE,
                                                           project_oid=pro_test1.oid)
    inspection_template_test1.add_host(host_1)
    inspection_template_test1.add_host_group(host_group2)
    inspection_template_test1.add_inspection_code(inspect_code_test1)

    if inspection_template_test1.execution_method != cofable.EXECUTION_METHOD_NONE:
        cron_trigger1 = cofable.LaunchTemplateTrigger(
            inspection_template_oid=inspection_template_test1.oid,
            project_oid=pro_test1.oid)
        inspection_template_test1.cron_detection_trigger_oid = cron_trigger1.oid
        # 开始执行监视任务，达到触发条件就执行相应巡检模板
        cron_trigger1.start_crontab_job()
    else:
        pass
    inspection_template_test1.save_to_project(pro_test1)
    job_1 = cofable.LaunchInspectionJob(name='job_1')  # 手动触发巡检模板
    job_1.start_job(inspection_template_test1)
    end_time = time.time()
    print(f"用时{end_time - start_time}秒")
    print("end of create ################################################")


create_project()
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
    print(code.name, code.code_list[0]['code_content'], code.code_list[0]['code_index'])

inspect_template_list = cofable.load_inspection_templates_from_dbfile('pro_test1.db')
for template in inspect_template_list:
    print(template.name, template.host_oid_list, template.host_group_oid_list, template.inspection_code_oid_list)
