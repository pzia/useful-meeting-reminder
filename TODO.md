# TODO

## FIXME

* html entities clean up (beautfiful soup ?)
* recurring events are not kept when in the past

## FEATURE : FOCUS

* better handling around meeting time
* Blacklisting
  * by title (regexp)
  * by uid
* reply with html from markdown
* Remind past event when TODO or FIXME

## ARCHITECTURE

* check_mail in status.json to ajust frequency
  * once per hour
  * every 2 minute if activity during last fifteen minutes
* cleverer loading of ics (mtime change of the file)
* more conf
* Modular storage (standardfile, sqlite, reddis)
* Testability : dry_run mode (see keep_my_datas)

## FEATURE : OTHER

* append file to meeting
* multiple calendars ?
* ICS feed from store

## WOULD BE NICE ELSEWHERE

* Efficiency : match meetings with work inbox
  * detect event in mails
  * propose for inclusion in calendar
