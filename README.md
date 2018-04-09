### Saltshaker_plus Restful API

#### **API文档见Wiki https://github.com/yueyongyue/saltshaker_api/wiki**


#### **前端项目 https://github.com/yueyongyue/saltshaker_frontend**
#### **要求 python > 3.0**
#### **要求 Mysql >= 5.7.8**
#### **MariaDB > 10.0.1 对于Json的处理方式不同，SQL语句不同，不建议使用**

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

#### **GitLab 使用说明**
官方配置gitfs说明 请查看此[链接](https://docs.saltstack.com/en/latest/topics/tutorials/gitfs.html#simple-configuration)
需要 pygit2 或者 GitPython 包用于支持git, 如果都存在优先选择pygit2
````
Saltstack SLS 文件采用 GitLab 进行存储及管理,使用前务必已经存在 GitLab (其他存储方式陆续支持)

配置master,添加如下

fileserver_backend:
  - roots
  - git               # git 和 roots 表示既支持本地又支持git 先后顺序决定了当sls文件冲突时,使用哪个sls文件(谁在前面用谁的)
gitfs_remotes:
  - http://test.com.cn:9000/root/salt_sls.git # GitLab 项目地址 格式https://<user>:<password>@<url>
gitfs_base: master    # git 分支默认master

````
#### **Roots 本地文件**
````
支持Roots模式的fileserver, 由于支持多产品多个独立master的管理方式, 采用Roots模式的服务将使用Rsync进行数据的同步及管理
````

### Saltshaker 交流学习QQ群:622806083
![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/qq.png)