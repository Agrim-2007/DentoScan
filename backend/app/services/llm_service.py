import os
import google.generativeai as genai
from typing import List, Dict, Any

# Get API key from environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

async def generate_report(predictions: List[Dict[str, Any]]) -> str:
    """
    Generate a diagnostic report using a Gemini model based on the predictions.
    """
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY environment variable not set. Using mock report.")
        # Fallback to a mock report if API key is not set
        pathology_list = ', '.join([p['class'] for p in predictions]) if predictions else "no pathologies"
        return f"""Mock Diagnostic Report:\nBased on the analysis of the dental X-ray, the following findings were observed: {pathology_list}.\n\nPlease consult with a dental professional for a complete evaluation and treatment plan."""

    if not predictions:
        return "No pathologies detected."

    prompt = "You are a dental radiologist. Based on the image annotations provided below (which include detected pathologies), write a concise diagnostic report in clinical language.\n\nDetected Pathologies:\n"
    for pred in predictions:
        # Simplify location for the prompt, just mention the detected class and confidence.
        prompt += f"- {pred['class']} (Confidence: {pred['confidence']:.2%})\n"

    prompt += "\nPlease provide a brief paragraph highlighting:\n1. Detected pathologies\n2. Location if possible (e.g., upper left molar)\n3. Clinical advice (optional)\n\nKeep the report professional and concise."

    try:
        # Use a suitable Gemini model, e.g., 'gemini-pro' or 'gemini-flash'
        # Check available models and choose one appropriate for text generation.
        model = genai.GenerativeModel('gemini-2.0-flash') # Using gemini-2.0-flash model
        # For text-only input, use generate_content directly
        response = await model.generate_content_async(prompt)
        
        # Check if response contains text
        if response and response.text:
            return response.text
        else:
            print("Gemini API returned no text in the response.")
            # Fallback to a mock report if API returns no text
            pathology_list = ', '.join([p['class'] for p in predictions]) if predictions else "no pathologies"
            return f"""Mock Diagnostic Report:\nBased on the analysis of the dental X-ray, the following findings were observed: {pathology_list}.\n\nPlease consult with a dental professional for a complete evaluation and treatment plan."""


    except Exception as e:
        print(f"Error generating report with LLM: {e}")
        # Fallback to a mock report if LLM call fails
        pathology_list = ', '.join([p['class'] for p in predictions]) if predictions else "no pathologies"
        return f"""Mock Diagnostic Report:\nBased on the analysis of the dental X-ray, the following findings were observed: {pathology_list}.\n\nPlease consult with a dental professional for a complete evaluation and treatment plan.""" 