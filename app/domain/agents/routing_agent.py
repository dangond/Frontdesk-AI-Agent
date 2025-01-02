from langchain import hub
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models import ChatOllama

from dotenv import load_dotenv
import os

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

llm = ChatOpenAI(model="mistral", api_key="ollama", base_url="http://localhost:11434/v1")
tools = [TavilySearchResults(max_results=2)]
prompt = hub.pull("wfh/react-agent-executor")
agent_executor = create_react_agent(llm, tools, messages_modifier=prompt)

def RoutingAgent(message, name):
    print('user message: ', message)
    message = message + f'Respond in less than 3 sentences as if you were a hotel manager at the Ritz Carlton Bachelor Gulch, and refer to me as {name}.'
    
    print('Getting response...')
    response = agent_executor.invoke({"messages": [("user", message)]})
    print('returning response. this is the response[messages]: ', response['messages'])
    
    return response['messages'][-1].content
