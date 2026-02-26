from utils.chart import get_colors, auto_detect_keys
from utils.theme import get_theme_global, VALUE_AXIS, CATEGORY_AXIS, BAR_ITEM_STYLE
import json

def generate_echarts_stacked_bar(
    data_list: list,
    name_key: str = None,
    value_keys: list = None,
    title: str = None,
    series_names: list = None,
    saturation=0.5,
    brightness=0.95
) -> str:
    """
    生成 ECharts 堆叠柱状图配置。
    参考 utils/bar.py 实现，强制开启堆叠 (stack: 'total')。
    """
    if not data_list:
        raise ValueError("数据列表不能为空")
    
    if not name_key:
        name_key, _ = auto_detect_keys(data_list)
    
    if not value_keys:
        _, value_key = auto_detect_keys(data_list)
        value_keys = [value_key]
    
    if series_names is None:
        series_names = [f"{value_key}" for value_key in value_keys] # 堆叠图通常直接用字段名作为系列名
    
    # 验证字段存在
    required_fields = [name_key] + value_keys
    for field in required_fields:
        if field not in data_list[0]:
            raise KeyError(f"数据中未找到字段: '{field}'")
    
    # 构造配置
    global_theme = get_theme_global()
    config = {
        "animation": True,
        "animationDuration": 1000,
        "backgroundColor": global_theme.get("backgroundColor"),
        "title": {"text": title, "left": "center", "textStyle": global_theme["title"]["textStyle"]},
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"}, # 堆叠图通常使用 shadow 指示器
            **global_theme["tooltip"],
        },
        "legend": {**global_theme["legend"], "data": series_names},
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": [item[name_key] for item in data_list],
            **CATEGORY_AXIS,
            "axisTick": {"alignWithLabel": True, **CATEGORY_AXIS.get("axisTick", {})},
        },
        "yAxis": {"type": "value", **VALUE_AXIS},
        "series": [],
    }
    
    # 使用主题色板
    color_list = get_colors(len(value_keys), saturation=saturation, brightness=brightness)
    
    series_data_list = []
    for value_key in value_keys:
        series_data = [item[value_key] for item in data_list]
        series_data_list.append(series_data)
        
    for i, series_data in enumerate(series_data_list):
        series_config = {
            "name": series_names[i],
            "type": "bar",
            "stack": "total", # 开启堆叠
            "data": series_data,
            "itemStyle": {
                **BAR_ITEM_STYLE,
                "color": color_list[i],
                # 堆叠图通常不需要圆角，或者只有最上面的有圆角，这里简化处理不设圆角或仅设顶部
                "barBorderRadius": 0 
            },
            # 显示标签（可选）
            "label": {
                "show": False, # 默认不显示，避免拥挤
                "position": "inside"
            }
        }
        config["series"].append(series_config)
    
    # 更新标题
    if not title:
        title = f"{name_key} {', '.join(value_keys)}堆叠柱状图"
    config["title"]["text"] = title
    
    return json.dumps(config, indent=4, ensure_ascii=False)
