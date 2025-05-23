from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import json
import colorsys

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

def generate_colors(num_colors):
    """
    动态生成指定数量的鲜艳颜色
    :param num_colors: 所需颜色的数量
    :return: 颜色列表
    """
    colors = []
    for i in range(num_colors):
        hue = i / num_colors
        # 提高饱和度和亮度以生成更鲜艳的颜色
        rgb = colorsys.hsv_to_rgb(hue, 0.9, 0.95)
        colors.append('#%02x%02x%02x' % tuple(int(c * 255) for c in rgb))
    return colors

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
    # 动态生成颜色列表
    color_list = generate_colors(len(data_list))

    config = {
        "animation": True,  # 开启动画效果
        "animationDuration": 1000,  # 动画持续时间，单位为毫秒
        "animationEasing": "cubicOut",  # 动画缓动效果，cubicOut 是一种常见的缓动函数
        "title": {
            # 标题文本内容
            "text": title,
            # 标题水平对齐方式，这里设置为居中
            "left": "center",
            # 标题文本样式配置
            "textStyle": {
                # 标题字体大小
                "fontSize": 16,
                # 标题字体粗细
                "fontWeight": "bold"
            }
        },
        # 鼠标悬停提示框配置
        "tooltip": {
            # 触发类型，'item' 表示鼠标悬停在数据项上时触发
            "trigger": "item",
            # 提示框内容格式，{a} 系列名，{b} 数据项名称，{c} 数据值，{d} 百分比
            "formatter": f"{{a}}<br/>{{b}}: {{c}}{unit} ({{d}}%)"
        },
        # 图例配置
        "legend": {
            # 图例排列方向，'vertical' 表示垂直排列
            "orient": "vertical",
            # 图例距离容器右侧的距离
            "left": "15%",
            # 图例垂直居中显示
            "top": "center",
            # 图例标题配置
            "title": {"text": series_name, "show": True},
            # 图例的数据项名称列表
            "data": [item[name_key] for item in data_list]
        },
        # 系列配置，可包含多个系列
        "series": [
            {
                # 系列名称，会显示在图例和提示框中
                "name": series_name,
                # 图表类型，这里是饼图
                "type": "pie",
                # 饼图的内外半径，这里设置为环形饼图
                "radius": ["40%", "70%"],
                # 是否避免标签重叠
                "avoidLabelOverlap": False,
                # 数据项样式配置
                "itemStyle": {
                    # 数据项边框圆角
                    "borderRadius": 10,
                    # 数据项边框颜色
                    "borderColor": "#fff",
                    # 数据项边框宽度
                    "borderWidth": 2
                },
                # 数据标签配置
                "label": {
                    # 是否显示标签
                    "show": False,
                    # 标签位置，'center' 表示显示在饼图中心，outside表示外面
                    "position": "center",
                },
                # 鼠标悬停高亮时的配置
                "emphasis": {
                    # 高亮时的标签配置
                    "label": {
                        # 高亮时显示标签
                        "show": True,
                        # 高亮时标签字体大小
                        "fontSize": "18",
                        # 高亮时标签字体粗细
                        "fontWeight": "bold"
                    }
                },
                # 标签线配置
                "labelLine": {
                    # 是否显示标签线
                    "show": False
                },
                # 饼图的数据列表
                "data": echarts_data
            }
        ],
        # 饼图各数据项的颜色列表，按顺序依次应用
        "color": color_list
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
    
    # 动态生成颜色列表
    color_list = generate_colors(len(data_list))

    # 构造配置
    config = {
        "animation": True,  # 添加动画效果
        "animationDuration": 1000,  # 动画持续时间
        "title": {"text": title, "left": "center"},
        "tooltip": {
            "trigger": "axis",
            "formatter": f"{{a}}<br/>{{b}}: {{c}}{unit}",
            "backgroundColor": 'rgba(50,50,50,0.9)',  # 提示框背景色
            "textStyle": {
                "color": '#fff'  # 提示框文字颜色
            },
            "borderColor": '#333',  # 提示框边框颜色
            "borderWidth": 1  # 提示框边框宽度
        },
        "xAxis": {
            "type": "category",
            "data": x_axis_data,
            "axisTick": {
                "alignWithLabel": True  # 刻度线与标签对齐
            },
            "axisLabel": {
                "rotate": 45,  # x 轴标签旋转 45 度，避免标签过长重叠
                "interval": 0  # 强制显示所有标签
            },
            "splitLine": {
                "show": True,  # 显示 x 轴网格线
                "lineStyle": {
                    "color": ['#eee'],  # 网格线颜色
                    "type": 'dashed'  # 网格线样式
                }
            }
        },
        "yAxis": {
            "type": "value",
            "splitLine": {
                "show": True,  # 显示 y 轴网格线
                "lineStyle": {
                    "color": ['#eee'],  # 网格线颜色
                    "type": 'dashed'  # 网格线样式
                }
            }
        },
        "series": [
            {
                "name": series_name,
                "type": "bar",
                "data": series_data,
                "itemStyle": {
                    # 预先计算每个柱子的颜色
                    "color": color_list,
                    "barBorderRadius": [5, 5, 0, 0],  # 柱子圆角
                    "shadowBlur": 10,  # 阴影模糊程度
                    "shadowColor": 'rgba(0, 0, 0, 0.3)'  # 阴影颜色
                }
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
        "animation": True,  # 添加动画效果
        "animationDuration": 1000,  # 动画持续时间
        "title": {"text": title, "left": "center"},
        "tooltip": {
            "trigger": "axis",
            "formatter": f"{{a}}<br/>{{b}}: {{c}}{unit}",
            "backgroundColor": 'rgba(50,50,50,0.9)',  # 提示框背景色
            "textStyle": {
                "color": '#fff'  # 提示框文字颜色
            },
            "borderColor": '#333',  # 提示框边框颜色
            "borderWidth": 1  # 提示框边框宽度
        },
        "xAxis": {
            "type": "category",
            "data": x_axis_data,
            "axisTick": {
                "alignWithLabel": True  # 刻度线与标签对齐
            },
            "splitLine": {
                "show": True,  # 显示 x 轴网格线
                "lineStyle": {
                    "color": ['#eee'],  # 网格线颜色
                    "type": 'dashed'  # 网格线样式
                }
            }
        },
        "yAxis": {
            "type": "value",
            "splitLine": {
                "show": True,  # 显示 y 轴网格线
                "lineStyle": {
                    "color": ['#eee'],  # 网格线颜色
                    "type": 'dashed'  # 网格线样式
                }
            }
        },
        "series": [
            {
                "name": series_name,
                "type": "line",
                "data": series_data,
                "smooth": True,  # 折线平滑
                "lineStyle": {
                    "width": 2,  # 折线宽度
                    "color": '#5470c6'  # 折线颜色
                },
                "itemStyle": {
                    "color": '#5470c6'  # 数据点颜色
                },
                "symbol": 'circle',  # 数据点形状
                "symbolSize": 8  # 数据点大小
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