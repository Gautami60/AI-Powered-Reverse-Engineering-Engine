def build_explanation_prompt(file_id, function_addr, disassembly_json):
    """
    Build a prompt for AI explanation of a function's disassembly.
    
    Args:
        file_id: The ID of the file being analyzed
        function_addr: The address of the function
        disassembly_json: The disassembly JSON data
        
    Returns:
        str: The formatted prompt for the AI
    """
    # Extract ops from disassembly_json["ops"]
    ops = disassembly_json.get("ops", [])
    
    # Check if disassembly was trimmed
    was_trimmed = disassembly_json.get("_trimmed", False)
    original_length = disassembly_json.get("_original_length", len(ops))
    
    # Produce plain text assembly lines
    asm_lines = []
    for op in ops:
        offset = op.get("offset", 0)
        disasm = op.get("disasm", "")
        asm_lines.append(f"0x{offset:x}: {disasm}")
    
    asm_text = "\n".join(asm_lines)
    
    # Compose the user prompt with shorter, more focused instructions
    prompt = f"""You are an expert reverse engineer. 
Explain this function in 3 parts:

1) High-level summary.
2) Important steps in order.
3) Simple pseudocode.

Be concise. Avoid unnecessary details.

Disassembly (file_id: {file_id}, addr: {function_addr}):
{asm_text}"""
    
    # Add note about trimming if applicable
    if was_trimmed:
        prompt += f"\n\nNOTE: The disassembly was trimmed to avoid Gemini token limits.\nOnly the first and last parts of the function are included.\nOriginal instruction count: {original_length}\nIncluded: 120 instructions."
    
    return prompt