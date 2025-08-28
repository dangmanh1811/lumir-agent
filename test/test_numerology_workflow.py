
#!/usr/bin/env python3
"""
Numerology Workflow Test Script

This script tests the complete numerology workflow including:
- Agent analysis and execution
- S3 context retrieval
- Keyword parsing and processing
- Numerology calculations

Author: Lumir AI Team
Date: 2025
"""

import sys
import os
from typing import Dict, List

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Add path for import
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'lumir', 'src'))

# ============================================================================
# IMPORTS
# ============================================================================

from lumir.src.utils.tools.numerology import S3Client, CalNum
from lumir.src.core.agent.agent_loader import NodeAgentLoader

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_numerology_context(name: str, birthday: str, list_key_word: List) -> Dict[str, str]:
    """Get numerology context from S3 based on specified keywords
    
    Args:
        name (str): Person's name
        birthday (str): Birth date in dd/mm/yyyy format
        list_key_word (List): List of keywords to retrieve context for
        
    Returns:
        Dict[str, str]: Dictionary containing context for requested keywords
    """
    try:   
        calculator = CalNum(dob=birthday, name=name)
        s3_client = S3Client()
        
        context_sources = {}
        
        # Calculate all numerology numbers
        life_path = calculator.calculate_life_path()
        soul_number = calculator.calculate_soul()
        personality_number = calculator.calculate_personality()
        balance_number = calculator.calculate_balance()
        maturity_number = calculator.calculate_maturity()
        
        # Mapping keywords to S3 paths and calculated numbers
        keyword_mapping = {
            'life_path': ('life_path', life_path),
            'purpose': ('purpose', life_path),  # Purpose often relates to life path
            'soul': ('soul', soul_number),
            'balance': ('balance', balance_number),
            'personality': ('personality', personality_number),
            'attitude': ('attitude', personality_number),  # Attitude relates to personality
            'maturity': ('maturity', maturity_number),
            'passion': ('passion', soul_number),  # Passion relates to soul number
            'birth_day': ('birth_day', calculator.calculate_birth_day() if hasattr(calculator, 'calculate_birth_day') else life_path),
            'rational_thinking': ('rational_thinking', balance_number),  # Rational thinking relates to balance
            'lifepath_life_purpose_link': ('lifepath_life_purpose_link', life_path),
            'soul_personality_link': ('soul_personality_link', f"{soul_number}_{personality_number}")
        }
        
        # Get information from S3 only for requested keywords
        for keyword in list_key_word:
            if keyword in keyword_mapping:
                s3_path, number_value = keyword_mapping[keyword]
                try:
                    context_sources[keyword] = s3_client.get_document_text_for_numerology(s3_path, number_value)
                except Exception as e:
                    # Fallback information if S3 retrieval fails
                    context_sources[keyword] = f"Information about {keyword} number {number_value}"
            else:
                # Handle unknown keywords
                context_sources[keyword] = f"No information available for keyword: {keyword}"
        
        return context_sources
    
    except Exception as e:
        print(f"Error getting numerology context: {e}")
        return {}

def extract_output_json(output_messages) -> Dict:
    """
    Extract dictionary data from DSPy Prediction object
    
    Args:
        output_messages: DSPy Prediction object containing agent response
        
    Returns:
        Dict: Extracted data from the _store attribute
    """
    plan_dict = vars(output_messages) if hasattr(output_messages, '__dict__') else dict(output_messages)
    extracted_data = plan_dict['_store']
    return extracted_data 

def test_numerology_workflow_v2():
    # Initialize agent
    agent_node = NodeAgentLoader(config_path='config/agent_node/numerogy_v2.json')

    # Test data
    test_data = {
        'name': 'Hồ Đăng Mạnh',
        'birth_date': '18/11/2004'
    }

    user_question = "Hôm nay kết quả trading nó không tốt, tôi đã bị thua lỗ rất nhiều. Nhưng tôi không biết tại sao."

    plan = agent_node.analyze_agent({'user_question': user_question})

    # extract keyword
    keyword_plan = extract_output_json(plan)
    

def test_numerology_workflow():

    # Init agent
    agent_node = NodeAgentLoader(config_path='config/agent_node/numerogy_v2.json')
    
    # Test data
    test_data = {
        "name": "Hồ Đăng Mạnh",
        "birth_date": "18/11/2004",
        "question": "Tôi muốn biết về tính cách và vận mệnh của mình"
    }
    
    user_question = "Hôm nay kết quả trading nó không tốt, tôi đã bị thua lỗ rất nhiều. Nhưng tôi k biết tại sao."

    plan = agent_node.analyze_agent({'users_question': user_question})
 
    # extract key word 
    keyword_plan = extract_output_json(plan)
    response = keyword_plan['response']
  
    # Parse the keyword response if it's a string representation of a list
    if isinstance(response, str) and response.startswith('[') and response.endswith(']'):
        try:
            # Remove brackets and split by comma, then clean each keyword
            keyword_list = [k.strip().strip("'\"") for k in response[1:-1].split(',')]
        except:
            # Fallback to default keywords if parsing fails
            keyword_list = ['life_path', 'purpose', 'soul', 'balance', 'personality', 'attitude', 'maturity', 'passion', 'birth_day', 'rational_thinking', 'lifepath_life_purpose_link', 'soul_personality_link']
    elif isinstance(response, list):
        keyword_list = response
    else:
        # Default keywords if format is unexpected
        keyword_list = ['life_path', 'purpose', 'soul', 'balance', 'personality', 'attitude', 'maturity', 'passion', 'birth_day', 'rational_thinking', 'lifepath_life_purpose_link', 'soul_personality_link']
    
    numerology_context = get_numerology_context(test_data['name'], test_data['birth_date'], keyword_list)
    context_source = "\n\n".join([f"{key}: {value}" for key, value in numerology_context.items()])
    
    # Loop checker agent to refine response
    n_attempts = 3 # Hyper-parameter to control the number of attempts
    execute_response = None
    evaluated_response = None
    for _ in range(n_attempts):
        print(f"------ Iteration {_ + 1} ------")
        execute_result = agent_node.execute_agent({'users_question': user_question, 'context_sources': context_source, 'draft_response': execute_response, "feedback": evaluated_response})
        execute_result_json = extract_output_json(execute_result)

        execute_response = execute_result_json['response']
        plan_execute = execute_result_json['plan']

        print(execute_response)
        
        checker_result = agent_node.checker_agent({'users_question': user_question, 'context_sources': context_source, 'response': execute_response, 'plan': plan_execute})
        checker_result_json = extract_output_json(checker_result)
        
        evaluated_response = checker_result_json['response']
        evaluated_response_states = checker_result_json['states']
        if evaluated_response_states == 'success':
            print("States is success, break the loop")
            break
    
    if evaluated_response_states == 'failed':
        print("States is failed, return the last response")

    return evaluated_response
    
        

            

    # return response_execute
    return execute_result

if __name__ == "__main__":
    # test_numerology()
    # execute_result = test_numerrology_workflow()
    # print(execute_result)

    checker_result = test_numerology_workflow()
    print(checker_result)
