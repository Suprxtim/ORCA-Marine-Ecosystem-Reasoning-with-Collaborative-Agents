import asyncio
from src.agents.geospatial_agent import get_geospatial_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

async def main():
    agent = get_geospatial_agent()
    
    print("\n--- Test 1: Inside MPA (69.2, 22.5) ---")
    res1 = await agent.ainvoke({"messages": [HumanMessage(content="Check geofence for 22.5, 69.2")]})
    print(res1["messages"][-1].content)
    
    print("\n--- Test 2: Far Open Water (60.0, 15.0) ---")
    res2 = await agent.ainvoke({"messages": [HumanMessage(content="Check geofence for 15.0, 60.0")]})
    print(res2["messages"][-1].content)
    
    print("\n--- Test 3: Near IMBL (67.6, 22.4) ---")
    # IMBL is [67.5, 22.5]
    res3 = await agent.ainvoke({"messages": [HumanMessage(content="Check geofence for 22.4, 67.6")]})
    print(res3["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
