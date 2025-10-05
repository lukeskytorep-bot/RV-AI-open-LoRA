# Dataset V1 SFT 1.0

This dataset (`datasetV1_sft_1_0.jsonl`) contains structured **question–answer pairs**
prepared for supervised fine-tuning (SFT) and LoRA training in the  
**AI Remote Viewing (RV)** project.

## Format
- JSONL format with `question` and `answer` fields.
- Example:
  ```json
  {"question": "What is the first step of the Elisius Meditation?", "answer": "Empty yourself. Pause, quiet the head, do not ask any questions yet. Just remain present."}
  ```

## Focus
- Precise, instruction-based Q→A data derived from RV training materials.
- Designed for LoRA / QLoRA fine-tuning tests on open models (e.g., Mistral 7B).

## License
- CC0 1.0 Universal (public domain).
- Free to use, copy, or modify without restrictions.

## Version
- 1.0
