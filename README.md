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
    开发模式：python /root/work/github/saltshaker_api/app.py
    Gunicorn模式： cd /root/work/github/saltshaker_api/ && gunicorn -c gun.py app:app
````
````
5. 启动Celery
    celery -A app.celery worker --loglevel=info
````

#### **GitLab 使用说明 版本要求　GitLab >= 9.0**
官方配置gitfs说明 请查看此[链接](https://docs.saltstack.com/en/latest/topics/tutorials/gitfs.html#simple-configuration)
需要 pygit2 或者 GitPython 包用于支持git, 如果都存在优先选择pygit2
````
Saltstack state及pillar SLS文件采用GitLab进行存储及管理,使用前务必已经存在GitLab(其他存储方式陆续支持)


fileserver_backend:
  - roots
  - git               # git和roots表示既支持本地又支持git 先后顺序决定了当sls文件冲突时,使用哪个sls文件(谁在前面用谁的)
  
gitfs_remotes:
  - http://test.com.cn:9000/root/salt_sls.git: # GitLab项目地址 格式https://<user>:<password>@<url>
    - mountpoint: salt://                      # 很重要，否则在使用file.managed等相关文件管理的时候会找不到GitLab上的文件 https://docs.saltstack.com/en/latest/topics/tutorials/gitfs.html
  
gitfs_base: master    # git分支默认master

pillar_roots:         
  base:
    - /srv/pillar
    
ext_pillar:           # 配置pillar使用gitfs, 需要配置top.sls
  - git:
    - http://test.com.cn:9000/root/salt_pillar.git：
      - mountpoint: salt://

````
#### **后端文件服务器文件更新**
````
1. master 配置文件修改如下内容 (不建议)
    loop_interval: 1      # 默认时间为60s, 使用后端文件服务,修改gitlab文件时将不能及时更新, 可根据需求缩短时间
````
````
2. saltshaker_plus 页面通过hook提供刷新功能, 使用reactor监听event, 当event的tag中出现gitfs/update的时候更新fiilerserver
    a. 在master上开启saltstack reactor
       reactor:
         - 'salt/netapi/hook/gitfs/*':
           - /srv/reactor/gitfs.sls
    b. 编写/srv/reactor/gitfs.sls
        {% if 'gitfs/update' in tag %}
        gitfs_update: 
          runner.fileserver.update
        pillar_update:
          runner.git_pillar.update
        {% endif %}
 
````
````
3. 也可以使用gitlab自带的Webhook功能, 不在赘述
   API接口: POST方法 /saltshaker/api/v1.0/hook/gitfs/update
   验证方法： X-Gitlab-Token
   Token生成见wiki Token生成API
````
#### **Roots 本地文件**
````
支持Roots模式的fileserver, 由于支持多产品多个独立master的管理方式, 采用Roots模式的服务将使用Rsync进行数据的同步及管理
````
#### 功能展示 ####


### Saltshaker 交流学习QQ群:622806083
![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/qq.png)