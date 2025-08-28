import json
import re
from textwrap import indent
from typing import Dict, Any
import dspy
from lumir.src.core.agent.client import LLMClient, LLMConfig


class DynamicSignature:

    @staticmethod
    def from_json(input_json, output_json, instruction: str = None):
        """
        """
        class_attrs = {}
        
        for field_name, description in input_json.items():
            class_attrs[field_name] = dspy.InputField(desc=description)
        
        for field_name, description in output_json.items():
            class_attrs[field_name] = dspy.OutputField(desc=description)
        
        new_class = type("AutoSignature", (dspy.Signature,), class_attrs)
        if instruction:
            new_class.__doc__ = instruction
        return new_class

class BaseAgentLoader:
    
    def __init__(self, config_path: str):
        """
        """
        self.config_path = config_path
        self.llm_config = LLMConfig()
        self.llm_client = LLMClient(self.llm_config)
        self.llm_client.client("dspy")
        self.dynamic_signature = DynamicSignature()
    
    def load_config_json(self) -> Dict[str, Any]:
        """
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)


    def execute(self, input_data: Dict[str,any]):
        pass

class PlannerAgentLoader(BaseAgentLoader):  
    def __init__(self, config_path: str):
        super().__init__(config_path)

    def execute(self, input_data: Dict[str, Any]):
        """
        """
        planner_config = self.load_config_json()[0]
        input_json = planner_config['input']
        output_json = planner_config['output']
        signature = self.dynamic_signature.from_json(input_json, output_json)
        planner = dspy.Predict(signature)
        result = planner(**input_data)
        return result


class NodeAgentLoader(BaseAgentLoader):
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        
    def analyze_agent(self, input_data: Dict[str, Any]):
        agent_config = self.load_config_json()[0]
        input_json = agent_config['input']
        output_json = agent_config['output']
        try:
            objective_system_instruction = agent_config['objective_system_instruction']
        except:
            objective_system_instruction = None
        signature = self.dynamic_signature.from_json(input_json, output_json, objective_system_instruction)
        
        planner = dspy.Predict(signature)
        result = planner(**input_data)
        # print("Prompt of analyze agent")
        # print("-"*50)
        # planner.inspect_history(n=1)
        return result
    
    def execute_agent(self, input_data: Dict[str, Any]):
        agent_config = self.load_config_json()[1]
        input_json = agent_config['input']
        output_json = agent_config['output']
        try:
            objective_system_instruction = agent_config['objective_system_instruction']
        except:
            objective_system_instruction = None
        signature = self.dynamic_signature.from_json(input_json, output_json, objective_system_instruction)

        
        executer = dspy.Predict(signature)
        result = executer(**input_data)
        # print("Prompt of execute agent")
        # print("-"*50)
        # executer.inspect_history(n=1)
        return result

    def checker_agent(self, input_data: Dict[str, Any]):
        checker_config = self.load_config_json()[2]
        input_json = checker_config['input']
        output_json = checker_config['output']
        signature = self.dynamic_signature.from_json(input_json, output_json)
        checker = dspy.ChainOfThought(signature)
        
        result = checker(**input_data)
        return result

    def execute(self, input_data: Dict[str, Any]):
        """
        """
        pass
    
# if __name__ == '__main__':
#     loader = PlannerAgentLoader('config/agent_node/plan.json')

#     result = loader.execute({
#         'question': 'What should I do when I feel sad today?'
#     })
#     print('this is result: ',result)
