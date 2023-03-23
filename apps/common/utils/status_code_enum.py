#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Desc: { 项目枚举类模块 }


from enum import Enum


class StatusCodeEnum(Enum):
    """状态码枚举类"""

    OK = (0, '成功')
    ANSIBLE_NOT_RUN = (5001, 'Ansible 未运行')
    ANSIBLE_NOT_DONE = (5002, 'Ansible 未运行完毕')
    ANSIBLE_RUN_ERROR = (5003, 'Ansible 运行失败')

    UNREACHABLE = (50004, '主机不可达')
    FAILED = (50005, '业务失败')

    @property
    def code(self):
        """获取状态码"""
        return self.value[0]

    @property
    def msg(self):
        """获取状态码信息"""
        return self.value[1]
