# Saltshaker API

Saltshaker是基于saltstack开发的以Web方式进行配置管理的运维工具，简化了saltstack的日常使用，丰富了saltstack的功能，支持多Master的管理。此项目为Saltshaker的后端Restful API，需要结合前端项目[Saltshaker_frontend](https://github.com/saltshaker-plus/saltshaker_frontend)。
## 架构图
![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/Saltshaker_Plus.jpg)
## Dashboard
![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/dashboard.png)

## 指导手册

- [要求](#要求)
- [安装](#安装)
- [配置Salt Master](#配置salt-master)
- [Restful API](#restful-api)
- [功能介绍](#功能介绍)
    - [Job](#job)
        - [Job创建](#job创建)
        - [Job历史](#job历史)
        - [Job管理](#job管理)
    - [Minion管理](#minion管理)
        - [状态信息](#状态信息)
        - [Key管理](#key管理)
        - [Grains](#grains)
    - [主机管理](#主机管理)
    - [分组管理](#分组管理)
    - [文件管理](#文件管理)
    - [执行命令](#执行命令)
        - [Shell](#shell)
        - [State](#state)
        - [Pillar](#pillar)
    - [产品线管理](#产品线管理)
    - [ACL管理](#acl管理)
    - [系统管理](#acl管理)
        - [用户管理](#用户管理)
        - [角色管理](#角色管理)
        - [操作日志](#操作日志)
        - [系统工具](#系统工具)

## 要求

- Python >= 3.6
- Mysql >= 5.7.8 （支持Json的Mysql都可以）
- Redis（无版本要求）
- RabbitMQ （无版本要求）
- Python 软件包见requirements.txt
- Supervisor (4.0.0.dev0 版本 默认pip安装的不支持python3) 请使用此命令安装：pip install git+https://github.com/Supervisor/supervisor@master
- GitLab >= 9.0

## 安装

准备工作（相关依赖及配置见saltshaker.conf）：
- 安装Redis： 建议使用Docker命令如下：
```sh
$ docker run -p 0.0.0.0:6379:6379 --name saltshaker_redis -e REDIS_PASSWORD=saltshaker -d yueyongyue/redis:08
```
- 安装RabbitMQ： 建议使用Docker命令如下：
        
```sh
$ docker run -d --name saltshaker_rabbitmq -e RABBITMQ_DEFAULT_USER=saltshaker -e RABBITMQ_DEFAULT_PASS=saltshaker -p 15672:15672 -p 5672:5672 rabbitmq:3-management
```
- 安装Mysql： 初始化系统管理员 用户名：admin 密码：admin
```sh
$ docker run -p 0.0.0.0:3306:3306 --name saltshaker_mysql -e MYSQL_ROOT_PASSWORD=123456 -d yueyongyue/saltshaker_mysql:10 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```
    
### 使用Docker镜像安装
1. 后端API服务
```sh
$ docker run -d -p 0.0.0.0:9000:9000 --name saltshaker_api \
-e REDIS_HOST=192.168.10.100 \
-e REDIS_PORT=6379 \
-e REDIS_PASSWORD=saltshaker \
-e MYSQL_HOST=192.168.10.100 \
-e MYSQL_PORT=3306 \
-e MYSQL_USER=root \
-e MYSQL_PASSWORD=123456 \
-e MYSQL_DB=saltshaker_plus \
-e MYSQL_CHARSET=utf8 \
-e BROKER_HOST=192.168.10.100 \
-e BROKER_PORT=5672 \
-e BROKER_USER=saltshaker \
-e BROKER_PASSWORD=saltshaker \
-e FROM_ADDR=test@saltshaker.com \
-e MAIL_PASSWORD=123345 \
-e SMTP_SERVER=smtp.saltshaker.com \
-e SMTP_PORT=25 \
yueyongyue/saltshaker_api:1.12.1
```
- REDIS_HOST：       Redis主机地址
- REDIS_PORT：       Redis端口
- REDIS_PASSWORD：   Redis密码
- MYSQL_HOST：       Mysql数据库地址
- MYSQL_PORT：       Mysql端口
- MYSQL_USER：       Mysql用户名
- MYSQL_PASSWORD:    Mysql密码
- MYSQL_DB：         Mysql数据库名
- MYSQL_CHARSET：    Mysql字符集
- BROKER_HOST：      RabbitMQ地址
- BROKER_PORT：      RabbitMQ端口
- BROKER_USER：      RabbitMQ用户
- BROKER_PASSWORD：  RabbitMQ密码
- FROM_ADDR：        邮箱地址用于发生邮件
- MAIL_PASSWORD：    邮箱密码
- SMTP_SERVER：      SMTP服务器地址
- SMTP_PORT：        SMTP服务器端口

2. 前端服务
```sh
$ docker run -d -p 0.0.0.0:80:80 --name saltshaker_frontend \
-e DOMAIN=192.168.10.100  \
-e API_ADDR=192.168.10.100 \
-e Nginx_PROXY_PASS=192.168.10.100:9000 \
yueyongyue/saltshaker_frontend:1.12
```
- DOMAIN: 部署服务器的IP地址（最终通过这个地址进行浏览器访问）
- API_ADDR： 后端API服务器的地址
- Nginx_PROXY_PASS：后端API服务器的地址加端口

### 手动部署
安装Saltshaker，你需要首先准备Python 3的环境（假定项目clone到你的家目录即$HOME下面，若果不是请对应修改相关路径）

1. 下载:

    ```sh
    $ cd $HOME
    $ git clone https://github.com/yueyongyue/saltshaker_api.git
    ```

2. 安装依赖:

    ```sh
    $ pip install -r requirements.txt
    ```

3. 导入FLASK_APP环境变量以便使用Flask CLI工具,路径为所部署的app的路径

    ```sh
    $ export FLASK_APP=$Home/saltshaker_api/app.py
    ```

4. 初始化数据库表及相关信息，键入超级管理员用户名和密码（数据库的配置见saltshaker.conf，请确保数据库可以连接并已经创建对应的数据库）

    ```sh
    $ mkdir /var/log/saltshaker_plus
    $ flask init
    ```
    
    ```
    输出如下：
        Enter the initial administrators username [admin]: admin
        Enter the initial Administrators password: 
        Repeat for confirmation: 
        Create user table is successful
        Create role table is successful
        Create acl table is successful
        Create groups table is successful
        Create product table is successful
        Create audit_log table is successful
        Create event table is successful
        Create cmd_history table is successful
        Create host table is successful
        Create grains table is successful
        Create period_task table is successful
        Create period_result table is successful
        Create period_audit table is successful
        Create sls table is successful
        Init 超级管理员 role successful
        Init 普通用户 role successful
        Init 产品管理员 role successful
        Init 用户管理员 role successful
        Init 访问控制管理员 role successful
        Init user successful
        Successful
    ```
    也可以直接导入数据库文件saltshaker_plus.sql, 初始化管理员用户名：admin 密码：admin
    ```sh
    mysql> source $HOME/saltshaker_api/saltshaker_plus.sql;
    ```

5. 启动Flask App, 成功启动后会启动9000的端口
    - 开发模式
    
        ```sh
        $ python $Home/saltshaker_api/app.py
        ```
    - Gunicorn模式
    
        ```sh
        $ cd $Home/saltshaker_api/ && gunicorn -c gun.py app:app
        ```
    - 生产模式
    
        ```sh
        supervisord.conf 里面的directory配置项修改为自己对应的代码路径
        $ /usr/local/bin/supervisord -c $Home/saltshaker_api/supervisord.conf
        ```
    
6. 启动Celery （使用生产模式的忽略此步骤，因为在Supervisor里面已经启动Celery）

    ```sh
    $ cd $Home/saltshaker_api/ && celery -A app.celery worker --loglevel=info
    ```
7. 结合前端项目
    ```
    https://github.com/yueyongyue/saltshaker_frontend
    ```
 
## 配置Salt Master （如下是以 CentOS 7 版本进行安装配置的，其他版本的操作系统请替换对应的命令，以下操作都是在salt master服务器上完成）
1. 安装salt-api 具体安装方法请查看官方文档（[https://repo.saltstack.com/](https://docs.saltstack.com/en/latest/topics/tutorials/gitfs.html#simple-configuration)）
    ```sh
    sudo yum install salt-api
    ```
    
2. 创建salt api 认证用户名密码，使用pam认证方式
    ```sh
    sudo useradd admin          # 必须是admin，如果是其他用户，需要对应修改$HOME/saltshaker_api/saltapi.conf里面的admin
    sudo passwd admin           # 记住admin的密码，稍后配置产品线的时候需要填写
    ```
        
3. 配置saltstack api
    拷贝 saltshaker_api/saltapi.conf 到 master配置文件下，开启salt-api的Restful接口(端口为8000)
    ```sh
    sudo cp $HOME/saltshaker_api/saltapi.conf /etc/salt/master.d/
    sudo systemctl restart salt-master
    sudo systemctl restart salt-api
    ```

4. 使用GitLab作为FileServer:
    官方配置gitfs说明 请查看此[链接](https://docs.saltstack.com/en/latest/topics/tutorials/gitfs.html#simple-configuration)需要 pygit2 或者 GitPython 包用于支持git, 如果都存在优先选择pygit2
    Saltstack state及pillar SLS文件采用GitLab进行存储及管理，使用前务必已经存在GitLab，如下配置在/etc/salt/master进行添加修改
    
    ```sh
    fileserver_backend:
      - roots
      - git   # git和roots表示既支持本地又支持git 先后顺序决定了当sls文件冲突时,使用哪个sls文件(谁在前面用谁的)
      
    gitfs_remotes:
      - http://test.com.cn:9000/root/salt_sls.git: # GitLab项目地址 格式https://<user>:<password>@<url>
        - mountpoint: salt://  # 很重要，否则在使用file.managed等相关文件管理的时候会找不到GitLab上的文件 https://docs.saltstack.com/en/latest/topics/tutorials/gitfs.html
      
    gitfs_base: master   # git分支默认master
    
    pillar_roots:         
      base:
        - /srv/pillar
        
    ext_pillar:  # 配置pillar使用gitfs, 需要配置top.sls
      - git:
        - http://test.com.cn:9000/root/salt_pillar.git：
          - mountpoint: salt://
    ```

5. 后端文件服务器文件更新:

    - master 配置文件修改如下内容 (不建议)
    
        ```sh
        loop_interval: 1      # 默认时间为60s, 使用后端文件服务,修改gitlab文件时将不能及时更新, 可根据需求缩短时间
        ```
    - Saltshaker页面通过Webhook提供刷新功能, 使用reactor监听event, 当event的tag中出现gitfs/update的时候更新fiilerserve
    
        ```sh
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
        ```
    
## Restful API

Restful API文档见Wiki: https://github.com/yueyongyue/saltshaker_api/wiki

## Saltshaker 交流学习QQ群:622806083
![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/qq.png)
## 运维架构技术 交流学习QQ群:991904631
![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/qq01.JPG)
## Saltshaker 论坛
http://project-help.cn/forum-4.htm

## 功能介绍
### Job
#### Job创建

Job创建，主要是以Job的方式进行日常的配管工作，避免重复性的手动执行配管操作，同时支持定时及周期性的Job

并行为0                                      | 立即        | 定时        | 周期 	
--------------------------------------------|-----------:|------------:|-----------:
一次                                         | 重开、删除  |  重开、删除  |  无
周期                                         | 无         |  无         |  暂停周期、继续周期、删除

并行为非0                                    | 立即        | 定时        | 周期 	
--------------------------------------------|-----------:|------------:|-----------:
一次                                         | 暂停并行、继续并行、重开、删除	  |  暂停并行、继续并行、重开、删除  |  无
周期                                         | 无         |  无         |  暂停周期、继续周期、删除

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/job_create.gif)

#### Job历史

Job历史，通过saltstack event获取相关saltshaker事件供用户查看及检索（系统工具里面的event要开启才会有，每增加一个产品线要重启一次）

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/job_history.gif)

#### Job管理

Job管理，如果执行了某些长时间驻留的任务，如ping，top这种，可以在里面进行kill

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/job_manage.gif)

### Minion管理
#### 状态信息

可以查看minion的状态信息

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/minion_status.gif)

#### Key管理

可以对minion key 进行管理，接受key会自动同步minion到主机，删除后自动从主机，分组中删除

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/minion_key.gif)

#### Grains

展示minion Grains 信息；此功能根据salt master已经接受的minion进行Grains的生成，`同步Grains`使用了异步方式进行同步，同步之前请确保celery worker已经启动

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/minion_grains.gif)


### 主机管理

在key管理里面点击`Accepted`后，此minion id会自动同步到主机管理，如果不是在页面点击的`Accepted`可以使用`同步主机`进行同步，或者发现管理的minion于主机的数量不相同，也可以点击`同步主机`同步，此功能会根据salt maste已经接受的minion进行主机的同步

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/host.gif)

### 分组管理

对主机进行分组，以便进行批量操作

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/group.gif)

### 文件管理

使用基于gitfs的方式进行日常的文件管理；state、template、pillar等文件都可以放到里面；支持添加、编辑、删除、上传等操作；使用webhook对gitfs文件进行更新

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/fs01.gif)

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/fs02.gif)

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/fs03.gif)

### 执行命令
#### Shell

根据分组执行对应的shell命令

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/shell.gif)

#### State

根据分组执行对应的state

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/state.gif)

#### Pillar

根据分组执行对应的pillar(只有pillar形式的sls,执行才有效果)

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/pillar.gif)

### 产品线管理
`项目初始完成后首先需要配置的`
支持多产品线的管理，不同产品线使用不同的salt-master,可以分别进行管理，方便多master的接入
 - 产品线名：为管理的salt-master起个名字
 - 描述：描述
 - Master ID：salt-master所在的服务器也是要部署salt-minion的，此ID为这台服务器上`salt-minion的ID`，用于管理salt-master服务器
 - Master API 地址：salt-api的地址；如：http://192.168.10.10:8000
 - Master API 用户名：salt-api的用户名
 - Master API 密码： salt-api的密码
 - 文件服务器： 现只支持GitLab模式，默认勾就可以了，选择GitLab后saltstack的后端文件服务将是使用GitLab
 - GitLab 地址：Gitlab服务的地址；如：http://git.saltshaker.com.cn
 - GitLab API 版本：此版本为GitLab API的版本，不是GitLab的版本，填`4`即可
 - GitLab Token：访问GitLab的Token，可以去GitLab的页面生成
 - GitLab State 项目：salt state项目的地址；如：`xxx/项目名`
 - GitLab Pillar 项目：salt pillar项目的地址；如：`xxx/项目名`
 
![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/product.gif)

### ACL管理

对执行的shell进行ACL,避免执行敏感命令，如reboot、shutdown等，现在只支持`黑名单（拒绝的,只有Shell有效，SLS的文件暂时不支持）`

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/acl.gif)

### 系统管理
#### 用户管理

对注册进来的用户，进行产品线的分配、主机组的分配、ACL的分配、角色的分配等

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/user.gif)

#### 角色管理

系统预定义的角色，不能删除修改，如有需要可以扩展角色

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/role.gif)

#### 操作日志

记录用户日常操作

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/log.gif)

#### 系统工具

event工具用于对saltstack event进行记录，每添加一个产品线重启一次，如果发现celery worker的数量的数量多于产品线数量，job历史可能重复

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/tools.gif)
