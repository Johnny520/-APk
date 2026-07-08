# -*- coding: utf-8 -*-
"""API 密钥与全局配置。key 由 App 设置页写入，未填写时走免 key 兜底源。"""
import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    # 在 App 设置页填入你在各免费平台注册的 key
    "apibyte_key": "",        # https://www.apibyte.cn  （工商基础，免费注册）
    "xxapi_key": "",          # https://xxapi.cn        （股东/变更，免费注册）
    "jisuapi_key": "",        # https://www.jisuapi.com （工商/股东/变更/高管，字段极全，免费注册）
    "juhe_key": "",           # https://apis.juhe.cn    （对外投资等，注册后送额度）
    "tianyancha_key": "",     # 天眼查开放平台 https://openapi.tianyancha.com （分支等，需申请）
    "qcc_key": "",            # 企查查开放平台 https://openapi.qcc.com （全维度，需企业认证）
    "custom_apis": [],        # 自定义源列表：[{name, url, key, header, mapping}]
    "timeout": 12,            # 单次请求超时(秒)
    "cache_days": 3,          # 本地缓存有效期(天)
    "enable_scrape": True,    # 无 key 时是否启用免费网页抓取兜底（能爬才爬）
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def set_key(name, value):
    cfg = load_config()
    cfg[name] = value
    save_config(cfg)
    return cfg
