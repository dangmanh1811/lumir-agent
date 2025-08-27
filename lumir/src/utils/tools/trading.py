
import os
import pandas as pd
import math
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

def read_trading_excel(file_path: str) -> pd.DataFrame:
    """Đọc file Excel giao dịch và trả về DataFrame đã được làm sạch"""
    try:
        # Đọc file Excel
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.xls'):
            df = pd.read_excel(file_path, engine='xlrd')
        else:
            raise ValueError("File phải có định dạng .xlsx hoặc .xls")
        
        # Làm sạch tên cột
        df.columns = [str(col).strip() for col in df.columns]
        
        # Ánh xạ tên cột về tiêu chuẩn
        column_mapping = {
            'symbol': ['symbol', 'cặp tiền', 'cặp', 'pair', 'instrument'],
            'side': ['side', 'hướng', 'direction', 'loại', 'type'],
            'close_time': ['close_time', 'thời gian đóng', 'ngày đóng', 'date', 'time'],
            'net_profit': ['net_profit', 'lợi nhuận ròng', 'pnl', 'profit', 'lãi lỗ'],
            'commission': ['commission', 'phí giao dịch', 'phí', 'fee'],
            'swap': ['swap', 'phí qua đêm', 'phí swap', 'overnight'],
            'balance_after': ['balance_after', 'số dư sau', 'balance', 'số dư'],
            'pips': ['pips', 'điểm', 'pip'],
            'volume_lots_closed': ['volume_lots_closed', 'khối lượng đóng', 'volume', 'lot'],
            'quantity_closed': ['quantity_closed', 'số lượng đóng', 'quantity', 'số lượng'],
            'open_price': ['open_price', 'giá mở', 'giá vào lệnh', 'entry price'],
            'close_price': ['close_price', 'giá đóng', 'giá thoát lệnh', 'exit price']
        }
        
        # Áp dụng ánh xạ cột
        for standard_name, possible_names in column_mapping.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    if standard_name not in df.columns:
                        df[standard_name] = df[possible_name]
                    break
        
        # Kiểm tra cột bắt buộc
        required_columns = ['symbol', 'side', 'close_time', 'net_profit']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Thiếu cột bắt buộc: {missing_columns}")
        
        return df
        
    except Exception as e:
        print(f"Lỗi đọc file Excel: {e}")
        raise

def calculate_trade_index(df: pd.DataFrame):
    """Tính toán các chỉ số giao dịch từ dữ liệu"""
    # Chuẩn hóa tên cột
    df = df.rename(columns={c: c.strip() for c in df.columns})
    
    # Chuyển đổi giá trị hướng từ tiếng Việt sang tiếng Anh
    if 'side' in df.columns:
        df['side'] = df['side'].replace({'Mua': 'BUY', 'Bán': 'SELL'})
    
    # Chuyển đổi cột thời gian
    if 'close_time' in df.columns:
        df['close_time'] = pd.to_datetime(df['close_time'], errors='coerce', dayfirst=True)
        df['hour'] = df['close_time'].dt.hour
        df['date'] = df['close_time'].dt.date
    
    # Ép kiểu số cho các cột số
    numeric_cols = ['commission', 'swap', 'net_profit', 'balance_after', 'pips', 'volume_lots_closed']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Tính toán các chỉ số cơ bản
    trades = len(df)
    win_trades = df[df['net_profit'] > 0]
    loss_trades = df[df['net_profit'] < 0]
    
    win_rate_pct = (len(win_trades) / trades * 100.0) if trades > 0 else 0.0
    net_profit = float(df['net_profit'].sum()) if 'net_profit' in df.columns else 0.0
    avg_profit_per_trade = net_profit / trades if trades > 0 else 0.0
    
    profit_win = float(win_trades['net_profit'].mean()) if len(win_trades) > 0 else 0.0
    loss_loss = float(loss_trades['net_profit'].mean()) if len(loss_trades) > 0 else 0.0
    
    # Tính hệ số lợi nhuận
    total_profit = float(win_trades['net_profit'].sum()) if len(win_trades) > 0 else 0.0
    total_loss = abs(float(loss_trades['net_profit'].sum())) if len(loss_trades) > 0 else 0.0
    profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
    
    # Tìm lệnh thắng và thua nhất
    best_trade = float(df['net_profit'].max()) if 'net_profit' in df.columns else 0.0
    worst_trade = float(df['net_profit'].min()) if 'net_profit' in df.columns else 0.0
    
    # Tính số lệnh lỗ liên tiếp tối đa
    max_consecutive_losses = 0
    current_streak = 0
    for profit in df['net_profit']:
        if profit < 0:
            current_streak += 1
            max_consecutive_losses = max(max_consecutive_losses, current_streak)
        else:
            current_streak = 0
    
    # Phân tích theo cặp tiền
    symbol_analysis = {}
    if 'symbol' in df.columns:
        for symbol in df['symbol'].unique():
            symbol_trades = df[df['symbol'] == symbol]
            symbol_analysis[symbol] = {
                'trades': len(symbol_trades),
                'profit': float(symbol_trades['net_profit'].sum()),
                'win_rate': len(symbol_trades[symbol_trades['net_profit'] > 0]) / len(symbol_trades) * 100
            }
    
    return {
        'trades': trades,
        'net_profit': net_profit,
        'win_rate_pct': win_rate_pct,
        'avg_profit_per_trade': avg_profit_per_trade,
        'avg_profit_win': profit_win,
        'avg_loss_loss': loss_loss,
        'profit_factor': profit_factor,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'max_consecutive_losses': max_consecutive_losses,
        'symbol_analysis': symbol_analysis
    }

