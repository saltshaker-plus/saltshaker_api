# -*- coding:utf-8 -*-
from flask import abort, jsonify
from common.db import DB
from common.saltstack_api import SaltAPI
import uuid
import base64
from common.log import loggers
from common.redis import RedisTool
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from datetime import datetime

logger = loggers()


def uuid_prefix(prefix):
    str_uuid = str(uuid.uuid1())
    s_uuid = ''.join(str_uuid.split("-"))
    return prefix + "-" + s_uuid


def salt_api_for_product(product_id):
    db = DB()
    status, result = db.select_by_id("product", product_id)
    db.close_mysql()
    if status is True:
        if result:
            product = result
        else:
            return {"status": False, "message": "product %s does not exist" % product_id}
    else:
        return {"status": False, "message": result}
    salt_api = SaltAPI(
        url=product.get("salt_master_url"),
        user=product.get("salt_master_user"),
        passwd=product.get("salt_master_password")
    )
    return salt_api


# 重新定义flask restful 400错误
def custom_abort(http_status_code, *args, **kwargs):
    if http_status_code == 400:
        if kwargs:
            for key in kwargs["message"]:
                parameter = key
        else:
            parameter = "unknown"
        abort(jsonify({"status": False, "message": "The specified %s parameter does not exist" % parameter}))
    return abort(http_status_code)


# 生成秘钥对
def generate_key_pair():
    # 伪随机数生成器
    random_generator = Random.new().read
    # rsa算法生成实例
    rsa = RSA.generate(1024, random_generator)
    # 私钥
    private_key = rsa.exportKey()
    RedisTool.setex("private_key", 24 * 60 * 60, private_key)
    # 公钥
    public_key = rsa.publickey().exportKey()
    RedisTool.setex("public_key", 24 * 60 * 60, public_key)


# 解密RSA
def rsa_decrypt(decrypt_text):
    try:
        random_generator = Random.new().read
        private_key = RedisTool.get("private_key")
        rsa_key = RSA.importKey(private_key)
        cipher = Cipher_pkcs1_v1_5.new(rsa_key)
        text = cipher.decrypt(base64.b64decode(decrypt_text), random_generator)
        return text
    except Exception as e:
        logger.error("Decrypt rsa error: %s" % e)
        return False


# 加密RSA
def rsa_encrypt(encrypt_text):
    try:
        public_key = RedisTool.get("public_key")
        rsa_key = RSA.importKey(public_key)
        cipher = Cipher_pkcs1_v1_5.new(rsa_key)
        text = base64.b64decode(cipher.encrypt(encrypt_text))
        return text
    except Exception as e:
        logger.error("Encrypt rsa error: %s" % e)
        return False


# UTC转本地时间
def utc_to_local(utc):
    utc_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    utc_tm = datetime.strptime(utc, utc_format)
    local_tm = datetime.fromtimestamp(0)
    utc_dtm = datetime.utcfromtimestamp(0)
    offset = local_tm - utc_dtm
    local = utc_tm + offset
    return local.strftime("%Y-%m-%d %H:%M:%S")


# 本地时间转UTC
def local_to_utc(local):
    local_format = "%Y-%m-%d %H:%M:%S"
    local_tm = datetime.strptime(local, local_format)
    utc = datetime.utcfromtimestamp(local_tm.timestamp())
    return utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
