import os

from dotenv import load_dotenv
from langchain.agents import AgentType, initialize_agent
from langchain.tools import Tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_openai import ChatOpenAI


def build_agent():
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    serpapi_api_key = os.getenv("SERPAPI_API_KEY")

    if not openai_api_key:
        raise ValueError("Missing OPENAI_API_KEY in .env")
    if not serpapi_api_key:
        raise ValueError("Missing SERPAPI_API_KEY in .env")

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
    )

    search = SerpAPIWrapper()
    tools = [
        Tool(
            name="google_search",
            func=search.run,
            description="Use this tool to search up-to-date information on Google.",
        )
    ]

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
