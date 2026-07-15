# SES-3 
This session focuses on bug fixing , CI/CD improvement and some research about new features. 

## New Feature research
I realized for the past 2 weeks I have not implemented new features, and only fixed bugs and did improvements. I researched a little and looked into other QR libraries and looked for the stuff that the other libraries lack. I decided on some new features like Kanji Mode, there are few but I wont mention them here. (research time isnt logged cause I forgot but it was like an hour)

## Bug Fixing
Did some bug fixing with the logo embedding QR code again. Its the only QR code type that fails the most. This time I guarantee it wont fail again.

## CI/CD Improvements 
Finally I realized for my test workflows I use `pyzbar` which is a qr code decoding library. But it does not support microqr decoding. So I had to switch to another libray called `zxingcpp` which does support what `pyzbar` has with microqr decoding support as well. I took some help from some people online regarding the tests and they help me make some test scripts. I broke down the main test script into smaller parts so Its easier for me and the readers.

## Conclusion
Thats it for this session. Its like 95% completed for shipping and logged 50 hours as well. Just some final new features (mentioned above) and some documentation work and It v2 will be released. Thank you for reading the entire thing. I hope you'll like it and find BetterQR useful. New features / suggestions / complaints are accepted in the replies via a DM on slack. I need some honest feedback.