# Language Specification for Quantitative Trading Strategy System

## Data Types

### One-dimensional Data Types

数值（pure）：表示没有特定量纲的纯数值，通常用于计数或指标系数等。
价格（price）：表示货币单位的数值，人民币和美元。
价格变化（price_change）：表示价格的变化量，具有相同的货币单位。
数量（quantity）：表示交易的数量，通常为整数。
时间点（time）：表示特定时间的时间戳。
时间段（period）：表示一段时间的区间。
单根K线/蜡烛图(candle)：包含开盘价、最高价、最低价、收盘价和成交量的复合数据类型。

### Two-dimensional Data Types

线类型(line)：表示按时间序列排列的数值集合，通常用于技术指标计算。
K线序列(kline)：按时间顺序排列的K线集合。

## Keywords

module: 定义一个模块，包含策略的主要逻辑。
always: 定义一个持续监控的块，当条件满足时触发相应操作。
assign: 用于变量赋值，将表达式的结果赋值给变量。
assert: 用于断言某个条件为真，否则触发错误。
buy: 执行买入操作，通常后跟买入数量。
sell: 执行卖出操作，通常后跟卖出数量。
initial: 定义一个初始块，在策略开始时执行一次。
if/else: 条件语句，根据条件执行不同的代码块。
parameter: 定义常量参数，用于配置策略的可调参数。
crossabove: 用于判断一条线是否上穿另一条线。
crossbelow: 用于判断一条线是否下穿另一条线。

## Operators

算术运算符：+（加），-（减），*（乘），/（除），%（取模）
比较运算符：==（等于），!=（不等于），>（大于），<（小于），>=（大于等于），<=（小于等于）
逻辑运算符：&&（与），||（或），!（非）

### Functions

MA(line, period): 计算指定周期的移动平均线，返回线类型。

EMA(line, period): 计算指定周期的指数移动平均线，返回线类型。

## Example Strategy

module MovingAverageCrossover{
    parameter symbol = "AAPL"
    parameter short_period = 5
    parameter long_period = 20

    assign line short_ma = MA([symbol], short_period)
    assign line long_ma = MA([symbol], long_period)

    always@(short_ma crossabove long_ma) 
        buy 100

    always@(short_ma crossbelow long_ma) 
        sell 100
}



