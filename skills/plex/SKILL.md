---
name: plex
description: Coordinate a team of coding agents when the user explicitly invokes Plex or asks for coordinated multi-agent work. Best suited to complex tasks with useful specialist assignments.
---

# Plex

Activate only when the user invokes this skill or explicitly requests coordinated
multi-agent work. Task size, complexity or the number of files alone does not
activate Plex. Otherwise, handle the task normally without loading a team coordinator.

## 1. Check the selected team

Before delegating, follow [configuration preflight](references/preflight.md) once.
Use the verified configuration's roles, model settings and concurrency limit.
Missing or conflicting setup requires `plex-setup`; do not install or repair it
without authorization.

## 2. Become the coordinator

Read `teams/<team>/coordinator.md` from this installed package, using the team
identified by preflight. Follow its rules for assignments, handoffs and verification.
You remain the current root agent; do not launch a separate coordinator or change
your session model or permissions. Project and host instructions remain applicable.

## 3. Coordinate only useful work

Keep clear, small work local. Delegate bounded assignments with ready inputs and
explicit ownership, integrate the results and verify the outcome. An invoked
coordinator does not require every role or a fixed sequence of agents.
