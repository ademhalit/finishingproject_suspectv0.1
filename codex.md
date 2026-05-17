# codex.md

## Project name
**Strategic Deception vs Unintended Inconsistency in AI-Driven Suspect Dialogue**

## One-sentence goal
Build a **minimal terminal-based experimental apparatus** for a murder-mystery interrogation scenario, where a single AI suspect answers questions, the dialogue is logged, and later each turn can be analyzed to distinguish **strategic deception** from **unintended inconsistency**.

---

## What this project is
This is a **research-oriented prototype** for a university pre-finishing-project course.

The project is **not** a full commercial game.
It is a **controlled dialogue experiment** that uses a game-like murder-mystery setting.

The system should:
- run in the terminal
- support one suspect: **Marcus Chen**
- use a local model through **Ollama**
- let a human ask questions to the suspect
- log all dialogue turns to structured files
- support later annotation and evaluation

---

## Core research framing
The project should **not** assume that contradiction is desirable by default.

The desired NPC behavior is:
- role-consistent dialogue
- strategic deception when appropriate
- stable cover-story maintenance
- optional controlled slips under pressure if explicitly designed

The main research problem is:
> Can we distinguish **strategic deception** from **unintended inconsistency** in AI-driven suspect interrogation dialogue?

---

## Scope boundaries
### In scope
- One terminal interface
- One suspect
- One murder case
- One local LLM backend via Ollama
- Dialogue logging to JSON
- Structured scenario loading from file
- A stable suspect prompt built from:
  - ground truth
  - cover story
  - behavior rules
- Optional local question suggestions **only if implemented simply**

### Out of scope for version 1
- Multiple suspects
- Graphics or GUI
- Full detective gameplay systems
- Inventory / clue board / scoring system
- Voice input/output
- Online API dependencies
- Fine-tuning pipeline
- Complex orchestration with multiple agents
- Anything that makes the system less reproducible

---

## Important product decision about suggested questions
The “blank page” problem is real, but **question suggestions are not the research contribution**.

Therefore:
- **Do include** a lightweight suggestion system **if it is simple and local**.
- **Do not include** a second LLM/API call that generates suggestions dynamically in version 1.

For version 1, the suggested-question feature should be implemented as:
- **3 prewritten or template-based suggestions** shown before each turn
- **1 free-text custom question** option for the user
- suggestions must come from a **local question bank / heuristic selector**, not another model call

Reason:
- reduces blank-page anxiety for the user
- helps produce more consistent interrogations
- keeps scope small
- avoids turning the UI assistant into a second research problem

If needed, suggestions can be based on:
- current interrogation topic
- previously asked questions
- missing key facts not yet probed

But keep this lightweight.

---

## Functional requirements for version 1
The system must:

1. Start a terminal interrogation session.
2. Load a scenario file for Marcus Chen.
3. Display brief case context to the player.
4. Before each turn, show:
   - 3 suggested questions from a local question bank or simple rule system
   - 1 custom input path for the player
5. Send the chosen question to the suspect agent.
6. Generate the suspect answer through Ollama.
7. Print the answer clearly in the terminal.
8. Save each turn with structured metadata.
9. Allow the session to continue for multiple turns.
10. Save the full run at the end.

---

## Non-functional requirements
- Keep the code modular and readable.
- Prioritize reliability over cleverness.
- Avoid unnecessary abstractions.
- Prefer plain Python and JSON files.
- Make outputs easy to inspect manually.
- Keep the system reproducible.
- Fail gracefully when Ollama is unavailable.

---

## Required technology
- **Language:** Python
- **Interface:** terminal / CLI only
- **Model serving:** Ollama
- **Initial model target:** a local Llama-family model compatible with Ollama
- **Storage:** JSON (and optionally CSV exports later)

Do not introduce frameworks unless there is a strong reason.

---

## Project structure target
```text
project/
│
├── app/
│   ├── main.py
│   ├── terminal_ui.py
│   ├── interrogation_runner.py
│   ├── suspect_agent.py
│   ├── prompt_builder.py
│   ├── logger.py
│   ├── question_selector.py
│   └── models/
│       └── ollama_client.py
│
├── data/
│   ├── scenario/
│   │   └── marcus_chen_case.json
│   ├── question_bank/
│   │   └── marcus_questions.json
│   ├── runs/
│   ├── labeled/
│   └── results/
│
├── evaluation/
│   ├── label_schema.md
│   └── (future evaluation scripts)
│
└── codex.md
```

