import json
import re
from textwrap import indent
from typing import Dict, Any, List, Literal
import dspy
from lumir.src.core.agent.client import LLMClient, LLMConfig
from lumir.src.utils.logging import Logger, get_logger
from pprint import pprint
import json


# Initialize logger for this module
logger = get_logger(__name__)




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
    def __init__(self, config: Dict['str', Any]):

        # -------- init llm config -------- #
        self.llm_config = LLMConfig()
        self.llm_client = LLMClient(self.llm_config)

        # Choose type config dspy
        self.llm_client.client(type= "dspy")

        # -------- init agent config -------- #
        self.config = config
        self.agent = self.initialize_agent()

    def initialize_agent(self, module_name: Literal['ChainOfThought', 'ReAct', 'Predict'] = 'ChainOfThought'):
        
        input_json = self.config['input']
        output_json = self.config['output']
        objective_instruction = self.config.get('objective_instruction') or self.config.get('objective_system_instruction', '')
        signature = DynamicSignature().from_json(input_json, output_json, objective_instruction)

        try:
            if module_name == 'ChainOfThought':
                return dspy.ChainOfThought(signature)
            elif module_name == 'Predict':
                return dspy.Predict(signature)
            elif module_name == 'ReAct':
                return dspy.ReAct(signature)
        
        except Exception as e:
            logger.error(f"Error initializing agent: {e}")
            raise


    def execute(self, input_data):
        """Execute the agent with given input"""
        try:
            # For dspy ChainOfThought, we need to pass input as keyword arguments
            if isinstance(input_data, dict):
                result = self.agent(**input_data)
            else:
                # If input_data is a string, convert to the expected format
                result = self.agent(user_question=input_data)
            return result
        except Exception as e:
            logger.error(f"Error executing agent: {e}")
            raise
    
    def show_config(self):

        logger.info('================ CONFIG ==============')
        pprint(f"Agent config: {self.config}")
        logger.info('================ CONFIG ==============')



