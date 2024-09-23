import gradio as gr

from modules import shared, ui_prompt_styles
import modules.images

from modules.ui_components import ToolButton
import time



class Toprow:
    

    """Creates a top row UI with prompts, generate button, styles, extra little buttons for things, and enables some functionality related to their operation"""

    prompt = None
    Bprompt = None
    prompt_img = None
    negative_prompt = None

    button_interrogate = None
    button_deepbooru = None

    interrupt = None
    interrupting = None
    skip = None
    submit = None

    paste = None
    clear_prompt_button = None
    apply_styles = None
    restore_progress_button = None
    batch_process_button = None


    token_counter = None
    token_button = None
    negative_token_counter = None
    negative_token_button = None

    ui_styles = None

    submit_box = None

    

    def __init__(self, is_img2img, is_compact=False, id_part=None):
        
        if id_part is None:
            id_part = "img2img" if is_img2img else "txt2img"

        self.id_part = id_part
        self.is_img2img = is_img2img
        self.is_compact = is_compact

        if not is_compact:
            with gr.Row(elem_id=f"{id_part}_toprow", variant="compact"):
                self.create_classic_toprow()
        else:
            self.create_submit_box()

    def create_classic_toprow(self):
        self.create_prompts()

        with gr.Column(scale=1, elem_id=f"{self.id_part}_actions_column"):
            self.create_submit_box()

            self.create_tools_row()

            self.create_styles_ui()

            self.generated_image = gr.Image(type="pil", visible=False, elem_id="generated_image")
       
            self.output_image = gr.Image(elem_id="output_image")
               
            





    def create_inline_toprow_prompts(self):
        if not self.is_compact:
            return

        self.create_prompts()

        with gr.Row(elem_classes=["toprow-compact-stylerow"]):
            with gr.Column(elem_classes=["toprow-compact-tools"]):
                self.create_tools_row()
            with gr.Column():
                self.create_styles_ui()

    def create_inline_toprow_image(self):
        if not self.is_compact:
            return

        self.submit_box.render()
    
    

    def create_prompts(self):
        with gr.Column(elem_id=f"{self.id_part}_prompt_container", elem_classes=["prompt-container-compact"] if self.is_compact else [], scale=6):
            with gr.Row(elem_id=f"{self.id_part}_prompt_row", elem_classes=["prompt-row"]):
                self.prompt = gr.Textbox(
                    label="Prompt",
                    elem_id=f"{self.id_part}_prompt",
                    show_label=False,
                    lines=3,
                    placeholder="Prompt\n(Press Ctrl+Enter to generate, Alt+Enter to skip, Esc to interrupt)",
                    elem_classes=["prompt"],
                    value=''
                )
                self.Bprompt = gr.Textbox(
                    label="Batch Prompts",
                    elem_id="batch_prompts",
                    show_label=True,
                    lines=5,
                    placeholder="Enter prompts separated by '#'",
                    value=''
                )
                self.prompt_img = gr.File(
                    label="",
                    elem_id=f"{self.id_part}_prompt_image",
                    file_count="single",
                    type="binary",
                    visible=False
                )

            with gr.Row(elem_id=f"{self.id_part}_neg_prompt_row", elem_classes=["prompt-row"]):
                self.negative_prompt = gr.Textbox(
                    label="Negative prompt",
                    elem_id=f"{self.id_part}_neg_prompt",
                    show_label=False,
                    lines=3,
                    placeholder="Negative prompt\n(Press Ctrl+Enter to generate, Alt+Enter to skip, Esc to interrupt)",
                    elem_classes=["prompt"],
                    value=''
                )

        self.prompt_img.change(
            fn=modules.images.image_data,
            inputs=[self.prompt_img],
            outputs=[self.prompt, self.prompt_img],
            show_progress=False,
        )
        self.dummy_js_trigger = gr.Button("Dummy JS Trigger", visible=False)  # Invisible button to trigger JS

        # Override the submit and change events of the prompt textbox
        def dummy_submit_function(*args):
            pass  # Do nothing

        self.prompt.submit(
            fn=dummy_submit_function,
            inputs=[],
            outputs=[]
        )

        



    def create_submit_box(self):
        with gr.Row(elem_id=f"{self.id_part}_generate_box", elem_classes=["generate-box"] + (["generate-box-compact"] if self.is_compact else []), render=not self.is_compact) as submit_box:
            self.submit_box = submit_box

            self.interrupt = gr.Button('Interrupt', elem_id=f"{self.id_part}_interrupt", elem_classes="generate-box-interrupt", tooltip="End generation immediately or after completing current batch")
            self.skip = gr.Button('Skip', elem_id=f"{self.id_part}_skip", elem_classes="generate-box-skip", tooltip="Stop generation of current batch and continues onto next batch")
            self.interrupting = gr.Button('Interrupting...', elem_id=f"{self.id_part}_interrupting", elem_classes="generate-box-interrupting", tooltip="Interrupting generation...")
            self.submit = gr.Button('Generate', elem_id=f"{self.id_part}_generate", variant='primary', tooltip="Right click generate forever menu")

            self.submit.click(
                fn=None,  # Use existing backend function to generate image
                _js="""
               function() {
        function checkImage() {
            var img = document.querySelector('#txt2img_gallery .image-button img');
            var lastImageUrl = document.querySelector('#generated_link').value;  // Get the last stored image URL from the Textbox

            // Check if the image is loaded, complete, and a new image
            if (img && img.src && img.complete && img.naturalHeight !== 0 && img.src !== lastImageUrl) {
                console.log('New image fully loaded, proceeding with download.');
                document.querySelector('#generated_link').value = img.src;  // Update the Textbox with the new image URL
                document.querySelector('#generated_link').dispatchEvent(new Event('input', {bubbles: true})); // Ensure Gradio registers the change

                var link = document.createElement('a');
                link.href = img.src;
                link.download = 'generated_image_' + Date.now() + '.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

               

                // Set the generation complete flag
                var completeTextbox = document.querySelector('div#generation_complete').querySelector('textarea[data-testid="textbox"]');
                if (completeTextbox) {
                    completeTextbox.value = 'true';
                    completeTextbox.dispatchEvent(new Event('input', {bubbles: true}));
                    completeTextbox.dispatchEvent(new Event('change', {bubbles: true})); 
                    console.log('Generation complete flag set.');
                }
            } else {
                console.log('Image not ready or no new image found, checking again in 1 second.');
                setTimeout(checkImage, 1000);
            }
        }

       

        checkImage();
    }
                """
            )



            def interrupt_function():
                if not shared.state.stopping_generation and shared.state.job_count > 1 and shared.opts.interrupt_after_current:
                    shared.state.stop_generating()
                    gr.Info("Generation will stop after finishing this image, click again to stop immediately.")
                else:
                    shared.state.interrupt()

            self.skip.click(fn=shared.state.skip)
            self.interrupt.click(fn=interrupt_function, _js='function(){ showSubmitInterruptingPlaceholder("' + self.id_part + '"); }')
            self.interrupting.click(fn=interrupt_function)

            

    def create_tools_row(self):
        with gr.Row(elem_id=f"{self.id_part}_tools"):
            from modules.ui import paste_symbol, clear_prompt_symbol, restore_progress_symbol

            self.paste = ToolButton(value=paste_symbol, elem_id="paste", tooltip="Read generation parameters from prompt or last generation if prompt is empty into user interface.")
            self.clear_prompt_button = ToolButton(value=clear_prompt_symbol, elem_id=f"{self.id_part}_clear_prompt", tooltip="Clear prompt")
            self.apply_styles = ToolButton(value=ui_prompt_styles.styles_materialize_symbol, elem_id=f"{self.id_part}_style_apply", tooltip="Apply all selected styles to prompts.")

            if self.is_img2img:
                self.button_interrogate = ToolButton('📎', tooltip='Interrogate CLIP - use CLIP neural network to create a text describing the image, and put it into the prompt field', elem_id="interrogate")
                self.button_deepbooru = ToolButton('📦', tooltip='Interrogate DeepBooru - use DeepBooru neural network to create a text describing the image, and put it into the prompt field', elem_id="deepbooru")

            self.restore_progress_button = ToolButton(value=restore_progress_symbol, elem_id=f"{self.id_part}_restore_progress", visible=False, tooltip="Restore progress")

            self.token_counter = gr.HTML(value="<span>0/75</span>", elem_id=f"{self.id_part}_token_counter", elem_classes=["token-counter"], visible=False)
            self.token_button = gr.Button(visible=False, elem_id=f"{self.id_part}_token_button")
            self.negative_token_counter = gr.HTML(value="<span>0/75</span>", elem_id=f"{self.id_part}_negative_token_counter", elem_classes=["token-counter"], visible=False)
            self.negative_token_button = gr.Button(visible=False, elem_id=f"{self.id_part}_negative_token_button")

            self.clear_prompt_button.click(
                fn=lambda *x: x,
                _js="confirm_clear_prompt",
                inputs=[self.prompt,self.Bprompt, self.negative_prompt],
                outputs=[self.prompt, self.negative_prompt],
            )
            self.batch_process_button = gr.Button("Process Batch", elem_id="process_batch", variant="primary")
            
            self.generate_trigger = gr.Checkbox(visible=False, value=False, elem_id=f"{self.id_part}_generate_trigger")
            self.batch_process_button.click(
                fn=lambda: None,  # The backend function won't do anything; JS will handle everything.
                inputs=[],
                outputs=[],
                _js="""
                () => {
                    const batchPrompts = document.getElementById('batch_prompts').querySelector('textarea[data-testid="textbox"]').value.split("#");
                    const promptInput = document.getElementById('txt2img_prompt').querySelector('textarea[data-testid="textbox"]');
                    const generateButton = document.getElementById('txt2img_generate');

                    let index = 0;

                    function triggerNextPrompt() {
                        if (index < batchPrompts.length) {
                            promptInput.value = batchPrompts[index].trim();  // Set the next prompt
                            promptInput.dispatchEvent(new Event('input', {bubbles: true}));  // Ensure Gradio registers the change
                            generateButton.click();  // Trigger image generation
                            waitForCompletion();
                        }
                    }

                    function waitForCompletion() {
                        var completeTextbox = document.querySelector('div#generation_complete').querySelector('textarea[data-testid="textbox"]');
                        if (completeTextbox.value.toLowerCase() === 'true') {
                            // Reset the completion flag properly
                            completeTextbox.value = 'false';  // Reset flag
                            completeTextbox.dispatchEvent(new Event('input', {bubbles: true}));
                            completeTextbox.dispatchEvent(new Event('change', {bubbles: true}));  // Force the interface to notice the change

                            index++;  // Move to the next prompt
                            // Allow some time for the UI to process and reset before triggering the next prompt
                            setTimeout(triggerNextPrompt, 5000);  // Delay adjusted for UI processing
                        } else {
                            setTimeout(waitForCompletion, 1000);  // Shorter polling interval
                        }
                    }

                    triggerNextPrompt();  // Start processing
                }
                """
            )
                        #self.batch_process_button.click(
            #    fn=self.process_batch_prompts,
            #    inputs=[self.Bprompt],
            #    outputs=[self.prompt, self.generate_trigger, self.generation_complete]  # Include self.generation_complete
            #)
            generate_button_id = self.submit.elem_id

            def dummy_function(value):
                return

            self.generate_trigger.change(
                fn=dummy_function,
                inputs=[self.generate_trigger],
                outputs=[],
                _js=f"""
                function(trigger) {{
                    if (trigger === true) {{
                        // Simulate click on the Generate button
                        document.getElementById('{generate_button_id}').click();
                    }}
                }}
                """
            )
    def process_batch_prompts(self, batch_prompts):
        prompts = [p.strip() for p in batch_prompts.split('#') if p.strip()]
        print(f"Total prompts received: {len(prompts)}")  # Debug: Total number of prompts

        for index, prompt in enumerate(prompts):
            print(f"Processing prompt {index+1}/{len(prompts)}: {prompt}")  # Debug: Show current prompt being processed

            # Set the prompt and trigger the image generation
            yield [
                gr.update(value=prompt),        # Update the prompt text
                gr.update(value=True),          # Set generate_trigger to True to start generation
                gr.update(value='False')        # Reset the generation_complete flag
            ]

            # Wait until the image generation is marked as complete
       
            while self.generation_complete.value.lower() != 'True':
                print(f"Waiting for the completion of prompt {index+1}: Current flag state: {self.generation_complete.value}")
                time.sleep(1)

            print(f"Image generation for prompt {index+1} completed, proceeding to download.")  # Debug: Confirm image generation complete

            # Reset for the next prompt
            yield [
                gr.update(value=''),            # Clear the prompt field
                gr.update(value=False),         # Reset the generate_trigger
                gr.update(value='False')        # Reset the generation_complete flag for safety
            ]

            print(f"Ready for the next prompt after {prompt}.")  # Debug: Ready for next


            
    




    def create_classic_toprow(self):
        self.create_prompts()

        with gr.Column(scale=1, elem_id=f"{self.id_part}_actions_column"):
            self.create_submit_box()
        
            # Define generation_complete before using it
            self.generation_complete = gr.Textbox(visible=True, elem_id='generation_complete', value='False')
            self.generated_link = gr.Textbox(visible=True, elem_id='generated_link', value='')
        
            self.create_tools_row()
            self.create_styles_ui()

            


    def create_styles_ui(self):
        self.ui_styles = ui_prompt_styles.UiPromptStyles(self.id_part, self.prompt, self.negative_prompt)
        self.ui_styles.setup_apply_button(self.apply_styles)

    