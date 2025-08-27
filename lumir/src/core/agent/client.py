from langchain_openai import ChatOpenAI
from abc import ABC, abstractmethod
from dataclasses import dataclass
import os 
from dotenv import load_dotenv
import dspy

load_dotenv()   
@dataclass
class LLMConfig:

    """
    LLM configuration class.

    Attributes:
        model_name (str): The name of the model to use.
        base_url (str): The base URL for the API.
        api_key (str): The API key for authentication.
        temperature (float): The temperature parameter for the model.
        max_tokens (int): The maximum number of tokens to generate.
    """

    model_name: str = os.getenv("MODEL_NAME")
    base_url: str = os.getenv("BASE_URL")
    api_key: str = os.getenv("API_KEY")
    temperature: float = os.getenv("TEMPERATURE")
    max_tokens: int = os.getenv("MAX_TOKENS")


class LLMClient(ABC):

    """
    LLM client class.

    Attributes:
        config (LLMConfig): The configuration for the LLM.
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    def  langchain_openai_llm(self):
        return ChatOpenAI(
            model_name=self.config.model_name,
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

    def dspy_llm(self):


        lm = dspy.LM(
                self.config.model_name,
                api_base=self.config.base_url,
                api_key=self.config.api_key,
            )
        dspy.configure(lm=lm)

        return lm


    def client(self, type:str):

        """
        Get the LLM client.

        Args:
            type (str): The type of LLM client to get. if type is "langchain", return langchain client. if type is "dspy", return dspy client.
            
        Returns:
            LLM: The LLM client.
        """

        if type == "langchain":
            return self.langchain_openai_llm()
        elif type == "dspy":
            return self.dspy_llm()
        else:
            raise ValueError(f"LLM type {type} not supported")
    

    

