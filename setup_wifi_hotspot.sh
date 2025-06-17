
#!/bin/bash

echo "Setting up ParakaleoMed WiFi Hotspot..."

# Install required packages
sudo apt update
sudo apt install hostapd dnsmasq iptables-persistent -y

# Stop conflicting services
echo "Stopping conflicting services..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sudo systemctl stop NetworkManager 2>/dev/null || true
sudo systemctl stop wpa_supplicant 2>/dev/null || true

# Kill any processes using wlan0
sudo pkill wpa_supplicant 2>/dev/null || true
sudo pkill dhcpcd 2>/dev/null || true

# Set regulatory domain (important for some regions)
echo "Setting WiFi regulatory domain..."
sudo rfkill unblock wifi
echo 'REGDOMAIN=US' | sudo tee /etc/default/crda > /dev/null

# Configure hostapd with more compatible settings
echo "Configuring hostapd..."
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
country_code=US
ieee80211n=1
EOF

# Tell hostapd where to find config
echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | sudo tee /etc/default/hostapd > /dev/null

# Configure dnsmasq
echo "Configuring dnsmasq..."
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true
sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=local
address=/gw.wlan/192.168.4.1
EOF

# Configure static IP for wlan0 - remove any existing entries first
echo "Configuring network interface..."
sudo sed -i '/interface wlan0/,/^$/d' /etc/dhcpcd.conf
sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF

interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Disable NetworkManager for wlan0
echo "Configuring NetworkManager..."
sudo tee /etc/NetworkManager/NetworkManager.conf > /dev/null <<EOF
[main]
plugins=ifupdown,keyfile

[ifupdown]
managed=false

[keyfile]
unmanaged-devices=interface-name:wlan0
EOF

# Enable IP forwarding
echo "Enabling IP forwarding..."
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf > /dev/null

# Configure iptables for internet sharing (optional)
echo "Configuring firewall..."
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
sudo netfilter-persistent save 2>/dev/null || true

# Restart dhcpcd to apply interface changes
echo "Restarting network services..."
sudo systemctl restart dhcpcd

# Wait a moment for interface to settle
sleep 3

# Test hostapd configuration
echo "Testing hostapd configuration..."
sudo hostapd -t /etc/hostapd/hostapd.conf
if [ $? -eq 0 ]; then
    echo "✅ hostapd configuration is valid"
else
    echo "❌ hostapd configuration has errors"
    exit 1
fi

# Enable services
echo "Enabling services..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Try to start services
echo "Starting services..."
sudo systemctl start hostapd
sudo systemctl start dnsmasq

# Check if services started successfully
if sudo systemctl is-active --quiet hostapd && sudo systemctl is-active --quiet dnsmasq; then
    echo ""
    echo "🎉 WiFi hotspot configured successfully!"
    echo "SSID: ParakaleoMed-Clinic"
    echo "Password: wpawpawpa"
    echo "Pi IP: 192.168.4.1"
    echo "App URL: http://192.168.4.1:5000"
    echo ""
    echo "✅ Hotspot is now active!"
    echo "You should see the WiFi network 'ParakaleoMed-Clinic' in your available networks."
else
    echo ""
    echo "⚠️  Services configured but may need a reboot to fully activate."
    echo "Run: sudo reboot"
fi
