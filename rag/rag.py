import os
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.pydantic_v1 import BaseModel, Field
from constants import (
    CLOUD_QUESTION, 
    SOLUTION_QUESTION, 
    ORG_TYPE_QUESTION, 
    CLOUD_TEMPLATE, 
    SOLUTION_TEMPLATE, 
    ORG_TYPE_TEMPLATE, 
    CONSOLIDATED_TEMPLATE, 
    VALIDATION_TEMPLATE,
    LLM_OUTPUT_TEMPLATE,
    CONFIRMATION_TEMPLATE
    )

# Load secrets
from dotenv import load_dotenv
load_dotenv()

os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'

# Load the release notes and solutions
def load_documents(file_path, loader_class, chunk_size=1000, chunk_overlap=200):
    """Loads and splits documents from a file using the specified loader."""
    loader = loader_class(file_path)
    docs = loader.load()
    if loader_class == PyPDFLoader:
        docs = docs[375:551]  # If it's a PDF, select specific pages
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    splits = text_splitter.split_documents(docs)

    return splits

release_notes_splits = load_documents("docs/salesforce_summer24_release_notes.pdf", PyPDFLoader)
solutions_splits = load_documents("docs/solutions.txt", TextLoader)

# Create vectorstores
def create_vectorstore(splits):
    """Creates a Chroma vectorstore from the given document splits."""
    return Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

cloud_vectorstore = create_vectorstore(release_notes_splits)
solutions_vectorstore = create_vectorstore(solutions_splits)

# Create retrievers
cloud_retriever = cloud_vectorstore.as_retriever(search_kwargs={"k": 2})
solutions_retriever = solutions_vectorstore.as_retriever(search_kwargs={"k": 1})\

# Create the prompts
cloud_prompt = ChatPromptTemplate.from_template(CLOUD_TEMPLATE)
solution_prompt = ChatPromptTemplate.from_template(SOLUTION_TEMPLATE)
org_type_prompt = ChatPromptTemplate.from_template(ORG_TYPE_TEMPLATE)
consolidated_prompt = ChatPromptTemplate.from_template(CONSOLIDATED_TEMPLATE)
validation_prompt = ChatPromptTemplate.from_template(VALIDATION_TEMPLATE)
llm_output_prompt = ChatPromptTemplate.from_template(LLM_OUTPUT_TEMPLATE)

# Class for final response
class SalesforceRecommendation(BaseModel):
    """
    Represents a recommendation for Salesforce clouds, solutions, and org type.
    """

    clouds: list[str] = Field(description="List of recommended Salesforce clouds")
    solutions: list[str] = Field(description="List of recommended Salesforce solutions (can be empty)")
    org_type: str = Field(description="Recommended Salesforce org type")
    need_more_info: bool = Field(description="Indicates if more information is needed from the user")
    message: str = Field(description="Message for user in case more information is needed")

class CloudsAndSolutions(BaseModel):
    clouds: list[str] = Field(description="List of recommended Salesforce clouds")
    solutions: list[str] = Field(description="List of recommended Salesforce solutions (can be empty)")

# Main function to process user input
def process_chat_history(chat_history):
    """Processes the user input and generates a final answer."""

    def format_docs(docs):
        """Formats the retrieved documents for the prompt."""
        return "\n\n".join(doc.page_content for doc in docs)

    def get_chain_response(retriever, prompt, previous_question=None, previous_response=None):
        """Retrieves relevant documents, formats them, and gets a response from the chain."""
        if retriever:
            retrieved_docs = retriever.invoke(chat_history)
            formatted_docs = format_docs(retrieved_docs)
        else:
            formatted_docs = None
        rag_chain = (
            prompt
            | llm
            | StrOutputParser()
        )
        return rag_chain.invoke({
            "context": formatted_docs,
            "chat_history": chat_history,
            "previous_question": previous_question,
            "previous_response": previous_response,
            "cloud_question": CLOUD_QUESTION,
            "solution_question": SOLUTION_QUESTION,
            "org_type_question": ORG_TYPE_QUESTION
        })

    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

    cloud_answer = get_chain_response(retriever=cloud_retriever, prompt=cloud_prompt)
    cloud_solution_answer = get_chain_response(retriever=solutions_retriever, prompt=solution_prompt, previous_question=CLOUD_QUESTION, previous_response=cloud_answer)
    org_type_answer = get_chain_response(retriever=None, prompt=org_type_prompt)
    
    # Set the model as structured
    structured_llm = llm.with_structured_output(SalesforceRecommendation, method="json_mode")
    rag_chain = (
        consolidated_prompt
        | structured_llm
    )

    consolidated_answer = rag_chain.invoke({
        "chat_history": chat_history,
        "identified_clouds_solutions": cloud_solution_answer,
        "identified_org_type": org_type_answer
    })
    
    # Run Validation
    clouds = consolidated_answer.clouds
    solutions = consolidated_answer.solutions
    retrieved_docs = solutions_retriever.invoke(chat_history)
    formatted_docs = format_docs(retrieved_docs)
    structured_llm = llm.with_structured_output(CloudsAndSolutions, method="json_mode")
    rag_chain_validation = (
        validation_prompt
        | structured_llm
    )

    validation_answer = rag_chain_validation.invoke({
        "chat_history": chat_history,
        "clouds": clouds,
        "solutions": solutions,
        "context": formatted_docs
    })
    
    consolidated_answer.clouds = validation_answer.clouds
    consolidated_answer.solutions = validation_answer.solutions

    # LLM Output
    rag_chain = (
        llm_output_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain.invoke({
        "clouds": consolidated_answer.clouds,
        "solutions": consolidated_answer.solutions,
        "org_type": consolidated_answer.org_type,
        "need_more_info": consolidated_answer.need_more_info,
        "message": consolidated_answer.message
    })

def check_user_confirmation(chat_history):

    class Confirmation(BaseModel):
        clouds: list[str] = Field(description="List of recommended Salesforce clouds")
        solutions: list[str] = Field(description="List of recommended Salesforce solutions (can be empty)")
        org_type: str = Field(description="Recommended Salesforce org type")
        confirmation: bool = Field(description="Whether the user has confirmed or not")

    # Extract the last LLM response
    last_llm_response = None
    if "LLM: " in chat_history:
        last_llm_user_response = chat_history.split("LLM: ")[-1].strip()
        last_llm_response = last_llm_user_response.split("User: ")[0].strip
    else:
        return None, None, None, False

    confirmation_prompt = ChatPromptTemplate.from_template(CONFIRMATION_TEMPLATE)

    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(Confirmation, method="json_mode")
    rag_chain = (
        confirmation_prompt
        | structured_llm
    )

    result = rag_chain.invoke({
        "chat_history": chat_history,
        "last_llm_response": last_llm_response
    })

    return result.clouds, result.solutions, result.org_type, result.confirmation


# Interactive chat loop
chat_history = ""
while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    chat_history += "User: " + user_input + "\n"
    clouds, solutions, org_type, confirmation = check_user_confirmation(chat_history)
    if confirmation:
        print(f"CONFIRMED:\n CLOUDS: {clouds},\n SOLUTIONS: {solutions},\n ORG_TYPE: {org_type}")
        exit(0)
    else:
        response = process_chat_history(chat_history)
        chat_history += "LLM: " + str(response) + "\n"
        print("LLM: " + str(response))