# test_akfinance.py
import sys
import os

# 添加当前目录到 Python 路径，这样可以直接导入 akfinance
sys.path.append(os.path.dirname(__file__))

import akfinance as yf
import pandas as pd
import matplotlib.pyplot as plt


def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试 AKFinance 基本功能 ===")

    # 测试 1: 使用 download 函数
    print("\n1. 测试 download 函数:")
    data = yf.download('600519.SH', start='2023-01-01', end='2024-01-01')
    print(f"数据形状: {data.shape}")
    print(data.head())

    # 测试 2: 使用 Ticker 类
    print("\n2. 测试 Ticker 类:")
    kweichow = yf.Ticker('600519.SH')
    info = kweichow.info()
    history_data = kweichow.history(period="6mo")

    print(f"股票信息: {info}")
    print(f"历史数据形状: {history_data.shape}")
    print(history_data.head())

    # 测试 3: 多股票下载
    print("\n3. 测试多股票下载:")
    multiple_data = yf.download(['000001.SZ', '600519.SH'], period="3mo")
    print(f"多股票数据形状: {multiple_data.shape}")
    print(multiple_data.head())

    return data, info, history_data, multiple_data


def test_plotting(data):
    """测试绘图功能"""
    print("\n=== 测试绘图功能 ===")

    plt.figure(figsize=(12, 8))

    # 绘制价格走势
    plt.subplot(2, 1, 1)
    plt.plot(data.index, data['Close'], label='Close Price', linewidth=2)
    plt.title('贵州茅台股价走势')
    plt.ylabel('价格 (元)')
    plt.legend()
    plt.grid(True)

    # 绘制成交量
    plt.subplot(2, 1, 2)
    plt.bar(data.index, data['Volume'], alpha=0.7, color='orange')
    plt.title('成交量')
    plt.ylabel('成交量')
    plt.xlabel('日期')
    plt.grid(True)

    plt.tight_layout()
    plt.show()


def test_different_tickers():
    """测试不同的股票代码格式"""
    print("\n=== 测试不同股票代码格式 ===")

    tickers = [
        '600519',  # 简写上交所代码
        '600519.SH',  # 完整上交所代码
        '000001',  # 简写深交所代码
        '000001.SZ',  # 完整深交所代码
        '00700.HK',  # 港股代码
    ]

    for ticker in tickers:
        try:
            print(f"\n测试 {ticker}:")
            stock = yf.Ticker(ticker)
            data = stock.history(period="1mo")
            print(f"  数据形状: {data.shape}")
            info = stock.info()
            print(f"  市场: {info.get('market', 'N/A')}")
            print(f"  交易所: {info.get('exchange', 'N/A')}")
        except Exception as e:
            print(f"  {ticker} 失败: {e}")


if __name__ == "__main__":
    # 运行所有测试
    data, info, history_data, multiple_data = test_basic_functionality()
    test_different_tickers()

    # 只有在有数据时才绘图
    if not data.empty:
        test_plotting(data)
    else:
        print("没有数据可用于绘图")

    print("\n=== 测试完成 ===")