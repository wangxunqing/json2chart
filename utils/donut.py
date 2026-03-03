from utils.chart import get_colors, auto_detect_keys
from utils.theme import get_theme_global, PIE_ITEM_STYLE
import json

def generate_echarts_donut(
    data_list: list,
    name_key: str = None,
    value_keys: list = None,
    title: str = None,
    center_text: str = None,
    center_subtext: str = None,
    saturation=0.5,
    brightness=0.95
) -> str:
    """
    生成 ECharts 环形图配置，支持中心文字和左侧图例布局。
    参考 utils/pie.py 实现，主要调整了 radius、title 和 legend。
    """
    if not data_list:
        raise ValueError("数据列表不能为空")
    
    if not name_key:
        name_key, _ = auto_detect_keys(data_list)
    
    if not value_keys:
        _, value_key = auto_detect_keys(data_list)
        value_keys = [value_key]
    
    # 验证字段存在
    if name_key not in data_list[0]:
        raise KeyError(f"数据中未找到推断的字段: '{name_key}'")
    
    for value_key in value_keys:
        if value_key not in data_list[0]:
            raise KeyError(f"数据中未找到推断的字段: '{value_key}'")
    
    # 自动生成标题
    if not title:
        title = f"{name_key} {', '.join(value_keys)}分布环形图"

    legend_data = [item[name_key] for item in data_list]

    # 使用主题色板
    color_list = get_colors(len(data_list), saturation=saturation, brightness=brightness)

    global_theme = get_theme_global()
    
    # 构建标题数组
    titles = [
        # 主标题（左上角）
        {
            "text": title,
            "left": "left",
            "top": "top",
            "textStyle": {**global_theme["title"]["textStyle"], "fontSize": 16, "fontWeight": "bold"},
        }
    ]
    
    # 如果有中心文字，添加中心标题
    if center_text:
        titles.append({
            "text": center_text,
            "subtext": center_subtext or "",
            "left": "center",
            "top": "center",
            "textStyle": {"fontSize": 14, "color": "#666", "fontWeight": "normal"},
            "subtextStyle": {"fontSize": 18, "color": "#333", "fontWeight": "bold"},
        })

    config = {
        "animation": True,
        "animationDuration": 1000,
        "animationEasing": "cubicOut",
        "backgroundColor": global_theme.get("backgroundColor"),
        "title": titles,
        "tooltip": {
            "trigger": "item",
            "formatter": "{a} <br/>{b}: {c} ({d}%)",
            **global_theme["tooltip"],
        },
        # 图例配置为左侧垂直布局
        "legend": {
            **global_theme["legend"],
            "data": legend_data,
            "orient": "vertical",
            "left": "left",
            "top": "center",
            "itemGap": 20, # 增加间距
            "formatter": "{name}", # 如果需要显示数值，这里需要复杂的富文本处理，暂用默认名称
        },
        "series": [],
        "color": color_list,
    }
    
    # 动态计算半径
    num_series = len(value_keys)
    min_radius = 50  # 最小内径（保留给中心文字）
    max_radius = 80  # 最大外径
    
    # 如果只有一个系列，使用经典的 50%-70%
    if num_series == 1:
        radii_list = [(50, 70)]
    else:
        # 多个系列，均分空间
        available_width = max_radius - min_radius
        gap = 2
        ring_width = (available_width - (num_series - 1) * gap) / num_series
        
        radii_list = []
        for i in range(num_series):
            # 从内向外生成
            inner = min_radius + i * (ring_width + gap)
            outer = inner + ring_width
            radii_list.append((inner, outer))

    for i, value_key in enumerate(value_keys):
        inner_r, outer_r = radii_list[i]
        
        echarts_data = [
            {"value": item[value_key], "name": item[name_key]}
            for item in data_list
        ]
        
        series_config = {
            "name": value_key,
            "type": "pie",
            "radius": [f"{inner_r}%", f"{outer_r}%"],  # 设置环形半径
            "center": ["50%", "50%"],  # 居中
            "avoidLabelOverlap": False,
            "itemStyle": {
                **PIE_ITEM_STYLE,
                "borderRadius": 5, # 圆角
                "borderColor": '#fff',
                "borderWidth": 2
            },
            "label": {
                "show": False,
                "position": "center"
            },
            "emphasis": {
                "label": {
                    "show": False, # 如果已有中心文字，hover时不显示标签
                },
                "scale": True,
                "scaleSize": 10
            },
            "labelLine": {
                "show": False
            },
            "data": echarts_data
        }
        config["series"].append(series_config)

    return json.dumps(config, indent=4, ensure_ascii=False)
