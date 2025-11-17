from fastapi import APIRouter, HTTPException
import os
import json
from ..core import storage
from ..utils.ai_prompt import build_explanation_prompt
from ..utils.llm_client import call_llm

router = APIRouter(prefix="/explain", tags=["explain"])

# In-memory cache for explanations (key: "{file_id}:{addr}", value: explanation)
explanation_cache = {}

def trim_disassembly(disassembly_json, limit=120):
    """
    Hard-trim disassembly to prevent token limit issues.
    Keep first 60 and last 60 operations.
    """
    ops = disassembly_json.get("ops", [])

    if len(ops) <= limit:
        return disassembly_json  # No trimming needed

    half = limit // 2
    trimmed_ops = ops[:half] + ops[-half:]

    trimmed = dict(disassembly_json)
    trimmed["ops"] = trimmed_ops
    trimmed["_trimmed"] = True
    trimmed["_original_length"] = len(ops)

    return trimmed

@router.get("/{file_id}/{addr}")
async def explain_function(file_id: str, addr: str):
    """
    Get AI explanation for a function's disassembly.
    
    Args:
        file_id: The ID of the file
        addr: The address of the function
        
    Returns:
        dict: Explanation of the function
    """
    # 1. Define artifact folder path
    artifact_folder = os.path.join("storage", "artifacts", file_id)
    
    # 2. Define disassembly path
    disasm_path = os.path.join(artifact_folder, "disassembly", f"{addr}.json")
    
    # 3. Check if disassembly file exists
    if not os.path.exists(disasm_path):
        raise HTTPException(status_code=404, detail="Disassembly not found")
    
    # 4. Load disassembly JSON
    try:
        with open(disasm_path, "r") as f:
            disassembly_json = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load disassembly: {str(e)}")
    
    # 5. Defensive check: ensure disassembly has valid ops array before calling AI
    if not isinstance(disassembly_json, dict) or not isinstance(disassembly_json.get("ops"), list):
        raise HTTPException(status_code=500, detail="Disassembly is in unexpected format, cannot explain.")
    
    # 6. Check cache first
    cache_key = f"{file_id}:{addr}"
    if cache_key in explanation_cache:
        return {
            "file_id": file_id,
            "addr": addr,
            "explanation": explanation_cache[cache_key]
        }
    
    # Check if explanation file exists
    explanations_dir = os.path.join(artifact_folder, "explanations")
    explanation_path = os.path.join(explanations_dir, f"{addr}.txt")
    
    if os.path.exists(explanation_path):
        try:
            with open(explanation_path, "r") as f:
                explanation = f.read()
            # Cache it
            explanation_cache[cache_key] = explanation
            return {
                "file_id": file_id,
                "addr": addr,
                "explanation": explanation
            }
        except Exception as e:
            pass  # If file read fails, continue to generate new explanation
    
    # 7. Trim disassembly before building prompt
    disassembly_json = trim_disassembly(disassembly_json)
    
    # 8. Build prompt
    prompt = build_explanation_prompt(file_id, addr, disassembly_json)
    
    # 9. Call LLM
    try:
        # Convert prompt to messages format for LLM
        messages = [
            {"role": "system", "content": "You are a helpful assistant that explains assembly code."},
            {"role": "user", "content": prompt}
        ]
        explanation = await call_llm(messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get explanation from AI: {str(e)}")
    
    # 10. Save explanation to file
    try:
        os.makedirs(explanations_dir, exist_ok=True)
        with open(explanation_path, "w") as f:
            f.write(explanation)
        # Cache it
        explanation_cache[cache_key] = explanation
    except Exception as e:
        pass  # If save fails, we still return the explanation
    
    # 11. Return JSON
    return {
        "file_id": file_id,
        "addr": addr,
        "explanation": explanation
    }