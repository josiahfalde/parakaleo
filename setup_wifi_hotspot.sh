
#!/bin/bash

# Install required packages
sudo apt update
sudo apt install hostapd dnsmasq iptables-persistent -y

# Stop services
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# Configure hostapd
sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan0
driver=nl80211
ssid=ParakaleoMed-Clinic
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=wpawpawpa
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Configure dnsmasq
sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Configure static IP for wlan0
sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Enable IP forwarding and configure iptables
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

# Enable services
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "WiFi hotspot configured!"
echo "SSID: ParakaleoMed-Clinic"
echo "Password: wpawpawpa"
echo "Pi IP: 192.168.4.1"
echo "App URL: http://192.168.4.1:5000"
echo "Reboot to activate: sudo reboot"
#!/bin/bash

# Install required packages
sudo apt update
sudo apt install hostapd dnsmasq iptables-persistent -y

# Stop services
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# Configure hostapd
sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan0
driver=nl80211
ssid=ParakaleoMed-Clinic
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=wpawpawpa
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Configure dnsmasq
sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Configure static IP for wlan0
sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Enable IP forwarding and configure iptables
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

# Enable services
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "WiFi hotspot configured!"
echo "SSID: ParakaleoMed-Clinic"
echo "Password: wpawpawpa"
echo "Pi IP: 192.168.4.1"
echo "App URL: http://192.168.4.1:5000"
echo "Reboot to activate: sudo reboot"
