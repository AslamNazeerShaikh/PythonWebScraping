# Fastfetch — system information

[Fastfetch](https://github.com/fastfetch-cli/fastfetch) is the system
information tool used to capture the environment snapshot below. Installed
here via Homebrew: `brew install fastfetch` (v2.70.0 at time of writing).

## Snapshot

```
                     ..'          aslamshaikh@Aslams-MacBook-Pro
                 ,xNMM.           ------------------------------
               .OMMMMo            OS: macOS Golden Gate 27.0.1 (26A434) arm64
               lMM"               Host: MacBook Pro (14-inch, M5, 2025)
     .;loddo:.  .olloddol;.       Kernel: Darwin 27.0.0
   cKMMMMMMMMMMNWMMMMMMMMMM0:     Uptime: 10 hours, 14 mins
 .KMMMMMMMMMMMMMMMMMMMMMMMWd.     Packages: 40 (brew), 6 (brew-cask)
 XMMMMMMMMMMMMMMMMMMMMMMMX.       Shell: zsh 5.9
;MMMMMMMMMMMMMMMMMMMMMMMM:        Display (DELL S2725QC): 5120x2880 @ 2x in 27", 120 Hz [External] *
:MMMMMMMMMMMMMMMMMMMMMMMM:        Display (Color LCD): 3024x1964 @ 2x in 14", 120 Hz [Built-in]
.MMMMMMMMMMMMMMMMMMMMMMMMX.       Window Manager: Quartz Compositor 1.600.0
 kMMMMMMMMMMMMMMMMMMMMMMMMWd.     WM Theme: Multicolor (Light)
 'XMMMMMMMMMMMMMMMMMMMMMMMMMMk    Theme: Liquid Glass
  'XMMMMMMMMMMMMMMMMMMMMMMMMK.    Font: .AppleSystemUIFont [System], Helvetica [User]
    kMMMMMMMMMMMMMMMMMMMMMMd      Cursor: Fill - Black, Outline - White (32px)
     ;KMMMMMMMWXXWMMMMMMMk.       Terminal: opencode.exe
       "cooc*"    "*coo'"         CPU: Apple M5 (4+6) @ 4.61 GHz
                                  GPU: Apple M5 (10) @ 1.62 GHz [Integrated]
                                  Memory: 19.83 GiB / 32.00 GiB (62%)
                                  Swap: Unused
                                  Disk (/): 209.68 GiB / 926.30 GiB (23%) - apfs [Read-only]
                                  Local IP (en0): 192.168.1.4/24
                                  Battery (bq40z651): 80% [AC Connected]
                                  Power Adapter: 65W
                                  Locale: C.UTF-8
```

## Usage

```bash
fastfetch                # default logo + system info
fastfetch --pipe         # disable colors (useful for logs/docs)
fastfetch --logo none    # disable logo
```

Run `fastfetch --help` for the full option list.
