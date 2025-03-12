![Biovault](/biovault.png)

### About:

With the two helper scripts in this repo it is possible to read and write an AES-256 encrypted file on an NFC implant (specifically the [xSIID](https://dangerousthings.com/product/xsiid/)). The `hf_i2c_plus_2k_utils` script can also be used standalone to write arbitrary data to user memory on a sector of your choosing (sector 0 or 1). 

The `vault.py` script is a python wrapper around `hf_i2c_plus_2k_utils` which reads and writes the encrypted file (CSV format) to/from the implant. In read mode the CSV file is carved from a user memory hexdump, reversed with xxd, decrypted with openssl (if you have the password) and then displayed in the terminal in JSON format.

`vault.py` writes data to sector 1 not sector 0 for two reasons:

1.  Sector 0 can still be used to read and write NDEF records. Sector 1 remains untouched when modifying sector 0.
2.  Sector 1 is not accessible from Android or IOS without a custom application or a tool to send raw commands.

Even with encrypted data written to sector 1, when the implant is read from a device such as a phone it will still only return the NDEF record in sector 0 (URL, vcard etc). When the encrypted data needs to be accessed just use the proxmark3 to access sector 1 using `vault.py`.



### To Do:

- [ ] : The lua script is good. The python script is functional but shit. When I have some time I will refactor it to use pure python not os.system calls so no files need to be written/deleted from disk.
- [ ] : Add support for other data formats and maybe some compression to save space.


### Requirements:


Software: python3, openssl, jq ,csvtojson

• sudo apt install -y python3 openssl jq npm

• sudo npm -g install csvtojson

Hardware: Proxmark3

Usage:

1.  move `hf_i2c_plus_2k_utils.lua` to `~/.proxmark3/luascripts/`
    - this script is now in the [Proxmark3 Iceman fork](https://github.com/RfidResearchGroup/proxmark3/blob/master/client/luascripts/hf_i2c_plus_2k_utils.lua) so you can just do a `git pull` to grab the latest version
2.  install jq and csvtojson : `brew install jq ; npm -g install csvtojson`
3.  create a csv file in the following format and save it as vault.txt in the same folder as vault.py:

Example vault.txt:
```
d,u,p
google.com,testuser,Password1
reddit.com,reddituser,Password2
```
- Write the encrypted file to the xSIID:

4.  `python3 biovault.py -m w`

- Zero sector 1 with null bytes and then write the encrypted file to the xSIID:

5.  `python3 biovault.py -m w -z`

- Dump, carve, decrypt and write the stored file to vault.txt.dec:

6.  `python3 biovault.py -m r`

- Securely shred and delete vault.txt.dec:

7.  `python3 biovault.py -s`


*Note:* 

*You will need to modify variables `pm3_path` and `uid` in vault.py (lines 13,14) to reflect the path to the pm3 binary and your implants UID.* 
*If you already have data on sector 1, use the -z flag to zero out the user memory of sector 1 with NULL bytes.*

### Demo:

https://user-images.githubusercontent.com/39644720/203556380-568f0041-d17b-4663-94a9-fe70b80680e4.mp4



