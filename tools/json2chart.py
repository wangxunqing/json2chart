#第四版，更智能的图表生成方案
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import json
import ast
import re
from utils.pie import generate_echarts_pie
from utils.line import generate_echarts_line
from utils.bar import generate_echarts_bar
from utils.radar import generate_echarts_radar
from utils.funnel import generate_echarts_funnel
from utils.scatter import generate_echarts_scatter
from utils.donut import generate_echarts_donut
from utils.dual_axis import generate_echarts_dual_axis
from utils.stacked_bar import generate_echarts_stacked_bar


from dify_plugin.entities.model.llm import LLMModelConfig
from dify_plugin.entities.model.message import SystemPromptMessage, UserPromptMessage
import pandas as pd

class Json2chartTool(Tool):
    def _parse_chart_data_text(self, chart_data_text: str) -> Any:
        candidates = []
        raw = (chart_data_text or "").strip()
        candidates.append(raw)
        candidates.append(raw.replace('\xa0', ' ').replace('\\n', ' '))
        candidates.append(raw.replace('\xa0', ' ').replace('\\n', ' ').replace('\\"', '"'))
        try:
            candidates.append(raw.encode("utf-8").decode("unicode_escape"))
        except Exception:
            pass

        for candidate in candidates:
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, str):
                    try:
                        parsed = json.loads(parsed)
                    except Exception:
                        pass
                return parsed
            except json.JSONDecodeError:
                try:
                    parsed = ast.literal_eval(candidate)
                    if isinstance(parsed, str):
                        try:
                            parsed = json.loads(parsed)
                        except Exception:
                            pass
                    return parsed
                except Exception:
                    continue
        raise ValueError("图表数据不是有效的 JSON 格式")

    def _parse_numeric_value(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            normalized = value.strip().replace(",", "")
            if not normalized:
                return None
            try:
                return float(normalized)
            except ValueError:
                return None
        return None

    def _is_numeric_like(self, value: Any) -> bool:
        return self._parse_numeric_value(value) is not None

    def _get_unit_factor(self, value_unit: str) -> float:
        unit = (value_unit or "").strip()
        unit_factor_map = {
            "元": 1.0,
            "万元": 10000.0,
            "亿元": 100000000.0,
        }
        return unit_factor_map.get(unit, 10000.0)

    def _scale_value(self, value: Any, factor: float) -> Any:
        if isinstance(value, bool):
            return value
        numeric_value = self._parse_numeric_value(value)
        if numeric_value is not None:
            return round(numeric_value / factor, 6)
        return value

    def _auto_detect_keys_with_numeric_string(self, data_list: list[dict[str, Any]]) -> tuple[str, list[str]]:
        if not data_list:
            raise ValueError("数据列表不能为空")
        sample = data_list[0]
        if not isinstance(sample, dict):
            raise ValueError("数据项格式不正确，期望为对象列表")

        name_candidates = []
        value_candidates = []
        for key, value in sample.items():
            if self._is_numeric_like(value):
                value_candidates.append(key)
            elif isinstance(value, str):
                name_candidates.append(key)

        if not name_candidates:
            raise ValueError("数据中不包含类别字段，无法确定名称字段")
        if not value_candidates:
            raise ValueError("数据中不包含可转换为数值的字段，无法确定值字段")

        common_name_keys = ["name", "名称", "类别", "category", "label", "项目", "月份", "日期", "时间"]
        name_key = next((k for k in common_name_keys if k in name_candidates), name_candidates[0])
        return name_key, value_candidates

    def _convert_single_row_wide_table(
        self,
        data_list: list[dict[str, Any]],
        value_keys: list[str] | None = None,
        series_names: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        if len(data_list) != 1 or not isinstance(data_list[0], dict):
            return data_list, False

        row = data_list[0]
        candidate_keys = value_keys or [k for k, v in row.items() if self._is_numeric_like(v)]
        transposed_data = []
        for i, key in enumerate(candidate_keys):
            if key not in row:
                continue
            numeric_value = self._parse_numeric_value(row.get(key))
            if numeric_value is None:
                continue
            category_name = series_names[i] if series_names and i < len(series_names) else key
            transposed_data.append({"category": category_name, "value": numeric_value})

        if not transposed_data:
            return data_list, False
        return transposed_data, True

    def _scale_series_data(self, data: Any, factor: float) -> Any:
        if isinstance(data, list):
            scaled = []
            for item in data:
                if isinstance(item, dict):
                    new_item = dict(item)
                    if "value" in new_item:
                        if isinstance(new_item["value"], list):
                            new_item["value"] = [self._scale_value(v, factor) for v in new_item["value"]]
                        else:
                            new_item["value"] = self._scale_value(new_item["value"], factor)
                    scaled.append(new_item)
                elif isinstance(item, list):
                    if len(item) >= 2:
                        new_point = list(item)
                        new_point[1] = self._scale_value(new_point[1], factor)
                        scaled.append(new_point)
                    else:
                        scaled.append(item)
                else:
                    scaled.append(self._scale_value(item, factor))
            return scaled
        return data

    def _add_unit_to_formatter(self, formatter: Any, value_unit: str) -> Any:
        if not isinstance(formatter, str) or not value_unit:
            return formatter
        updated = formatter
        for token in ["{c}", "{c0}", "{c1}", "{c2}", "{c[0]}", "{c[1]}", "{c[2]}"]:
            updated = updated.replace(token, f"{token}{value_unit}")
        return updated

    def _apply_value_unit(self, echarts_config: str, value_unit: str) -> str:
        factor = self._get_unit_factor(value_unit)
        try:
            config = json.loads(echarts_config)
        except Exception:
            return echarts_config

        tooltip = config.get("tooltip")
        if isinstance(tooltip, dict) and "formatter" in tooltip:
            tooltip["formatter"] = self._add_unit_to_formatter(tooltip.get("formatter"), value_unit)

        y_axis = config.get("yAxis")
        if isinstance(y_axis, dict):
            y_axis["name"] = value_unit
            axis_label = y_axis.get("axisLabel", {})
            if isinstance(axis_label, dict):
                axis_label["formatter"] = f"{{value}}{value_unit}"
                y_axis["axisLabel"] = axis_label
        elif isinstance(y_axis, list):
            for i, axis in enumerate(y_axis):
                if not isinstance(axis, dict):
                    continue
                axis_name = axis.get("name", "")
                # Skip scaling for rate axis (usually right axis or contains rate/率)
                if "率" in axis_name or "rate" in axis_name.lower():
                    continue
                
                axis["name"] = f"{axis_name}{value_unit}" if axis_name else value_unit
                axis_label = axis.get("axisLabel", {})
                if isinstance(axis_label, dict):
                    axis_label["formatter"] = f"{{value}}{value_unit}"
                    axis["axisLabel"] = axis_label

        series_list = config.get("series")
        if isinstance(series_list, list):
            for series in series_list:
                if not isinstance(series, dict):
                    continue
                series_name = series.get("name", "")
                # Skip scaling if the series is a rate
                if "率" in series_name or "rate" in series_name.lower() or series_name == "比率":
                    continue
                
                if "data" in series:
                    series["data"] = self._scale_series_data(series["data"], factor)
                series_tooltip = series.get("tooltip")
                if isinstance(series_tooltip, dict) and "formatter" in series_tooltip:
                    series_tooltip["formatter"] = self._add_unit_to_formatter(series_tooltip.get("formatter"), value_unit)

        return json.dumps(config, indent=4, ensure_ascii=False)
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        chart_data = tool_parameters.get("chart_data", [])
        chart_title = tool_parameters.get("chart_title")
        chart_type = tool_parameters.get("chart_type")
        data_desc = tool_parameters.get("data_desc")
        model = tool_parameters.get("model")
        saturation = tool_parameters.get("saturation", 0.5)
        brightness = tool_parameters.get("brightness", 0.95)
        value_unit = tool_parameters.get("value_unit", "万元")
        
        # 检查 chart_data 是否为字符串，若是则尝试解析为 JSON
        if isinstance(chart_data, str):
            try:
                chart_data = self._parse_chart_data_text(chart_data)
            except Exception as e:
                raise ValueError("图表数据不是有效的 JSON 格式") from e

        try:
            df = pd.DataFrame(chart_data)
            data_list = df.to_dict(orient='records')  # 将 DataFrame 转换为列表

            # 提取数据样本时，优先使用去重后的数据，确保展示所有类型
            try:
                unique_df = df.drop_duplicates()
            except TypeError:
                # 如果包含不可哈希的类型（如列表），则跳过去重
                unique_df = df
            
            if len(unique_df) > 20:
                sample_df = unique_df.head(20)
            else:
                sample_df = unique_df
            # 转换为类似 Markdown 格式，设置 index=False 避免输出索引列
            sample_data = sample_df.to_csv(sep='|', na_rep='nan', index=False)
            sample_markdown = '|' + sample_data.replace('\n', '\n|')

            # 调用大模型生成配置参数
            try:
                response = self.session.model.llm.invoke(
                    model_config=LLMModelConfig(
                        provider=model.get('provider'),
                        model=model.get('model'),
                        mode=model.get('mode'),
                        completion_params=model.get('completion_params'),
                    ),
                    prompt_messages=[
                        SystemPromptMessage(
                            content="""
                            你是一个专业的数据可视化专家，需要根据给定的 Markdown 表格数据，判断合适的横坐标和纵坐标，用于生成可视化图表。请遵循以下规则：
                            1. 输出格式必须为 JSON，包含`chart_type`, `chart_title`, `name_key`, `value_keys`, `series_names` 字段。
                            2. `chart_type` 的值为字符串，代表图表类型，目前支持"柱状图"、"折线图"、"饼状图"、"雷达图"、"漏斗图"、"散点图"、"环形图"、"双轴图"、"堆叠柱状图"。若用户指定了图表类型，则按用户的来，若没有指定，则你根据表格样例信息自动判断。
                            3. `chart_title` 的值为字符串，代表图表标题，若用户指定了标题，则按用户的来，若没有指定，则你根据表格样例信息自动生成。
                            4. `name_key` 的值为一个字符串，代表横坐标的 key，必须为 Markdown 表格中已有的表头字段，且应为类别型数据。
                            5. `value_keys` 的值为一个字符串数组，代表纵坐标的 key，这些 key 必须为 Markdown 表格中已有的表头字段，且必须为数值类型数据。
                            6. `series_names` 的值为一个字符串数组，是 `value_keys` 对应 key 的中文翻译，与 `value_keys` 数组元素一一对应。
                            7. `group_key` 的值为一个字符串（可选），代表用于分组的字段名。当数据需要按某个维度分组展示多系列图表时使用，如课程号、产品类别等。
                            8. 请根据 markdown 表格数据内容，抓取对数据分析有展现价值的 key。
                            9. 确保横纵坐标的选取有数据分析意义，避免选取序号等无分析价值的字段。
                            10. 雷达图适合多维度对比分析，至少需要3个数值字段；散点图适合两个数值指标间的相关性分析，必须选择两个数值字段作为value_keys，name_key应选择类别型或ID型字段（不是数值字段）；漏斗图适合流程转化率分析，需要有明确的先后顺序。
                            11. 饼图和环形图支持多个数值字段（生成同心圆），若需展示多维数据占比可选择多个value_keys；柱状图和折线图适合展示类别与数值的关系。
                            12. 当数据中存在明显的分组维度（如多个课程、多个产品等）且需要比较它们在同一指标上的差异时，应识别出合适的`group_key`，group_key应是类别型字段。
                            13. 对于散点图，当需要按类别区分不同数据点时，应将类别型字段设置为group_key，而不是name_key。
                            14. 请仔细识别数据类型，确保value_keys只包含可以进行数学运算的数值字段，避免选择文本或混合类型字段。
                            15. 对于双轴图，请额外输出 `bar_value_keys`（柱状图指标数组）和 `line_value_keys`（折线图指标数组）。
                            16. 对于环形图，如果可以计算出总额或有明确的中心文本，请输出 `center_text` 字段。
                            17. 只输出标准的 json 格式内容，不要包含```json```标签，不要输出其他任何文字。
                            
                            示例：
                            表格数据：
                            |产品|销量|利润|
                            |---|---|---|
                            |A|100|20|
                            |B|200|50|
                            |C|150|30|
                            
                            柱状图输出：
                            {"chart_type":"柱状图","chart_title":"产品销量与利润分析","name_key":"产品","value_keys":["销量","利润"],"series_names":["销量","利润"]}
                            
                            饼图输出：
                            {"chart_type":"饼状图","chart_title":"产品销量分布","name_key":"产品","value_keys":["销量"],"series_names":["销量"]}
                            
                            带分组的折线图输出（例如课程成绩数据）：
                            {"chart_type":"折线图","chart_title":"各课程成绩对比","name_key":"score_month","value_keys":["score"],"series_names":["成绩"],"group_key":"course_no"}
                            
                            散点图输出（例如产品价格与销量关系分析）：
                            {"chart_type":"散点图","chart_title":"产品价格与销量关系分析","name_key":"产品名称","value_keys":["价格(元)","月销量(台)"],"series_names":["价格(元)","月销量(台)"],"group_key":"品牌"}

                            双轴图输出（例如税负率和同比变动率）：
                            {"chart_type":"双轴图","chart_title":"税负率分析","name_key":"月份","value_keys":["税负率","同比变动率"],"series_names":["税负率","同比变动率"],"bar_value_keys":["税负率"],"line_value_keys":["同比变动率"]}
                            """
                        ),
                        UserPromptMessage(
                            content=f"用户指定的类型：{chart_type}\n用户指定的标题：{chart_title}\n数据补充说明：{data_desc}\n表格的样例数据:\n{sample_markdown}"
                        )
                    ],
                    stream=False
                )
            except Exception as e:
                raise RuntimeError(f"调用大模型生成配置失败: {str(e)}") from e

            # 提取大模型返回的 JSON 数据
            try:
                content = response.message.content.strip()
                # 尝试去除 markdown 代码块标记
                if "```" in content:
                    pattern = r"```(?:json)?\s*(.*?)\s*```"
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        content = match.group(1)
                
                print("大模型输出的json (清洗后):", content)
                config_params = json.loads(content)
                required_fields = ["chart_type", "chart_title", "name_key", "value_keys", "series_names"]
                for field in required_fields:
                    if field not in config_params:
                        raise ValueError(f"大模型返回的 JSON 缺少必要字段: {field}")

                chart_type = config_params["chart_type"]
                chart_title = config_params["chart_title"]
                name_key = config_params["name_key"]
                value_keys = config_params["value_keys"]
                series_names = config_params["series_names"]
                # group_key是可选的
                group_key = config_params.get("group_key")
                # 新增图表类型的可选参数
                bar_value_keys = config_params.get("bar_value_keys", [])
                line_value_keys = config_params.get("line_value_keys", [])
                center_text = config_params.get("center_text")

                # 针对双轴图的特殊处理：确保 value_keys 包含 bar_value_keys 和 line_value_keys
                if chart_type == "双轴图":
                    # 如果 bar_value_keys 或 line_value_keys 不存在，尝试从 value_keys 中拆分
                    if not bar_value_keys and not line_value_keys:
                        if len(value_keys) >= 2:
                            bar_value_keys = [value_keys[0]]
                            line_value_keys = value_keys[1:]
                        else:
                            bar_value_keys = value_keys
                            line_value_keys = []
                    
                    # 重新构建 value_keys 和 series_names，确保后续的数值转换逻辑能覆盖到
                    # 注意：这里会覆盖大模型返回的 value_keys，以 bar_value_keys + line_value_keys 为准
                    all_keys = []
                    all_names = []
                    
                    for key in bar_value_keys:
                        if key not in all_keys:
                            all_keys.append(key)
                            # 尝试找对应的 series_name，如果没有则用 key
                            if key in value_keys:
                                index = value_keys.index(key)
                                if index < len(series_names):
                                    all_names.append(series_names[index])
                                else:
                                    all_names.append(key)
                            else:
                                all_names.append(key)
                                
                    for key in line_value_keys:
                        if key not in all_keys:
                            all_keys.append(key)
                            # 尝试找对应的 series_name
                            if key in value_keys:
                                index = value_keys.index(key)
                                if index < len(series_names):
                                    all_names.append(series_names[index])
                                else:
                                    all_names.append(key)
                            else:
                                all_names.append(key)
                    
                    value_keys = all_keys
                    series_names = all_names

                if len(value_keys) != len(series_names):
                    raise ValueError("value_keys 和 series_names 的长度不一致")

                if name_key not in df.columns:
                    raise ValueError(f"name_key {name_key} 不存在于 DataFrame 中")

                for value_key in value_keys:
                    if value_key not in df.columns:
                        raise ValueError(f"value_key {value_key} 不存在于 DataFrame 中")

            except json.JSONDecodeError:
                raise ValueError("大模型返回的内容不是有效的 JSON 格式")
            except Exception as e:
                # 当大模型配置无效时，尝试使用auto_detect_keys作为后备方案
                try:
                    recovered_with_llm_alias = False
                    if isinstance(value_keys, list) and value_keys:
                        converted_data, converted = self._convert_single_row_wide_table(
                            data_list,
                            value_keys=value_keys,
                            series_names=series_names if isinstance(series_names, list) else None,
                        )
                        if converted:
                            data_list = converted_data
                            name_key = "category"
                            value_keys = ["value"]
                            series_names = ["数值"]
                            group_key = None
                            df = pd.DataFrame(data_list)
                            recovered_with_llm_alias = True

                    if recovered_with_llm_alias:
                        if chart_type is None:
                            chart_type = "柱状图"
                        if chart_title is None:
                            chart_title = f"{name_key} 数据分析图表"
                    else:
                    # 单行宽表优先转为 category/value，避免名称字段缺失导致回退失败
                        data_list, wide_table_converted = self._convert_single_row_wide_table(data_list)
                        # 自动检测合适的字段
                        detected_name_key, detected_value_keys = self._auto_detect_keys_with_numeric_string(data_list)
                        
                        # 根据检测到的字段自动选择图表类型
                        if chart_type is None:
                            if wide_table_converted:
                                chart_type = "柱状图"
                            elif len(detected_value_keys) >= 3:
                                chart_type = "雷达图"
                            elif len(detected_value_keys) == 2:
                                chart_type = "散点图"
                            else:
                                chart_type = "柱状图"
                        
                        # 设置默认的series_names
                        detected_series_names = detected_value_keys

                        # 使用检测到的字段继续处理
                        name_key = detected_name_key
                        value_keys = detected_value_keys
                        series_names = detected_series_names
                        group_key = None  # 自动检测模式下暂不支持group_key
                        df = pd.DataFrame(data_list)
                        
                        # 重新设置图表标题（如果未指定）
                        if chart_title is None:
                            chart_title = f"{name_key} 数据分析图表"
                except Exception as fallback_error:
                    raise ValueError(f"自动检测字段也失败: {str(fallback_error)}") from fallback_error

            # 根据图表类型验证配置参数
            try:
                # 验证数据类型是否适合所选图表
                if chart_type == "散点图":
                    # 检查name_key是否是数值字段且value_keys只有一个元素
                    if len(value_keys) == 1 and name_key in df.columns:
                        try:
                            # 尝试将name_key转换为数值类型，检查是否为有效数值
                            df[name_key] = pd.to_numeric(df[name_key], errors='coerce')
                            if not df[name_key].isna().all():
                                # 如果name_key是数值字段，将其也加入value_keys
                                value_keys = [name_key] + value_keys
                                series_names = [name_key] + series_names
                        except:
                            pass
                    
                    # 如果最终还是少于两个数值字段，使用scatter.py中的自动补充逻辑
                    if len(value_keys) < 1:
                        raise ValueError("散点图需要至少一个数值字段")
                elif chart_type == "雷达图" and len(value_keys) < 3:
                    raise ValueError("雷达图需要至少三个数值字段进行多维度分析")

                # 特殊处理：双轴图且为单行宽表数据自动转置
                if chart_type == "双轴图" and len(data_list) == 1 and bar_value_keys and line_value_keys:
                    if len(bar_value_keys) == len(line_value_keys):
                        transposed = []
                        # series_names length should match the number of pairs
                        # but in the prompt we ask LLM to output series_names corresponding to value_keys
                        # For dual axis, value_keys usually has length = len(bar) + len(line)
                        # or LLM just outputs series_names for the categories. We will try our best:
                        cat_names = series_names[:len(bar_value_keys)] if len(series_names) >= len(bar_value_keys) else bar_value_keys
                        for i in range(len(bar_value_keys)):
                            b_key = bar_value_keys[i]
                            l_key = line_value_keys[i]
                            if b_key in data_list[0] and l_key in data_list[0]:
                                b_val = self._parse_numeric_value(data_list[0].get(b_key))
                                l_val = self._parse_numeric_value(data_list[0].get(l_key))
                                if b_val is not None and l_val is not None:
                                    transposed.append({
                                        "category": cat_names[i],
                                        "bar_value": b_val,
                                        "line_value": l_val
                                    })
                        if transposed:
                            # Try to infer metric names
                            b_name = "柱状指标"
                            l_name = "折线指标"
                            if "amt" in bar_value_keys[0].lower() or "额" in bar_value_keys[0]:
                                b_name = "金额"
                            if "rate" in line_value_keys[0].lower() or "率" in line_value_keys[0]:
                                l_name = "比率"
                            
                            data_list = transposed
                            name_key = "category"
                            bar_value_keys = ["bar_value"]
                            line_value_keys = ["line_value"]
                            value_keys = ["bar_value", "line_value"]
                            series_names = [b_name, l_name]
                            df = pd.DataFrame(data_list)

                # 特殊处理：单行宽表数据自动转置
                # 当饼图/环形图只有一行数据，但有多个数值列时，很可能是宽表结构（列名即类别）
                # 此时应该转置数据，将列名作为name_key，列值作为value_key
                if chart_type in ["饼状图", "环形图"] and len(data_list) == 1 and len(value_keys) > 1:
                    transposed_data, converted = self._convert_single_row_wide_table(
                        data_list,
                        value_keys=value_keys,
                        series_names=series_names,
                    )
                    
                    if converted:
                        # 更新上下文变量
                        data_list = transposed_data
                        name_key = "category"
                        value_keys = ["value"]
                        series_names = ["数值"]
                        # 更新 df，确保后续验证逻辑能找到新的字段
                        df = pd.DataFrame(data_list)

                # 验证字段是否为数值类型
                for value_key in value_keys:
                    try:
                        # 尝试将数据转换为数值类型，验证是否为有效数值
                        df[value_key] = pd.to_numeric(df[value_key], errors='coerce')
                        # 检查是否有值被转换为NaN
                        if df[value_key].isna().all():
                            raise ValueError(f"字段 {value_key} 无法转换为数值类型")
                    except Exception as e:
                        raise ValueError(f"字段 {value_key} 不是有效的数值类型: {str(e)}")

                data_list = df.to_dict(orient='records')
                
                # 根据图表类型生成 ECharts 配置
                supported_chart_types = ["饼状图", "柱状图", "折线图", "雷达图", "漏斗图", "散点图", "环形图", "双轴图", "堆叠柱状图"]
                if chart_type not in supported_chart_types:
                    raise ValueError(f"不支持的图表类型: {chart_type}")

                if chart_type == "饼状图":
                    echarts_config = generate_echarts_pie(data_list, name_key=name_key, title=chart_title, value_keys=value_keys, series_names=series_names, saturation=saturation, brightness=brightness)
                elif chart_type == "环形图":
                    echarts_config = generate_echarts_donut(data_list, name_key=name_key, title=chart_title, value_keys=value_keys, center_text=center_text, saturation=saturation, brightness=brightness)
                elif chart_type == "柱状图":
                    echarts_config = generate_echarts_bar(data_list, name_key=name_key, title=chart_title, value_keys=value_keys, series_names=series_names, saturation=saturation, brightness=brightness, group_key=group_key)
                elif chart_type == "堆叠柱状图":
                    echarts_config = generate_echarts_stacked_bar(data_list, name_key=name_key, title=chart_title, value_keys=value_keys, series_names=series_names, saturation=saturation, brightness=brightness)
                elif chart_type == "折线图":
                    echarts_config = generate_echarts_line(data_list, name_key=name_key, title=chart_title, value_keys=value_keys, series_names=series_names, saturation=saturation, brightness=brightness, group_key=group_key)
                elif chart_type == "双轴图":
                    bar_names = series_names[:len(bar_value_keys)] if len(series_names) >= len(bar_value_keys) else bar_value_keys
                    line_names = series_names[len(bar_value_keys):len(bar_value_keys)+len(line_value_keys)] if len(series_names) >= len(bar_value_keys) + len(line_value_keys) else line_value_keys
                    # 直接调用，参数已经在前面处理好了
                    echarts_config = generate_echarts_dual_axis(data_list, name_key=name_key, title=chart_title, bar_value_keys=bar_value_keys, line_value_keys=line_value_keys, bar_names=bar_names, line_names=line_names, saturation=saturation, brightness=brightness)
                elif chart_type == "雷达图":
                    echarts_config = generate_echarts_radar(data_list, name_key=name_key, title=chart_title, value_keys=value_keys, series_names=series_names, saturation=saturation, brightness=brightness, group_key=group_key)
                elif chart_type == "漏斗图":
                    echarts_config = generate_echarts_funnel(data_list, name_key=name_key, title=chart_title, value_keys=value_keys, series_names=series_names, saturation=saturation, brightness=brightness)
                elif chart_type == "散点图":
                    echarts_config = generate_echarts_scatter(data_list, name_key=name_key, title=chart_title, value_keys=value_keys, series_names=series_names, saturation=saturation, brightness=brightness, group_key=group_key)

                echarts_config = self._apply_value_unit(echarts_config, value_unit)
                yield self.create_text_message(f"\n```echarts\n{echarts_config}\n```")

            except Exception:
                raise
        except Exception:
            raise
