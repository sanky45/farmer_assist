from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from .llm import get_llm
from .tools import get_weather, detect_disease


SYSTEM_PROMPT_TEMPLATE = """
You are an expert agriculture assistant specialized in helping farmers.

Farmer Profile:
- Name: {name}
- Location: {location}
- Main Crop: {main_crop}
- Farm Size: {farm_size}
- Soil Type: {soil_type}

Your job:
- Help this farmer with personalized agricultural advice based on their profile
- Give simple, practical, and actionable advice
- If user asks about weather, use the weather tool to get current conditions
- If the user wants to analyze a crop image for diseases, use the detect_disease tool and guide them on uploading an image
- Consider the farmer's location, crop type, and soil type when giving advice
- Keep answers short and clear
"""


def run_agent(user_input: str, chat_history: list, profile=None) -> str:
    llm = get_llm()

    tools = [get_weather, detect_disease]
    llm_with_tools = llm.bind_tools(tools)

    # 🌾 Build personalized system prompt with profile data
    profile_data = {
        "name": profile.name or "Farmer",
        "location": profile.location or "Unknown",
        "main_crop": profile.main_crop or "Not specified",
        "farm_size": profile.farm_size or "Not specified",
        "soil_type": profile.soil_type or "Not specified",
    } if profile else {
        "name": "Farmer",
        "location": "Unknown",
        "main_crop": "Not specified",
        "farm_size": "Not specified",
        "soil_type": "Not specified",
    }
    
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(**profile_data)
    messages = [SystemMessage(content=system_prompt)]

    # 🔹 Add previous conversation history
    for msg in chat_history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.message))
        else:
            messages.append(AIMessage(content=msg.message))

    # 🔹 Add new user message
    messages.append(HumanMessage(content=user_input))

    try:
        response = llm_with_tools.invoke(messages)
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"

    # 🔹 If tool is called, handle it properly
    if response.tool_calls:
        messages.append(response)  # Add AI response first
        
        for tool_call in response.tool_calls:
            try:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})

                # 🌦️ Handle weather tool
                if tool_name == "get_weather":
                    tool_result = get_weather.invoke(tool_args)
                elif tool_name == "detect_disease":
                    tool_result = detect_disease.invoke(tool_args)
                else:
                    tool_result = f"Unknown tool: {tool_name}"

                # Add tool result to conversation
                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call.get("id", "unknown"),
                    )
                )
                
            except Exception as e:
                # Handle tool execution errors gracefully
                messages.append(
                    ToolMessage(
                        content=f"Tool error: {str(e)}",
                        tool_call_id=tool_call.get("id", "unknown"),
                    )
                )

        # Get final response after tool calls
        try:
            final_response = llm.invoke(messages)
            # Handle different response formats from Gemini
            if hasattr(final_response, 'content'):
                content = final_response.content
                if isinstance(content, list):
                    # Extract text from structured response
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    return ''.join(text_parts)
                else:
                    return str(content)
            else:
                return str(final_response)
        except Exception as e:
            return f"Error generating final response: {str(e)}"

    # No tool calls, return direct response
    try:
        if hasattr(response, 'content'):
            content = response.content
            if isinstance(content, list):
                # Extract text from structured response
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif isinstance(item, str):
                        text_parts.append(item)
                return ''.join(text_parts)
            else:
                return str(content)
        else:
            return str(response)
    except Exception as e:
        return f"Error processing response: {str(e)}"