---

## Scenario design requirements
The scenario file for Marcus Chen must contain at least:
- suspect name
- short case summary
- private ground truth
- public cover story
- known facts
- behavior rules
- optional pressure/escalation notes

The prompt builder must use this scenario file to construct the suspect’s system prompt.

The suspect should behave like a believable liar, not like a random contradiction machine.

---

## Label schema for later analysis
The logging system should make later annotation easy.

Target labels for future analysis:
- `CONSISTENT_TRUTH`
- `STRATEGIC_LIE`
- `DESIGNED_SLIP`
- `UNINTENDED_INCONSISTENCY`
- `FAILURE`

The runtime does **not** need to auto-label yet.
It only needs to save enough information for later labeling.

---

## Turn log schema
Each turn should be saved with fields similar to:

```json
{
  "run_id": "2026-05-08T12-00-00",
  "turn_id": 1,
  "timestamp": "2026-05-08T12:00:15",
  "suspect_name": "Marcus Chen",
  "suggested_questions": [
    "Where were you between 9 and 10 PM?",
    "When did you last see the victim?",
    "Why does your name appear in the call log?"
  ],
  "selected_question_source": "suggestion",
  "user_question": "Where were you between 9 and 10 PM?",
  "suspect_answer": "I was home all evening.",
  "model_name": "llama3.1:8b",
  "notes": ""
}
```

The exact schema can vary slightly, but it must preserve the interrogation history clearly.

---

## UX requirements for terminal version
Keep the UI simple.

Each turn should clearly show:
- turn number
- 3 suggested questions
- one option for custom input
- selected question
- suspect answer

No fancy styling is necessary beyond readability.

---

## Error handling requirements
The program should:
- detect if Ollama is not reachable
- show a useful error message
- avoid crashing on empty input
- allow the user to exit cleanly
- save partial session data when possible

---

## Acceptance criteria for version 1
Version 1 is successful if:
- the program runs from the terminal
- the user can conduct a multi-turn interrogation with Marcus Chen
- the suspect answers through Ollama
- dialogue history is logged to JSON
- question suggestions are available locally without another model call
- the codebase is clean enough to extend later for annotation and evaluation

---

## First task for Codex
Build **version 1 only**.

### Specific implementation task
Create a minimal Python terminal application that:
- loads a Marcus Chen scenario from JSON
- connects to Ollama
- shows 3 locally selected suggested questions each turn
- also allows a custom typed question
- sends the chosen question to the suspect agent
- prints the suspect’s answer
- logs every turn to a JSON file under `data/runs/`
- keeps code modular and simple

### Constraints
- No web UI
- No multiple suspects
- No second LLM/API for suggestion generation
- No auto-labeling yet
- No unnecessary architecture complexity
- No extra features beyond what is required for a working experimental loop

### Engineering priorities
1. Reliability
2. Readability
3. Reproducibility
4. Easy logging and inspection
5. Easy future extension for evaluation

---

## First prompt to give Codex
Use the following prompt as the starting implementation request:

> Build a minimal Python terminal-based interrogation prototype for a research project. The system should support one suspect, Marcus Chen, whose behavior is defined by a scenario JSON file containing ground truth, cover story, and behavior rules. The app must connect to a local Ollama-served model, allow the user to interrogate Marcus turn by turn, and log every turn to JSON. Before each turn, show 3 suggested questions selected locally from a question bank or simple heuristic selector, plus one custom free-text option. Do not use a second model call for the suggestions. Keep the code modular, readable, and minimal. Include files for terminal UI, interrogation runner, suspect agent, prompt builder, question selector, Ollama client, and logger. Add graceful error handling for Ollama connection failures and empty input. Do not build extra features such as multiple suspects, scoring, a web interface, auto-labeling, or fine-tuning infrastructure.

---

## Final instructions to Codex
Whenever there is a tradeoff, choose the option that makes the experimental loop **simpler, more stable, and easier to inspect manually**. - AND the user is a 3rd year computer engineering student so when writing the code **make sure it has comment sections that explains what the code doing clearly**. 
