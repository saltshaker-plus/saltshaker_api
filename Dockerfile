FROM python:3.6.6-alpine
MAINTAINER  yongpeng1 for sina as <yueyongyue@sina.cn>
ENV TZ "Asia/Shanghai"
ENV S "saltshaker.conf"

RUN set -xe \
    && echo "https://mirror.tuna.tsinghua.edu.cn/alpine/v3.4/main" > /etc/apk/repositories \
    && apk --no-cache add gcc \
                      linux-headers \
                      libc-dev \
                      git \
                      tzdata \
    && git clone https://github.com/saltshaker-plus/saltshaker_api.git -b master /data0/saltshaker_api \
    && pip install -r /data0/saltshaker_api/requirements.txt \
    && mkdir -p /var/log/saltshaker_plus \
    && mkdir -p /var/log/gunicorn \
    && echo "${TZ}" > /etc/timezone \
    && ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && pip install git+https://github.com/Supervisor/supervisor@master

CMD cd /data0/saltshaker_api/ && \
sed -i "s/\(MYSQL_HOST = \).*/\1${MYSQL_HOST}/g" ${S} && \
sed -i "s/\(MYSQL_PORT = \).*/\1${MYSQL_PORT}/g" ${S} && \
sed -i "s/\(MYSQL_USER = \).*/\1${MYSQL_USER}/g" ${S} && \
sed -i "s/\(MYSQL_PASSWORD = \).*/\1${MYSQL_PASSWORD}/g" ${S} && \
sed -i "s/\(MYSQL_DB = \).*/\1${MYSQL_DB}/g" ${S} && \
sed -i "s/\(MYSQL_CHARSET = \).*/\1${MYSQL_CHARSET}/g" ${S} && \
sed -i "s/\(REDIS_HOST = \).*/\1${REDIS_HOST}/g" ${S} && \
sed -i "s/\(REDIS_PORT = \).*/\1${REDIS_PORT}/g" ${S} && \
sed -i "s/\(REDIS_PASSWORD = \).*/\1${REDIS_PASSWORD}/g" ${S} && \
sed -i "s/\(BROKER_HOST = \).*/\1${BROKER_HOST}/g" ${S} && \
sed -i "s/\(BROKER_PORT = \).*/\1${BROKER_PORT}/g" ${S} && \
sed -i "s/\(BROKER_USER = \).*/\1${BROKER_USER}/g" ${S} && \
sed -i "s/\(BROKER_PASSWORD = \).*/\1${BROKER_PASSWORD}/g" ${S} && \
#sed -i "s/\(BROKER_VHOST = \).*/\1${BROKER_VHOST}/g" ${S} && \
sed -i "s/\(FROM_ADDR = \).*/\1${FROM_ADDR}/g" ${S} && \
sed -i "s/\(MAIL_PASSWORD = \).*/\1${MAIL_PASSWORD}/g" ${S} && \
sed -i "s/\(SMTP_SERVER = \).*/\1${SMTP_SERVER}/g" ${S} && \
sed -i "s/\(SMTP_PORT = \).*/\1${SMTP_PORT}/g" ${S} && \
supervisord -c supervisord.conf
EXPOSE 9000
