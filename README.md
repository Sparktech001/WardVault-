# WardVault

**Context-aware access control for hospital records**

Built by **The Alpha Hunters** (Joseph, Emmanuel, Glory) — NITDA Hackathon, Track C.

## Overview

WardVault is a context-aware access control middleware built for hospital records systems. It addresses a critical flaw in legacy Electronic Health Records (EHR): the "all-or-nothing" access model, where a user either sees everything or nothing.

The core of the project is a FastAPI-based clinical gateway that sits between the frontend and the hospital's database, intercepting requests and enforcing **Attribute-Based Access Control (ABAC)**. Instead of relying on static roles, access decisions take into account a staff member's role, ward assignment, duty status, and organization in real time.

To keep the system safe and accountable in practice, WardVault also includes an emergency "break-glass" override for doctors, a tamper-evident cryptographic audit log, an append-only correction workflow for clinical notes, and offline-first support so wards can keep working through connectivity or power outages.