def generate_comprehensive_report(df: pd.DataFrame, result: Dict[str, Any]) -> str:
    """Tạo báo cáo tổng hợp từ dữ liệu giao dịch"""
    
    report_parts = [
        "📊 BÁO CÁO TỔNG QUAN GIAO DỊCH",
        "=" * 50,
        "",
        "📈 TỔNG QUAN",
        f"• Tổng số lệnh: {result['trades']}",
        f"• Tổng lợi nhuận: {result['net_profit']:,.2f}",
        f"• Tỷ lệ thắng: {result['win_rate_pct']:.1f}%",
        f"• Lợi nhuận trung bình/lệnh: {result['avg_profit_per_trade']:,.2f}",
        "",
        "🎯 HIỆU SUẤT",
        f"• Lệnh thắng trung bình: {result['avg_profit_win']:,.2f}",
        f"• Lệnh thua trung bình: {result['avg_loss_loss']:,.2f}",
        f"• Hệ số lợi nhuận: {result['profit_factor']:.2f}",
        f"• Lệnh thắng nhất: {result['best_trade']:,.2f}",
        f"• Lệnh thua nhất: {result['worst_trade']:,.2f}",
        "",
        "⚠️ RỦI RO",
        f"• Số lệnh lỗ liên tiếp tối đa: {result['max_consecutive_losses']}",
        "",
        "💱 PHÂN TÍCH CẶP TIỀN"
    ]
    
    # Thêm phân tích theo từng cặp tiền
    for symbol, data in result['symbol_analysis'].items():
        report_parts.append(f"• {symbol}: {data['trades']} lệnh, lợi nhuận: {data['profit']:,.2f}, win rate: {data['win_rate']:.1f}%")
    
    # Thêm đánh giá tổng quan
    report_parts.extend([
        "",
        "🎯 ĐÁNH GIÁ TỔNG QUAN"
    ])
    
    # Đánh giá hiệu suất
    if result['win_rate_pct'] >= 60:
        report_parts.append("• Hiệu suất: 🟢 Tuyệt vời (>60% win rate)")
    elif result['win_rate_pct'] >= 50:
        report_parts.append("• Hiệu suất: 🟡 Tốt (50-60% win rate)")
    else:
        report_parts.append("• Hiệu suất: 🔴 Cần cải thiện (<50% win rate)")
    
    # Đánh giá rủi ro
    max_risk_per_trade = abs(result['worst_trade'])
    if max_risk_per_trade <= 50:
        report_parts.append(f"• Quản lý rủi ro: 🟢 Tốt (rủi ro/lệnh: {max_risk_per_trade:,.2f})")
    else:
        report_parts.append(f"• Quản lý rủi ro: 🔴 Cần kiểm tra (rủi ro/lệnh: {max_risk_per_trade:,.2f})")
    
    return "\n".join(report_parts)

def analyze_trading_excel(file_path: str) -> Dict[str, Any]:
    """
    Phân tích file Excel dữ liệu giao dịch và trả về nhận định tổng hợp
    
    Args:
        file_path: Đường dẫn đến file Excel
        
    Returns:
        Dict chứa kết quả phân tích và báo cáo
        
    Example:
        >>> result = analyze_trading_excel("trading_data.xlsx")
        >>> print(result["report"])  # Xem báo cáo tổng hợp
    """
    try:
        print(f"🔍 Đang phân tích file Excel: {file_path}")
        
        # Đọc dữ liệu
        df = read_trading_excel(file_path)
        print(f"✅ Đọc thành công: {len(df)} dòng dữ liệu")
        
        # Tính toán chỉ số
        result = calculate_trade_index(df)
        print(f"✅ Tính toán chỉ số hoàn thành")
        
        # Tạo báo cáo
        report = generate_comprehensive_report(df, result)
        print(f"✅ Tạo báo cáo hoàn thành")
        
        return {
            "success": True,
            "data": df,
            "result": result,
            "report": report,
            "file_path": file_path,
            "summary": {
                "total_trades": result['trades'],
                "net_profit": result['net_profit'],
                "win_rate": result['win_rate_pct']
            }
        }
        
    except Exception as e:
        error_msg = f"Lỗi phân tích: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "file_path": file_path
        }