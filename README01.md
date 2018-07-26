# Saltshaker API

Saltshaker是基于saltstack开发的以Web方式进行配置管理的运维工具，简化了saltstack的日常使用，丰富了saltstack的功能，支持多Master的管理。此项目为Saltshaker的后端Restful API，需要结合前端项目[Saltshaker_frontend](https://github.com/yueyongyue/saltshaker_frontend)。

![image](https://github.com/yueyongyue/saltshaker_api/blob/master/screenshots/dashboard.png)

## 指导手册

- [要求](#要求)
- [安装](#安装)
- [Salt_Master配置](#Salt_Master配置)
- [Restful_API文档](#Restful_API文档)
- [功能介绍](#功能介绍)
    - [Job管理](#Job管理)
        - [Job创建](#Job创建)
        - [Job历史](#Job历史)
        - [Job管理](#Job管理)
    - [Minion管理](#Minion管理)
        - [状态信息](#状态信息)
        - [Key管理](#Key管理)
        - [Grains](#Grains)
    - [主机管理](#主机管理)
    - [分组管理](#分组管理)
    - [文件管理](#文件管理)
    - [执行命令](#执行命令)
        - [Shell](#Shell)
        - [State](#State)
        - [Pillar](#Pillar)

## 要求

- Python >= 3.6
- Mysql >= 5.7.8 （支持Json的Mysql都可以）
- Redis（无版本要求）
- RabbitMQ （无版本要求）
- Python 软件包见requirements.txt
- Supervisor (4.0.0.dev0 版本)
- GitLab >= 9.0

## 安装

安装Saltshaker，你需要首先准备Python环境

1. 准备工作（相关依赖及配置见saltshaker.conf）:
    - 安装Redis： 建议使用Docker命令如下：
    
        ```sh
        $ docker run -p 0.0.0.0:6379:6379 --name saltshaker_redis -e REDIS_PASSWORD=saltshaker -d yueyongyue/redis:05
        ```

    - 安装RabbitMQ： 建议使用Docker命令如下：
    
        ```sh
        $ docker run -d --name saltshaker_rabbitmq -e RABBITMQ_DEFAULT_USER=saltshaker -e RABBITMQ_DEFAULT_PASS=saltshaker -p 15672:15672 -p 5672:5672 rabbitmq:3-management
        ```
    - 安装Mysql: 请自行安装

2. 下载:

    ```sh
    $ git clone https://github.com/yueyongyue/saltshaker_api.git
    ```

3. 安装依赖:

    ```sh
    $ pip install -r requirements.txt
    ```

4. 导入FLASK_APP环境变量以便使用Flask CLI工具,路径为所部署的app的路径

    ```sh
    $ export FLASK_APP=$Home/saltshaker_api/app.py
    ```

5. 初始化数据库表及相关信息，键入超级管理员用户名和密码（数据库的配置见saltshaker.conf，请确保数据库可以连接并已经创建对应的数据库）

    ```sh
    $ flask init
    ```
    
    ```
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
    ```

6. 启动Flask App
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
        $ /usr/local/bin/supervisord -c $Home/saltshaker_api/supervisord.conf
        ```
    
7. 启动Celery （使用生产模式的忽略此步骤，因为在Supervisor里面已经启动Celery）

    ```sh
    $ cd $Home/saltshaker_api/ && celery -A app.celery worker --loglevel=info
    ```
    
## Salt_Master配置

1. 使用GitLab作为FileServer:
    官方配置gitfs说明 请查看此[链接](https://docs.saltstack.com/en/latest/topics/tutorials/gitfs.html#simple-configuration)需要 pygit2 或者 GitPython 包用于支持git, 如果都存在优先选择pygit2
    Saltstack state及pillar SLS文件采用GitLab进行存储及管理，使用前务必已经存在GitLab
    
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

2. 后端文件服务器文件更新:

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
    
## Restful_API文档

Restful API文档见Wiki: https://github.com/yueyongyue/saltshaker_api/wiki

## Benchmarks

Gin uses a custom version of [HttpRouter](https://github.com/julienschmidt/httprouter)

[See all benchmarks](/BENCHMARKS.md)

Benchmark name                              | (1)        | (2)         | (3) 		    | (4)
--------------------------------------------|-----------:|------------:|-----------:|---------:
**BenchmarkGin_GithubAll**                  | **30000**  |  **48375**  |     **0**  |   **0**
BenchmarkAce_GithubAll                      |   10000    |   134059    |   13792    |   167
BenchmarkBear_GithubAll                     |    5000    |   534445    |   86448    |   943
BenchmarkBeego_GithubAll                    |    3000    |   592444    |   74705    |   812
BenchmarkBone_GithubAll                     |     200    |  6957308    |  698784    |  8453
BenchmarkDenco_GithubAll                    |   10000    |   158819    |   20224    |   167
BenchmarkEcho_GithubAll                     |   10000    |   154700    |    6496    |   203
BenchmarkGocraftWeb_GithubAll               |    3000    |   570806    |  131656    |  1686
BenchmarkGoji_GithubAll                     |    2000    |   818034    |   56112    |   334
BenchmarkGojiv2_GithubAll                   |    2000    |  1213973    |  274768    |  3712
BenchmarkGoJsonRest_GithubAll               |    2000    |   785796    |  134371    |  2737
BenchmarkGoRestful_GithubAll                |     300    |  5238188    |  689672    |  4519
BenchmarkGorillaMux_GithubAll               |     100    | 10257726    |  211840    |  2272
BenchmarkHttpRouter_GithubAll               |   20000    |   105414    |   13792    |   167
BenchmarkHttpTreeMux_GithubAll              |   10000    |   319934    |   65856    |   671
BenchmarkKocha_GithubAll                    |   10000    |   209442    |   23304    |   843
BenchmarkLARS_GithubAll                     |   20000    |    62565    |       0    |     0
BenchmarkMacaron_GithubAll                  |    2000    |  1161270    |  204194    |  2000
BenchmarkMartini_GithubAll                  |     200    |  9991713    |  226549    |  2325
BenchmarkPat_GithubAll                      |     200    |  5590793    | 1499568    | 27435
BenchmarkPossum_GithubAll                   |   10000    |   319768    |   84448    |   609
BenchmarkR2router_GithubAll                 |   10000    |   305134    |   77328    |   979
BenchmarkRivet_GithubAll                    |   10000    |   132134    |   16272    |   167
BenchmarkTango_GithubAll                    |    3000    |   552754    |   63826    |  1618
BenchmarkTigerTonic_GithubAll               |    1000    |  1439483    |  239104    |  5374
BenchmarkTraffic_GithubAll                  |     100    | 11383067    | 2659329    | 21848
BenchmarkVulcan_GithubAll                   |    5000    |   394253    |   19894    |   609

- (1): Total Repetitions achieved in constant time, higher means more confident result
- (2): Single Repetition Duration (ns/op), lower is better
- (3): Heap Memory (B/op), lower is better
- (4): Average Allocations per Repetition (allocs/op), lower is better
