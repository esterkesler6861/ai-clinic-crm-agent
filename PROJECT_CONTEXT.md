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
  appointment_booking.py
  appointment_cancellation.py
  statuses.py
  commons.py

prompt_templates/
  clinic_crm.py
  customer_support.py

prompts.py                   # backward-compatible facade
```

---

## FastAPI

Backend API:

* `/chat`
* serves HTML frontend
* invokes LangGraph workflow

---

## LangGraph

Main orchestration layer.

The graph is defined in `graph.py` and imports nodes using:

```python
from nodes import *
```

`nodes.py` is intentionally kept as a stable facade layer.

### Routing / orchestration nodes

* context_guard_node
* classify_intent_node
* evaluate_classification_node
* generate_response_node

### Workflow nodes

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
* knowledge_request_node

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

current_datetime
current_date
current_time
current_weekday
timezone
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
* knowledge requests
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

# RAG System

Implemented RAG pipeline using:

* Chroma vector database
* LangChain retrieval
* semantic chunking
* embedding search
* prompt augmentation

Current capabilities:

* FAQ retrieval
* urgent care information
* semantic search
* retrieval logging
* context-aware answering

RAG logs include:

* retrieved documents
* chunk previews
* context size
* retrieval statistics
* answer generation tracing

---

# Prompts

Prompts are organized under `prompt_templates/`:

* `clinic_crm.py`
* `customer_support.py`

Prompts include:

* routing prompts
* evaluator prompts
* RAG answering prompts
* response formatting prompts

---

# Context Guard

Handles:

* workflow continuation
* explicit flow switching
* state reset logic
* override requests
* ambiguity handling

Examples:

* switching from booking to cancellation
* asking for human representative mid-flow
* resetting stuck flows

---

# Override Rules

Explicit override detection exists for:

* human representative
* secretary
* human support
* escalation requests

These requests override active workflow states.

---

# Fake Backend

Current `tools.py` contains fake in-memory backend:

* appointments
* referrals
* Form 17 requests
* available slots

Purpose:

Learn orchestration before integrating real backend systems.

---

# Deployment

Deployment stack:

* GitHub
* Render

Resolved deployment issues:

* certifi_win32 Linux issue
* dependency issues
* OpenAI timeout handling
* retry configuration
* environment variables
* langchain-chroma deployment issue

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
* short follow-up questions

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
* workflow orchestration

## Reliability

* context management
* workflow continuation
* override logic
* ambiguity handling
* fallback logic

## RAG Engineering

* chunking strategies
* embeddings
* vector search
* retrieval debugging
* answer synthesis
* context injection

## Engineering

* deployment
* debugging
* retries/timeouts
* environment handling
* GitHub workflow

---

# Current TODO

## High Priority (Current Focus)

| Priority | Topic | Status | Estimated Time |
|---|---|---|---|
| 1 | Stabilize deployment + cleanup | In Progress | 3–6 hours |
| 2 | Professional README + architecture diagrams | Not Started | 3–5 hours |
| 3 | Demo conversation scenarios | Partial | 2–4 hours |
| 4 | Full flow testing (not only routing) | Partial | 5–10 hours |
| 5 | LangSmith tracing + observability | Not Started | 4–8 hours |
| 6 | Evaluation datasets + regression testing | Partial | 5–10 hours |
| 7 | Improve RAG reliability + fallback strategies | In Progress | 4–8 hours |
| 8 | Human-in-the-loop checkpoints | Not Started | 4–8 hours |
| 9 | Streaming responses | Not Started | 4–8 hours |
| 10 | Real persistence/database integration | Not Started | 6–12 hours |

---

## Medium Priority

| Topic | Estimated Time |
|---|---|
| Async workflows | 6–10 hours |
| Memory improvements | 4–8 hours |
| Conversation replay tools | 4–8 hours |
| Analytics dashboard | 6–12 hours |
| Planner/reviewer hierarchy | 8–16 hours |

---

## Advanced / Later Stage

| Topic | Estimated Time |
|---|---|
| Multi-agent architecture | 8–20 hours |
| Subgraphs | 4–8 hours |
| MCP integration | 10–20 hours |
| Skills system | 10–20 hours |
| Parallel execution workflows | 6–10 hours |

---

# Course Alignment Progress

| Course Module | Status |
|---|---|
| Introduction to AI Agents | Completed Practically |
| Prompt Engineering | Strong Practical Usage |
| RAG / Embeddings / Vector Search | Implemented |
| RAG in Practice | Partial |
| MCP | Not Started |
| Skills | Not Started |
| Effective Agents / Patterns | Strong Progress |
| LangChain | Implemented |
| LangGraph | Strong Progress |
| LangSmith / Observability | Partial |

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
* RAG orchestration

---

## Evaluator role

The evaluator validates reasoning quality.

It does NOT replace the classifier.

---

# Development Style

Project is intentionally developed step-by-step to deeply understand:

* why architectural layers exist
* how AI systems fail
* how reliability is improved
* how orchestration patterns work
* how production agents are debugged

Focus is on learning professional AI engineering patterns rather than rapidly building features.