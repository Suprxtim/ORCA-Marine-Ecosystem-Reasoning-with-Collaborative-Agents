from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from src.tools.data_tools import weather_tool

def get_weather_agent():
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, max_tokens=800)
    
    prompt = f"""You are the Weather Agent for the ORCA project. 
Your job is to look up marine weather data for a given location or coordinates.
You have access to the get_weather_data tool. Extract the location or coordinates from the conversation.
If you have coordinates, pass both latitude and longitude to the tool.

When you receive the data from the tool, format it clearly into a markdown table.
CRITICAL: You must explicitly list the source for each parameter (e.g., "live, Open-Meteo" or "reference data") in the table. 
If a parameter has a 'low_confidence' flag because the reference data is far away, you MUST explicitly state "(Low Confidence: >20km from query)" next to it.

For example:
| Parameter | Value | Source |
|-----------|-------|--------|
| Wind Speed | 14.2 knots | live, Open-Meteo |
| Wave Height | 1.8 m | live, Open-Meteo |
| Cyclone Alert | None | reference data (Low Confidence: >20km from query) |
| Lightning Risk | Low | reference data |

Do NOT invent or hallucinate data. Only use the exact data returned by the tool.
"""

    return create_react_agent(
        llm,
        tools=[weather_tool],
        prompt=prompt
    )
