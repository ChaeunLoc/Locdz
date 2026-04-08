import os

from dotenv import load_dotenv
from langchain.agents import AgentType, initialize_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI


def build_agent():
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if not openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY in .env")
    if not tavily_api_key:
        raise ValueError("Missing TAVILY_API_KEY in .env")

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
    )

    tools = [TavilySearchResults(max_results=5)]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
    )
    return agent


def main():
    agent = build_agent()
    user_query = input("Enter your question for the AI Agent: ").strip()
    if not user_query:
        print("No question provided.")
        return

    result = agent.invoke({"input": user_query})
    print("\n=== Result ===")
    print(result["output"])


if __name__ == "__main__":
    main()
