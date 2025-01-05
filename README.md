# DaveZ's : DayZ Python Tools.

<!-- ----------------------------------------------------------------------- -->
# ABOUT

PyDayZ package contains a variety of classes for reading and reinterpreting
various DayZ and ArmA file formats.

This is very much a work in progress, and is based largely on the very excellent
contributions by many more skilled people than I. This project is attempting to
translation their hard work in deciphering the DayZ/Arma binaries into a usable
python library.

Currently the library can ingest Paa, Pbo, OPRW (WRP) world files, and de-rap.

Testing is limited to the latest release of DayZ (1.26) and has not been tested
with Arma, Reforger. Technically as they all use similar file structures it 
should work, I've tried to follow the documented exceptions for each.

P3D.py is definitely not working yet. I'm just stuck on this one as the
documentation seems to have deviated from the files I have???  
https://community.bistudio.com/wiki?title=P3D_File_Format_-_ODOLV4x


File formats:<br/>
https://community.bistudio.com/wiki/BIS_File_Formats?useskin=darkvector<br/>
PAA : https://community.bistudio.com/wiki/PAA_File_Format<br/>
PBO : https://community.bistudio.com/wiki/PBO_File_Format<br/>
WRP : https://community.bistudio.com/wiki/Wrp_File_Format_-_OPRWv17_to_24<br/>
P3D : https://community.bistudio.com/wiki?title=P3D_File_Format_-_ODOLV4x<br/>
RAP : https://community.bistudio.com/wiki/raP_File_Format_-_OFP<br/>

Data Types:<br/>
https://community.bistudio.com/wiki/Generic_FileFormat_Data_Types<br/>


# Setup

I'm just developing at the moment running the tests with python -m tests
See the tests/__main__.py for that.
