from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from src.agents.state import AgentState
from src.agents.marine_agent import get_marine_agent
from src.agents.weather_agent import get_weather_agent
from src.agents.geospatial_agent import get_geospatial_agent
from src.agents.risk_agent import get_risk_agent
from src.agents.visualization_agent import visualization_node

def create_supervisor_graph():
    """
    Compiles the multi-agent graph. 
    For this MVP, we use a structured sequence to guarantee all data is gathered before risk assessment.
    Flow: User Query -> Marine Agent -> Weather Agent -> Geospatial Agent -> Risk Agent -> Visualization -> Final Output
    """
    builder = StateGraph(AgentState)
    
    async def _execute_tool_node(state: AgentState, tool_instance):
        from langchain_groq import ChatGroq
        from langchain_core.messages import ToolMessage, SystemMessage
        llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
        llm_with_tools = llm.bind_tools([tool_instance], tool_choice=tool_instance.name)
        
        system_msg = SystemMessage(content="You are a silent data extractor. You must call the provided tool immediately. Do not generate any conversational text, markdown tables, or commentary.")
        
        # Only pass the original human query to prevent the LLM from summarizing previous tool results
        original_query = state["messages"][0]
        messages = [system_msg, original_query]
        
        ai_msg = await llm_with_tools.ainvoke(messages)
        if ai_msg.tool_calls:
            tool_call = ai_msg.tool_calls[0]
            result = await tool_instance.ainvoke(tool_call["args"])
            tool_msg = ToolMessage(content=str(result), tool_call_id=tool_call["id"], name=tool_instance.name)
            return {"messages": [ai_msg, tool_msg]}
        return {"messages": [ai_msg]}

    async def marine_node(state: AgentState):
        from src.tools.data_tools import marine_tool
        return await _execute_tool_node(state, marine_tool)
        
    async def weather_node(state: AgentState):
        from src.tools.data_tools import weather_tool
        return await _execute_tool_node(state, weather_tool)
        
    async def geospatial_node(state: AgentState):
        from src.agents.geospatial_agent import check_geofence
        return await _execute_tool_node(state, check_geofence)
        
    async def risk_node(state: AgentState):
        agent = get_risk_agent()
        result = await agent.ainvoke({"messages": state["messages"]})
        return {"messages": [result["messages"][-1]]}
        
    async def vis_node_wrapper(state: AgentState):
        return visualization_node(state)
        
    async def language_node(state: AgentState):
        from src.agents.language_agent import language_node as ln
        return await ln(state)
        
    # Add nodes to graph
    builder.add_node("marine", marine_node)
    builder.add_node("weather", weather_node)
    builder.add_node("geospatial", geospatial_node)
    builder.add_node("risk", risk_node)
    builder.add_node("language", language_node)
    builder.add_node("visualization", vis_node_wrapper)
    
    # Define the sequential orchestration flow
    builder.add_edge(START, "marine")
    builder.add_edge("marine", "weather")
    builder.add_edge("weather", "geospatial")
    builder.add_edge("geospatial", "risk")
    builder.add_edge("risk", "language")
    builder.add_edge("language", "visualization")
    builder.add_edge("visualization", END)
    
    return builder.compile()
