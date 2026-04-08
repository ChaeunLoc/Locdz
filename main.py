import os

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = """You are a senior data analyst.
Always answer in Vietnamese.
Verify important information with available tools before concluding.
If sources conflict, state the conflict and provide a cautious conclusion."""

REACT_PROMPT_TEMPLATE = """{system_prompt}

You have access to the following tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat multiple times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
Thought:{agent_scratchpad}
"""


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
    prompt = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE).partial(
        system_prompt=SYSTEM_PROMPT
    )
    react_agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

    agent = AgentExecutor(
        agent=react_agent,
        tools=tools,
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
