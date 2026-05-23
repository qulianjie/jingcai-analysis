# -*- coding: utf-8 -*-
"""联赛匹配工具 v2 — 基于 _league_id_map.json 动态查找

三层ID查找（对标 league_map.js 的 getLeagueId()）：
  1. 直接查 _league_id_map[name]
  2. 通过 LEAGUE_NAME_MAP 映射后查
  3. 模糊匹配遍历所有key

文件来源（全部本地，零网络请求）：
  - _league_id_map.json  (29KB, 1286个联赛) — 自动构建的别名→ID映射
  - league_map.json      (59KB)              — 别名映射关系（用于 _league_match）
  - league_name_map.json (22KB)              — 缩写→全称映射（从 league_map.js 提取）
  - leagues_all.json     (70KB)              — liansai.500.com 原始联赛数据

用法:
    from _league_util import get_league_id, _league_match
    lid = get_league_id("日职")      # => "19524"
    lid = get_league_id("英超")      # => "9110"
    if _league_match("英超Premier League", "英超"): ...
"""

import os, json, logging

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 延迟加载缓存
_league_id_map = None
_league_name_map = None
_league_map = None


def _load_league_id_map():
    """加载联赛ID映射（1286个联赛，延迟加载）"""
    global _league_id_map
    if _league_id_map is not None:
        return _league_id_map
    map_path = os.path.join(SCRIPT_DIR, "_league_id_map.json")
    if os.path.exists(map_path):
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                _league_id_map = json.load(f)
        except Exception:
            _league_id_map = {}
    else:
        _league_id_map = {}
    return _league_id_map


def _load_league_name_map():
    """加载缩写→全称映射（从 league_map.js 提取，554条）"""
    global _league_name_map
    if _league_name_map is not None:
        return _league_name_map
    map_path = os.path.join(SCRIPT_DIR, "league_name_map.json")
    if os.path.exists(map_path):
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                _league_name_map = json.load(f)
        except Exception:
            _league_name_map = {}
    else:
        _league_name_map = {}
    return _league_name_map


def _load_league_map():
    """加载别名映射关系（1268条，用于 _league_match 模糊匹配）"""
    global _league_map
    if _league_map is not None:
        return _league_map
    map_path = os.path.join(SCRIPT_DIR, "league_map.json")
    if os.path.exists(map_path):
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                _league_map = json.load(f)
        except Exception:
            _league_map = {}
    else:
        _league_map = {}
    return _league_map


def _normalize(name):
    """标准化联赛名称：去空格"""
    return name.strip() if name else ""


def get_league_id(name):
    """三层联赛ID查找（对标 league_map.js 的 getLeagueId()）
    
    1. 直接查 _league_id_map[name]
    2. 通过 LEAGUE_NAME_MAP 映射全称后查
    3. 模糊遍历所有key
    
    Args:
        name: 联赛名称（如 "日职", "英超Premier League", "J1联赛"）
    
    Returns:
        str: 联赛ID，未找到返回 None
    """
    if not name:
        return None
    
    name = _normalize(name)
    id_map = _load_league_id_map()
    
    # 第一层：直接查找
    if name in id_map:
        return id_map[name]
    
    # 第二层：通过 LEAGUE_NAME_MAP 映射后查
    name_map = _load_league_name_map()
    if name in name_map:
        full_name = name_map[name]
        if full_name in id_map:
            return id_map[full_name]
        league_map = _load_league_map()
        if full_name in league_map:
            for alias in league_map[full_name]:
                if alias in id_map:
                    return id_map[alias]
    
    # 反向查：name_map 的值→键反向映射
    for abbr, full in name_map.items():
        if name == full and abbr in id_map:
            return id_map[abbr]
    
    # 第三层：模糊遍历
    for key, lid in id_map.items():
        if name in key or key in name:
            if len(name) >= 2 and len(key) >= 2:
                return lid
    
    return None


def _league_match(src_league, target_league):
    """模糊匹配两个联赛名称是否指向同一个联赛
    
    先精确匹配，再通过 league_map.json 的映射关系进行模糊匹配。
    
    Args:
        src_league: 源站联赛名称（如 "英超Premier League"）
        target_league: 目标联赛名称（如 "英超"）
    
    Returns:
        bool: 如果两个联赛名称指向同一个联赛则返回 True
    """
    if not src_league or not target_league:
        return False
    
    src = _normalize(src_league)
    tgt = _normalize(target_league)
    
    if src == tgt:
        return True
    
    league_map = _load_league_map()
    
    # 正向：target 的别名列表里是否包含 src
    if tgt in league_map:
        for alias in league_map[tgt]:
            if alias == src:
                return True
            if len(src) >= 2 and len(alias) >= 2:
                if src in alias or alias in src:
                    return True
    
    # 反向：src 的别名列表里是否包含 target
    if src in league_map:
        for alias in league_map[src]:
            if alias == tgt:
                return True
            if len(tgt) >= 2 and len(alias) >= 2:
                if tgt in alias or alias in tgt:
                    return True
    
    # 全面搜索：检查两个名称是否在同一个映射组中
    if tgt in league_map and src in league_map:
        tgt_set = set(league_map[tgt]) | {tgt}
        src_set = set(league_map[src]) | {src}
        if tgt_set & src_set:
            return True
    
    return False


# 向后兼容：旧代码 from _league_util import LEAGUE_ID_MAP
_LEAGUE_ID_MAP_CACHE = None

def _build_legacy_map():
    global _LEAGUE_ID_MAP_CACHE
    if _LEAGUE_ID_MAP_CACHE is not None:
        return _LEAGUE_ID_MAP_CACHE
    _LEAGUE_ID_MAP_CACHE = _load_league_id_map()
    return _LEAGUE_ID_MAP_CACHE

# 动态代理：支持 LEAGUE_ID_MAP.get('英超', '') 和 LEAGUE_ID_MAP['英超']
class _LazyLeagueDict(dict):
    def __init__(self):
        super().__init__()
        self._loaded = False
    def _ensure(self):
        if not self._loaded:
            self.update(_build_legacy_map())
            self._loaded = True
    def __getitem__(self, key):
        self._ensure()
        return super().__getitem__(key)
    def get(self, key, default=None):
        self._ensure()
        return super().get(key, default)
    def __contains__(self, key):
        self._ensure()
        return super().__contains__(key)
    def keys(self):
        self._ensure()
        return super().keys()
    def items(self):
        self._ensure()
        return super().items()
    def values(self):
        self._ensure()
        return super().values()
    def __len__(self):
        self._ensure()
        return super().__len__()
    def __iter__(self):
        self._ensure()
        return super().__iter__()

LEAGUE_ID_MAP = _LazyLeagueDict()
