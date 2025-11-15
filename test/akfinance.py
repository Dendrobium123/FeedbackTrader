# akfinance.py
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Optional, Union, List
import warnings


class AKFinance:
    """
    将 AKShare 接口封装成 yfinance 风格的类
    """

    def __init__(self, ticker: str):
        """
        初始化

        Parameters:
        -----------
        ticker : str
            股票代码，支持多种格式：
            - A股: '000001'、'000001.SZ'、'600519.SH'
            - 港股: '00700'、'00700.HK'
            - 美股: 'AAPL'、'TSLA'
        """
        self.ticker = self._standardize_ticker(ticker)
        self.history_data = None

    def _standardize_ticker(self, ticker: str) -> str:
        """标准化股票代码 - 修复 .SS 后缀问题"""
        # 移除可能的空格
        ticker = ticker.replace(' ', '').upper()

        # 处理 .SS 后缀（yfinance 格式）转换为 .SH
        if ticker.endswith('.SS'):
            ticker = ticker.replace('.SS', '.SH')

        # 如果已经包含正确的交易所代码，直接返回
        if '.' in ticker:
            return ticker

        # 根据代码规则判断交易所
        if ticker.startswith(('00', '30')):  # 深交所
            return f"{ticker}.SZ"
        elif ticker.startswith(('50', '51', '60', '68', '90')):  # 上交所
            return f"{ticker}.SH"
        elif ticker.startswith(('0', '1', '2', '3', '4', '5')) and len(ticker) == 5:  # 港股
            return f"{ticker}.HK"
        else:  # 默认作为美股或其他
            return f"{ticker}"

    def _convert_date(self, date_str: Union[str, datetime]) -> str:
        """转换日期格式"""
        if isinstance(date_str, datetime):
            return date_str.strftime('%Y%m%d')
        return date_str.replace('-', '')

    def _safe_ak_call(self, func, *args, **kwargs):
        """安全调用 AKShare 函数，处理 None 返回值"""
        try:
            result = func(*args, **kwargs)
            if result is None:
                print(f"AKShare 返回 None: {func.__name__} with args {args} {kwargs}")
                return pd.DataFrame()
            return result
        except Exception as e:
            print(f"AKShare 调用失败: {func.__name__} with args {args} {kwargs}, error: {e}")
            return pd.DataFrame()

    def info(self) -> dict:
        """获取股票基本信息"""
        try:
            ticker_clean = self.ticker.split('.')[0]
            exchange = self.ticker.split('.')[-1] if '.' in self.ticker else ''

            print(f"获取股票信息: {self.ticker}, 代码: {ticker_clean}, 交易所: {exchange}")

            if exchange in ['SH', 'SZ']:
                # A股信息
                stock_info = self._safe_ak_call(ak.stock_individual_info_em, symbol=ticker_clean)

                if stock_info.empty:
                    print(f"未获取到 {self.ticker} 的基本信息")
                    return self._get_default_info()

                info_dict = {
                    'symbol': self.ticker,
                    'shortName': self._get_info_value(stock_info, '股票简称', ticker_clean),
                    'longName': self._get_info_value(stock_info, '公司全称', ticker_clean),
                    'exchange': exchange,
                    'currency': 'CNY',
                    'market': 'cn'
                }
                print(f"成功获取基本信息: {info_dict['shortName']}")

            else:
                # 其他市场（简化处理）
                info_dict = {
                    'symbol': self.ticker,
                    'shortName': ticker_clean,
                    'longName': ticker_clean,
                    'exchange': exchange,
                    'currency': 'USD' if exchange not in ['SH', 'SZ', 'HK'] else 'HKD',
                    'market': 'us' if exchange not in ['SH', 'SZ', 'HK'] else 'hk'
                }

            return info_dict

        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return self._get_default_info()

    def _get_info_value(self, df, item_name, default):
        """安全获取信息值"""
        try:
            filtered = df[df['item'] == item_name]
            if not filtered.empty and 'value' in filtered.columns:
                return filtered['value'].iloc[0]
            return default
        except:
            return default

    def _get_default_info(self):
        """获取默认信息"""
        return {
            'symbol': self.ticker,
            'shortName': self.ticker.split('.')[0],
            'longName': self.ticker.split('.')[0],
            'exchange': self.ticker.split('.')[-1] if '.' in self.ticker else 'Unknown',
            'currency': 'CNY',
            'market': 'cn'
        }

    def history(self,
                start: Optional[str] = None,
                end: Optional[str] = None,
                period: str = "1y",
                interval: str = "1d",
                actions: bool = False,
                auto_adjust: bool = True) -> pd.DataFrame:
        """
        获取历史价格数据
        """
        try:
            ticker_clean = self.ticker.split('.')[0]
            exchange = self.ticker.split('.')[-1] if '.' in self.ticker else ''

            # 设置默认日期范围
            end_date = self._convert_date(end) if end else datetime.now().strftime('%Y%m%d')
            start_date = self._get_start_date(start, period)

            print(f"获取数据: {self.ticker}, 期间: {start_date} 到 {end_date}, 间隔: {interval}")

            # 根据不同的市场和间隔获取数据
            df = self._get_market_data(ticker_clean, exchange, start_date, end_date, interval, auto_adjust)

            if df is None or df.empty:
                print(f"未获取到 {self.ticker} 的历史数据")
                return pd.DataFrame()

            print(f"成功获取数据，形状: {df.shape}")

            # 标准化数据格式
            df = self._standardize_dataframe(df, exchange)

            self.history_data = df
            return df

        except Exception as e:
            print(f"获取历史数据失败: {e}")
            return pd.DataFrame()

    def _get_start_date(self, start, period):
        """根据周期获取开始日期"""
        if start:
            return self._convert_date(start)

        period_days = {
            "1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
            "1y": 365, "2y": 730, "5y": 1825, "10y": 3650
        }

        days = period_days.get(period, 365)
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

        # 对于年初至今的情况
        if period == "ytd":
            start_date = datetime.now().replace(month=1, day=1).strftime('%Y%m%d')

        return start_date

    def _get_market_data(self, ticker, exchange, start_date, end_date, interval, auto_adjust):
        """根据市场获取数据"""
        adjust = "qfq" if auto_adjust else ""

        try:
            if exchange in ['SH', 'SZ']:
                # A股数据
                period_map = {"1d": "daily", "1wk": "weekly", "1mo": "monthly"}
                period = period_map.get(interval, "daily")

                print(f"调用 A股接口: stock_zh_a_hist({ticker}, {period}, {start_date}, {end_date})")

                df = self._safe_ak_call(ak.stock_zh_a_hist,
                                        symbol=ticker,
                                        period=period,
                                        start_date=start_date,
                                        end_date=end_date,
                                        adjust=adjust)

            elif exchange == 'HK':
                # 港股数据
                print(f"调用港股接口: stock_hk_hist({ticker}, {start_date}, {end_date})")
                df = self._safe_ak_call(ak.stock_hk_hist,
                                        symbol=ticker,
                                        start_date=start_date,
                                        end_date=end_date,
                                        adjust=adjust)

            else:
                # 美股数据
                print(f"调用美股接口: stock_us_hist({ticker}, {start_date}, {end_date})")
                df = self._safe_ak_call(ak.stock_us_hist,
                                        symbol=ticker,
                                        start_date=start_date,
                                        end_date=end_date,
                                        adjust=adjust)

            return df

        except Exception as e:
            print(f"获取 {exchange} 市场数据失败: {e}")
            return pd.DataFrame()

    def _standardize_dataframe(self, df, exchange):
        """标准化 DataFrame 格式"""
        if df is None or df.empty:
            return pd.DataFrame()

        # 复制 DataFrame 避免修改原始数据
        df = df.copy()

        print(f"原始数据列名: {df.columns.tolist()}")
        print(f"原始数据形状: {df.shape}")

        # 重命名列
        column_mapping = self._get_column_mapping(exchange)
        df = df.rename(columns=column_mapping)

        # 设置日期索引
        date_columns = ['Date', '日期', 'date', 'datetime']
        date_column = None
        for col in date_columns:
            if col in df.columns:
                date_column = col
                break

        if date_column:
            df[date_column] = pd.to_datetime(df[date_column])
            df = df.set_index(date_column)
            print(f"使用日期列: {date_column}")
        else:
            # 如果没有日期列，创建默认索引
            print("未找到日期列，创建默认索引")
            df.index = pd.date_range(start=datetime.now() - timedelta(days=len(df)),
                                     periods=len(df), freq='D')

        # 确保有必要的列
        necessary_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in necessary_columns:
            if col not in df.columns:
                print(f"添加缺失列: {col}")
                df[col] = 0.0

        print(f"处理后的列名: {df.columns.tolist()}")

        return df

    def _get_column_mapping(self, exchange):
        """获取列名映射"""
        base_mapping = {
            '开盘': 'Open',
            '收盘': 'Close',
            '最高': 'High',
            '最低': 'Low',
            '成交量': 'Volume',
            '成交额': 'Amount',
            '振幅': 'Amplitude',
            '涨跌幅': 'Percent',
            '涨跌额': 'Change',
            '换手率': 'Turnover',
            '日期': 'Date',
            '时间': 'Time'
        }

        return base_mapping

    def dividends(self) -> pd.Series:
        """获取股息数据"""
        try:
            ticker_clean = self.ticker.split('.')[0]
            exchange = self.ticker.split('.')[-1] if '.' in self.ticker else ''

            if exchange in ['SH', 'SZ']:
                print(f"获取股息数据: {ticker_clean}")
                div_df = self._safe_ak_call(ak.stock_dividend_detail, indicator="分红", symbol=ticker_clean)
                if not div_df.empty and '除权除息日' in div_df.columns and '派息比例' in div_df.columns:
                    div_df['除权除息日'] = pd.to_datetime(div_df['除权除息日'])
                    div_df = div_df.set_index('除权除息日')
                    return div_df['派息比例']
            return pd.Series()
        except Exception as e:
            print(f"获取股息数据失败: {e}")
            return pd.Series()

    def splits(self) -> pd.Series:
        """获取拆股数据"""
        try:
            ticker_clean = self.ticker.split('.')[0]
            exchange = self.ticker.split('.')[-1] if '.' in self.ticker else ''

            if exchange in ['SH', 'SZ']:
                print(f"获取拆股数据: {ticker_clean}")
                split_df = self._safe_ak_call(ak.stock_dividend_detail, indicator="拆股", symbol=ticker_clean)
                if not split_df.empty and '除权除息日' in split_df.columns and '送转比例' in split_df.columns:
                    split_df['除权除息日'] = pd.to_datetime(split_df['除权除息日'])
                    split_df = split_df.set_index('除权除息日')
                    return split_df['送转比例']
            return pd.Series()
        except Exception as e:
            print(f"获取拆股数据失败: {e}")
            return pd.Series()


