from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain import globals
from langchain_core.runnables import chain
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
import base64


import os

from langchain_core.pydantic_v1 import BaseModel, Field

class ImageInformation(BaseModel):
    """Information about an image."""
    # image_description: str = Field(description="a short description of the image")
    soil_type: str = Field(description="Classification of type of soil and small description")
    crops_suitable: str = Field(description="A small description on the types of crops suitable in India for that soil")
    short_description: str = Field(description="A 200 word description about the soil type and how its farmed in India")

load_dotenv()

parser = JsonOutputParser(pydantic_object=ImageInformation)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(OPENAI_API_KEY)

def encode_image(image_path = "images.png"):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


# Set verbose
globals.set_debug(True)


@chain
def image_model(inputs: dict) -> str | list[str] | dict:
    """Invoke model with image and prompt."""
    model = ChatOpenAI(temperature=0.5, model="gpt-4o", api_key=OPENAI_API_KEY)
    msg = model.invoke(
                [HumanMessage(
                content=[
                {"type": "text", "text": inputs["prompt"]},
                {"type": "text", "text": parser.get_format_instructions()},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{inputs['image']}"}},
                ])]
                )
    return msg.content


def get_image_informations(image_base64: str) -> dict:
   vision_prompt = """
   You are an agriculture expert who can deduce soil types based on images. 

   There are a few types of soil, which are listed below.

    Alluvial Soil
    Black Cotton Soil
    Red & Yellow Soil
    Laterite Soil
    Mountainous or Forest Soil
    Arid or Desert Soil
    Saline and Alkaline Soil
    Peaty and Marshy Soil

   Given the image classify the soil in the image and, provide the following information
   of the soil based on the image:

   - Type of soil based on the image
   - Crops suitable for that particular soil
   - A description of the soil in 200 words

   The output should be something like this:

        {
        "soil_type":"Black Cotton Soil"
        "crops_suitable":"Cotton, sorghum, millet, wheat, and pulses"
        "short_description":"Black Cotton Soil, also known as Regur Soil, is a type of soil found in India that is ideal for growing cotton, hence the name. This soil is characterized by its high moisture retention capacity and is rich in soil nutrients such as calcium carbonate, magnesium, potash, and lime. It is particularly well-suited for dry farming and is predominantly found in the Deccan Plateau regions of India, including states like Maharashtra, Madhya Pradesh, Gujarat, Andhra Pradesh, and Tamil Nadu. Black Cotton Soil is black in color due to the presence of various salts and is very fine-grained and sticky when wet. Despite its fertility, it can be challenging to work with due to its tendency to swell when wet and shrink upon drying, which can lead to cracking. This soil is also used for producing important cereals, oilseeds, and fibers, contributing significantly to the agricultural output of the region. Farmers in India manage these soil conditions by using appropriate tillage methods and crop rotation to maintain soil health and prevent erosion."
        }

    Use the above format DO NOT COPY IT.
   Manage with the image alone, and provide the data and descriptions accordingly.
   """
   vision_chain = image_model | parser
   return vision_chain.invoke({'image': f'{image_base64}', 
                               'prompt': vision_prompt})


class farma_chatbot():
    def __init__(self) -> None:
        self.llm =  ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")
        self.output_parser = StrOutputParser()
        self.memory = ConversationBufferWindowMemory(k = 10)

    def update_user_message(self, message):
        self.memory.chat_memory.add_user_message(message)

    def update_ai_message(self, ai_message):
        self.memory.chat_memory.add_ai_message(ai_message)

    def translator_for_bot(self, text, language):
        llm = ChatOpenAI(temperature=0.5, model="gpt-4o", api_key=OPENAI_API_KEY)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Translator"),
            ("user", """You will be given a sentence and a destination language.
                You are to translate that sentence to the destination language. Be clear
                and do not add uneccessary data.
                
                Sentence to be translated:
                {sentence}
                
                Destination Language:
                {dest_lang}
                
                ONLY GIVE THE TRANSLATED SENTENCE, DO NOT GIVE ANYTHING ELSE""")
        ])
        chain = prompt | llm | self.output_parser
        chatbot_response = chain.invoke({"sentence": text, "dest_lang": language})
        return chatbot_response

    def farma_chatbot_prompt(self):
        prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an agriculture expert"),
                ("user", """You will be given data about a particular type of soil. You are
                 to analyze that data and answer agricultural questions related to the same.

                 Here is the data about the soil.
                 {soil_data}

                 Here is the users query:
                 {user_query}

                 Here is the conversation or chat_history:
                 {conversation_history}
                 
                PROVIDE THE RESPONSE ALONE NOTHING ELSE IS REQUIRED""")
            ])
        return prompt
    
    def chatbot_runner(self, soil_results, user_query):
       chain = self.farma_chatbot_prompt() | self.llm | self.output_parser
       chatbot_response = chain.invoke({"soil_data": soil_results, "user_query": user_query, "conversation_history": self.memory})
       return chatbot_response
       
