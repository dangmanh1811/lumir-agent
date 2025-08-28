#!/usr/bin/env python3
"""
Trading Workflow Test Script

This script tests the complete trading workflow including:
- Agent analysis and execution
- Trading data processing
- Context generation from analysis results
- DSPy-based agent execution

Author: Lumir AI Team
Date: 2025
"""

import sys
import os
from typing import Dict, List

# Path configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lumir', 'src'))

# Import required modules
from lumir.src.core.agent.agent_loader import NodeAgentLoader
from lumir.src.utils.tools.trading import analyze_trading_excel

def extract_output_json(output_messages) -> Dict:
    """Extract dictionary data from DSPy Prediction object"""
    plan_dict = vars(output_messages) if hasattr(output_messages, '__dict__') else dict(output_messages)
    extracted_data = plan_dict['_store']
    return extracted_data

def get_trading_context_from_analysis(analysis_result: Dict) -> str:
    """Generate context sources for execute_agent based on analysis results"""
    
    # Get trading data analysis result
    trading_result = analyze_trading_excel("./docs/test_sample.xlsx")
    
    # Suppress the print output from analyze_trading_excel
    import os
    import io
    from contextlib import redirect_stderr, redirect_stdout
    
    # Redirect stdout and stderr to null
    with open(os.devnull, 'w') as devnull:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            trading_result = analyze_trading_excel("./docs/test_sample.xlsx")
    
    if not trading_result.get("success"):
        return "Cannot retrieve trading data"
    
    result_data = trading_result.get("result", {})
    
    # Build context from trading analysis
    context_parts = []
    
    # Overview context
    context_parts.append("trading_data: Detailed trading history with total " + 
                        str(result_data.get('trades', 0)) + " trades. Net profit: " +
                        f"{result_data.get('net_profit', 0):,.2f}. Win rate: " +
                        f"{result_data.get('win_rate_pct', 0):.1f}%.")
    
    # Performance metrics
    avg_profit_win = result_data.get('avg_profit_win', 0)
    avg_loss_loss = result_data.get('avg_loss_loss', 0)
    profit_factor = result_data.get('profit_factor', 0)
    
    context_parts.append(f"performance_metrics: Performance details - Average win: {avg_profit_win:,.2f}, " +
                        f"Average loss: {avg_loss_loss:,.2f}, Profit factor: {profit_factor:.2f}.")
    
    # Risk analysis
    max_drawdown = result_data.get('max_drawdown_pct', 0)
    max_consecutive_losses = result_data.get('max_consecutive_losses', 0)
    
    context_parts.append(f"risk_analysis: Risk analysis - Max drawdown: {max_drawdown:.1f}%, " +
                        f"Max consecutive losses: {max_consecutive_losses}. Risk management needs improvement.")
    
    # Symbol analysis
    symbol_analysis = result_data.get('symbol_analysis', {})
    if symbol_analysis:
        symbol_context = "symbol_analysis: Symbol analysis - "
        for symbol, data in symbol_analysis.items():
            symbol_context += f"{symbol}: {data['trades']} trades, profit {data['profit']:,.2f}, win rate {data['win_rate']:.1f}%. "
        context_parts.append(symbol_context)
    
    # Behavioral patterns
    behavioral = result_data.get('behavioral', {})
    rapid_fire_ratio = behavioral.get('rapid_fire_ratio', 0) if behavioral else 0
    
    context_parts.append(f"behavioral_patterns: Trading behavior - Rapid trade ratio: {rapid_fire_ratio:.1%}. " +
                        "Need to control trading patterns for better optimization.")
    
    # Win rate analysis
    win_rate = result_data.get('win_rate_pct', 0)
    if win_rate >= 60:
        win_rate_context = "win_rate: High win rate (>=60%) shows good trading performance."
    elif win_rate >= 50:
        win_rate_context = "win_rate: Medium win rate (50-60%) needs improvement."
    else:
        win_rate_context = "win_rate: Low win rate (<50%) needs better risk management system."
    
    context_parts.append(win_rate_context)
    
    # Join all context parts
    return "\n\n".join(context_parts)

def test_trading_workflow():
    """Test the complete trading workflow"""
    
    try:
        # Step 1: Initialize the NodeAgentLoader for trading
        agent_node = NodeAgentLoader(config_path='config/agent_node/trading_v2.json')
        
        # Step 2: Test analyze_agent
        # test_question = "Phan tich hieu suat giao dich cua toi trong thoi gian qua"
        test_question = "Hãy phân tích hiệu suất giao dịch của tôi trong thời gian qua và hãy đưa cho tôi một vào cách để có thể tăng hiệu suất giao dịch, để tôi có thể lời vãi cả lều"
        
        analyze_input = {
            'users_question': test_question,
            'user_id': 'test_user_001',
            'task': 'analyze_trading_performance',
            'status': 'ready'
        }
        
        analyze_result = agent_node.analyze_agent(analyze_input)
        analyze_data = extract_output_json(analyze_result)
        
        print(analyze_data)
        # quit()

        # Step 3: Generate context and test execute_agent
        trading_context = get_trading_context_from_analysis(analyze_data)
        print(trading_context)
        # quit()

        execute_input = {
            'users_question': test_question,
            'user_id': 'test_user_001',
            'task': 'generate_trading_advice',
            'status': 'ready',
            'plan': analyze_data.get('plan', ''),
            'response': analyze_data.get('response', []),
            'context_sources': trading_context
        }
        
        execute_result = agent_node.execute_agent(execute_input)
        execute_data = extract_output_json(execute_result)

        return execute_data['response']
    
    except Exception as e:
        print(f"Error in test_trading_workflow: {e}")
        return None
    
        
    

if __name__ == "__main__":
    print("Starting trading workflow test...")
    
    # Run the workflow test
    success = test_trading_workflow()
    print(success)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)



