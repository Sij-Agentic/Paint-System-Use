import os
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from concurrent.futures import TimeoutError
from mcp.types import TextContent

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 5
last_response = None
iteration = 0
iteration_response = []

def reset_state():
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def generate_with_timeout(prompt, timeout=15):
    print("🔮 Generating with Gemini...")
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        return response.text.strip()
    except TimeoutError:
        raise Exception("LLM generation timed out!")
    except Exception as e:
        raise Exception(f"LLM error: {e}")

async def main():
    reset_state()
    print("🚀 Starting MCP Tkinter Agent")

    server_params = StdioServerParameters(command="python", args=["example2-tkinter.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = tools_result.tools

            # Format tool descriptions
            tool_descriptions = []
            for i, tool in enumerate(tools):
                params = tool.inputSchema
                name = getattr(tool, 'name', f'tool_{i}')
                desc = getattr(tool, 'description', 'No description')

                if 'properties' in params:
                    param_list = [
                        f"{param}: {info.get('type', 'unknown')}"
                        for param, info in params['properties'].items()
                    ]
                    param_str = ", ".join(param_list)
                else:
                    param_str = "no parameters"

                tool_descriptions.append(f"{i+1}. {name}({param_str}) - {desc}")

            tools_block = "\n".join(tool_descriptions)

            system_prompt = f"""You are a visual reasoning agent that can draw on a canvas using tools.

### Tool Usage:
- FUNCTION_CALL: tool_name|param1|param2|... (one per line) e.g FUNCTION_CALL: add|4|3 
- Include 'FUNCTION_CALL:', function_name| , and parameters (if necessary). All separated by '|' - this format is super strict. 
- Ensure this format is follwed strictly otherwise the process will break
- Should include only function call, functiona name, '|', parameters (if any)
- FINAL_ANSWER: result

Rules:
- Always call open_canvas FIRST before drawing or adding text
- Don't retry open_canvas if it already succeeded
- Use plain lines only (no markdown, no extra formatting)

Available Tools:
{tools_block}
"""

            query = "Find the ASCII values of 'INDIA', sum their exponentials, then open the canvas, draw a rectangle, and write the final result inside it."

            global iteration, last_response
            canvas_opened = False

            while iteration < max_iterations:
                print(f"\n--- Iteration {iteration + 1} ---")

                prompt = f"{system_prompt}\n\nQuery: {query}\n"
                if iteration_response:
                    prompt += "\nSo far:\n"
                    for r in iteration_response:
                        prompt += f"- {r}\n"
                    prompt += "\nWhat should you do next?\n"

                try:
                    response_text = await generate_with_timeout(prompt)
                    print(f"\n🧠 Gemini Response:\n{response_text}")
                except Exception as e:
                    print(f"LLM Error: {e}")
                    break

                if response_text.strip().startswith("FINAL_ANSWER:"):
                    answer = response_text.strip().replace("FINAL_ANSWER:", "").strip()
                    print(f"\n✅ Final Answer: {answer}")
                    iteration_response.append(f"FINAL_ANSWER: {answer}")
                    break

                function_lines = [
                    line.strip() for line in response_text.splitlines()
                    if line.strip().startswith("FUNCTION_CALL:")
                ]

                if not function_lines:
                    print("⚠️ No FUNCTION_CALL found. Stopping.")
                    break

                for func_line in function_lines:
                    try:
                        _, call = func_line.split(":", 1)
                        parts = [p.strip() for p in call.split("|") if p.strip()]
                        func_name = parts[0]
                        params = parts[1:] if len(parts) > 1 else []

                        tool = next((t for t in tools if t.name == func_name), None)
                        if not tool:
                            print(f"❌ Tool '{func_name}' not found.")
                            continue

                        if func_name in {"draw_rectangle", "add_text"} and not canvas_opened:
                            print(f"⚠️ Skipping '{func_name}' because canvas is not open yet.")
                            continue

                        arguments = {}
                        schema = tool.inputSchema.get("properties", {})
                        param_names = list(schema.keys())

                        for i, (param_name, param_info) in enumerate(schema.items()):
                            if i >= len(params):
                                raise ValueError(f"Missing parameter for {func_name}")
                            value = params[i]
                            param_type = param_info.get("type", "string")
                            if param_type == "integer":
                                arguments[param_name] = int(value)
                            elif param_type == "number":
                                arguments[param_name] = float(value)
                            elif param_type == "array":
                                arguments[param_name] = [int(x) for x in value.strip("[]").split(",")]
                            else:
                                arguments[param_name] = value

                        print(f"⚙️ Calling {func_name}({arguments})")
                        result = await session.call_tool(func_name, arguments=arguments)

                        import json

                        texts = []
                        if hasattr(result, 'content'):
                            for item in result.content:
                                if isinstance(item, TextContent):
                                    print(f"[Debug] TextContent raw: {item}")
                                    try:
                                        # Parse item.text as JSON
                                        parsed = json.loads(item.text)
                                        # Extract the real message from parsed["content"][0]["text"]
                                        true_text = parsed["content"][0]["text"]
                                        print(f"[Debug] Extracted inner text: {true_text}")
                                        texts.append(true_text.strip().lower())
                                    except Exception as e:
                                        print(f"[Error] Failed to parse JSON from item.text: {e}")
                                        texts.append(item.text.strip().lower())

                        result_str = "[" + ", ".join(texts) + "]"              


                        if func_name == "open_canvas":
                            print(f"[Debug] Final cleaned texts for check: {texts}")
                            canvas_success = any("✅ canvas window opened" in t for t in texts)
                            if canvas_success:
                                canvas_opened = True
                                print("✅ Canvas opened.")
                                iteration_response.append(f"{func_name} => Canvas opened ✅")
                            else:
                                print("❌ Failed to open canvas. Retrying.")
                                iteration_response.append(f"{func_name} => Failed ❌")
                                continue
                        else:
                            iteration_response.append(f"{func_name}({arguments}) => {result_str}")
                            last_response = result_str

                    except Exception as e:
                        print(f"❌ Error processing line '{func_line}': {e}")
                        break

                iteration += 1

if __name__ == "__main__":
    asyncio.run(main())
