import boto3
import json

def assume_bedrock_role(role)
    client = boto3.client('sts')
    client.asume_role(
        RoleArn=role,
        RoleSessionName='bedrock-session'
    )
    

def invoke_bedrock_model(model_id, prompt):
       
    bedrock_runtime = boto3.client("bedrock-runtime")
    if "anthropic" in model_id:
        payload = {
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 300,
            "temperature": 0.5,
            "top_k": 50,
            "top_p": 0.9
        }
    elif "ai21" in model_id:
        payload = {
            "prompt": prompt,
            "maxTokens": 300,
            "temperature": 0.5,
            "topKReturn": 50,
            "topP": 0.9
        }
    elif "amazon" in model_id:
        payload = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 300,
                "temperature": 0.5,
                "topP": 0.9
            }
        }
    else:
        raise ValueError("Unsupported model. Update script with the correct model format.")

    # Invoke the model
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(payload)
    )
    
    response_body = json.loads(response["body"].read())

    # Extract text based on model type
    if "anthropic" in model_id:
        return response_body.get("completion", "No response received.")
    elif "ai21" in model_id:
        return response_body.get("completions", [{}])[0].get("data", {}).get("text", "No response received.")
    elif "amazon" in model_id:
        return response_body.get("results", [{}])[0].get("outputText", "No response received.")
    else:
        return "Unsupported model response format."

if __name__ == "__main__":
    selected_model = "anthropic.claude-v2"    
    user_prompt = ""    
    try:
        model_response = invoke_bedrock_model(selected_model, user_prompt)
        print("\nModel Response:\n", model_response)
    except Exception as e:
        print("Error:", str(e))
