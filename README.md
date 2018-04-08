# useful-meeting-reminder

Ics based meeting reminder allowing storing notes &amp; ideas by replying to the email reminder.

## concept

The idea is to store a meeting plan associated with an event.
To be able to update this meeting plan by replying by mail to event reminders
The remind rule is called "halfway rule" : remind if event is new OR if time since last update is higher than time to event.

## overall command

### update meetings

* parse local ICS file
* keep event not older than 90 days and not farther in the furture than 90 days
* update local storage
* remove old events in storage, and notify by mail of the removal

### send reminders

* read local storage
* use the halfway rule to remind meeting

### process mails

* read dedicated inbox
* parse message
* if appending to the meeting plan is possible, do it
* if no appending and updating the meeting plan is possible, do it
* send back the results
