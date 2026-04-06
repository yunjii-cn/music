"""
Model Management Interface Component
"""
import gradio as gr
import os
from pathlib import Path
from typing import Dict, List, Tuple
from acestep.model_downloader import (
    list_available_models, 
    check_model_exists, 
    download_submodel, 
    download_main_model,
    SUBMODEL_REGISTRY,
    MAIN_MODEL_COMPONENTS,
    MAIN_MODEL_REPO
)
from acestep.ui.gradio.i18n import t


def create_model_management_section(language='en'):
    """
    Create model management section
    
    Args:
        language: UI language code
        
    Returns:
        Dictionary of components
    """
    components = {}
    
    # Get available models
    available_models = list_available_models()
    
    # Create model list
    model_list = []
    
    # Add main model
    model_list.append({
        "name": "main",
        "display_name": "Main Model",
        "repo": MAIN_MODEL_REPO,
        "description": "Contains: vae, Qwen3-Embedding-0.6B, acestep-v15-turbo, acestep-5Hz-lm-1.7B",
        "exists": all(check_model_exists(comp) for comp in MAIN_MODEL_COMPONENTS)
    })
    
    # Add submodels
    for model_name, repo in SUBMODEL_REGISTRY.items():
        # Determine model type
        model_type = "LM Model" if "lm" in model_name.lower() else "DiT Model"
        
        model_list.append({
            "name": model_name,
            "display_name": model_name,
            "repo": repo,
            "description": f"{model_type}",
            "exists": check_model_exists(model_name)
        })
    
    # Create model management section
    with gr.Column(elem_id="model-management-section"):
        gr.Markdown(f"### {t('model_management.title')}")
        
        # Model status tabs
        with gr.Tabs():
            # All models tab
            with gr.Tab(t('model_management.all_models')):
                components['all_models_table'] = gr.Dataframe(
                    value=[[
                        model['display_name'],
                        "✓" if model['exists'] else "✗",
                        model['description'],
                        model['repo']
                    ] for model in model_list],
                    headers=[t('model_management.model_name'), t('model_management.status'), t('model_management.description'), t('model_management.repository')],
                    interactive=False,
                    elem_id="all-models-table"
                )
            
            # Available models tab
            with gr.Tab(t('model_management.available_models')):
                available_models_list = [model for model in model_list if model['exists']]
                components['available_models_table'] = gr.Dataframe(
                    value=[[
                        model['display_name'],
                        model['description'],
                        model['repo']
                    ] for model in available_models_list],
                    headers=[t('model_management.model_name'), t('model_management.description'), t('model_management.repository')],
                    interactive=False,
                    elem_id="available-models-table"
                )
            
            # Missing models tab
            with gr.Tab(t('model_management.missing_models')):
                missing_models_list = [model for model in model_list if not model['exists']]
                components['missing_models_table'] = gr.Dataframe(
                    value=[[
                        model['display_name'],
                        model['description'],
                        model['repo']
                    ] for model in missing_models_list],
                    headers=[t('model_management.model_name'), t('model_management.description'), t('model_management.repository')],
                    interactive=False,
                    elem_id="missing-models-table"
                )
        
        # Download controls
        with gr.Row():
            components['model_to_download'] = gr.Dropdown(
                choices=[model['display_name'] for model in model_list if not model['exists']],
                label=t('model_management.select_model'),
                elem_id="model-to-download"
            )
            
            components['download_button'] = gr.Button(
                t('model_management.download'),
                elem_id="download-button"
            )
        
   # Download progress (disabled for Gradio 6.2.0 compatibility)
        # components['download_progress'] = gr.Progress(
        #     visible=False,
        #     elem_id="download-progress"
        # )
        
        components['download_status'] = gr.Textbox(
            label=t('model_management.download_status'),
            value="",
            interactive=False,
            elem_id="download-status"
        )
    
    # Define download function
    def download_model(model_name):
        if not model_name:
            return "Please select a model to download"
        
        # Map display name to actual model name
        actual_model_name = model_name
        if model_name == "Main Model":
            actual_model_name = "main"
        
        try:
            if actual_model_name == "main":
                success, message = download_main_model()
            else:
                success, message = download_submodel(actual_model_name)
            
            if success:
                return f"Success: {message}"
            else:
                return f"Error: {message}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Connect download button
    components['download_button'].click(
        fn=download_model,
        inputs=[components['model_to_download']],
        outputs=[components['download_status']]
    )
    
    return components