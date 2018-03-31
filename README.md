### Saltshaker_plus Restful API

#### **要求 python > 3.0**
#### **要求 Mysql >= 5.7**

````
1. 安装依赖
    #pip install -r requirements.txt
````
````
2. 导入FLASK_APP　环境变量以便使用Flask CLI 工具,路径为所部署的app的路径
    #export FLASK_APP=/root/work/github/saltshaker_api/app.py
````
````
3. 初始化相关信息及数据库 键入超级管理员用户名和密码
    #flask init
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
````
````
4. 启动Flask App
    python /root/work/github/saltshaker_api/app.py
````

### Saltshaker 交流学习QQ群:622806083
![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/qq.png)