class AgentNode(dspy.Module):
    def __init__(self, configs: List[Dict['str', Any]]):
        super().__init__()
        # Store all agent configs
        self.agent_configs = configs if isinstance(configs, list) else [configs]
        self.agent_chain = []    # Store agent execution chain
        
        # Create BaseAgentLoader instances for each config
        self.agents = []
        for config in self.agent_configs:
            agent = BaseAgentLoader(config)
            self.agents.append(agent)


        # init agent_cache
        self.agent_cache = {

            # for analyze agent
            "plan": None,
            "external_keywords": None,
            # for execute agent 
            "execute_response": None,
            "user_question": None,
            # for checker agent
            "evalute_response": None,
            "missing_steps": None,
            "follow_plan": None,
            "score": 0
        }


    def load_node_config(self, config_path: str = None):
        """Load additional agent configs from file or directory"""
        try:
            if config_path:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                # Handle both single config and array of configs
                if isinstance(config_data, list):
                    additional_configs = config_data
                else:
                    additional_configs = [config_data]
                    
                # Add to existing configs
                self.agent_configs.extend(additional_configs)
                
                # Create BaseAgentLoader instances for new configs
                for config in additional_configs:
                    agent = BaseAgentLoader(config)
                    self.agents.append(agent)
                    
                logger.info(f"Loaded {len(additional_configs)} additional agent configs from {config_path}")
            else:
                logger.warning("No config path provided")
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def get_agent_chain_info(self):
        """Print all available agents in the chain"""
        logger.info('================ AGENT CHAIN INFO ==============') 
        
        if not self.agent_configs:
            logger.info("No agent configs loaded")
            return
            
        agent_names = []
        for i, config in enumerate(self.agent_configs):
            agent_name = config.get('name', f'Agent_{i}')
            agent_names.append(agent_name)
            
        logger.info(f"Available agents: {', '.join(agent_names)}")
        logger.info('================ END AGENT CHAIN INFO ==============')

    def get_chain(self):
        """Return the flow of input/output for agent execution"""
        chain_flow = {
            'total_agents': len(self.agent_configs),
            'execution_flow': [],
            'data_flow': []
        }
        
        for i, config in enumerate(self.agent_configs):
            agent_name = config.get('name', f'Agent_{i}')
            
            # Agent execution info
            agent_flow = {
                'step': i + 1,
                'agent_name': agent_name,
                'input_schema': config.get('input', {}),
                'output_schema': config.get('output', {}),
                'objective': config.get('objective_instruction', '')
            }
            
            chain_flow['execution_flow'].append(agent_flow)
            
            # Data flow between agents
            if i > 0:
                prev_agent = self.agent_configs[i-1]
                prev_outputs = set(prev_agent.get('output', {}).keys())
                current_inputs = set(config.get('input', {}).keys())
                
                # Find matching fields between previous output and current input
                data_transfer = {
                    'from_agent': prev_agent.get('name', f'Agent_{i-1}'),
                    'to_agent': agent_name,
                    'shared_fields': list(prev_outputs.intersection(current_inputs)),
                    'new_inputs': list(current_inputs - prev_outputs)
                }
                
                chain_flow['data_flow'].append(data_transfer)
        
        return chain_flow

    def get_agent_by_name(self, agent_name: str):
        for agent in self.agents:
            if agent.config['name'] == agent_name:
                return agent
        return None


    def execute(self, input: Dict[str, Any], external_function=None, max_iterations: int = 5):
        """
        Execute the agent chain with feedback loop between execute and checker agents
        
        Args:
            input: Dictionary containing user input
            external_function: Function to get external data from keywords
            max_iterations: Maximum number of iterations for feedback loop
        
        Returns:
            Final response from execute agent when all steps are completed
        """
        
        # 1. Get plan from analyze agent
        try:
            plan = self.get_agent_by_name('analyze_agent_0').execute(input)
            
            # Save plan output to cache
            self.agent_cache['plan'] = plan
            self.agent_cache['user_question'] = input['user_question']
            self.agent_cache['external_keywords'] = plan['external_keywords']
            
            logger.info(f"Plan generated: {plan}")
            
        except Exception as e:
            logger.error(f"Error getting plan: {e}")
            raise
        
        # 2. Get external data if function provided
        if external_function and 'external_keywords' in self.agent_cache:
            try:
                external_keywords = self.agent_cache['external_keywords']
                if external_keywords:  # Only call function if keywords exist
                    # Parse external_keywords if it's a string (JSON format)
                    if isinstance(external_keywords, str):
                        try:
                            # Attempt to parse as JSON list
                            parsed_keywords = json.loads(external_keywords)
                            # Ensure it's a list
                            if isinstance(parsed_keywords, list):
                                external_keywords = parsed_keywords
                            elif isinstance(parsed_keywords, str):
                                # If JSON parsing results in single string, wrap in list
                                external_keywords = [parsed_keywords]
                            else:
                                logger.warning(f"Unexpected external_keywords format after JSON parsing: {parsed_keywords}")
                                external_keywords = None
                        except json.JSONDecodeError:
                            # If not valid JSON, check if it looks like a Python list string
                            if external_keywords.startswith('[') and external_keywords.endswith(']'):
                                # Try to extract list items from string format
                                import re
                                matches = re.findall(r"'([^']*)'", external_keywords)
                                if matches:
                                    external_keywords = matches
                                else:
                                    external_keywords = None
                            else:
                                # Treat as single keyword
                                external_keywords = [external_keywords]
                    
                    # Call external_function with parsed keywords
                    if external_keywords and isinstance(external_keywords, list):
                        external_data = external_function(external_keywords)
                        if external_data:  # Only update cache if function returns something
                            self.agent_cache['external_data'] = external_data
                            logger.info(f"External data retrieved: {external_data}")
                        else:
                            logger.info("External function returned empty data, keeping original state")
                    else:
                        logger.info("No valid external keywords found, skipping external data retrieval")
                else:
                    logger.info("No external keywords found, skipping external data retrieval")
            except Exception as e:
                logger.warning(f"Error getting external data: {e}, keeping original state")
        
        # 3. Feedback loop between execute and checker agents
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Starting iteration {iteration}")
            
            try:
                # Get output from execute agent
                agent_execute_response = self.get_agent_by_name('execute_agent_0').execute(self.agent_cache)
                
                # Save execute agent response to cache
                self.agent_cache['execute_response'] = agent_execute_response
                self.agent_cache['response'] = agent_execute_response.get('response', '')
                
                # logger.info(f"Execute agent response: {agent_execute_response}")
                
                # Get evaluation from checker agent
                checker_response = self.get_agent_by_name('checker_agent_0').execute(self.agent_cache)
                
                # Save checker response to cache
                self.agent_cache['evalute_response'] = checker_response
                self.agent_cache['missing_steps'] = checker_response.get('missing_steps')
                self.agent_cache['follow_plan'] = checker_response.get('follow_plan')
                
                # logger.info(f"Checker response: {checker_response}")
                
                # Check if all steps are completed (no missing steps)
                missing_steps = checker_response.get('missing_steps')
                if missing_steps is None or missing_steps == "None" or not missing_steps:
                    logger.info("All steps completed successfully!")
                    return agent_execute_response
                
                # Update cache with feedback for next iteration
                self.agent_cache['loss_response'] = f"Missing steps: {missing_steps}. Please complete these steps: {missing_steps}"
                
                # logger.info(f"Missing steps detected: {missing_steps}. Continuing to iteration {iteration + 1}")
                
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                if iteration == 1:  # If first iteration fails, raise the error
                    raise
                else:  # If later iterations fail, return the last successful response
                    logger.warning(f"Returning last successful response due to error: {e}")
                    return self.agent_cache.get('execute_response', {})
        
        # If max iterations reached, return the last response
        logger.warning(f"Max iterations ({max_iterations}) reached. Returning final response.")
        return self.agent_cache.get('execute_response', {})
