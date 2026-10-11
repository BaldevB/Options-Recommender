---
name: superpowers
description: Complete software engineering methodology for AI coding agents. Enforces disciplined brainstorming, strict test-driven development (TDD / red-green-refactor), git worktrees, bite-sized implementation planning, subagent-driven development, code review, systematic debugging, and verification before completion. Use whenever the user asks for superpowers, superpower, or wants disciplined software engineering, TDD, structured workflows, or systematic debugging.
---

# Superpowers: Disciplined Engineering Methodology

Superpowers is an engineering framework for coding agents that enforces engineering discipline, structured workflows, test-driven development, and quality control.

## The Superpowers Lifecycle

1. **brainstorming (`superpowers:brainstorming`)**
   - Pauses before code generation to ask clarifying questions and explore requirements.
   - Generates a focused, bite-sized specification approved in chunks by the user.

2. **using-git-worktrees (`superpowers:using-git-worktrees`)**
   - Isolates development on dedicated git branches/worktrees to prevent workspace pollution.

3. **writing-plans (`superpowers:writing-plans`)**
   - Breaks approved designs into micro-tasks (2-5 min each).
   - Specifies exact files, code changes, and verification commands.

4. **subagent-driven-development / executing-plans**
   - Dispatches tasks with clean context and reviews work against specifications.

5. **test-driven-development (`superpowers:test-driven-development`)**
   - Enforces the **RED-GREEN-REFACTOR** cycle:
     - Red: Write a failing test first and verify it fails.
     - Green: Write minimal code to pass the test.
     - Refactor: Clean up and optimize while tests remain green.

6. **systematic-debugging (`superpowers:systematic-debugging`)**
   - 4-phase root cause analysis before guessing or applying patches.

7. **verification-before-completion (`superpowers:verification-before-completion`)**
   - Runs full test suites, typechecks, and builds before marking any task as complete.

## Available Superpowers Skills
- `superpowers`
- `using-superpowers`
- `brainstorming`
- `writing-plans`
- `executing-plans`
- `test-driven-development`
- `systematic-debugging`
- `subagent-driven-development`
- `dispatching-parallel-agents`
- `requesting-code-review`
- `receiving-code-review`
- `verification-before-completion`
- `using-git-worktrees`
- `finishing-a-development-branch`
- `diagnosing-superpowers`
- `writing-skills`
