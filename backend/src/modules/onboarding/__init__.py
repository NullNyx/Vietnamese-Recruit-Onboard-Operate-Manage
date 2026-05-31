"""Onboarding module.

Consumes the `candidate_accepted` domain event to turn an accepted Candidate
into an active Employee through a fixed, checklist-driven OnboardingProcess.
Creates an inactive Employee, drives task completion by HR (the admin role),
and activates the Employee once every Onboarding Task is done.
"""
