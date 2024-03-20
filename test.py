import cofable

if __name__ == '__main__':
    global_info_obj = cofable.GlobalInfo()  # 创建全局信息类，用于存储所有资源类的对象
    global_info_obj.load_all_data_from_sqlite3()  # 首先加载数据库，加载所有资源（若未指定数据库文件名称，则默认为"cofable_default.db"）
    if len(global_info_obj.project_obj_list) == 0:  # 如果项目为空，默认先自动创建一个名为default的项目
        project_default = cofable.Project(global_info=global_info_obj)
        global_info_obj.project_obj_list.append(project_default)
        project_default.save()
    main_window_obj = cofable.MainWindow(width=800, height=480, title='CofAble', global_info=global_info_obj)  # 创建程序主界面
    main_window_obj.show()
    
