# PROJECT_CONTEXT.md

# AI CRM Assistant — Project Context

## Project Goal

Build an AI-powered CRM assistant for a clinic using:

* LangGraph
* LangChain
* FastAPI
* OpenAI
* HTML frontend

Main learning goal:

Learn professional AI Agent Architecture and AI Engineering concepts, not build a medically accurate production clinic system.

Main focus:

* routing
* orchestration
* state machines
* evaluators
* reliability
* agent patterns
* debugging
* deployment

---

# Current Architecture

```text
User
↓
context_guard
↓
classify_intent
↓
conditional evaluator
↓
workflow node
↓
generate_response
```

---

# Main Components

## Code Organization (post-modularization)

To keep the public import path stable (`from nodes import *`) while refactoring, the code is split as follows:

```text
nodes.py                     # facade / re-exports for LangGraph
workflow_nodes/              # real node implementations (modular)
  logging_utils.py
  context_guard.py
  intent_classification.py
  response_generation.py
  appointment_booking.py     # currently re-exports legacy nodes_booking.py
  appointment_cancellation.py
  statuses.py
  commons.py
prompt_templates/            # prompt strings + formatter helpers
  clinic_crm.py
  customer_support.py
prompts.py                   # facade / re-exports for prompt_templates
```


## FastAPI

Backend API:

* `/chat`
* serves HTML frontend
* invokes LangGraph workflow

---

## LangGraph

Main orchestration layer.

The graph is defined in `graph.py` and imports nodes using:

* `from nodes import *`

`nodes.py` is intentionally kept as a **backward-compatible facade** (stable import path) and re-exports the real implementations from the `workflow_nodes/` package.

### Nodes in the graph

Routing / orchestration nodes:

* context_guard_node
* classify_intent_node
* evaluate_classification_node
* generate_response_node

Workflow nodes:

* book_appointment_node
* select_appointment_slot_node
* confirm_action_node
* cancel_confirmation_node
* cancel_appointment_node
* select_appointment_to_cancel_node
* referral_status_node
* form17_status_node
* human_escalation_node
* general_feedback_node
* unsupported_topic_node
* unknown_node


---

# State Management

Main state fields:

```python
active_flow
intent
classification_confidence

waiting_for_specialty
waiting_for_time_selection
waiting_for_confirmation
waiting_for_referral_id
waiting_for_form17_id
waiting_for_appointment_selection

specialty
selected_slot
selected_appointment_id

pending_action
pending_data

tool_result
answer

messages
logs
```

The system uses waiting-state logic to continue workflows across messages.

---

# Intent Classification

Uses structured output with Pydantic.

## IntentResult

Includes:

```python
intent
confidence
needs_clarification
missing_fields
reason
```

Classifier handles:

* appointment booking
* appointment cancellation
* referral status
* Form 17 status
* human escalation
* general feedback
* unsupported topics
* unknown requests

---

# Evaluator Pattern

Implemented:

```text
Classifier
↓
Evaluator
↓
Workflow
```

The evaluator reviews low-confidence classifications.

## ClassificationEvaluation

```python
decision_valid
suggested_intent
evaluation_reason
```

---

# Conditional Evaluator

Evaluator runs only when:

```python
classification_confidence < threshold
```

High-confidence classifications skip evaluator for performance and lower latency.

---

# Prompts

Prompts are now organized under `prompt_templates/`:

* `prompt_templates/clinic_crm.py` – clinic CRM prompts + formatter helpers
* `prompt_templates/customer_support.py` – customer support/router prompts

`prompts.py` remains as a backward-compatible facade to keep imports stable across the codebase.

---

# Context Guard


Handles:

* workflow continuation
* explicit flow switching
* state reset logic
* override requests

Examples:

* switching from booking to cancellation
* asking for human representative mid-flow

---

# Override Rules

Explicit override detection exists for:

* human representative
* secretary
* human support
* escalation requests

These requests should override active workflow states.

---

# Fake Backend

Current tools.py contains fake in-memory backend:

* appointments
* referrals
* Form 17 requests
* available slots

Purpose:
Learn AI orchestration before integrating real DB/backend systems.

---

# Deployment

Deployment stack:

* GitHub
* Render

Resolved issues:

* certifi_win32 Linux issue
* OpenAI timeout issues
* retry configuration
* environment variables

---

# Current Model Configuration

```python
COMMON_CONFIG = {
    "model": "gpt-4.1-mini",
    "temperature": 0,
    "max_retries": 2,
    "timeout": 60,
}
```

---

# Current Routing Quality

Evaluation dataset:

* 55 test cases
* 52 passed
* ~94.5% accuracy

Main remaining weak spots:

* generic help requests
* vague ambiguous intent
* context conflict edge cases

---

# Key Concepts Learned

## AI Architecture

* orchestration
* separation of concerns
* multi-step reasoning
* conditional routing

## Agent Patterns

* evaluator pattern
* critic/reviewer agent
* confidence gating
* deterministic guardrails

## Reliability

* context management
* workflow continuation
* override logic
* ambiguity handling

## Engineering

* deployment
* debugging
* retries/timeouts
* environment handling
* GitHub workflow

---

# Current TODO

## High Priority

1. Improve generic help request handling
2. Add Decision Summary Layer
3. Improve override rules
4. Build routing evaluation dataset
5. Add LangSmith tracing

---

# Future Ideas

* RAG integration
* real database
* async workflows
* memory improvements
* multi-agent architecture
* planner/reviewer hierarchy
* analytics dashboard
* conversation replay tools

---

# Important Design Decisions

## generate_response_node

Should only generate responses from state.

It should NOT:

* manage workflows
* make routing decisions
* contain business logic

---

## Workflow logic belongs in workflow nodes

Examples:

* booking logic
* slot selection
* confirmation handling
* cancellation flow

---

## Evaluator role

The evaluator validates reasoning quality.

It does NOT replace the classifier.

---

# Development Style

Project is intentionally developed step-by-step to deeply understand:

* why each architectural layer exists
* how AI systems fail
* how reliability is improved
* how orchestration patterns work

Focus is on learning professional AI engineering patterns rather than rapidly building features.
