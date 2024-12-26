#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding=utf-8
# module name: cofnet
# author: Cof-Lee <cof8007@gmail.com>
# this module uses the GPL-3.0 open source protocol
# update: 2024-11-17

"""
★术语解析:
ip                      ipv4地址，如 10.1.1.2 ，不含掩码（也可写为ip_address）       类型: str
cidr                    ipv4地址块，网段及掩码位数 ，如 10.1.0.0/16                  类型: str
maskint                 ipv4掩码数字型，如 24 ，子网掩码位数                         类型: int
maskbyte                ipv4掩码字节型，如 255.255.255.0 ，子网掩码                 类型: str
netseg                  ipv4网段，如 10.1.0.0 ，不含掩码                           类型: str
hostseg                 ipv4主机号，一个ip地址去除网段后，剩下的部分（十进制数值）       类型: int
ip_with_maskint         ip/子网掩码位数 的格式，如 10.1.1.2/24                      类型: str
wildcard_mask           反掩码，也叫通配符掩码，如 0.0.0.255                         类型: str

ipv6                    ipv6地址，如 FD00:1234::abcd ，不含前缀长度（也可写为ipv6_address）                        类型: str
cidrv6                  ipv6地址块，网段及前缀长度 ，如 FD00:1234::/64                                           类型: str
ipv6_full               ipv6地址完全展开式，非缩写形式，如 FD00:2222:3333:4444:5555:6666:0077:8888 ，不含前缀长度    类型: str
ipv6_short              ipv6地址缩写式，全0块缩写形式，如 FD00::8888 ，不含前缀长度                                 类型: str
ipv6_seg                ipv6地址块（2字节为一块），如 FD00                                                       类型: str
ipv6_prefix             ipv6地址前缀，网段，如 FD00:: ，不含前缀长度                                              类型: str
ipv6_prefix_len         ipv6地址前缀长度 ，前缀大小，地址块bit位数，如 64                                          类型: int
ipv6_with_prefix_len    ipv6地址前带缀长度 的表示格式，如 FD00::33/64                                            类型: str

★规定：
凡是以 is_ 开头的用于判断的函数，只返回True或False两个值，不报错，不抛出异常

★作者:
李茂福（英文名Cof-Lee）
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import re


# #################################  start of module's function  ##############################
# #### ipv4 ####
def is_ip_addr(input_str: str) -> bool:
    """
    判断 输入的字符串 是否为 ipv4地址（不带掩码），返回bool值，是则返回True，否则返回False。例如：
    输入 "10.99.1.1"  返回  True
    输入  "10.99.1.1/24"  返回  False，纯ipv4地址不能带掩码
    """
    seg_list = input_str.split(".")
    if len(seg_list) != 4:
        return False
    if seg_list[0].isdigit():
        if 0 > int(seg_list[0]) or int(seg_list[0]) > 255:
            return False
    else:
        return False
    if seg_list[1].isdigit():
        if 0 > int(seg_list[1]) or int(seg_list[1]) > 255:
            return False
    else:
        return False
    if seg_list[2].isdigit():
        if 0 > int(seg_list[2]) or int(seg_list[2]) > 255:
            return False
    else:
        return False
    if seg_list[3].isdigit():
        if 0 > int(seg_list[3]) or int(seg_list[3]) > 255:
            return False
    else:
        return False
    return True


def is_cidr(input_str: str) -> bool:
    """
    判断 输入字符串 是否为 cidr地址块，返回bool值，是则返回True，否则返回False
    输入 "10.99.1.0/24" 输出 True
    输入 "10.99.1.1/24" 输出 False ，不是正确的cidr地址块写法，24位掩码，的最后一字节必须为0
    """
    netseg_maskint_seg_list = input_str.split("/")
    if len(netseg_maskint_seg_list) != 2:
        return False
    if not netseg_maskint_seg_list[1].isdigit():
        return False
    if int(netseg_maskint_seg_list[1]) > 32 or int(netseg_maskint_seg_list[1]) < 0:
        return False
    ipv4_seg_list = netseg_maskint_seg_list[0].split(".")
    if len(ipv4_seg_list) != 4:
        return False
    if ipv4_seg_list[0].isdigit():
        if 0 > int(ipv4_seg_list[0]) or int(ipv4_seg_list[0]) > 255:
            return False
    else:
        return False
    if ipv4_seg_list[1].isdigit():
        if 0 > int(ipv4_seg_list[1]) or int(ipv4_seg_list[1]) > 255:
            return False
    else:
        return False
    if ipv4_seg_list[2].isdigit():
        if 0 > int(ipv4_seg_list[2]) or int(ipv4_seg_list[2]) > 255:
            return False
    else:
        return False
    if ipv4_seg_list[3].isdigit():
        if 0 > int(ipv4_seg_list[3]) or int(ipv4_seg_list[3]) > 255:
            return False
    else:
        return False
    netseg_int = int(ipv4_seg_list[0]) << 24 | int(ipv4_seg_list[1]) << 16 | int(ipv4_seg_list[2]) << 8 | int(ipv4_seg_list[3])
    netseg_int_and = netseg_int & (0xFFFFFFFF << (32 - int(netseg_maskint_seg_list[1])))
    if netseg_int != netseg_int_and:
        return False
    return True


def is_netseg_with_maskbyte(netseg: str, maskbyte: str) -> bool:
    """
    判断 输入字符串 是否为 正确的 网段及子网掩码，返回bool值，是则返回True，否则返回False，例：
    输入 "10.99.1.0","255.255.255.0"  输出 True
    输入 "10.99.1.3","255.255.255.0"  输出 False，原因是24位掩码时，网段最后8位（最后一字节）必须为全0
    """
    if not is_ip_addr(netseg):
        return False
    if not is_maskbyte(maskbyte):
        return False
    netseg_int_of_calc = get_netseg_int(netseg, maskbyte)
    if netseg_int_of_calc != ip_or_maskbyte_to_int(netseg):
        return False
    else:
        return True


def is_ip_with_maskint(input_str: str) -> bool:
    """
    判断 输入字符串 是否为 ip/子网掩码位数 的格式，返回bool值，是则返回True，否则返回False，例：
    输入 "10.99.1.55/24" 输出 True
    输入 "10.99.1.55/255.255.255.0" 输出 False，原因是 / 后面只能接数字，不能接子网掩码byte型
    """
    ip_maskint_seg_list = input_str.split("/")
    if len(ip_maskint_seg_list) != 2:
        return False
    if not ip_maskint_seg_list[1].isdigit():
        return False
    if int(ip_maskint_seg_list[1]) > 32 or int(ip_maskint_seg_list[1]) < 0:
        return False
    ipv4_seg_list = ip_maskint_seg_list[0].split(".")
    if len(ipv4_seg_list) != 4:
        return False
    if ipv4_seg_list[0].isdigit():
        if 0 > int(ipv4_seg_list[0]) or int(ipv4_seg_list[0]) > 255:
            return False
    else:
        return False
    if ipv4_seg_list[1].isdigit():
        if 0 > int(ipv4_seg_list[1]) or int(ipv4_seg_list[1]) > 255:
            return False
    else:
        return False
    if ipv4_seg_list[2].isdigit():
        if 0 > int(ipv4_seg_list[2]) or int(ipv4_seg_list[2]) > 255:
            return False
    else:
        return False
    if ipv4_seg_list[3].isdigit():
        if 0 > int(ipv4_seg_list[3]) or int(ipv4_seg_list[3]) > 255:
            return False
    else:
        return False
    return True


def is_ip_range(input_str: str) -> bool:
    """
    判断 输入字符串 是否为 ip地址范围，返回bool值，是则返回True，否则返回False
    输入 "10.99.1.33-55" 输出 True
    输入 "10.99.1.22-10" 输出 False ，不是正确的地址范围，首ip大于了尾ip（首ip可以等于尾ip）
    """
    seg_list = input_str.split(".")
    if len(seg_list) != 4:
        return False
    if seg_list[0].isdigit():
        if 0 > int(seg_list[0]) or int(seg_list[0]) > 255:
            return False
    else:
        return False
    if seg_list[1].isdigit():
        if 0 > int(seg_list[1]) or int(seg_list[1]) > 255:
            return False
    else:
        return False
    if seg_list[2].isdigit():
        if 0 > int(seg_list[2]) or int(seg_list[2]) > 255:
            return False
    else:
        return False
    if seg_list[3].isdigit():  # 第4段为 数字-数字 的形式，不能是单个数字
        return False
    range_list = seg_list[3].split("-")
    if len(range_list) == 2:
        if range_list[0].isdigit():
            if 0 > int(range_list[0]) or int(range_list[0]) > 255:
                return False
        else:
            return False
        if range_list[1].isdigit():
            if 0 > int(range_list[1]) or int(range_list[1]) > 255:
                return False
        else:
            return False
        if int(range_list[0]) > int(range_list[1]):
            return False
        return True
    else:
        return False


def is_ip_range_2(input_str: str) -> bool:
    """
    判断 输入的字符串 是否为 ip地址范围，返回bool值，是则返回True，否则返回False
    输入 "10.99.1.33-10.99.1.55" 输出 True
    输入 "10.99.1.22-10.99.1.10" 输出 False ，不是正确的地址范围，首ip大于了尾ip（首ip可以等于尾ip）
    """
    ip_list = input_str.split("-")
    if len(ip_list) != 2:
        return False
    if not is_ip_addr(ip_list[0]):
        return False
    if not is_ip_addr(ip_list[1]):
        return False
    if ip_or_maskbyte_to_int(ip_list[0]) > ip_or_maskbyte_to_int(ip_list[1]):
        return False
    return True


def is_maskbyte(input_str: str) -> bool:
    """
    判断输入的字符串 是否为 maskbyte掩码字节型，返回bool值，是则返回True，否则返回False
    输入 "255.255.0.0" 输出 True
    输入 "10.99.1.0" 输出 False，这是不一个正确的子网掩码
    """
    if not is_ip_addr(input_str):
        return False
    maskbyte_to_int32 = ip_or_maskbyte_to_int(input_str)
    # 大力出奇迹，只能一个一个地对比了（可以把常用的掩码放前面）
    if maskbyte_to_int32 == 0xFFFFFF00:  # 24 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFFFF:  # 32 位掩码
        return True
    if maskbyte_to_int32 == 0x00000000:  # 0 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFFFC:  # 30 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFF000:  # 20 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFF800:  # 21 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFC00:  # 22 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFE00:  # 23 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFF80:  # 25 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFFC0:  # 26 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFFE0:  # 27 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFFF0:  # 28 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFFF8:  # 29 位掩码
        return True
    if maskbyte_to_int32 == 0xFFF00000:  # 12 位掩码
        return True
    if maskbyte_to_int32 == 0xFFF80000:  # 13 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFC0000:  # 14 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFE0000:  # 15 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFF0000:  # 16 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFF8000:  # 17 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFC000:  # 18 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFE000:  # 19 位掩码
        return True
    if maskbyte_to_int32 == 0xFF000000:  # 8 位掩码
        return True
    if maskbyte_to_int32 == 0xFF800000:  # 9 位掩码
        return True
    if maskbyte_to_int32 == 0xFFC00000:  # 10 位掩码
        return True
    if maskbyte_to_int32 == 0xFFE00000:  # 11 位掩码
        return True
    if maskbyte_to_int32 == 0xFFFFFFFE:  # 31 位掩码
        return True
    if maskbyte_to_int32 == 0x80000000:  # 1 位掩码
        return True
    if maskbyte_to_int32 == 0xC0000000:  # 2 位掩码
        return True
    if maskbyte_to_int32 == 0xE0000000:  # 3 位掩码
        return True
    if maskbyte_to_int32 == 0xF0000000:  # 4 位掩码
        return True
    if maskbyte_to_int32 == 0xF8000000:  # 5 位掩码
        return True
    if maskbyte_to_int32 == 0xFC000000:  # 6 位掩码
        return True
    if maskbyte_to_int32 == 0xFE000000:  # 7 位掩码
        return True
    return False


def maskint_to_maskbyte(maskint: int) -> str:
    """
    将子网掩码数字型 转为 子网掩码字节型，例如：
    输入 16 输出 "255.255.0.0"
    输入 24 输出 "255.255.255.0
    【输入错误会抛出Exception异常】
    """
    if maskint < 0 or maskint > 32:
        raise Exception("子网掩码数值应在[0-32]", maskint)
    mask = [0, 0, 0, 0]
    i = 0
    while maskint >= 8:
        mask[i] = 255
        i += 1
        maskint -= 8
    if i < 4:
        mask[i] = 255 - (2 ** (8 - maskint) - 1)
    return ".".join(map(str, mask))


def maskint_to_wildcard_mask(maskint: int) -> str:
    """
    将子网掩码数字型 转为 反掩码，例如：
    输入 16 输出 "0.0.255.255"
    输入 24 输出 "0.0.0.255
    【输入错误会抛出Exception异常】
    """
    if maskint < 0 or maskint > 32:
        raise Exception("子网掩码数值应在[0-32]", maskint)
    wildcard_mask = [255, 255, 255, 255]
    i = 0
    while maskint >= 8:
        wildcard_mask[i] = 0
        i += 1
        maskint -= 8
    if i < 4:
        wildcard_mask[i] = 2 ** (8 - maskint) - 1
    return ".".join(map(str, wildcard_mask))


def local__mask_seg_to_cidr(mask_seg: str) -> int:
    """
    将掩码其中一个字节的数字 转为 二进制数最开头的1的个数, 例如：
    输入 "192" 输出 2 ，即 1100 0000
    输入 "248" 输出 5 ，即 1111 1000
    输入 "255" 输出 8 ，即 1111 1111
    """
    mask_seg_1_number = 0
    mask_seg_int = int(mask_seg)
    while mask_seg_int != 0:
        mask_seg_1_number += 1
        mask_seg_int = (mask_seg_int << 1) & 0xFF
    return mask_seg_1_number


def maskbyte_to_maskint(maskbyte: str) -> int:
    """
    将子网掩码字节型 转为 子网掩码数字型，例如：
    输入 "255.255.255.0" 输出 24
    输入 "255.255.0.0"   输出 16
    【输入错误会抛出Exception异常】
    """
    if not is_ip_addr(maskbyte):
        raise Exception("不是正确的子网掩码,E1", maskbyte)
    mask_seg_list = maskbyte.split(".")
    mask_seg_index = 0
    maskint = 0
    while mask_seg_list[mask_seg_index] == "255":
        maskint += 8
        mask_seg_index += 1
        if mask_seg_index == 4:
            break
    if mask_seg_index < 4 and mask_seg_list[mask_seg_index] != "":
        maskint += local__mask_seg_to_cidr(mask_seg_list[mask_seg_index])  # 依赖 local_mask_seg_to_cidr()
    if maskbyte != maskint_to_maskbyte(maskint):
        raise Exception("不是正确的子网掩码,E2", maskbyte)
    return maskint


def ip_to_hex_string(ip_addresss: str) -> str:
    """
    将ip地址转为十六进制表示，例如：
    输入 "10.99.1.254" 输出 "0A6301FE"
    【输入错误会抛出Exception异常】
    """
    if not is_ip_addr(ip_addresss):
        raise Exception("不是正确的ip地址,E1", ip_addresss)
    return "".join("{:0>2X}".format(int(ip_seg_int)) for ip_seg_int in ip_addresss.split("."))


def ip_or_maskbyte_to_int(ip_or_mask: str) -> int:
    """
    将 ip地址或掩码byte型 转为 32 bit的数值，例如：
    输入 "255.255.255.0" 输出 4294967040
    输入 "192.168.1.1"   输出 3232235777
    【输入错误会抛出Exception异常】
    """
    if not is_ip_addr(ip_or_mask):
        raise Exception("不是正确的ip地址或掩码", ip_or_mask)
    seg_list = ip_or_mask.split(".")
    ip_mask_int = int(seg_list[0]) << 24 | int(seg_list[1]) << 16 | int(seg_list[2]) << 8 | int(seg_list[3])
    return ip_mask_int


def ip_or_maskbyte_to_binary_with_space(ip_or_maskbyte: str) -> str:
    """
    将 ip地址或掩码byte型 转为 二进制数表示，★每8位数插入1个空格，例如：
    输入 "255.255.255.0" 输出 "11111111 11111111 11111111 00000000"
    输入 "192.168.1.1"   输出 "11000000 10101000 00000001 00000001"
    【输入错误会抛出Exception异常】
    """
    if not is_ip_addr(ip_or_maskbyte):
        raise Exception("不是正确的ip地址或掩码", ip_or_maskbyte)
    return " ".join("{:0>8b}".format(int(ip_seg_int)) for ip_seg_int in ip_or_maskbyte.split("."))


def get_maskint_with_space(maskint: int) -> int:
    """
    根据子网掩码位数，返回带空格时的二进制的掩码总长度，即每8位加1个空格字符，
    一般和 ip_or_maskbyte_to_binary_with_space() 配置使用，给子网掩码bit位突出显示时使用
    【输入错误会抛出Exception异常】
    """
    if not isinstance(maskint, int):
        raise Exception("不是正确的子网掩码位数", maskint)
    if maskint > 32 or maskint < 0:
        raise Exception("不是正确的子风掩码位数", maskint)
    if maskint > 24:
        return maskint + 3
    elif maskint > 16:
        return maskint + 2
    elif maskint > 8:
        return maskint + 1
    else:
        return maskint


def int32_to_ip(int32: int) -> str:
    """
    将 32bit数值 转为 ipv4地址，例如:
    输入 174260481 输出 "10.99.1.1"
    【输入错误会抛出Exception异常】
    """
    if int32 < 0 or int32 > 4294967295:
        raise Exception("ipv4地址数值应在[0-4294967295]范围内", int32)
    ipaddress = [0xFF & (int32 >> 24), 0xFF & (int32 >> 16), 0xFF & (int32 >> 8), 0xFF & int32]
    return ".".join(map(str, ipaddress))


def get_netseg_int(ip_address: str, maskintorbyte: str) -> int:
    """
    根据 子网掩码 获取ip地址的 网段（int值），子网掩码可为int型或byte型，例如：
    输入 "10.99.1.1","24"             输出 174260480 （输出值是网段的int值）
    输入 "10.99.1.1","255.255.255.0"  输出 174260480 （输出值是网段的int值）
    【输入错误会抛出Exception异常】
    """
    if not is_ip_addr(ip_address):
        raise Exception("不是正确的ip地址", ip_address)
    maskintorbyte_seg = str(maskintorbyte).split(".")
    if len(maskintorbyte_seg) == 1:
        if not maskintorbyte_seg[0].isdigit():
            raise Exception("不是正确的子网掩码", maskintorbyte_seg)
        if int(maskintorbyte_seg[0]) < 0 or int(maskintorbyte_seg[0]) > 32:
            raise Exception("子网掩码数值应在[0-32]范围内", maskintorbyte_seg)
        else:
            maskint2bin = 0xFFFFFFFF << (32 - int(maskintorbyte_seg[0]))
            return ip_or_maskbyte_to_int(ip_address) & maskint2bin
    elif len(maskintorbyte_seg) == 4:
        if not is_maskbyte(maskintorbyte):
            raise Exception("不是正确的子网掩码", maskintorbyte)
        maskint2bin = 0xFFFFFFFF << (32 - int(maskbyte_to_maskint(maskintorbyte)))
        return ip_or_maskbyte_to_int(ip_address) & maskint2bin
    else:
        raise Exception("不是正确的子网掩码", maskintorbyte)


def get_netseg_byte(ip: str, maskintorbyte: str) -> str:
    """
    根据 子网掩码 获 取ip地址的 网段（byte值），子网掩码可为int型或byte型，例如：
    输入 "10.99.1.1","24"             输出 10.99.1.0
    输入 "10.99.1.1","255.255.255.0"  输出 10.99.1.0
    依赖本模块的2个函数:  get_netseg_int() 以及 int32_to_ip()
    【输入错误会抛出Exception异常】
    """
    try:
        return int32_to_ip(get_netseg_int(ip, maskintorbyte))
    except Exception as err:
        raise err


def get_netseg_byte_c(cidr: str) -> str:
    """
    根据 cidr 获取ip地址的 网段（byte值），子网掩码可为int型或byte型，例如：
    输入 "10.99.1.1/24"     输出 10.99.1.0
    依赖上面的2个函数:  get_netseg_int() 以及 int32_to_ip()
    【输入错误会抛出Exception异常】
    """
    if not is_cidr(cidr):
        raise Exception("不是正确的cidr,", cidr)
    netseg_maskint_seg_list = cidr.split("/")
    try:
        return int32_to_ip(get_netseg_int(netseg_maskint_seg_list[0], netseg_maskint_seg_list[1]))
    except Exception as err:
        raise err


def get_hostseg_int(ip: str, maskintorbyte: str) -> int:
    """
    根据 子网掩码 获 取ip地址的 主机号（int值），可得知此ip为此网段第几个ip（从0开始），子网掩码可为int型或byte型，例如：
    输入 "10.99.1.145","24"             输出 145 （主机号为第4个字节的值）
    输入 "10.99.1.145","255.255.255.0"  输出 145
    【输入错误会抛出Exception异常】
    """
    if not is_ip_addr(ip):
        raise Exception("不是正确的ip地址,E1", ip)
    maskintorbyte_seg = str(maskintorbyte).split(".")
    if len(maskintorbyte_seg) == 1:
        if int(maskintorbyte_seg[0]) < 0 or int(maskintorbyte_seg[0]) > 32:
            raise Exception("子网掩码数值应在[0-32]", maskintorbyte_seg)
        else:
            maskint2bin = 0xFFFFFFFF << (32 - int(maskintorbyte_seg[0]))
            return ip_or_maskbyte_to_int(ip) & ~maskint2bin
    elif len(maskintorbyte_seg) == 4:
        if not is_maskbyte(maskintorbyte):
            raise Exception("不是正确的掩码,E2", maskintorbyte)
        else:
            maskint2bin = 0xFFFFFFFF << (32 - int(maskbyte_to_maskint(maskintorbyte)))
            return ip_or_maskbyte_to_int(ip) & ~maskint2bin
    else:
        raise Exception("不是正确的掩码,E3", maskintorbyte)


def get_hostseg_num(maskint: int) -> int:
    """
    根据子网掩码位数获取主机号可表示的主机ip数量
    例如：24位的掩码，主机号为8位，可表示的主机ip数量为256
    """
    if maskint > 32 or maskint < 0:
        raise Exception("不是正确的子网掩码位数", maskint)
    else:
        return (0xFFFFFFFF >> maskint) + 1


def is_ip_in_cidr(ip: str, cidr: str) -> bool:
    """
    判断 ip地址 是否在 网段cidr内，此ip是否属于某网段地址块，返回bool值: True表示ip在网段内，False表示不在网段内
    输入 "10.99.1.1","10.99.1.0/24"  输出 True
    输入 "10.99.3.1","10.99.1.0/24"  输出 False
    ★若输入格式有误则返回False，且不会报错
    """
    if not is_ip_addr(ip):
        # raise Exception("不是正确的ip地址,E1", ip)
        return False
    if not is_cidr(cidr):
        # raise Exception("不是正确的cidr地址块,E2", cidr)
        return False
    netseg_maskint = cidr.split("/")
    netseg_int_of_ip = get_netseg_int(ip, netseg_maskint[1])
    netseg_int_of_cidr = get_netseg_int(netseg_maskint[0], netseg_maskint[1])
    if netseg_int_of_ip == netseg_int_of_cidr:
        return True
    else:
        return False


def is_ip_in_net_maskbyte(ip: str, netseg: str, maskbyte: str) -> bool:
    """
    判断 ip地址 是否在 网段 net maskbyte内，是否属于某网段地址块，返回bool值: True表示ip在网段内，False不在网段内
    输入 "10.99.1.1","10.99.1.0","255.255.255.0"  输出 True
    输入 "10.99.3.1","10.99.1.0","255.255.255.0"  输出 False
    ★若输入格式有误则返回False，且不会报错
    """
    if not is_ip_addr(ip):
        # raise Exception("不是正确的ip地址,E1", ip)
        return False
    if not is_netseg_with_maskbyte(netseg, maskbyte):
        # raise Exception("不是正确的网段及子网掩码,E2", netseg, maskbyte)
        return False
    netseg_int_of_ip = get_netseg_int(ip, maskbyte)
    netseg_int_of_cidr = get_netseg_int(netseg, maskbyte)
    if netseg_int_of_ip == netseg_int_of_cidr:
        return True
    else:
        return False


def is_ip_in_range(targetip: str, start_ip: str, end_ip: str) -> bool:
    """
    判断 ip地址 是否在 ip地址范围内，返回bool值: True表示ip在ip-range内，False不在ip-range内
    输入 "10.99.1.88","10.99.1.1","10.99.2.22"  输出 True
    输入 "10.99.1.88","10.99.1.1","10.99.1.22"  输出 False
    ★若输入格式有误则返回False，且不会报错
    """
    if not is_ip_addr(targetip):
        # raise Exception("不是正确的ip地址,E1", targetip)
        return False
    if not is_ip_addr(start_ip):
        # raise Exception("不是正确的ip地址,E2", start_ip)
        return False
    if not is_ip_addr(end_ip):
        # raise Exception("不是正确的ip地址,E3", end_ip)
        return False
    if ip_or_maskbyte_to_int(end_ip) >= ip_or_maskbyte_to_int(targetip) >= ip_or_maskbyte_to_int(start_ip):
        return True
    else:
        return False


# ################ ipv6 ################
def is_ipv6_addr(input_str: str) -> bool:
    """
    判断 输入字符串 是否为 ipv6地址（不带前缀长度），返回bool值，是则返回True，否则返回False，例：
    输入 "FD00::1"   输出 True
    输入 "FD00::1/64" 输出 False，原因是带了前缀长度
    """
    seg_list_sp = input_str.split("/")
    if len(seg_list_sp) > 1:
        return False
    match_pattern = r'\:{2,}'
    ret = re.findall(match_pattern, input_str, flags=re.I)
    if ret.__len__() >= 2:  # 如果 输入的地址 有超过2个 :: 块，则为错误的ipv6地址，ipv6地址最多只能有1个 ::
        return False
    match_pattern2 = r'\:{3,}'
    ret2 = re.findall(match_pattern2, input_str, flags=re.I)
    if ret2.__len__() >= 1:  # 如果 输入的地址 有连续三个及以上数量的冒号，如 ::: ，则为错误的ipv6地址，最多只有2个连续的冒号
        return False
    seg_list = input_str.split("::")
    if len(seg_list) == 1:  # 没有 "::" 0位缩写，则必须有8块
        seg_list0 = input_str.split(":")
        if len(seg_list0) != 8:
            return False
        for ipv6_seg in seg_list0:
            try:
                if int(ipv6_seg, base=16) > 0xFFFF or int(ipv6_seg, base=16) < 0:
                    return False
            except ValueError:
                return False
        return True
    elif len(seg_list) == 2:  # 只有1个 "::" 0位缩写，则全0缩写:: 至少为2个块
        if seg_list[0] != "" and seg_list[1] != "":  # 例如 FD00:1234::ffff
            seg_list_head = seg_list[0].split(":")
            seg_list_tail = seg_list[1].split(":")
            if len(seg_list_head) + len(seg_list_tail) > 6:
                return False
            for ipv6_seg in seg_list_head:
                try:
                    if int(ipv6_seg, base=16) > 0xFFFF or int(ipv6_seg, base=16) < 0:
                        return False
                except ValueError:
                    return False
            for ipv6_seg in seg_list_tail:
                try:
                    if int(ipv6_seg, base=16) > 0xFFFF or int(ipv6_seg, base=16) < 0:
                        return False
                except ValueError:
                    return False
            return True
        elif seg_list[0] == "" and seg_list[1] != "":  # 例如 ::ffff
            seg_list_tail = seg_list[1].split(":")
            if len(seg_list_tail) > 6:
                return False
            for ipv6_seg in seg_list_tail:
                try:
                    if int(ipv6_seg, base=16) > 0xFFFF or int(ipv6_seg, base=16) < 0:
                        return False
                except ValueError:
                    return False
            return True
        elif seg_list[0] != "" and seg_list[1] == "":  # 例如 FD00::
            seg_list_head = seg_list[0].split(":")
            if len(seg_list_head) > 6:
                return False
            for ipv6_seg in seg_list_head:
                try:
                    if int(ipv6_seg, base=16) > 0xFFFF or int(ipv6_seg, base=16) < 0:
                        return False
                except ValueError:
                    return False
            return True
        else:  # :: 的情况（全0）
            return True
    else:
        return False


def is_ipv6_with_prefix_len(input_str: str) -> bool:
    """
    判断 输入字符串 是否为 ipv6地址带前缀长度的格式，返回bool值，是则返回True，否则返回False
    输入 "FD00::/64" 输出 True
    输入 "FD00::11" 输出 False ，没有带前缀长度
    """
    seg_list = input_str.split("/")
    if len(seg_list) != 2:
        return False
    if not is_ipv6_addr(seg_list[0]):
        return False
    if seg_list[1].isdigit():
        if 0 > int(seg_list[1]) or int(seg_list[1]) > 128:
            return False
        else:
            return True
    else:
        return False


def local__convert_to_ipv6_seg_full(ipv6_seg: str) -> str:
    """
    将ipv6的地址块（2字节为一块）转为4个字符的16进制数，返回的十六进制数都用大写字母表示
    输入 "fd"  输出 "00FD"
    """
    if len(ipv6_seg) == 1:
        return "000" + ipv6_seg.upper()
    elif len(ipv6_seg) == 2:
        return "00" + ipv6_seg.upper()
    elif len(ipv6_seg) == 3:
        return "0" + ipv6_seg.upper()
    elif len(ipv6_seg) == 4:
        return ipv6_seg.upper()
    else:
        raise Exception("不是正确的ipv6地址块（2字节为一块）,E1", ipv6_seg)


def convert_to_ipv6_full(ipv6_address: str) -> str:
    """
    输入ipv6地址，转为完全展开式的ipv6地址（非缩写形式），返回的十六进制数都用大写字母表示
    输入 "FD00:123::11" 输出 "FD00:0123:0000:0000:0000:0000:0000:0011"
    【输入错误会抛出Exception异常】
    """
    if not is_ipv6_addr(ipv6_address):
        raise Exception("不是正确的ipv6地址,E1", ipv6_address)
    ipv6_full_seg_list = []
    seg_list = ipv6_address.split("::")
    if len(seg_list) == 1:  # 没有 "::" 0位缩写，则必须有8块
        seg_list0 = ipv6_address.split(":")
        for ipv6_seg in seg_list0:
            ipv6_full_seg_list.append(local__convert_to_ipv6_seg_full(ipv6_seg))
        return ":".join(ipv6_full_seg_list)
    else:  # 只有1个 "::" 0位缩写，每个::缩写至少为2个块
        if seg_list[0] != "" and seg_list[1] != "":  # 例如 FD00:1234::ffff
            seg_list_head = seg_list[0].split(":")
            seg_list_tail = seg_list[1].split(":")
            len_seg_of_abbr = len(seg_list_head) + len(seg_list_tail)  # :: 全0缩写代表的块数
            for ipv6_seg in seg_list_head:
                ipv6_full_seg_list.append(local__convert_to_ipv6_seg_full(ipv6_seg))
            for seg_zero in range(8 - len_seg_of_abbr):
                ipv6_full_seg_list.append("0000")
            for ipv6_seg in seg_list_tail:
                ipv6_full_seg_list.append(local__convert_to_ipv6_seg_full(ipv6_seg))
            return ":".join(ipv6_full_seg_list)
        elif seg_list[0] == "" and seg_list[1] != "":  # 例如 ::ffff
            seg_list_tail = seg_list[1].split(":")
            for seg_zero in range(8 - len(seg_list_tail)):
                ipv6_full_seg_list.append("0000")
            for ipv6_seg in seg_list_tail:
                ipv6_full_seg_list.append(local__convert_to_ipv6_seg_full(ipv6_seg))
            return ":".join(ipv6_full_seg_list)
        elif seg_list[0] != "" and seg_list[1] == "":  # 例如 FD00::
            seg_list_head = seg_list[0].split(":")
            for ipv6_seg in seg_list_head:
                ipv6_full_seg_list.append(local__convert_to_ipv6_seg_full(ipv6_seg))
            for seg_zero in range(8 - len(seg_list_head)):
                ipv6_full_seg_list.append("0000")
            return ":".join(ipv6_full_seg_list)
        else:  # ::的情况（全0）
            return "0000:0000:0000:0000:0000:0000:0000:0000"


def local__convert_to_ipv6_seg_short(ipv6_seg: str) -> str:
    """
    将ipv6的地址块（2字节为一块）转为缩写形式的地址块（最前面的0省略），返回的十六进制数都用大写字母表示
    输入 "00FD"  输出 "FD"
    """
    return str(hex(int(ipv6_seg, base=16))).replace("0x", "").upper()


def convert_to_ipv6_short(ipv6_address: str) -> str:
    """
    输入ipv6地址，转为缩写形式的ipv6地址（全0块缩写为::），返回的十六进制数都用大写字母表示
    输入 "FD00:0123:0000:0000:0000:0000:0000:0011" 输出 "FD00:123::11"
    【输入错误会抛出Exception异常】
    """
    if not is_ipv6_addr(ipv6_address):
        raise Exception("不是正确的ipv6地址,E1", ipv6_address)
    # 先转为完全展开形式的ipv6地址，再转为缩写形式
    ipv6_full_address_seg_list = convert_to_ipv6_full(ipv6_address).split(":")
    ipv6_full_address_short = []
    ipv6_full_address_short_re = []
    for ipv6_seg in ipv6_full_address_seg_list:
        ipv6_seg_short = local__convert_to_ipv6_seg_short(ipv6_seg)
        ipv6_full_address_short.append(ipv6_seg_short)
        if ipv6_seg_short != "0":
            ipv6_full_address_short_re.append("1")
        else:
            ipv6_full_address_short_re.append("0")
    # 使用re去查找最长的全0块
    match_pattern = r'(?:0)+'
    ret2 = re.finditer(match_pattern, "".join(ipv6_full_address_short_re), flags=re.I)
    ret_list = []
    ret_len_list = []
    for ret_item in ret2:
        ret_len_list.append(ret_item.span()[1] - ret_item.span()[0])
        ret_list.append(ret_item)
    if len(ret_len_list) != 0:  # 查询到有全0块
        longgest = max(ret_len_list)
        if longgest >= 2:  # 至少要有2个全0块才缩写
            max_index = ret_len_list.index(longgest)  # 查询到第1个最长全0块的索引
            ipv6_full_address_short_head = ipv6_full_address_short[0:ret_list[max_index].span()[0]]
            ipv6_full_address_short_tail = ipv6_full_address_short[ret_list[max_index].span()[1]:]
            if len(ipv6_full_address_short_head) != 0 and len(ipv6_full_address_short_tail) != 0:
                return ":".join(ipv6_full_address_short_head) + "::" + ":".join(ipv6_full_address_short_tail)
            elif len(ipv6_full_address_short_head) == 0 and len(ipv6_full_address_short_tail) != 0:
                return "::" + ":".join(ipv6_full_address_short_tail)
            elif len(ipv6_full_address_short_head) != 0 and len(ipv6_full_address_short_tail) == 0:
                return ":".join(ipv6_full_address_short_head) + "::"
            else:
                return "::"
        else:
            return ":".join(ipv6_full_address_short)
    else:  # 没有查询到全0块
        return ":".join(ipv6_full_address_short)


def get_ipv6_prefix(ipv6_address: str, ipv6_prefix_len: int) -> str:
    """
    获取ipv6地址前缀（不带/前缀长度）
    输入 "FD00:0234::11, 64"                            输出 "FD00:234::"
    输入 "FD00:0000:0000:0000:0000:0000:0000:8811, 80"  输出 "FD00::"
    输入 "FD00:0000:0000:0000:000A:0000:0000:8811, 80"  输出 "FD00::A:0:0:0"  不带前缀长度时，最后3个0不能删除
    【输入错误会抛出Exception异常】
    """
    if not is_ipv6_addr(ipv6_address):
        raise Exception("不是正确的ipv6地址,E1", ipv6_address)
    if 0 > ipv6_prefix_len or ipv6_prefix_len > 128:
        raise Exception("不是正确的ipv6地址前缀大小,E2", ipv6_prefix_len)
    # 先转为完全展开形式的ipv6地址，再去截取前缀
    ipv6_full_address = convert_to_ipv6_full(ipv6_address)
    ipv6_full_address_seg_list = ipv6_full_address.split(":")
    prefix_seg_num = ipv6_prefix_len // 16
    prefix_last_seg_remainder = ipv6_prefix_len % 16
    if prefix_last_seg_remainder == 0:
        ipv6_prefix_seg_list = ipv6_full_address_seg_list[0:prefix_seg_num]
    else:
        ipv6_prefix_seg_list = ipv6_full_address_seg_list[0:prefix_seg_num]
        ipv6_prefix_last_seg = int(ipv6_full_address_seg_list[prefix_seg_num], base=16) >> (16 - prefix_last_seg_remainder) << (
                16 - prefix_last_seg_remainder)
        ipv6_prefix_seg_list.append(str(hex(ipv6_prefix_last_seg)).replace("0x", ""))
    if len(ipv6_prefix_seg_list) == 8:
        return convert_to_ipv6_short(":".join(ipv6_prefix_seg_list))
    else:
        for i in range(8 - len(ipv6_prefix_seg_list)):
            ipv6_prefix_seg_list.append("0000")
        return convert_to_ipv6_short(":".join(ipv6_prefix_seg_list))


def get_ipv6_prefix_cidrv6(ipv6_address: str, ipv6_prefix_len: int) -> str:
    """
    获取ipv6地址前缀（带/前缀长度），前缀本身若有多个全0块也不缩写为::
    输入 "FD00:0234::11, 64"  输出 "FD00:234::/64"
    输入 "FD00:0000:0000:0000:0000:0000:0000:8811, 80"  输出 "FD00::/80"
    输入 "FD00:0000:0000:0000:000A:0000:0000:8811, 80"  输出 "FD00::A/80"
    """
    ipv6_prefix = get_ipv6_prefix(ipv6_address, ipv6_prefix_len)
    ipv6_prefix_split = ipv6_prefix.split("::")
    if len(ipv6_prefix_split) < 2:  # 没有"::"
        not_drop_seg_num = 8 - ((128 - ipv6_prefix_len) // 16)
        new_ipv6_seg_list = ipv6_prefix_split[0].split(":")[0:not_drop_seg_num]
        return ":".join(new_ipv6_seg_list) + "/" + str(ipv6_prefix_len)
    else:  # 有一个"::"
        ipv6_seg_tail_list = ipv6_prefix_split[1].split(":")
        not_drop_seg_num = len(ipv6_seg_tail_list) - ((128 - ipv6_prefix_len) // 16)
        new_ipv6_seg_tail_list = ipv6_seg_tail_list[0:not_drop_seg_num]
        return ipv6_prefix_split[0] + "::" + ":".join(new_ipv6_seg_tail_list) + "/" + str(ipv6_prefix_len)


# #################################  end of module's function  ##############################
if __name__ == '__main__':
    print("Hello, this is cofnet.py")
