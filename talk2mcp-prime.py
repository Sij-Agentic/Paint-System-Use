import os
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from concurrent.futures import TimeoutError

# Define the system prompt at the top
SYSTEM_PROMPT = """You are a reasoning agent that can call tools to solve problems and draw answers in Paint.

### Tool Usage:
- FUNCTION_CALL: tool_name|param1|param2|... (one per line) e.g FUNCTION_CALL: add|4|3 
- Include 'FUNCTION_CALL:', function_name| , and parameters (if necessary). All separated by '|' - this format is super strict. Ensure this format
- FINAL_ANSWER: result

### Notes:
- Always call open_paint FIRST before draw_rectangle or add_text_in_paint
- Never include markdown (like ``` or tool_code). Only plain lines.

✅ If you see a message confirming Paint is already open, you can continue with drawing and adding text.
❌ Only retry open_paint if the result says there was an error.

- Do NOT call open_paint again if it has already succeeded. This can cause tool errors.
- Only retry a tool if its last call returned ❌ or the result message included "error" or "failed".

### Tools:
{tools_block}
"""

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
    print("Generating with Gemini...")
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
    print("Starting MCP Agent")

    server_params = StdioServerParameters(command="python", args=["example2-prime.py"])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = tools_result.tools

            tool_descriptions = []
            for i, tool in enumerate(tools):
                try:
                    params = tool.inputSchema
                    desc = getattr(tool, 'description', 'No description')
                    name = getattr(tool, 'name', f'tool_{i}')

                    if 'properties' in params:
                        param_list = [
                            f"{param}: {info.get('type', 'unknown')}"
                            for param, info in params['properties'].items()
                        ]
                        param_str = ", ".join(param_list)
                    else:
                        param_str = "no parameters"

                    tool_descriptions.append(f"{i+1}. {name}({param_str}) - {desc}")
                except Exception as e:
                    tool_descriptions.append(f"{i+1}. Error loading tool: {str(e)}")

            tools_block = "\n".join(tool_descriptions)
            system_prompt = SYSTEM_PROMPT.replace('{tools_block}', tools_block)

            query = "Find the ASCII values of 'INDIA', sum their exponentials, then open Paint, draw a rectangle."

            global iteration, last_response
            paint_opened = False

            while iteration < max_iterations:
                print(f"\n--- Iteration {iteration + 1} ---")

                prompt = f"{system_prompt}\n\nQuery: {query}\n"
                if iteration_response:
                    prompt += "So far, you have done:\n"
                    for r in iteration_response:
                        prompt += f"- {r}\n"
                    prompt += "\nWhat should you do next?\n"

                try:
                    response_text = await generate_with_timeout(prompt)
                    print(f"Gemini Response:\n{response_text}")
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
                    print("⚠️ No valid FUNCTION_CALL lines detected. Stopping.")
                    break

                for func_line in function_lines:
                    try:
                        _, call = func_line.split(":", 1)
                        parts = [p.strip() for p in call.split("|") if p.strip()]
                        func_name = parts[0]
                        params = parts[1:] if len(parts) > 1 else []

                        tool = next((t for t in tools if t.name == func_name), None)
                        if not tool:
                            print(f"❌ Tool '{func_name}' not found. Available tools: {[t.name for t in tools]}")
                            continue

                        if func_name in {"draw_rectangle", "add_text_in_paint"} and not paint_opened:
                            print(f"⚠️ Skipping '{func_name}' because Paint is not opened yet.")
                            continue

                        arguments = {}
                        schema = tool.inputSchema.get("properties", {})
                        param_names = list(schema.keys())
                        clean_params = []
                        for p in params:
                            if p in param_names:
                                print(f"⚠️ Skipping parameter name: {p}")
                                continue
                            clean_params.append(p)
                        params = clean_params

                        for i, (param_name, param_info) in enumerate(schema.items()):
                            if i >= len(params):
                                raise ValueError(f"Not enough parameters for {func_name}")
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
                        await asyncio.sleep(1.0)
                        if func_name in {"draw_rectangle", "add_text_in_paint"}:
                            await asyncio.sleep(2.5)
                        else:
                            await asyncio.sleep(1.5)

                        # Logging result details
                        print(f"[Debug] Raw result: {result}")
                        texts = []
                        if hasattr(result, 'content'):
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    print(f"[Debug] Tool text content: {item.text}")
                                    texts.append(item.text)
                                else:
                                    print(f"[Debug] Tool non-text content: {item}")
                                    texts.append(str(item))
                        else:
                            print(f"[Debug] Result had no content: {result}")
                            texts = [str(result)]

                        result_str = "[" + ", ".join(texts) + "]"

                        if func_name == "open_paint":
                            paint_success = any(
                                "paint has been opened" in t.lower() or
                                "already open" in t.lower() or
                                "✅" in t
                                for t in texts
                            )
                            print(f"[Debug] Paint success detection: {paint_success}")

                            if paint_success:
                                paint_opened = True
                                print("✅ Paint opened successfully. Continuing.")
                                iteration_response.append(f"{func_name} => Paint opened successfully ✅")
                            else:
                                print("❌ Paint open attempt failed. Gemini may retry.")
                                iteration_response.append(f"{func_name} => Error: Paint not confirmed open ❌")
                                continue
                        else:
                            iteration_response.append(f"{func_name}({arguments}) => {result_str}")
                            last_response = result_str

                    except Exception as e:
                        print(f"❌ Error processing function call '{func_line}': {e}")
                        break

                iteration += 1

if __name__ == "__main__":
    asyncio.run(main())