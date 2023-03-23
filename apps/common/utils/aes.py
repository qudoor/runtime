import base64

from Crypto.Cipher import AES
from django.conf import settings


def aesEncrypt(data):
    '''
    AES的ECB模式加密方法
    :param key: 密钥
    :param data:被加密字符串（明文）
    :return:密文
    '''

    BLOCK_SIZE = 32  # Bytes
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                    chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
    key = str(settings.PWD_ENCRYPTION).encode('utf8')
    # 字符串补位
    data = pad(data)
    cipher = AES.new(key, AES.MODE_ECB)
    # 加密后得到的是bytes类型的数据，使用Base64进行编码,返回byte字符串
    result = cipher.encrypt(data.encode())
    encodestrs = base64.b64encode(result)
    enctext = encodestrs.decode('utf8')
    print(enctext)
    return enctext


def aesDecrypt(passwd):
    '''

    :param key: 密钥
    :param data: 加密后的数据（密文）
    :return:明文
    '''

    key = str(settings.PWD_ENCRYPTION).encode('utf8')
    data = base64.b64decode(passwd)
    cipher = AES.new(key, AES.MODE_ECB)

    unpad = lambda s: s[:-ord(s[len(s) - 1:])]
    # 去补位
    text_decrypted = unpad(cipher.decrypt(data))
    text_decrypted = text_decrypted.decode('utf8')
    print(text_decrypted)
    return text_decrypted
