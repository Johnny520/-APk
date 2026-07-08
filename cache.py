# -*- coding: utf-8 -*-
"""极简 SQLite 缓存，按 (source, key) 存 JSON，过期自动失效。"""
import os
import sqlite3
import json
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kv "
        "(k TEXT PRIMARY KEY, v TEXT, ts REAL)"
    )
    return conn


def get(k, max_age_days=3):
    try:
        conn = _conn()
        row = conn.execute("SELECT v, ts FROM kv WHERE k=?", (k,)).fetchone()
        conn.close()
        if not row:
            return None
        v, ts = row
        if (time.time() - ts) > max_age_days * 86400:
            return None
        return json.loads(v)
    except Exception:
        return None


def set(k, v, max_age_days=3):
    try:
        conn = _conn()
        conn.execute(
            "INSERT OR REPLACE INTO kv VALUES (?,?,?)",
            (k, json.dumps(v, ensure_ascii=False), time.time()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def cache_key(source, ident):
    return f"{source}:{ident}"


def clear_all():
    """清空全部本地缓存。"""
    try:
        conn = _conn()
        conn.execute("DELETE FROM kv")
        conn.commit()
        conn.close()
    except Exception:
        pass
