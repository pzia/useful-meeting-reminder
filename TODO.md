# TODO

## IDEAS

* Architecture : check_mail in status.json to ajust frequency
  * once per hour
  * every 2 minute if activity during last fifteen minutes
* Architecture : cleverer loading of ics (mtime change of the file)
* Focus : better handling around meeting time
* Focus : Blacklisting
  * by title (regexp)
  * by uid
* Testability : dry_run mode (see keep_my_datas)
* Architecture : more conf
* Architecture : Modular storage (standardfile, sqlite, reddis)
* Feature : append file to meeting
* Feature : multiple calendars ?
* Focus : reply with html from markdown
* Focus : append (and not only replace)

## Elsewhere

* Efficiency : match meetings with work inbox
  * detect event in mails
  * propose for inclusion in calendar