# 为兼容性添加 Ticker 类别名
Ticker = AKFinance


# 模拟 yfinance 的 download 函数
def download(symbols: Union[str, List[str]],
             start: Optional[str] = None,
             end: Optional[str] = None,
             period: str = "1y",
             interval: str = "1d",
             group_by: str = 'ticker',
             auto_adjust: bool = True,
             actions: bool = False,
             threads: bool = True,
             progress: bool = True) -> pd.DataFrame:
    """
    模拟 yfinance.download 函数
    """
    if isinstance(symbols, str):
        symbols = [symbols]

    result_dfs = []

    for symbol in symbols:
        if progress:
            print(f"\n正在下载 {symbol}...")

        try:
            ak_stock = AKFinance(symbol)
            df = ak_stock.history(start=start, end=end, period=period,
                                  interval=interval, auto_adjust=auto_adjust)

            if not df.empty:
                print(f"成功下载 {symbol}，数据形状: {df.shape}")
                # 添加多级列索引以匹配 yfinance
                if len(symbols) > 1:
                    df.columns = pd.MultiIndex.from_product([[symbol], df.columns])
                result_dfs.append(df)
            else:
                print(f"未获取到 {symbol} 的数据")

        except Exception as e:
            print(f"下载 {symbol} 失败: {e}")
            continue

    if not result_dfs:
        print("所有股票数据获取失败")
        return pd.DataFrame()

    # 合并所有数据
    if len(result_dfs) == 1:
        final_df = result_dfs[0]
    else:
        # 对齐索引并合并
        all_dates = set()
        for df in result_dfs:
            all_dates.update(df.index)

        all_dates = sorted(all_dates)
        combined_df = pd.DataFrame(index=all_dates)

        for df in result_dfs:
            for col in df.columns:
                combined_df[col] = df[col]

        final_df = combined_df

    print(f"\n最终数据形状: {final_df.shape}")
    return final_df


# 版本信息
__version__ = "1.2.0"
__author__ = "AKFinance Team"