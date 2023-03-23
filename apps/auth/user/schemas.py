#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : chengshuang
@Contact : chengshuang@qudoor.cn
@File    : schema.py
@Software: PyCharm
@Time    : 2023/2/28 10:39
"""

from pydantic import BaseModel


class UserInfo(BaseModel):
    id: int
    username: str
    is_superuser: bool

    class Config:
        orm_mode = True


class Password(BaseModel):
    password: str
    password_new: str
