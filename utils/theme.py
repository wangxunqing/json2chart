# -*- coding: utf-8 -*-
"""
ECharts 主题配置，样式参考 hm-app-analysis 项目 (src/plugin/echarts/theme.json)。
用于统一图表颜色与全局组件样式，使 json2chart 输出与 hm 项目视觉一致。
"""

# 与 hm-app-analysis theme.json 一致的色板（共 12 色）
COLOR_PALETTE = [
    "#48A1FF",
    "#5DD8AD",
    "#FFB74D",
    "#67E0E3",
    "#9FE7B8",
    "#31C5E9",
    "#C5CAE9",
    "#F790A1",
    "#FEDB5B",
    "#FF9F7F",
    "#9B9BFF",
    "#DCE775",
]

# 背景色（透明）
BACKGROUND_COLOR = "rgba(0, 0, 0, 0)"

# 标题样式
TITLE_TEXT_STYLE = {"color": "#5e5e5e"}
TITLE_SUBTEXT_STYLE = {"color": "#242424"}

# 图例样式
LEGEND_TEXT_STYLE = {"color": "#242424", "fontSize": 12}

# 坐标轴：类目轴
CATEGORY_AXIS = {
    "axisLine": {"show": True, "lineStyle": {"color": "#dcdcdc"}},
    "axisTick": {"show": True, "lineStyle": {"color": "#dcdcdc"}},
    "axisLabel": {"show": True, "color": "#5e5e5e"},
    "splitLine": {"show": False, "lineStyle": {"color": ["#E0E6F1"]}},
}

# 坐标轴：数值轴
VALUE_AXIS = {
    "axisLine": {"show": False, "lineStyle": {"color": "#6E7079"}},
    "axisTick": {"show": False, "lineStyle": {"color": "#6E7079"}},
    "axisLabel": {"show": True, "color": "#5e5e5e"},
    "splitLine": {"show": True, "lineStyle": {"color": ["#e0e0e0"], "type": "dashed"}},
}

# 分割线（图表内网格）- 与 valueAxis 一致，供 bar/line 等统一使用
SPLIT_LINE_STYLE = {"show": True, "lineStyle": {"color": ["#e0e0e0"], "type": "dashed"}}

# 提示框
TOOLTIP_AXIS_POINTER = {
    "lineStyle": {"color": "#ccc", "width": 1},
    "crossStyle": {"color": "#ccc", "width": 1},
}

# 柱状图默认 itemStyle（与 theme bar 一致）
BAR_ITEM_STYLE = {"barBorderWidth": 0, "barBorderColor": "#eeeeee"}

# 折线图默认（与 theme line 一致）
LINE_ITEM_STYLE = {"borderWidth": 2}
LINE_LINE_STYLE = {"width": 2}
LINE_SYMBOL = "emptyCircle"
LINE_SYMBOL_SIZE = 4

# 饼图默认 itemStyle（与 theme pie 一致）
PIE_ITEM_STYLE = {"borderWidth": 2, "borderColor": "#fff"}

# 雷达图默认（与 theme radar 一致）
RADAR_ITEM_STYLE = {"borderWidth": 2}
RADAR_LINE_STYLE = {"width": 2}
RADAR_SYMBOL_SIZE = 4
RADAR_SYMBOL = "emptyCircle"

# 散点/漏斗 边框
SCATTER_ITEM_STYLE = {"borderWidth": 0, "borderColor": "#eeeeee"}
FUNNEL_ITEM_STYLE = {"borderWidth": 0, "borderColor": "#eeeeee"}


def get_theme_colors(n: int) -> list:
    """
    获取主题色板中的前 n 个颜色；若 n 超过色板长度则循环使用。
    :param n: 需要的颜色数量
    :return: 颜色十六进制字符串列表
    """
    if n <= 0:
        return []
    palette = COLOR_PALETTE
    if n <= len(palette):
        return list(palette[:n])
    return [palette[i % len(palette)] for i in range(n)]


def get_theme_global() -> dict:
    """
    获取 ECharts 全局样式对象，用于与各图表 config 合并。
    包含 backgroundColor、title 默认样式、legend 默认样式、tooltip 默认样式。
    """
    return {
        "backgroundColor": BACKGROUND_COLOR,
        "title": {
            "textStyle": TITLE_TEXT_STYLE,
            "subtextStyle": TITLE_SUBTEXT_STYLE,
            "left": "center",
        },
        "legend": {
            "left": "center",
            "bottom": "0%",
            "textStyle": LEGEND_TEXT_STYLE,
            "type": "scroll",
            "itemHeight": 4,
            "itemWidth": 12,
        },
        "tooltip": {
            "axisPointer": TOOLTIP_AXIS_POINTER,
            "backgroundColor": "rgba(50,50,50,0.9)",
            "textStyle": {"color": "#fff"},
            "borderColor": "#333",
            "borderWidth": 1,
        },
    }
