from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

def get_risk_agent():
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, max_tokens=800)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the Synthesis and Risk Assessment Agent for the ORCA project.
Your job is to read the raw structured data (JSON) gathered by the Marine, Weather, and Geospatial tools in the conversation history, and output EXACTLY ONE cohesive paragraph that synthesizes this data into a final safety verdict.

CRITICAL RULE: If the Geospatial Agent reports that `inside_restricted_zone` is true, you MUST declare the verdict as UNSAFE, regardless of how good the weather is.

Output Format:
VERDICT: [SAFE | CAUTION | UNSAFE]
REASONING: [Write a single cohesive paragraph explaining why, weaving in the wind, wave, SST, chlorophyll, PFZ, and geofence findings as supporting evidence. Do NOT use markdown tables. Do NOT write separate safety assessment sections. Just one unified paragraph.]"""),
        ("user", "Here is the data gathered so far:\n\n{context}\n\nPlease provide your final verdict.")
    ])
    
    def format_context(inputs):
        msgs = inputs["messages"]
        context = ""
        for m in msgs:
            text = ""
            if isinstance(m.content, list):
                text = "".join(b.get("text", "") for b in m.content if isinstance(b, dict))
            else:
                text = str(m.content)
            role = "User" if m.type == "human" else "Agent"
            context += f"{role}: {text}\n\n"
        return {"context": context}
        
    def wrap_in_dict(ai_message):
        return {"messages": [ai_message]}
        
    return format_context | prompt | llm | wrap_in_dict
