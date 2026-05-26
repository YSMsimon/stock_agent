import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.model = os.getenv('MODEL')
        self.llm_api_key = os.getenv('LLM_API_KEY')
        self.llm_api_url = os.getenv('LLM_URL')
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')

    def validate(self):
        if not self.model:
            raise ValueError("MODEL environment variable is required.")
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY environment variable is required.")
        if not self.llm_api_url:
            raise ValueError("LLM_API_URL environment variable is required.")
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY environment variable is required.")

