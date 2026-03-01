---
name: railway_booking
description: 12306铁路查询：查询火车站信息和火车票务
---

# 12306铁路查询技能

## 功能范围

- 获取当前日期
- 车站查询：搜索火车站、高铁站信息
- 车票查询：查询火车、高铁班次和余票
- 票务服务：订票、退改签相关操作
- 时刻表查询：列车运行时刻信息

## 使用规范

1. 专门处理铁路交通相关查询
2. 需要明确出发地、目的地、日期等信息
3. 实时票务信息可能会有延迟

## 部分工具说明

- get-current-date: 获取当前日期，以上海时区（Asia/Shanghai, UTC+8）为准，返回格式为 "yyyy-MM-dd"。主要用于解析用户提到的相对日期（如"明天"、"下周三"），为其他需要日期的接口提供准确的日期输入。
- get-stations-code-in-city: 通过中文城市名查询该城市 **所有** 火车站的名称及其对应的 `station_code`，结果是一个包含多个车站信息的列表。
  - city (string) 中文城市名称，例如："北京", "上海"
- get-station-code-of-citys: 通过中文城市名查询代表该城市的 `station_code`。此接口主要用于在用户提供**城市名**作为出发地或到达地时，为接口准备 `station_code` 参数。
  - citys (string) 要查询的城市，比如"北京"。若要查询多个城市，请用|分割，比如"北京|上海"。
- get-station-code-by-names: 通过具体的中文车站名查询其 `station_code` 和车站名。此接口主要用于在用户提供**具体车站名**作为出发地或到达地时，为接口准备 `station_code` 参数。
  - stationNames (string) 具体的中文车站名称，例如："北京南", "上海虹桥"。若要查询多个站点，请用|分割，比如"北京南|上海虹桥"。
- get-tickets: 查询12306余票信息。
  - fromStation (string) 出发地的 `station_code`。必须是通过 `get-station-code-by-names` 或 `get-station-code-of-citys` 接口查询得到的编码，严禁直接使用中文地名。
  - toStation (string) 到达地的 `station_code`。必须是通过 `get-station-code-by-names` 或 `get-station-code-of-citys` 接口查询得到的编码，严禁直接使用中文地名。
  - date (string) 查询日期，格式为 "yyyy-MM-dd"。如果用户提供的是相对日期（如"明天"），请务必先调用 `get-current-date` 接口获取当前日期，并计算出目标日期。
  - trainFilterFlags (string) 车次筛选条件，默认为空，即不筛选。支持多个标志同时筛选。例如用户说"高铁票"，则应使用 "G"。可选标志：[G(高铁/城际),D(动车),Z(直达特快),T(特快),K(快速),O(其他),F(复兴号),S(智能动车组)]
