from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import json

def auto_detect_keys(data_list: list) -> tuple:
    """自动检测数据中的名称字段和值字段"""
    if not data_list:
        raise ValueError("数据列表不能为空")
    
    # 获取第一个数据项的键值对
    sample = data_list[0]
    
    # 候选名称字段（字符串类型）
    name_candidates = [k for k, v in sample.items() if isinstance(v, str)]
    
    # 候选值字段（数值类型）
    value_candidates = [k for k, v in sample.items() if isinstance(v, (int, float))]
    
    # 验证是否找到合适的字段
    if not name_candidates:
        raise ValueError("数据中不包含字符串类型的字段，无法确定名称字段")
    if not value_candidates:
        raise ValueError("数据中不包含数值类型的字段，无法确定值字段")
    
    # 优先选择可能的字段名（按常见名称排序）
    common_name_keys = ["name", "device_id", "id", "product", "label"]
    common_value_keys = ["value", "efficiency", "sales", "count", "amount"]
    
    # 尝试找到最匹配的名称字段
    name_key = next((k for k in common_name_keys if k in name_candidates), name_candidates[0])
    
    # 尝试找到最匹配的值字段
    value_key = next((k for k in common_value_keys if k in value_candidates), value_candidates[0])
    
    return name_key, value_key

def generate_echarts_pie(
    data_list: list,
    name_key: str = None,
    value_key: str = None,
    title: str = None,
    series_name: str = None
) -> str:
    """生成通用 ECharts 饼图配置，支持自动推断字段"""
    if not data_list:
        raise ValueError("数据列表不能为空")
    
    # 自动检测 name_key 和 value_key（如果未提供）
    if not name_key or not value_key:
        name_key, value_key = auto_detect_keys(data_list)
    
    # 验证字段存在
    if value_key not in data_list[0] or name_key not in data_list[0]:
        raise KeyError(f"数据中未找到推断的字段: '{value_key}' 或 '{name_key}'")
    
    # 生成数据项
    echarts_data = [
        {"value": item[value_key], "name": item[name_key]}
        for item in data_list
    ]
    
    # 自动生成标题
    if not title:
        unit = ""
        sample_value = data_list[0][value_key]
        if isinstance(sample_value, float):
            unit = "%"
        title = f"{name_key} {value_key}分布{unit}饼图"
    
    # 自动生成系列名称
    if not series_name:
        series_name = f"{value_key}分布"
    
    # 处理单位
    unit = ""
    first_item_value = data_list[0][value_key]
    if isinstance(first_item_value, float):
        unit = "%"
    
    # 构造配置
    config = {
        "title": {"text": title, "left": "center"},
        "tooltip": {
            "trigger": "item",
            "formatter": f"{{a}}<br/>{{b}}: {{c}}{unit} ({{d}}%)"  # 显示系列名
        },
        "legend": {
            "orient": "vertical",
            "left": "left",
            "title": {"text": series_name, "show": True},  # 图例标题
            "data": [item[name_key] for item in data_list]
        },
        "series": [
            {
                "name": series_name,
                "type": "pie",
                "radius": "50%",
                "data": echarts_data,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }
    
    return json.dumps(config, indent=4, ensure_ascii=False)

def generate_echarts_bar(
    data_list: list,
    name_key: str = None,
    value_key: str = None,
    title: str = None,
    series_name: str = None
) -> str:
    """生成通用 ECharts 柱状图配置，支持自动推断字段"""
    if not data_list:
        raise ValueError("数据列表不能为空")
    
    # 自动检测 name_key 和 value_key（如果未提供）
    if not name_key or not value_key:
        name_key, value_key = auto_detect_keys(data_list)
    
    # 验证字段存在
    if value_key not in data_list[0] or name_key not in data_list[0]:
        raise KeyError(f"数据中未找到推断的字段: '{value_key}' 或 '{name_key}'")
    
    # 生成数据项
    x_axis_data = [item[name_key] for item in data_list]
    series_data = [item[value_key] for item in data_list]
    
    # 自动生成标题
    if not title:
        unit = ""
        sample_value = data_list[0][value_key]
        if isinstance(sample_value, float):
            unit = "%"
        title = f"{name_key} {value_key}分布{unit}柱状图"
    
    # 自动生成系列名称
    if not series_name:
        series_name = f"{value_key}分布"
    
    # 处理单位
    unit = ""
    first_item_value = data_list[0][value_key]
    if isinstance(first_item_value, float):
        unit = "%"
    
    # 构造配置
    config = {
        "title": {"text": title, "left": "center"},
        "tooltip": {
            "trigger": "axis",
            "formatter": f"{{a}}<br/>{{b}}: {{c}}{unit}"
        },
        "xAxis": {
            "type": "category",
            "data": x_axis_data
        },
        "yAxis": {
            "type": "value"
        },
        "series": [
            {
                "name": series_name,
                "type": "bar",
                "data": series_data
            }
        ]
    }
    
    return json.dumps(config, indent=4, ensure_ascii=False)

def generate_echarts_line(
    data_list: list,
    name_key: str = None,
    value_key: str = None,
    title: str = None,
    series_name: str = None
) -> str:
    """生成通用 ECharts 折线图配置，支持自动推断字段"""
    if not data_list:
        raise ValueError("数据列表不能为空")
    
    # 自动检测 name_key 和 value_key（如果未提供）
    if not name_key or not value_key:
        name_key, value_key = auto_detect_keys(data_list)
    
    # 验证字段存在
    if value_key not in data_list[0] or name_key not in data_list[0]:
        raise KeyError(f"数据中未找到推断的字段: '{value_key}' 或 '{name_key}'")
    
    # 生成数据项
    x_axis_data = [item[name_key] for item in data_list]
    series_data = [item[value_key] for item in data_list]
    
    # 自动生成标题
    if not title:
        unit = ""
        sample_value = data_list[0][value_key]
        if isinstance(sample_value, float):
            unit = "%"
        title = f"{name_key} {value_key}分布{unit}折线图"
    
    # 自动生成系列名称
    if not series_name:
        series_name = f"{value_key}分布"
    
    # 处理单位
    unit = ""
    first_item_value = data_list[0][value_key]
    if isinstance(first_item_value, float):
        unit = "%"
    
    # 构造配置
    config = {
        "title": {"text": title, "left": "center"},
        "tooltip": {
            "trigger": "axis",
            "formatter": f"{{a}}<br/>{{b}}: {{c}}{unit}"
        },
        "xAxis": {
            "type": "category",
            "data": x_axis_data
        },
        "yAxis": {
            "type": "value"
        },
        "series": [
            {
                "name": series_name,
                "type": "line",
                "data": series_data
            }
        ]
    }
    
    return json.dumps(config, indent=4, ensure_ascii=False)

class Json2chartTool(Tool):
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        chart_type = tool_parameters.get("chart_type", "饼状图")
        chart_data = tool_parameters.get("chart_data", [])
        chart_title = tool_parameters.get("chart_title", "图表")
        try:
            data_list = json.loads(chart_data)
            if chart_type == "饼状图":
                echarts_config = generate_echarts_pie(data_list, title=chart_title)
            elif chart_type == "柱状图":
                echarts_config = generate_echarts_bar(data_list, title=chart_title)
            elif chart_type == "折线图":
                echarts_config = generate_echarts_line(data_list, title=chart_title)
            else:
                raise ValueError(f"不支持的图表类型: {chart_type}")

            yield self.create_text_message(f"```echarts\n{echarts_config}\n```")

        except Exception as e:
            yield self.create_text_message(f"生成失败！错误信息: {str(e)}")