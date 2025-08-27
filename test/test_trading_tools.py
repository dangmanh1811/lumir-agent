#!/usr/bin/env python3
"""
Test script for trading tools
"""

import os
import sys
from pathlib import Path

# Add path for import
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lumir', 'src'))

from lumir.src.utils.tools.trading import analyze_trading_excel

def test_trading_analysis():
    """Test the trading analysis function"""
    # Path to Excel file
    excel_file = os.path.join(project_root, 'docs', 'test_sample.xlsx')
    
    print("=" * 60)
    print("TEST TRADING TOOLS")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(excel_file):
        print(f"Excel file not found: {excel_file}")
        return False
    
    print(f"Excel file found: {excel_file}")
    
    try:
        # Test trading analysis
        print(f"Testing trading analysis...")
        result = analyze_trading_excel(excel_file)
        
        # Check result structure
        if not result.get("success"):
            print(f"Analysis failed: {result.get('error', 'Unknown error')}")
            return False
        
        print(f"Analysis successful!")
        
        # Print summary
        summary = result.get("summary", {})
        print(f"SUMMARY:")
        print(f"  - Total trades: {summary.get('total_trades', 'N/A')}")
        print(f"  - Net profit: {summary.get('net_profit', 'N/A'):,.2f}")
        print(f"  - Win rate: {summary.get('win_rate', 'N/A'):.1f}%")
        
        # Print detailed report
        report = result.get("report", "")
        if report:
            print(f"DETAILED REPORT:")
            print(report)
        
        # Print symbol analysis
        result_data = result.get("result", {})
        symbol_analysis = result_data.get("symbol_analysis", {})
        if symbol_analysis:
            print(f"SYMBOL ANALYSIS:")
            for symbol, data in symbol_analysis.items():
                print(f"  - {symbol}: {data.get('trades', 0)} trades, "
                      f"profit: {data.get('profit', 0):,.2f}, "
                      f"win rate: {data.get('win_rate', 0):.1f}%")
        
        print(f"Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

def test_edge_cases():
    """Test edge cases"""
    print(f"")
    print("=" * 60)
    print("TEST EDGE CASES")
    print("=" * 60)
    
    # Test with non-existent file
    print(f"Testing with non-existent file...")
    result = analyze_trading_excel("non_existent_file.xlsx")
    if not result.get("success"):
        print(f"Correctly handled non-existent file: {result.get('error')}")
    else:
        print(f"Should have failed for non-existent file")
        return False
    
    # Test with invalid file extension
    print(f"Testing with invalid file extension...")
    # Create a temporary text file
    temp_file = os.path.join(project_root, 'temp_test.txt')
    with open(temp_file, 'w') as f:
        f.write("This is not an Excel file")
    
    try:
        result = analyze_trading_excel(temp_file)
        if not result.get("success"):
            print(f"Correctly handled invalid file format: {result.get('error')}")
        else:
            print(f"Should have failed for invalid file format")
            return False
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    print(f"Edge cases test completed!")
    return True

if __name__ == "__main__":
    print("Starting trading tools tests...")
    
    # Run main test
    main_test_passed = test_trading_analysis()
    
    # Run edge cases test
    edge_cases_test_passed = test_edge_cases()
    
    # Final result
    print(f"")
    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    if main_test_passed and edge_cases_test_passed:
        print(f"ALL TESTS PASSED!")
        print(f"Trading tools are working correctly")
        sys.exit(0)
    else:
        print(f"SOME TESTS FAILED!")
        print(f"Main test: {'PASSED' if main_test_passed else 'FAILED'}")
        print(f"Edge cases test: {'PASSED' if edge_cases_test_passed else 'FAILED'}")
        sys.exit(1)



