# Flipper Zero Database Files

This directory contains a comprehensive collection of database files, signal captures, and assets for the Flipper Zero device. These files are sourced from the [FlipperZeroDB](https://github.com/curiousqeorqe/FlipperZeroDB) repository, which aggregates community contributions and useful signal captures.

## Directory Structure

### Core Signal Databases

- **NFC/** - NFC card captures and examples
  - MIFARE Classic cards
  - MIFARE Ultralight cards
  - NFC-A/B/F protocol examples
  - Authentication dumps
  - Various card types and formats

- **Sub-GHz/** - Sub-GHz radio frequency captures
  - Ceiling fans
  - Doorbells
  - Gates and garage door openers
  - Vehicle remotes
  - LED controllers
  - Outlets and switches
  - Miscellaneous RF captures
  - Configuration files and settings

- **infrared/** - Infrared remote control databases
  - TVs (various brands)
  - Air conditioners
  - Audio systems
  - Set-top boxes
  - Projectors
  - Other IR-controlled devices

- **ibutton/** - iButton/Dallas key captures
  - Example key files
  - Common key types

### Additional Resources

- **BadUSB/** - BadUSB scripts and payloads
  - Various OS-specific payloads
  - Utility scripts
  - Educational examples

- **assets/** - Asset files and libraries
  - NFC dictionaries
  - Protocol definitions

- **picopass/** - Picopass/HID iCLASS captures
  - Example card dumps

- **unirf/** - Universal RF map files
  - Multi-button RF captures

- **SubPlaylist/** - Sub-GHz playlist files
  - Automated playback sequences

- **Music_Player/** - RTTTL music files
  - Ringtones and melodies

- **Applications/** - Example application files
  - Application manifests
  - Sample data files

- **Graphics/** - Custom graphics and animations
  - Icons and images

- **Dolphin_Level/** - Dolphin level/achievement files
  - Custom achievements

## Usage

These database files can be copied to your Flipper Zero's SD card to extend its functionality:

1. **Via qFlipper**: Use the file browser to upload specific files
2. **Direct SD Card**: Copy directories directly to your SD card
3. **Via USB**: Transfer files through the USB connection

### File Locations on Flipper Zero

Copy files to these locations on your SD card:

```
/ext/
├── nfc/           # NFC captures
├── subghz/        # Sub-GHz captures
├── infrared/      # IR captures
├── ibutton/       # iButton captures
├── lfrfid/        # RFID captures
├── picopass/      # Picopass captures
├── unirf/         # Universal RF maps
├── music_player/  # Music files
└── badusb/        # BadUSB scripts
```

## Important Notes

### Legal Disclaimer

⚠️ **IMPORTANT**: These files are provided for educational and research purposes only.

- Only use on devices you own or have explicit permission to test
- Unauthorized access to electronic systems is illegal in most jurisdictions
- Always comply with local laws and regulations
- RF transmission may be regulated in your area - check frequency restrictions
- Some signal captures may contain sensitive information - use responsibly

### Security Considerations

- **NFC captures** may contain partial authentication data
- **Sub-GHz signals** should only be transmitted in accordance with local regulations
- **BadUSB scripts** can modify system settings - test in controlled environments
- Always verify captured signals before transmission

## File Formats

### NFC Files (`.nfc`)
```
Filetype: Flipper NFC device
Version: 2
# Device type
Device type: MIFARE Classic
# UID, ATQA, SAK
UID: 04 68 C9 1A
ATQA: 00 44
SAK: 08
```

### Sub-GHz Files (`.sub`)
```
Filetype: Flipper SubGhz RAW File
Version: 1
Frequency: 433920000
Preset: FuriHalSubGhzPresetOok650Async
Protocol: RAW
```

### Infrared Files (`.ir`)
```
Filetype: IR signals file
Version: 1
# Device type
name: Power
type: parsed
protocol: NECext
```

## Contributing

These files are maintained by the community. To contribute:

1. Test captures thoroughly
2. Document device information
3. Verify compatibility
4. Follow naming conventions
5. Submit to the source repository

## Attribution

Files sourced from: [curiousqeorqe/FlipperZeroDB](https://github.com/curiousqeorqe/FlipperZeroDB)

A comprehensive collection maintained by the Flipper Zero community for educational and research purposes.

## Updates

This database is periodically updated with new captures and files from the community. Check the original repository for the latest updates.

Last Updated: October 2025

## Resources

- [Flipper Zero Official Documentation](https://docs.flipperzero.one/)
- [FlipperZeroDB Repository](https://github.com/curiousqeorqe/FlipperZeroDB)
- [Awesome Flipper Zero](https://github.com/djsime1/awesome-flipperzero)
- [Flipper Zero Forum](https://forum.flipperzero.one/)

## License

Individual files may have their own licenses. Please respect the original authors' rights and use responsibly.
