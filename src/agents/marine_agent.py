from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from src.tools.data_tools import marine_tool

def get_marine_agent():
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, max_tokens=800)
    
    prompt = f"""You are the Marine Agent for the ORCA project. 
Your job is to look up marine data for a given location or coordinates.
You have access to the get_marine_data tool. Extract the location or coordinates from the conversation.
If you have coordinates, pass both latitude and longitude to the tool.

When you receive the data from the tool, format it clearly into a markdown table.
CRITICAL: You must explicitly list the source for each parameter (e.g., "live, Open-Meteo" or "reference data") in the table. 
If a parameter has a 'low_confidence' flag because the reference data is far away, you MUST explicitly state "(Low Confidence: >20km from query)" next to it.

For example:
| Parameter | Value | Source |
|-----------|-------|--------|
| Sea Surface Temperature (SST) | 28.2°C | live, Open-Meteo |
| Chlorophyll-a | 3.8 mg m⁻³ | reference data (Low Confidence: >20km from query) |
| Potential Fishing Zone (PFZ) | Yes | reference data |

Do NOT invent or hallucinate data. Only use the exact data returned by the tool.
"""

    return create_react_agent(
        llm,
        tools=[marine_tool],
        prompt=prompt
    )
