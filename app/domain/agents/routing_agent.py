from langchain import hub
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models import ChatOllama

from app.schema import User

from dotenv import load_dotenv
import os
import time

import json
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

llm = ChatOpenAI(model="mistral", api_key="ollama", base_url="http://localhost:11434/v1")
tools = [TavilySearchResults(max_results=2)]
prompt = hub.pull("wfh/react-agent-executor")
agent_executor = create_react_agent(llm, tools, messages_modifier=prompt)

class RoutingAgent:
    '''Classifies whether the guest query is a task request or an info request.
    If it is a task request, it prepares a JSON object for the task, to later route to the admin portal.
    If it is an info request, it sends the query to the agent executor for a response.'''
    def __init__(self, user):
        self.user = user
        self.room_number = 400 + len(user.last_name) #for now
        self.agent_executor = agent_executor

    def process_message(self, message):
        """
        Main function to process user messages. Determines whether to search the web or
        prepare a task JSON based on the type of request in the message.
        """
        print('User message:', message)

        # Analyze message intent
        intent = self._analyze_intent(message)

        if intent == "search":
            logging.info("Handling search request")
            return self._handle_search_request(message, self.user.first_name)
        elif intent == "task":
            logging.info("Handling task request")
            return self._prepare_task_json(message)
        else:
            return "I'm sorry, I couldn't determine the intent of your request."

    def _analyze_intent(self, message):
        """
        Analyzes the intent of the message to determine whether it is a web search or task.
        Returns "search" for web search, "task" for a task, and None if undecidable.
        """
        # Basic heuristic: Check for action keywords
        action_keywords = ["need", "send", "bring", "deliver", "request", "call", "help"]
        if any(keyword in message.lower() for keyword in action_keywords):
            return "task"
        else:
            return "search"

    def _handle_search_request(self, message, first_name):
        """
        Handles web search requests by invoking the agent executor.
        """
        # Append instructions for web-based responses
        message = message + f" Respond in less than 3 sentences as if you were a hotel manager \
          at the ski resort: Ritz Carlton Bachelor Gulch, and refer to me as {first_name}. Please do not make up information."
        print('Getting response...')
        response = self.agent_executor.invoke({"messages": [("user", message)]})
        print('Returning response. This is the response[messages]: ', response['messages'])
        return response['messages'][-1].content

    def assure_guest(self, response_json):
        """
        Generates a guest response using an LLM based on the task details.
        """
        try:
            if isinstance(response_json, dict) and "department" in response_json:
                # Extract details from response_json
                department = response_json["department"]
                user_name = self.user.first_name
                room_number = response_json.get("room_number", "N/A")
                task_message = response_json.get("message", "No details provided")

                # Use LLM to generate a dynamic response
                prompt = (
                    f"You are a polite and professional hotel owner named Karim at the Ritz-Carlton, Bachelor Gulch. "
                    f"A guest named {user_name}, staying in room {room_number}, has submitted the following request: "
                    f'"{task_message}". This request has been routed to the {department} department. '
                    f"Write a response to the guest that acknowledges their request, assures them that the {department} team "
                    f"is working on it, and invites them to make additional requests if needed. Respond in a friendly and "
                    f"professional tone, and Please limit your response to 3 sentences or fewer."
                )

                # Log the prompt before invoking the model
                logger.info("Invoking LLM with prompt: %s", prompt)

                # Start the timer to log how long the invocation takes
                start_time = time.time()

                try:
                    # Invoke LLM to generate the response
                    response = llm.invoke([{"role": "user", "content": prompt}, {"role": "system", "content": "Please limit your response to 3 sentences or fewer."}])

                    # Log how long the invocation took
                    end_time = time.time()
                    logger.info("LLM invocation took %.2f seconds", end_time - start_time)

                except Exception as e:
                    # Log any errors that occur during LLM invocation
                    end_time = time.time()
                    logger.error("Error during LLM invocation: %s", str(e), exc_info=True)
                    return "Sorry, there was an issue generating a response. Please try again later."

                # Log the response
                logger.info("LLM response: %s", response)

                # Return the content generated by the LLM
                guest_response = response.get("content") if hasattr(response, "get") else response.content
                return guest_response

            else:
                # Log a warning if the structure is unexpected
                logging.warning(f"Unexpected JSON structure: {response_json}")
                return "We are processing your request. Please contact us if you need further assistance."

        except Exception as e:
            # Log any unexpected errors
            logging.error(f"An unexpected error occurred in assure_guest: {str(e)}", exc_info=True)
            return (
                f"Thank you for reaching out, {self.user.first_name}. "
                f"We are reviewing your request and will get back to you shortly. "
                f"If you have any urgent needs, please contact the front desk."
            )
       

    def _prepare_task_json(self, message):
        """
        Prepares a JSON object for task requests based on the user message.
        """
        # TODO: use alg for better department mapping based on message content
        # Basic example of department mapping based on keywords
        department_mapping = {
            "towels": "housekeeping",
            "cleaning": "housekeeping",
            "room service": "room service",
            "food": "room service",
            "technical issue": "maintenance",
            "light": "maintenance",
            "leak": "maintenance",
            "heat": "maintenance",
            "air conditioning": "maintenance",
        }

        # Determine department from message
        department = None
        for keyword, dept in department_mapping.items():
            if keyword in message.lower():
                department = dept
                break

        if not department:
            department = "general"  # Fallback if no department is matched

        # Prepare task JSON
        task_json = {
            "department": department,
            "user_first_name": self.user.first_name,
            "user_last_name": self.user.last_name,
            "room_number": self.room_number,
            "message": message
        }

        print("Task JSON prepared: ", task_json)
        # TODO: Send the task to the admin portal
        print("Task sent to admin portal")
        # send guest a message letting them know their task has been received.
        reply_task_message = self.assure_guest(task_json)

        return reply_task_message + '\n\n You can track your request status at this link: https://www.google.com.'
    

    