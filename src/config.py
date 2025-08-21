import os
from strands.models import BedrockModel

def get_agent_prompt(prompt: str) -> str:
    try:
        with open(f'prompts/{prompt}.txt', 'r', encoding='utf-8') as f:
            read_prompt = f.read()
    except FileNotFoundError:
        print(f"Error: {prompt} not found")
        read_prompt = ""
    
    return read_prompt

def knowledge_base_config(kb_id, region):
    return {
        "knowledgeBaseId": f"{kb_id}",
        "numberOfResults": 5,
        "region": f"{region}"
    }

def get_configured_model(model_id: str = None) -> BedrockModel:
    """Workshop Bedrock model configuration
    
    Args:
        model_id: Model ID to use (optional)
        
    Returns:
        Configured BedrockModel instance
    """
    # TODO: Implement in Lab 1
    # Determine model ID (priority: parameter > environment variable > default)
    final_model_id = (
        model_id or 
        os.getenv("MODEL_ID") or 
        "anthropic.claude-3-haiku-20240307-v1:0"  # Seoul 리전에서 더 안정적
    )
    
    # AWS region configuration
    region = os.getenv("AWS_REGION", "ap-northeast-2")
    
    # Create Bedrock model
    model = BedrockModel(
        model_id=final_model_id,
        region=region,
        temperature=0.1,
        max_tokens=4096,
        streaming=False  # Disable streaming for workshop
    )
    
    # Add model_id attribute (compatibility)
    if not hasattr(model, 'model_id'):
        model.model_id = final_model_id
    
    return model

