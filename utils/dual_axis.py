from utils.chart import get_colors, auto_detect_keys
from utils.theme import get_theme_global, VALUE_AXIS, CATEGORY_AXIS
import json

def generate_echarts_dual_axis(
    data_list: list,
    name_key: str = None,
    bar_value_keys: list = None,
    line_value_keys: list = None,
    title: str = None,
    bar_names: list = None,
    line_names: list = None,
    saturation=0.5,
    brightness=0.95
) -> str:
    """
    生成 ECharts 双轴图配置（柱状图 + 折线图）。
    左轴对应柱状图，右轴对应折线图。
    """
    if not data_list:
        raise ValueError("数据列表不能为空")
    
    if not name_key:
        name_key, _ = auto_detect_keys(data_list)
    
    # 如果未指定 value_keys，尝试自动推断
    if not bar_value_keys and not line_value_keys:
        # 简单处理：取前两个数值字段，第一个给bar，第二个给line
        sample = data_list[0]
        value_candidates = [k for k, v in sample.items() if isinstance(v, (int, float)) and k != name_key]
        if len(value_candidates) >= 1:
            bar_value_keys = [value_candidates[0]]
        if len(value_candidates) >= 2:
            line_value_keys = [value_candidates[1]]
    
    bar_value_keys = bar_value_keys or []
    line_value_keys = line_value_keys or []
    
    if not bar_value_keys and not line_value_keys:
         raise ValueError("无法确定数值字段，请指定 bar_value_keys 或 line_value_keys")

    # 默认名称
    if bar_names is None:
        bar_names = bar_value_keys
    if line_names is None:
        line_names = line_value_keys
        
    # 验证字段
    required_fields = [name_key] + bar_value_keys + line_value_keys
    for field in required_fields:
        if field not in data_list[0]:
            raise KeyError(f"数据中未找到字段: '{field}'")
            
    # 准备数据
    x_axis_data = [item[name_key] for item in data_list]
    
    # 颜色生成
    total_series = len(bar_value_keys) + len(line_value_keys)
    color_list = get_colors(total_series, saturation=saturation, brightness=brightness)
    
    global_theme = get_theme_global()
    
    config = {
        "animation": True,
        "backgroundColor": global_theme.get("backgroundColor"),
        "title": {"text": title, "left": "left", "textStyle": global_theme["title"]["textStyle"]}, # 标题居左
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            **global_theme["tooltip"],
        },
        "legend": {
            **global_theme["legend"],
            "data": bar_names + line_names,
            "top": "top", # 图例置顶
            "right": "right" # 图例靠右
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": x_axis_data,
            **CATEGORY_AXIS,
            "axisTick": {"alignWithLabel": True},
        },
        "yAxis": [
            # 左轴：柱状图
            {
                "type": "value",
                "name": "柱状图数据", # 可根据实际情况传入参数设置名称
                "position": "left",
                "axisLine": {"show": True, "lineStyle": {"color": "#5470C6"}}, # 蓝色
                "axisLabel": {"formatter": "{value}"},
                **VALUE_AXIS,
                "splitLine": {"show": False} # 左轴不显示网格线，避免重叠
            },
            # 右轴：折线图
            {
                "type": "value",
                "name": "折线图数据",
                "position": "right",
                "axisLine": {"show": True, "lineStyle": {"color": "#91CC75"}}, # 绿色
                "axisLabel": {"formatter": "{value}"}, # 如果是百分比，可以使用 "{value}%"
                **VALUE_AXIS,
                "splitLine": {"show": True, "lineStyle": {"type": "dashed", "color": "#eee"}} # 右轴显示网格线
            }
        ],
        "series": [],
        "color": color_list
    }
    
    # 添加柱状图系列
    for i, key in enumerate(bar_value_keys):
        series_name = bar_names[i] if i < len(bar_names) else key
        config["series"].append({
            "name": series_name,
            "type": "bar",
            "yAxisIndex": 0, # 使用左轴
            "data": [item[key] for item in data_list],
            "barMaxWidth": 30,
            "itemStyle": {"borderRadius": [5, 5, 0, 0]}
        })
        
    # 添加折线图系列
    for i, key in enumerate(line_value_keys):
        series_name = line_names[i] if i < len(line_names) else key
        config["series"].append({
            "name": series_name,
            "type": "line",
            "yAxisIndex": 1, # 使用右轴
            "data": [item[key] for item in data_list],
            "smooth": True,
            "symbol": "circle",
            "symbolSize": 8,
            "lineStyle": {"width": 3}
        })
        
    return json.dumps(config, indent=4, ensure_ascii=False)
