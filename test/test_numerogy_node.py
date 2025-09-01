import json
from lumir.src.core.agent.agent_loader import AgentNode

from lumir.src.utils.logging import Logger, get_logger

from lumir.src.utils.tools.numerology import S3Client, CalNum

from typing import List, Dict


logger = get_logger(__name__)

def get_numerology_context( list_key_word: List) -> Dict[str, str]:
    """Get numerology context from S3 based on specified keywords
    
    Args:
        name (str): Person's name
        birthday (str): Birth date in dd/mm/yyyy format
        list_key_word (List): List of keywords to retrieve context for
        
    Returns:
        Dict[str, str]: Dictionary containing context for requested keywords
    """
    try:   
        name = 'Hồ Đăng Mạnh'
        birthday = '18/11/2004'
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





def test_node():
    config_data = '/home/clara/chaos/repo/lumir-agent/config/agent_node/numerogy_v2.json'
    with open(config_data, 'r', encoding ='utf-8') as f:
        config_data = json.load(f)

    agent_node = AgentNode(config_data)
    agent_node.get_agent_chain_info()

    # Test with function

    input_data = {

        "user_question": 'Ngày hôm nay tôi nên trading làm gì để tốt hơn hả.'
    }

    agent_result = agent_node.execute(input_data, get_numerology_context)

    return agent_result

if __name__ =='__main__':
    # result = get_numerology_context(['life_path', 'soul'])

    result = test_node()
    print(result)