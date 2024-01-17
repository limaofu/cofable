import time
import cofable

print('业务流程：')
# 首先创建一个项目
pro_test1 = cofable.Project(name='pro_test1', description='cofable测试项目1')

# 再创建资源
cred_host1 = cofable.Credential(name='cred_host1', username='root', password='xxxxxx', project_id=pro_test1.id)

host_1 = cofable.Host(name='host_01', address='10.99.1.233', ssh_port='22', project_id=pro_test1.id)
host_1.add_credential(cred_host1.id)  # 主机添加登录凭据

inspect_code_test1 = cofable.InspectionCode(name='inspect_code_test1', code_source='local',
                                            project_id=pro_test1.id)
inspect_code_test1.add_code(r'df -Th')  # 巡检代码对象添加要执行的命令
inspect_code_test1.add_code(r'ls -lh')  # 巡检代码对象添加要执行的命令

# 创建巡检模板
inspection_template_test1 = cofable.InspectionTemplate(name='template1', enabled_crond_job=True,
                                                       project_id=pro_test1.id)
inspection_template_test1.add_host(host_1.id)
inspection_template_test1.add_inspection_code(inspect_code_test1.id)
if inspection_template_test1.enabled_crond_job:
    cron_trigger1 = cofable.CronDetectionTrigger(
        inspection_template_id=inspection_template_test1.id,
        project_id=pro_test1.id)
    inspection_template_test1.cron_detection_trigger_id = cron_trigger1.id
    # 开始执行监视任务，达到触发条件就执行相应巡检模板
    cron_trigger1.start_crontab_job()
else:
    pass  # 手动触发巡检模板
