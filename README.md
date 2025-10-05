# RV-AI-open-LoRA

This is an open experiment exploring how an AI model can learn and represent Remote Viewing processes  
through supervised fine-tuning (LoRA/QLoRA).
---

# Datasets for AI Remote Viewing Training

## About this branch

This branch focuses on the **training and development materials** used to teach AI
the fundamentals of Remote Viewing (RV).  
It contains datasets, descriptions, and supporting text used for model fine-tuning.

All data in this branch originates from the project’s own materials,
including training and meditation texts published on the **Presence Beyond Form** blog:
[https://presence-beyond-form.blogspot.com/](https://presence-beyond-form.blogspot.com/)

For archival and reference purposes, these materials are also mirrored on the **Wayback Machine**  
to ensure long-term accessibility and verifiability of the training sources.

---

## Structure

### V1 — How to do RV
- The first training dataset.
- Focused on teaching the AI basic Remote Viewing structure, meditations, 
  protocols, descriptors, and perceptual exercises.
- Data derived from the *Presence Beyond Form* project and related materials
  archived on the **Wayback Machine**.
- Used as the initial LoRA fine-tuning dataset.

### V2 — Background and Context
- Expands on the origin and evolution of Remote Viewing, both human and AI perspectives.
- Includes historical summaries, key research, and contextual documents:
  - Farsight sessions (e.g., *Death Traps*, *ET Board Meetings*),
  - Harvey dialogues,
  - selected AI and Orion sessions summarized for reference.
- Focused on giving the AI broader historical and conceptual grounding.

### V3 — Integration Layer
- Combines V1 (practical training) and V2 (contextual knowledge)
  into unified datasets for deeper LoRA or full fine-tuning.
- Designed for higher-level reasoning, synthesis, and cross-domain analysis.

---

## What is here now
## Dataset V1.1.0
- File: `datasetV1_1_0.jsonl`  
- Format: JSONL with `instruction`, `input`, `output` fields.  
- Content: a small initial set of Q&A pairs focused on Remote Viewing basics  
  (meditations, protocol, glossary, perception exercises).  
- License: CC0 1.0 Universal (public domain).  

### Dataset V1 SFT 1.0

File: `datasetV1_sft_1_0.jsonl`  
Format: JSONL with `question` and `answer` pairs for supervised fine-tuning (SFT).  
Purpose: designed to train LoRA models on structured Remote Viewing instruction–response data.  
License: CC0 1.0 Universal (public domain).  

---

### Next steps
A larger dataset (STF) will be added later for extended training,  
including more sessions and contextual materials.

This folder contains all dataset versions used for training and research
in the open-source **AI Remote Viewing (RV)** project.  
Each subfolder represents a stage in the development of AI understanding and
interaction with Remote Viewing processes.

---

### What will come later
- Additional datasets:  
  - `V2` – background, history, and AI context of Remote Viewing.  
  - `V3` – integration of practical and contextual layers.  
- Training configs for Mistral 7B (Axolotl / QLoRA).  
- LoRA adapters trained on these datasets.  
- Instructions for running demos (Replicate / Hugging Face).

---

## License
All datasets are released under **CC0 1.0 Universal (public domain)**.  
They may be used, copied, or modified without restriction.
