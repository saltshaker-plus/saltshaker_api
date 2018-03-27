### Saltshaker_plus Restful API

1. 安装依赖
    pip install -r requirements.txt
    
2. 导入FLASK_APP　环境变了以便使用　Flask CLI 工具；
　　路径为所部属的app的路径
   export FLASK_APP=/root/work/github/saltshaker_api/app.py
3. 初始化数据库 键入超级管理员用户名和密码
　　flask initdb
　　输出如下：
        Enter the initial administrators username [admin]: 
        Enter the initial Administrators password: 
        Repeat for confirmation: 
        Create user table is successful
        Create role table is successful
        Create acl table is successful
        Create groups table is successful
        Create product table is successful
        Create audit_log table is successful
        Create event table is successful
        Init role successful
        Init user successful
        Successful

