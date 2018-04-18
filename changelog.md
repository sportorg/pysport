# Changelog

## 2018-04-17 v1.1.0

+ SFR (http://www.sportsystem.ru) timekeeping system support on Windows (only last model U5a with HID Interface). Thanks to Alexander Kurdumov for support and equipment sample.
+ Sportiduino (https://github.com/alexandervolikov/sportiduino) timekeeping system support. Thanks to Semyon Yakimov for contribution.
+ Sound effects while e-card readout
+ Auto filling of group and team if filter applied
+ Confirmation of application closing (including Alt+F4)
+ Detailed description of disqualification rules (Rus)
+ rufso-18-2. 'ZMS' qualification was removed (Rus)
+ rufso-18-10. Some translation changes (Rus)

- Fixed. Incorrect course order in relay printout
- Fixed. No ".json" extension while saving file on Linux

## 2018-03-16 v1.0.0

+ Official stable release
+ COM-port selecting for SPORTident master station

* Environment configuration for html templates
* Minor fixes in data model

## 2018-03-06 v0.11.0-rc4

+ Automatic disqualification if overtime
+ Templates improvement - information about course, location, time limit, referees was added
+ Team lists - added sorting by number and start time
+ Custom statuses for disqualification (external file)
+ Entry statistics report
+ Ranking for relays (Rus)
+ Saving of ranking information (Rus)

- Row braking in event title
- Relay online sending for orgeo.ru
- Simple finish support fixed (just finish time, F3)
- SI card editing fixed

## 2018-02-23 v0.11.0-rc3

+ SI Card assign mode
+ New templates for relay (start/result)
+ New storage format (.json)
+ Team work (client/server)
+ Editing person from result dialog
+ SI station status
+ Multi-language support
+ CP removing from courses and splits
+ Integration with Telegram

- Minor bug fixed
- Search fixed
- Online sending fixed

## 2018-01-25 v0.11.0-rc2

+ Fast start group editing (Alt + num)
+ Bulk DNS processing
+ New templates for splits and results
+ Partial relay support
+ Custom course order checking

- Minor buf fixed
- Saving with applied filter
- Stable sireader working (separated thread)

## 2018-01-16 v0.11.0-rc1

+ Added new field - id (uuid4)
+ Search tool - search text in all columns of current table
+ Creation organization while athlete editing
+ Team lists with start fee
+ Taking of start and finish time from any punch (by code)
+ Taking of start and finish from first and last punches
+ Live translation (to orgeo.ru)
+ Score calculation (formula and array)
+ Team result calculation by organization and region
+ Basic relay support (number assigning mode, place calculation)
+ Penalty calculation for marked route (Rus)
+ New Russian ranking ESVK 2018-2021 (Rus)

- Fixed the error of concurrent SI readout and split printing

## 2017-12-12 v0.10.0-beta

+ Added the ability to edit splits
+ Support for multiple marking systems at the model level
+ Printing of bib
+ Numbering rows in tables
+ Ability to select templates for separation
+ New template for split

- Taking into account the change in the starting time of the result

* Changed the project structure

## 2017-11-15 v0.9.0-beta

+ Assigning of card for athlete while result editing
+ Result editing - interactive number change
+ Person editing - check for duplicated bibs and card numbers
+ Improvements in SPORTident card readout
+ Rank calculation (specific for Russian orienteering)
+ Control order rechecking option
+ Automatic split reloading after course or bib change of result
+ Results tab: card number showing
+ Course editing: example of course control points configuration
+ Database format was changed - don't use files from previous version

- Default file names - date is moved to the first position
- Course: lap length saving was fixed
- Translation fixing for reports and interface
- Readout of cards with empty finish was fixed

## 2017-10-31 v0.8.0-beta

+ Automatical database saving while new finish or readout
+ Automatical SPORTident station connection
+ Remember the last used directory
+ Opening of recent file
+ Submenu "Recent files"
+ Templates (start list, results) were updated
+ Automatical split printing while readout

- "Open with" option for *.sportorg extention
- Mixing several groups while tossing
- Winorient import - splits import was fixed

## 2017-10-17 v0.7.2-beta

* Init
