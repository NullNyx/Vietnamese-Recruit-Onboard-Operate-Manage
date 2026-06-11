with open('backend/src/modules/recruitment/application/candidate_service.py', 'r') as f:
    content = f.read()

content = content.replace(
    "event = await self._create_calendar_event(user_id, candidate_id, spec)",
    "event = await self._create_calendar_event(user_id, candidate_id, calendar_port, spec)"
)

# And also remove the `self._send_interview_email_notification` which I added incorrectly.
search_email = """        # Step 8: Email notification (if applicable)
        await self._send_interview_email_notification(candidate, spec)

"""
content = content.replace(search_email, "")

with open('backend/src/modules/recruitment/application/candidate_service.py', 'w') as f:
    f.write(content)
