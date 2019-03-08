FROM mysql:5.7.25
MAINTAINER  yongpeng1 for sina as <yueyongyue@sina.cn>

RUN set -xe \
    && apt-get update \
    && cp /usr/share/zoneinfo/PRC /etc/localtime \
    && apt-get install wget -y \
    && wget -P /docker-entrypoint-initdb.d https://raw.githubusercontent.com/yueyongyue/saltshaker_api/master/saltshaker_plus.sql
