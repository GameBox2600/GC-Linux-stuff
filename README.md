
SDHC compatible GameCube Linux kernels from gcforever 
found at https://www.gc-forever.com/forums/viewtopic.php?t=769&sid=dd7d03e7a5f62ff94f8903c7f2145c77
Thanks to the person who put the effort into that^^

and a rootfs at
https://drive.google.com/drive/folders/14wgup_nv1WpPJG1_MLbANGUeLu55gVhb

kern2 was compiled from the 2.6.32 stable version at https://github.com/DeltaResero/GC-Wii-Linux-Kernels
it has the included sdhc support and networking, boot args are, 
root=/dev/gcnsdb2 rw rootwait force_keyboard_port=4 video=gcnfb:auto
ip=192.168.1.2::192.168.1.3:255.255.255.0::eth0:off

Boots off ext3 partition 2 of sdcard in memory card slot B, Uses ASCII ASC-1901PO GameCube Controller on port 4
sdcard must be reinstered during boot when it says waiting for /dev/gcnsdb2 etc.
Supports networking and was tested with DOL-15 offical broadband adapter,
Static IP set to 192.168.1.2 and gateway set to 192.168.1.3 on eth0, 
be sure to run the following at the first shell,
# mount -t proc proc /proc
# mount -t sysfs sysfs /sys
# exit
login etc...

