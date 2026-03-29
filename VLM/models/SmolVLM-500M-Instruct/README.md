---
library_name: transformers
license: apache-2.0
datasets:
- HuggingFaceM4/the_cauldron
- HuggingFaceM4/Docmatix
pipeline_tag: image-text-to-text
language:
- en
base_model:
- HuggingFaceTB/SmolLM2-360M-Instruct
- google/siglip-base-patch16-512
---

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/SmolVLM_256_banner.png" width="800" height="auto" alt="Image description">

# SmolVLM-500M

SmolVLM-500M is a tiny multimodal model, member of the SmolVLM family. It accepts arbitrary sequences of image and text inputs to produce text outputs. It's designed for efficiency. SmolVLM can answer questions about images, describe visual content, or transcribe text. Its lightweight architecture makes it suitable for on-device applications while maintaining strong performance on multimodal tasks. It can run inference on one image with 1.23GB of GPU RAM.

## Model Summary

- **Developed by:** Hugging Face 🤗
- **Model type:** Multi-modal model (image+text)
- **Language(s) (NLP):** English
- **License:** Apache 2.0
- **Architecture:** Based on [Idefics3](https://huggingface.co/HuggingFaceM4/Idefics3-8B-Llama3) (see technical summary)

## Resources

- **Demo:** [SmolVLM-256 Demo](https://huggingface.co/spaces/HuggingFaceTB/SmolVLM-256M-Demo)
- **Blog:** [Blog post](https://huggingface.co/blog/smolvlm)

## Uses

SmolVLM can be used for inference on multimodal (image + text) tasks where the input comprises text queries along with one or more images. Text and images can be interleaved arbitrarily, enabling tasks like image captioning, visual question answering, and storytelling based on visual content. The model does not support image generation.

To fine-tune SmolVLM on a specific task, you can follow [the fine-tuning tutorial](https://github.com/huggingface/smollm/blob/main/vision/finetuning/Smol_VLM_FT.ipynb).

## Evaluation


<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/smoller_vlm_benchmarks.png" alt="Benchmarks" style="width:90%;" />


### Technical Summary

SmolVLM leverages the lightweight SmolLM2 language model to provide a compact yet powerful multimodal experience. It introduces several changes compared to the larger SmolVLM 2.2B model:

- **Image compression:** We introduce a more radical image compression compared to Idefics3 and SmolVLM-2.2B to enable the model to infer faster and use less RAM.
- **Visual Token Encoding:** SmolVLM-256 uses 64 visual tokens to encode image patches of size 512×512. Larger images are divided into patches, each encoded separately, enhancing efficiency without compromising performance.
- **New special tokens:** We added new special tokens to divide the subimages. This allows for more efficient tokenization of the images.
- **Smoller vision encoder:** We went from a 400M parameter siglip vision encoder to a much smaller 93M encoder.
- **Larger image patches:** We are now passing patches of 512x512 to the vision encoder, instead of 384x384 like the larger SmolVLM. This allows the information to be encoded more efficiently.

More details about the training and architecture are available in our technical report.

### How to get started

You can use transformers to load, infer and fine-tune SmolVLM.

```python
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForVision2Seq
from transformers.image_utils import load_image

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load images
image = load_image("https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg")

# Initialize processor and model
processor = AutoProcessor.from_pretrained("HuggingFaceTB/SmolVLM-500M-Instruct")
model = AutoModelForVision2Seq.from_pretrained(
    "HuggingFaceTB/SmolVLM-500M-Instruct",
    torch_dtype=torch.bfloat16,
    _attn_implementation="flash_attention_2" if DEVICE == "cuda" else "eager",
).to(DEVICE)

# Create input messages
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": "Can you describe this image?"}
        ]
    },
]

# Prepare inputs
prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
inputs = processor(text=prompt, images=[image], return_tensors="pt")
inputs = inputs.to(DEVICE)

# Generate outputs
generated_ids = model.generate(**inputs, max_new_tokens=500)
generated_texts = processor.batch_decode(
    generated_ids,
    skip_special_tokens=True,
)

print(generated_texts[0])
"""
Assistant: The image depicts a cityscape featuring a prominent landmark, the Statue of Liberty, prominently positioned on Liberty Island. The statue is a green, humanoid figure with a crown atop its head and is situated on a small island surrounded by water. The statue is characterized by its large, detailed structure, with a statue of a woman holding a torch above her head and a tablet in her left hand. The statue is surrounded by a small, rocky island, which is partially visible in the foreground.
In the background, the cityscape is dominated by numerous high-rise buildings, which are densely packed and vary in height. The buildings are primarily made of glass and steel, reflecting the sunlight and creating a bright, urban skyline. The skyline is filled with various architectural styles, including modern skyscrapers and older, more traditional buildings.
The water surrounding the island is calm, with a few small boats visible, indicating that the area is likely a popular tourist destination. The water is a deep blue, suggesting that it is a large body of water, possibly a river or a large lake.
In the foreground, there is a small strip of land with trees and grass, which adds a touch of natural beauty to the urban landscape. The trees are green, indicating that it is likely spring or summer.
The image captures a moment of tranquility and reflection, as the statue and the cityscape come together to create a harmonious and picturesque scene. The statue's presence in the foreground draws attention to the city's grandeur, while the calm water and natural elements in the background provide a sense of peace and serenity.
In summary, the image showcases the Statue of Liberty, a symbol of freedom and democracy, set against a backdrop of a bustling cityscape. The statue is a prominent and iconic representation of human achievement, while the cityscape is a testament to human ingenuity and progress. The image captures the beauty and complexity of urban life, with the statue serving as a symbol of hope and freedom, while the cityscape provides a glimpse into the modern world.
"""
```


### Model optimizations

**Precision**: For better performance, load and run the model in half-precision (`torch.bfloat16`) if your hardware supports it.

```python
from transformers import AutoModelForVision2Seq
import torch

model = AutoModelForVision2Seq.from_pretrained(
    "HuggingFaceTB/SmolVLM-Instruct",
    torch_dtype=torch.bfloat16
).to("cuda")
```

You can also load SmolVLM with 4/8-bit quantization using bitsandbytes, torchao or Quanto. Refer to [this page](https://huggingface.co/docs/transformers/en/main_classes/quantization) for other options.

```python
from transformers import AutoModelForVision2Seq, BitsAndBytesConfig
import torch

quantization_config = BitsAndBytesConfig(load_in_8bit=True)
model = AutoModelForVision2Seq.from_pretrained(
    "HuggingFaceTB/SmolVLM-Instruct",
    quantization_config=quantization_config,
)
```

**Vision Encoder Efficiency**: Adjust the image resolution by setting `size={"longest_edge": N*512}` when initializing the processor, where N is your desired value. The default `N=4` works well, which results in input images of
size 2048×2048. Decreasing N can save GPU memory and is appropriate for lower-resolution images. This is also useful if you want to fine-tune on videos.


## Misuse and Out-of-scope Use

SmolVLM is not intended for high-stakes scenarios or critical decision-making processes that affect an individual's well-being or livelihood. The model may produce content that appears factual but may not be accurate. Misuse includes, but is not limited to:

- Prohibited Uses:
  - Evaluating or scoring individuals (e.g., in employment, education, credit)
  - Critical automated decision-making
  - Generating unreliable factual content
- Malicious Activities:
  - Spam generation
  - Disinformation campaigns
  - Harassment or abuse
  - Unauthorized surveillance

### License

SmolVLM is built upon [SigLIP](https://huggingface.co/google/siglip-base-patch16-512) as image encoder and [SmolLM2](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) for text decoder part.

We release the SmolVLM checkpoints under the Apache 2.0 license.

## Training Details

### Training Data

The training data comes from [The Cauldron](https://huggingface.co/datasets/HuggingFaceM4/the_cauldron) and [Docmatix](https://huggingface.co/datasets/HuggingFaceM4/Docmatix) datasets, with emphasis on document understanding (25%) and image captioning (18%), while maintaining balanced coverage across other crucial capabilities like visual reasoning, chart comprehension, and general instruction following.
<img src="https://huggingface.co/HuggingFaceTB/SmolVLM-Instruct/resolve/main/mixture_the_cauldron.png" alt="Example Image" style="width:90%;" />

# Citation information
You can cite us in the following way:
```bibtex
@article{marafioti2025smolvlm,
  title={SmolVLM: Redefining small and efficient multimodal models}, 
  author={Andrés Marafioti and Orr Zohar and Miquel Farré and Merve Noyan and Elie Bakouch and Pedro Cuenca and Cyril Zakka and Loubna Ben Allal and Anton Lozhkov and Nouamane Tazi and Vaibhav Srivastav and Joshua Lochner and Hugo Larcher and Mathieu Morlon and Lewis Tunstall and Leandro von Werra and Thomas Wolf},
  journal={arXiv preprint arXiv:2504.05299},
  year={2025}
}
```

